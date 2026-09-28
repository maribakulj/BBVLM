#!/usr/bin/env python3
"""Fetch only the pre-frozen BnL A45 members from a 1.9 GiB remote ZIP.

The script reads the ZIP central directory and selected local members with HTTP
range requests.  It never downloads the complete public archive.
"""
from __future__ import annotations

import binascii
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import struct
import urllib.request
import zlib


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/loop/bnl-independent-a45"
SPLIT = EXPERIMENT / "split.json"
SOURCE = EXPERIMENT / "source"
PREFIX = "bnl-ground-truth-newspapers-before-1878-raw/data/"
EOCD = struct.Struct("<4s4H2LH")
CENTRAL = struct.Struct("<4s6H3L5H2L")
LOCAL = struct.Struct("<4s5H3L2H")


def request(url: str, start: int | None = None, end: int | None = None) -> bytes:
    headers = {"User-Agent": "BBVLM/independent-ground-truth-fetch"}
    if start is not None:
        headers["Range"] = f"bytes={start}-{'' if end is None else end}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        if start is not None and response.status != 206:
            raise ValueError(f"server ignored byte range (HTTP {response.status})")
        return response.read()


def content_length(url: str) -> int:
    request_obj = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "BBVLM/independent-ground-truth-fetch"})
    with urllib.request.urlopen(request_obj, timeout=120) as response:
        return int(response.headers["Content-Length"])


def central_entries(url: str) -> dict[str, dict[str, int]]:
    size = content_length(url)
    tail_size = min(size, 16 * 1024 * 1024)
    tail_start = size - tail_size
    tail = request(url, tail_start, size - 1)
    eocd_position = tail.rfind(b"PK\x05\x06")
    if eocd_position < 0:
        raise ValueError("ZIP end-of-central-directory record not found")
    fields = EOCD.unpack_from(tail, eocd_position)
    count, central_size, central_offset = fields[4], fields[5], fields[6]
    if central_offset < tail_start or central_offset + central_size > size:
        central_data = request(url, central_offset, central_offset + central_size - 1)
    else:
        relative = central_offset - tail_start
        central_data = tail[relative:relative + central_size]
    entries = {}
    position = 0
    for _ in range(count):
        fields = CENTRAL.unpack_from(central_data, position)
        if fields[0] != b"PK\x01\x02":
            raise ValueError("invalid central-directory member signature")
        compression, crc, compressed, uncompressed = fields[4], fields[7], fields[8], fields[9]
        name_length, extra_length, comment_length = fields[10], fields[11], fields[12]
        local_offset = fields[16]
        start = position + CENTRAL.size
        name = central_data[start:start + name_length].decode("utf-8")
        entries[name] = {"compression": compression, "crc": crc, "compressed": compressed,
                         "uncompressed": uncompressed, "local_offset": local_offset}
        position = start + name_length + extra_length + comment_length
    return entries


def member_bytes(url: str, entry: dict[str, int]) -> bytes:
    offset = entry["local_offset"]
    header = request(url, offset, offset + LOCAL.size - 1)
    fields = LOCAL.unpack(header)
    if fields[0] != b"PK\x03\x04":
        raise ValueError("invalid local member signature")
    data_start = offset + LOCAL.size + fields[9] + fields[10]
    compressed = request(url, data_start, data_start + entry["compressed"] - 1)
    if entry["compression"] == 0:
        data = compressed
    elif entry["compression"] == 8:
        data = zlib.decompress(compressed, -zlib.MAX_WBITS)
    else:
        raise ValueError(f"unsupported ZIP compression method {entry['compression']}")
    if len(data) != entry["uncompressed"] or (binascii.crc32(data) & 0xFFFFFFFF) != entry["crc"]:
        raise ValueError("member size/CRC verification failed")
    return data


def main() -> None:
    split = json.loads(SPLIT.read_text())
    url = split["source"]["url"]
    wanted = [PREFIX + identifier + suffix for identifier in split["selection"]["ids"]
              for suffix in (".xml", ".png")]
    entries = central_entries(url)
    missing = sorted(set(wanted) - set(entries))
    if missing:
        raise ValueError(f"members missing from archive: {missing}")
    SOURCE.mkdir(parents=True, exist_ok=True)
    def fetch_one(name: str) -> dict[str, object]:
        destination = SOURCE / Path(name).name
        entry = entries[name]
        if destination.exists():
            data = destination.read_bytes()
            if len(data) != entry["uncompressed"] or (binascii.crc32(data) & 0xFFFFFFFF) != entry["crc"]:
                data = member_bytes(url, entry)
                destination.write_bytes(data)
        else:
            data = member_bytes(url, entry)
            destination.write_bytes(data)
        return {"member": name, "file": destination.name, "bytes": len(data),
                "crc32": f"{entry['crc']:08x}"}

    with ThreadPoolExecutor(max_workers=8) as pool:
        manifest = list(pool.map(fetch_one, wanted))
    (EXPERIMENT / "fetch-manifest.json").write_text(json.dumps({
        "schema": "bbvlm.remote-zip-range-fetch/1", "source": url,
        "complete_archive_downloaded": False, "members": manifest
    }, indent=2) + "\n")
    print(json.dumps({"members": len(manifest), "bytes": sum(row["bytes"] for row in manifest),
                      "destination": str(SOURCE)}, indent=2))


if __name__ == "__main__":
    main()

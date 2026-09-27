#!/usr/bin/env python3
"""Download the official BnF IMPACT corrected-OCR archive reproducibly.

Only the ZIP central directory is inspected here. PAGE/image bytes remain
unopened until the A26 protocol, implementation and split are sealed.
"""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "loop" / "bnf-impact-a26" / "source"
ARCHIVE = OUT / "impact.zip"
MANIFEST = OUT / "archive-manifest.json"
SHARE = "https://transfert.bnf.fr/link/b72a8623-c428-4d1b-a916-e4384c2c4573"
POST = "https://transfert.bnf.fr/webclient/godrive/PublicGoDrive.xhtml"
TARGET = "impact.zip"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    first = opener.open(SHARE, timeout=120)
    html = first.read().decode("utf-8", "replace")
    form_start = html.index('<form id="fileList"')
    form_end = html.index("</form>", form_start)
    form = html[form_start:form_end]
    viewstate = re.search(
        r'name="javax.faces.ViewState"[^>]*value="([^"]+)"', form
    )
    if not viewstate:
        raise RuntimeError("missing JSF view state")
    link = re.search(
        r"PrimeFaces\.addSubmitParam\('fileList',\{'([^']+)':'[^']+'\}\)"
        r"\.submit\('fileList'\);return false;\">" + re.escape(TARGET),
        form,
    )
    if not link:
        raise RuntimeError(f"{TARGET} not listed by official share")
    control = link.group(1)
    payload = urllib.parse.urlencode(
        {"fileList": "fileList", control: control, "fileList_SUBMIT": "1",
         "javax.faces.ViewState": viewstate.group(1)}
    ).encode()
    request = urllib.request.Request(POST, data=payload, headers={"Referer": first.url})
    response = opener.open(request, timeout=180)
    disposition = response.headers.get("Content-Disposition", "")
    if TARGET not in disposition:
        raise RuntimeError(f"unexpected response: {disposition!r}")
    expected = int(response.headers.get("Content-Length", "0"))
    if expected < 100_000_000:
        raise RuntimeError(f"unexpected archive length: {expected}")
    with ARCHIVE.open("wb") as output:
        while block := response.read(1024 * 1024):
            output.write(block)
    if ARCHIVE.stat().st_size != expected:
        raise RuntimeError("truncated download")

    with zipfile.ZipFile(ARCHIVE) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"corrupt archive member: {bad}")
        members = [
            {"name": item.filename, "bytes": item.file_size,
             "compressed_bytes": item.compress_size, "crc32": f"{item.CRC:08x}",
             "is_dir": item.is_dir()}
            for item in archive.infolist()
        ]
    report = {
        "schema": "bbvlm.bnf-impact-archive-a26/1",
        "source_page": "https://api.bnf.fr/fr/ocr-corrige-de-documents-de-presse-de-gallica",
        "official_share": SHARE,
        "archive": TARGET,
        "bytes": ARCHIVE.stat().st_size,
        "sha256": digest(ARCHIVE),
        "downloaded_unix": time.time(),
        "inspection_scope": "ZIP central-directory names/sizes/CRC only; member bytes unopened",
        "members": members,
    }
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("archive", "bytes", "sha256", "inspection_scope")}
                     | {"members": len(members)}, indent=2))


if __name__ == "__main__":
    main()

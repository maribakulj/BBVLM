"""Restore exactly the native Eynollah textline SavedModel used by A72."""
import argparse
import hashlib
from pathlib import Path

from remotezip import RemoteZip

ROOT = Path(__file__).resolve().parents[1]
URL = "https://zenodo.org/api/records/21381102/files/models_training_layout_v0_9_1.zip/content"
PREFIX = "models_eynollah/modelens_textline_0_1__2_4_16092024/"
DEST = ROOT / "models/eynollah/native/modelens_textline_0_1__2_4_16092024"
HASHES = {
    "config.json": "aac06e8f74e82812db2d2534034a434bfb162a0022d62d6815a92cf4c7ac9585",
    "fingerprint.pb": "e1757519fac1208e1f2c6625a79e433762d57db48d399db69a1466f2cf560e46",
    "keras_metadata.pb": "3c3f53339a7f5b7db6c3407ded7ccaa32a3cdf165ee801d332fa7f704d333ca2",
    "saved_model.pb": "9b799e2510b5b144a7b94328b7e3b49b45edb1a74ec5e1f27473d6ad1a993825",
    "variables/variables.data-00000-of-00001": "5da57fd65ecbdaf49657318740121600583de9b57774b96a854dc8957e9d8a15",
    "variables/variables.index": "aeb2d2d226f27e26de38eb40ab4599b12e2b5fec89dacc290cc2b625631f1b5b",
}


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def verify():
    for relative, expected in HASHES.items():
        path = DEST / relative
        if not path.is_file() or digest(path) != expected:
            raise SystemExit(f"missing or invalid: {relative}")
    print(f"verified {len(HASHES)} files in {DEST}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if not args.verify_only:
        with RemoteZip(URL) as archive:
            members = {entry.filename: entry for entry in archive.infolist()}
            for relative in HASHES:
                name = PREFIX + relative
                destination = DEST / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.is_file() and digest(destination) == HASHES[relative]:
                    continue
                with archive.open(members[name]) as source, destination.open("wb") as target:
                    while chunk := source.read(1024 * 1024):
                        target.write(chunk)
    verify()


if __name__ == "__main__":
    main()

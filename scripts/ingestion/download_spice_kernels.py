from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path


OUTPUT_DIR = Path("data/raw/spice")

KERNELS = {
    "de440s.bsp": (
        "https://naif.jpl.nasa.gov/pub/naif/"
        "generic_kernels/spk/planets/de440s.bsp"
    ),
    "naif0012.tls": (
        "https://naif.jpl.nasa.gov/pub/naif/"
        "generic_kernels/lsk/naif0012.tls"
    ),
    "pck00011.tpc": (
    "https://naif.jpl.nasa.gov/pub/naif/"
    "generic_kernels/pck/pck00011.tpc"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []

    for filename, url in KERNELS.items():
        destination = OUTPUT_DIR / filename

        if destination.exists():
            print(f"Already exists: {filename}")
        else:
            print(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, destination)

        file_hash = sha256(destination)

        manifest.append(
            {
                "filename": filename,
                "source_url": url,
                "size_bytes": destination.stat().st_size,
                "sha256": file_hash,
            }
        )

        print(
            f"  size: {destination.stat().st_size:,} bytes\n"
            f"  sha256: {file_hash}"
        )

    manifest_path = OUTPUT_DIR / "kernel_manifest.json"

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print()
    print(f"Wrote kernel manifest: {manifest_path}")


if __name__ == "__main__":
    main()
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    ROOT
    / "data"
    / "raw"
    / "spice"
)

FILENAME = (
    "earth_1962_260806_2126_combined.bpc"
)

URL = (
    "https://naif.jpl.nasa.gov/pub/naif/"
    "generic_kernels/pck/"
    "earth_1962_260806_2126_combined.bpc"
)

EXPECTED_SHA256 = (
    "CC87AD1A495CF598800BA403763D350"
    "F087AC0B97DA9FEC603278A3864C6A53E"
)


def sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as f:
        while True:
            chunk = f.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return (
        digest.hexdigest()
        .upper()
    )


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        / FILENAME
    )

    if output_path.exists():
        existing_hash = sha256(
            output_path
        )

        if (
            existing_hash
            == EXPECTED_SHA256
        ):
            print()
            print(
                "Earth orientation kernel "
                "already present."
            )

            print(
                f"File: "
                f"{output_path.relative_to(ROOT)}"
            )

            print(
                f"SHA256: "
                f"{existing_hash}"
            )

            return

        raise SystemExit(
            "Existing Earth orientation "
            "kernel has unexpected SHA256:\n"
            f"{existing_hash}"
        )

    print(
        "Downloading:"
    )

    print(
        URL
    )

    urllib.request.urlretrieve(
        URL,
        output_path,
    )

    observed_hash = sha256(
        output_path
    )

    if (
        observed_hash
        != EXPECTED_SHA256
    ):
        output_path.unlink(
            missing_ok=True
        )

        raise SystemExit(
            "Downloaded Earth orientation "
            "kernel failed SHA256 validation.\n"
            f"Expected: {EXPECTED_SHA256}\n"
            f"Observed: {observed_hash}"
        )

    print()
    print(
        "Earth orientation kernel "
        "downloaded and verified."
    )

    print(
        f"File: "
        f"{output_path.relative_to(ROOT)}"
    )

    print(
        f"SHA256: "
        f"{observed_hash}"
    )


if __name__ == "__main__":
    main()
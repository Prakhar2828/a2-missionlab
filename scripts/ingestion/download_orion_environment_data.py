from __future__ import annotations

import hashlib
import re
import shutil
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    ROOT
    / "data"
    / "raw"
    / "pds"
    / "artemis2"
    / "orion_environment"
)

BASE_URL = (
    "https://pds-geosciences.wustl.edu/"
    "artemis2/"
    "urn-nasa-pds-artemis2_mission/"
    "data_orion_environment/"
)

BUNDLE_MD5_URL = (
    "https://pds-geosciences.wustl.edu/"
    "artemis2/"
    "urn-nasa-pds-artemis2_mission/"
    "urn-nasa-pds-artemis2_mission.md5"
)

MD5_MANIFEST_FILENAME = (
    "urn-nasa-pds-artemis2_mission.md5"
)

FILES = {
    "art002_086-162546_111-205046_hobo1104_raw_v01.csv": {
        "expected_size": 1702078,
        "logger": "SN 1104",
        "product_type": "CSV",
    },
    "art002_086-162546_111-205046_hobo1104_raw_v01.xml": {
        "expected_size": 7585,
        "logger": "SN 1104",
        "product_type": "PDS4_LABEL",
    },
    "art002_086-162926_111-203826_hobo1105_raw_v01.csv": {
        "expected_size": 1697492,
        "logger": "SN 1105",
        "product_type": "CSV",
    },
    "art002_086-162926_111-203826_hobo1105_raw_v01.xml": {
        "expected_size": 7670,
        "logger": "SN 1105",
        "product_type": "PDS4_LABEL",
    },
    "collection_data_orion_environment.xml": {
        "expected_size": 5261,
        "logger": None,
        "product_type": "PDS4_COLLECTION_LABEL",
    },
    "collection_data_orion_environment_inventory.csv": {
        "expected_size": 204,
        "logger": None,
        "product_type": "PDS4_COLLECTION_INVENTORY",
    },
}


def md5(
    path: Path,
) -> str:
    digest = hashlib.md5()

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
        .lower()
    )


def download_file(
    url: str,
    destination: Path,
):
    temporary = (
        destination
        .with_suffix(
            destination.suffix
            + ".part"
        )
    )

    temporary.unlink(
        missing_ok=True
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "A2-MissionLab/1.0 "
                "NASA-PDS-public-data-ingestion"
            )
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=120,
    ) as response:
        with temporary.open(
            "wb"
        ) as output:
            shutil.copyfileobj(
                response,
                output,
            )

    temporary.replace(
        destination
    )


def download_md5_manifest():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        OUTPUT_DIR
        / MD5_MANIFEST_FILENAME
    )

    print()
    print(
        "Downloading NASA PDS bundle "
        "checksum manifest..."
    )

    download_file(
        BUNDLE_MD5_URL,
        path,
    )

    print(
        f"Saved: "
        f"{path.relative_to(ROOT)}"
    )

    return path


def extract_expected_md5(
    manifest_text: str,
    filename: str,
) -> str | None:
    for line in (
        manifest_text.splitlines()
    ):
        if filename not in line:
            continue

        match = re.search(
            r"\b[0-9a-fA-F]{32}\b",
            line,
        )

        if match:
            return (
                match.group(0)
                .lower()
            )

    return None


def validate_file(
    path: Path,
    expected_size: int,
    expected_md5: str | None,
):
    observed_size = (
        path.stat().st_size
    )

    if (
        observed_size
        != expected_size
    ):
        return (
            False,
            (
                "SIZE_MISMATCH "
                f"expected={expected_size} "
                f"observed={observed_size}"
            ),
        )

    if expected_md5:
        observed_md5 = md5(
            path
        )

        if (
            observed_md5
            != expected_md5
        ):
            return (
                False,
                (
                    "MD5_MISMATCH "
                    f"expected={expected_md5} "
                    f"observed={observed_md5}"
                ),
            )

    return (
        True,
        "PASS",
    )


def main():
    print()
    print(
        "A2 MissionLab — "
        "Artemis II Orion Environment "
        "PDS Downloader"
    )
    print(
        "=" * 72
    )

    print()
    print(
        "Source:"
    )
    print(
        "  NASA Planetary Data System"
    )
    print(
        "  Artemis II Mission Bundle"
    )

    print()
    print(
        "Collection:"
    )
    print(
        "  Orion Environment Data"
    )

    print()
    print(
        "Released logger products:"
    )
    print(
        "  SN 1104"
    )
    print(
        "  SN 1105"
    )

    print()
    print(
        "Measured quantities:"
    )
    print(
        "  temperature"
    )
    print(
        "  relative humidity"
    )
    print(
        "  dew point"
    )

    print()
    print(
        "Nominal cadence:"
    )
    print(
        "  60 seconds"
    )

    manifest_path = (
        download_md5_manifest()
    )

    manifest_text = (
        manifest_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    print()
    print(
        "Downloading and validating "
        "PDS products..."
    )

    downloaded = 0
    reused = 0

    results = []

    for filename, metadata in (
        FILES.items()
    ):
        expected_size = (
            metadata[
                "expected_size"
            ]
        )

        expected_md5 = (
            extract_expected_md5(
                manifest_text,
                filename,
            )
        )

        destination = (
            OUTPUT_DIR
            / filename
        )

        url = (
            BASE_URL
            + filename
        )

        if destination.exists():
            valid, reason = (
                validate_file(
                    destination,
                    expected_size,
                    expected_md5,
                )
            )

            if valid:
                print()
                print(
                    f"Already present: "
                    f"{filename}"
                )

                reused += 1

                results.append(
                    (
                        filename,
                        "PASS",
                        expected_md5,
                    )
                )

                continue

            print()
            print(
                f"Existing file failed "
                f"validation:"
            )
            print(
                f"  {filename}"
            )
            print(
                f"  {reason}"
            )
            print(
                "Removing invalid local "
                "copy and redownloading."
            )

            destination.unlink()

        print()
        print(
            f"Downloading:"
        )
        print(
            f"  {filename}"
        )

        download_file(
            url,
            destination,
        )

        valid, reason = (
            validate_file(
                destination,
                expected_size,
                expected_md5,
            )
        )

        if not valid:
            destination.unlink(
                missing_ok=True
            )

            raise SystemExit(
                "\nNASA PDS product failed "
                "post-download validation:\n"
                f"{filename}\n"
                f"{reason}"
            )

        downloaded += 1

        results.append(
            (
                filename,
                "PASS",
                expected_md5,
            )
        )

    print()
    print(
        "=" * 72
    )
    print(
        "ORION ENVIRONMENT DOWNLOAD COMPLETE"
    )
    print(
        "=" * 72
    )

    print()
    print(
        f"Downloaded: {downloaded}"
    )
    print(
        f"Reused:     {reused}"
    )
    print(
        f"Products:   {len(FILES)}"
    )

    print()
    print(
        "Validation:"
    )

    for (
        filename,
        status,
        expected_md5,
    ) in results:
        checksum_status = (
            expected_md5
            if expected_md5
            else (
                "checksum not located "
                "in bundle manifest; "
                "size validated"
            )
        )

        print()
        print(
            f"  {status}  {filename}"
        )
        print(
            f"        MD5: "
            f"{checksum_status}"
        )

    print()
    print(
        "Local source directory:"
    )
    print(
        "  "
        + str(
            OUTPUT_DIR.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "Evidence boundary:"
    )
    print(
        "  These HOBO measurements "
        "characterize Orion storage "
        "locker environments."
    )
    print(
        "  They are not a complete "
        "Orion ECLSS telemetry stream."
    )


if __name__ == "__main__":
    main()
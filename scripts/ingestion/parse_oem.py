from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path


RAW_ZIP = Path("data/raw/arow/all-artemis-ii-oem-files.zip")
OUTPUT_DIR = Path("data/processed/trajectory")


def parse_oem_text(text: str) -> tuple[dict, list[dict]]:
    metadata = {}
    states = []

    in_metadata = False

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line == "META_START":
            in_metadata = True
            continue

        if line == "META_STOP":
            in_metadata = False
            continue

        if in_metadata and "=" in line:
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()
            continue

        if line.startswith("COMMENT"):
            continue

        if line.startswith("CCSDS_OEM_VERS"):
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()
            continue

        if line.startswith("CREATION_DATE"):
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()
            continue

        if line.startswith("ORIGINATOR"):
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()
            continue

        if line.startswith("2026-"):
            parts = line.split()

            if len(parts) < 7:
                continue

            states.append(
                {
                    "timestamp_utc": parts[0],
                    "x_km": float(parts[1]),
                    "y_km": float(parts[2]),
                    "z_km": float(parts[3]),
                    "vx_km_s": float(parts[4]),
                    "vy_km_s": float(parts[5]),
                    "vz_km_s": float(parts[6]),
                }
            )

    return metadata, states


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []

    with zipfile.ZipFile(RAW_ZIP) as outer_zip:
        for nested_name in outer_zip.namelist():
            if "Post-RTC3 to EI" in nested_name:
                print(f"Skipping non-OEM entry file: {nested_name}")
                continue

            nested_bytes = outer_zip.read(nested_name)

            with zipfile.ZipFile(io.BytesIO(nested_bytes)) as inner_zip:
                inner_name = inner_zip.namelist()[0]

                if not inner_name.lower().endswith(".asc"):
                    continue

                text = inner_zip.read(inner_name).decode("utf-8")

                metadata, states = parse_oem_text(text)

                stem = Path(inner_name).stem

                csv_path = OUTPUT_DIR / f"{stem}.csv"
                metadata_path = OUTPUT_DIR / f"{stem}.metadata.json"

                with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.DictWriter(
                        csv_file,
                        fieldnames=[
                            "timestamp_utc",
                            "x_km",
                            "y_km",
                            "z_km",
                            "vx_km_s",
                            "vy_km_s",
                            "vz_km_s",
                        ],
                    )

                    writer.writeheader()
                    writer.writerows(states)

                with metadata_path.open("w", encoding="utf-8") as metadata_file:
                    json.dump(metadata, metadata_file, indent=2)

                manifest.append(
                    {
                        "source_archive": nested_name,
                        "source_file": inner_name,
                        "output_csv": str(csv_path),
                        "metadata_file": str(metadata_path),
                        "state_count": len(states),
                        "start_time": metadata.get("START_TIME"),
                        "stop_time": metadata.get("STOP_TIME"),
                        "reference_frame": metadata.get("REF_FRAME"),
                        "time_system": metadata.get("TIME_SYSTEM"),
                        "center": metadata.get("CENTER_NAME"),
                        "originator": metadata.get("ORIGINATOR"),
                    }
                )

                print(
                    f"Parsed {inner_name}: "
                    f"{len(states)} state vectors"
                )

    manifest_path = OUTPUT_DIR / "manifest.json"

    with manifest_path.open("w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, indent=2)

    print()
    print(f"Wrote manifest: {manifest_path}")
    print(f"Parsed {len(manifest)} OEM trajectory products.")


if __name__ == "__main__":
    main()
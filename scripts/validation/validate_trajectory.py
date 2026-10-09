from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path


TRAJECTORY_DIR = Path("data/processed/trajectory")
MANIFEST_PATH = TRAJECTORY_DIR / "manifest.json"


REQUIRED_METADATA = {
    "CCSDS_OEM_VERS",
    "CREATION_DATE",
    "ORIGINATOR",
    "OBJECT_NAME",
    "CENTER_NAME",
    "REF_FRAME",
    "TIME_SYSTEM",
    "START_TIME",
    "STOP_TIME",
}


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_product(product: dict) -> list[str]:
    errors = []

    csv_path = Path(product["output_csv"])
    metadata_path = Path(product["metadata_file"])

    if not csv_path.exists():
        return [f"Missing CSV: {csv_path}"]

    if not metadata_path.exists():
        return [f"Missing metadata: {metadata_path}"]

    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)

    missing_metadata = REQUIRED_METADATA - metadata.keys()

    if missing_metadata:
        errors.append(
            f"{csv_path.name}: missing metadata {sorted(missing_metadata)}"
        )

    if metadata.get("CENTER_NAME") != "EARTH":
        errors.append(
            f"{csv_path.name}: unexpected center "
            f"{metadata.get('CENTER_NAME')}"
        )

    if metadata.get("REF_FRAME") != "EME2000":
        errors.append(
            f"{csv_path.name}: unexpected frame "
            f"{metadata.get('REF_FRAME')}"
        )

    if metadata.get("TIME_SYSTEM") != "UTC":
        errors.append(
            f"{csv_path.name}: unexpected time system "
            f"{metadata.get('TIME_SYSTEM')}"
        )

    rows = []

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if len(rows) != product["state_count"]:
        errors.append(
            f"{csv_path.name}: manifest says "
            f"{product['state_count']} rows but CSV has {len(rows)}"
        )

    if not rows:
        errors.append(f"{csv_path.name}: contains no state vectors")
        return errors

    timestamps = []
    previous_timestamp = None

    min_radius = math.inf
    max_radius = -math.inf
    min_speed = math.inf
    max_speed = -math.inf

    for index, row in enumerate(rows, start=2):
        timestamp = parse_timestamp(row["timestamp_utc"])

        if previous_timestamp is not None:
            if timestamp <= previous_timestamp:
                errors.append(
                    f"{csv_path.name}: timestamps not strictly "
                    f"increasing at CSV line {index}"
                )

        previous_timestamp = timestamp
        timestamps.append(timestamp)

        try:
            x = float(row["x_km"])
            y = float(row["y_km"])
            z = float(row["z_km"])

            vx = float(row["vx_km_s"])
            vy = float(row["vy_km_s"])
            vz = float(row["vz_km_s"])

        except ValueError:
            errors.append(
                f"{csv_path.name}: non-numeric state at line {index}"
            )
            continue

        values = [x, y, z, vx, vy, vz]

        if not all(math.isfinite(value) for value in values):
            errors.append(
                f"{csv_path.name}: non-finite state at line {index}"
            )
            continue

        radius = math.sqrt(x**2 + y**2 + z**2)
        speed = math.sqrt(vx**2 + vy**2 + vz**2)

        min_radius = min(min_radius, radius)
        max_radius = max(max_radius, radius)

        min_speed = min(min_speed, speed)
        max_speed = max(max_speed, speed)

    metadata_start = parse_timestamp(metadata["START_TIME"])
    metadata_stop = parse_timestamp(metadata["STOP_TIME"])

    if timestamps[0] != metadata_start:
        errors.append(
            f"{csv_path.name}: first state does not match START_TIME"
        )

    if timestamps[-1] != metadata_stop:
        errors.append(
            f"{csv_path.name}: final state does not match STOP_TIME"
        )

    print(
        f"{csv_path.name}\n"
        f"  states: {len(rows)}\n"
        f"  start:  {timestamps[0].isoformat()}\n"
        f"  stop:   {timestamps[-1].isoformat()}\n"
        f"  Earth-centered radius: "
        f"{min_radius:,.1f} to {max_radius:,.1f} km\n"
        f"  inertial speed: "
        f"{min_speed:.3f} to {max_speed:.3f} km/s\n"
    )

    return errors


def main() -> None:
    if not MANIFEST_PATH.exists():
        raise SystemExit(
            f"Manifest not found: {MANIFEST_PATH}"
        )

    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    all_errors = []

    for product in manifest:
        all_errors.extend(validate_product(product))

    if all_errors:
        print("VALIDATION FAILED\n")

        for error in all_errors:
            print(f"- {error}")

        raise SystemExit(1)

    print(
        f"OK: {len(manifest)} Artemis II OEM trajectory "
        "products validated."
    )


if __name__ == "__main__":
    main()
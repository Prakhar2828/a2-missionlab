from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path


CONFIG_PATH = Path("data/config/mission.json")
TRAJECTORY_DIR = Path("data/processed/trajectory")


def parse_utc(value: str) -> datetime:
    value = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def format_met(seconds: float) -> str:
    total = int(round(seconds))

    days, remainder = divmod(total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"


def main() -> None:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = json.load(f)

    launch_epoch = parse_utc(config["launch_epoch_utc"])

    input_path = TRAJECTORY_DIR / config["primary_oem"]
    output_path = TRAJECTORY_DIR / "primary_trajectory.csv"

    if not input_path.exists():
        raise SystemExit(f"Missing source trajectory: {input_path}")

    processed = []

    with input_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            timestamp = parse_utc(row["timestamp_utc"])

            x = float(row["x_km"])
            y = float(row["y_km"])
            z = float(row["z_km"])

            vx = float(row["vx_km_s"])
            vy = float(row["vy_km_s"])
            vz = float(row["vz_km_s"])

            radius = math.sqrt(x**2 + y**2 + z**2)
            speed = math.sqrt(vx**2 + vy**2 + vz**2)

            radial_velocity = (
                x * vx + y * vy + z * vz
            ) / radius

            met_seconds = (timestamp - launch_epoch).total_seconds()

            processed.append(
                {
                    **row,
                    "met_seconds": round(met_seconds, 3),
                    "met": format_met(met_seconds),
                    "earth_center_distance_km": round(radius, 6),
                    "inertial_speed_km_s": round(speed, 9),
                    "earth_radial_velocity_km_s": round(
                        radial_velocity, 9
                    ),
                }
            )

    fieldnames = list(processed[0].keys())

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed)

    closest = min(
        processed,
        key=lambda r: r["earth_center_distance_km"]
    )

    farthest = max(
        processed,
        key=lambda r: r["earth_center_distance_km"]
    )

    print(f"Primary OEM: {config['primary_oem']}")
    print(f"States: {len(processed)}")
    print()
    print("Closest Earth-center distance:")
    print(
        f"  {closest['earth_center_distance_km']:,.1f} km "
        f"at {closest['timestamp_utc']}"
    )
    print()
    print("Maximum Earth-center distance:")
    print(
        f"  {farthest['earth_center_distance_km']:,.1f} km "
        f"at {farthest['timestamp_utc']}"
    )
    print()
    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
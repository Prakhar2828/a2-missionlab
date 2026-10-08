from __future__ import annotations

import csv
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


TRAJECTORY_PATH = Path(
    "data/processed/trajectory/trajectory_with_lunar_geometry.csv"
)

PERICYNTHION_PATH = Path(
    "data/processed/trajectory/lunar_closest_approach.json"
)

OUTPUT_CSV = Path(
    "data/processed/trajectory/trajectory_with_mission_phases.csv"
)

OUTPUT_SUMMARY = Path(
    "data/processed/trajectory/mission_phase_summary.json"
)

# NASA-reported Artemis II lunar sphere-of-influence boundary.
NASA_LUNAR_SOI_MILES = 41072.0

# Exact international mile -> kilometer conversion.
MILES_TO_KM = 1.609344

NASA_LUNAR_SOI_KM = (
    NASA_LUNAR_SOI_MILES * MILES_TO_KM
)


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def interpolate_crossing(
    row0: dict,
    row1: dict,
    threshold_km: float,
) -> datetime:

    t0 = parse_utc(row0["timestamp_utc"])
    t1 = parse_utc(row1["timestamp_utc"])

    d0 = float(row0["orion_moon_distance_km"])
    d1 = float(row1["orion_moon_distance_km"])

    if d1 == d0:
        return t0

    fraction = (
        threshold_km - d0
    ) / (
        d1 - d0
    )

    duration = (t1 - t0).total_seconds()

    return t0 + timedelta(
        seconds=fraction * duration
    )


def find_soi_crossings(rows: list[dict]):
    crossings = []

    for index in range(1, len(rows)):
        previous = rows[index - 1]
        current = rows[index]

        previous_distance = float(
            previous["orion_moon_distance_km"]
        )

        current_distance = float(
            current["orion_moon_distance_km"]
        )

        previous_inside = (
            previous_distance <= NASA_LUNAR_SOI_KM
        )

        current_inside = (
            current_distance <= NASA_LUNAR_SOI_KM
        )

        if previous_inside != current_inside:
            crossing_time = interpolate_crossing(
                previous,
                current,
                NASA_LUNAR_SOI_KM,
            )

            crossing_type = (
                "ENTRY"
                if current_inside
                else "EXIT"
            )

            crossings.append(
                {
                    "type": crossing_type,
                    "timestamp_utc":
                        crossing_time.isoformat(),
                    "between_samples": [
                        previous["timestamp_utc"],
                        current["timestamp_utc"],
                    ],
                }
            )

    return crossings


def main():
    with TRAJECTORY_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        rows = list(csv.DictReader(f))

    with PERICYNTHION_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        pericynthion = json.load(f)

    if not rows:
        raise SystemExit("No trajectory rows found.")

    crossings = find_soi_crossings(rows)

    entries = [
        crossing
        for crossing in crossings
        if crossing["type"] == "ENTRY"
    ]

    exits = [
        crossing
        for crossing in crossings
        if crossing["type"] == "EXIT"
    ]

    if len(entries) != 1 or len(exits) != 1:
        raise SystemExit(
            "Expected exactly one lunar SOI entry "
            "and one lunar SOI exit."
        )

    entry_time = parse_utc(
        entries[0]["timestamp_utc"]
    )

    exit_time = parse_utc(
        exits[0]["timestamp_utc"]
    )

    pericynthion_time = parse_utc(
        pericynthion["timestamp_utc"]
    )

    output_rows = []

    for row in rows:
        timestamp = parse_utc(
            row["timestamp_utc"]
        )

        moon_distance = float(
            row["orion_moon_distance_km"]
        )

        inside_soi = (
            moon_distance <= NASA_LUNAR_SOI_KM
        )

        if timestamp < entry_time:
            phase = "OUTBOUND_TRANSIT"

        elif timestamp <= pericynthion_time:
            phase = "LUNAR_APPROACH"

        elif timestamp <= exit_time:
            phase = "LUNAR_DEPARTURE"

        else:
            phase = "TRANS_EARTH_RETURN"

        output_rows.append(
            {
                **row,
                "inside_nasa_lunar_soi":
                    str(inside_soi).lower(),
                "geometric_mission_phase":
                    phase,
            }
        )

    with OUTPUT_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(
                output_rows[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(output_rows)

    soi_duration_hours = (
        exit_time - entry_time
    ).total_seconds() / 3600.0

    farthest = max(
        rows,
        key=lambda row:
            float(
                row["earth_center_distance_km"]
            ),
    )

    summary = {
        "lunar_soi": {
            "boundary_miles":
                NASA_LUNAR_SOI_MILES,

            "boundary_km":
                NASA_LUNAR_SOI_KM,

            "boundary_provenance":
                "NASA_REPORTED",

            "derived_entry_utc":
                entry_time.isoformat(),

            "derived_exit_utc":
                exit_time.isoformat(),

            "duration_hours":
                soi_duration_hours,

            "crossing_method":
                "Linear interpolation between "
                "adjacent NASA OEM samples.",
        },

        "pericynthion": pericynthion,

        "maximum_earth_center_distance": {
            "timestamp_utc":
                farthest["timestamp_utc"],

            "distance_km":
                float(
                    farthest[
                        "earth_center_distance_km"
                    ]
                ),

            "provenance":
                "DERIVED_FROM_FLIGHT_DATA",
        },
    }

    with OUTPUT_SUMMARY.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary,
            f,
            indent=2,
        )

    print()
    print("Artemis II Geometric Mission Phases")
    print("-----------------------------------")

    print(
        f"NASA lunar SOI boundary: "
        f"{NASA_LUNAR_SOI_MILES:,.0f} mi "
        f"({NASA_LUNAR_SOI_KM:,.1f} km)"
    )

    print()
    print(
        f"Derived SOI entry: "
        f"{entry_time.isoformat()}"
    )

    print(
        f"Derived SOI exit:  "
        f"{exit_time.isoformat()}"
    )

    print(
        f"Time inside SOI:   "
        f"{soi_duration_hours:.2f} hours"
    )

    print()
    print(
        f"Pericynthion:      "
        f"{pericynthion_time.isoformat()}"
    )

    print()
    print(
        "Maximum Earth-center distance:"
    )

    print(
        f"  {float(farthest['earth_center_distance_km']):,.3f} km"
    )

    print(
        f"  {farthest['timestamp_utc']}"
    )

    print()
    print(f"Wrote: {OUTPUT_CSV}")
    print(f"Wrote: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()
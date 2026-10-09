from __future__ import annotations

import csv
import json
import math
import statistics
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path


TRAJECTORY_DIR = Path("data/processed/trajectory")
MANIFEST_PATH = TRAJECTORY_DIR / "manifest.json"
CONFIG_PATH = Path("data/config/mission.json")

OUTPUT_SUMMARY = (
    TRAJECTORY_DIR / "oem_comparison_summary.json"
)

OUTPUT_DETAIL = (
    TRAJECTORY_DIR / "oem_comparison_detail.csv"
)


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def magnitude(vector):
    return math.sqrt(
        sum(component**2 for component in vector)
    )


def percentile(values, fraction):
    if not values:
        return None

    ordered = sorted(values)

    index = (
        fraction * (len(ordered) - 1)
    )

    lower = int(math.floor(index))
    upper = int(math.ceil(index))

    if lower == upper:
        return ordered[lower]

    weight = index - lower

    return (
        ordered[lower] * (1 - weight)
        + ordered[upper] * weight
    )


def load_product(path: Path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        rows = list(csv.DictReader(f))

    times = [
        parse_utc(row["timestamp_utc"])
        for row in rows
    ]

    return rows, times


def state_from_row(row):
    position = [
        float(row["x_km"]),
        float(row["y_km"]),
        float(row["z_km"]),
    ]

    velocity = [
        float(row["vx_km_s"]),
        float(row["vy_km_s"]),
        float(row["vz_km_s"]),
    ]

    return position, velocity


def interpolate_state(
    rows,
    times,
    target_time,
):
    if (
        target_time < times[0]
        or target_time > times[-1]
    ):
        return None

    index = bisect_right(
        times,
        target_time,
    )

    if index == 0:
        return state_from_row(rows[0])

    if index >= len(rows):
        return state_from_row(rows[-1])

    row0 = rows[index - 1]
    row1 = rows[index]

    t0 = times[index - 1]
    t1 = times[index]

    if target_time == t0:
        return state_from_row(row0)

    if target_time == t1:
        return state_from_row(row1)

    total_seconds = (
        t1 - t0
    ).total_seconds()

    u = (
        target_time - t0
    ).total_seconds() / total_seconds

    p0, v0 = state_from_row(row0)
    p1, v1 = state_from_row(row1)

    h00 = 2 * u**3 - 3 * u**2 + 1
    h10 = u**3 - 2 * u**2 + u
    h01 = -2 * u**3 + 3 * u**2
    h11 = u**3 - u**2

    position = [
        h00 * p0[i]
        + h10 * total_seconds * v0[i]
        + h01 * p1[i]
        + h11 * total_seconds * v1[i]
        for i in range(3)
    ]

    dh00 = 6 * u**2 - 6 * u
    dh10 = 3 * u**2 - 4 * u + 1
    dh01 = -6 * u**2 + 6 * u
    dh11 = 3 * u**2 - 2 * u

    velocity = [
        (
            dh00 * p0[i]
            + dh10 * total_seconds * v0[i]
            + dh01 * p1[i]
            + dh11 * total_seconds * v1[i]
        )
        / total_seconds
        for i in range(3)
    ]

    return position, velocity


def summarize(records):
    if not records:
        return None

    position = [
        record["position_difference_km"]
        for record in records
    ]

    velocity = [
        record["velocity_difference_m_s"]
        for record in records
    ]

    return {
        "count": len(records),

        "position_difference_km": {
            "median": statistics.median(position),
            "p95": percentile(position, 0.95),
            "max": max(position),
        },

        "velocity_difference_m_s": {
            "median": statistics.median(velocity),
            "p95": percentile(velocity, 0.95),
            "max": max(velocity),
        },
    }


def main():
    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        manifest = json.load(f)

    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        config = json.load(f)

    reference_name = config["primary_oem"]

    reference_path = (
        TRAJECTORY_DIR / reference_name
    )

    reference_rows, reference_times = (
        load_product(reference_path)
    )

    detail_records = []
    summaries = []

    for product in manifest:
        path = Path(product["output_csv"])

        if path.name == reference_name:
            continue

        rows, times = load_product(path)

        metadata_path = Path(
            product["metadata_file"]
        )

        with metadata_path.open(
            "r",
            encoding="utf-8",
        ) as f:
            metadata = json.load(f)

        creation_time = parse_utc(
            metadata["CREATION_DATE"]
        )

        product_records = []

        for reference_row, target_time in zip(
            reference_rows,
            reference_times,
        ):
            comparison_state = (
                interpolate_state(
                    rows,
                    times,
                    target_time,
                )
            )

            if comparison_state is None:
                continue

            reference_position, reference_velocity = (
                state_from_row(reference_row)
            )

            comparison_position, comparison_velocity = (
                comparison_state
            )

            position_difference = magnitude(
                [
                    comparison_position[i]
                    - reference_position[i]
                    for i in range(3)
                ]
            )

            velocity_difference = (
                magnitude(
                    [
                        comparison_velocity[i]
                        - reference_velocity[i]
                        for i in range(3)
                    ]
                )
                * 1000.0
            )

            epoch_class = (
                "AT_OR_BEFORE_PRODUCT_CREATION"
                if target_time <= creation_time
                else "AFTER_PRODUCT_CREATION"
            )

            record = {
                "product":
                    path.name,

                "product_creation_utc":
                    creation_time.isoformat(),

                "comparison_timestamp_utc":
                    target_time.isoformat(),

                "epoch_class":
                    epoch_class,

                "position_difference_km":
                    position_difference,

                "velocity_difference_m_s":
                    velocity_difference,
            }

            product_records.append(record)
            detail_records.append(record)

        before_creation = [
            record
            for record in product_records
            if record["epoch_class"]
            == "AT_OR_BEFORE_PRODUCT_CREATION"
        ]

        after_creation = [
            record
            for record in product_records
            if record["epoch_class"]
            == "AFTER_PRODUCT_CREATION"
        ]

        summaries.append(
            {
                "product":
                    path.name,

                "creation_date":
                    metadata["CREATION_DATE"],

                "comparison_reference":
                    reference_name,

                "all_common_epochs":
                    summarize(product_records),

                "at_or_before_product_creation":
                    summarize(before_creation),

                "after_product_creation":
                    summarize(after_creation),
            }
        )

    with OUTPUT_DETAIL.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(
                detail_records[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(detail_records)

    with OUTPUT_SUMMARY.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            {
                "reference_product":
                    reference_name,

                "interpretation_warning":
                    (
                        "Differences are solution-to-solution "
                        "differences, not navigation errors. "
                        "The latest released OEM is used only "
                        "as the comparison reference."
                    ),

                "products":
                    summaries,
            },
            f,
            indent=2,
        )

    print()
    print("Artemis II OEM Solution Comparison")
    print("----------------------------------")

    print(
        f"Reference: {reference_name}"
    )

    print()

    for summary in summaries:
        all_stats = summary[
            "all_common_epochs"
        ]

        after_stats = summary[
            "after_product_creation"
        ]

        print(summary["product"])

        print(
            "  Median position difference: "
            f"{all_stats['position_difference_km']['median']:,.3f} km"
        )

        print(
            "  95th percentile:            "
            f"{all_stats['position_difference_km']['p95']:,.3f} km"
        )

        print(
            "  Maximum:                    "
            f"{all_stats['position_difference_km']['max']:,.3f} km"
        )

        if after_stats:
            print(
                "  Post-creation median:       "
                f"{after_stats['position_difference_km']['median']:,.3f} km"
            )

        print()

    print(f"Wrote: {OUTPUT_DETAIL}")
    print(f"Wrote: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()
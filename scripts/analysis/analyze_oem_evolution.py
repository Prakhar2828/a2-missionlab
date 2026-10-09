from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


INPUT_PATH = Path(
    "data/processed/trajectory/oem_comparison_detail.csv"
)

OUTPUT_JSON = Path(
    "data/processed/trajectory/oem_evolution_analysis.json"
)

OUTPUT_PLOT = Path(
    "docs/assets/phase1f_oem_position_difference.svg"
)

# Numerical tolerance used to treat values as effectively identical.
EXACT_POSITION_TOLERANCE_KM = 1e-6
EXACT_VELOCITY_TOLERANCE_M_S = 1e-6

# Analysis threshold only.
# This is NOT a NASA-defined navigation threshold.
MEANINGFUL_POSITION_DIFFERENCE_KM = 1.0


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def median_or_none(values):
    if not values:
        return None

    return statistics.median(values)


def analyze_product(records):
    records = sorted(
        records,
        key=lambda r: r["timestamp"],
    )

    positions = [
        r["position_difference_km"]
        for r in records
    ]

    velocities = [
        r["velocity_difference_m_s"]
        for r in records
    ]

    before = [
        r
        for r in records
        if r["epoch_class"]
        == "AT_OR_BEFORE_PRODUCT_CREATION"
    ]

    after = [
        r
        for r in records
        if r["epoch_class"]
        == "AFTER_PRODUCT_CREATION"
    ]

    exact_matches = [
        r
        for r in records
        if (
            r["position_difference_km"]
            <= EXACT_POSITION_TOLERANCE_KM
            and
            r["velocity_difference_m_s"]
            <= EXACT_VELOCITY_TOLERANCE_M_S
        )
    ]

    meaningful = [
        r
        for r in records
        if r["position_difference_km"]
        >= MEANINGFUL_POSITION_DIFFERENCE_KM
    ]

    max_position_record = max(
        records,
        key=lambda r:
            r["position_difference_km"],
    )

    max_velocity_record = max(
        records,
        key=lambda r:
            r["velocity_difference_m_s"],
    )

    return {
        "common_epoch_count":
            len(records),

        "effectively_identical_epoch_count":
            len(exact_matches),

        "effectively_identical_percent":
            100.0
            * len(exact_matches)
            / len(records),

        "median_position_difference_km":
            statistics.median(positions),

        "median_velocity_difference_m_s":
            statistics.median(velocities),

        "before_or_at_creation": {
            "count":
                len(before),

            "median_position_difference_km":
                median_or_none(
                    [
                        r["position_difference_km"]
                        for r in before
                    ]
                ),

            "median_velocity_difference_m_s":
                median_or_none(
                    [
                        r["velocity_difference_m_s"]
                        for r in before
                    ]
                ),
        },

        "after_creation": {
            "count":
                len(after),

            "median_position_difference_km":
                median_or_none(
                    [
                        r["position_difference_km"]
                        for r in after
                    ]
                ),

            "median_velocity_difference_m_s":
                median_or_none(
                    [
                        r["velocity_difference_m_s"]
                        for r in after
                    ]
                ),
        },

        "maximum_position_difference": {
            "value_km":
                max_position_record[
                    "position_difference_km"
                ],

            "timestamp_utc":
                max_position_record[
                    "timestamp"
                ].isoformat(),
        },

        "maximum_velocity_difference": {
            "value_m_s":
                max_velocity_record[
                    "velocity_difference_m_s"
                ],

            "timestamp_utc":
                max_velocity_record[
                    "timestamp"
                ].isoformat(),
        },

        "meaningful_difference_threshold_km":
            MEANINGFUL_POSITION_DIFFERENCE_KM,

        "first_meaningful_difference_utc":
            (
                meaningful[0]["timestamp"].isoformat()
                if meaningful
                else None
            ),

        "last_meaningful_difference_utc":
            (
                meaningful[-1]["timestamp"].isoformat()
                if meaningful
                else None
            ),
    }


def build_plot(grouped_records):
    OUTPUT_PLOT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(13, 7)
    )

    for product, records in sorted(
        grouped_records.items()
    ):
        records = sorted(
            records,
            key=lambda r: r["timestamp"],
        )

        timestamps = [
            r["timestamp"]
            for r in records
        ]

        differences = [
            r["position_difference_km"]
            for r in records
        ]

        short_name = (
            product
            .replace("Artemis_II_OEM_", "")
            .replace(".csv", "")
            .replace("_", " ")
        )

        ax.plot(
            timestamps,
            differences,
            linewidth=1.2,
            label=short_name,
        )

    ax.axhline(
        MEANINGFUL_POSITION_DIFFERENCE_KM,
        linestyle="--",
        linewidth=1,
        label="1 km analysis threshold",
    )

    ax.set_title(
        "Artemis II Public OEM Solution Differences\n"
        "Relative to April 10 Public OEM"
    )

    ax.set_xlabel("UTC")
    ax.set_ylabel(
        "3-D Position Difference (km)"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(
            "%b %d",
            tz=timezone.utc,
        )
    )

    ax.legend(
        fontsize=7,
        loc="upper right",
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(
        OUTPUT_PLOT,
        format="svg",
        bbox_inches="tight",
    )

    plt.close(fig)


def main():
    if not INPUT_PATH.exists():
        raise SystemExit(
            f"Missing comparison data: {INPUT_PATH}\n"
            "Run compare_oem_products.py first."
        )

    grouped = defaultdict(list)

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            grouped[row["product"]].append(
                {
                    "timestamp":
                        parse_utc(
                            row[
                                "comparison_timestamp_utc"
                            ]
                        ),

                    "creation_time":
                        parse_utc(
                            row[
                                "product_creation_utc"
                            ]
                        ),

                    "epoch_class":
                        row["epoch_class"],

                    "position_difference_km":
                        float(
                            row[
                                "position_difference_km"
                            ]
                        ),

                    "velocity_difference_m_s":
                        float(
                            row[
                                "velocity_difference_m_s"
                            ]
                        ),
                }
            )

    analysis = {}

    print()
    print("Artemis II OEM Evolution Analysis")
    print("---------------------------------")
    print()

    for product, records in sorted(
        grouped.items()
    ):
        result = analyze_product(records)

        analysis[product] = result

        print(product)

        print(
            "  Common epochs:                "
            f"{result['common_epoch_count']}"
        )

        print(
            "  Effectively identical:        "
            f"{result['effectively_identical_percent']:.2f}%"
        )

        print(
            "  Median position difference:   "
            f"{result['median_position_difference_km']:.3f} km"
        )

        before_value = (
            result[
                "before_or_at_creation"
            ][
                "median_position_difference_km"
            ]
        )

        after_value = (
            result[
                "after_creation"
            ][
                "median_position_difference_km"
            ]
        )

        print(
            "  Pre/at-creation median:        "
            + (
                f"{before_value:.3f} km"
                if before_value is not None
                else "N/A"
            )
        )

        print(
            "  Post-creation median:          "
            + (
                f"{after_value:.3f} km"
                if after_value is not None
                else "N/A"
            )
        )

        print(
            "  Maximum position difference:  "
            f"{result['maximum_position_difference']['value_km']:.3f} km"
        )

        print(
            "  At:                           "
            f"{result['maximum_position_difference']['timestamp_utc']}"
        )

        print(
            "  First >= 1 km difference:     "
            f"{result['first_meaningful_difference_utc']}"
        )

        print(
            "  Last >= 1 km difference:      "
            f"{result['last_meaningful_difference_utc']}"
        )

        print()

    OUTPUT_JSON.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            {
                "reference":
                    "April 10 public OEM",

                "exact_match_tolerances": {
                    "position_km":
                        EXACT_POSITION_TOLERANCE_KM,

                    "velocity_m_s":
                        EXACT_VELOCITY_TOLERANCE_M_S,
                },

                "meaningful_difference_threshold": {
                    "position_km":
                        MEANINGFUL_POSITION_DIFFERENCE_KM,

                    "interpretation":
                        (
                            "Analysis threshold only. "
                            "Not a NASA navigation, "
                            "flight-rule, or operational threshold."
                        ),
                },

                "products":
                    analysis,
            },
            f,
            indent=2,
        )

    build_plot(grouped)

    print(f"Wrote: {OUTPUT_JSON}")
    print(f"Wrote: {OUTPUT_PLOT}")


if __name__ == "__main__":
    main()
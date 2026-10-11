from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "eclss"
)

INPUT_CSV = (
    INPUT_DIR
    / "orion_environment_normalized.csv"
)

INPUT_METADATA = (
    INPUT_DIR
    / "orion_environment_metadata.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "eclss"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "eclss"
)

PERIOD_CSV = (
    OUTPUT_DIR
    / "orion_environment_period_summary.csv"
)

DAILY_CSV = (
    OUTPUT_DIR
    / "orion_environment_daily_summary.csv"
)

LOGGER_COMPARISON_CSV = (
    OUTPUT_DIR
    / "orion_environment_logger_comparison.csv"
)

SUMMARY_JSON = (
    OUTPUT_DIR
    / "orion_environment_trend_summary.json"
)

TEMPERATURE_FIGURE = (
    ASSET_DIR
    / "phase3a2_temperature_trends.svg"
)

HUMIDITY_FIGURE = (
    ASSET_DIR
    / "phase3a2_humidity_trends.svg"
)

DEW_POINT_FIGURE = (
    ASSET_DIR
    / "phase3a2_dew_point_trends.svg"
)

LOGGER_DIFFERENCE_FIGURE = (
    ASSET_DIR
    / "phase3a2_logger_temperature_difference.svg"
)


EXPECTED_DATASET_ID = (
    "phase3a1_artemis_ii_"
    "orion_environment_normalized"
)

LOGGER_SERIALS = [
    "1104",
    "1105",
]

MISSION_PERIODS = [
    "PRELAUNCH",
    "IN_FLIGHT",
    "POSTFLIGHT",
]

MEASUREMENTS = [
    "temperature_c",
    "relative_humidity_pct",
    "dew_point_c",
]

#
# The two HOBO logger series are each sampled
# every 60 seconds, but their timestamp grids
# are offset.
#
# SN 1104 timestamps occur at second :46.
# SN 1105 timestamps occur at second :26.
#
# Therefore exact timestamp equality does not
# occur. A nearest-time comparison within
# +/-30 seconds provides one-to-one temporal
# pairing without claiming simultaneous
# measurements.
#
PAIRING_TOLERANCE_SECONDS = 30.0


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 3A.2 ANALYSIS FAILED: "
        f"{message}"
    )


def parse_utc(
    value: str,
) -> datetime:
    try:
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

    except ValueError:
        fail(
            "invalid UTC timestamp: "
            f"{value}"
        )

        raise


def iso_z(
    value: datetime,
) -> str:
    return (
        value.isoformat(
            timespec="seconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def require_finite(
    value: str,
    field: str,
) -> float:
    try:
        parsed = float(
            value
        )

    except ValueError:
        fail(
            f"{field} is not numeric: "
            f"{value!r}"
        )

    if not math.isfinite(
        parsed
    ):
        fail(
            f"{field} is not finite"
        )

    return parsed


def percentile(
    values: list[float],
    fraction: float,
) -> float:
    if not values:
        fail(
            "cannot calculate percentile "
            "for empty sequence"
        )

    ordered = sorted(
        values
    )

    if len(
        ordered
    ) == 1:
        return ordered[0]

    position = (
        fraction
        * (
            len(
                ordered
            )
            - 1
        )
    )

    lower = int(
        math.floor(
            position
        )
    )

    upper = int(
        math.ceil(
            position
        )
    )

    if lower == upper:
        return ordered[
            lower
        ]

    fraction_above = (
        position
        - lower
    )

    return (
        ordered[
            lower
        ]
        * (
            1.0
            - fraction_above
        )
        + ordered[
            upper
        ]
        * fraction_above
    )


def summarize_values(
    values: list[float],
) -> dict:
    if not values:
        fail(
            "cannot summarize "
            "empty measurement set"
        )

    return {
        "count": len(
            values
        ),
        "minimum": min(
            values
        ),
        "p05": percentile(
            values,
            0.05,
        ),
        "median": statistics.median(
            values
        ),
        "mean": statistics.fmean(
            values
        ),
        "p95": percentile(
            values,
            0.95,
        ),
        "maximum": max(
            values
        ),
        "standard_deviation": (
            statistics.pstdev(
                values
            )
        ),
    }


def load_inputs():
    if not INPUT_CSV.exists():
        fail(
            "missing normalized CSV: "
            f"{INPUT_CSV}"
        )

    if not INPUT_METADATA.exists():
        fail(
            "missing normalization "
            "metadata JSON"
        )

    with INPUT_METADATA.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        metadata = json.load(
            f
        )

    if (
        metadata.get(
            "dataset_id"
        )
        != EXPECTED_DATASET_ID
    ):
        fail(
            "unexpected normalization "
            "dataset ID"
        )

    with INPUT_CSV.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(
            csv.DictReader(
                f
            )
        )

    if not rows:
        fail(
            "normalized environment "
            "dataset is empty"
        )

    return (
        rows,
        metadata,
    )


def build_period_summary(
    rows: list[dict],
):
    grouped = defaultdict(
        lambda: defaultdict(
            list
        )
    )

    for row in rows:
        logger = row[
            "logger_serial"
        ]

        period = row[
            "mission_period"
        ]

        if logger not in (
            LOGGER_SERIALS
        ):
            fail(
                "unexpected logger: "
                f"{logger}"
            )

        if period not in (
            MISSION_PERIODS
        ):
            fail(
                "unexpected mission period: "
                f"{period}"
            )

        for measurement in (
            MEASUREMENTS
        ):
            grouped[
                (
                    logger,
                    period,
                )
            ][
                measurement
            ].append(
                require_finite(
                    row[
                        measurement
                    ],
                    measurement,
                )
            )

    output_rows = []

    nested_summary = {}

    for logger in (
        LOGGER_SERIALS
    ):
        nested_summary[
            logger
        ] = {}

        for period in (
            MISSION_PERIODS
        ):
            key = (
                logger,
                period,
            )

            if key not in grouped:
                fail(
                    "missing logger/period "
                    f"group: {key}"
                )

            nested_summary[
                logger
            ][
                period
            ] = {}

            for measurement in (
                MEASUREMENTS
            ):
                summary = (
                    summarize_values(
                        grouped[
                            key
                        ][
                            measurement
                        ]
                    )
                )

                nested_summary[
                    logger
                ][
                    period
                ][
                    measurement
                ] = summary

                output_rows.append(
                    {
                        "logger_serial": (
                            logger
                        ),
                        "mission_period": (
                            period
                        ),
                        "measurement": (
                            measurement
                        ),
                        "count": (
                            summary[
                                "count"
                            ]
                        ),
                        "minimum": (
                            summary[
                                "minimum"
                            ]
                        ),
                        "p05": (
                            summary[
                                "p05"
                            ]
                        ),
                        "median": (
                            summary[
                                "median"
                            ]
                        ),
                        "mean": (
                            summary[
                                "mean"
                            ]
                        ),
                        "p95": (
                            summary[
                                "p95"
                            ]
                        ),
                        "maximum": (
                            summary[
                                "maximum"
                            ]
                        ),
                        "standard_deviation": (
                            summary[
                                "standard_deviation"
                            ]
                        ),
                        "provenance": (
                            "MISSIONLAB_DERIVED_"
                            "DESCRIPTIVE_STATISTICS"
                        ),
                    }
                )

    return (
        output_rows,
        nested_summary,
    )


def build_daily_summary(
    rows: list[dict],
):
    grouped = defaultdict(
        lambda: defaultdict(
            list
        )
    )

    period_counts = defaultdict(
        lambda: defaultdict(
            int
        )
    )

    for row in rows:
        logger = row[
            "logger_serial"
        ]

        timestamp = parse_utc(
            row[
                "timestamp_utc"
            ]
        )

        date_utc = (
            timestamp.date()
            .isoformat()
        )

        key = (
            logger,
            date_utc,
        )

        period_counts[
            key
        ][
            row[
                "mission_period"
            ]
        ] += 1

        for measurement in (
            MEASUREMENTS
        ):
            grouped[
                key
            ][
                measurement
            ].append(
                require_finite(
                    row[
                        measurement
                    ],
                    measurement,
                )
            )

    output_rows = []

    for (
        logger,
        date_utc,
    ) in sorted(
        grouped
    ):
        key = (
            logger,
            date_utc,
        )

        measurements = grouped[
            key
        ]

        temp = summarize_values(
            measurements[
                "temperature_c"
            ]
        )

        rh = summarize_values(
            measurements[
                "relative_humidity_pct"
            ]
        )

        dew = summarize_values(
            measurements[
                "dew_point_c"
            ]
        )

        dominant_period = max(
            period_counts[
                key
            ],
            key=(
                period_counts[
                    key
                ].get
            ),
        )

        output_rows.append(
            {
                "logger_serial": (
                    logger
                ),
                "date_utc": (
                    date_utc
                ),
                "dominant_mission_period": (
                    dominant_period
                ),
                "records": (
                    temp[
                        "count"
                    ]
                ),
                "temperature_mean_c": (
                    temp[
                        "mean"
                    ]
                ),
                "temperature_min_c": (
                    temp[
                        "minimum"
                    ]
                ),
                "temperature_max_c": (
                    temp[
                        "maximum"
                    ]
                ),
                "relative_humidity_mean_pct": (
                    rh[
                        "mean"
                    ]
                ),
                "relative_humidity_min_pct": (
                    rh[
                        "minimum"
                    ]
                ),
                "relative_humidity_max_pct": (
                    rh[
                        "maximum"
                    ]
                ),
                "dew_point_mean_c": (
                    dew[
                        "mean"
                    ]
                ),
                "dew_point_min_c": (
                    dew[
                        "minimum"
                    ]
                ),
                "dew_point_max_c": (
                    dew[
                        "maximum"
                    ]
                ),
                "provenance": (
                    "MISSIONLAB_DERIVED_"
                    "DAILY_STATISTICS"
                ),
            }
        )

    return output_rows


def get_inflight_logger_rows(
    rows: list[dict],
    logger_serial: str,
) -> list[dict]:
    selected = [
        row
        for row in rows
        if (
            row[
                "logger_serial"
            ]
            == logger_serial
            and row[
                "mission_period"
            ]
            == "IN_FLIGHT"
        )
    ]

    selected.sort(
        key=lambda row: (
            row[
                "timestamp_utc"
            ]
        )
    )

    return selected


def pair_nearest_inflight_samples(
    rows: list[dict],
):
    rows_1104 = (
        get_inflight_logger_rows(
            rows,
            "1104",
        )
    )

    rows_1105 = (
        get_inflight_logger_rows(
            rows,
            "1105",
        )
    )

    if not rows_1104:
        fail(
            "no inflight records found "
            "for SN 1104"
        )

    if not rows_1105:
        fail(
            "no inflight records found "
            "for SN 1105"
        )

    index_1104 = 0
    index_1105 = 0

    pairs = []

    unmatched_1104 = 0
    unmatched_1105 = 0

    while (
        index_1104
        < len(
            rows_1104
        )
        and index_1105
        < len(
            rows_1105
        )
    ):
        row_1104 = (
            rows_1104[
                index_1104
            ]
        )

        row_1105 = (
            rows_1105[
                index_1105
            ]
        )

        time_1104 = parse_utc(
            row_1104[
                "timestamp_utc"
            ]
        )

        time_1105 = parse_utc(
            row_1105[
                "timestamp_utc"
            ]
        )

        offset_seconds = (
            time_1105
            - time_1104
        ).total_seconds()

        if (
            abs(
                offset_seconds
            )
            <= PAIRING_TOLERANCE_SECONDS
        ):
            pairs.append(
                (
                    row_1104,
                    row_1105,
                    offset_seconds,
                )
            )

            index_1104 += 1
            index_1105 += 1

        elif (
            time_1104
            < time_1105
        ):
            unmatched_1104 += 1
            index_1104 += 1

        else:
            unmatched_1105 += 1
            index_1105 += 1

    unmatched_1104 += (
        len(
            rows_1104
        )
        - index_1104
    )

    unmatched_1105 += (
        len(
            rows_1105
        )
        - index_1105
    )

    if not pairs:
        fail(
            "no near-synchronous "
            "inflight logger pairs found "
            f"within +/-"
            f"{PAIRING_TOLERANCE_SECONDS:.0f} s"
        )

    return (
        pairs,
        {
            "inflight_records_1104": (
                len(
                    rows_1104
                )
            ),
            "inflight_records_1105": (
                len(
                    rows_1105
                )
            ),
            "paired_records": (
                len(
                    pairs
                )
            ),
            "unmatched_records_1104": (
                unmatched_1104
            ),
            "unmatched_records_1105": (
                unmatched_1105
            ),
        },
    )


def build_logger_comparison(
    rows: list[dict],
):
    (
        pairs,
        pairing_counts,
    ) = pair_nearest_inflight_samples(
        rows
    )

    output_rows = []

    time_offsets = []

    absolute_time_offsets = []

    temperature_differences = []

    humidity_differences = []

    dew_point_differences = []

    for (
        row_1104,
        row_1105,
        offset_seconds,
    ) in pairs:
        temp_1104 = require_finite(
            row_1104[
                "temperature_c"
            ],
            "temperature_c",
        )

        temp_1105 = require_finite(
            row_1105[
                "temperature_c"
            ],
            "temperature_c",
        )

        rh_1104 = require_finite(
            row_1104[
                "relative_humidity_pct"
            ],
            "relative_humidity_pct",
        )

        rh_1105 = require_finite(
            row_1105[
                "relative_humidity_pct"
            ],
            "relative_humidity_pct",
        )

        dew_1104 = require_finite(
            row_1104[
                "dew_point_c"
            ],
            "dew_point_c",
        )

        dew_1105 = require_finite(
            row_1105[
                "dew_point_c"
            ],
            "dew_point_c",
        )

        temp_difference = (
            temp_1105
            - temp_1104
        )

        rh_difference = (
            rh_1105
            - rh_1104
        )

        dew_difference = (
            dew_1105
            - dew_1104
        )

        time_offsets.append(
            offset_seconds
        )

        absolute_time_offsets.append(
            abs(
                offset_seconds
            )
        )

        temperature_differences.append(
            temp_difference
        )

        humidity_differences.append(
            rh_difference
        )

        dew_point_differences.append(
            dew_difference
        )

        output_rows.append(
            {
                "timestamp_1104_utc": (
                    row_1104[
                        "timestamp_utc"
                    ]
                ),
                "timestamp_1105_utc": (
                    row_1105[
                        "timestamp_utc"
                    ]
                ),
                "time_offset_1105_minus_1104_seconds": (
                    offset_seconds
                ),
                "pairing_method": (
                    "NEAREST_TIME_WITHIN_30_SECONDS"
                ),
                "mission_elapsed_1104": (
                    row_1104[
                        "mission_elapsed"
                    ]
                ),
                "mission_elapsed_1105": (
                    row_1105[
                        "mission_elapsed"
                    ]
                ),
                "temperature_1104_c": (
                    temp_1104
                ),
                "temperature_1105_c": (
                    temp_1105
                ),
                "temperature_1105_minus_1104_c": (
                    temp_difference
                ),
                "relative_humidity_1104_pct": (
                    rh_1104
                ),
                "relative_humidity_1105_pct": (
                    rh_1105
                ),
                "relative_humidity_1105_minus_1104_pct": (
                    rh_difference
                ),
                "dew_point_1104_c": (
                    dew_1104
                ),
                "dew_point_1105_c": (
                    dew_1105
                ),
                "dew_point_1105_minus_1104_c": (
                    dew_difference
                ),
                "provenance": (
                    "MISSIONLAB_DERIVED_"
                    "NEAR_SYNCHRONOUS_COMPARISON"
                ),
            }
        )

    maximum_absolute_offset = max(
        absolute_time_offsets
    )

    if (
        maximum_absolute_offset
        > PAIRING_TOLERANCE_SECONDS
    ):
        fail(
            "paired logger sample exceeds "
            "pairing tolerance"
        )

    summary = {
        "pairing_method": (
            "NEAREST_TIME_ONE_TO_ONE"
        ),
        "pairing_tolerance_seconds": (
            PAIRING_TOLERANCE_SECONDS
        ),
        "exact_timestamp_matches_required": (
            False
        ),
        "measurements_are_simultaneous": (
            False
        ),
        "pairing_counts": (
            pairing_counts
        ),
        "time_offset_1105_minus_1104_seconds": (
            summarize_values(
                time_offsets
            )
        ),
        "absolute_time_offset_seconds": (
            summarize_values(
                absolute_time_offsets
            )
        ),
        "temperature_1105_minus_1104_c": (
            summarize_values(
                temperature_differences
            )
        ),
        "relative_humidity_1105_minus_1104_pct": (
            summarize_values(
                humidity_differences
            )
        ),
        "dew_point_1105_minus_1104_c": (
            summarize_values(
                dew_point_differences
            )
        ),
    }

    return (
        output_rows,
        summary,
    )


def write_csv(
    path: Path,
    rows: list[dict],
):
    if not rows:
        fail(
            "cannot write empty CSV: "
            f"{path.name}"
        )

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(
                rows[0].keys()
            ),
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


def plot_measurement(
    rows: list[dict],
    measurement: str,
    ylabel: str,
    title: str,
    output_path: Path,
):
    series = {
        "1104": {
            "time": [],
            "value": [],
        },
        "1105": {
            "time": [],
            "value": [],
        },
    }

    for row in rows:
        if (
            row[
                "mission_period"
            ]
            != "IN_FLIGHT"
        ):
            continue

        logger = row[
            "logger_serial"
        ]

        series[
            logger
        ][
            "time"
        ].append(
            parse_utc(
                row[
                    "timestamp_utc"
                ]
            )
        )

        series[
            logger
        ][
            "value"
        ].append(
            float(
                row[
                    measurement
                ]
            )
        )

    fig, ax = plt.subplots(
        figsize=(
            11,
            5,
        )
    )

    for logger in (
        LOGGER_SERIALS
    ):
        ax.plot(
            series[
                logger
            ][
                "time"
            ],
            series[
                logger
            ][
                "value"
            ],
            linewidth=0.8,
            label=(
                f"HOBO SN {logger}"
            ),
        )

    ax.set_title(
        title
    )

    ax.set_xlabel(
        "UTC"
    )

    ax.set_ylabel(
        ylabel
    )

    ax.legend()

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.autofmt_xdate()

    fig.tight_layout()

    fig.savefig(
        output_path,
        format="svg",
    )

    plt.close(
        fig
    )


def plot_logger_temperature_difference(
    comparison_rows: list[dict],
):
    times = [
        parse_utc(
            row[
                "timestamp_1104_utc"
            ]
        )
        for row in comparison_rows
    ]

    values = [
        float(
            row[
                "temperature_1105_minus_1104_c"
            ]
        )
        for row in comparison_rows
    ]

    fig, ax = plt.subplots(
        figsize=(
            11,
            5,
        )
    )

    ax.plot(
        times,
        values,
        linewidth=0.8,
    )

    ax.axhline(
        0.0,
        linewidth=1.0,
    )

    ax.set_title(
        "Artemis II Inflight Near-Synchronous "
        "Logger Temperature Difference"
    )

    ax.set_xlabel(
        "SN 1104 UTC sample time"
    )

    ax.set_ylabel(
        "SN 1105 - SN 1104 (°C)"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.autofmt_xdate()

    fig.tight_layout()

    fig.savefig(
        LOGGER_DIFFERENCE_FIGURE,
        format="svg",
    )

    plt.close(
        fig
    )


def main():
    print()
    print(
        "Phase 3A.2 Artemis II "
        "Orion Environmental "
        "Trend Reconstruction"
    )
    print(
        "=" * 72
    )

    (
        rows,
        metadata,
    ) = load_inputs()

    print()
    print(
        "Dependency:"
    )
    print(
        "  Phase 3A.1 normalized "
        "environment dataset: PASS"
    )

    print()
    print(
        "Records:"
    )
    print(
        f"  {len(rows)}"
    )

    (
        period_rows,
        period_summary,
    ) = build_period_summary(
        rows
    )

    daily_rows = (
        build_daily_summary(
            rows
        )
    )

    (
        comparison_rows,
        comparison_summary,
    ) = build_logger_comparison(
        rows
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_csv(
        PERIOD_CSV,
        period_rows,
    )

    write_csv(
        DAILY_CSV,
        daily_rows,
    )

    write_csv(
        LOGGER_COMPARISON_CSV,
        comparison_rows,
    )

    plot_measurement(
        rows,
        "temperature_c",
        "Temperature (°C)",
        (
            "Artemis II Inflight "
            "Storage-Locker Temperature"
        ),
        TEMPERATURE_FIGURE,
    )

    plot_measurement(
        rows,
        "relative_humidity_pct",
        "Relative Humidity (%)",
        (
            "Artemis II Inflight "
            "Storage-Locker Relative Humidity"
        ),
        HUMIDITY_FIGURE,
    )

    plot_measurement(
        rows,
        "dew_point_c",
        "Dew Point (°C)",
        (
            "Artemis II Inflight "
            "Storage-Locker Dew Point"
        ),
        DEW_POINT_FIGURE,
    )

    plot_logger_temperature_difference(
        comparison_rows
    )

    inflight_summary = {}

    for logger in (
        LOGGER_SERIALS
    ):
        inflight_summary[
            logger
        ] = period_summary[
            logger
        ][
            "IN_FLIGHT"
        ]

    summary = {
        "dataset_id": (
            "phase3a2_artemis_ii_"
            "orion_environment_trends"
        ),
        "mission": (
            "Artemis II"
        ),
        "phase": (
            "3A.2"
        ),
        "status": (
            "ANALYSIS_COMPLETE"
        ),
        "dependency": {
            "dataset_id": (
                metadata[
                    "dataset_id"
                ]
            ),
            "records": len(
                rows
            ),
        },
        "analysis_scope": {
            "descriptive_statistics": (
                True
            ),
            "daily_aggregation": (
                True
            ),
            "mission_period_comparison": (
                True
            ),
            "near_synchronous_logger_comparison": (
                True
            ),
            "exact_timestamp_logger_comparison": (
                False
            ),
            "change_point_detection": (
                False
            ),
            "anomaly_detection": (
                False
            ),
            "causal_inference": (
                False
            ),
        },
        "period_summary": (
            period_summary
        ),
        "inflight_summary": (
            inflight_summary
        ),
        "inflight_logger_comparison": (
            comparison_summary
        ),
        "evidence_boundary": {
            "temperature_humidity_and_dew_point_are_direct_pds_measurements": (
                True
            ),
            "descriptive_statistics_are_missionlab_derived": (
                True
            ),
            "daily_aggregates_are_missionlab_derived": (
                True
            ),
            "logger_differences_are_missionlab_derived": (
                True
            ),
            "logger_series_have_exact_matching_timestamps": (
                False
            ),
            "near_synchronous_pairing_is_missionlab_derived": (
                True
            ),
            "paired_measurements_are_simultaneous": (
                False
            ),
            "logger_difference_is_not_spacecraft_wide_temperature_gradient": (
                True
            ),
            "logger_difference_is_not_eclss_performance_metric": (
                True
            ),
            "environmental_trend_is_not_anomaly_by_itself": (
                True
            ),
            "no_anomaly_classification_performed_in_phase3a2": (
                True
            ),
        },
        "outputs": {
            "period_summary_csv": str(
                PERIOD_CSV.relative_to(
                    ROOT
                )
            ),
            "daily_summary_csv": str(
                DAILY_CSV.relative_to(
                    ROOT
                )
            ),
            "logger_comparison_csv": str(
                LOGGER_COMPARISON_CSV.relative_to(
                    ROOT
                )
            ),
            "temperature_figure": str(
                TEMPERATURE_FIGURE.relative_to(
                    ROOT
                )
            ),
            "humidity_figure": str(
                HUMIDITY_FIGURE.relative_to(
                    ROOT
                )
            ),
            "dew_point_figure": str(
                DEW_POINT_FIGURE.relative_to(
                    ROOT
                )
            ),
            "logger_difference_figure": str(
                LOGGER_DIFFERENCE_FIGURE.relative_to(
                    ROOT
                )
            ),
        },
    }

    with SUMMARY_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary,
            f,
            indent=2,
        )

        f.write(
            "\n"
        )

    print()
    print(
        "Mission-period statistics:"
    )

    for logger in (
        LOGGER_SERIALS
    ):
        print()
        print(
            f"  Logger SN {logger}"
        )

        for period in (
            MISSION_PERIODS
        ):
            temp = (
                period_summary[
                    logger
                ][
                    period
                ][
                    "temperature_c"
                ]
            )

            rh = (
                period_summary[
                    logger
                ][
                    period
                ][
                    "relative_humidity_pct"
                ]
            )

            dew = (
                period_summary[
                    logger
                ][
                    period
                ][
                    "dew_point_c"
                ]
            )

            print(
                f"    {period}:"
            )

            print(
                "      temperature mean: "
                f"{temp['mean']:.3f} °C"
            )

            print(
                "      temperature range: "
                f"{temp['minimum']:.3f} "
                "to "
                f"{temp['maximum']:.3f} °C"
            )

            print(
                "      RH mean: "
                f"{rh['mean']:.3f} %"
            )

            print(
                "      dew-point mean: "
                f"{dew['mean']:.3f} °C"
            )

    print()
    print(
        "Inflight near-synchronous "
        "logger comparison:"
    )

    pairing_counts = (
        comparison_summary[
            "pairing_counts"
        ]
    )

    print(
        "  SN 1104 inflight records: "
        f"{pairing_counts['inflight_records_1104']}"
    )

    print(
        "  SN 1105 inflight records: "
        f"{pairing_counts['inflight_records_1105']}"
    )

    print(
        "  paired records: "
        f"{pairing_counts['paired_records']}"
    )

    print(
        "  unmatched SN 1104 records: "
        f"{pairing_counts['unmatched_records_1104']}"
    )

    print(
        "  unmatched SN 1105 records: "
        f"{pairing_counts['unmatched_records_1105']}"
    )

    time_offset = (
        comparison_summary[
            "time_offset_1105_minus_1104_seconds"
        ]
    )

    absolute_offset = (
        comparison_summary[
            "absolute_time_offset_seconds"
        ]
    )

    print(
        "  pairing tolerance: "
        f"+/-{PAIRING_TOLERANCE_SECONDS:.0f} s"
    )

    print(
        "  mean signed time offset "
        "(1105 - 1104): "
        f"{time_offset['mean']:.3f} s"
    )

    print(
        "  maximum absolute time offset: "
        f"{absolute_offset['maximum']:.3f} s"
    )

    temp_difference = (
        comparison_summary[
            "temperature_1105_minus_1104_c"
        ]
    )

    rh_difference = (
        comparison_summary[
            "relative_humidity_1105_minus_1104_pct"
        ]
    )

    dew_difference = (
        comparison_summary[
            "dew_point_1105_minus_1104_c"
        ]
    )

    print(
        "  mean temperature difference "
        "(1105 - 1104): "
        f"{temp_difference['mean']:.3f} °C"
    )

    print(
        "  mean RH difference "
        "(1105 - 1104): "
        f"{rh_difference['mean']:.3f} %"
    )

    print(
        "  mean dew-point difference "
        "(1105 - 1104): "
        f"{dew_difference['mean']:.3f} °C"
    )

    print()
    print(
        "Timestamp-grid boundary:"
    )
    print(
        "  SN 1104 and SN 1105 do not "
        "share exact sample timestamps"
    )
    print(
        "  comparison uses one-to-one "
        "nearest-time pairing"
    )
    print(
        "  tolerance = +/-30 seconds"
    )
    print(
        "  paired samples are "
        "near-synchronous, not simultaneous"
    )

    print()
    print(
        "Evidence boundary:"
    )
    print(
        "  Direct environmental "
        "measurements: NASA PDS"
    )
    print(
        "  Statistics / aggregates / "
        "logger differences: "
        "MISSIONLAB DERIVED"
    )
    print(
        "  Near-time pairing: "
        "MISSIONLAB DERIVED"
    )
    print(
        "  Logger difference != "
        "spacecraft-wide gradient"
    )
    print(
        "  Environmental trend != "
        "ECLSS anomaly"
    )
    print(
        "  No anomaly classification "
        "performed in Phase 3A.2"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            PERIOD_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            DAILY_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            LOGGER_COMPARISON_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            SUMMARY_JSON.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            TEMPERATURE_FIGURE.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            HUMIDITY_FIGURE.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            DEW_POINT_FIGURE.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            LOGGER_DIFFERENCE_FIGURE.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 3A.2 ANALYSIS COMPLETE"
    )


if __name__ == "__main__":
    main()
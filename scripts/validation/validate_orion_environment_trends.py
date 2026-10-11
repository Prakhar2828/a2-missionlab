from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "eclss"
)

NORMALIZED_CSV = (
    INPUT_DIR
    / "orion_environment_normalized.csv"
)

PERIOD_CSV = (
    INPUT_DIR
    / "orion_environment_period_summary.csv"
)

DAILY_CSV = (
    INPUT_DIR
    / "orion_environment_daily_summary.csv"
)

LOGGER_COMPARISON_CSV = (
    INPUT_DIR
    / "orion_environment_logger_comparison.csv"
)

SUMMARY_JSON = (
    INPUT_DIR
    / "orion_environment_trend_summary.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "eclss"
)

FIGURES = [
    (
        ASSET_DIR
        / "phase3a2_temperature_trends.svg"
    ),
    (
        ASSET_DIR
        / "phase3a2_humidity_trends.svg"
    ),
    (
        ASSET_DIR
        / "phase3a2_dew_point_trends.svg"
    ),
    (
        ASSET_DIR
        / "phase3a2_logger_temperature_difference.svg"
    ),
]

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

EXPECTED_TOTAL_RECORDS = 75396

EXPECTED_INFLIGHT_PER_LOGGER = 13052

EXPECTED_PAIR_COUNT = 13052

EXPECTED_TIME_OFFSET_SECONDS = -20.0

PAIRING_TOLERANCE_SECONDS = 30.0

EXPECTED_PERIOD_SUMMARY_ROWS = 18

EXPECTED_DAILY_ROWS = 54


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 3A.2 VALIDATION FAILED: "
        f"{message}"
    )


def load_json(
    path: Path,
) -> dict:
    if not path.exists():
        fail(
            f"missing JSON file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(
            f
        )


def load_csv(
    path: Path,
) -> list[dict]:
    if not path.exists():
        fail(
            f"missing CSV file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        return list(
            csv.DictReader(
                f
            )
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


def require_float(
    value,
    label: str,
) -> float:
    try:
        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        fail(
            f"{label} is not numeric"
        )

    if not math.isfinite(
        number
    ):
        fail(
            f"{label} is not finite"
        )

    return number


def percentile(
    values: list[float],
    fraction: float,
) -> float:
    ordered = sorted(
        values
    )

    if not ordered:
        fail(
            "cannot calculate percentile "
            "for empty values"
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

    upper_fraction = (
        position
        - lower
    )

    return (
        ordered[
            lower
        ]
        * (
            1.0
            - upper_fraction
        )
        + ordered[
            upper
        ]
        * upper_fraction
    )


def summarize(
    values: list[float],
) -> dict:
    if not values:
        fail(
            "cannot summarize empty values"
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


def assert_close(
    observed,
    expected,
    label: str,
    tolerance: float = 1e-9,
):
    observed_value = require_float(
        observed,
        label,
    )

    expected_value = require_float(
        expected,
        label,
    )

    if abs(
        observed_value
        - expected_value
    ) > tolerance:
        fail(
            f"{label} mismatch: "
            f"observed={observed_value} "
            f"expected={expected_value}"
        )


def validate_summary(
    observed: dict,
    expected: dict,
    label: str,
):
    if (
        int(
            observed[
                "count"
            ]
        )
        != int(
            expected[
                "count"
            ]
        )
    ):
        fail(
            f"{label} count mismatch"
        )

    for field in [
        "minimum",
        "p05",
        "median",
        "mean",
        "p95",
        "maximum",
        "standard_deviation",
    ]:
        assert_close(
            observed[
                field
            ],
            expected[
                field
            ],
            (
                f"{label} "
                f"{field}"
            ),
        )


def build_expected_period_summary(
    normalized_rows: list[dict],
) -> dict:
    grouped = defaultdict(
        lambda: defaultdict(
            list
        )
    )

    for row in normalized_rows:
        logger = row[
            "logger_serial"
        ]

        period = row[
            "mission_period"
        ]

        if logger not in LOGGER_SERIALS:
            fail(
                f"unexpected logger: {logger}"
            )

        if period not in MISSION_PERIODS:
            fail(
                "unexpected mission period: "
                f"{period}"
            )

        for measurement in MEASUREMENTS:
            grouped[
                (
                    logger,
                    period,
                )
            ][
                measurement
            ].append(
                require_float(
                    row[
                        measurement
                    ],
                    measurement,
                )
            )

    result = {}

    for logger in LOGGER_SERIALS:
        result[
            logger
        ] = {}

        for period in MISSION_PERIODS:
            result[
                logger
            ][
                period
            ] = {}

            for measurement in MEASUREMENTS:
                result[
                    logger
                ][
                    period
                ][
                    measurement
                ] = summarize(
                    grouped[
                        (
                            logger,
                            period,
                        )
                    ][
                        measurement
                    ]
                )

    return result


def build_expected_pairs(
    normalized_rows: list[dict],
):
    inflight = {
        "1104": [],
        "1105": [],
    }

    for row in normalized_rows:
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

        inflight[
            logger
        ].append(
            row
        )

    for logger in LOGGER_SERIALS:
        inflight[
            logger
        ].sort(
            key=lambda row: (
                row[
                    "timestamp_utc"
                ]
            )
        )

    if (
        len(
            inflight[
                "1104"
            ]
        )
        != EXPECTED_INFLIGHT_PER_LOGGER
    ):
        fail(
            "SN 1104 inflight "
            "record count mismatch"
        )

    if (
        len(
            inflight[
                "1105"
            ]
        )
        != EXPECTED_INFLIGHT_PER_LOGGER
    ):
        fail(
            "SN 1105 inflight "
            "record count mismatch"
        )

    pairs = []

    i = 0
    j = 0

    while (
        i
        < len(
            inflight[
                "1104"
            ]
        )
        and j
        < len(
            inflight[
                "1105"
            ]
        )
    ):
        row_1104 = (
            inflight[
                "1104"
            ][
                i
            ]
        )

        row_1105 = (
            inflight[
                "1105"
            ][
                j
            ]
        )

        t_1104 = parse_utc(
            row_1104[
                "timestamp_utc"
            ]
        )

        t_1105 = parse_utc(
            row_1105[
                "timestamp_utc"
            ]
        )

        offset = (
            t_1105
            - t_1104
        ).total_seconds()

        if (
            abs(
                offset
            )
            <= PAIRING_TOLERANCE_SECONDS
        ):
            pairs.append(
                (
                    row_1104,
                    row_1105,
                    offset,
                )
            )

            i += 1
            j += 1

        elif (
            t_1104
            < t_1105
        ):
            i += 1

        else:
            j += 1

    return pairs


def main():
    print()
    print(
        "Phase 3A.2 Artemis II "
        "Orion Environmental "
        "Trend Reconstruction Validation"
    )
    print(
        "=" * 72
    )

    normalized_rows = load_csv(
        NORMALIZED_CSV
    )

    period_rows = load_csv(
        PERIOD_CSV
    )

    daily_rows = load_csv(
        DAILY_CSV
    )

    comparison_rows = load_csv(
        LOGGER_COMPARISON_CSV
    )

    summary = load_json(
        SUMMARY_JSON
    )

    #
    # Dependency identity
    #

    if (
        len(
            normalized_rows
        )
        != EXPECTED_TOTAL_RECORDS
    ):
        fail(
            "normalized dependency "
            "record count mismatch"
        )

    if (
        summary.get(
            "dataset_id"
        )
        != (
            "phase3a2_artemis_ii_"
            "orion_environment_trends"
        )
    ):
        fail(
            "summary dataset ID mismatch"
        )

    if (
        summary.get(
            "mission"
        )
        != "Artemis II"
    ):
        fail(
            "summary mission mismatch"
        )

    if (
        summary.get(
            "phase"
        )
        != "3A.2"
    ):
        fail(
            "summary phase mismatch"
        )

    if (
        summary.get(
            "status"
        )
        != "ANALYSIS_COMPLETE"
    ):
        fail(
            "summary status mismatch"
        )

    print()
    print(
        "Dependency dataset: PASS"
    )
    print(
        "Analysis identity: PASS"
    )

    #
    # Period summaries
    #

    if (
        len(
            period_rows
        )
        != EXPECTED_PERIOD_SUMMARY_ROWS
    ):
        fail(
            "period summary row "
            f"count is {len(period_rows)}, "
            "expected "
            f"{EXPECTED_PERIOD_SUMMARY_ROWS}"
        )

    expected_period = (
        build_expected_period_summary(
            normalized_rows
        )
    )

    period_lookup = {}

    for row in period_rows:
        key = (
            row[
                "logger_serial"
            ],
            row[
                "mission_period"
            ],
            row[
                "measurement"
            ],
        )

        if key in period_lookup:
            fail(
                "duplicate period-summary "
                f"row: {key}"
            )

        period_lookup[
            key
        ] = row

        if (
            row[
                "provenance"
            ]
            != (
                "MISSIONLAB_DERIVED_"
                "DESCRIPTIVE_STATISTICS"
            )
        ):
            fail(
                "period-summary provenance "
                "mismatch"
            )

    for logger in LOGGER_SERIALS:
        for period in MISSION_PERIODS:
            for measurement in MEASUREMENTS:
                key = (
                    logger,
                    period,
                    measurement,
                )

                if key not in period_lookup:
                    fail(
                        "missing period-summary "
                        f"row: {key}"
                    )

                expected = (
                    expected_period[
                        logger
                    ][
                        period
                    ][
                        measurement
                    ]
                )

                observed = (
                    period_lookup[
                        key
                    ]
                )

                if (
                    int(
                        observed[
                            "count"
                        ]
                    )
                    != expected[
                        "count"
                    ]
                ):
                    fail(
                        "period-summary count "
                        f"mismatch: {key}"
                    )

                for field in [
                    "minimum",
                    "p05",
                    "median",
                    "mean",
                    "p95",
                    "maximum",
                    "standard_deviation",
                ]:
                    assert_close(
                        observed[
                            field
                        ],
                        expected[
                            field
                        ],
                        (
                            f"{key} "
                            f"{field}"
                        ),
                    )

    print(
        "Mission-period statistics: PASS"
    )

    #
    # Summary JSON period statistics
    #

    for logger in LOGGER_SERIALS:
        for period in MISSION_PERIODS:
            for measurement in MEASUREMENTS:
                validate_summary(
                    summary[
                        "period_summary"
                    ][
                        logger
                    ][
                        period
                    ][
                        measurement
                    ],
                    expected_period[
                        logger
                    ][
                        period
                    ][
                        measurement
                    ],
                    (
                        f"{logger} "
                        f"{period} "
                        f"{measurement}"
                    ),
                )

    print(
        "Summary JSON statistics: PASS"
    )

    #
    # Daily summaries
    #

    if (
        len(
            daily_rows
        )
        != EXPECTED_DAILY_ROWS
    ):
        fail(
            "daily summary row count "
            f"is {len(daily_rows)}, "
            f"expected {EXPECTED_DAILY_ROWS}"
        )

    daily_keys = set()

    for row in daily_rows:
        key = (
            row[
                "logger_serial"
            ],
            row[
                "date_utc"
            ],
        )

        if key in daily_keys:
            fail(
                "duplicate daily summary "
                f"row: {key}"
            )

        daily_keys.add(
            key
        )

        if (
            row[
                "provenance"
            ]
            != (
                "MISSIONLAB_DERIVED_"
                "DAILY_STATISTICS"
            )
        ):
            fail(
                "daily-summary provenance "
                "mismatch"
            )

        records = int(
            row[
                "records"
            ]
        )

        if records <= 0:
            fail(
                "daily summary has "
                "non-positive record count"
            )

        for field in [
            "temperature_mean_c",
            "temperature_min_c",
            "temperature_max_c",
            "relative_humidity_mean_pct",
            "relative_humidity_min_pct",
            "relative_humidity_max_pct",
            "dew_point_mean_c",
            "dew_point_min_c",
            "dew_point_max_c",
        ]:
            require_float(
                row[
                    field
                ],
                field,
            )

    print(
        "Daily aggregation: PASS"
    )

    #
    # Independent nearest-time pairing
    #

    expected_pairs = (
        build_expected_pairs(
            normalized_rows
        )
    )

    if (
        len(
            expected_pairs
        )
        != EXPECTED_PAIR_COUNT
    ):
        fail(
            "independent pairing "
            f"produced {len(expected_pairs)} "
            f"pairs instead of "
            f"{EXPECTED_PAIR_COUNT}"
        )

    if (
        len(
            comparison_rows
        )
        != EXPECTED_PAIR_COUNT
    ):
        fail(
            "comparison CSV contains "
            f"{len(comparison_rows)} rows, "
            f"expected {EXPECTED_PAIR_COUNT}"
        )

    offsets = []

    temperature_differences = []

    humidity_differences = []

    dew_point_differences = []

    for index, (
        expected_pair,
        observed,
    ) in enumerate(
        zip(
            expected_pairs,
            comparison_rows,
        ),
        start=1,
    ):
        (
            row_1104,
            row_1105,
            expected_offset,
        ) = expected_pair

        if (
            observed[
                "timestamp_1104_utc"
            ]
            != row_1104[
                "timestamp_utc"
            ]
        ):
            fail(
                f"pair {index}: "
                "SN 1104 timestamp mismatch"
            )

        if (
            observed[
                "timestamp_1105_utc"
            ]
            != row_1105[
                "timestamp_utc"
            ]
        ):
            fail(
                f"pair {index}: "
                "SN 1105 timestamp mismatch"
            )

        observed_offset = (
            require_float(
                observed[
                    "time_offset_1105_minus_1104_seconds"
                ],
                "pairing offset",
            )
        )

        if abs(
            observed_offset
            - expected_offset
        ) > 1e-9:
            fail(
                f"pair {index}: "
                "time-offset mismatch"
            )

        if abs(
            observed_offset
        ) > PAIRING_TOLERANCE_SECONDS:
            fail(
                f"pair {index}: "
                "pairing tolerance exceeded"
            )

        if (
            observed[
                "pairing_method"
            ]
            != (
                "NEAREST_TIME_WITHIN_30_SECONDS"
            )
        ):
            fail(
                f"pair {index}: "
                "pairing-method label mismatch"
            )

        if (
            observed[
                "provenance"
            ]
            != (
                "MISSIONLAB_DERIVED_"
                "NEAR_SYNCHRONOUS_COMPARISON"
            )
        ):
            fail(
                f"pair {index}: "
                "comparison provenance mismatch"
            )

        temp_1104 = require_float(
            row_1104[
                "temperature_c"
            ],
            "SN 1104 temperature",
        )

        temp_1105 = require_float(
            row_1105[
                "temperature_c"
            ],
            "SN 1105 temperature",
        )

        rh_1104 = require_float(
            row_1104[
                "relative_humidity_pct"
            ],
            "SN 1104 RH",
        )

        rh_1105 = require_float(
            row_1105[
                "relative_humidity_pct"
            ],
            "SN 1105 RH",
        )

        dew_1104 = require_float(
            row_1104[
                "dew_point_c"
            ],
            "SN 1104 dew point",
        )

        dew_1105 = require_float(
            row_1105[
                "dew_point_c"
            ],
            "SN 1105 dew point",
        )

        expected_temp_difference = (
            temp_1105
            - temp_1104
        )

        expected_rh_difference = (
            rh_1105
            - rh_1104
        )

        expected_dew_difference = (
            dew_1105
            - dew_1104
        )

        assert_close(
            observed[
                "temperature_1105_minus_1104_c"
            ],
            expected_temp_difference,
            (
                f"pair {index} "
                "temperature difference"
            ),
        )

        assert_close(
            observed[
                "relative_humidity_1105_minus_1104_pct"
            ],
            expected_rh_difference,
            (
                f"pair {index} "
                "RH difference"
            ),
        )

        assert_close(
            observed[
                "dew_point_1105_minus_1104_c"
            ],
            expected_dew_difference,
            (
                f"pair {index} "
                "dew-point difference"
            ),
        )

        offsets.append(
            observed_offset
        )

        temperature_differences.append(
            expected_temp_difference
        )

        humidity_differences.append(
            expected_rh_difference
        )

        dew_point_differences.append(
            expected_dew_difference
        )

    print(
        "Near-synchronous pairing: PASS"
    )
    print(
        "Pair-by-pair derived differences: PASS"
    )

    #
    # Clock-grid relationship
    #

    unique_offsets = sorted(
        set(
            offsets
        )
    )

    if (
        unique_offsets
        != [
            EXPECTED_TIME_OFFSET_SECONDS
        ]
    ):
        fail(
            "logger time-grid offset "
            f"is not uniformly "
            f"{EXPECTED_TIME_OFFSET_SECONDS} s: "
            f"{unique_offsets[:10]}"
        )

    print(
        "Logger time-grid offset: PASS"
    )

    #
    # Comparison summary JSON
    #

    comparison_summary = (
        summary[
            "inflight_logger_comparison"
        ]
    )

    if (
        comparison_summary[
            "pairing_method"
        ]
        != "NEAREST_TIME_ONE_TO_ONE"
    ):
        fail(
            "summary pairing method mismatch"
        )

    assert_close(
        comparison_summary[
            "pairing_tolerance_seconds"
        ],
        PAIRING_TOLERANCE_SECONDS,
        "summary pairing tolerance",
    )

    if (
        comparison_summary[
            "exact_timestamp_matches_required"
        ]
        is not False
    ):
        fail(
            "exact timestamp matching "
            "boundary failed"
        )

    if (
        comparison_summary[
            "measurements_are_simultaneous"
        ]
        is not False
    ):
        fail(
            "simultaneous-measurement "
            "boundary failed"
        )

    counts = (
        comparison_summary[
            "pairing_counts"
        ]
    )

    if (
        counts[
            "inflight_records_1104"
        ]
        != EXPECTED_INFLIGHT_PER_LOGGER
    ):
        fail(
            "summary SN 1104 "
            "inflight count mismatch"
        )

    if (
        counts[
            "inflight_records_1105"
        ]
        != EXPECTED_INFLIGHT_PER_LOGGER
    ):
        fail(
            "summary SN 1105 "
            "inflight count mismatch"
        )

    if (
        counts[
            "paired_records"
        ]
        != EXPECTED_PAIR_COUNT
    ):
        fail(
            "summary paired count mismatch"
        )

    if (
        counts[
            "unmatched_records_1104"
        ]
        != 0
    ):
        fail(
            "unexpected unmatched "
            "SN 1104 samples"
        )

    if (
        counts[
            "unmatched_records_1105"
        ]
        != 0
    ):
        fail(
            "unexpected unmatched "
            "SN 1105 samples"
        )

    validate_summary(
        comparison_summary[
            "time_offset_1105_minus_1104_seconds"
        ],
        summarize(
            offsets
        ),
        "time offset",
    )

    validate_summary(
        comparison_summary[
            "absolute_time_offset_seconds"
        ],
        summarize(
            [
                abs(
                    value
                )
                for value in offsets
            ]
        ),
        "absolute time offset",
    )

    validate_summary(
        comparison_summary[
            "temperature_1105_minus_1104_c"
        ],
        summarize(
            temperature_differences
        ),
        "temperature difference",
    )

    validate_summary(
        comparison_summary[
            "relative_humidity_1105_minus_1104_pct"
        ],
        summarize(
            humidity_differences
        ),
        "RH difference",
    )

    validate_summary(
        comparison_summary[
            "dew_point_1105_minus_1104_c"
        ],
        summarize(
            dew_point_differences
        ),
        "dew-point difference",
    )

    print(
        "Logger comparison summary: PASS"
    )

    #
    # Analysis-scope boundaries
    #

    scope = (
        summary[
            "analysis_scope"
        ]
    )

    required_true_scope = [
        "descriptive_statistics",
        "daily_aggregation",
        "mission_period_comparison",
        "near_synchronous_logger_comparison",
    ]

    required_false_scope = [
        "exact_timestamp_logger_comparison",
        "change_point_detection",
        "anomaly_detection",
        "causal_inference",
    ]

    for key in required_true_scope:
        if (
            scope.get(
                key
            )
            is not True
        ):
            fail(
                "analysis scope expected "
                f"TRUE: {key}"
            )

    for key in required_false_scope:
        if (
            scope.get(
                key
            )
            is not False
        ):
            fail(
                "analysis scope expected "
                f"FALSE: {key}"
            )

    print(
        "Analysis-scope boundaries: PASS"
    )

    #
    # Evidence boundaries
    #

    boundary = (
        summary[
            "evidence_boundary"
        ]
    )

    required_true_boundaries = [
        (
            "temperature_humidity_and_"
            "dew_point_are_direct_pds_measurements"
        ),
        (
            "descriptive_statistics_are_"
            "missionlab_derived"
        ),
        (
            "daily_aggregates_are_"
            "missionlab_derived"
        ),
        (
            "logger_differences_are_"
            "missionlab_derived"
        ),
        (
            "near_synchronous_pairing_is_"
            "missionlab_derived"
        ),
        (
            "logger_difference_is_not_"
            "spacecraft_wide_temperature_gradient"
        ),
        (
            "logger_difference_is_not_"
            "eclss_performance_metric"
        ),
        (
            "environmental_trend_is_not_"
            "anomaly_by_itself"
        ),
        (
            "no_anomaly_classification_"
            "performed_in_phase3a2"
        ),
    ]

    required_false_boundaries = [
        (
            "logger_series_have_exact_"
            "matching_timestamps"
        ),
        (
            "paired_measurements_are_"
            "simultaneous"
        ),
    ]

    for key in required_true_boundaries:
        if (
            boundary.get(
                key
            )
            is not True
        ):
            fail(
                "evidence boundary "
                f"expected TRUE: {key}"
            )

    for key in required_false_boundaries:
        if (
            boundary.get(
                key
            )
            is not False
        ):
            fail(
                "evidence boundary "
                f"expected FALSE: {key}"
            )

    print(
        "Evidence-boundary policy: PASS"
    )

    #
    # Figures
    #

    for figure in FIGURES:
        if not figure.exists():
            fail(
                "missing figure: "
                f"{figure}"
            )

        if (
            figure.stat().st_size
            <= 0
        ):
            fail(
                "empty figure: "
                f"{figure}"
            )

        content = (
            figure.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )

        if (
            "<svg"
            not in content
        ):
            fail(
                "figure is not valid "
                f"SVG text: {figure}"
            )

    print(
        "Documentation figures: PASS"
    )

    print()
    print(
        "Validated results:"
    )
    print(
        "  normalized records: "
        f"{len(normalized_rows)}"
    )
    print(
        "  period-summary rows: "
        f"{len(period_rows)}"
    )
    print(
        "  daily-summary rows: "
        f"{len(daily_rows)}"
    )
    print(
        "  inflight pairs: "
        f"{len(comparison_rows)}"
    )
    print(
        "  logger offset: "
        f"{EXPECTED_TIME_OFFSET_SECONDS:.1f} s"
    )

    print()
    print(
        "Key inflight differences:"
    )
    print(
        "  mean temperature "
        "(1105 - 1104): "
        f"{statistics.fmean(temperature_differences):.3f} °C"
    )
    print(
        "  mean RH "
        "(1105 - 1104): "
        f"{statistics.fmean(humidity_differences):.3f} %"
    )
    print(
        "  mean dew point "
        "(1105 - 1104): "
        f"{statistics.fmean(dew_point_differences):.3f} °C"
    )

    print()
    print(
        "PHASE 3A.2 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
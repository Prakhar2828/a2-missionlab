from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone
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

TREND_SUMMARY = (
    INPUT_DIR
    / "orion_environment_trend_summary.json"
)

CHANGE_CSV = (
    INPUT_DIR
    / "orion_environment_change_candidates.csv"
)

ANOMALY_CSV = (
    INPUT_DIR
    / "orion_environment_anomaly_candidates.csv"
)

SUMMARY_JSON = (
    INPUT_DIR
    / "orion_environment_change_analysis.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "eclss"
)

CHANGE_FIGURE = (
    ASSET_DIR
    / "phase3a3_change_point_scores.svg"
)

ANOMALY_FIGURE = (
    ASSET_DIR
    / "phase3a3_anomaly_scores.svg"
)


UTC = timezone.utc

EXPECTED_RECORDS = 75396

EXPECTED_AGGREGATE_BINS = {
    "1104": 2515,
    "1105": 2514,
}

EXPECTED_CHANGE_CANDIDATES = 107

EXPECTED_ANOMALY_CANDIDATES = 13

EXPECTED_CHANGE_CONTEXT = {
    "MISSION_BOUNDARY_LAUNCH_CONTEXT": 2,
    "MISSION_BOUNDARY_SPLASHDOWN_CONTEXT": 7,
    "NASA_REPORTED_CARGO_HANDOVER_CONTEXT": 4,
    "NASA_REPORTED_LOGGER_RELOCATION_CONTEXT": 2,
    "NO_MATCHING_PUBLIC_CONTEXT_IN_CURATED_SET": 92,
}

EXPECTED_ANOMALY_CONTEXT = {
    "NO_MATCHING_PUBLIC_CONTEXT_IN_CURATED_SET": 13,
}

LOGGER_SERIALS = [
    "1104",
    "1105",
]

MEASUREMENTS = [
    "temperature_c",
    "relative_humidity_pct",
    "dew_point_c",
]

AGGREGATION_MINUTES = 15

CHANGE_WINDOW_BINS = 4

CHANGE_SCORE_THRESHOLD = 8.0

CHANGE_MIN_SEPARATION_BINS = 12

MAX_CHANGE_CANDIDATES_PER_SERIES = 20

LOCAL_HALF_WINDOW_BINS = 12

ANOMALY_SCORE_THRESHOLD = 6.0

ANOMALY_CLUSTER_GAP_BINS = 2

MAX_ANOMALY_CANDIDATES_PER_SERIES = 25

SCALE_FLOORS = {
    "temperature_c": 0.05,
    "relative_humidity_pct": 0.10,
    "dew_point_c": 0.05,
}

LAUNCH_UTC = datetime(
    2026,
    4,
    1,
    22,
    35,
    12,
    tzinfo=UTC,
)

SN1105_TRANSFER_START_UTC = datetime(
    2026,
    4,
    9,
    18,
    0,
    0,
    tzinfo=UTC,
)

SN1105_TRANSFER_END_UTC = datetime(
    2026,
    4,
    9,
    21,
    0,
    0,
    tzinfo=UTC,
)

SPLASHDOWN_UTC = datetime(
    2026,
    4,
    11,
    0,
    7,
    0,
    tzinfo=UTC,
)

ORION_POWER_DOWN_UTC = datetime(
    2026,
    4,
    11,
    0,
    30,
    0,
    tzinfo=UTC,
)

RECOVERY_WELL_DECK_UTC = datetime(
    2026,
    4,
    11,
    8,
    14,
    0,
    tzinfo=UTC,
)

CARGO_HANDOVER_BOUNDARY_UTC = datetime(
    2026,
    4,
    14,
    19,
    0,
    0,
    tzinfo=UTC,
)


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 3A.3 VALIDATION FAILED: "
        f"{message}"
    )


def load_csv(
    path: Path,
) -> list[dict]:
    if not path.exists():
        fail(
            f"missing CSV: {path}"
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


def load_json(
    path: Path,
) -> dict:
    if not path.exists():
        fail(
            f"missing JSON: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(
            f
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
        ).astimezone(
            UTC
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
        value.astimezone(
            UTC
        )
        .isoformat(
            timespec="seconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def finite_float(
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


def assert_close(
    observed,
    expected,
    label: str,
    tolerance: float = 1e-9,
):
    observed_value = finite_float(
        observed,
        label,
    )

    expected_value = finite_float(
        expected,
        label,
    )

    if abs(
        observed_value
        - expected_value
    ) > tolerance:
        fail(
            f"{label} mismatch: "
            f"observed={observed_value}, "
            f"expected={expected_value}"
        )


def median(
    values: list[float],
) -> float:
    if not values:
        fail(
            "cannot calculate median "
            "for empty sequence"
        )

    return statistics.median(
        values
    )


def robust_scale(
    values: list[float],
    floor: float,
) -> float:
    if not values:
        return floor

    center = median(
        values
    )

    deviations = [
        abs(
            value
            - center
        )
        for value in values
    ]

    mad = median(
        deviations
    )

    return max(
        1.4826 * mad,
        floor,
    )


def floor_to_bin(
    timestamp: datetime,
) -> datetime:
    minute = (
        timestamp.minute
        // AGGREGATION_MINUTES
        * AGGREGATION_MINUTES
    )

    return timestamp.replace(
        minute=minute,
        second=0,
        microsecond=0,
    )


def classify_public_context(
    logger: str,
    timestamp: datetime,
) -> str:
    if (
        logger == "1105"
        and (
            SN1105_TRANSFER_START_UTC
            - timedelta(
                hours=1
            )
        )
        <= timestamp
        <= (
            SN1105_TRANSFER_END_UTC
            + timedelta(
                hours=1
            )
        )
    ):
        return (
            "NASA_REPORTED_LOGGER_"
            "RELOCATION_CONTEXT"
        )

    if abs(
        (
            timestamp
            - LAUNCH_UTC
        ).total_seconds()
    ) <= 2 * 3600:
        return (
            "MISSION_BOUNDARY_"
            "LAUNCH_CONTEXT"
        )

    if abs(
        (
            timestamp
            - SPLASHDOWN_UTC
        ).total_seconds()
    ) <= 2 * 3600:
        return (
            "MISSION_BOUNDARY_"
            "SPLASHDOWN_CONTEXT"
        )

    if abs(
        (
            timestamp
            - ORION_POWER_DOWN_UTC
        ).total_seconds()
    ) <= 2 * 3600:
        return (
            "NASA_REPORTED_"
            "POWER_DOWN_CONTEXT"
        )

    if abs(
        (
            timestamp
            - RECOVERY_WELL_DECK_UTC
        ).total_seconds()
    ) <= 2 * 3600:
        return (
            "NASA_REPORTED_"
            "RECOVERY_CONTEXT"
        )

    if (
        CARGO_HANDOVER_BOUNDARY_UTC
        <= timestamp
        <= (
            CARGO_HANDOVER_BOUNDARY_UTC
            + timedelta(
                hours=12
            )
        )
    ):
        return (
            "NASA_REPORTED_"
            "CARGO_HANDOVER_CONTEXT"
        )

    return (
        "NO_MATCHING_PUBLIC_CONTEXT_"
        "IN_CURATED_SET"
    )


def aggregate_series(
    rows: list[dict],
):
    buckets = defaultdict(
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

        if logger not in LOGGER_SERIALS:
            fail(
                f"unexpected logger: {logger}"
            )

        timestamp = parse_utc(
            row[
                "timestamp_utc"
            ]
        )

        bucket = floor_to_bin(
            timestamp
        )

        key = (
            logger,
            bucket,
        )

        period_counts[
            key
        ][
            row[
                "mission_period"
            ]
        ] += 1

        for measurement in MEASUREMENTS:
            buckets[
                key
            ][
                measurement
            ].append(
                finite_float(
                    row[
                        measurement
                    ],
                    measurement,
                )
            )

    series = {
        logger: {
            measurement: []
            for measurement
            in MEASUREMENTS
        }
        for logger in LOGGER_SERIALS
    }

    for (
        logger,
        bucket,
    ) in sorted(
        buckets
    ):
        key = (
            logger,
            bucket,
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

        for measurement in MEASUREMENTS:
            series[
                logger
            ][
                measurement
            ].append(
                {
                    "timestamp": (
                        bucket
                    ),
                    "value": median(
                        buckets[
                            key
                        ][
                            measurement
                        ]
                    ),
                    "mission_period": (
                        dominant_period
                    ),
                }
            )

    return series


def detect_change_candidates(
    series,
):
    output = []

    for logger in LOGGER_SERIALS:
        for measurement in MEASUREMENTS:
            records = (
                series[
                    logger
                ][
                    measurement
                ]
            )

            values = [
                row[
                    "value"
                ]
                for row in records
            ]

            differences = [
                current
                - previous
                for previous, current
                in zip(
                    values[:-1],
                    values[1:],
                )
            ]

            scale = robust_scale(
                differences,
                SCALE_FLOORS[
                    measurement
                ],
            )

            raw_candidates = []

            for index in range(
                CHANGE_WINDOW_BINS,
                len(
                    records
                )
                - CHANGE_WINDOW_BINS,
            ):
                before = [
                    records[
                        j
                    ][
                        "value"
                    ]
                    for j in range(
                        index
                        - CHANGE_WINDOW_BINS,
                        index,
                    )
                ]

                after = [
                    records[
                        j
                    ][
                        "value"
                    ]
                    for j in range(
                        index,
                        index
                        + CHANGE_WINDOW_BINS,
                    )
                ]

                before_median = median(
                    before
                )

                after_median = median(
                    after
                )

                delta = (
                    after_median
                    - before_median
                )

                score = (
                    abs(
                        delta
                    )
                    / scale
                )

                if (
                    score
                    < CHANGE_SCORE_THRESHOLD
                ):
                    continue

                raw_candidates.append(
                    {
                        "index": index,
                        "timestamp": (
                            records[
                                index
                            ][
                                "timestamp"
                            ]
                        ),
                        "mission_period": (
                            records[
                                index
                            ][
                                "mission_period"
                            ]
                        ),
                        "before_median": (
                            before_median
                        ),
                        "after_median": (
                            after_median
                        ),
                        "delta": delta,
                        "scale": scale,
                        "score": score,
                    }
                )

            raw_candidates.sort(
                key=lambda item: (
                    item[
                        "score"
                    ]
                ),
                reverse=True,
            )

            selected = []

            for candidate in raw_candidates:
                too_close = any(
                    abs(
                        candidate[
                            "index"
                        ]
                        - existing[
                            "index"
                        ]
                    )
                    < CHANGE_MIN_SEPARATION_BINS
                    for existing
                    in selected
                )

                if too_close:
                    continue

                selected.append(
                    candidate
                )

                if (
                    len(
                        selected
                    )
                    >= (
                        MAX_CHANGE_CANDIDATES_PER_SERIES
                    )
                ):
                    break

            selected.sort(
                key=lambda item: (
                    item[
                        "timestamp"
                    ]
                )
            )

            for rank, candidate in enumerate(
                selected,
                start=1,
            ):
                timestamp = (
                    candidate[
                        "timestamp"
                    ]
                )

                output.append(
                    {
                        "candidate_id": (
                            f"CP_{logger}_"
                            f"{measurement}_"
                            f"{rank:02d}"
                        ),
                        "logger_serial": (
                            logger
                        ),
                        "measurement": (
                            measurement
                        ),
                        "timestamp_utc": (
                            iso_z(
                                timestamp
                            )
                        ),
                        "mission_period": (
                            candidate[
                                "mission_period"
                            ]
                        ),
                        "before_median": (
                            candidate[
                                "before_median"
                            ]
                        ),
                        "after_median": (
                            candidate[
                                "after_median"
                            ]
                        ),
                        "delta": (
                            candidate[
                                "delta"
                            ]
                        ),
                        "scale": (
                            candidate[
                                "scale"
                            ]
                        ),
                        "score": (
                            candidate[
                                "score"
                            ]
                        ),
                        "public_context": (
                            classify_public_context(
                                logger,
                                timestamp,
                            )
                        ),
                    }
                )

    output.sort(
        key=lambda row: (
            row[
                "timestamp_utc"
            ],
            row[
                "logger_serial"
            ],
            row[
                "measurement"
            ],
        )
    )

    return output


def local_robust_score(
    records: list[dict],
    index: int,
    measurement: str,
):
    start = max(
        0,
        index
        - LOCAL_HALF_WINDOW_BINS,
    )

    stop = min(
        len(
            records
        ),
        index
        + LOCAL_HALF_WINDOW_BINS
        + 1,
    )

    neighbors = [
        records[
            j
        ][
            "value"
        ]
        for j in range(
            start,
            stop,
        )
        if j != index
    ]

    if len(
        neighbors
    ) < 4:
        return (
            0.0,
            records[
                index
            ][
                "value"
            ],
            SCALE_FLOORS[
                measurement
            ],
        )

    baseline = median(
        neighbors
    )

    deviations = [
        abs(
            value
            - baseline
        )
        for value
        in neighbors
    ]

    scale = max(
        1.4826
        * median(
            deviations
        ),
        SCALE_FLOORS[
            measurement
        ],
    )

    value = (
        records[
            index
        ][
            "value"
        ]
    )

    score = (
        (
            value
            - baseline
        )
        / scale
    )

    return (
        score,
        baseline,
        scale,
    )


def cluster_indices(
    candidates: list[dict],
):
    if not candidates:
        return []

    ordered = sorted(
        candidates,
        key=lambda item: (
            item[
                "index"
            ]
        ),
    )

    clusters = [
        [
            ordered[0]
        ]
    ]

    for candidate in ordered[1:]:
        previous = (
            clusters[
                -1
            ][
                -1
            ]
        )

        if (
            candidate[
                "index"
            ]
            - previous[
                "index"
            ]
            <= ANOMALY_CLUSTER_GAP_BINS
        ):
            clusters[
                -1
            ].append(
                candidate
            )

        else:
            clusters.append(
                [
                    candidate
                ]
            )

    return clusters


def detect_anomaly_candidates(
    series,
):
    output = []

    for logger in LOGGER_SERIALS:
        for measurement in MEASUREMENTS:
            records = (
                series[
                    logger
                ][
                    measurement
                ]
            )

            raw_candidates = []

            for index in range(
                len(
                    records
                )
            ):
                (
                    score,
                    baseline,
                    scale,
                ) = local_robust_score(
                    records,
                    index,
                    measurement,
                )

                if (
                    abs(
                        score
                    )
                    < ANOMALY_SCORE_THRESHOLD
                ):
                    continue

                raw_candidates.append(
                    {
                        "index": index,
                        "timestamp": (
                            records[
                                index
                            ][
                                "timestamp"
                            ]
                        ),
                        "mission_period": (
                            records[
                                index
                            ][
                                "mission_period"
                            ]
                        ),
                        "value": (
                            records[
                                index
                            ][
                                "value"
                            ]
                        ),
                        "baseline": (
                            baseline
                        ),
                        "scale": (
                            scale
                        ),
                        "score": (
                            score
                        ),
                    }
                )

            clusters = (
                cluster_indices(
                    raw_candidates
                )
            )

            events = []

            for cluster in clusters:
                peak = max(
                    cluster,
                    key=lambda item: (
                        abs(
                            item[
                                "score"
                            ]
                        )
                    ),
                )

                events.append(
                    {
                        "start": (
                            cluster[
                                0
                            ][
                                "timestamp"
                            ]
                        ),
                        "end": (
                            cluster[
                                -1
                            ][
                                "timestamp"
                            ]
                        ),
                        "bins": len(
                            cluster
                        ),
                        "peak": (
                            peak
                        ),
                    }
                )

            events.sort(
                key=lambda item: (
                    abs(
                        item[
                            "peak"
                        ][
                            "score"
                        ]
                    )
                ),
                reverse=True,
            )

            events = events[
                :
                MAX_ANOMALY_CANDIDATES_PER_SERIES
            ]

            events.sort(
                key=lambda item: (
                    item[
                        "peak"
                    ][
                        "timestamp"
                    ]
                )
            )

            for rank, event in enumerate(
                events,
                start=1,
            ):
                peak = (
                    event[
                        "peak"
                    ]
                )

                timestamp = (
                    peak[
                        "timestamp"
                    ]
                )

                output.append(
                    {
                        "candidate_id": (
                            f"AN_{logger}_"
                            f"{measurement}_"
                            f"{rank:02d}"
                        ),
                        "logger_serial": (
                            logger
                        ),
                        "measurement": (
                            measurement
                        ),
                        "cluster_start_utc": (
                            iso_z(
                                event[
                                    "start"
                                ]
                            )
                        ),
                        "cluster_end_utc": (
                            iso_z(
                                event[
                                    "end"
                                ]
                            )
                        ),
                        "peak_timestamp_utc": (
                            iso_z(
                                timestamp
                            )
                        ),
                        "mission_period": (
                            peak[
                                "mission_period"
                            ]
                        ),
                        "cluster_bins": (
                            event[
                                "bins"
                            ]
                        ),
                        "value": (
                            peak[
                                "value"
                            ]
                        ),
                        "baseline": (
                            peak[
                                "baseline"
                            ]
                        ),
                        "deviation": (
                            peak[
                                "value"
                            ]
                            - peak[
                                "baseline"
                            ]
                        ),
                        "scale": (
                            peak[
                                "scale"
                            ]
                        ),
                        "score": (
                            peak[
                                "score"
                            ]
                        ),
                        "public_context": (
                            classify_public_context(
                                logger,
                                timestamp,
                            )
                        ),
                    }
                )

    output.sort(
        key=lambda row: (
            row[
                "peak_timestamp_utc"
            ],
            row[
                "logger_serial"
            ],
            row[
                "measurement"
            ],
        )
    )

    return output


def count_contexts(
    rows: list[dict],
) -> dict:
    counts = defaultdict(
        int
    )

    for row in rows:
        counts[
            row[
                "public_context"
            ]
        ] += 1

    return dict(
        sorted(
            counts.items()
        )
    )


def validate_change_rows(
    expected: list[dict],
    observed: list[dict],
):
    if len(
        observed
    ) != len(
        expected
    ):
        fail(
            "change candidate CSV "
            "record count mismatch"
        )

    for index, (
        exp,
        obs,
    ) in enumerate(
        zip(
            expected,
            observed,
        ),
        start=1,
    ):
        for field in [
            "candidate_id",
            "logger_serial",
            "measurement",
            "timestamp_utc",
            "mission_period",
            "public_context",
        ]:
            if (
                obs[
                    field
                ]
                != exp[
                    field
                ]
            ):
                fail(
                    f"change candidate "
                    f"{index}: "
                    f"{field} mismatch"
                )

        if (
            obs[
                "interpretation"
            ]
            != (
                "STATISTICAL_CHANGE_"
                "CANDIDATE_ONLY"
            )
        ):
            fail(
                f"change candidate {index}: "
                "interpretation mismatch"
            )

        if (
            obs[
                "provenance"
            ]
            != "MISSIONLAB_DERIVED"
        ):
            fail(
                f"change candidate {index}: "
                "provenance mismatch"
            )

        if (
            int(
                obs[
                    "pre_window_minutes"
                ]
            )
            != 60
        ):
            fail(
                "change pre-window mismatch"
            )

        if (
            int(
                obs[
                    "post_window_minutes"
                ]
            )
            != 60
        ):
            fail(
                "change post-window mismatch"
            )

        assert_close(
            obs[
                "before_median"
            ],
            exp[
                "before_median"
            ],
            (
                f"change {index} "
                "before median"
            ),
        )

        assert_close(
            obs[
                "after_median"
            ],
            exp[
                "after_median"
            ],
            (
                f"change {index} "
                "after median"
            ),
        )

        assert_close(
            obs[
                "delta_after_minus_before"
            ],
            exp[
                "delta"
            ],
            (
                f"change {index} "
                "delta"
            ),
        )

        assert_close(
            obs[
                "robust_scale"
            ],
            exp[
                "scale"
            ],
            (
                f"change {index} "
                "scale"
            ),
        )

        assert_close(
            obs[
                "change_score"
            ],
            exp[
                "score"
            ],
            (
                f"change {index} "
                "score"
            ),
        )

        if (
            finite_float(
                obs[
                    "change_score"
                ],
                "change score",
            )
            < CHANGE_SCORE_THRESHOLD
        ):
            fail(
                "change candidate below "
                "configured threshold"
            )


def validate_anomaly_rows(
    expected: list[dict],
    observed: list[dict],
):
    if len(
        observed
    ) != len(
        expected
    ):
        fail(
            "anomaly candidate CSV "
            "record count mismatch"
        )

    for index, (
        exp,
        obs,
    ) in enumerate(
        zip(
            expected,
            observed,
        ),
        start=1,
    ):
        for field in [
            "candidate_id",
            "logger_serial",
            "measurement",
            "cluster_start_utc",
            "cluster_end_utc",
            "peak_timestamp_utc",
            "mission_period",
            "public_context",
        ]:
            if (
                obs[
                    field
                ]
                != exp[
                    field
                ]
            ):
                fail(
                    f"anomaly candidate "
                    f"{index}: "
                    f"{field} mismatch"
                )

        if (
            int(
                obs[
                    "cluster_bins"
                ]
            )
            != exp[
                "cluster_bins"
            ]
        ):
            fail(
                "anomaly cluster-size "
                "mismatch"
            )

        if (
            int(
                obs[
                    "aggregation_minutes"
                ]
            )
            != AGGREGATION_MINUTES
        ):
            fail(
                "anomaly aggregation "
                "interval mismatch"
            )

        if (
            obs[
                "interpretation"
            ]
            != (
                "STATISTICAL_ANOMALY_"
                "CANDIDATE_ONLY"
            )
        ):
            fail(
                f"anomaly candidate {index}: "
                "interpretation mismatch"
            )

        if (
            obs[
                "provenance"
            ]
            != "MISSIONLAB_DERIVED"
        ):
            fail(
                f"anomaly candidate {index}: "
                "provenance mismatch"
            )

        assert_close(
            obs[
                "observed_value"
            ],
            exp[
                "value"
            ],
            (
                f"anomaly {index} "
                "observed value"
            ),
        )

        assert_close(
            obs[
                "local_median"
            ],
            exp[
                "baseline"
            ],
            (
                f"anomaly {index} "
                "local median"
            ),
        )

        assert_close(
            obs[
                "deviation_from_local_median"
            ],
            exp[
                "deviation"
            ],
            (
                f"anomaly {index} "
                "deviation"
            ),
        )

        assert_close(
            obs[
                "robust_scale"
            ],
            exp[
                "scale"
            ],
            (
                f"anomaly {index} "
                "scale"
            ),
        )

        assert_close(
            obs[
                "robust_score"
            ],
            exp[
                "score"
            ],
            (
                f"anomaly {index} "
                "score"
            ),
        )

        assert_close(
            obs[
                "absolute_robust_score"
            ],
            abs(
                exp[
                    "score"
                ]
            ),
            (
                f"anomaly {index} "
                "absolute score"
            ),
        )

        if (
            abs(
                finite_float(
                    obs[
                        "robust_score"
                    ],
                    "robust score",
                )
            )
            < ANOMALY_SCORE_THRESHOLD
        ):
            fail(
                "anomaly candidate below "
                "configured threshold"
            )


def validate_svg(
    path: Path,
):
    if not path.exists():
        fail(
            f"missing figure: {path}"
        )

    if (
        path.stat().st_size
        <= 0
    ):
        fail(
            f"empty figure: {path}"
        )

    content = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    if "<svg" not in content:
        fail(
            f"invalid SVG: {path}"
        )


def main():
    print()
    print(
        "Phase 3A.3 Artemis II "
        "Environmental Change-Point "
        "and Anomaly-Evidence Validation"
    )
    print(
        "=" * 72
    )

    normalized_rows = load_csv(
        NORMALIZED_CSV
    )

    trend_summary = load_json(
        TREND_SUMMARY
    )

    change_rows = load_csv(
        CHANGE_CSV
    )

    anomaly_rows = load_csv(
        ANOMALY_CSV
    )

    summary = load_json(
        SUMMARY_JSON
    )

    #
    # Dependencies
    #

    if (
        len(
            normalized_rows
        )
        != EXPECTED_RECORDS
    ):
        fail(
            "Phase 3A.1 record "
            "count mismatch"
        )

    if (
        trend_summary.get(
            "dataset_id"
        )
        != (
            "phase3a2_artemis_ii_"
            "orion_environment_trends"
        )
    ):
        fail(
            "Phase 3A.2 dependency "
            "identity mismatch"
        )

    print()
    print(
        "Phase 3A.1 dependency: PASS"
    )
    print(
        "Phase 3A.2 dependency: PASS"
    )

    #
    # Analysis identity
    #

    if (
        summary.get(
            "dataset_id"
        )
        != (
            "phase3a3_artemis_ii_"
            "orion_environment_change_analysis"
        )
    ):
        fail(
            "dataset identity mismatch"
        )

    if (
        summary.get(
            "mission"
        )
        != "Artemis II"
    ):
        fail(
            "mission identity mismatch"
        )

    if (
        summary.get(
            "phase"
        )
        != "3A.3"
    ):
        fail(
            "phase identity mismatch"
        )

    if (
        summary.get(
            "status"
        )
        != "ANALYSIS_COMPLETE"
    ):
        fail(
            "analysis status mismatch"
        )

    print(
        "Analysis identity: PASS"
    )

    #
    # Independent aggregation
    #

    series = aggregate_series(
        normalized_rows
    )

    observed_bins = {
        logger: len(
            series[
                logger
            ][
                "temperature_c"
            ]
        )
        for logger
        in LOGGER_SERIALS
    }

    if (
        observed_bins
        != EXPECTED_AGGREGATE_BINS
    ):
        fail(
            "aggregate-bin counts "
            f"mismatch: {observed_bins}"
        )

    if (
        summary[
            "results"
        ][
            "aggregate_bins"
        ]
        != EXPECTED_AGGREGATE_BINS
    ):
        fail(
            "summary aggregate-bin "
            "counts mismatch"
        )

    print(
        "15-minute aggregation: PASS"
    )

    #
    # Recompute change points
    #

    expected_changes = (
        detect_change_candidates(
            series
        )
    )

    if (
        len(
            expected_changes
        )
        != EXPECTED_CHANGE_CANDIDATES
    ):
        fail(
            "independent change-point "
            "count mismatch: "
            f"{len(expected_changes)}"
        )

    validate_change_rows(
        expected_changes,
        change_rows,
    )

    print(
        "Change-point reconstruction: PASS"
    )
    print(
        "Change-point candidate values: PASS"
    )

    #
    # Recompute anomalies
    #

    expected_anomalies = (
        detect_anomaly_candidates(
            series
        )
    )

    if (
        len(
            expected_anomalies
        )
        != EXPECTED_ANOMALY_CANDIDATES
    ):
        fail(
            "independent anomaly "
            "count mismatch: "
            f"{len(expected_anomalies)}"
        )

    validate_anomaly_rows(
        expected_anomalies,
        anomaly_rows,
    )

    print(
        "Local anomaly reconstruction: PASS"
    )
    print(
        "Anomaly candidate values: PASS"
    )

    #
    # Public-context classifications
    #

    change_context = (
        count_contexts(
            change_rows
        )
    )

    anomaly_context = (
        count_contexts(
            anomaly_rows
        )
    )

    if (
        change_context
        != EXPECTED_CHANGE_CONTEXT
    ):
        fail(
            "change context counts "
            f"mismatch: {change_context}"
        )

    if (
        anomaly_context
        != EXPECTED_ANOMALY_CONTEXT
    ):
        fail(
            "anomaly context counts "
            f"mismatch: {anomaly_context}"
        )

    if (
        summary[
            "results"
        ][
            "change_candidates_by_context"
        ]
        != EXPECTED_CHANGE_CONTEXT
    ):
        fail(
            "summary change-context "
            "counts mismatch"
        )

    if (
        summary[
            "results"
        ][
            "anomaly_candidates_by_context"
        ]
        != EXPECTED_ANOMALY_CONTEXT
    ):
        fail(
            "summary anomaly-context "
            "counts mismatch"
        )

    print(
        "Public-context correlation: PASS"
    )

    #
    # Candidate totals
    #

    results = (
        summary[
            "results"
        ]
    )

    if (
        results[
            "change_candidate_count"
        ]
        != EXPECTED_CHANGE_CANDIDATES
    ):
        fail(
            "summary change-candidate "
            "count mismatch"
        )

    if (
        results[
            "anomaly_candidate_count"
        ]
        != EXPECTED_ANOMALY_CANDIDATES
    ):
        fail(
            "summary anomaly-candidate "
            "count mismatch"
        )

    if (
        results[
            "change_candidates_without_matching_public_context"
        ]
        != 92
    ):
        fail(
            "unmatched change-candidate "
            "count mismatch"
        )

    if (
        results[
            "anomaly_candidates_without_matching_public_context"
        ]
        != 13
    ):
        fail(
            "unmatched anomaly-candidate "
            "count mismatch"
        )

    print(
        "Candidate totals: PASS"
    )

    #
    # Method definitions
    #

    methods = (
        summary[
            "methods"
        ]
    )

    if (
        methods[
            "aggregation"
        ][
            "minutes"
        ]
        != AGGREGATION_MINUTES
    ):
        fail(
            "aggregation interval mismatch"
        )

    assert_close(
        methods[
            "change_point_evidence"
        ][
            "threshold"
        ],
        CHANGE_SCORE_THRESHOLD,
        "change threshold",
    )

    if (
        methods[
            "change_point_evidence"
        ][
            "minimum_candidate_separation_minutes"
        ]
        != (
            CHANGE_MIN_SEPARATION_BINS
            * AGGREGATION_MINUTES
        )
    ):
        fail(
            "change-candidate separation "
            "configuration mismatch"
        )

    assert_close(
        methods[
            "anomaly_evidence"
        ][
            "threshold_absolute_score"
        ],
        ANOMALY_SCORE_THRESHOLD,
        "anomaly threshold",
    )

    if (
        methods[
            "anomaly_evidence"
        ][
            "local_half_window_minutes"
        ]
        != (
            LOCAL_HALF_WINDOW_BINS
            * AGGREGATION_MINUTES
        )
    ):
        fail(
            "anomaly local-window "
            "configuration mismatch"
        )

    print(
        "Statistical method metadata: PASS"
    )

    #
    # NASA-reported context metadata
    #

    context = (
        summary[
            "public_context"
        ]
    )

    if (
        context[
            "sn1104"
        ][
            "location"
        ]
        != "Locker E / Bag L_011"
    ):
        fail(
            "SN 1104 location context "
            "mismatch"
        )

    if (
        context[
            "sn1105"
        ][
            "launch_location"
        ]
        != "Locker D / Bag L_022"
    ):
        fail(
            "SN 1105 launch location "
            "mismatch"
        )

    if (
        context[
            "sn1105"
        ][
            "later_location"
        ]
        != "Locker F / Bag R_027"
    ):
        fail(
            "SN 1105 later location "
            "mismatch"
        )

    if (
        context[
            "sn1105"
        ][
            "transfer_window_start_utc"
        ]
        != (
            "2026-04-09T18:00:00Z"
        )
    ):
        fail(
            "SN 1105 transfer-window "
            "start mismatch"
        )

    if (
        context[
            "sn1105"
        ][
            "transfer_window_end_utc"
        ]
        != (
            "2026-04-09T21:00:00Z"
        )
    ):
        fail(
            "SN 1105 transfer-window "
            "end mismatch"
        )

    if (
        context[
            "sn1105"
        ][
            "exact_transfer_time_known"
        ]
        is not False
    ):
        fail(
            "SN 1105 exact transfer-time "
            "boundary failed"
        )

    if (
        context[
            "orion_power_down_utc"
        ]
        != "2026-04-11T00:30:00Z"
    ):
        fail(
            "Orion power-down context "
            "mismatch"
        )

    if (
        context[
            "recovery_well_deck_utc"
        ]
        != "2026-04-11T08:14:00Z"
    ):
        fail(
            "recovery well-deck context "
            "mismatch"
        )

    print(
        "NASA-reported context metadata: PASS"
    )

    #
    # Evidence boundaries
    #

    boundary = (
        summary[
            "evidence_boundary"
        ]
    )

    required_false = [
        "raw_measurements_modified",
        "change_candidate_equals_spacecraft_anomaly",
        "anomaly_candidate_equals_confirmed_spacecraft_anomaly",
        "absence_of_matching_public_context_proves_anomaly",
        "absence_of_matching_public_context_proves_no_public_record_exists",
        "sn1105_transfer_related_change_proves_eclss_event",
        "postflight_environment_is_equivalent_to_inflight_environment",
        "causal_inference_performed",
    ]

    for key in required_false:
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

    if (
        boundary.get(
            "statistical_candidates_are_missionlab_derived"
        )
        is not True
    ):
        fail(
            "MissionLab-derived "
            "candidate boundary failed"
        )

    print(
        "Evidence-boundary policy: PASS"
    )

    #
    # Generated figures
    #

    validate_svg(
        CHANGE_FIGURE
    )

    validate_svg(
        ANOMALY_FIGURE
    )

    print(
        "Documentation figures: PASS"
    )

    print()
    print(
        "Validated results:"
    )
    print(
        "  raw normalized records: "
        f"{len(normalized_rows)}"
    )
    print(
        "  SN 1104 aggregate bins: "
        f"{observed_bins['1104']}"
    )
    print(
        "  SN 1105 aggregate bins: "
        f"{observed_bins['1105']}"
    )
    print(
        "  change-point candidates: "
        f"{len(change_rows)}"
    )
    print(
        "  anomaly-evidence candidates: "
        f"{len(anomaly_rows)}"
    )

    print()
    print(
        "Validated change contexts:"
    )

    for (
        key,
        value,
    ) in change_context.items():
        print(
            f"  {key}: {value}"
        )

    print()
    print(
        "Validated anomaly contexts:"
    )

    for (
        key,
        value,
    ) in anomaly_context.items():
        print(
            f"  {key}: {value}"
        )

    print()
    print(
        "Interpretation boundary:"
    )
    print(
        "  107 change candidates "
        "are statistical candidates only"
    )
    print(
        "  13 anomaly candidates "
        "are statistical candidates only"
    )
    print(
        "  unmatched public context "
        "does not prove spacecraft anomaly"
    )
    print(
        "  causal inference: FALSE"
    )

    print()
    print(
        "PHASE 3A.3 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
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

TREND_SUMMARY = (
    INPUT_DIR
    / "orion_environment_trend_summary.json"
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

CHANGE_POINT_CSV = (
    OUTPUT_DIR
    / "orion_environment_change_candidates.csv"
)

ANOMALY_CSV = (
    OUTPUT_DIR
    / "orion_environment_anomaly_candidates.csv"
)

SUMMARY_JSON = (
    OUTPUT_DIR
    / "orion_environment_change_analysis.json"
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

LOGGER_SERIALS = [
    "1104",
    "1105",
]

MEASUREMENTS = [
    "temperature_c",
    "relative_humidity_pct",
    "dew_point_c",
]

MEASUREMENT_LABELS = {
    "temperature_c": (
        "Temperature (C)"
    ),
    "relative_humidity_pct": (
        "Relative Humidity (%)"
    ),
    "dew_point_c": (
        "Dew Point (C)"
    ),
}

#
# Analysis grid.
#
# Raw PDS values remain untouched.
# Statistical analysis is performed on
# MissionLab-derived 15-minute medians.
#
AGGREGATION_MINUTES = 15

#
# Change-point detection compares the median
# of one hour before each candidate boundary
# with one hour after it.
#
CHANGE_WINDOW_BINS = 4

CHANGE_SCORE_THRESHOLD = 8.0

CHANGE_MIN_SEPARATION_BINS = 12

MAX_CHANGE_CANDIDATES_PER_SERIES = 20

#
# Local anomaly evidence is evaluated against
# a +/-3 hour neighborhood on the 15-minute
# aggregate grid.
#
LOCAL_HALF_WINDOW_BINS = 12

ANOMALY_SCORE_THRESHOLD = 6.0

ANOMALY_CLUSTER_GAP_BINS = 2

MAX_ANOMALY_CANDIDATES_PER_SERIES = 25

#
# Numerical floors prevent quantized sensor
# measurements from producing arbitrarily
# large robust scores when the local MAD is
# near zero.
#
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
        "PHASE 3A.3 ANALYSIS FAILED: "
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
    field: str,
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
            f"{field} is not numeric: "
            f"{value!r}"
        )

    if not math.isfinite(
        number
    ):
        fail(
            f"{field} is not finite"
        )

    return number


def median(
    values: list[float],
) -> float:
    if not values:
        fail(
            "cannot compute median "
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

    sigma = (
        1.4826
        * mad
    )

    return max(
        sigma,
        floor,
    )


def summary_stats(
    values: list[float],
) -> dict:
    if not values:
        return {
            "count": 0,
            "minimum": None,
            "median": None,
            "mean": None,
            "maximum": None,
        }

    return {
        "count": len(
            values
        ),
        "minimum": min(
            values
        ),
        "median": median(
            values
        ),
        "mean": statistics.fmean(
            values
        ),
        "maximum": max(
            values
        ),
    }


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


def load_inputs():
    if not INPUT_CSV.exists():
        fail(
            "missing normalized "
            "environment dataset"
        )

    if not TREND_SUMMARY.exists():
        fail(
            "missing Phase 3A.2 "
            "trend summary"
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

    if (
        len(
            rows
        )
        != EXPECTED_RECORDS
    ):
        fail(
            "normalized record count "
            f"is {len(rows)}, "
            f"expected {EXPECTED_RECORDS}"
        )

    with TREND_SUMMARY.open(
        "r",
        encoding="utf-8",
    ) as f:
        trend_summary = json.load(
            f
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
            "unexpected Phase 3A.2 "
            "dependency dataset"
        )

    return (
        rows,
        trend_summary,
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
                "unexpected logger "
                f"{logger}"
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
        for logger
        in LOGGER_SERIALS
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
            values = (
                buckets[
                    key
                ][
                    measurement
                ]
            )

            series[
                logger
            ][
                measurement
            ].append(
                {
                    "timestamp": bucket,
                    "value": median(
                        values
                    ),
                    "raw_samples": len(
                        values
                    ),
                    "mission_period": (
                        dominant_period
                    ),
                }
            )

    return series


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


def mission_phase_for_time(
    timestamp: datetime,
) -> str:
    if timestamp < LAUNCH_UTC:
        return "PRELAUNCH"

    if timestamp <= SPLASHDOWN_UTC:
        return "IN_FLIGHT"

    return "POSTFLIGHT"


def detect_change_candidates(
    series,
):
    output = []

    score_series = []

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
                record[
                    "value"
                ]
                for record in records
            ]

            if (
                len(
                    values
                )
                < (
                    2
                    * CHANGE_WINDOW_BINS
                    + 1
                )
            ):
                continue

            first_differences = [
                current
                - previous
                for previous, current
                in zip(
                    values[:-1],
                    values[1:],
                )
            ]

            scale = robust_scale(
                first_differences,
                SCALE_FLOORS[
                    measurement
                ],
            )

            candidates = []

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

                score_series.append(
                    {
                        "logger_serial": (
                            logger
                        ),
                        "measurement": (
                            measurement
                        ),
                        "timestamp": (
                            records[
                                index
                            ][
                                "timestamp"
                            ]
                        ),
                        "score": score,
                    }
                )

                if (
                    score
                    < CHANGE_SCORE_THRESHOLD
                ):
                    continue

                candidates.append(
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
                        "score": score,
                        "scale": scale,
                    }
                )

            candidates.sort(
                key=lambda item: (
                    item[
                        "score"
                    ]
                ),
                reverse=True,
            )

            selected = []

            for candidate in candidates:
                if any(
                    abs(
                        candidate[
                            "index"
                        ]
                        - existing[
                            "index"
                        ]
                    )
                    < (
                        CHANGE_MIN_SEPARATION_BINS
                    )
                    for existing in selected
                ):
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

                context = (
                    classify_public_context(
                        logger,
                        timestamp,
                    )
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
                        "pre_window_minutes": (
                            CHANGE_WINDOW_BINS
                            * AGGREGATION_MINUTES
                        ),
                        "post_window_minutes": (
                            CHANGE_WINDOW_BINS
                            * AGGREGATION_MINUTES
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
                        "delta_after_minus_before": (
                            candidate[
                                "delta"
                            ]
                        ),
                        "robust_scale": (
                            candidate[
                                "scale"
                            ]
                        ),
                        "change_score": (
                            candidate[
                                "score"
                            ]
                        ),
                        "public_context": (
                            context
                        ),
                        "interpretation": (
                            "STATISTICAL_CHANGE_"
                            "CANDIDATE_ONLY"
                        ),
                        "provenance": (
                            "MISSIONLAB_DERIVED"
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

    return (
        output,
        score_series,
    )


def local_robust_score(
    records: list[dict],
    index: int,
    measurement: str,
) -> tuple[
    float,
    float,
    float,
]:
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
        for value in neighbors
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
) -> list[list[dict]]:
    if not candidates:
        return []

    candidates = sorted(
        candidates,
        key=lambda item: (
            item[
                "index"
            ]
        ),
    )

    clusters = [
        [
            candidates[0]
        ]
    ]

    for candidate in candidates[1:]:
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
            <= (
                ANOMALY_CLUSTER_GAP_BINS
            )
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

    score_series = []

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

                score_series.append(
                    {
                        "logger_serial": (
                            logger
                        ),
                        "measurement": (
                            measurement
                        ),
                        "timestamp": (
                            records[
                                index
                            ][
                                "timestamp"
                            ]
                        ),
                        "score": score,
                    }
                )

                if (
                    abs(
                        score
                    )
                    < (
                        ANOMALY_SCORE_THRESHOLD
                    )
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
                        "baseline": baseline,
                        "scale": scale,
                        "score": score,
                    }
                )

            clusters = (
                cluster_indices(
                    raw_candidates
                )
            )

            cluster_events = []

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

                cluster_events.append(
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
                        "peak": peak,
                        "bins": len(
                            cluster
                        ),
                    }
                )

            cluster_events.sort(
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

            cluster_events = (
                cluster_events[
                    :
                    MAX_ANOMALY_CANDIDATES_PER_SERIES
                ]
            )

            cluster_events.sort(
                key=lambda item: (
                    item[
                        "peak"
                    ][
                        "timestamp"
                    ]
                )
            )

            for rank, event in enumerate(
                cluster_events,
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

                context = (
                    classify_public_context(
                        logger,
                        timestamp,
                    )
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
                        "aggregation_minutes": (
                            AGGREGATION_MINUTES
                        ),
                        "observed_value": (
                            peak[
                                "value"
                            ]
                        ),
                        "local_median": (
                            peak[
                                "baseline"
                            ]
                        ),
                        "deviation_from_local_median": (
                            peak[
                                "value"
                            ]
                            - peak[
                                "baseline"
                            ]
                        ),
                        "robust_scale": (
                            peak[
                                "scale"
                            ]
                        ),
                        "robust_score": (
                            peak[
                                "score"
                            ]
                        ),
                        "absolute_robust_score": (
                            abs(
                                peak[
                                    "score"
                                ]
                            )
                        ),
                        "public_context": (
                            context
                        ),
                        "interpretation": (
                            "STATISTICAL_ANOMALY_"
                            "CANDIDATE_ONLY"
                        ),
                        "provenance": (
                            "MISSIONLAB_DERIVED"
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

    return (
        output,
        score_series,
    )


def write_csv(
    path: Path,
    rows: list[dict],
):
    if not rows:
        #
        # Preserve a machine-readable artifact
        # even when no statistical candidates
        # satisfy the threshold.
        #
        path.write_text(
            "candidate_id\n",
            encoding="utf-8",
        )

        return

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(
                rows[
                    0
                ].keys()
            ),
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


def context_counts(
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


def mission_period_counts(
    rows: list[dict],
) -> dict:
    counts = defaultdict(
        int
    )

    for row in rows:
        counts[
            row[
                "mission_period"
            ]
        ] += 1

    return dict(
        sorted(
            counts.items()
        )
    )


def measurement_counts(
    rows: list[dict],
) -> dict:
    counts = defaultdict(
        int
    )

    for row in rows:
        key = (
            f"SN_{row['logger_serial']}_"
            f"{row['measurement']}"
        )

        counts[
            key
        ] += 1

    return dict(
        sorted(
            counts.items()
        )
    )


def plot_score_series(
    score_series: list[dict],
    threshold: float,
    title: str,
    ylabel: str,
    output_path: Path,
    absolute: bool,
):
    fig, ax = plt.subplots(
        figsize=(
            12,
            6,
        )
    )

    for logger in LOGGER_SERIALS:
        for measurement in MEASUREMENTS:
            selected = [
                row
                for row
                in score_series
                if (
                    row[
                        "logger_serial"
                    ]
                    == logger
                    and row[
                        "measurement"
                    ]
                    == measurement
                )
            ]

            if not selected:
                continue

            times = [
                row[
                    "timestamp"
                ]
                for row
                in selected
            ]

            if absolute:
                scores = [
                    abs(
                        row[
                            "score"
                        ]
                    )
                    for row
                    in selected
                ]

            else:
                scores = [
                    row[
                        "score"
                    ]
                    for row
                    in selected
                ]

            ax.plot(
                times,
                scores,
                linewidth=0.65,
                label=(
                    f"SN {logger} "
                    f"{MEASUREMENT_LABELS[measurement]}"
                ),
            )

    if absolute:
        ax.axhline(
            threshold,
            linewidth=1.0,
            linestyle="--",
        )

    else:
        ax.axhline(
            threshold,
            linewidth=1.0,
            linestyle="--",
        )

        ax.axhline(
            -threshold,
            linewidth=1.0,
            linestyle="--",
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

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        fontsize=7,
        ncol=2,
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


def main():
    print()
    print(
        "Phase 3A.3 Artemis II "
        "Environmental Change-Point "
        "and Anomaly-Evidence Analysis"
    )
    print(
        "=" * 72
    )

    (
        rows,
        trend_summary,
    ) = load_inputs()

    print()
    print(
        "Dependencies:"
    )
    print(
        "  Phase 3A.1 normalized "
        "environment dataset: PASS"
    )
    print(
        "  Phase 3A.2 environmental "
        "baseline: PASS"
    )

    print()
    print(
        "Input records:"
    )
    print(
        f"  {len(rows)}"
    )

    print()
    print(
        "Analysis grid:"
    )
    print(
        f"  {AGGREGATION_MINUTES}-minute "
        "median aggregation"
    )

    series = (
        aggregate_series(
            rows
        )
    )

    aggregate_counts = {}

    for logger in LOGGER_SERIALS:
        aggregate_counts[
            logger
        ] = len(
            series[
                logger
            ][
                "temperature_c"
            ]
        )

    print()
    print(
        "Aggregated bins:"
    )

    for logger in LOGGER_SERIALS:
        print(
            f"  SN {logger}: "
            f"{aggregate_counts[logger]}"
        )

    (
        change_candidates,
        change_scores,
    ) = detect_change_candidates(
        series
    )

    (
        anomaly_candidates,
        anomaly_scores,
    ) = detect_anomaly_candidates(
        series
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
        CHANGE_POINT_CSV,
        change_candidates,
    )

    write_csv(
        ANOMALY_CSV,
        anomaly_candidates,
    )

    plot_score_series(
        change_scores,
        CHANGE_SCORE_THRESHOLD,
        (
            "Artemis II Orion Environment "
            "Change-Point Candidate Scores"
        ),
        "Absolute robust change score",
        CHANGE_FIGURE,
        True,
    )

    plot_score_series(
        anomaly_scores,
        ANOMALY_SCORE_THRESHOLD,
        (
            "Artemis II Orion Environment "
            "Local Robust Anomaly Scores"
        ),
        "Robust local score",
        ANOMALY_FIGURE,
        False,
    )

    change_context = (
        context_counts(
            change_candidates
        )
    )

    anomaly_context = (
        context_counts(
            anomaly_candidates
        )
    )

    change_no_context = sum(
        1
        for row
        in change_candidates
        if (
            row[
                "public_context"
            ]
            == (
                "NO_MATCHING_PUBLIC_CONTEXT_"
                "IN_CURATED_SET"
            )
        )
    )

    anomaly_no_context = sum(
        1
        for row
        in anomaly_candidates
        if (
            row[
                "public_context"
            ]
            == (
                "NO_MATCHING_PUBLIC_CONTEXT_"
                "IN_CURATED_SET"
            )
        )
    )

    summary = {
        "dataset_id": (
            "phase3a3_artemis_ii_"
            "orion_environment_change_analysis"
        ),
        "mission": (
            "Artemis II"
        ),
        "phase": (
            "3A.3"
        ),
        "status": (
            "ANALYSIS_COMPLETE"
        ),
        "dependencies": {
            "phase3a1_records": (
                len(
                    rows
                )
            ),
            "phase3a2_dataset_id": (
                trend_summary[
                    "dataset_id"
                ]
            ),
        },
        "methods": {
            "aggregation": {
                "method": (
                    "15_MINUTE_MEDIAN"
                ),
                "minutes": (
                    AGGREGATION_MINUTES
                ),
                "purpose": (
                    "reduce minute-scale "
                    "sensor quantization/noise "
                    "without modifying raw data"
                ),
            },
            "change_point_evidence": {
                "method": (
                    "ONE_HOUR_PRE_POST_"
                    "MEDIAN_DIFFERENCE"
                ),
                "score": (
                    "ABS_DELTA_DIVIDED_BY_"
                    "ROBUST_FIRST_DIFFERENCE_SCALE"
                ),
                "threshold": (
                    CHANGE_SCORE_THRESHOLD
                ),
                "minimum_candidate_separation_minutes": (
                    CHANGE_MIN_SEPARATION_BINS
                    * AGGREGATION_MINUTES
                ),
                "classification": (
                    "STATISTICAL_CHANGE_"
                    "CANDIDATE_ONLY"
                ),
            },
            "anomaly_evidence": {
                "method": (
                    "LOCAL_MEDIAN_MAD"
                ),
                "local_half_window_minutes": (
                    LOCAL_HALF_WINDOW_BINS
                    * AGGREGATION_MINUTES
                ),
                "threshold_absolute_score": (
                    ANOMALY_SCORE_THRESHOLD
                ),
                "classification": (
                    "STATISTICAL_ANOMALY_"
                    "CANDIDATE_ONLY"
                ),
            },
        },
        "public_context": {
            "source": (
                "Artemis II Lunar Science "
                "Data User Guide Section 3.4"
            ),
            "sn1104": {
                "location": (
                    "Locker E / Bag L_011"
                ),
                "duration": (
                    "entire mission"
                ),
            },
            "sn1105": {
                "launch_location": (
                    "Locker D / Bag L_022"
                ),
                "later_location": (
                    "Locker F / Bag R_027"
                ),
                "transfer_window_start_utc": (
                    iso_z(
                        SN1105_TRANSFER_START_UTC
                    )
                ),
                "transfer_window_end_utc": (
                    iso_z(
                        SN1105_TRANSFER_END_UTC
                    )
                ),
                "exact_transfer_time_known": (
                    False
                ),
            },
            "orion_power_down_utc": (
                iso_z(
                    ORION_POWER_DOWN_UTC
                )
            ),
            "recovery_well_deck_utc": (
                iso_z(
                    RECOVERY_WELL_DECK_UTC
                )
            ),
            "cargo_handover": (
                "after "
                + iso_z(
                    CARGO_HANDOVER_BOUNDARY_UTC
                )
            ),
        },
        "results": {
            "aggregate_bins": (
                aggregate_counts
            ),
            "change_candidate_count": (
                len(
                    change_candidates
                )
            ),
            "anomaly_candidate_count": (
                len(
                    anomaly_candidates
                )
            ),
            "change_candidates_by_context": (
                change_context
            ),
            "anomaly_candidates_by_context": (
                anomaly_context
            ),
            "change_candidates_by_series": (
                measurement_counts(
                    change_candidates
                )
            ),
            "anomaly_candidates_by_series": (
                measurement_counts(
                    anomaly_candidates
                )
            ),
            "change_candidates_by_mission_period": (
                mission_period_counts(
                    change_candidates
                )
            ),
            "anomaly_candidates_by_mission_period": (
                mission_period_counts(
                    anomaly_candidates
                )
            ),
            "change_candidates_without_matching_public_context": (
                change_no_context
            ),
            "anomaly_candidates_without_matching_public_context": (
                anomaly_no_context
            ),
        },
        "evidence_boundary": {
            "raw_measurements_modified": (
                False
            ),
            "statistical_candidates_are_missionlab_derived": (
                True
            ),
            "change_candidate_equals_spacecraft_anomaly": (
                False
            ),
            "anomaly_candidate_equals_confirmed_spacecraft_anomaly": (
                False
            ),
            "absence_of_matching_public_context_proves_anomaly": (
                False
            ),
            "absence_of_matching_public_context_proves_no_public_record_exists": (
                False
            ),
            "sn1105_transfer_related_change_proves_eclss_event": (
                False
            ),
            "postflight_environment_is_equivalent_to_inflight_environment": (
                False
            ),
            "causal_inference_performed": (
                False
            ),
        },
        "outputs": {
            "change_candidates_csv": str(
                CHANGE_POINT_CSV.relative_to(
                    ROOT
                )
            ),
            "anomaly_candidates_csv": str(
                ANOMALY_CSV.relative_to(
                    ROOT
                )
            ),
            "summary_json": str(
                SUMMARY_JSON.relative_to(
                    ROOT
                )
            ),
            "change_score_figure": str(
                CHANGE_FIGURE.relative_to(
                    ROOT
                )
            ),
            "anomaly_score_figure": str(
                ANOMALY_FIGURE.relative_to(
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
        "Statistical candidate results:"
    )
    print(
        "  change-point candidates: "
        f"{len(change_candidates)}"
    )
    print(
        "  anomaly-evidence candidates: "
        f"{len(anomaly_candidates)}"
    )

    print()
    print(
        "Change candidates by context:"
    )

    if change_context:
        for key, value in (
            change_context.items()
        ):
            print(
                f"  {key}: {value}"
            )

    else:
        print(
            "  none"
        )

    print()
    print(
        "Anomaly candidates by context:"
    )

    if anomaly_context:
        for key, value in (
            anomaly_context.items()
        ):
            print(
                f"  {key}: {value}"
            )

    else:
        print(
            "  none"
        )

    print()
    print(
        "Unmatched-to-curated-context "
        "candidates:"
    )
    print(
        "  change candidates: "
        f"{change_no_context}"
    )
    print(
        "  anomaly candidates: "
        f"{anomaly_no_context}"
    )

    print()
    print(
        "NASA-reported context boundary:"
    )
    print(
        "  SN 1104 remained in "
        "Locker E / Bag L_011"
    )
    print(
        "  SN 1105 moved from "
        "Locker D / Bag L_022"
    )
    print(
        "  to Locker F / Bag R_027"
    )
    print(
        "  transfer occurred sometime "
        "between:"
    )
    print(
        "    2026-04-09T18:00:00Z"
    )
    print(
        "    2026-04-09T21:00:00Z"
    )
    print(
        "  exact transfer time is unknown"
    )

    print()
    print(
        "Evidence boundary:"
    )
    print(
        "  statistical change candidate "
        "!= spacecraft anomaly"
    )
    print(
        "  statistical anomaly candidate "
        "!= confirmed spacecraft anomaly"
    )
    print(
        "  SN 1105 relocation-related "
        "change != proven ECLSS event"
    )
    print(
        "  no matching curated context "
        "!= proof no public explanation exists"
    )
    print(
        "  causal inference performed: FALSE"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            CHANGE_POINT_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            ANOMALY_CSV.relative_to(
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
            CHANGE_FIGURE.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            ANOMALY_FIGURE.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 3A.3 ANALYSIS COMPLETE"
    )


if __name__ == "__main__":
    main()
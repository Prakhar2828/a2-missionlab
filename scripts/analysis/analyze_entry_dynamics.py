from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_geometry.csv"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_dynamics.csv"
)

OUTPUT_SUMMARY = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_dynamics_summary.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
)

G0 = 9.80665

PRIMARY_DERIVATIVE_WINDOW = 7

ROBUSTNESS_WINDOWS = [
    5,
    7,
    9,
    11,
    15,
]

ALTITUDE_MILESTONES_KM = [
    100.0,
    80.0,
    60.0,
    50.0,
    40.0,
    30.0,
    20.0,
    10.0,
    5.0,
    2.0,
    1.0,
]

SPEED_MILESTONES_KM_S = [
    10.0,
    9.0,
    8.0,
    7.0,
    6.0,
    5.0,
    4.0,
    3.0,
    2.0,
    1.0,
    0.5,
    0.2,
    0.1,
    0.05,
]


plt.rcParams["svg.hashsalt"] = (
    "a2-missionlab"
)

SVG_METADATA = {
    "Date": None,
}


def normalize_svg(
    path: Path,
):
    text = path.read_text(
        encoding="utf-8"
    )

    cleaned = "\n".join(
        line.rstrip(" \t")
        for line in text.splitlines()
    ) + "\n"

    path.write_text(
        cleaned,
        encoding="utf-8",
    )


def parse_utc(
    value: str,
) -> datetime:
    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def format_utc(
    value: datetime,
) -> str:
    return (
        value.isoformat(
            timespec="microseconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def local_quadratic_derivative(
    time_s: np.ndarray,
    values: np.ndarray,
    window_size: int,
) -> np.ndarray:
    if (
        window_size < 3
        or window_size % 2 == 0
    ):
        raise ValueError(
            "window_size must be odd "
            "and at least 3"
        )

    half = (
        window_size // 2
    )

    derivative = np.full(
        len(values),
        np.nan,
        dtype=float,
    )

    for i in range(
        half,
        len(values) - half,
    ):
        local_time = (
            time_s[
                i - half:
                i + half + 1
            ]
            - time_s[i]
        )

        local_values = values[
            i - half:
            i + half + 1
        ]

        coefficients = np.polyfit(
            local_time,
            local_values,
            2,
        )

        derivative[i] = (
            coefficients[1]
        )

    return derivative


def interpolate_crossing(
    t0: float,
    y0: float,
    t1: float,
    y1: float,
    target: float = 0.0,
) -> float:
    if y1 == y0:
        return t0

    fraction = (
        target - y0
    ) / (
        y1 - y0
    )

    return (
        t0
        + fraction
        * (t1 - t0)
    )


def interpolate_series(
    time_s: np.ndarray,
    values: np.ndarray,
    target_time_s: float,
) -> float:
    return float(
        np.interp(
            target_time_s,
            time_s,
            values,
        )
    )


def elapsed_to_utc(
    start: datetime,
    seconds: float,
) -> str:
    return format_utc(
        start
        + timedelta(
            seconds=float(seconds)
        )
    )


def find_descending_crossing(
    values: np.ndarray,
    target: float,
    time_s: np.ndarray,
):
    for i in range(
        1,
        len(values),
    ):
        before = (
            values[i - 1]
        )

        after = (
            values[i]
        )

        if (
            before > target
            and after <= target
        ):
            crossing = (
                interpolate_crossing(
                    time_s[i - 1],
                    before,
                    time_s[i],
                    after,
                    target,
                )
            )

            return crossing

    return None


def find_vertical_zero_crossings(
    time_s: np.ndarray,
    vertical_velocity: np.ndarray,
):
    crossings = []

    for i in range(
        1,
        len(vertical_velocity),
    ):
        before = (
            vertical_velocity[
                i - 1
            ]
        )

        after = (
            vertical_velocity[i]
        )

        if (
            before * after < 0.0
        ):
            crossing = (
                interpolate_crossing(
                    time_s[i - 1],
                    before,
                    time_s[i],
                    after,
                    0.0,
                )
            )

            if (
                before < 0.0
                and after > 0.0
            ):
                direction = (
                    "DESCENT_TO_CLIMB"
                )

            elif (
                before > 0.0
                and after < 0.0
            ):
                direction = (
                    "CLIMB_TO_DESCENT"
                )

            else:
                direction = (
                    "OTHER"
                )

            crossings.append(
                {
                    "elapsed_seconds":
                        crossing,

                    "direction":
                        direction,
                }
            )

    return crossings


def make_plot(
    x,
    y,
    xlabel,
    ylabel,
    title,
    filename,
    markers=None,
):
    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        ASSET_DIR
        / filename
    )

    fig, ax = plt.subplots()

    ax.plot(
        x,
        y,
    )

    if markers:
        for marker in markers:
            ax.scatter(
                [
                    marker[
                        "x"
                    ]
                ],
                [
                    marker[
                        "y"
                    ]
                ],
            )

            ax.annotate(
                marker[
                    "label"
                ],
                (
                    marker[
                        "x"
                    ],
                    marker[
                        "y"
                    ],
                ),
            )

    ax.set_xlabel(
        xlabel
    )

    ax.set_ylabel(
        ylabel
    )

    ax.set_title(
        title
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(
        fig
    )

    normalize_svg(
        path
    )

    return path


def main():
    if not INPUT_CSV.exists():
        raise SystemExit(
            "Missing entry geometry:\n"
            f"{INPUT_CSV}"
        )

    with INPUT_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(
            f
        )

        input_fields = (
            reader.fieldnames
            or []
        )

        rows = list(
            reader
        )

    if len(rows) != 819:
        raise SystemExit(
            f"Expected 819 entry states, "
            f"found {len(rows)}"
        )

    timestamps = [
        parse_utc(
            row[
                "timestamp_utc"
            ]
        )
        for row in rows
    ]

    start_time = (
        timestamps[0]
    )

    time_s = np.array(
        [
            (
                timestamp
                - start_time
            ).total_seconds()
            for timestamp
            in timestamps
        ],
        dtype=float,
    )

    altitude_km = np.array(
        [
            float(
                row[
                    "wgs84_altitude_km"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    speed_km_s = np.array(
        [
            float(
                row[
                    "earth_relative_speed_km_s"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    vertical_km_s = np.array(
        [
            float(
                row[
                    "vertical_velocity_km_s"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    horizontal_km_s = np.array(
        [
            float(
                row[
                    "horizontal_speed_km_s"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    fpa_deg = np.array(
        [
            float(
                row[
                    "flight_path_angle_deg"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    latitude_deg = np.array(
        [
            float(
                row[
                    "geodetic_latitude_deg"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    longitude_deg = np.array(
        [
            float(
                row[
                    "geodetic_longitude_deg"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    # --------------------------------------------------------
    # Raw finite-difference derivative
    # --------------------------------------------------------

    raw_speed_derivative = (
        np.gradient(
            speed_km_s,
            time_s,
        )
    )

    raw_decel_m_s2 = (
        -raw_speed_derivative
        * 1000.0
    )

    # --------------------------------------------------------
    # Primary smoothed local derivative
    # --------------------------------------------------------

    quadratic_speed_derivative = (
        local_quadratic_derivative(
            time_s,
            speed_km_s,
            PRIMARY_DERIVATIVE_WINDOW,
        )
    )

    smoothed_decel_m_s2 = (
        -quadratic_speed_derivative
        * 1000.0
    )

    smoothed_decel_g = (
        smoothed_decel_m_s2
        / G0
    )

    # --------------------------------------------------------
    # Altitude derivative consistency
    # --------------------------------------------------------

    altitude_rate_km_s = (
        np.gradient(
            altitude_km,
            time_s,
        )
    )

    altitude_vertical_difference_m_s = (
        (
            altitude_rate_km_s
            - vertical_km_s
        )
        * 1000.0
    )

    # --------------------------------------------------------
    # Primary peak
    # --------------------------------------------------------

    valid = np.isfinite(
        smoothed_decel_m_s2
    )

    valid_indices = np.where(
        valid
    )[0]

    peak_index = valid_indices[
        np.argmax(
            smoothed_decel_m_s2[
                valid
            ]
        )
    ]

    # --------------------------------------------------------
    # Robustness windows
    # --------------------------------------------------------

    robustness = []

    for window in (
        ROBUSTNESS_WINDOWS
    ):
        derivative = (
            local_quadratic_derivative(
                time_s,
                speed_km_s,
                window,
            )
        )

        decel = (
            -derivative
            * 1000.0
        )

        valid = np.isfinite(
            decel
        )

        indices = np.where(
            valid
        )[0]

        local_peak_index = (
            indices[
                np.argmax(
                    decel[
                        valid
                    ]
                )
            ]
        )

        robustness.append(
            {
                "window_samples":
                    window,

                "peak_index":
                    int(
                        local_peak_index
                    ),

                "peak_elapsed_seconds":
                    float(
                        time_s[
                            local_peak_index
                        ]
                    ),

                "peak_utc":
                    rows[
                        local_peak_index
                    ][
                        "timestamp_utc"
                    ],

                "peak_deceleration_m_s2":
                    float(
                        decel[
                            local_peak_index
                        ]
                    ),

                "peak_g0_equivalent":
                    float(
                        decel[
                            local_peak_index
                        ]
                        / G0
                    ),
            }
        )

    # --------------------------------------------------------
    # Skip/rebound geometry
    # --------------------------------------------------------

    zero_crossings = (
        find_vertical_zero_crossings(
            time_s,
            vertical_km_s,
        )
    )

    for crossing in (
        zero_crossings
    ):
        elapsed = (
            crossing[
                "elapsed_seconds"
            ]
        )

        crossing.update(
            {
                "utc":
                    elapsed_to_utc(
                        start_time,
                        elapsed,
                    ),

                "altitude_km":
                    interpolate_series(
                        time_s,
                        altitude_km,
                        elapsed,
                    ),

                "speed_km_s":
                    interpolate_series(
                        time_s,
                        speed_km_s,
                        elapsed,
                    ),

                "flight_path_angle_deg":
                    interpolate_series(
                        time_s,
                        fpa_deg,
                        elapsed,
                    ),
            }
        )

    skip_summary = None

    if (
        len(zero_crossings)
        >= 2
        and zero_crossings[0][
            "direction"
        ]
        == "DESCENT_TO_CLIMB"
        and zero_crossings[1][
            "direction"
        ]
        == "CLIMB_TO_DESCENT"
    ):
        first = (
            zero_crossings[0]
        )

        second = (
            zero_crossings[1]
        )

        skip_summary = {
            "start":
                first,

            "end":
                second,

            "duration_seconds":
                (
                    second[
                        "elapsed_seconds"
                    ]
                    - first[
                        "elapsed_seconds"
                    ]
                ),

            "altitude_recovery_km":
                (
                    second[
                        "altitude_km"
                    ]
                    - first[
                        "altitude_km"
                    ]
                ),

            "speed_loss_km_s":
                (
                    first[
                        "speed_km_s"
                    ]
                    - second[
                        "speed_km_s"
                    ]
                ),
        }

    # --------------------------------------------------------
    # Milestones
    # --------------------------------------------------------

    altitude_milestones = []

    for threshold in (
        ALTITUDE_MILESTONES_KM
    ):
        crossing = (
            find_descending_crossing(
                altitude_km,
                threshold,
                time_s,
            )
        )

        if crossing is None:
            continue

        altitude_milestones.append(
            {
                "altitude_km":
                    threshold,

                "elapsed_seconds":
                    crossing,

                "utc":
                    elapsed_to_utc(
                        start_time,
                        crossing,
                    ),

                "speed_km_s":
                    interpolate_series(
                        time_s,
                        speed_km_s,
                        crossing,
                    ),

                "flight_path_angle_deg":
                    interpolate_series(
                        time_s,
                        fpa_deg,
                        crossing,
                    ),
            }
        )

    speed_milestones = []

    for threshold in (
        SPEED_MILESTONES_KM_S
    ):
        crossing = (
            find_descending_crossing(
                speed_km_s,
                threshold,
                time_s,
            )
        )

        if crossing is None:
            continue

        speed_milestones.append(
            {
                "speed_km_s":
                    threshold,

                "elapsed_seconds":
                    crossing,

                "utc":
                    elapsed_to_utc(
                        start_time,
                        crossing,
                    ),

                "altitude_km":
                    interpolate_series(
                        time_s,
                        altitude_km,
                        crossing,
                    ),

                "flight_path_angle_deg":
                    interpolate_series(
                        time_s,
                        fpa_deg,
                        crossing,
                    ),
            }
        )

    # --------------------------------------------------------
    # Write state-by-state dynamics
    # --------------------------------------------------------

    output_rows = []

    for i, row in enumerate(
        rows
    ):
        output = dict(
            row
        )

        smoothed = (
            smoothed_decel_m_s2[i]
        )

        smoothed_g = (
            smoothed_decel_g[i]
        )

        output.update(
            {
                "ei_elapsed_seconds":
                    time_s[i],

                "raw_kinematic_deceleration_m_s2":
                    raw_decel_m_s2[i],

                "raw_kinematic_deceleration_g0_equivalent":
                    (
                        raw_decel_m_s2[i]
                        / G0
                    ),

                "smoothed_kinematic_deceleration_m_s2":
                    (
                        ""
                        if not math.isfinite(
                            smoothed
                        )
                        else smoothed
                    ),

                "smoothed_kinematic_deceleration_g0_equivalent":
                    (
                        ""
                        if not math.isfinite(
                            smoothed_g
                        )
                        else smoothed_g
                    ),

                "numerical_altitude_rate_km_s":
                    altitude_rate_km_s[i],

                "altitude_rate_minus_enu_vertical_m_s":
                    altitude_vertical_difference_m_s[i],
            }
        )

        output_rows.append(
            output
        )

    appended_fields = [
        "ei_elapsed_seconds",
        "raw_kinematic_deceleration_m_s2",
        "raw_kinematic_deceleration_g0_equivalent",
        "smoothed_kinematic_deceleration_m_s2",
        "smoothed_kinematic_deceleration_g0_equivalent",
        "numerical_altitude_rate_km_s",
        "altitude_rate_minus_enu_vertical_m_s",
    ]

    with OUTPUT_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=(
                input_fields
                + appended_fields
            ),
        )

        writer.writeheader()

        writer.writerows(
            output_rows
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    interior_vertical_difference = (
        altitude_vertical_difference_m_s[
            1:-1
        ]
    )

    summary = {
        "records":
            len(
                rows
            ),

        "start_utc":
            rows[0][
                "timestamp_utc"
            ],

        "stop_utc":
            rows[-1][
                "timestamp_utc"
            ],

        "duration_seconds":
            float(
                time_s[-1]
            ),

        "primary_derivative": {
            "method":
                (
                    "local quadratic polynomial "
                    "derivative"
                ),

            "window_samples":
                PRIMARY_DERIVATIVE_WINDOW,

            "peak": {
                "utc":
                    rows[
                        peak_index
                    ][
                        "timestamp_utc"
                    ],

                "elapsed_seconds":
                    float(
                        time_s[
                            peak_index
                        ]
                    ),

                "altitude_km":
                    float(
                        altitude_km[
                            peak_index
                        ]
                    ),

                "speed_km_s":
                    float(
                        speed_km_s[
                            peak_index
                        ]
                    ),

                "flight_path_angle_deg":
                    float(
                        fpa_deg[
                            peak_index
                        ]
                    ),

                "latitude_deg":
                    float(
                        latitude_deg[
                            peak_index
                        ]
                    ),

                "longitude_deg":
                    float(
                        longitude_deg[
                            peak_index
                        ]
                    ),

                "kinematic_deceleration_m_s2":
                    float(
                        smoothed_decel_m_s2[
                            peak_index
                        ]
                    ),

                "g0_equivalent":
                    float(
                        smoothed_decel_g[
                            peak_index
                        ]
                    ),
            },
        },

        "raw_gradient_peak": {
            "index":
                int(
                    np.argmax(
                        raw_decel_m_s2
                    )
                ),

            "kinematic_deceleration_m_s2":
                float(
                    np.max(
                        raw_decel_m_s2
                    )
                ),
        },

        "derivative_robustness":
            robustness,

        "skip_rebound":
            skip_summary,

        "vertical_velocity_zero_crossings":
            zero_crossings,

        "altitude_rate_consistency": {
            "overall_max_abs_difference_m_s":
                float(
                    np.max(
                        np.abs(
                            altitude_vertical_difference_m_s
                        )
                    )
                ),

            "interior_median_abs_difference_m_s":
                float(
                    np.median(
                        np.abs(
                            interior_vertical_difference
                        )
                    )
                ),

            "interior_p95_abs_difference_m_s":
                float(
                    np.percentile(
                        np.abs(
                            interior_vertical_difference
                        ),
                        95,
                    )
                ),

            "interior_max_abs_difference_m_s":
                float(
                    np.max(
                        np.abs(
                            interior_vertical_difference
                        )
                    )
                ),
        },

        "altitude_milestones":
            altitude_milestones,

        "speed_milestones":
            speed_milestones,

        "interpretation_limits": [
            (
                "Kinematic deceleration is "
                "-d|v_Earth-relative|/dt."
            ),
            (
                "g0-equivalent values are "
                "unit-scaled kinematic "
                "deceleration only."
            ),
            (
                "Neither quantity is crew "
                "g-load, proper acceleration, "
                "accelerometer output, or "
                "isolated aerodynamic drag."
            ),
            (
                "Skip/rebound events are "
                "derived geometrically from "
                "vertical-velocity sign changes."
            ),
        ],
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

    # --------------------------------------------------------
    # Documentation plots
    # --------------------------------------------------------

    skip_markers = []

    if skip_summary:
        skip_markers = [
            {
                "x":
                    skip_summary[
                        "start"
                    ][
                        "elapsed_seconds"
                    ],

                "y":
                    skip_summary[
                        "start"
                    ][
                        "altitude_km"
                    ],

                "label":
                    "descent → climb",
            },
            {
                "x":
                    skip_summary[
                        "end"
                    ][
                        "elapsed_seconds"
                    ],

                "y":
                    skip_summary[
                        "end"
                    ][
                        "altitude_km"
                    ],

                "label":
                    "climb → descent",
            },
        ]

    make_plot(
        time_s,
        altitude_km,
        "Seconds after Entry Interface",
        "WGS 84 altitude (km)",
        "Artemis II Entry Altitude",
        "phase2c_entry_altitude.svg",
        markers=skip_markers,
    )

    make_plot(
        time_s,
        speed_km_s,
        "Seconds after Entry Interface",
        "Earth-relative speed (km/s)",
        "Artemis II Entry Speed",
        "phase2c_entry_speed.svg",
    )

    make_plot(
        time_s[
            np.isfinite(
                smoothed_decel_m_s2
            )
        ],
        smoothed_decel_m_s2[
            np.isfinite(
                smoothed_decel_m_s2
            )
        ],
        "Seconds after Entry Interface",
        "Kinematic deceleration (m/s²)",
        "Artemis II Kinematic Entry Deceleration",
        "phase2c_entry_kinematic_deceleration.svg",
        markers=[
            {
                "x":
                    time_s[
                        peak_index
                    ],

                "y":
                    smoothed_decel_m_s2[
                        peak_index
                    ],

                "label":
                    "peak",
            }
        ],
    )

    make_plot(
        time_s,
        fpa_deg,
        "Seconds after Entry Interface",
        "Earth-relative flight-path angle (deg)",
        "Artemis II Entry Flight-Path Angle",
        "phase2c_entry_flight_path_angle.svg",
    )

    # --------------------------------------------------------
    # Console summary
    # --------------------------------------------------------

    print()
    print(
        "Artemis II Entry Dynamics"
    )

    print(
        "-------------------------"
    )

    print(
        f"Records: "
        f"{len(rows)}"
    )

    print(
        f"Duration: "
        f"{time_s[-1]:.3f} s"
    )

    print()
    print(
        "Primary kinematic "
        "deceleration estimate:"
    )

    print(
        "  Method: "
        f"{PRIMARY_DERIVATIVE_WINDOW}-sample "
        "local quadratic derivative"
    )

    print(
        f"  UTC: "
        f"{rows[peak_index]['timestamp_utc']}"
    )

    print(
        f"  EI+: "
        f"{time_s[peak_index]:.3f} s"
    )

    print(
        f"  Altitude: "
        f"{altitude_km[peak_index]:.6f} km"
    )

    print(
        f"  Speed: "
        f"{speed_km_s[peak_index]:.6f} km/s"
    )

    print(
        f"  -dV/dt: "
        f"{smoothed_decel_m_s2[peak_index]:.6f} m/s^2"
    )

    print(
        f"  g0-equivalent: "
        f"{smoothed_decel_g[peak_index]:.6f}"
    )

    print()
    print(
        "Derivative robustness:"
    )

    for item in robustness:
        print(
            f"  {item['window_samples']:2d} samples: "
            f"EI+{item['peak_elapsed_seconds']:.3f} s  "
            f"{item['peak_deceleration_m_s2']:.6f} m/s^2"
        )

    if skip_summary:
        print()
        print(
            "Derived skip/rebound:"
        )

        print(
            "  Descent -> climb:"
        )

        print(
            f"    "
            f"{skip_summary['start']['utc']}"
        )

        print(
            f"    EI+"
            f"{skip_summary['start']['elapsed_seconds']:.6f} s"
        )

        print(
            "  Climb -> descent:"
        )

        print(
            f"    "
            f"{skip_summary['end']['utc']}"
        )

        print(
            f"    EI+"
            f"{skip_summary['end']['elapsed_seconds']:.6f} s"
        )

        print(
            f"  Duration: "
            f"{skip_summary['duration_seconds']:.6f} s"
        )

        print(
            f"  Altitude recovery: "
            f"{skip_summary['altitude_recovery_km']:.6f} km"
        )

        print(
            f"  Speed loss: "
            f"{skip_summary['speed_loss_km_s']:.6f} km/s"
        )

    print()
    print(
        "Altitude-rate consistency:"
    )

    print(
        "  Interior median abs: "
        f"{summary['altitude_rate_consistency']['interior_median_abs_difference_m_s']:.6f} m/s"
    )

    print(
        "  Interior p95 abs: "
        f"{summary['altitude_rate_consistency']['interior_p95_abs_difference_m_s']:.6f} m/s"
    )

    print(
        "  Interior max abs: "
        f"{summary['altitude_rate_consistency']['interior_max_abs_difference_m_s']:.6f} m/s"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Kinematic deceleration and "
        "g0-equivalent values are not "
        "crew g-load or proper acceleration."
    )

    print()
    print(
        f"Wrote: "
        f"{OUTPUT_CSV.relative_to(ROOT)}"
    )

    print(
        f"Wrote: "
        f"{OUTPUT_SUMMARY.relative_to(ROOT)}"
    )

    print(
        "Wrote documentation SVGs "
        f"under {ASSET_DIR.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
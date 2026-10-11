from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]

GEOMETRY_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_geometry.csv"
)

DYNAMICS_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_dynamics.csv"
)

SUMMARY_PATH = (
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


def fail(
    message: str,
):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
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


def local_quadratic_derivative(
    time_s,
    values,
    window_size,
):
    half = (
        window_size // 2
    )

    result = np.full(
        len(values),
        np.nan,
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

        result[i] = (
            coefficients[1]
        )

    return result


def crossing(
    t0,
    y0,
    t1,
    y1,
):
    return (
        t0
        + (
            -y0
            / (y1 - y0)
        )
        * (t1 - t0)
    )


def main():
    for path in [
        GEOMETRY_CSV,
        DYNAMICS_CSV,
        SUMMARY_PATH,
    ]:
        if not path.exists():
            fail(
                f"missing required file: "
                f"{path}"
            )

    with GEOMETRY_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        geometry = list(
            csv.DictReader(
                f
            )
        )

    with DYNAMICS_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        dynamics = list(
            csv.DictReader(
                f
            )
        )

    with SUMMARY_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        summary = json.load(
            f
        )

    if (
        len(geometry) != 819
        or len(dynamics) != 819
    ):
        fail(
            "expected 819 records"
        )

    timestamps = [
        parse_utc(
            row[
                "timestamp_utc"
            ]
        )
        for row in geometry
    ]

    start = (
        timestamps[0]
    )

    time_s = np.array(
        [
            (
                timestamp
                - start
            ).total_seconds()
            for timestamp
            in timestamps
        ]
    )

    altitude = np.array(
        [
            float(
                row[
                    "wgs84_altitude_km"
                ]
            )
            for row in geometry
        ]
    )

    speed = np.array(
        [
            float(
                row[
                    "earth_relative_speed_km_s"
                ]
            )
            for row in geometry
        ]
    )

    vertical = np.array(
        [
            float(
                row[
                    "vertical_velocity_km_s"
                ]
            )
            for row in geometry
        ]
    )

    expected_raw_decel = (
        -np.gradient(
            speed,
            time_s,
        )
        * 1000.0
    )

    expected_primary = (
        -local_quadratic_derivative(
            time_s,
            speed,
            7,
        )
        * 1000.0
    )

    max_raw_error = 0.0
    max_primary_error = 0.0

    for i, row in enumerate(
        dynamics
    ):
        if (
            row[
                "timestamp_utc"
            ]
            != geometry[i][
                "timestamp_utc"
            ]
        ):
            fail(
                f"timestamp mismatch "
                f"at record {i + 1}"
            )

        raw_value = float(
            row[
                "raw_kinematic_deceleration_m_s2"
            ]
        )

        max_raw_error = max(
            max_raw_error,
            abs(
                raw_value
                - expected_raw_decel[i]
            ),
        )

        stored_primary = (
            row[
                "smoothed_kinematic_deceleration_m_s2"
            ]
        )

        if np.isfinite(
            expected_primary[i]
        ):
            if stored_primary == "":
                fail(
                    f"missing primary derivative "
                    f"at record {i + 1}"
                )

            max_primary_error = max(
                max_primary_error,
                abs(
                    float(
                        stored_primary
                    )
                    - expected_primary[i]
                ),
            )

        else:
            if stored_primary != "":
                fail(
                    "edge derivative should "
                    "be blank"
                )

    valid = np.isfinite(
        expected_primary
    )

    valid_indices = np.where(
        valid
    )[0]

    peak_index = (
        valid_indices[
            np.argmax(
                expected_primary[
                    valid
                ]
            )
        ]
    )

    observed_peak = (
        summary[
            "primary_derivative"
        ][
            "peak"
        ]
    )

    if abs(
        observed_peak[
            "elapsed_seconds"
        ]
        - time_s[
            peak_index
        ]
    ) > 1e-9:
        fail(
            "primary peak time mismatch"
        )

    if abs(
        observed_peak[
            "kinematic_deceleration_m_s2"
        ]
        - expected_primary[
            peak_index
        ]
    ) > 1e-10:
        fail(
            "primary peak magnitude mismatch"
        )

    # --------------------------------------------------------
    # Derivative robustness
    # --------------------------------------------------------

    robustness_peaks = []

    for window in [
        5,
        7,
        9,
        11,
        15,
    ]:
        decel = (
            -local_quadratic_derivative(
                time_s,
                speed,
                window,
            )
            * 1000.0
        )

        valid = np.isfinite(
            decel
        )

        indices = np.where(
            valid
        )[0]

        local_peak = indices[
            np.argmax(
                decel[
                    valid
                ]
            )
        ]

        robustness_peaks.append(
            (
                time_s[
                    local_peak
                ],
                decel[
                    local_peak
                ],
            )
        )

    peak_times = np.array(
        [
            item[0]
            for item
            in robustness_peaks
        ]
    )

    peak_values = np.array(
        [
            item[1]
            for item
            in robustness_peaks
        ]
    )

    if (
        np.max(
            peak_times
        )
        - np.min(
            peak_times
        )
        > 1.0
    ):
        fail(
            "peak derivative time is "
            "not robust across windows"
        )

    if (
        np.max(
            peak_values
        )
        - np.min(
            peak_values
        )
        > 0.2
    ):
        fail(
            "peak derivative magnitude is "
            "not robust across windows"
        )

    # --------------------------------------------------------
    # Skip/rebound geometry
    # --------------------------------------------------------

    crossings = []

    for i in range(
        1,
        len(vertical),
    ):
        if (
            vertical[i - 1]
            * vertical[i]
            < 0.0
        ):
            crossings.append(
                (
                    crossing(
                        time_s[i - 1],
                        vertical[i - 1],
                        time_s[i],
                        vertical[i],
                    ),
                    vertical[i - 1],
                    vertical[i],
                )
            )

    if len(
        crossings
    ) != 2:
        fail(
            f"expected exactly 2 vertical "
            f"zero crossings, found "
            f"{len(crossings)}"
        )

    if not (
        crossings[0][1] < 0.0
        and crossings[0][2] > 0.0
    ):
        fail(
            "first zero crossing is not "
            "descent-to-climb"
        )

    if not (
        crossings[1][1] > 0.0
        and crossings[1][2] < 0.0
    ):
        fail(
            "second zero crossing is not "
            "climb-to-descent"
        )

    skip = (
        summary[
            "skip_rebound"
        ]
    )

    if skip is None:
        fail(
            "skip summary missing"
        )

    if (
        skip[
            "altitude_recovery_km"
        ]
        <= 0.0
    ):
        fail(
            "skip altitude recovery "
            "is not positive"
        )

    if (
        skip[
            "duration_seconds"
        ]
        <= 0.0
    ):
        fail(
            "skip duration is not positive"
        )

    # --------------------------------------------------------
    # dh/dt consistency
    # --------------------------------------------------------

    altitude_rate = (
        np.gradient(
            altitude,
            time_s,
        )
    )

    difference_m_s = (
        (
            altitude_rate
            - vertical
        )
        * 1000.0
    )

    interior = (
        difference_m_s[
            1:-1
        ]
    )

    median_abs = float(
        np.median(
            np.abs(
                interior
            )
        )
    )

    p95_abs = float(
        np.percentile(
            np.abs(
                interior
            ),
            95,
        )
    )

    max_abs = float(
        np.max(
            np.abs(
                interior
            )
        )
    )

    if median_abs > 0.1:
        fail(
            "median dh/dt consistency "
            "is worse than expected"
        )

    if p95_abs > 0.5:
        fail(
            "p95 dh/dt consistency "
            "is worse than expected"
        )

    if max_abs > 3.0:
        fail(
            "maximum interior dh/dt "
            "consistency is worse "
            "than expected"
        )

    # --------------------------------------------------------
    # Documentation figures
    # --------------------------------------------------------

    expected_assets = [
        (
            ASSET_DIR
            / "phase2c_entry_altitude.svg"
        ),
        (
            ASSET_DIR
            / "phase2c_entry_speed.svg"
        ),
        (
            ASSET_DIR
            / "phase2c_entry_kinematic_deceleration.svg"
        ),
        (
            ASSET_DIR
            / "phase2c_entry_flight_path_angle.svg"
        ),
    ]

    for asset in (
        expected_assets
    ):
        if not asset.exists():
            fail(
                f"missing documentation "
                f"asset: {asset}"
            )

    print()
    print(
        "Artemis II Entry "
        "Dynamics Validation"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Records checked: "
        f"{len(dynamics)}"
    )

    print()
    print(
        "Primary derivative:"
    )

    print(
        "  7-sample local "
        "quadratic fit"
    )

    print(
        f"  Peak EI+: "
        f"{time_s[peak_index]:.3f} s"
    )

    print(
        f"  Peak: "
        f"{expected_primary[peak_index]:.6f} m/s^2"
    )

    print(
        f"  g0-equivalent: "
        f"{expected_primary[peak_index] / G0:.6f}"
    )

    print()
    print(
        "Derivative reconstruction:"
    )

    print(
        "  Raw maximum error: "
        f"{max_raw_error:.12e} m/s^2"
    )

    print(
        "  Smoothed maximum error: "
        f"{max_primary_error:.12e} m/s^2"
    )

    print()
    print(
        "Robustness:"
    )

    print(
        "  Peak-time spread: "
        f"{np.max(peak_times) - np.min(peak_times):.3f} s"
    )

    print(
        "  Peak-magnitude spread: "
        f"{np.max(peak_values) - np.min(peak_values):.6f} m/s^2"
    )

    print()
    print(
        "Skip/rebound:"
    )

    print(
        f"  Start EI+: "
        f"{crossings[0][0]:.6f} s"
    )

    print(
        f"  End EI+: "
        f"{crossings[1][0]:.6f} s"
    )

    print(
        f"  Duration: "
        f"{skip['duration_seconds']:.6f} s"
    )

    print(
        f"  Altitude recovery: "
        f"{skip['altitude_recovery_km']:.6f} km"
    )

    print(
        f"  Speed loss: "
        f"{skip['speed_loss_km_s']:.6f} km/s"
    )

    print()
    print(
        "Altitude-rate consistency:"
    )

    print(
        f"  Interior median abs: "
        f"{median_abs:.6f} m/s"
    )

    print(
        f"  Interior p95 abs: "
        f"{p95_abs:.6f} m/s"
    )

    print(
        f"  Interior max abs: "
        f"{max_abs:.6f} m/s"
    )

    print()
    print(
        "OK: entry dynamics, derivative "
        "robustness, and skip/rebound "
        "geometry validated."
    )

    print()
    print(
        "NOTE: g0-equivalent values are "
        "not crew g-load or proper acceleration."
    )


if __name__ == "__main__":
    main()
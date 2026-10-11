from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]

MACH_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_mach.csv"
)

MODEL_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_rarefaction_model.json"
)

RAREFACTION_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_rarefaction.csv"
)

SUMMARY_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_rarefaction_summary.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
)


def fail(
    message,
):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def mean_free_path(
    number_density,
    collision_diameter,
):
    return (
        1.0
        / (
            math.sqrt(2.0)
            * math.pi
            * collision_diameter**2
            * number_density
        )
    )


def classify(
    kn,
):
    if kn < 0.01:
        return "CONTINUUM"

    if kn < 0.1:
        return "SLIP"

    if kn < 10.0:
        return "TRANSITION"

    return "FREE_MOLECULAR"


def descending_crossings(
    time_s,
    values,
    target,
):
    results = []

    for i in range(
        1,
        len(values),
    ):
        if not (
            values[i - 1] > target
            and values[i] <= target
        ):
            continue

        fraction = (
            target
            - values[i - 1]
        ) / (
            values[i]
            - values[i - 1]
        )

        results.append(
            float(
                time_s[i - 1]
                + fraction
                * (
                    time_s[i]
                    - time_s[i - 1]
                )
            )
        )

    return results


def interp(
    time_s,
    values,
    target,
):
    return float(
        np.interp(
            target,
            time_s,
            values,
        )
    )


def main():
    for path in [
        MACH_CSV,
        MODEL_JSON,
        RAREFACTION_CSV,
        SUMMARY_JSON,
    ]:
        if not path.exists():
            fail(
                f"missing required file: "
                f"{path}"
            )

    with MACH_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        mach_rows = list(
            csv.DictReader(f)
        )

    with RAREFACTION_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        rarefaction_rows = list(
            csv.DictReader(f)
        )

    with MODEL_JSON.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        model = json.load(f)

    with SUMMARY_JSON.open(
        "r",
        encoding="utf-8",
    ) as f:
        summary = json.load(f)

    if not (
        len(mach_rows)
        == len(rarefaction_rows)
        == 819
    ):
        fail(
            "expected 819 aligned states"
        )

    time_s = np.array(
        [
            (
                np.datetime64(
                    row[
                        "timestamp_utc"
                    ].replace(
                        "Z",
                        ""
                    )
                )
                - np.datetime64(
                    mach_rows[0][
                        "timestamp_utc"
                    ].replace(
                        "Z",
                        ""
                    )
                )
            )
            / np.timedelta64(
                1,
                "s",
            )
            for row
            in mach_rows
        ],
        dtype=float,
    )

    altitude = np.array(
        [
            float(
                row[
                    "wgs84_altitude_km"
                ]
            )
            for row
            in mach_rows
        ]
    )

    mach = np.array(
        [
            float(
                row[
                    "modeled_free_stream_mach"
                ]
            )
            for row
            in mach_rows
        ]
    )

    number_density = np.array(
        [
            float(
                row[
                    "thermal_particle_number_density_m3"
                ]
            )
            for row
            in mach_rows
        ]
    )

    dynamic_pressure = np.array(
        [
            float(
                row[
                    "modeled_dynamic_pressure_pa"
                ]
            )
            for row
            in mach_rows
        ]
    )

    characteristic_length = float(
        model[
            "characteristic_length"
        ][
            "value_m"
        ]
    )

    collision_diameter = float(
        model[
            "collision_model"
        ][
            "reference_collision_diameter_m"
        ]
    )

    expected_lambda = np.array(
        [
            mean_free_path(
                n,
                collision_diameter,
            )
            for n
            in number_density
        ]
    )

    expected_kn = (
        expected_lambda
        / characteristic_length
    )

    stored_lambda = np.array(
        [
            float(
                row[
                    "reference_hard_sphere_mean_free_path_m"
                ]
            )
            for row
            in rarefaction_rows
        ]
    )

    stored_kn = np.array(
        [
            float(
                row[
                    "body_scale_knudsen_number"
                ]
            )
            for row
            in rarefaction_rows
        ]
    )

    lambda_error = float(
        np.max(
            np.abs(
                expected_lambda
                - stored_lambda
            )
        )
    )

    kn_error = float(
        np.max(
            np.abs(
                expected_kn
                - stored_kn
            )
        )
    )

    if lambda_error > 1e-12:
        fail(
            "stored mean-free-path mismatch"
        )

    if kn_error > 1e-13:
        fail(
            "stored Knudsen mismatch"
        )

    if classify(
        expected_kn[0]
    ) != "TRANSITION":
        fail(
            "Entry Interface should "
            "be transition regime"
        )

    max_mach_index = int(
        np.argmax(
            mach
        )
    )

    if classify(
        expected_kn[
            max_mach_index
        ]
    ) != "SLIP":
        fail(
            "maximum formal Mach state "
            "should be slip regime"
        )

    expected_threshold_ranges = {
        0.1:
            (
                105.0,
                110.0,
            ),

        0.01:
            (
                92.0,
                96.0,
            ),

        0.001:
            (
                78.0,
                82.0,
            ),
    }

    reconstructed_crossings = {}

    for threshold, (
        low_altitude,
        high_altitude,
    ) in (
        expected_threshold_ranges.items()
    ):
        matches = (
            descending_crossings(
                time_s,
                expected_kn,
                threshold,
            )
        )

        if len(matches) != 1:
            fail(
                f"unexpected Kn={threshold} "
                f"crossing count"
            )

        t = matches[0]

        h = interp(
            time_s,
            altitude,
            t,
        )

        if not (
            low_altitude
            <= h
            <= high_altitude
        ):
            fail(
                f"Kn={threshold} altitude "
                f"outside expected range"
            )

        reconstructed_crossings[
            threshold
        ] = (
            t,
            h,
        )

    sensitivity_altitudes = []

    for diameter in model[
        "collision_model"
    ][
        "sensitivity_collision_diameters_m"
    ]:
        diameter = float(
            diameter
        )

        lambda_values = np.array(
            [
                mean_free_path(
                    n,
                    diameter,
                )
                for n
                in number_density
            ]
        )

        kn_values = (
            lambda_values
            / characteristic_length
        )

        matches = (
            descending_crossings(
                time_s,
                kn_values,
                0.01,
            )
        )

        if len(matches) != 1:
            fail(
                "unexpected sensitivity "
                "crossing count"
            )

        sensitivity_altitudes.append(
            interp(
                time_s,
                altitude,
                matches[0],
            )
        )

    sensitivity_spread = (
        max(
            sensitivity_altitudes
        )
        - min(
            sensitivity_altitudes
        )
    )

    if sensitivity_spread > 2.0:
        fail(
            "collision-diameter sensitivity "
            "moves Kn=0.01 altitude by "
            "more than 2 km"
        )

    local_q_maxima = []

    for i in range(
        1,
        len(
            dynamic_pressure
        ) - 1,
    ):
        if (
            dynamic_pressure[i]
            > dynamic_pressure[i - 1]
            and dynamic_pressure[i]
            >= dynamic_pressure[i + 1]
        ):
            local_q_maxima.append(i)

    local_q_maxima = sorted(
        local_q_maxima,
        key=lambda index:
            dynamic_pressure[index],
        reverse=True,
    )

    if len(
        local_q_maxima
    ) < 2:
        fail(
            "expected two dominant "
            "dynamic-pressure peaks"
        )

    for index in (
        local_q_maxima[:2]
    ):
        if not (
            expected_kn[index]
            < 0.001
        ):
            fail(
                "dominant dynamic-pressure "
                "peak is not below Kn=0.001"
            )

    stored_regime = [
        row[
            "body_scale_rarefaction_regime"
        ]
        for row
        in rarefaction_rows
    ]

    for i, value in enumerate(
        expected_kn
    ):
        if (
            stored_regime[i]
            != classify(value)
        ):
            fail(
                f"regime classification "
                f"mismatch at record {i + 1}"
            )

    expected_assets = [
        (
            ASSET_DIR
            / "phase2e_knudsen_history.svg"
        ),
        (
            ASSET_DIR
            / "phase2e_knudsen_altitude.svg"
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
        "Artemis II Body-Scale "
        "Rarefaction Validation"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Records checked: "
        f"{len(rarefaction_rows)}"
    )

    print()
    print(
        "Independent reconstruction:"
    )

    print(
        f"  Max mean-free-path error: "
        f"{lambda_error:.12e} m"
    )

    print(
        f"  Max Knudsen error: "
        f"{kn_error:.12e}"
    )

    print()
    print(
        "Entry Interface:"
    )

    print(
        f"  Kn: "
        f"{expected_kn[0]:.9f}"
    )

    print(
        f"  regime: "
        f"{classify(expected_kn[0])}"
    )

    print()
    print(
        "Maximum formal Mach state:"
    )

    print(
        f"  altitude: "
        f"{altitude[max_mach_index]:.6f} km"
    )

    print(
        f"  Mach: "
        f"{mach[max_mach_index]:.6f}"
    )

    print(
        f"  Kn: "
        f"{expected_kn[max_mach_index]:.9f}"
    )

    print(
        f"  regime: "
        f"{classify(expected_kn[max_mach_index])}"
    )

    print()
    print(
        "Body-scale Kn crossings:"
    )

    for threshold in [
        0.1,
        0.01,
        0.001,
    ]:
        t, h = (
            reconstructed_crossings[
                threshold
            ]
        )

        print(
            f"  Kn={threshold:g}: "
            f"EI+{t:.6f}s, "
            f"h={h:.6f} km"
        )

    print()
    print(
        "Collision-diameter sensitivity:"
    )

    print(
        "  Kn=0.01 altitude spread: "
        f"{sensitivity_spread:.6f} km"
    )

    print()
    print(
        "Dominant dynamic-pressure peaks:"
    )

    for index in (
        local_q_maxima[:2]
    ):
        print(
            f"  "
            f"{mach_rows[index]['timestamp_utc']}  "
            f"h={altitude[index]:.6f} km  "
            f"Kn={expected_kn[index]:.12e}  "
            f"{classify(expected_kn[index])}"
        )

    print()
    print(
        "OK: body-scale mean free path, "
        "Knudsen number, rarefaction "
        "classification, and sensitivity "
        "validated."
    )

    print()
    print(
        "NOTE: This is a body-scale "
        "continuum indicator, not a "
        "local shock-layer breakdown "
        "criterion."
    )


if __name__ == "__main__":
    main()

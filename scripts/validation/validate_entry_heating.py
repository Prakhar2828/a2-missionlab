from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_rarefaction.csv"
)

MODEL_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_convective_heating_model.json"
)

HEATING_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_heating.csv"
)

SUMMARY_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_heating_summary.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
)


def fail(message):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def parse_utc(value):
    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def interp(
    t,
    y,
    x,
):
    return float(
        np.interp(
            x,
            t,
            y,
        )
    )


def descending_crossing(
    t,
    values,
    target,
):
    matches = []

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

        matches.append(
            float(
                t[i - 1]
                + fraction
                * (
                    t[i]
                    - t[i - 1]
                )
            )
        )

    if not matches:
        fail(
            f"missing descending crossing "
            f"for {target}"
        )

    return matches[-1]


def integrate_between(
    t,
    y,
    start,
    stop,
):
    mask = (
        (t > start)
        & (t < stop)
    )

    tx = np.concatenate(
        (
            [start],
            t[mask],
            [stop],
        )
    )

    yx = np.concatenate(
        (
            [
                interp(
                    t,
                    y,
                    start,
                )
            ],
            y[mask],
            [
                interp(
                    t,
                    y,
                    stop,
                )
            ],
        )
    )

    return float(
        np.trapezoid(
            yx,
            tx,
        )
    )


def main():
    for path in [
        INPUT_CSV,
        MODEL_JSON,
        HEATING_CSV,
        SUMMARY_JSON,
    ]:
        if not path.exists():
            fail(
                f"missing required file: "
                f"{path}"
            )

    with INPUT_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        source = list(
            csv.DictReader(f)
        )

    with HEATING_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        heating = list(
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
        len(source)
        == len(heating)
        == 819
    ):
        fail(
            "expected 819 aligned states"
        )

    for i in range(
        819
    ):
        if (
            source[i][
                "timestamp_utc"
            ]
            != heating[i][
                "timestamp_utc"
            ]
        ):
            fail(
                f"timestamp mismatch "
                f"at record {i + 1}"
            )

    epoch = parse_utc(
        source[0][
            "timestamp_utc"
        ]
    )

    t = np.array(
        [
            (
                parse_utc(
                    row[
                        "timestamp_utc"
                    ]
                )
                - epoch
            ).total_seconds()
            for row in source
        ],
        dtype=float,
    )

    rho = np.array(
        [
            float(
                row[
                    "msis_total_mass_density_kg_m3"
                ]
            )
            for row in source
        ]
    )

    velocity = np.array(
        [
            float(
                row[
                    "earth_relative_speed_km_s"
                ]
            )
            * 1000.0
            for row in source
        ]
    )

    mach = np.array(
        [
            float(
                row[
                    "modeled_free_stream_mach"
                ]
            )
            for row in source
        ]
    )

    kn = np.array(
        [
            float(
                row[
                    "body_scale_knudsen_number"
                ]
            )
            for row in source
        ]
    )

    altitude = np.array(
        [
            float(
                row[
                    "wgs84_altitude_km"
                ]
            )
            for row in source
        ]
    )

    k = float(
        model[
            "correlation"
        ][
            "earth_constant"
        ]
    )

    radius = float(
        model[
            "geometry"
        ][
            "reference_nose_radius_m"
        ]
    )

    expected = (
        k
        * np.sqrt(
            rho
            / radius
        )
        * velocity**3
    )

    stored = np.array(
        [
            float(
                row[
                    "sg_convective_heat_flux_w_m2"
                ]
            )
            for row in heating
        ]
    )

    flux_error = float(
        np.max(
            np.abs(
                expected
                - stored
            )
        )
    )

    if flux_error > 1e-8:
        fail(
            "stored Sutton-Graves "
            "heat-flux mismatch"
        )

    peak_index = int(
        np.argmax(
            expected
        )
    )

    if not (
        80.0
        <= t[
            peak_index
        ]
        <= 90.0
    ):
        fail(
            "SG peak timing outside "
            "expected range"
        )

    if not (
        58.0
        <= altitude[
            peak_index
        ]
        <= 65.0
    ):
        fail(
            "SG peak altitude outside "
            "expected range"
        )

    peak_w_cm2 = (
        expected[
            peak_index
        ]
        / 10000.0
    )

    if not (
        100.0
        <= peak_w_cm2
        <= 120.0
    ):
        fail(
            "SG peak heat flux outside "
            "expected regression range"
        )

    if not (
        kn[
            peak_index
        ]
        < 0.001
    ):
        fail(
            "SG peak should be inside "
            "strong continuum domain"
        )

    primary_start = (
        descending_crossing(
            t,
            kn,
            0.01,
        )
    )

    strong_start = (
        descending_crossing(
            t,
            kn,
            0.001,
        )
    )

    mach5 = (
        descending_crossing(
            t,
            mach,
            5.0,
        )
    )

    full = float(
        np.trapezoid(
            expected,
            t,
        )
    )

    pre_primary = (
        integrate_between(
            t,
            expected,
            t[0],
            primary_start,
        )
    )

    primary = (
        integrate_between(
            t,
            expected,
            primary_start,
            mach5,
        )
    )

    strong = (
        integrate_between(
            t,
            expected,
            strong_start,
            mach5,
        )
    )

    post_mach5 = (
        integrate_between(
            t,
            expected,
            mach5,
            t[-1],
        )
    )

    if not (
        160.0
        <= primary / 1e6
        <= 165.0
    ):
        fail(
            "primary heat load outside "
            "expected regression range"
        )

    if not (
        157.0
        <= strong / 1e6
        <= 162.0
    ):
        fail(
            "strong-domain heat load "
            "outside expected range"
        )

    if not (
        primary
        / full
        > 0.98
    ):
        fail(
            "primary domain contains "
            "less than 98 percent of "
            "formal heat load"
        )

    if not (
        pre_primary
        / full
        < 0.01
    ):
        fail(
            "pre-continuum contribution "
            "exceeds one percent"
        )

    if not (
        post_mach5
        / full
        < 0.01
    ):
        fail(
            "post-Mach-5 contribution "
            "exceeds one percent"
        )

    summary_primary = (
        summary[
            "heat_load"
        ][
            "primary_kn_lt_0_01_mach_ge_5_mj_m2"
        ]
    )

    summary_strong = (
        summary[
            "heat_load"
        ][
            "strong_kn_lt_0_001_mach_ge_5_mj_m2"
        ]
    )

    if abs(
        summary_primary
        - primary / 1e6
    ) > 1e-9:
        fail(
            "summary primary heat load "
            "does not independently reproduce"
        )

    if abs(
        summary_strong
        - strong / 1e6
    ) > 1e-9:
        fail(
            "summary strong heat load "
            "does not independently reproduce"
        )

    radius_cases = (
        summary[
            "nose_radius_sensitivity"
        ]
    )

    if len(
        radius_cases
    ) != 3:
        fail(
            "expected three radius "
            "sensitivity cases"
        )

    low_peak = (
        radius_cases[0][
            "strong_domain_peak_w_cm2"
        ]
    )

    reference_peak = (
        radius_cases[1][
            "strong_domain_peak_w_cm2"
        ]
    )

    high_peak = (
        radius_cases[2][
            "strong_domain_peak_w_cm2"
        ]
    )

    if not (
        low_peak
        > reference_peak
        > high_peak
    ):
        fail(
            "nose-radius sensitivity "
            "does not follow expected "
            "inverse-square-root trend"
        )

    expected_assets = [
        (
            ASSET_DIR
            / "phase2e_sutton_graves_heat_flux.svg"
        ),
        (
            ASSET_DIR
            / "phase2e_sutton_graves_heat_load.svg"
        ),
    ]

    for asset in expected_assets:
        if not asset.exists():
            fail(
                f"missing documentation "
                f"asset: {asset}"
            )

    print()
    print(
        "Artemis II Sutton-Graves "
        "Heating Validation"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Records checked: "
        f"{len(heating)}"
    )

    print()
    print(
        "Independent reconstruction:"
    )

    print(
        f"  Max heat-flux error: "
        f"{flux_error:.12e} W/m^2"
    )

    print()
    print(
        "Qualified SG peak:"
    )

    print(
        f"  UTC: "
        f"{source[peak_index]['timestamp_utc']}"
    )

    print(
        f"  EI+: "
        f"{t[peak_index]:.3f} s"
    )

    print(
        f"  altitude: "
        f"{altitude[peak_index]:.6f} km"
    )

    print(
        f"  heat flux: "
        f"{peak_w_cm2:.6f} W/cm^2"
    )

    print(
        f"  Kn: "
        f"{kn[peak_index]:.12e}"
    )

    print()
    print(
        "Heat-load domains:"
    )

    print(
        f"  primary: "
        f"{primary / 1e6:.9f} MJ/m^2"
    )

    print(
        f"  strong: "
        f"{strong / 1e6:.9f} MJ/m^2"
    )

    print(
        f"  formal full trajectory: "
        f"{full / 1e6:.9f} MJ/m^2"
    )

    print()
    print(
        "Excluded-domain contribution:"
    )

    print(
        f"  before Kn=0.01: "
        f"{100.0 * pre_primary / full:.9f}%"
    )

    print(
        f"  after Mach 5: "
        f"{100.0 * post_mach5 / full:.9f}%"
    )

    print()
    print(
        "OK: Sutton-Graves heat flux, "
        "continuum/hypersonic domain "
        "gating, integrated heat load, "
        "and radius sensitivity validated."
    )

    print()
    print(
        "NOTE: This is a low-fidelity "
        "MODEL-DERIVED cold-wall "
        "stagnation-point convective "
        "heating estimate."
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pymsis


ROOT = Path(__file__).resolve().parents[2]

GEOMETRY_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_geometry.csv"
)

DRIVER_CSV = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_msis_drivers.csv"
)

MACH_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_mach.csv"
)

SUMMARY_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_mach_summary.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
)


R_UNIVERSAL = 8.31446261815324
AVOGADRO = 6.02214076e23

MOLAR_MASS = {
    "N2": 28.0134e-3,
    "O2": 31.9988e-3,
    "O": 15.9994e-3,
    "HE": 4.002602e-3,
    "H": 1.00794e-3,
    "AR": 39.948e-3,
    "N": 14.0067e-3,
}


def fail(
    message: str,
):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def species(
    msis,
    variable,
):
    return np.nan_to_num(
        np.asarray(
            msis[
                ...,
                variable
            ],
            dtype=float,
        ),
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )


def main():
    for path in [
        GEOMETRY_CSV,
        DRIVER_CSV,
        MACH_CSV,
        SUMMARY_JSON,
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
            csv.DictReader(f)
        )

    with DRIVER_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        drivers = list(
            csv.DictReader(f)
        )

    with MACH_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        mach_rows = list(
            csv.DictReader(f)
        )

    with SUMMARY_JSON.open(
        "r",
        encoding="utf-8",
    ) as f:
        summary = json.load(f)

    if not (
        len(geometry)
        == len(drivers)
        == len(mach_rows)
        == 819
    ):
        fail(
            "expected 819 aligned records"
        )

    for i in range(
        819
    ):
        timestamp = geometry[i][
            "timestamp_utc"
        ]

        if (
            drivers[i][
                "timestamp_utc"
            ]
            != timestamp
            or mach_rows[i][
                "timestamp_utc"
            ]
            != timestamp
        ):
            fail(
                f"timestamp mismatch "
                f"at record {i + 1}"
            )

    dates = np.array(
        [
            np.datetime64(
                row[
                    "timestamp_utc"
                ].replace(
                    "Z",
                    ""
                )
            )
            for row
            in geometry
        ]
    )

    longitude = np.array(
        [
            float(
                row[
                    "geodetic_longitude_deg"
                ]
            )
            for row
            in geometry
        ]
    )

    latitude = np.array(
        [
            float(
                row[
                    "geodetic_latitude_deg"
                ]
            )
            for row
            in geometry
        ]
    )

    altitude = np.array(
        [
            float(
                row[
                    "wgs84_altitude_km"
                ]
            )
            for row
            in geometry
        ]
    )

    model_altitude = np.maximum(
        altitude,
        0.0,
    )

    speed = np.array(
        [
            float(
                row[
                    "earth_relative_speed_km_s"
                ]
            )
            * 1000.0
            for row
            in geometry
        ]
    )

    f107 = np.array(
        [
            float(
                row[
                    "f107"
                ]
            )
            for row
            in drivers
        ]
    )

    f107a = np.array(
        [
            float(
                row[
                    "f107a"
                ]
            )
            for row
            in drivers
        ]
    )

    aps = np.array(
        [
            [
                float(
                    row[
                        "ap_daily"
                    ]
                ),
                float(
                    row[
                        "ap_current_3h"
                    ]
                ),
                float(
                    row[
                        "ap_3h_prior"
                    ]
                ),
                float(
                    row[
                        "ap_6h_prior"
                    ]
                ),
                float(
                    row[
                        "ap_9h_prior"
                    ]
                ),
                float(
                    row[
                        "ap_12_to_33h_average"
                    ]
                ),
                float(
                    row[
                        "ap_36_to_57h_average"
                    ]
                ),
            ]
            for row
            in drivers
        ],
        dtype=float,
    )

    msis = pymsis.calculate(
        dates,
        longitude,
        latitude,
        model_altitude,
        f107s=f107,
        f107as=f107a,
        aps=aps,
        version=2.0,
        geomagnetic_activity=-1,
    )

    temperature = np.asarray(
        msis[
            ...,
            pymsis.Variable.TEMPERATURE
        ],
        dtype=float,
    )

    thermal_species = {
        "N2":
            species(
                msis,
                pymsis.Variable.N2,
            ),

        "O2":
            species(
                msis,
                pymsis.Variable.O2,
            ),

        "O":
            species(
                msis,
                pymsis.Variable.O,
            ),

        "HE":
            species(
                msis,
                pymsis.Variable.HE,
            ),

        "H":
            species(
                msis,
                pymsis.Variable.H,
            ),

        "AR":
            species(
                msis,
                pymsis.Variable.AR,
            ),

        "N":
            species(
                msis,
                pymsis.Variable.N,
            ),
    }

    anomalous_o = species(
        msis,
        pymsis.Variable.ANOMALOUS_O,
    )

    n_thermal = np.zeros(
        819
    )

    for values in (
        thermal_species.values()
    ):
        n_thermal += values

    fractions = {
        name:
            values
            / n_thermal

        for name, values
        in thermal_species.items()
    }

    x_diatomic = (
        fractions[
            "N2"
        ]
        + fractions[
            "O2"
        ]
    )

    x_monatomic = (
        fractions[
            "O"
        ]
        + fractions[
            "HE"
        ]
        + fractions[
            "H"
        ]
        + fractions[
            "AR"
        ]
        + fractions[
            "N"
        ]
    )

    gamma = (
        1.0
        + 1.0
        / (
            2.5
            * x_diatomic
            + 1.5
            * x_monatomic
        )
    )

    molar_mass = np.zeros(
        819
    )

    for name, values in (
        fractions.items()
    ):
        molar_mass += (
            values
            * MOLAR_MASS[name]
        )

    r_mix = (
        R_UNIVERSAL
        / molar_mass
    )

    sound_speed = np.sqrt(
        gamma
        * r_mix
        * temperature
    )

    mach = (
        speed
        / sound_speed
    )

    stored_gamma = np.array(
        [
            float(
                row[
                    "modeled_mixture_gamma"
                ]
            )
            for row
            in mach_rows
        ]
    )

    stored_r = np.array(
        [
            float(
                row[
                    "modeled_specific_gas_constant_j_kg_k"
                ]
            )
            for row
            in mach_rows
        ]
    )

    stored_sound_speed = np.array(
        [
            float(
                row[
                    "modeled_sound_speed_m_s"
                ]
            )
            for row
            in mach_rows
        ]
    )

    stored_mach = np.array(
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

    gamma_error = float(
        np.max(
            np.abs(
                gamma
                - stored_gamma
            )
        )
    )

    r_error = float(
        np.max(
            np.abs(
                r_mix
                - stored_r
            )
        )
    )

    sound_error = float(
        np.max(
            np.abs(
                sound_speed
                - stored_sound_speed
            )
        )
    )

    mach_error = float(
        np.max(
            np.abs(
                mach
                - stored_mach
            )
        )
    )

    if gamma_error > 1e-12:
        fail(
            "stored gamma mismatch"
        )

    if r_error > 1e-9:
        fail(
            "stored gas constant mismatch"
        )

    if sound_error > 1e-9:
        fail(
            "stored sound speed mismatch"
        )

    if mach_error > 1e-10:
        fail(
            "stored Mach mismatch"
        )

    max_index = int(
        np.argmax(
            mach
        )
    )

    if not (
        15.0
        <= summary[
            "maximum_formal_free_stream_mach"
        ][
            "ei_elapsed_seconds"
        ]
        <= 25.0
    ):
        fail(
            "maximum Mach timing "
            "outside expected interval"
        )

    if not (
        95.0
        <= altitude[
            max_index
        ]
        <= 105.0
    ):
        fail(
            "maximum Mach altitude "
            "outside expected range"
        )

    if not (
        38.0
        <= mach[
            max_index
        ]
        <= 39.0
    ):
        fail(
            "maximum formal Mach "
            "outside expected range"
        )

    anomalous_fraction = (
        anomalous_o
        / (
            n_thermal
            + anomalous_o
        )
    )

    if (
        np.max(
            anomalous_fraction
        )
        > 1e-12
    ):
        fail(
            "unexpected anomalous-O "
            "contribution"
        )

    thermal_density = np.zeros(
        819
    )

    for name, values in (
        thermal_species.items()
    ):
        thermal_density += (
            values
            * (
                MOLAR_MASS[name]
                / AVOGADRO
            )
        )

    stored_density = np.array(
        [
            float(
                row[
                    "msis_total_mass_density_kg_m3"
                ]
            )
            for row
            in mach_rows
        ]
    )

    mass_difference_percent = (
        100.0
        * np.abs(
            thermal_density
            - stored_density
        )
        / stored_density
    )

    if (
        np.max(
            mass_difference_percent
        )
        > 0.001
    ):
        fail(
            "thermal-species mass "
            "reconstruction differs by "
            "more than 0.001 percent"
        )

    transition_limits = {
        "hypersonic_to_supersonic":
            (
                30.0,
                37.0,
            ),

        "supersonic_to_transonic":
            (
                18.0,
                22.0,
            ),

        "mach_1":
            (
                16.0,
                20.0,
            ),

        "transonic_to_subsonic":
            (
                12.0,
                16.0,
            ),
    }

    transitions = summary[
        "final_flow_regime_transitions"
    ]

    for (
        name,
        (
            minimum_altitude,
            maximum_altitude,
        ),
    ) in transition_limits.items():

        event_altitude = (
            transitions[
                name
            ][
                "altitude_km"
            ]
        )

        if not (
            minimum_altitude
            <= event_altitude
            <= maximum_altitude
        ):
            fail(
                f"{name} altitude outside "
                f"expected validation range"
            )

    expected_crossing_counts = {
        "35":
            2,
        "30":
            2,
        "25":
            2,
        "20":
            1,
        "15":
            1,
        "10":
            1,
        "5":
            1,
        "3":
            1,
        "1.2":
            1,
        "1":
            1,
        "0.8":
            1,
    }

    history = summary[
        "threshold_history"
    ]

    for key, count in (
        expected_crossing_counts.items()
    ):
        if len(
            history[
                key
            ]
        ) != count:
            fail(
                f"unexpected Mach "
                f"{key} crossing count"
            )

    recovery = summary[
        "recovery_event_conditions"
    ]

    if not (
        recovery[
            "drogue_altitude_anchor"
        ][
            "modeled_free_stream_mach"
        ]
        < 1.0
    ):
        fail(
            "drogue anchor should "
            "be subsonic"
        )

    if not (
        recovery[
            "main_altitude_anchor"
        ][
            "modeled_free_stream_mach"
        ]
        < 1.0
    ):
        fail(
            "main anchor should "
            "be subsonic"
        )

    if not (
        recovery[
            "splashdown_correlated_surface_crossing"
        ][
            "modeled_free_stream_mach"
        ]
        < 0.1
    ):
        fail(
            "surface crossing Mach "
            "unexpectedly high"
        )

    if (
        summary[
            "sensitivity"
        ][
            "maximum_absolute_dry_air_mach_difference_below_80_km_percent"
        ]
        > 0.1
    ):
        fail(
            "dry-air sensitivity below "
            "80 km exceeds 0.1 percent"
        )

    expected_assets = [
        (
            ASSET_DIR
            / "phase2e_mach_history.svg"
        ),
        (
            ASSET_DIR
            / "phase2e_flow_regime_timeline.svg"
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
        "Artemis II Free-Stream "
        "Mach Validation"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Records checked: "
        f"{len(mach_rows)}"
    )

    print()
    print(
        "Independent reconstruction:"
    )

    print(
        f"  Max gamma error: "
        f"{gamma_error:.12e}"
    )

    print(
        f"  Max R error: "
        f"{r_error:.12e} J/(kg K)"
    )

    print(
        f"  Max sound-speed error: "
        f"{sound_error:.12e} m/s"
    )

    print(
        f"  Max Mach error: "
        f"{mach_error:.12e}"
    )

    print()
    print(
        "Maximum formal free-stream Mach:"
    )

    print(
        f"  UTC: "
        f"{geometry[max_index]['timestamp_utc']}"
    )

    print(
        f"  altitude: "
        f"{altitude[max_index]:.6f} km"
    )

    print(
        f"  Mach: "
        f"{mach[max_index]:.6f}"
    )

    print()
    print(
        "Thermal-mixture consistency:"
    )

    print(
        "  maximum anomalous-O "
        "particle fraction: "
        f"{100.0 * np.max(anomalous_fraction):.12e}%"
    )

    print(
        "  maximum thermal mass-density "
        "difference: "
        f"{np.max(mass_difference_percent):.12e}%"
    )

    print()
    print(
        "Final flow-regime transitions:"
    )

    for name, state in (
        transitions.items()
    ):
        print(
            f"  {name}: "
            f"EI+"
            f"{state['ei_elapsed_seconds']:.6f}s  "
            f"h={state['altitude_km']:.6f} km"
        )

    print()
    print(
        "Recovery anchors:"
    )

    for name, state in (
        recovery.items()
    ):
        print(
            f"  {name}: "
            f"M="
            f"{state['modeled_free_stream_mach']:.6f}"
        )

    print()
    print(
        "OK: thermal-mixture sound speed, "
        "formal free-stream Mach, and "
        "flow-regime transitions validated."
    )

    print()
    print(
        "NOTE: Highest-altitude Mach values "
        "remain formal estimates until "
        "continuum validity is evaluated."
    )


if __name__ == "__main__":
    main()
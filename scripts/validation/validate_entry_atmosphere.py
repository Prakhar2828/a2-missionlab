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

ATMOSPHERE_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_atmosphere.csv"
)

SUMMARY_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_atmosphere_summary.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
)

MODEL_VERSION = 2.0
GEOMAGNETIC_ACTIVITY = -1


def fail(
    message: str,
):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def main():
    for path in [
        GEOMETRY_CSV,
        DRIVER_CSV,
        ATMOSPHERE_CSV,
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

    with ATMOSPHERE_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        atmosphere = list(
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
        == len(atmosphere)
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
            or atmosphere[i][
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

    trajectory_altitude = np.array(
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
        trajectory_altitude,
        0.0,
    )

    speed = np.array(
        [
            float(
                row[
                    "earth_relative_speed_km_s"
                ]
            )
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

    expected = pymsis.calculate(
        dates,
        longitude,
        latitude,
        model_altitude,
        f107s=f107,
        f107as=f107a,
        aps=aps,
        version=MODEL_VERSION,
        geomagnetic_activity=(
            GEOMAGNETIC_ACTIVITY
        ),
    )

    expected_density = np.asarray(
        expected[
            ...,
            pymsis.Variable.MASS_DENSITY
        ],
        dtype=float,
    )

    expected_temperature = np.asarray(
        expected[
            ...,
            pymsis.Variable.TEMPERATURE
        ],
        dtype=float,
    )

    stored_density = np.array(
        [
            float(
                row[
                    "msis_total_mass_density_kg_m3"
                ]
            )
            for row
            in atmosphere
        ]
    )

    stored_temperature = np.array(
        [
            float(
                row[
                    "msis_neutral_temperature_k"
                ]
            )
            for row
            in atmosphere
        ]
    )

    stored_q = np.array(
        [
            float(
                row[
                    "modeled_dynamic_pressure_pa"
                ]
            )
            for row
            in atmosphere
        ]
    )

    expected_q = (
        0.5
        * expected_density
        * (
            speed
            * 1000.0
        ) ** 2
    )

    density_error = np.max(
        np.abs(
            expected_density
            - stored_density
        )
    )

    temperature_error = np.max(
        np.abs(
            expected_temperature
            - stored_temperature
        )
    )

    q_error = np.max(
        np.abs(
            expected_q
            - stored_q
        )
    )

    if density_error > 1e-15:
        fail(
            "stored MSIS density does not "
            "match independent reconstruction"
        )

    if temperature_error > 1e-10:
        fail(
            "stored neutral temperature "
            "does not match reconstruction"
        )

    if q_error > 1e-8:
        fail(
            "stored dynamic pressure does "
            "not match independent calculation"
        )

    if int(
        np.sum(
            trajectory_altitude < 0.0
        )
    ) != 1:
        fail(
            "unexpected negative-altitude "
            "state count"
        )

    peak_q_index = int(
        np.argmax(
            expected_q
        )
    )

    peak_q_kpa = (
        expected_q[
            peak_q_index
        ]
        / 1000.0
    )

    if not (
        35.0
        <= trajectory_altitude[
            peak_q_index
        ]
        <= 45.0
    ):
        fail(
            "global modeled q peak occurs "
            "outside expected altitude range"
        )

    if not (
        12.0
        <= peak_q_kpa
        <= 14.0
    ):
        fail(
            "global modeled q peak outside "
            "expected magnitude range"
        )

    if not (
        expected_q[0]
        < 2.0
    ):
        fail(
            "Entry Interface modeled q "
            "unexpectedly high"
        )

    local_maxima = []

    for i in range(
        1,
        len(
            expected_q
        ) - 1,
    ):
        if (
            expected_q[i]
            > expected_q[
                i - 1
            ]
            and expected_q[i]
            >= expected_q[
                i + 1
            ]
        ):
            local_maxima.append(i)

    local_maxima = sorted(
        local_maxima,
        key=lambda index:
            expected_q[index],
        reverse=True,
    )

    if len(
        local_maxima
    ) < 2:
        fail(
            "expected at least two "
            "dynamic-pressure local maxima"
        )

    first_two = (
        local_maxima[:2]
    )

    q_difference_fraction = (
        abs(
            expected_q[
                first_two[0]
            ]
            - expected_q[
                first_two[1]
            ]
        )
        / expected_q[
            first_two[0]
        ]
    )

    if (
        q_difference_fraction
        > 0.01
    ):
        fail(
            "two dominant modeled q peaks "
            "differ by more than 1 percent"
        )

    # Permanent 2.0 vs 2.1 sensitivity check.
    comparison = pymsis.calculate(
        dates,
        longitude,
        latitude,
        model_altitude,
        f107s=f107,
        f107as=f107a,
        aps=aps,
        version=2.1,
        geomagnetic_activity=(
            GEOMAGNETIC_ACTIVITY
        ),
    )

    density21 = np.asarray(
        comparison[
            ...,
            pymsis.Variable.MASS_DENSITY
        ],
        dtype=float,
    )

    temperature21 = np.asarray(
        comparison[
            ...,
            pymsis.Variable.TEMPERATURE
        ],
        dtype=float,
    )

    density_version_difference = np.max(
        np.abs(
            density21
            - expected_density
        )
        / expected_density
    )

    temperature_version_difference = np.max(
        np.abs(
            temperature21
            - expected_temperature
        )
    )

    boundary = summary[
        "utc_driver_boundary_control"
    ]

    if abs(
        boundary[
            "driver_only_density_effect_percent"
        ]
    ) > 1e-9:
        fail(
            "UTC driver boundary control "
            "shows unexpected density effect"
        )

    expected_assets = [
        (
            ASSET_DIR
            / "phase2e_density.svg"
        ),
        (
            ASSET_DIR
            / "phase2e_dynamic_pressure.svg"
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
        "Atmosphere Validation"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Records checked: "
        f"{len(atmosphere)}"
    )

    print()
    print(
        "Independent reconstruction:"
    )

    print(
        "  Max density error: "
        f"{density_error:.12e} kg/m^3"
    )

    print(
        "  Max temperature error: "
        f"{temperature_error:.12e} K"
    )

    print(
        "  Max dynamic-pressure error: "
        f"{q_error:.12e} Pa"
    )

    print()
    print(
        "Entry Interface:"
    )

    print(
        f"  density: "
        f"{expected_density[0]:.12e} kg/m^3"
    )

    print(
        f"  q: "
        f"{expected_q[0]:.6f} Pa"
    )

    print()
    print(
        "Global modeled q peak:"
    )

    print(
        f"  UTC: "
        f"{geometry[peak_q_index]['timestamp_utc']}"
    )

    print(
        f"  altitude: "
        f"{trajectory_altitude[peak_q_index]:.6f} km"
    )

    print(
        f"  speed: "
        f"{speed[peak_q_index]:.6f} km/s"
    )

    print(
        f"  q: "
        f"{peak_q_kpa:.6f} kPa"
    )

    print()
    print(
        "Two dominant local q peaks:"
    )

    for index in (
        first_two
    ):
        print(
            f"  {geometry[index]['timestamp_utc']}  "
            f"h={trajectory_altitude[index]:.6f} km  "
            f"q={expected_q[index] / 1000.0:.6f} kPa"
        )

    print(
        "  relative magnitude difference: "
        f"{100.0 * q_difference_fraction:.6f}%"
    )

    print()
    print(
        "NRLMSIS 2.0 vs 2.1:"
    )

    print(
        "  max relative density "
        "difference: "
        f"{100.0 * density_version_difference:.12f}%"
    )

    print(
        "  max temperature difference: "
        f"{temperature_version_difference:.12e} K"
    )

    print()
    print(
        "UTC boundary control:"
    )

    print(
        "  observed trajectory density "
        "change: "
        f"{boundary['observed_density_change_percent']:+.9f}%"
    )

    print(
        "  driver-only density effect: "
        f"{boundary['driver_only_density_effect_percent']:+.12f}%"
    )

    print(
        "  interpretation: descent through "
        "the atmospheric density gradient"
    )

    print()
    print(
        "OK: NRLMSIS atmosphere, pinned "
        "drivers, and modeled dynamic "
        "pressure validated."
    )

    print()
    print(
        "NOTE: Dynamic pressure is "
        "MODEL-DERIVED and assumes "
        "zero local atmospheric wind."
    )


if __name__ == "__main__":
    main()
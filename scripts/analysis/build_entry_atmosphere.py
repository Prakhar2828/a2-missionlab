from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
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

DYNAMICS_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_dynamics.csv"
)

DRIVER_CSV = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_msis_drivers.csv"
)

ENVIRONMENT_METADATA = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_msis_environment.json"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_atmosphere.csv"
)

OUTPUT_SUMMARY = (
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
EXPECTED_PYMSIS_VERSION = "0.12.0"

GEOMAGNETIC_ACTIVITY = -1

PA_TO_PSF = 0.020885434273039


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


def local_maxima(
    values: np.ndarray,
):
    result = []

    for i in range(
        1,
        len(values) - 1,
    ):
        if (
            values[i] > values[i - 1]
            and values[i] >= values[i + 1]
        ):
            result.append(i)

    return result


def load_drivers(
    rows,
):
    with DRIVER_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        driver_rows = list(
            csv.DictReader(f)
        )

    if len(
        driver_rows
    ) != len(rows):
        raise SystemExit(
            "Driver and trajectory "
            "record counts differ."
        )

    for i, (
        trajectory_row,
        driver_row,
    ) in enumerate(
        zip(
            rows,
            driver_rows,
        ),
        start=1,
    ):
        if (
            trajectory_row[
                "timestamp_utc"
            ]
            != driver_row[
                "timestamp_utc"
            ]
        ):
            raise SystemExit(
                f"Driver timestamp mismatch "
                f"at record {i}."
            )

    f107 = np.array(
        [
            float(
                row[
                    "f107"
                ]
            )
            for row
            in driver_rows
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
            in driver_rows
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
            in driver_rows
        ],
        dtype=float,
    )

    return (
        driver_rows,
        f107,
        f107a,
        aps,
    )


def main():
    if (
        pymsis.__version__
        != EXPECTED_PYMSIS_VERSION
    ):
        raise SystemExit(
            "Unexpected pymsis version.\n"
            f"Expected: "
            f"{EXPECTED_PYMSIS_VERSION}\n"
            f"Observed: "
            f"{pymsis.__version__}"
        )

    for path in [
        GEOMETRY_CSV,
        DYNAMICS_CSV,
        DRIVER_CSV,
        ENVIRONMENT_METADATA,
    ]:
        if not path.exists():
            raise SystemExit(
                f"Missing required file:\n"
                f"{path}"
            )

    with GEOMETRY_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(f)

        input_fields = (
            reader.fieldnames
            or []
        )

        rows = list(reader)

    with DYNAMICS_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        dynamics_rows = list(
            csv.DictReader(f)
        )

    with ENVIRONMENT_METADATA.open(
        "r",
        encoding="utf-8",
    ) as f:
        environment_metadata = (
            json.load(f)
        )

    if len(rows) != 819:
        raise SystemExit(
            f"Expected 819 geometry states, "
            f"found {len(rows)}."
        )

    if len(dynamics_rows) != 819:
        raise SystemExit(
            "Expected 819 dynamics states."
        )

    (
        driver_rows,
        f107,
        f107a,
        aps,
    ) = load_drivers(
        rows
    )

    timestamps = [
        parse_utc(
            row[
                "timestamp_utc"
            ]
        )
        for row
        in rows
    ]

    start = timestamps[0]

    time_s = np.array(
        [
            (
                timestamp
                - start
            ).total_seconds()
            for timestamp
            in timestamps
        ],
        dtype=float,
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
            in rows
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
            in rows
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
            in rows
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
            in rows
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
            for row
            in rows
        ]
    )

    output = pymsis.calculate(
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

    density = np.asarray(
        output[
            ...,
            pymsis.Variable.MASS_DENSITY
        ],
        dtype=float,
    )

    temperature = np.asarray(
        output[
            ...,
            pymsis.Variable.TEMPERATURE
        ],
        dtype=float,
    )

    if not np.all(
        np.isfinite(
            density
        )
    ):
        raise SystemExit(
            "Non-finite model density found."
        )

    if not np.all(
        density > 0.0
    ):
        raise SystemExit(
            "Non-positive model density found."
        )

    speed_m_s = (
        speed
        * 1000.0
    )

    # MODEL-DERIVED dynamic pressure using
    # Earth-relative velocity. This assumes
    # zero local atmospheric wind relative
    # to the rotating Earth-fixed frame.
    dynamic_pressure_pa = (
        0.5
        * density
        * speed_m_s**2
    )

    peak_q_index = int(
        np.argmax(
            dynamic_pressure_pa
        )
    )

    local_q_indices = (
        local_maxima(
            dynamic_pressure_pa
        )
    )

    local_q_indices = sorted(
        local_q_indices,
        key=lambda index:
            dynamic_pressure_pa[index],
        reverse=True,
    )

    smoothed_decel = np.array(
        [
            (
                np.nan
                if row[
                    "smoothed_kinematic_deceleration_m_s2"
                ] == ""
                else float(
                    row[
                        "smoothed_kinematic_deceleration_m_s2"
                    ]
                )
            )
            for row
            in dynamics_rows
        ]
    )

    valid_decel = np.isfinite(
        smoothed_decel
    )

    valid_decel_indices = np.where(
        valid_decel
    )[0]

    peak_decel_index = (
        valid_decel_indices[
            np.argmax(
                smoothed_decel[
                    valid_decel
                ]
            )
        ]
    )

    output_rows = []

    for i, row in enumerate(
        rows
    ):
        result = dict(row)

        result.update(
            {
                "msis_model_altitude_km":
                    model_altitude[i],

                "msis_altitude_clipped":
                    bool(
                        altitude[i] < 0.0
                    ),

                "msis_total_mass_density_kg_m3":
                    density[i],

                "msis_neutral_temperature_k":
                    temperature[i],

                "modeled_dynamic_pressure_pa":
                    dynamic_pressure_pa[i],

                "modeled_dynamic_pressure_kpa":
                    (
                        dynamic_pressure_pa[i]
                        / 1000.0
                    ),
            }
        )

        output_rows.append(
            result
        )

    appended_fields = [
        "msis_model_altitude_km",
        "msis_altitude_clipped",
        "msis_total_mass_density_kg_m3",
        "msis_neutral_temperature_k",
        "modeled_dynamic_pressure_pa",
        "modeled_dynamic_pressure_kpa",
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

    dominant_q_peaks = []

    for index in (
        local_q_indices[:5]
    ):
        dominant_q_peaks.append(
            {
                "utc":
                    rows[index][
                        "timestamp_utc"
                    ],

                "ei_elapsed_seconds":
                    float(
                        time_s[index]
                    ),

                "altitude_km":
                    float(
                        altitude[index]
                    ),

                "earth_relative_speed_km_s":
                    float(
                        speed[index]
                    ),

                "density_kg_m3":
                    float(
                        density[index]
                    ),

                "dynamic_pressure_pa":
                    float(
                        dynamic_pressure_pa[
                            index
                        ]
                    ),
            }
        )

    summary = {
        "model": {
            "name":
                "NRLMSIS",

            "version":
                MODEL_VERSION,

            "implementation":
                "pymsis",

            "pymsis_version":
                pymsis.__version__,

            "geomagnetic_activity":
                GEOMAGNETIC_ACTIVITY,

            "driver_snapshot":
                DRIVER_CSV.name,

            "space_weather_source_sha256":
                environment_metadata[
                    "space_weather_source"
                ][
                    "sha256"
                ],
        },

        "provenance": {
            "density":
                "MODEL",

            "neutral_temperature":
                "MODEL",

            "earth_relative_speed":
                "DERIVED_FROM_NASA_FLIGHT_DERIVED_EPHEMERIS",

            "dynamic_pressure":
                "MODEL_DERIVED",
        },

        "records":
            len(rows),

        "negative_altitude_states_clipped_to_zero_km":
            int(
                np.sum(
                    altitude < 0.0
                )
            ),

        "entry_interface": {
            "utc":
                rows[0][
                    "timestamp_utc"
                ],

            "altitude_km":
                float(
                    altitude[0]
                ),

            "density_kg_m3":
                float(
                    density[0]
                ),

            "neutral_temperature_k":
                float(
                    temperature[0]
                ),

            "dynamic_pressure_pa":
                float(
                    dynamic_pressure_pa[0]
                ),
        },

        "global_peak_dynamic_pressure": {
            "utc":
                rows[
                    peak_q_index
                ][
                    "timestamp_utc"
                ],

            "ei_elapsed_seconds":
                float(
                    time_s[
                        peak_q_index
                    ]
                ),

            "altitude_km":
                float(
                    altitude[
                        peak_q_index
                    ]
                ),

            "earth_relative_speed_km_s":
                float(
                    speed[
                        peak_q_index
                    ]
                ),

            "density_kg_m3":
                float(
                    density[
                        peak_q_index
                    ]
                ),

            "neutral_temperature_k":
                float(
                    temperature[
                        peak_q_index
                    ]
                ),

            "dynamic_pressure_pa":
                float(
                    dynamic_pressure_pa[
                        peak_q_index
                    ]
                ),

            "dynamic_pressure_psf":
                float(
                    dynamic_pressure_pa[
                        peak_q_index
                    ]
                    * PA_TO_PSF
                ),
        },

        "at_peak_kinematic_deceleration": {
            "utc":
                rows[
                    peak_decel_index
                ][
                    "timestamp_utc"
                ],

            "ei_elapsed_seconds":
                float(
                    time_s[
                        peak_decel_index
                    ]
                ),

            "altitude_km":
                float(
                    altitude[
                        peak_decel_index
                    ]
                ),

            "kinematic_deceleration_m_s2":
                float(
                    smoothed_decel[
                        peak_decel_index
                    ]
                ),

            "density_kg_m3":
                float(
                    density[
                        peak_decel_index
                    ]
                ),

            "dynamic_pressure_pa":
                float(
                    dynamic_pressure_pa[
                        peak_decel_index
                    ]
                ),
        },

        "largest_dynamic_pressure_local_maxima":
            dominant_q_peaks,

        "utc_driver_boundary_control":
            environment_metadata[
                "utc_boundary_control"
            ],

        "interpretation_limits": [
            (
                "NRLMSIS density and neutral "
                "temperature are empirical "
                "atmospheric MODEL quantities."
            ),
            (
                "Dynamic pressure is calculated "
                "as 0.5*rho*V^2 using modeled "
                "density and Earth-relative "
                "trajectory speed."
            ),
            (
                "The dynamic-pressure calculation "
                "assumes zero local atmospheric "
                "wind relative to the rotating "
                "Earth-fixed frame."
            ),
            (
                "No aerodynamic coefficient, "
                "vehicle force model, Mach-number "
                "model, heating correlation, or "
                "thermal-protection model is "
                "applied in Phase 2E.1."
            ),
            (
                "At very high altitude the "
                "continuum interpretation of "
                "dynamic pressure should be used "
                "with appropriate rarefied-flow "
                "caution."
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

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    density_figure = (
        ASSET_DIR
        / "phase2e_density.svg"
    )

    fig, ax = plt.subplots()

    ax.plot(
        time_s,
        density,
    )

    ax.set_yscale(
        "log"
    )

    ax.set_xlabel(
        "Seconds after Entry Interface"
    )

    ax.set_ylabel(
        "NRLMSIS total mass density (kg/m³)"
    )

    ax.set_title(
        "Artemis II Modeled Atmospheric Density"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        density_figure,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(fig)

    normalize_svg(
        density_figure
    )

    q_figure = (
        ASSET_DIR
        / "phase2e_dynamic_pressure.svg"
    )

    fig, ax = plt.subplots()

    ax.plot(
        time_s,
        dynamic_pressure_pa
        / 1000.0,
    )

    for index, label in [
        (
            local_q_indices[1],
            "early q peak",
        ),
        (
            peak_q_index,
            "global q peak",
        ),
        (
            peak_decel_index,
            "peak kinematic decel",
        ),
    ]:
        ax.scatter(
            [
                time_s[index]
            ],
            [
                dynamic_pressure_pa[
                    index
                ]
                / 1000.0
            ],
        )

        ax.annotate(
            label,
            (
                time_s[index],
                dynamic_pressure_pa[
                    index
                ]
                / 1000.0,
            ),
        )

    ax.set_xlabel(
        "Seconds after Entry Interface"
    )

    ax.set_ylabel(
        "Modeled dynamic pressure (kPa)"
    )

    ax.set_title(
        "Artemis II Modeled Dynamic Pressure"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        q_figure,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(fig)

    normalize_svg(
        q_figure
    )

    print()
    print(
        "Artemis II Entry Atmosphere"
    )

    print(
        "----------------------------"
    )

    print(
        "Model: NRLMSIS 2.0"
    )

    print(
        f"pymsis: "
        f"{pymsis.__version__}"
    )

    print(
        f"Records: "
        f"{len(rows)}"
    )

    print(
        "Negative-altitude states "
        "clipped to 0 km: "
        f"{summary['negative_altitude_states_clipped_to_zero_km']}"
    )

    print()
    print(
        "Entry Interface:"
    )

    print(
        f"  density: "
        f"{density[0]:.12e} kg/m^3"
    )

    print(
        f"  neutral temperature: "
        f"{temperature[0]:.3f} K"
    )

    print(
        f"  modeled q: "
        f"{dynamic_pressure_pa[0]:.6f} Pa"
    )

    print()
    print(
        "Global peak modeled "
        "dynamic pressure:"
    )

    print(
        f"  UTC: "
        f"{rows[peak_q_index]['timestamp_utc']}"
    )

    print(
        f"  EI+: "
        f"{time_s[peak_q_index]:.3f} s"
    )

    print(
        f"  altitude: "
        f"{altitude[peak_q_index]:.6f} km"
    )

    print(
        f"  speed: "
        f"{speed[peak_q_index]:.6f} km/s"
    )

    print(
        f"  density: "
        f"{density[peak_q_index]:.12e} kg/m^3"
    )

    print(
        f"  q: "
        f"{dynamic_pressure_pa[peak_q_index] / 1000.0:.6f} kPa"
    )

    print()
    print(
        "At peak kinematic deceleration:"
    )

    print(
        f"  UTC: "
        f"{rows[peak_decel_index]['timestamp_utc']}"
    )

    print(
        f"  altitude: "
        f"{altitude[peak_decel_index]:.6f} km"
    )

    print(
        f"  density: "
        f"{density[peak_decel_index]:.12e} kg/m^3"
    )

    print(
        f"  q: "
        f"{dynamic_pressure_pa[peak_decel_index] / 1000.0:.6f} kPa"
    )

    print()
    print(
        "Largest local q maxima:"
    )

    for peak in (
        dominant_q_peaks[:5]
    ):
        print(
            f"  {peak['utc']}  "
            f"EI+{peak['ei_elapsed_seconds']:7.3f}s  "
            f"h={peak['altitude_km']:8.3f} km  "
            f"q={peak['dynamic_pressure_pa'] / 1000.0:9.5f} kPa"
        )

    print()
    print(
        "UTC-driver boundary:"
    )

    print(
        "  driver-only density effect: "
        f"{environment_metadata['utc_boundary_control']['driver_only_density_effect_percent']:.12f}%"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Density and temperature are MODEL."
    )

    print(
        "Dynamic pressure is MODEL-DERIVED."
    )

    print(
        "Dynamic pressure assumes zero "
        "local atmospheric wind."
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
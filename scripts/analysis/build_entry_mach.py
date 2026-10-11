from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
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

ATMOSPHERE_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_atmosphere.csv"
)

DRIVER_CSV = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_msis_drivers.csv"
)

EVENT_REFERENCE_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_events.json"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_mach.csv"
)

OUTPUT_SUMMARY = (
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


EXPECTED_PYMSIS_VERSION = "0.12.0"
MODEL_VERSION = 2.0
GEOMAGNETIC_ACTIVITY = -1

R_UNIVERSAL = 8.31446261815324
AVOGADRO = 6.02214076e23

R_DRY_AIR = 287.05287
GAMMA_DRY_AIR = 1.4

FT_TO_KM = 0.0003048

MOLAR_MASS = {
    "N2": 28.0134e-3,
    "O2": 31.9988e-3,
    "O": 15.9994e-3,
    "HE": 4.002602e-3,
    "H": 1.00794e-3,
    "AR": 39.948e-3,
    "N": 14.0067e-3,
}

MACH_THRESHOLDS = [
    35.0,
    30.0,
    25.0,
    20.0,
    15.0,
    10.0,
    5.0,
    3.0,
    1.2,
    1.0,
    0.8,
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


def interpolate_crossing(
    t0,
    y0,
    t1,
    y1,
    target,
):
    if y1 == y0:
        return float(t0)

    fraction = (
        target - y0
    ) / (
        y1 - y0
    )

    return float(
        t0
        + fraction
        * (
            t1 - t0
        )
    )


def all_crossings(
    time_s,
    values,
    target,
):
    crossings = []

    for i in range(
        1,
        len(values),
    ):
        before = (
            values[i - 1]
            - target
        )

        after = (
            values[i]
            - target
        )

        if (
            before < 0.0
            and after >= 0.0
        ):
            direction = "ASCENDING"

        elif (
            before > 0.0
            and after <= 0.0
        ):
            direction = "DESCENDING"

        else:
            continue

        crossing = (
            interpolate_crossing(
                time_s[i - 1],
                values[i - 1],
                time_s[i],
                values[i],
                target,
            )
        )

        crossings.append(
            (
                direction,
                crossing,
            )
        )

    return crossings


def descending_crossing(
    time_s,
    values,
    target,
):
    matches = [
        crossing
        for direction, crossing
        in all_crossings(
            time_s,
            values,
            target,
        )
        if (
            direction
            == "DESCENDING"
        )
    ]

    if not matches:
        return None

    return float(
        matches[-1]
    )


def interp(
    time_s,
    values,
    target_time,
):
    return float(
        np.interp(
            target_time,
            time_s,
            values,
        )
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


def classify_mach(
    mach_value,
):
    if mach_value >= 5.0:
        return "HYPERSONIC"

    if mach_value >= 1.2:
        return "SUPERSONIC"

    if mach_value >= 0.8:
        return "TRANSONIC"

    return "SUBSONIC"


def crossing_state(
    start,
    crossing,
    time_s,
    altitude,
    speed,
    sound_speed,
    mach,
):
    utc = (
        start
        + timedelta(
            seconds=float(
                crossing
            )
        )
    )

    return {
        "utc":
            format_utc(utc),

        "ei_elapsed_seconds":
            float(crossing),

        "altitude_km":
            interp(
                time_s,
                altitude,
                crossing,
            ),

        "earth_relative_speed_m_s":
            interp(
                time_s,
                speed,
                crossing,
            ),

        "modeled_sound_speed_m_s":
            interp(
                time_s,
                sound_speed,
                crossing,
            ),

        "modeled_free_stream_mach":
            interp(
                time_s,
                mach,
                crossing,
            ),
    }


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
        ATMOSPHERE_CSV,
        DRIVER_CSV,
        EVENT_REFERENCE_JSON,
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
        geometry = list(
            csv.DictReader(f)
        )

    with ATMOSPHERE_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(f)

        atmosphere_fields = (
            reader.fieldnames
            or []
        )

        atmosphere = list(reader)

    with DRIVER_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        drivers = list(
            csv.DictReader(f)
        )

    with EVENT_REFERENCE_JSON.open(
        "r",
        encoding="utf-8",
    ) as f:
        event_reference = json.load(f)

    if not (
        len(geometry)
        == len(atmosphere)
        == len(drivers)
        == 819
    ):
        raise SystemExit(
            "Expected 819 aligned states."
        )

    for i in range(
        819
    ):
        timestamp = geometry[i][
            "timestamp_utc"
        ]

        if (
            atmosphere[i][
                "timestamp_utc"
            ]
            != timestamp
            or drivers[i][
                "timestamp_utc"
            ]
            != timestamp
        ):
            raise SystemExit(
                f"Timestamp mismatch "
                f"at record {i + 1}."
            )

    timestamps = [
        parse_utc(
            row[
                "timestamp_utc"
            ]
        )
        for row
        in geometry
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

    dynamic_pressure = np.array(
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
        version=MODEL_VERSION,
        geomagnetic_activity=(
            GEOMAGNETIC_ACTIVITY
        ),
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
        len(time_s),
        dtype=float,
    )

    for values in (
        thermal_species.values()
    ):
        n_thermal += values

    if not np.all(
        n_thermal > 0.0
    ):
        raise SystemExit(
            "Non-positive thermal "
            "particle density."
        )

    mole_fraction = {
        name:
            values
            / n_thermal

        for name, values
        in thermal_species.items()
    }

    x_diatomic = (
        mole_fraction[
            "N2"
        ]
        + mole_fraction[
            "O2"
        ]
    )

    x_monatomic = (
        mole_fraction[
            "O"
        ]
        + mole_fraction[
            "HE"
        ]
        + mole_fraction[
            "H"
        ]
        + mole_fraction[
            "AR"
        ]
        + mole_fraction[
            "N"
        ]
    )

    cv_over_r = (
        2.5
        * x_diatomic
        + 1.5
        * x_monatomic
    )

    gamma = (
        1.0
        + 1.0
        / cv_over_r
    )

    mixture_molar_mass = np.zeros(
        len(time_s),
        dtype=float,
    )

    for name, values in (
        mole_fraction.items()
    ):
        mixture_molar_mass += (
            values
            * MOLAR_MASS[name]
        )

    r_mix = (
        R_UNIVERSAL
        / mixture_molar_mass
    )

    pressure = (
        n_thermal
        * (
            R_UNIVERSAL
            / AVOGADRO
        )
        * temperature
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

    dry_sound_speed = np.sqrt(
        GAMMA_DRY_AIR
        * R_DRY_AIR
        * temperature
    )

    dry_mach = (
        speed
        / dry_sound_speed
    )

    thermal_density = np.zeros(
        len(time_s),
        dtype=float,
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

    thermal_density_difference_percent = (
        100.0
        * (
            thermal_density
            - stored_density
        )
        / stored_density
    )

    anomalous_fraction = (
        anomalous_o
        / (
            n_thermal
            + anomalous_o
        )
    )

    dry_mach_difference_percent = (
        100.0
        * (
            mach
            - dry_mach
        )
        / dry_mach
    )

    max_mach_index = int(
        np.argmax(
            mach
        )
    )

    peak_q_index = int(
        np.argmax(
            dynamic_pressure
        )
    )

    q_local_maxima = []

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
            q_local_maxima.append(i)

    early_q_index = min(
        q_local_maxima,
        key=lambda index:
            abs(
                time_s[index]
                - 95.0
            ),
    )

    threshold_history = {}

    for threshold in (
        MACH_THRESHOLDS
    ):
        key = (
            f"{threshold:g}"
        )

        threshold_history[key] = []

        for direction, crossing in (
            all_crossings(
                time_s,
                mach,
                threshold,
            )
        ):
            state = crossing_state(
                start,
                crossing,
                time_s,
                altitude,
                speed,
                sound_speed,
                mach,
            )

            state[
                "direction"
            ] = direction

            threshold_history[
                key
            ].append(
                state
            )

    final_transitions = {}

    for (
        name,
        threshold,
    ) in [
        (
            "hypersonic_to_supersonic",
            5.0,
        ),
        (
            "supersonic_to_transonic",
            1.2,
        ),
        (
            "mach_1",
            1.0,
        ),
        (
            "transonic_to_subsonic",
            0.8,
        ),
    ]:
        crossing = (
            descending_crossing(
                time_s,
                mach,
                threshold,
            )
        )

        if crossing is None:
            raise SystemExit(
                f"Missing descending "
                f"Mach {threshold} crossing."
            )

        final_transitions[
            name
        ] = crossing_state(
            start,
            crossing,
            time_s,
            altitude,
            speed,
            sound_speed,
            mach,
        )

    reference_events = {
        event[
            "event_id"
        ]: event
        for event
        in event_reference[
            "events"
        ]
    }

    recovery_states = {}

    for (
        event_id,
        label,
    ) in [
        (
            "drogue_deploy",
            "drogue_altitude_anchor",
        ),
        (
            "main_deploy",
            "main_altitude_anchor",
        ),
    ]:
        event = (
            reference_events[
                event_id
            ]
        )

        target_altitude = (
            float(
                event[
                    "reported_altitude_ft"
                ]
            )
            * FT_TO_KM
        )

        crossing = (
            descending_crossing(
                time_s,
                altitude,
                target_altitude,
            )
        )

        if crossing is None:
            raise SystemExit(
                f"Missing altitude crossing "
                f"for {event_id}."
            )

        recovery_states[
            label
        ] = crossing_state(
            start,
            crossing,
            time_s,
            altitude,
            speed,
            sound_speed,
            mach,
        )

    surface_crossing = (
        descending_crossing(
            time_s,
            altitude,
            0.0,
        )
    )

    if surface_crossing is None:
        raise SystemExit(
            "Missing WGS84 "
            "surface crossing."
        )

    recovery_states[
        "splashdown_correlated_surface_crossing"
    ] = crossing_state(
        start,
        surface_crossing,
        time_s,
        altitude,
        speed,
        sound_speed,
        mach,
    )

    appended_fields = [
        "thermal_particle_number_density_m3",
        "modeled_thermal_pressure_pa",
        "diatomic_particle_fraction",
        "monatomic_particle_fraction",
        "modeled_mixture_gamma",
        "modeled_mixture_molar_mass_kg_mol",
        "modeled_specific_gas_constant_j_kg_k",
        "modeled_sound_speed_m_s",
        "modeled_free_stream_mach",
        "dry_air_sound_speed_m_s",
        "dry_air_mach",
        "formal_flow_regime",
    ]

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=(
                atmosphere_fields
                + appended_fields
            ),
        )

        writer.writeheader()

        for i, row in enumerate(
            atmosphere
        ):
            output_row = dict(
                row
            )

            output_row.update(
                {
                    "thermal_particle_number_density_m3":
                        n_thermal[i],

                    "modeled_thermal_pressure_pa":
                        pressure[i],

                    "diatomic_particle_fraction":
                        x_diatomic[i],

                    "monatomic_particle_fraction":
                        x_monatomic[i],

                    "modeled_mixture_gamma":
                        gamma[i],

                    "modeled_mixture_molar_mass_kg_mol":
                        mixture_molar_mass[i],

                    "modeled_specific_gas_constant_j_kg_k":
                        r_mix[i],

                    "modeled_sound_speed_m_s":
                        sound_speed[i],

                    "modeled_free_stream_mach":
                        mach[i],

                    "dry_air_sound_speed_m_s":
                        dry_sound_speed[i],

                    "dry_air_mach":
                        dry_mach[i],

                    "formal_flow_regime":
                        classify_mach(
                            mach[i]
                        ),
                }
            )

            writer.writerow(
                output_row
            )

    max_mach_state = {
        "utc":
            geometry[
                max_mach_index
            ][
                "timestamp_utc"
            ],

        "ei_elapsed_seconds":
            float(
                time_s[
                    max_mach_index
                ]
            ),

        "altitude_km":
            float(
                altitude[
                    max_mach_index
                ]
            ),

        "earth_relative_speed_km_s":
            float(
                speed[
                    max_mach_index
                ]
                / 1000.0
            ),

        "neutral_temperature_k":
            float(
                temperature[
                    max_mach_index
                ]
            ),

        "gamma":
            float(
                gamma[
                    max_mach_index
                ]
            ),

        "mixture_molar_mass_g_mol":
            float(
                mixture_molar_mass[
                    max_mach_index
                ]
                * 1000.0
            ),

        "specific_gas_constant_j_kg_k":
            float(
                r_mix[
                    max_mach_index
                ]
            ),

        "sound_speed_m_s":
            float(
                sound_speed[
                    max_mach_index
                ]
            ),

        "mach":
            float(
                mach[
                    max_mach_index
                ]
            ),
    }

    summary = {
        "provenance": {
            "earth_relative_speed":
                "DERIVED_FROM_NASA_FLIGHT_DERIVED_EPHEMERIS",

            "composition":
                "MODEL",

            "neutral_temperature":
                "MODEL",

            "mixture_properties":
                "MODEL_DERIVED",

            "sound_speed":
                "MODEL_DERIVED",

            "mach":
                "MODEL_DERIVED",
        },

        "method": {
            "atmosphere_model":
                "NRLMSIS 2.0",

            "pymsis_version":
                pymsis.__version__,

            "velocity_assumption":
                (
                    "Earth-relative speed is "
                    "used as free-stream "
                    "air-relative speed. "
                    "Atmospheric winds are "
                    "neglected."
                ),

            "thermal_species": [
                "N2",
                "O2",
                "O",
                "He",
                "H",
                "Ar",
                "N",
            ],

            "excluded_from_acoustic_mixture": [
                "anomalous O",
            ],

            "diatomic_cv_over_r":
                2.5,

            "monatomic_cv_over_r":
                1.5,

            "vibrational_excitation":
                "neglected",

            "continuum_validity_check":
                "not yet applied",
        },

        "records":
            819,

        "entry_interface": {
            "utc":
                geometry[0][
                    "timestamp_utc"
                ],

            "altitude_km":
                float(
                    altitude[0]
                ),

            "earth_relative_speed_km_s":
                float(
                    speed[0]
                    / 1000.0
                ),

            "neutral_temperature_k":
                float(
                    temperature[0]
                ),

            "gamma":
                float(
                    gamma[0]
                ),

            "specific_gas_constant_j_kg_k":
                float(
                    r_mix[0]
                ),

            "sound_speed_m_s":
                float(
                    sound_speed[0]
                ),

            "mach":
                float(
                    mach[0]
                ),
        },

        "maximum_formal_free_stream_mach":
            max_mach_state,

        "early_modeled_dynamic_pressure_peak": {
            "utc":
                geometry[
                    early_q_index
                ][
                    "timestamp_utc"
                ],

            "ei_elapsed_seconds":
                float(
                    time_s[
                        early_q_index
                    ]
                ),

            "altitude_km":
                float(
                    altitude[
                        early_q_index
                    ]
                ),

            "mach":
                float(
                    mach[
                        early_q_index
                    ]
                ),
        },

        "global_modeled_dynamic_pressure_peak": {
            "utc":
                geometry[
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

            "mach":
                float(
                    mach[
                        peak_q_index
                    ]
                ),
        },

        "threshold_history":
            threshold_history,

        "final_flow_regime_transitions":
            final_transitions,

        "recovery_event_conditions":
            recovery_states,

        "sensitivity": {
            "maximum_anomalous_oxygen_particle_fraction_percent":
                float(
                    100.0
                    * np.max(
                        anomalous_fraction
                    )
                ),

            "maximum_absolute_thermal_mass_density_difference_percent":
                float(
                    np.max(
                        np.abs(
                            thermal_density_difference_percent
                        )
                    )
                ),

            "maximum_absolute_dry_air_mach_difference_below_80_km_percent":
                float(
                    np.max(
                        np.abs(
                            dry_mach_difference_percent[
                                altitude
                                <= 80.0
                            ]
                        )
                    )
                ),

            "maximum_absolute_dry_air_mach_difference_below_60_km_percent":
                float(
                    np.max(
                        np.abs(
                            dry_mach_difference_percent[
                                altitude
                                <= 60.0
                            ]
                        )
                    )
                ),
        },

        "mixture_property_range": {
            "gamma_min":
                float(
                    np.min(
                        gamma
                    )
                ),

            "gamma_max":
                float(
                    np.max(
                        gamma
                    )
                ),

            "specific_gas_constant_min_j_kg_k":
                float(
                    np.min(
                        r_mix
                    )
                ),

            "specific_gas_constant_max_j_kg_k":
                float(
                    np.max(
                        r_mix
                    )
                ),

            "sound_speed_min_m_s":
                float(
                    np.min(
                        sound_speed
                    )
                ),

            "sound_speed_max_m_s":
                float(
                    np.max(
                        sound_speed
                    )
                ),

            "mach_min":
                float(
                    np.min(
                        mach
                    )
                ),

            "mach_max":
                float(
                    np.max(
                        mach
                    )
                ),
        },

        "interpretation_limits": [
            (
                "Mach is a formal free-stream "
                "MODEL-DERIVED estimate."
            ),
            (
                "Earth-relative velocity is used "
                "as air-relative velocity, so "
                "atmospheric winds are neglected."
            ),
            (
                "Thermal species are treated as "
                "an ideal calorically perfect "
                "mixture with vibrational "
                "excitation neglected."
            ),
            (
                "The result does not represent "
                "post-shock temperature, "
                "dissociation, ionization, "
                "plasma chemistry, or TPS "
                "conditions."
            ),
            (
                "No Knudsen-number or continuum "
                "validity criterion has yet been "
                "applied, so the highest-altitude "
                "Mach values require caution."
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

    mach_figure = (
        ASSET_DIR
        / "phase2e_mach_history.svg"
    )

    fig, ax = plt.subplots()

    ax.plot(
        time_s,
        mach,
    )

    ax.scatter(
        [
            time_s[
                max_mach_index
            ]
        ],
        [
            mach[
                max_mach_index
            ]
        ],
    )

    ax.annotate(
        "formal max Mach",
        (
            time_s[
                max_mach_index
            ],
            mach[
                max_mach_index
            ],
        ),
    )

    for threshold in [
        5.0,
        1.2,
        1.0,
        0.8,
    ]:
        ax.axhline(
            threshold,
            linewidth=0.8,
        )

    ax.set_xlabel(
        "Seconds after Entry Interface"
    )

    ax.set_ylabel(
        "Modeled free-stream Mach"
    )

    ax.set_title(
        "Artemis II Modeled Free-Stream Mach"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        mach_figure,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(fig)

    normalize_svg(
        mach_figure
    )

    regime_figure = (
        ASSET_DIR
        / "phase2e_flow_regime_timeline.svg"
    )

    regime_code = np.array(
        [
            (
                3
                if value >= 5.0
                else 2
                if value >= 1.2
                else 1
                if value >= 0.8
                else 0
            )
            for value in mach
        ]
    )

    fig, ax = plt.subplots()

    ax.step(
        time_s,
        regime_code,
        where="post",
    )

    ax.set_yticks(
        [
            0,
            1,
            2,
            3,
        ]
    )

    ax.set_yticklabels(
        [
            "Subsonic",
            "Transonic",
            "Supersonic",
            "Hypersonic",
        ]
    )

    ax.set_xlabel(
        "Seconds after Entry Interface"
    )

    ax.set_title(
        "Artemis II Formal Flow-Regime Timeline"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        regime_figure,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(fig)

    normalize_svg(
        regime_figure
    )

    print()
    print(
        "Artemis II Free-Stream Mach"
    )

    print(
        "----------------------------"
    )

    print(
        f"Records: "
        f"{len(geometry)}"
    )

    print()
    print(
        "Entry Interface:"
    )

    print(
        f"  Mach: "
        f"{mach[0]:.6f}"
    )

    print(
        f"  sound speed: "
        f"{sound_speed[0]:.6f} m/s"
    )

    print(
        f"  gamma: "
        f"{gamma[0]:.9f}"
    )

    print()
    print(
        "Maximum formal free-stream Mach:"
    )

    print(
        f"  UTC: "
        f"{max_mach_state['utc']}"
    )

    print(
        f"  EI+: "
        f"{max_mach_state['ei_elapsed_seconds']:.3f} s"
    )

    print(
        f"  altitude: "
        f"{max_mach_state['altitude_km']:.6f} km"
    )

    print(
        f"  speed: "
        f"{max_mach_state['earth_relative_speed_km_s']:.6f} km/s"
    )

    print(
        f"  sound speed: "
        f"{max_mach_state['sound_speed_m_s']:.6f} m/s"
    )

    print(
        f"  Mach: "
        f"{max_mach_state['mach']:.6f}"
    )

    print()
    print(
        "Final flow-regime transitions:"
    )

    for name, state in (
        final_transitions.items()
    ):
        print(
            f"  {name}:"
        )

        print(
            f"    UTC: "
            f"{state['utc']}"
        )

        print(
            f"    EI+: "
            f"{state['ei_elapsed_seconds']:.6f} s"
        )

        print(
            f"    altitude: "
            f"{state['altitude_km']:.6f} km"
        )

        print(
            f"    Mach: "
            f"{state['modeled_free_stream_mach']:.6f}"
        )

    print()
    print(
        "Recovery conditions:"
    )

    for name, state in (
        recovery_states.items()
    ):
        print(
            f"  {name}: "
            f"M={state['modeled_free_stream_mach']:.6f}"
        )

    print()
    print(
        "Sensitivity:"
    )

    print(
        "  max anomalous-O fraction: "
        f"{summary['sensitivity']['maximum_anomalous_oxygen_particle_fraction_percent']:.12e}%"
    )

    print(
        "  max thermal-density difference: "
        f"{summary['sensitivity']['maximum_absolute_thermal_mass_density_difference_percent']:.12e}%"
    )

    print(
        "  max dry-air Mach difference "
        "below 80 km: "
        f"{summary['sensitivity']['maximum_absolute_dry_air_mach_difference_below_80_km_percent']:.9f}%"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Mach is MODEL-DERIVED."
    )

    print(
        "Highest-altitude values are "
        "formal estimates until continuum "
        "validity is evaluated."
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
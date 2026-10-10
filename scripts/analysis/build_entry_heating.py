from __future__ import annotations

import csv
import json
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
    / "entry_rarefaction.csv"
)

MODEL_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_convective_heating_model.json"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_heating.csv"
)

OUTPUT_SUMMARY = (
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


plt.rcParams["svg.hashsalt"] = (
    "a2-missionlab"
)

SVG_METADATA = {
    "Date": None,
}


def normalize_svg(path: Path):
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


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def format_utc(value: datetime) -> str:
    return (
        value.isoformat(
            timespec="microseconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def sutton_graves(
    density,
    velocity,
    radius,
    constant,
):
    return (
        constant
        * np.sqrt(
            density
            / radius
        )
        * velocity**3
    )


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


def descending_crossing(
    time_s,
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
                time_s[i - 1]
                + fraction
                * (
                    time_s[i]
                    - time_s[i - 1]
                )
            )
        )

    if not matches:
        raise RuntimeError(
            f"No descending crossing "
            f"for {target}."
        )

    return matches[-1]


def integrate_between(
    time_s,
    values,
    start,
    stop,
):
    if stop <= start:
        raise ValueError(
            "Integration stop must "
            "follow start."
        )

    mask = (
        (time_s > start)
        & (time_s < stop)
    )

    integration_time = np.concatenate(
        (
            [start],
            time_s[mask],
            [stop],
        )
    )

    integration_values = np.concatenate(
        (
            [
                interp(
                    time_s,
                    values,
                    start,
                )
            ],
            values[mask],
            [
                interp(
                    time_s,
                    values,
                    stop,
                )
            ],
        )
    )

    return float(
        np.trapezoid(
            integration_values,
            integration_time,
        )
    )


def cumulative_trapezoid(
    time_s,
    values,
):
    result = np.zeros(
        len(time_s),
        dtype=float,
    )

    result[1:] = np.cumsum(
        0.5
        * (
            values[1:]
            + values[:-1]
        )
        * np.diff(
            time_s
        )
    )

    return result


def state(
    rows,
    index,
    time_s,
    altitude,
    velocity,
    mach,
    kn,
    density,
    heat_flux,
):
    return {
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
                velocity[index]
                / 1000.0
            ),

        "mach":
            float(
                mach[index]
            ),

        "body_scale_knudsen":
            float(
                kn[index]
            ),

        "density_kg_m3":
            float(
                density[index]
            ),

        "heat_flux_w_m2":
            float(
                heat_flux[index]
            ),

        "heat_flux_w_cm2":
            float(
                heat_flux[index]
                / 10000.0
            ),
    }


def main():
    for path in [
        INPUT_CSV,
        MODEL_JSON,
    ]:
        if not path.exists():
            raise SystemExit(
                f"Missing required file:\n"
                f"{path}"
            )

    with INPUT_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(f)

        input_fields = (
            reader.fieldnames
            or []
        )

        rows = list(reader)

    with MODEL_JSON.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        model = json.load(f)

    if len(rows) != 819:
        raise SystemExit(
            f"Expected 819 states, "
            f"found {len(rows)}."
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

    low_radius = float(
        model[
            "nose_radius_sensitivity"
        ][
            "low_radius_m"
        ]
    )

    high_radius = float(
        model[
            "nose_radius_sensitivity"
        ][
            "high_radius_m"
        ]
    )

    primary_kn = float(
        model[
            "domain_definition"
        ][
            "primary"
        ][
            "maximum_body_scale_knudsen"
        ]
    )

    strong_kn = float(
        model[
            "domain_definition"
        ][
            "stronger_continuum_sensitivity"
        ][
            "maximum_body_scale_knudsen"
        ]
    )

    minimum_mach = float(
        model[
            "domain_definition"
        ][
            "primary"
        ][
            "minimum_mach"
        ]
    )

    timestamps = [
        parse_utc(
            row[
                "timestamp_utc"
            ]
        )
        for row in rows
    ]

    epoch = timestamps[0]

    time_s = np.array(
        [
            (
                timestamp
                - epoch
            ).total_seconds()
            for timestamp
            in timestamps
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
            for row in rows
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
            for row in rows
        ]
    )

    density = np.array(
        [
            float(
                row[
                    "msis_total_mass_density_kg_m3"
                ]
            )
            for row in rows
        ]
    )

    mach = np.array(
        [
            float(
                row[
                    "modeled_free_stream_mach"
                ]
            )
            for row in rows
        ]
    )

    kn = np.array(
        [
            float(
                row[
                    "body_scale_knudsen_number"
                ]
            )
            for row in rows
        ]
    )

    dynamic_pressure = np.array(
        [
            float(
                row[
                    "modeled_dynamic_pressure_pa"
                ]
            )
            for row in rows
        ]
    )

    heat_flux = sutton_graves(
        density,
        velocity,
        radius,
        k,
    )

    low_radius_flux = sutton_graves(
        density,
        velocity,
        low_radius,
        k,
    )

    high_radius_flux = sutton_graves(
        density,
        velocity,
        high_radius,
        k,
    )

    primary_start = (
        descending_crossing(
            time_s,
            kn,
            primary_kn,
        )
    )

    strong_start = (
        descending_crossing(
            time_s,
            kn,
            strong_kn,
        )
    )

    hypersonic_end = (
        descending_crossing(
            time_s,
            mach,
            minimum_mach,
        )
    )

    if not (
        primary_start
        < strong_start
        < hypersonic_end
    ):
        raise SystemExit(
            "Unexpected heating-domain "
            "boundary order."
        )

    full_load = float(
        np.trapezoid(
            heat_flux,
            time_s,
        )
    )

    pre_primary_load = (
        integrate_between(
            time_s,
            heat_flux,
            time_s[0],
            primary_start,
        )
    )

    primary_load = (
        integrate_between(
            time_s,
            heat_flux,
            primary_start,
            hypersonic_end,
        )
    )

    strong_load = (
        integrate_between(
            time_s,
            heat_flux,
            strong_start,
            hypersonic_end,
        )
    )

    post_hypersonic_load = (
        integrate_between(
            time_s,
            heat_flux,
            hypersonic_end,
            time_s[-1],
        )
    )

    global_peak_index = int(
        np.argmax(
            heat_flux
        )
    )

    primary_mask = (
        (time_s >= primary_start)
        & (
            time_s
            <= hypersonic_end
        )
    )

    strong_mask = (
        (time_s >= strong_start)
        & (
            time_s
            <= hypersonic_end
        )
    )

    primary_indices = np.where(
        primary_mask
    )[0]

    strong_indices = np.where(
        strong_mask
    )[0]

    primary_peak_index = (
        primary_indices[
            int(
                np.argmax(
                    heat_flux[
                        primary_mask
                    ]
                )
            )
        ]
    )

    strong_peak_index = (
        strong_indices[
            int(
                np.argmax(
                    heat_flux[
                        strong_mask
                    ]
                )
            )
        ]
    )

    if not (
        global_peak_index
        == primary_peak_index
        == strong_peak_index
    ):
        raise SystemExit(
            "Formal SG peak falls outside "
            "one of the permanent "
            "interpretation domains."
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

    q_local_maxima = sorted(
        q_local_maxima,
        key=lambda i:
            dynamic_pressure[i],
        reverse=True,
    )

    q_peak_context = []

    for index in (
        q_local_maxima[:2]
    ):
        q_peak_context.append(
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

                "mach":
                    float(
                        mach[index]
                    ),

                "body_scale_knudsen":
                    float(
                        kn[index]
                    ),

                "dynamic_pressure_kpa":
                    float(
                        dynamic_pressure[index]
                        / 1000.0
                    ),

                "sg_heat_flux_w_cm2":
                    float(
                        heat_flux[index]
                        / 10000.0
                    ),

                "time_offset_from_sg_peak_seconds":
                    float(
                        time_s[index]
                        - time_s[
                            global_peak_index
                        ]
                    ),
            }
        )

    radius_sensitivity = []

    for label, current_radius, values in [
        (
            "minus_10_percent",
            low_radius,
            low_radius_flux,
        ),
        (
            "reference",
            radius,
            heat_flux,
        ),
        (
            "plus_10_percent",
            high_radius,
            high_radius_flux,
        ),
    ]:
        peak = float(
            np.max(
                values[
                    strong_mask
                ]
            )
        )

        load = (
            integrate_between(
                time_s,
                values,
                strong_start,
                hypersonic_end,
            )
        )

        radius_sensitivity.append(
            {
                "case":
                    label,

                "nose_radius_m":
                    current_radius,

                "strong_domain_peak_w_cm2":
                    peak
                    / 10000.0,

                "strong_domain_heat_load_mj_m2":
                    load
                    / 1e6,
            }
        )

    cumulative = (
        cumulative_trapezoid(
            time_s,
            heat_flux,
        )
    )

    primary_domain = (
        (kn < primary_kn)
        & (mach >= minimum_mach)
    )

    strong_domain = (
        (kn < strong_kn)
        & (mach >= minimum_mach)
    )

    appended_fields = [
        "sg_convective_heat_flux_w_m2",
        "sg_convective_heat_flux_w_cm2",
        "sg_formal_cumulative_heat_load_j_m2",
        "sg_primary_domain",
        "sg_stronger_continuum_domain",
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
                input_fields
                + appended_fields
            ),
        )

        writer.writeheader()

        for i, row in enumerate(
            rows
        ):
            output = dict(row)

            output.update(
                {
                    "sg_convective_heat_flux_w_m2":
                        heat_flux[i],

                    "sg_convective_heat_flux_w_cm2":
                        heat_flux[i]
                        / 10000.0,

                    "sg_formal_cumulative_heat_load_j_m2":
                        cumulative[i],

                    "sg_primary_domain":
                        str(
                            bool(
                                primary_domain[i]
                            )
                        ).upper(),

                    "sg_stronger_continuum_domain":
                        str(
                            bool(
                                strong_domain[i]
                            )
                        ).upper(),
                }
            )

            writer.writerow(
                output
            )

    peak_state = state(
        rows,
        global_peak_index,
        time_s,
        altitude,
        velocity,
        mach,
        kn,
        density,
        heat_flux,
    )

    summary = {
        "provenance": {
            "density":
                "MODEL",

            "velocity":
                "DERIVED_FROM_NASA_FLIGHT_DERIVED_EPHEMERIS",

            "convective_heat_flux":
                "MODEL_DERIVED",

            "integrated_convective_heat_load":
                "MODEL_DERIVED",
        },

        "model":
            model,

        "records":
            len(rows),

        "entry_interface": {
            "utc":
                rows[0][
                    "timestamp_utc"
                ],

            "altitude_km":
                float(
                    altitude[0]
                ),

            "mach":
                float(
                    mach[0]
                ),

            "body_scale_knudsen":
                float(
                    kn[0]
                ),

            "formal_sg_heat_flux_w_cm2":
                float(
                    heat_flux[0]
                    / 10000.0
                ),

            "continuum_qualified":
                False,
        },

        "global_formal_sg_peak":
            peak_state,

        "primary_domain_peak":
            peak_state,

        "stronger_continuum_domain_peak":
            peak_state,

        "domain_boundaries": {
            "kn_0_01": {
                "utc":
                    format_utc(
                        epoch
                        + timedelta(
                            seconds=(
                                primary_start
                            )
                        )
                    ),

                "ei_elapsed_seconds":
                    primary_start,

                "altitude_km":
                    interp(
                        time_s,
                        altitude,
                        primary_start,
                    ),

                "mach":
                    interp(
                        time_s,
                        mach,
                        primary_start,
                    ),

                "sg_heat_flux_w_cm2":
                    interp(
                        time_s,
                        heat_flux,
                        primary_start,
                    )
                    / 10000.0,
            },

            "kn_0_001": {
                "utc":
                    format_utc(
                        epoch
                        + timedelta(
                            seconds=(
                                strong_start
                            )
                        )
                    ),

                "ei_elapsed_seconds":
                    strong_start,

                "altitude_km":
                    interp(
                        time_s,
                        altitude,
                        strong_start,
                    ),

                "mach":
                    interp(
                        time_s,
                        mach,
                        strong_start,
                    ),

                "sg_heat_flux_w_cm2":
                    interp(
                        time_s,
                        heat_flux,
                        strong_start,
                    )
                    / 10000.0,
            },

            "final_mach_5": {
                "utc":
                    format_utc(
                        epoch
                        + timedelta(
                            seconds=(
                                hypersonic_end
                            )
                        )
                    ),

                "ei_elapsed_seconds":
                    hypersonic_end,

                "altitude_km":
                    interp(
                        time_s,
                        altitude,
                        hypersonic_end,
                    ),

                "mach":
                    5.0,

                "sg_heat_flux_w_cm2":
                    interp(
                        time_s,
                        heat_flux,
                        hypersonic_end,
                    )
                    / 10000.0,
            },
        },

        "heat_load": {
            "formal_full_trajectory_mj_m2":
                full_load
                / 1e6,

            "before_kn_0_01_mj_m2":
                pre_primary_load
                / 1e6,

            "primary_kn_lt_0_01_mach_ge_5_mj_m2":
                primary_load
                / 1e6,

            "strong_kn_lt_0_001_mach_ge_5_mj_m2":
                strong_load
                / 1e6,

            "after_final_mach_5_mj_m2":
                post_hypersonic_load
                / 1e6,

            "primary_percent_of_formal_total":
                100.0
                * primary_load
                / full_load,

            "strong_percent_of_formal_total":
                100.0
                * strong_load
                / full_load,

            "before_primary_percent_of_formal_total":
                100.0
                * pre_primary_load
                / full_load,

            "after_mach_5_percent_of_formal_total":
                100.0
                * post_hypersonic_load
                / full_load,
        },

        "dynamic_pressure_peak_context":
            q_peak_context,

        "nose_radius_sensitivity":
            radius_sensitivity,

        "interpretation_limits":
            model[
                "interpretation_limits"
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

    flux_path = (
        ASSET_DIR
        / "phase2e_sutton_graves_heat_flux.svg"
    )

    fig, ax = plt.subplots()

    ax.plot(
        time_s,
        heat_flux
        / 10000.0,
    )

    ax.axvline(
        primary_start,
        linewidth=0.8,
    )

    ax.axvline(
        strong_start,
        linewidth=0.8,
    )

    ax.axvline(
        hypersonic_end,
        linewidth=0.8,
    )

    ax.scatter(
        [
            time_s[
                global_peak_index
            ]
        ],
        [
            heat_flux[
                global_peak_index
            ]
            / 10000.0
        ],
    )

    ax.annotate(
        "SG peak",
        (
            time_s[
                global_peak_index
            ],
            heat_flux[
                global_peak_index
            ]
            / 10000.0,
        ),
    )

    ax.set_xlabel(
        "Seconds after Entry Interface"
    )

    ax.set_ylabel(
        "Sutton-Graves heat flux (W/cm^2)"
    )

    ax.set_title(
        "Artemis II Modeled Stagnation-Point "
        "Convective Heating"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        flux_path,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(fig)

    normalize_svg(
        flux_path
    )

    load_path = (
        ASSET_DIR
        / "phase2e_sutton_graves_heat_load.svg"
    )

    fig, ax = plt.subplots()

    ax.plot(
        time_s,
        cumulative
        / 1e6,
    )

    ax.axvline(
        primary_start,
        linewidth=0.8,
    )

    ax.axvline(
        strong_start,
        linewidth=0.8,
    )

    ax.axvline(
        hypersonic_end,
        linewidth=0.8,
    )

    ax.set_xlabel(
        "Seconds after Entry Interface"
    )

    ax.set_ylabel(
        "Formal cumulative SG heat load (MJ/m^2)"
    )

    ax.set_title(
        "Artemis II Sutton-Graves "
        "Convective Heat-Load Integral"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        load_path,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(fig)

    normalize_svg(
        load_path
    )

    print()
    print(
        "Artemis II Sutton-Graves "
        "Convective Heating"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Records: "
        f"{len(rows)}"
    )

    print(
        f"Earth constant: "
        f"{k:.8e}"
    )

    print(
        f"Reference nose radius: "
        f"{radius:.6f} m"
    )

    print()
    print(
        "Global / qualified SG peak:"
    )

    print(
        f"  UTC: "
        f"{peak_state['utc']}"
    )

    print(
        f"  EI+: "
        f"{peak_state['ei_elapsed_seconds']:.3f} s"
    )

    print(
        f"  altitude: "
        f"{peak_state['altitude_km']:.6f} km"
    )

    print(
        f"  Mach: "
        f"{peak_state['mach']:.6f}"
    )

    print(
        f"  Kn: "
        f"{peak_state['body_scale_knudsen']:.12e}"
    )

    print(
        f"  heat flux: "
        f"{peak_state['heat_flux_w_cm2']:.6f} W/cm^2"
    )

    print()
    print(
        "Permanent interpretation domains:"
    )

    print(
        f"  Kn<0.01 and Mach>=5:"
    )

    print(
        f"    "
        f"{primary_load / 1e6:.9f} MJ/m^2"
    )

    print(
        f"    "
        f"{100.0 * primary_load / full_load:.9f}% "
        f"of formal total"
    )

    print(
        f"  Kn<0.001 and Mach>=5:"
    )

    print(
        f"    "
        f"{strong_load / 1e6:.9f} MJ/m^2"
    )

    print(
        f"    "
        f"{100.0 * strong_load / full_load:.9f}% "
        f"of formal total"
    )

    print()
    print(
        "Diagnostic exclusions:"
    )

    print(
        f"  before Kn=0.01: "
        f"{pre_primary_load / 1e6:.9f} MJ/m^2"
    )

    print(
        f"  after final Mach 5: "
        f"{post_hypersonic_load / 1e6:.9f} MJ/m^2"
    )

    print(
        f"  full formal integral: "
        f"{full_load / 1e6:.9f} MJ/m^2"
    )

    print()
    print(
        "Dynamic-pressure peak timing:"
    )

    for item in (
        q_peak_context
    ):
        print(
            f"  {item['utc']}  "
            f"offset="
            f"{item['time_offset_from_sg_peak_seconds']:+.3f}s  "
            f"q="
            f"{item['dynamic_pressure_kpa']:.6f} kPa  "
            f"SG="
            f"{item['sg_heat_flux_w_cm2']:.6f} W/cm^2"
        )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "This is a MODEL-DERIVED cold-wall "
        "engineering stagnation-point "
        "convective-heating reconstruction."
    )

    print(
        "Primary reporting is limited to "
        "Kn<0.01 and Mach>=5."
    )

    print(
        "No Artemis II-specific calibration "
        "factor is applied."
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
        "Wrote documentation SVGs under "
        f"{ASSET_DIR.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
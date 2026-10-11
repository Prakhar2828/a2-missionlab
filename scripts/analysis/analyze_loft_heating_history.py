from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]

HEATING_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_heating.csv"
)

HEATING_SUMMARY_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_heating_summary.json"
)

DYNAMICS_SUMMARY_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_dynamics_summary.json"
)

OUTPUT_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "loft_heating_history.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
)

FLUX_FIGURE = (
    ASSET_DIR
    / "phase2f_loft_heating_flux.svg"
)

PARTITION_FIGURE = (
    ASSET_DIR
    / "phase2f_loft_heat_load_partition.svg"
)

CUMULATIVE_FIGURE = (
    ASSET_DIR
    / "phase2f_loft_cumulative_heat_load.svg"
)

EXPECTED_RECORDS = 819


plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def normalize_svg(
    path: Path,
) -> None:
    text = path.read_text(
        encoding="utf-8",
    )

    cleaned = "\n".join(
        line.rstrip(" \t")
        for line in text.splitlines()
    ) + "\n"

    path.write_text(
        cleaned,
        encoding="utf-8",
    )


def load_json(
    path: Path,
):
    if not path.exists():
        raise SystemExit(
            "Missing required file:\n"
            f"{path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def load_csv(
    path: Path,
):
    if not path.exists():
        raise SystemExit(
            "Missing required file:\n"
            f"{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return list(
            csv.DictReader(f)
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


def interp(
    time_s: np.ndarray,
    values: np.ndarray,
    target: float,
) -> float:
    return float(
        np.interp(
            target,
            time_s,
            values,
        )
    )


def interval_arrays(
    time_s: np.ndarray,
    values: np.ndarray,
    start: float,
    stop: float,
):
    if stop <= start:
        raise ValueError(
            "Interval stop must follow start."
        )

    mask = (
        (time_s > start)
        & (time_s < stop)
    )

    local_time = np.concatenate(
        (
            [start],
            time_s[mask],
            [stop],
        )
    )

    local_values = np.concatenate(
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

    return (
        local_time,
        local_values,
    )


def integrate_between(
    time_s: np.ndarray,
    values: np.ndarray,
    start: float,
    stop: float,
) -> float:
    local_time, local_values = (
        interval_arrays(
            time_s,
            values,
            start,
            stop,
        )
    )

    return float(
        np.trapezoid(
            local_values,
            local_time,
        )
    )


def state_at(
    target: float,
    time_s: np.ndarray,
    altitude_km: np.ndarray,
    speed_km_s: np.ndarray,
    mach: np.ndarray,
    kn: np.ndarray,
    heat_flux_w_m2: np.ndarray,
):
    return {
        "ei_elapsed_seconds":
            float(target),

        "altitude_km":
            interp(
                time_s,
                altitude_km,
                target,
            ),

        "earth_relative_speed_km_s":
            interp(
                time_s,
                speed_km_s,
                target,
            ),

        "mach":
            interp(
                time_s,
                mach,
                target,
            ),

        "body_scale_knudsen":
            interp(
                time_s,
                kn,
                target,
            ),

        "sg_heat_flux_w_m2":
            interp(
                time_s,
                heat_flux_w_m2,
                target,
            ),

        "sg_heat_flux_w_cm2":
            (
                interp(
                    time_s,
                    heat_flux_w_m2,
                    target,
                )
                / 10000.0
            ),
    }


def interval_stats(
    name: str,
    start: float,
    stop: float,
    time_s: np.ndarray,
    altitude_km: np.ndarray,
    speed_km_s: np.ndarray,
    mach: np.ndarray,
    kn: np.ndarray,
    heat_flux_w_m2: np.ndarray,
    strong_total_j_m2: float,
):
    local_time, local_flux = (
        interval_arrays(
            time_s,
            heat_flux_w_m2,
            start,
            stop,
        )
    )

    heat_load = float(
        np.trapezoid(
            local_flux,
            local_time,
        )
    )

    maximum_index = int(
        np.argmax(
            local_flux
        )
    )

    minimum_index = int(
        np.argmin(
            local_flux
        )
    )

    average_flux = (
        heat_load
        / (
            stop
            - start
        )
    )

    return {
        "segment":
            name,

        "start":
            state_at(
                start,
                time_s,
                altitude_km,
                speed_km_s,
                mach,
                kn,
                heat_flux_w_m2,
            ),

        "end":
            state_at(
                stop,
                time_s,
                altitude_km,
                speed_km_s,
                mach,
                kn,
                heat_flux_w_m2,
            ),

        "duration_seconds":
            float(
                stop
                - start
            ),

        "integrated_heat_load_j_m2":
            heat_load,

        "integrated_heat_load_mj_m2":
            heat_load
            / 1e6,

        "percent_of_strong_domain_heat_load":
            (
                100.0
                * heat_load
                / strong_total_j_m2
            ),

        "average_sg_heat_flux_w_cm2":
            average_flux
            / 10000.0,

        "maximum_sg_heat_flux": {
            "ei_elapsed_seconds":
                float(
                    local_time[
                        maximum_index
                    ]
                ),

            "w_cm2":
                float(
                    local_flux[
                        maximum_index
                    ]
                    / 10000.0
                ),

            "location":
                (
                    "START_BOUNDARY"
                    if maximum_index == 0
                    else (
                        "END_BOUNDARY"
                        if maximum_index
                        == len(local_time) - 1
                        else "INTERIOR_SAMPLE"
                    )
                ),
        },

        "minimum_sg_heat_flux": {
            "ei_elapsed_seconds":
                float(
                    local_time[
                        minimum_index
                    ]
                ),

            "w_cm2":
                float(
                    local_flux[
                        minimum_index
                    ]
                    / 10000.0
                ),

            "location":
                (
                    "START_BOUNDARY"
                    if minimum_index == 0
                    else (
                        "END_BOUNDARY"
                        if minimum_index
                        == len(local_time) - 1
                        else "INTERIOR_SAMPLE"
                    )
                ),
        },
    }


def cumulative_from_boundary(
    time_s: np.ndarray,
    heat_flux_w_m2: np.ndarray,
    start: float,
    stop: float,
):
    mask = (
        (time_s > start)
        & (time_s < stop)
    )

    local_time = np.concatenate(
        (
            [start],
            time_s[mask],
            [stop],
        )
    )

    local_flux = np.concatenate(
        (
            [
                interp(
                    time_s,
                    heat_flux_w_m2,
                    start,
                )
            ],
            heat_flux_w_m2[
                mask
            ],
            [
                interp(
                    time_s,
                    heat_flux_w_m2,
                    stop,
                )
            ],
        )
    )

    cumulative = np.zeros(
        len(local_time),
        dtype=float,
    )

    cumulative[1:] = np.cumsum(
        0.5
        * (
            local_flux[1:]
            + local_flux[:-1]
        )
        * np.diff(
            local_time
        )
    )

    return (
        local_time,
        cumulative,
    )


def make_flux_figure(
    time_s,
    heat_flux_w_m2,
    strong_start,
    sg_peak_time,
    rebound_start,
    rebound_end,
    mach5_end,
):
    mask = (
        (time_s >= strong_start)
        & (time_s <= mach5_end)
    )

    fig, ax = plt.subplots(
        figsize=(
            9.0,
            5.5,
        )
    )

    ax.plot(
        time_s[mask],
        heat_flux_w_m2[mask]
        / 10000.0,
    )

    ax.axvline(
        sg_peak_time,
        linewidth=0.8,
    )

    ax.axvline(
        rebound_start,
        linewidth=0.8,
    )

    ax.axvline(
        rebound_end,
        linewidth=0.8,
    )

    ax.annotate(
        "SG peak",
        (
            sg_peak_time,
            interp(
                time_s,
                heat_flux_w_m2,
                sg_peak_time,
            )
            / 10000.0,
        ),
    )

    ax.annotate(
        "Loft start",
        (
            rebound_start,
            interp(
                time_s,
                heat_flux_w_m2,
                rebound_start,
            )
            / 10000.0,
        ),
    )

    ax.annotate(
        "Loft end",
        (
            rebound_end,
            interp(
                time_s,
                heat_flux_w_m2,
                rebound_end,
            )
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
        "Artemis II External Heating Through "
        "the Derived Loft / Rebound"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        FLUX_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(
        fig
    )

    normalize_svg(
        FLUX_FIGURE
    )


def make_partition_figure(
    segments,
):
    labels = [
        "Pre-loft",
        "Loft / rebound",
        "Post-loft",
    ]

    values = [
        segment[
            "integrated_heat_load_mj_m2"
        ]
        for segment in segments
    ]

    fig, ax = plt.subplots(
        figsize=(
            8.0,
            5.0,
        )
    )

    bars = ax.bar(
        labels,
        values,
    )

    for bar, segment in zip(
        bars,
        segments,
    ):
        height = float(
            bar.get_height()
        )

        percent = float(
            segment[
                "percent_of_strong_domain_heat_load"
            ]
        )

        ax.annotate(
            (
                f"{height:.3f} MJ/m^2\n"
                f"{percent:.2f}%"
            ),
            (
                bar.get_x()
                + bar.get_width()
                / 2.0,
                height,
            ),
            xytext=(
                0,
                4,
            ),
            textcoords=(
                "offset points"
            ),
            ha="center",
            va="bottom",
        )

    ax.set_ylabel(
        "Modeled convective heat load (MJ/m^2)"
    )

    ax.set_title(
        "Artemis II Strong-Domain Heat-Load Partition"
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        PARTITION_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(
        fig
    )

    normalize_svg(
        PARTITION_FIGURE
    )


def make_cumulative_figure(
    time_s,
    heat_flux_w_m2,
    strong_start,
    rebound_start,
    rebound_end,
    mach5_end,
):
    (
        local_time,
        cumulative,
    ) = cumulative_from_boundary(
        time_s,
        heat_flux_w_m2,
        strong_start,
        mach5_end,
    )

    fig, ax = plt.subplots(
        figsize=(
            9.0,
            5.5,
        )
    )

    ax.plot(
        local_time,
        cumulative
        / 1e6,
    )

    ax.axvline(
        rebound_start,
        linewidth=0.8,
    )

    ax.axvline(
        rebound_end,
        linewidth=0.8,
    )

    ax.annotate(
        "Loft start",
        (
            rebound_start,
            interp(
                local_time,
                cumulative,
                rebound_start,
            )
            / 1e6,
        ),
    )

    ax.annotate(
        "Loft end",
        (
            rebound_end,
            interp(
                local_time,
                cumulative,
                rebound_end,
            )
            / 1e6,
        ),
    )

    ax.set_xlabel(
        "Seconds after Entry Interface"
    )

    ax.set_ylabel(
        "Strong-domain cumulative SG heat load (MJ/m^2)"
    )

    ax.set_title(
        "Artemis II Heat-Load Accumulation Through "
        "the Derived Loft / Rebound"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        CUMULATIVE_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(
        fig
    )

    normalize_svg(
        CUMULATIVE_FIGURE
    )


def main() -> None:
    rows = load_csv(
        HEATING_CSV
    )

    heating_summary = load_json(
        HEATING_SUMMARY_JSON
    )

    dynamics_summary = load_json(
        DYNAMICS_SUMMARY_JSON
    )

    if len(
        rows
    ) != EXPECTED_RECORDS:
        raise SystemExit(
            f"Expected {EXPECTED_RECORDS} "
            f"heating states, found "
            f"{len(rows)}."
        )

    if (
        "ei_elapsed_seconds"
        in rows[0]
        and rows[0][
            "ei_elapsed_seconds"
        ] != ""
    ):
        time_s = np.array(
            [
                float(
                    row[
                        "ei_elapsed_seconds"
                    ]
                )
                for row in rows
            ],
            dtype=float,
        )

    else:
        timestamps = [
            parse_utc(
                row[
                    "timestamp_utc"
                ]
            )
            for row in rows
        ]

        epoch = (
            timestamps[0]
        )

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

    mach = np.array(
        [
            float(
                row[
                    "modeled_free_stream_mach"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    kn = np.array(
        [
            float(
                row[
                    "body_scale_knudsen_number"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    heat_flux_w_m2 = np.array(
        [
            float(
                row[
                    "sg_convective_heat_flux_w_m2"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    rebound = dynamics_summary.get(
        "skip_rebound"
    )

    if rebound is None:
        raise SystemExit(
            "Missing Artemis II "
            "derived rebound."
        )

    strong_start = float(
        heating_summary[
            "domain_boundaries"
        ][
            "kn_0_001"
        ][
            "ei_elapsed_seconds"
        ]
    )

    sg_peak_time = float(
        heating_summary[
            "global_formal_sg_peak"
        ][
            "ei_elapsed_seconds"
        ]
    )

    sg_peak_flux_w_cm2 = float(
        heating_summary[
            "global_formal_sg_peak"
        ][
            "heat_flux_w_cm2"
        ]
    )

    rebound_start = float(
        rebound[
            "start"
        ][
            "elapsed_seconds"
        ]
    )

    rebound_end = float(
        rebound[
            "end"
        ][
            "elapsed_seconds"
        ]
    )

    mach5_end = float(
        heating_summary[
            "domain_boundaries"
        ][
            "final_mach_5"
        ][
            "ei_elapsed_seconds"
        ]
    )

    if not (
        strong_start
        < sg_peak_time
        < rebound_start
        < rebound_end
        < mach5_end
    ):
        raise SystemExit(
            "Unexpected thermal-history "
            "boundary order."
        )

    strong_total_j_m2 = (
        float(
            heating_summary[
                "heat_load"
            ][
                "strong_kn_lt_0_001_mach_ge_5_mj_m2"
            ]
        )
        * 1e6
    )

    pre_segment = interval_stats(
        "PRE_REBOUND_STRONG_DOMAIN",
        strong_start,
        rebound_start,
        time_s,
        altitude_km,
        speed_km_s,
        mach,
        kn,
        heat_flux_w_m2,
        strong_total_j_m2,
    )

    rebound_segment = interval_stats(
        "REBOUND_LOFT",
        rebound_start,
        rebound_end,
        time_s,
        altitude_km,
        speed_km_s,
        mach,
        kn,
        heat_flux_w_m2,
        strong_total_j_m2,
    )

    post_segment = interval_stats(
        "POST_REBOUND_TO_MACH5",
        rebound_end,
        mach5_end,
        time_s,
        altitude_km,
        speed_km_s,
        mach,
        kn,
        heat_flux_w_m2,
        strong_total_j_m2,
    )

    segments = [
        pre_segment,
        rebound_segment,
        post_segment,
    ]

    partition_total_j_m2 = sum(
        segment[
            "integrated_heat_load_j_m2"
        ]
        for segment in segments
    )

    partition_closure_error_j_m2 = (
        partition_total_j_m2
        - strong_total_j_m2
    )

    partition_percent_total = sum(
        segment[
            "percent_of_strong_domain_heat_load"
        ]
        for segment in segments
    )

    rebound_start_flux = float(
        rebound_segment[
            "start"
        ][
            "sg_heat_flux_w_cm2"
        ]
    )

    rebound_end_flux = float(
        rebound_segment[
            "end"
        ][
            "sg_heat_flux_w_cm2"
        ]
    )

    rebound_flux_change_percent = (
        100.0
        * (
            rebound_end_flux
            - rebound_start_flux
        )
        / rebound_start_flux
    )

    peak_to_rebound_start_j_m2 = (
        integrate_between(
            time_s,
            heat_flux_w_m2,
            sg_peak_time,
            rebound_start,
        )
    )

    peak_to_rebound_end_j_m2 = (
        integrate_between(
            time_s,
            heat_flux_w_m2,
            sg_peak_time,
            rebound_end,
        )
    )

    peak_to_mach5_j_m2 = (
        integrate_between(
            time_s,
            heat_flux_w_m2,
            sg_peak_time,
            mach5_end,
        )
    )

    result = {
        "product_id":
            "phase2f3_loft_heating_history",

        "provenance":
            "MISSIONLAB_DERIVED_FROM_PHASE2E4_MODEL_OUTPUT",

        "scope":
            (
                "Time-resolved segmentation of "
                "the modeled Artemis II external "
                "Sutton-Graves convective heating "
                "history relative to the derived "
                "vertical rebound / loft."
            ),

        "thermal_history_order": {
            "strong_continuum_start_ei_seconds":
                strong_start,

            "sg_peak_ei_seconds":
                sg_peak_time,

            "rebound_start_ei_seconds":
                rebound_start,

            "rebound_end_ei_seconds":
                rebound_end,

            "final_mach5_ei_seconds":
                mach5_end,
        },

        "sg_peak": {
            "ei_elapsed_seconds":
                sg_peak_time,

            "heat_flux_w_cm2":
                sg_peak_flux_w_cm2,

            "seconds_before_rebound_start":
                (
                    rebound_start
                    - sg_peak_time
                ),
        },

        "segments":
            segments,

        "rebound_external_flux_change": {
            "start_w_cm2":
                rebound_start_flux,

            "end_w_cm2":
                rebound_end_flux,

            "signed_percent_change":
                rebound_flux_change_percent,

            "relationship":
                (
                    "DECREASED"
                    if rebound_flux_change_percent
                    < 0.0
                    else (
                        "INCREASED"
                        if rebound_flux_change_percent
                        > 0.0
                        else "UNCHANGED"
                    )
                ),
        },

        "strong_domain_partition": {
            "existing_phase2e4_heat_load_mj_m2":
                strong_total_j_m2
                / 1e6,

            "partition_total_mj_m2":
                partition_total_j_m2
                / 1e6,

            "closure_error_j_m2":
                partition_closure_error_j_m2,

            "partition_percent_total":
                partition_percent_total,
        },

        "post_peak_heat_load_context": {
            "sg_peak_to_rebound_start_mj_m2":
                peak_to_rebound_start_j_m2
                / 1e6,

            "sg_peak_to_rebound_end_mj_m2":
                peak_to_rebound_end_j_m2
                / 1e6,

            "sg_peak_to_final_mach5_mj_m2":
                peak_to_mach5_j_m2
                / 1e6,

            "sg_peak_to_rebound_end_percent_of_strong_domain":
                (
                    100.0
                    * peak_to_rebound_end_j_m2
                    / strong_total_j_m2
                ),

            "sg_peak_to_final_mach5_percent_of_strong_domain":
                (
                    100.0
                    * peak_to_mach5_j_m2
                    / strong_total_j_m2
                ),
        },

        "interpretation_guardrails": [
            (
                "A decrease in modeled external "
                "Sutton-Graves heat flux does not "
                "demonstrate decreasing internal "
                "TPS temperature."
            ),
            (
                "Modeled external convective heat "
                "load is not converted into Avcoat "
                "char loss, recession depth, "
                "cracking, permeability, or "
                "damage probability."
            ),
            (
                "The derived Artemis II vertical "
                "rebound is described as a loft "
                "or rebound, not a skip entry."
            ),
            (
                "The segmentation reuses the "
                "existing Phase 2E.4 external "
                "heating model and introduces no "
                "new TPS material-response model."
            ),
            (
                "No internal Avcoat temperature, "
                "pyrolysis-gas generation, gas "
                "pressure, or permeability history "
                "is inferred."
            ),
        ],

        "figures": [
            str(
                FLUX_FIGURE.relative_to(
                    ROOT
                )
            ),
            str(
                PARTITION_FIGURE.relative_to(
                    ROOT
                )
            ),
            str(
                CUMULATIVE_FIGURE.relative_to(
                    ROOT
                )
            ),
        ],
    }

    OUTPUT_JSON.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
        )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    make_flux_figure(
        time_s,
        heat_flux_w_m2,
        strong_start,
        sg_peak_time,
        rebound_start,
        rebound_end,
        mach5_end,
    )

    make_partition_figure(
        segments
    )

    make_cumulative_figure(
        time_s,
        heat_flux_w_m2,
        strong_start,
        rebound_start,
        rebound_end,
        mach5_end,
    )

    print()
    print(
        "Phase 2F.3 Artemis II Loft "
        "Heating-History Segmentation"
    )

    print(
        "========================================"
    )

    print()
    print(
        "Thermal-history order:"
    )

    print(
        f"  strong-domain start: "
        f"EI+{strong_start:.6f} s"
    )

    print(
        f"  SG peak:             "
        f"EI+{sg_peak_time:.6f} s"
    )

    print(
        f"  loft start:          "
        f"EI+{rebound_start:.6f} s"
    )

    print(
        f"  loft end:            "
        f"EI+{rebound_end:.6f} s"
    )

    print(
        f"  final Mach 5:        "
        f"EI+{mach5_end:.6f} s"
    )

    print()
    print(
        "SG peak relationship:"
    )

    print(
        f"  peak heat flux: "
        f"{sg_peak_flux_w_cm2:.6f} W/cm^2"
    )

    print(
        f"  peak before loft start: "
        f"{rebound_start - sg_peak_time:.6f} s"
    )

    print()
    print(
        "Strong-domain heat-load partition:"
    )

    for segment in segments:
        print(
            f"  {segment['segment']}:"
        )

        print(
            f"    "
            f"{segment['integrated_heat_load_mj_m2']:.9f} "
            "MJ/m^2"
        )

        print(
            f"    "
            f"{segment['percent_of_strong_domain_heat_load']:.6f}%"
        )

    print()
    print(
        "Rebound interval:"
    )

    print(
        f"  duration: "
        f"{rebound_segment['duration_seconds']:.6f} s"
    )

    print(
        "  start external SG flux:"
    )

    print(
        f"    "
        f"{rebound_start_flux:.6f} W/cm^2"
    )

    print(
        "  end external SG flux:"
    )

    print(
        f"    "
        f"{rebound_end_flux:.6f} W/cm^2"
    )

    print(
        "  signed change:"
    )

    print(
        f"    "
        f"{rebound_flux_change_percent:+.6f}%"
    )

    print(
        "  average external SG flux:"
    )

    print(
        f"    "
        f"{rebound_segment['average_sg_heat_flux_w_cm2']:.6f} "
        "W/cm^2"
    )

    print(
        "  interval maximum:"
    )

    print(
        f"    "
        f"{rebound_segment['maximum_sg_heat_flux']['w_cm2']:.6f} "
        "W/cm^2"
    )

    print(
        f"    at EI+"
        f"{rebound_segment['maximum_sg_heat_flux']['ei_elapsed_seconds']:.6f} s"
    )

    print(
        f"    "
        f"{rebound_segment['maximum_sg_heat_flux']['location']}"
    )

    print(
        "  interval minimum:"
    )

    print(
        f"    "
        f"{rebound_segment['minimum_sg_heat_flux']['w_cm2']:.6f} "
        "W/cm^2"
    )

    print(
        f"    at EI+"
        f"{rebound_segment['minimum_sg_heat_flux']['ei_elapsed_seconds']:.6f} s"
    )

    print(
        f"    "
        f"{rebound_segment['minimum_sg_heat_flux']['location']}"
    )

    print()
    print(
        "Partition closure:"
    )

    print(
        f"  partition total: "
        f"{partition_total_j_m2 / 1e6:.9f} MJ/m^2"
    )

    print(
        f"  Phase 2E.4 strong load: "
        f"{strong_total_j_m2 / 1e6:.9f} MJ/m^2"
    )

    print(
        f"  closure error: "
        f"{partition_closure_error_j_m2:.9f} J/m^2"
    )

    print(
        f"  percent sum: "
        f"{partition_percent_total:.9f}%"
    )

    print()
    print(
        "Post-peak context:"
    )

    print(
        "  SG peak to loft start:"
    )

    print(
        f"    "
        f"{peak_to_rebound_start_j_m2 / 1e6:.9f} MJ/m^2"
    )

    print(
        "  SG peak through loft end:"
    )

    print(
        f"    "
        f"{peak_to_rebound_end_j_m2 / 1e6:.9f} MJ/m^2"
    )

    print(
        f"    "
        f"{100.0 * peak_to_rebound_end_j_m2 / strong_total_j_m2:.6f}% "
        "of strong-domain load"
    )

    print(
        "  SG peak through final Mach 5:"
    )

    print(
        f"    "
        f"{peak_to_mach5_j_m2 / 1e6:.9f} MJ/m^2"
    )

    print(
        f"    "
        f"{100.0 * peak_to_mach5_j_m2 / strong_total_j_m2:.6f}% "
        "of strong-domain load"
    )

    print()
    print(
        "Guardrails:"
    )

    print(
        "  external heat-flux decline -> "
        "internal TPS cooling: NOT INFERRED"
    )

    print(
        "  external heat load -> "
        "Avcoat damage: NOT INFERRED"
    )

    print(
        "  loft geometry -> "
        "TPS damage: NOT INFERRED"
    )

    print()
    print(
        "Wrote:"
    )

    print(
        f"  {OUTPUT_JSON.relative_to(ROOT)}"
    )

    print(
        f"  {FLUX_FIGURE.relative_to(ROOT)}"
    )

    print(
        f"  {PARTITION_FIGURE.relative_to(ROOT)}"
    )

    print(
        f"  {CUMULATIVE_FIGURE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
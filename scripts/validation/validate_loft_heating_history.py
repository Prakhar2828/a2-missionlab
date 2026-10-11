from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path

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

PRODUCT_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "loft_heating_history.json"
)

FIGURES = [
    (
        ROOT
        / "docs"
        / "assets"
        / "entry"
        / "phase2f_loft_heating_flux.svg"
    ),
    (
        ROOT
        / "docs"
        / "assets"
        / "entry"
        / "phase2f_loft_heat_load_partition.svg"
    ),
    (
        ROOT
        / "docs"
        / "assets"
        / "entry"
        / "phase2f_loft_cumulative_heat_load.svg"
    ),
]

EXPECTED_RECORDS = 819

EXPECTED_SEGMENTS = [
    "PRE_REBOUND_STRONG_DOMAIN",
    "REBOUND_LOFT",
    "POST_REBOUND_TO_MACH5",
]

EXPECTED_GUARDRAILS = [
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
]


def fail(
    message: str,
) -> None:
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def load_json(
    path: Path,
):
    if not path.exists():
        fail(
            f"missing required file: {path}"
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
        fail(
            f"missing required file: {path}"
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


def close(
    actual: float,
    expected: float,
    tolerance: float,
    label: str,
) -> None:
    if not math.isclose(
        actual,
        expected,
        rel_tol=0.0,
        abs_tol=tolerance,
    ):
        fail(
            f"{label}: expected "
            f"{expected!r}, found "
            f"{actual!r}"
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


def interval_arrays(
    time_s,
    values,
    start,
    stop,
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
    time_s,
    values,
    start,
    stop,
):
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

    product = load_json(
        PRODUCT_JSON
    )

    if len(
        rows
    ) != EXPECTED_RECORDS:
        fail(
            f"expected {EXPECTED_RECORDS} "
            "heating states"
        )

    if (
        product.get(
            "product_id"
        )
        != "phase2f3_loft_heating_history"
    ):
        fail(
            "unexpected product_id"
        )

    if (
        product.get(
            "provenance"
        )
        != "MISSIONLAB_DERIVED_FROM_PHASE2E4_MODEL_OUTPUT"
    ):
        fail(
            "unexpected provenance"
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
        fail(
            "missing derived rebound"
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
        fail(
            "thermal-history boundary "
            "order changed"
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

    boundaries = [
        (
            strong_start,
            rebound_start,
        ),
        (
            rebound_start,
            rebound_end,
        ),
        (
            rebound_end,
            mach5_end,
        ),
    ]

    expected_loads = [
        integrate_between(
            time_s,
            heat_flux_w_m2,
            start,
            stop,
        )
        for start, stop in boundaries
    ]

    expected_total = sum(
        expected_loads
    )

    expected_percents = [
        100.0
        * value
        / strong_total_j_m2
        for value in expected_loads
    ]

    thermal_order = product.get(
        "thermal_history_order"
    )

    if not isinstance(
        thermal_order,
        dict,
    ):
        fail(
            "missing thermal-history order"
        )

    close(
        float(
            thermal_order[
                "strong_continuum_start_ei_seconds"
            ]
        ),
        strong_start,
        1e-9,
        "strong-domain start",
    )

    close(
        float(
            thermal_order[
                "sg_peak_ei_seconds"
            ]
        ),
        sg_peak_time,
        1e-9,
        "SG peak time",
    )

    close(
        float(
            thermal_order[
                "rebound_start_ei_seconds"
            ]
        ),
        rebound_start,
        1e-9,
        "rebound start",
    )

    close(
        float(
            thermal_order[
                "rebound_end_ei_seconds"
            ]
        ),
        rebound_end,
        1e-9,
        "rebound end",
    )

    close(
        float(
            thermal_order[
                "final_mach5_ei_seconds"
            ]
        ),
        mach5_end,
        1e-9,
        "Mach 5 boundary",
    )

    segments = product.get(
        "segments"
    )

    if not isinstance(
        segments,
        list,
    ):
        fail(
            "segments must be a list"
        )

    if len(
        segments
    ) != 3:
        fail(
            "expected three segments"
        )

    observed_names = [
        segment.get(
            "segment"
        )
        for segment in segments
    ]

    if (
        observed_names
        != EXPECTED_SEGMENTS
    ):
        fail(
            "segment order or names changed"
        )

    for index, segment in enumerate(
        segments
    ):
        start, stop = (
            boundaries[
                index
            ]
        )

        local_time, local_flux = (
            interval_arrays(
                time_s,
                heat_flux_w_m2,
                start,
                stop,
            )
        )

        expected_max_index = int(
            np.argmax(
                local_flux
            )
        )

        expected_min_index = int(
            np.argmin(
                local_flux
            )
        )

        expected_average = (
            expected_loads[
                index
            ]
            / (
                stop
                - start
            )
        )

        close(
            float(
                segment[
                    "duration_seconds"
                ]
            ),
            stop - start,
            1e-9,
            f"{observed_names[index]} duration",
        )

        close(
            float(
                segment[
                    "integrated_heat_load_j_m2"
                ]
            ),
            expected_loads[
                index
            ],
            1e-5,
            f"{observed_names[index]} load",
        )

        close(
            float(
                segment[
                    "percent_of_strong_domain_heat_load"
                ]
            ),
            expected_percents[
                index
            ],
            1e-9,
            f"{observed_names[index]} percent",
        )

        close(
            float(
                segment[
                    "average_sg_heat_flux_w_cm2"
                ]
            ),
            expected_average
            / 10000.0,
            1e-9,
            f"{observed_names[index]} average flux",
        )

        maximum = segment[
            "maximum_sg_heat_flux"
        ]

        minimum = segment[
            "minimum_sg_heat_flux"
        ]

        close(
            float(
                maximum[
                    "ei_elapsed_seconds"
                ]
            ),
            float(
                local_time[
                    expected_max_index
                ]
            ),
            1e-9,
            f"{observed_names[index]} max time",
        )

        close(
            float(
                maximum[
                    "w_cm2"
                ]
            ),
            float(
                local_flux[
                    expected_max_index
                ]
                / 10000.0
            ),
            1e-9,
            f"{observed_names[index]} max flux",
        )

        close(
            float(
                minimum[
                    "ei_elapsed_seconds"
                ]
            ),
            float(
                local_time[
                    expected_min_index
                ]
            ),
            1e-9,
            f"{observed_names[index]} min time",
        )

        close(
            float(
                minimum[
                    "w_cm2"
                ]
            ),
            float(
                local_flux[
                    expected_min_index
                ]
                / 10000.0
            ),
            1e-9,
            f"{observed_names[index]} min flux",
        )

    rebound_segment = (
        segments[1]
    )

    expected_rebound_start_flux = (
        interp(
            time_s,
            heat_flux_w_m2,
            rebound_start,
        )
        / 10000.0
    )

    expected_rebound_end_flux = (
        interp(
            time_s,
            heat_flux_w_m2,
            rebound_end,
        )
        / 10000.0
    )

    expected_rebound_change_percent = (
        100.0
        * (
            expected_rebound_end_flux
            - expected_rebound_start_flux
        )
        / expected_rebound_start_flux
    )

    flux_change = product.get(
        "rebound_external_flux_change"
    )

    if not isinstance(
        flux_change,
        dict,
    ):
        fail(
            "missing rebound flux-change block"
        )

    close(
        float(
            flux_change[
                "start_w_cm2"
            ]
        ),
        expected_rebound_start_flux,
        1e-9,
        "rebound start flux",
    )

    close(
        float(
            flux_change[
                "end_w_cm2"
            ]
        ),
        expected_rebound_end_flux,
        1e-9,
        "rebound end flux",
    )

    close(
        float(
            flux_change[
                "signed_percent_change"
            ]
        ),
        expected_rebound_change_percent,
        1e-9,
        "rebound flux percent change",
    )

    if (
        flux_change.get(
            "relationship"
        )
        != "DECREASED"
    ):
        fail(
            "rebound external flux must "
            "remain classified as DECREASED"
        )

    if (
        rebound_segment[
            "maximum_sg_heat_flux"
        ][
            "location"
        ]
        != "START_BOUNDARY"
    ):
        fail(
            "rebound maximum should occur "
            "at interpolated start boundary"
        )

    if (
        rebound_segment[
            "minimum_sg_heat_flux"
        ][
            "location"
        ]
        != "END_BOUNDARY"
    ):
        fail(
            "rebound minimum should occur "
            "at interpolated end boundary"
        )

    partition = product.get(
        "strong_domain_partition"
    )

    if not isinstance(
        partition,
        dict,
    ):
        fail(
            "missing partition block"
        )

    close(
        float(
            partition[
                "existing_phase2e4_heat_load_mj_m2"
            ]
        ),
        strong_total_j_m2
        / 1e6,
        1e-9,
        "existing strong load",
    )

    close(
        float(
            partition[
                "partition_total_mj_m2"
            ]
        ),
        expected_total
        / 1e6,
        1e-9,
        "partition total",
    )

    expected_closure = (
        expected_total
        - strong_total_j_m2
    )

    close(
        float(
            partition[
                "closure_error_j_m2"
            ]
        ),
        expected_closure,
        1e-5,
        "partition closure",
    )

    if abs(
        expected_closure
    ) > 1e-3:
        fail(
            "heat-load partition closure "
            "exceeds 1e-3 J/m^2"
        )

    close(
        float(
            partition[
                "partition_percent_total"
            ]
        ),
        sum(
            expected_percents
        ),
        1e-9,
        "partition percent total",
    )

    if abs(
        sum(
            expected_percents
        )
        - 100.0
    ) > 1e-8:
        fail(
            "segment percentages do not "
            "sum to 100%"
        )

    post_peak = product.get(
        "post_peak_heat_load_context"
    )

    if not isinstance(
        post_peak,
        dict,
    ):
        fail(
            "missing post-peak context"
        )

    expected_peak_to_start = (
        integrate_between(
            time_s,
            heat_flux_w_m2,
            sg_peak_time,
            rebound_start,
        )
    )

    expected_peak_to_end = (
        integrate_between(
            time_s,
            heat_flux_w_m2,
            sg_peak_time,
            rebound_end,
        )
    )

    expected_peak_to_mach5 = (
        integrate_between(
            time_s,
            heat_flux_w_m2,
            sg_peak_time,
            mach5_end,
        )
    )

    close(
        float(
            post_peak[
                "sg_peak_to_rebound_start_mj_m2"
            ]
        ),
        expected_peak_to_start
        / 1e6,
        1e-9,
        "peak-to-rebound-start load",
    )

    close(
        float(
            post_peak[
                "sg_peak_to_rebound_end_mj_m2"
            ]
        ),
        expected_peak_to_end
        / 1e6,
        1e-9,
        "peak-to-rebound-end load",
    )

    close(
        float(
            post_peak[
                "sg_peak_to_final_mach5_mj_m2"
            ]
        ),
        expected_peak_to_mach5
        / 1e6,
        1e-9,
        "peak-to-Mach5 load",
    )

    if (
        product.get(
            "interpretation_guardrails"
        )
        != EXPECTED_GUARDRAILS
    ):
        fail(
            "interpretation guardrails "
            "changed"
        )

    observed_figures = set(
        product.get(
            "figures",
            [],
        )
    )

    expected_figures = {
        str(
            path.relative_to(
                ROOT
            )
        )
        for path in FIGURES
    }

    if (
        observed_figures
        != expected_figures
    ):
        fail(
            "figure inventory mismatch"
        )

    for figure in FIGURES:
        if not figure.exists():
            fail(
                f"missing figure: {figure}"
            )

        text = figure.read_text(
            encoding="utf-8",
        )

        if "<svg" not in text:
            fail(
                f"invalid SVG: {figure}"
            )

        if len(
            text
        ) < 1000:
            fail(
                f"unexpectedly small SVG: {figure}"
            )

    print()
    print(
        "Phase 2F.3 Loft Heating-History "
        "Validation"
    )

    print(
        "======================================"
    )

    print()
    print(
        "Thermal-history order:"
    )

    print(
        f"  strong start: "
        f"EI+{strong_start:.6f} s"
    )

    print(
        f"  SG peak:      "
        f"EI+{sg_peak_time:.6f} s"
    )

    print(
        f"  loft start:   "
        f"EI+{rebound_start:.6f} s"
    )

    print(
        f"  loft end:     "
        f"EI+{rebound_end:.6f} s"
    )

    print(
        f"  Mach 5:       "
        f"EI+{mach5_end:.6f} s"
    )

    print()
    print(
        "Strong-domain heat-load partition:"
    )

    for name, load, percent in zip(
        EXPECTED_SEGMENTS,
        expected_loads,
        expected_percents,
    ):
        print(
            f"  {name}:"
        )

        print(
            f"    "
            f"{load / 1e6:.9f} MJ/m^2"
        )

        print(
            f"    "
            f"{percent:.6f}%"
        )

    print()
    print(
        "Rebound external SG flux:"
    )

    print(
        f"  start: "
        f"{expected_rebound_start_flux:.6f} W/cm^2"
    )

    print(
        f"  end:   "
        f"{expected_rebound_end_flux:.6f} W/cm^2"
    )

    print(
        f"  change: "
        f"{expected_rebound_change_percent:+.6f}%"
    )

    print(
        "  maximum location: START_BOUNDARY"
    )

    print(
        "  minimum location: END_BOUNDARY"
    )

    print()
    print(
        "Partition closure:"
    )

    print(
        f"  reconstructed: "
        f"{expected_total / 1e6:.9f} MJ/m^2"
    )

    print(
        f"  Phase 2E.4:    "
        f"{strong_total_j_m2 / 1e6:.9f} MJ/m^2"
    )

    print(
        f"  error: "
        f"{expected_closure:.9f} J/m^2"
    )

    print(
        f"  percent sum: "
        f"{sum(expected_percents):.9f}%"
    )

    print()
    print(
        "Post-peak context:"
    )

    print(
        f"  peak -> loft start: "
        f"{expected_peak_to_start / 1e6:.9f} MJ/m^2"
    )

    print(
        f"  peak -> loft end: "
        f"{expected_peak_to_end / 1e6:.9f} MJ/m^2"
    )

    print(
        f"  peak -> Mach 5: "
        f"{expected_peak_to_mach5 / 1e6:.9f} MJ/m^2"
    )

    print()
    print(
        "Guardrails:"
    )

    print(
        "  external-flux decline -> "
        "internal cooling: PROHIBITED"
    )

    print(
        "  external heat load -> "
        "Avcoat damage: PROHIBITED"
    )

    print(
        "  loft -> skip-entry relabeling: "
        "PROHIBITED"
    )

    print()
    print(
        "Figures checked: 3"
    )

    print()
    print(
        "OK: Phase 2F.3 loft/heating "
        "segmentation, interval endpoints, "
        "strong-domain heat-load partition, "
        "post-peak context, figures, and "
        "interpretation guardrails "
        "independently validated."
    )


if __name__ == "__main__":
    main()
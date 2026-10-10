from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_esm_propulsion_architecture.json"
)

MANEUVER_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_plan_execution.json"
)

ARCHITECTURE_CSV = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "esm_propulsion_architecture.csv"
)

SELECTION_CSV = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "burn_selection_evidence.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "esm_propulsion_architecture_summary.json"
)

ARCHITECTURE_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "maneuvers"
    / "phase2i2_esm_propulsion_architecture.svg"
)

SELECTION_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "maneuvers"
    / "phase2i2_burn_selection_evidence.svg"
)

EXPECTED_DATASET_ID = (
    "phase2i2_artemis_ii_esm_propulsion_architecture"
)

EXPECTED_PRODUCT_ID = (
    "phase2i2_esm_propulsion_architecture_analysis"
)


def fail(message: str) -> None:
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def load_json(path: Path):
    if not path.exists():
        fail(
            f"missing file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def check_close(
    label,
    observed,
    expected,
    tolerance=1e-9,
):
    if abs(
        float(observed)
        - float(expected)
    ) > tolerance:
        fail(
            f"{label}: "
            f"{observed} != {expected}"
        )


def main() -> None:
    reference = load_json(
        REFERENCE_PATH
    )

    maneuver_reference = load_json(
        MANEUVER_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    if (
        reference.get(
            "dataset_id"
        )
        != EXPECTED_DATASET_ID
    ):
        fail(
            "reference dataset ID mismatch"
        )

    if (
        summary.get(
            "product_id"
        )
        != EXPECTED_PRODUCT_ID
    ):
        fail(
            "summary product ID mismatch"
        )

    architecture = (
        reference[
            "architecture"
        ]
    )

    if (
        architecture[
            "engine_class_count"
        ]
        != 3
    ):
        fail(
            "engine-class count changed"
        )

    if (
        architecture[
            "total_engine_count"
        ]
        != 33
    ):
        fail(
            "total engine count changed"
        )

    classes = {
        item[
            "engine_class_id"
        ]:
            item
        for item in architecture[
            "engine_classes"
        ]
    }

    if set(
        classes
    ) != {
        "main_engine_oms_e",
        "auxiliary_r4d11",
        "reaction_control_system",
    }:
        fail(
            "engine-class identity changed"
        )

    main = (
        classes[
            "main_engine_oms_e"
        ]
    )

    aux = (
        classes[
            "auxiliary_r4d11"
        ]
    )

    rcs = (
        classes[
            "reaction_control_system"
        ]
    )

    if (
        main[
            "count"
        ]
        != 1
        or aux[
            "count"
        ]
        != 8
        or rcs[
            "count"
        ]
        != 24
    ):
        fail(
            "engine counts changed"
        )

    if (
        main[
            "count"
        ]
        + aux[
            "count"
        ]
        + rcs[
            "count"
        ]
        != 33
    ):
        fail(
            "engine counts do not sum to 33"
        )

    if (
        rcs[
            "pod_count"
        ]
        != 6
        or rcs[
            "engines_per_pod"
        ]
        != 4
    ):
        fail(
            "RCS pod arrangement changed"
        )

    if (
        rcs[
            "pod_count"
        ]
        * rcs[
            "engines_per_pod"
        ]
        != 24
    ):
        fail(
            "RCS pod arithmetic failed"
        )

    check_close(
        "main thrust",
        main[
            "nominal_thrust_newtons_each"
        ],
        25700.0,
    )

    check_close(
        "auxiliary thrust",
        aux[
            "nominal_thrust_newtons_each"
        ],
        490.0,
    )

    check_close(
        "RCS thrust",
        rcs[
            "nominal_thrust_newtons_each"
        ],
        220.0,
    )

    if (
        main[
            "gimballed"
        ]
        is not True
    ):
        fail(
            "main engine must remain gimballed"
        )

    if (
        aux[
            "display_name"
        ]
        != "R-4D-11 Auxiliary Engine"
    ):
        fail(
            "R-4D-11 identification changed"
        )

    expected_ratios = {
        "main_to_auxiliary":
            25700.0 / 490.0,

        "auxiliary_to_rcs":
            490.0 / 220.0,

        "main_to_rcs":
            25700.0 / 220.0,
    }

    observed_ratios = (
        summary[
            "derived_per_engine_thrust_ratios"
        ]
    )

    for key, expected in (
        expected_ratios.items()
    ):
        check_close(
            key,
            observed_ratios[
                key
            ],
            expected,
        )

    confirmed = {
        item[
            "maneuver_id"
        ]:
            item
        for item in reference[
            "confirmed_as_flown_major_maneuvers"
        ]
    }

    if set(
        confirmed
    ) != {
        "perigee_raise",
        "tli",
    }:
        fail(
            "confirmed major-maneuver assignments changed"
        )

    if (
        confirmed[
            "perigee_raise"
        ][
            "engine_class_id"
        ]
        != "main_engine_oms_e"
    ):
        fail(
            "perigee raise engine assignment changed"
        )

    check_close(
        "perigee raise duration",
        confirmed[
            "perigee_raise"
        ][
            "duration_seconds"
        ],
        43.0,
    )

    if (
        confirmed[
            "tli"
        ][
            "engine_class_id"
        ]
        != "main_engine_oms_e"
    ):
        fail(
            "TLI engine assignment changed"
        )

    check_close(
        "TLI duration",
        confirmed[
            "tli"
        ][
            "duration_seconds"
        ],
        350.0,
    )

    evidence = {
        item[
            "evidence_id"
        ]:
            item
        for item in reference[
            "trajectory_correction_selection_evidence"
        ]
    }

    nasa_plan = (
        evidence[
            "nasa_premission_outbound_oms_plan"
        ]
    )

    esa_operations = (
        evidence[
            "esa_operational_correction_selection"
        ]
    )

    if (
        nasa_plan[
            "evidence_stage"
        ]
        != "PREMISSION_PLAN"
        or nasa_plan[
            "engine_selection_claim"
        ]
        != "OMS_E"
        or nasa_plan[
            "burn_specific_as_flown_assignment"
        ]
        is not False
    ):
        fail(
            "NASA premission evidence boundary failed"
        )

    if (
        esa_operations[
            "evidence_stage"
        ]
        != "MISSION_OPERATIONAL_EXPLANATION"
        or esa_operations[
            "larger_correction_class"
        ]
        != "AUXILIARY"
        or esa_operations[
            "finer_correction_class"
        ]
        != "RCS"
        or esa_operations[
            "burn_specific_as_flown_assignment"
        ]
        is not False
    ):
        fail(
            "ESA operational evidence boundary failed"
        )

    relationship = (
        reference[
            "source_relationship"
        ]
    )

    if (
        relationship[
            "classification"
        ]
        != "SOURCE_SCOPE_OR_PLAN_DIFFERENCE_PRESERVED"
    ):
        fail(
            "source-relationship classification changed"
        )

    if (
        relationship[
            "treated_as_identical"
        ]
        is not False
        or relationship[
            "forced_reconciliation"
        ]
        is not False
        or relationship[
            "burn_specific_resolution_available"
        ]
        is not False
    ):
        fail(
            "source distinction was incorrectly reconciled"
        )

    corrections = (
        reference[
            "correction_burn_assignments"
        ]
    )

    expected_correction_ids = [
        "otc3",
        "rtc1",
        "rtc2",
        "rtc3",
    ]

    if [
        item[
            "maneuver_id"
        ]
        for item in corrections
    ] != expected_correction_ids:
        fail(
            "correction assignment identities changed"
        )

    phase2i1 = {
        item[
            "maneuver_id"
        ]:
            item
        for item in maneuver_reference[
            "maneuvers"
        ]
    }

    for item in corrections:
        maneuver_id = (
            item[
                "maneuver_id"
            ]
        )

        if (
            item[
                "assignment_status"
            ]
            != "UNRESOLVED_AS_FLOWN"
        ):
            fail(
                f"{maneuver_id} assignment "
                "incorrectly resolved"
            )

        if (
            item[
                "as_flown_engine_class_id"
            ]
            is not None
        ):
            fail(
                f"{maneuver_id} gained unsupported "
                "engine class"
            )

        execution = (
            phase2i1[
                maneuver_id
            ][
                "execution"
            ]
        )

        check_close(
            f"{maneuver_id} duration",
            item[
                "duration_seconds"
            ],
            execution[
                "duration_seconds"
            ],
        )

        expected_dv = (
            execution.get(
                "reported_delta_v_ft_s"
            )
        )

        observed_dv = (
            item.get(
                "reported_delta_v_ft_s"
            )
        )

        if expected_dv is None:
            if observed_dv is not None:
                fail(
                    f"{maneuver_id} gained unsupported delta-v"
                )
        else:
            check_close(
                f"{maneuver_id} delta-v",
                observed_dv,
                expected_dv,
            )

    boundary = (
        reference[
            "selection_boundary"
        ]
    )

    if (
        boundary[
            "flight_rules_influence_engine_selection"
        ]
        is not True
    ):
        fail(
            "flight-rule selection evidence lost"
        )

    if (
        boundary[
            "required_correction_influences_engine_selection"
        ]
        is not True
    ):
        fail(
            "required-correction selection evidence lost"
        )

    if (
        boundary[
            "exact_public_selection_thresholds_available"
        ]
        is not False
        or boundary[
            "exact_public_selection_algorithm_available"
        ]
        is not False
    ):
        fail(
            "unsupported selection thresholds "
            "or algorithm introduced"
        )

    for maneuver_id in (
        expected_correction_ids
    ):
        key = (
            f"{maneuver_id}_exact_engine_"
            "assignment_available"
        )

        if (
            boundary[
                key
            ]
            is not False
        ):
            fail(
                f"{maneuver_id} incorrectly "
                "marked resolved"
            )

    metric_policy = (
        reference[
            "derived_metric_policy"
        ]
    )

    if (
        metric_policy[
            "ratios_are_architecture_context_only"
        ]
        is not True
        or metric_policy[
            "ratios_are_not_spacecraft_acceleration_ratios"
        ]
        is not True
        or metric_policy[
            "installed_engine_count_times_thrust_is_not_one_direction_available_thrust"
        ]
        is not True
        or metric_policy[
            "thrust_times_duration_is_not_computed_as_maneuver_impulse_without_as_flown_engine_assignment"
        ]
        is not True
    ):
        fail(
            "derived-metric guardrail changed"
        )

    if not ARCHITECTURE_CSV.exists():
        fail(
            "architecture CSV missing"
        )

    with ARCHITECTURE_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        architecture_rows = list(
            csv.DictReader(f)
        )

    if len(
        architecture_rows
    ) != 3:
        fail(
            "architecture CSV must contain three rows"
        )

    if [
        row[
            "engine_class_id"
        ]
        for row in architecture_rows
    ] != [
        "main_engine_oms_e",
        "auxiliary_r4d11",
        "reaction_control_system",
    ]:
        fail(
            "architecture CSV ordering changed"
        )

    if not SELECTION_CSV.exists():
        fail(
            "selection-evidence CSV missing"
        )

    with SELECTION_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        selection_rows = list(
            csv.DictReader(f)
        )

    if len(
        selection_rows
    ) != 6:
        fail(
            "selection-evidence CSV must contain six rows"
        )

    if [
        row[
            "assignment_status"
        ]
        for row in selection_rows[2:]
    ] != [
        "UNRESOLVED_AS_FLOWN",
        "UNRESOLVED_AS_FLOWN",
        "UNRESOLVED_AS_FLOWN",
        "UNRESOLVED_AS_FLOWN",
    ]:
        fail(
            "as-flown correction assignments "
            "were incorrectly resolved in CSV"
        )

    if (
        summary[
            "architecture"
        ][
            "engine_class_count"
        ]
        != 3
        or summary[
            "architecture"
        ][
            "total_engine_count"
        ]
        != 33
    ):
        fail(
            "summary architecture counts changed"
        )

    if (
        summary[
            "as_flown_correction_assignments"
        ][
            "count"
        ]
        != 4
        or summary[
            "as_flown_correction_assignments"
        ][
            "resolved_count"
        ]
        != 0
        or summary[
            "as_flown_correction_assignments"
        ][
            "unresolved_count"
        ]
        != 4
    ):
        fail(
            "summary correction-assignment counts changed"
        )

    if (
        summary[
            "correction_selection_evidence"
        ][
            "forced_reconciliation"
        ]
        is not False
    ):
        fail(
            "summary forced source reconciliation"
        )

    if (
        summary[
            "selection_boundary"
        ]
        != boundary
    ):
        fail(
            "summary selection boundary mismatch"
        )

    if (
        summary[
            "guardrails"
        ]
        != reference[
            "guardrails"
        ]
    ):
        fail(
            "summary guardrails mismatch"
        )

    for figure in [
        ARCHITECTURE_FIGURE,
        SELECTION_FIGURE,
    ]:
        if not figure.exists():
            fail(
                f"figure missing: {figure}"
            )

        svg = figure.read_text(
            encoding="utf-8"
        )

        if (
            "<svg" not in svg
            or len(svg) < 1000
        ):
            fail(
                f"invalid SVG: {figure}"
            )

    print()
    print(
        "Phase 2I.2 ESM Propulsion Architecture / "
        "Burn-Selection Validation"
    )

    print("=" * 70)

    print()
    print(
        "Architecture:"
    )

    print(
        "  engine classes: 3"
    )

    print(
        "  total engines: 33"
    )

    print(
        "  main engine: 1"
    )

    print(
        "  auxiliary engines: 8"
    )

    print(
        "  RCS engines: 24"
    )

    print(
        "  RCS arrangement: 6 pods x 4"
    )

    print()
    print(
        "Nominal thrust:"
    )

    print(
        "  OMS-E: 25.7 kN"
    )

    print(
        "  auxiliary: 490 N each"
    )

    print(
        "  RCS: 220 N each"
    )

    print()
    print(
        "Per-engine thrust ratios:"
    )

    print(
        f"  main / auxiliary: "
        f"{expected_ratios['main_to_auxiliary']:.3f}x"
    )

    print(
        f"  auxiliary / RCS: "
        f"{expected_ratios['auxiliary_to_rcs']:.3f}x"
    )

    print(
        f"  main / RCS: "
        f"{expected_ratios['main_to_rcs']:.3f}x"
    )

    print(
        "  architecture context only: PASS"
    )

    print()
    print(
        "Confirmed as-flown major maneuvers:"
    )

    print(
        "  perigee raise -> OMS-E: PASS"
    )

    print(
        "  perigee raise duration -> 43.0 s: PASS"
    )

    print(
        "  TLI -> OMS-E: PASS"
    )

    print(
        "  TLI duration -> 350.0 s: PASS"
    )

    print()
    print(
        "Correction-selection evidence:"
    )

    print(
        "  NASA premission OMS-E plan: PASS"
    )

    print(
        "  ESA auxiliary/RCS flight-rule explanation: PASS"
    )

    print(
        "  evidence layers kept separate: PASS"
    )

    print(
        "  forced reconciliation: FALSE"
    )

    print()
    print(
        "As-flown correction assignments:"
    )

    print(
        "  OTC3: UNRESOLVED"
    )

    print(
        "  RTC1: UNRESOLVED"
    )

    print(
        "  RTC2: UNRESOLVED"
    )

    print(
        "  RTC3: UNRESOLVED"
    )

    print(
        "  resolved count: 0"
    )

    print(
        "  unresolved count: 4"
    )

    print()
    print(
        "Public selection boundary:"
    )

    print(
        "  flight rules influence selection: TRUE"
    )

    print(
        "  required correction influences selection: TRUE"
    )

    print(
        "  exact public thresholds: NONE"
    )

    print(
        "  exact public algorithm: NONE"
    )

    print()
    print(
        "Products:"
    )

    print(
        "  architecture CSV rows: 3"
    )

    print(
        "  selection-evidence CSV rows: 6"
    )

    print(
        "  summary: PASS"
    )

    print(
        "  architecture figure: PASS"
    )

    print(
        "  selection-evidence figure: PASS"
    )

    print()
    print(
        "OK: Phase 2I.2 ESM propulsion architecture, "
        "Artemis II engine-class roles, nominal thrust values, "
        "confirmed main-engine major maneuvers, NASA premission "
        "versus ESA operational correction-selection evidence, "
        "source-layer separation, unresolved as-flown correction "
        "assignments, per-engine thrust-ratio boundaries, "
        "generated products, and non-inference guardrails "
        "independently validated."
    )


if __name__ == "__main__":
    main()
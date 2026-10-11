from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

TPS_EVIDENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_tps_evidence.json"
)

TPS_PHYSICS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_tps_physics_boundary.json"
)

ENTRY_HERITAGE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_entry_profile_heritage.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "thermal"
)

CLOSURE_JSON = (
    OUTPUT_DIR
    / "artemis_tps_risk_closure.json"
)

CLOSURE_CSV = (
    OUTPUT_DIR
    / "artemis_tps_risk_closure_steps.csv"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "thermal"
    / "phase3c1_tps_risk_closure.svg"
)


EXPECTED_IDS = {
    "tps_evidence": (
        "phase2f1_orion_tps_heritage_evidence"
    ),
    "tps_physics": (
        "phase2f4_artemis_tps_physics_boundary"
    ),
    "entry_heritage": (
        "phase2f2_artemis_entry_profile_heritage"
    ),
    "phase3c1": (
        "phase3c1_artemis_tps_"
        "heritage_to_flight_risk_closure"
    ),
}


EXPECTED_STEP_IDS = [
    "artemis_i_anomaly",
    "artemis_i_root_cause",
    "artemis_i_environment_role",
    "artemis_ii_mitigation",
    "artemis_ii_as_flown",
    "artemis_ii_initial_postflight",
    "closure_boundary",
]


EXPECTED_STAGES = [
    "HERITAGE_ANOMALY",
    "ROOT_CAUSE",
    "ENVIRONMENT_INTERACTION",
    "RISK_MITIGATION",
    "AS_FLOWN_CONFIGURATION",
    "POSTFLIGHT_OUTCOME",
    "EVIDENCE_BOUNDARY",
]


REQUIRED_EVIDENCE_IDS = {
    "artemis_i_unexpected_char_loss",
    "artemis_i_root_cause_low_permeability",
    "artemis_i_skip_entry_role",
    "permeable_regions_did_not_show_same_behavior",
    "artemis_i_thermal_test_campaign",
    "artemis_i_ground_replication",
    "artemis_ii_trajectory_mitigation",
    "artemis_ii_no_skip_entry",
    "artemis_ii_postflight_tps_expected",
    "artemis_ii_char_loss_reduced",
    "artemis_ii_arcjet_consistency",
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 3C.1 VALIDATION FAILED: "
        f"{message}"
    )


def require(
    condition: bool,
    message: str,
):
    if not condition:
        fail(
            message
        )


def load_json(
    path: Path,
) -> dict:
    if not path.exists():
        fail(
            f"missing JSON file: {path}"
        )

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as f:
            return json.load(
                f
            )

    except json.JSONDecodeError as exc:
        fail(
            f"invalid JSON in {path}: {exc}"
        )

        raise


def load_csv(
    path: Path,
) -> list[dict]:
    if not path.exists():
        fail(
            f"missing CSV file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        return list(
            csv.DictReader(
                f
            )
        )


def bool_from_csv(
    value: str,
    label: str,
) -> bool:
    normalized = (
        value
        .strip()
        .lower()
    )

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    fail(
        f"{label} is not boolean: "
        f"{value!r}"
    )

    raise RuntimeError


def normalize_path(
    value: str,
) -> str:
    return value.replace(
        "\\",
        "/",
    )


def index_evidence(
    tps_evidence: dict,
) -> dict[str, dict]:
    result = {}

    for item in tps_evidence[
        "evidence_items"
    ]:
        item_id = (
            item[
                "id"
            ]
        )

        require(
            item_id not in result,
            (
                "duplicate TPS evidence "
                f"item: {item_id}"
            ),
        )

        result[
            item_id
        ] = item

    return result


def index_entry_heritage(
    entry_heritage: dict,
) -> dict[str, dict]:
    result = {}

    for item in entry_heritage[
        "evidence_items"
    ]:
        item_id = (
            item[
                "id"
            ]
        )

        require(
            item_id not in result,
            (
                "duplicate entry heritage "
                f"item: {item_id}"
            ),
        )

        result[
            item_id
        ] = item

    return result


def index_chain(
    closure: dict,
) -> dict[str, dict]:
    result = {}

    for step in closure[
        "closure_chain"
    ]:
        step_id = (
            step[
                "step_id"
            ]
        )

        require(
            step_id not in result,
            (
                "duplicate closure step: "
                f"{step_id}"
            ),
        )

        result[
            step_id
        ] = step

    return result


def validate_identity(
    tps_evidence: dict,
    tps_physics: dict,
    entry_heritage: dict,
    closure: dict,
):
    observed = {
        "tps_evidence": (
            tps_evidence.get(
                "dataset_id"
            )
        ),
        "tps_physics": (
            tps_physics.get(
                "dataset_id"
            )
        ),
        "entry_heritage": (
            entry_heritage.get(
                "dataset_id"
            )
        ),
        "phase3c1": (
            closure.get(
                "dataset_id"
            )
        ),
    }

    for (
        key,
        expected,
    ) in EXPECTED_IDS.items():
        require(
            observed[
                key
            ]
            == expected,
            (
                f"{key} dataset "
                "identity mismatch"
            ),
        )

    require(
        closure.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        closure.get(
            "heritage_mission"
        )
        == "Artemis I",
        "heritage mission mismatch",
    )

    require(
        closure.get(
            "phase"
        )
        == "3C.1",
        "phase identity mismatch",
    )

    require(
        closure.get(
            "status"
        )
        == (
            "INITIAL_FLIGHT_MITIGATION_"
            "CLOSURE_SUPPORTED"
        ),
        "Phase 3C.1 status mismatch",
    )


def validate_dependencies(
    tps_evidence: dict,
    tps_physics: dict,
    entry_heritage: dict,
    closure: dict,
):
    dependencies = (
        closure[
            "dependencies"
        ]
    )

    expected = {
        "tps_evidence": (
            tps_evidence[
                "dataset_id"
            ]
        ),
        "tps_physics_boundary": (
            tps_physics[
                "dataset_id"
            ]
        ),
        "entry_profile_heritage": (
            entry_heritage[
                "dataset_id"
            ]
        ),
    }

    require(
        dependencies
        == expected,
        "dependency registry mismatch",
    )

    require(
        tps_physics.get(
            "source_evidence_dataset_id"
        )
        == tps_evidence[
            "dataset_id"
        ],
        (
            "TPS physics boundary "
            "source dependency mismatch"
        ),
    )


def validate_phase2_evidence(
    evidence: dict[str, dict],
):
    missing = (
        REQUIRED_EVIDENCE_IDS
        - set(
            evidence
        )
    )

    require(
        not missing,
        (
            "required TPS evidence missing: "
            f"{sorted(missing)}"
        ),
    )

    anomaly = (
        evidence[
            "artemis_i_unexpected_char_loss"
        ]
    )

    require(
        anomaly[
            "mission_context"
        ]
        == "Artemis I",
        "Artemis I anomaly context mismatch",
    )

    require(
        anomaly[
            "category"
        ]
        == "ARTEMIS_I_ANOMALY",
        "Artemis I anomaly category mismatch",
    )

    root_cause = (
        evidence[
            "artemis_i_root_cause_low_permeability"
        ]
    )

    require(
        root_cause[
            "category"
        ]
        == "ROOT_CAUSE",
        "root-cause evidence category mismatch",
    )

    require(
        root_cause[
            "provenance"
        ]
        == "NASA_REPORTED",
        "root-cause provenance mismatch",
    )

    expected_mechanism = [
        "Avcoat heats during atmospheric entry",
        (
            "pyrolysis and ablation generate "
            "gases inside the material"
        ),
        (
            "low-permeability Avcoat "
            "restricts gas escape"
        ),
        (
            "internal gas pressure increases"
        ),
        "cracks form",
        "charred material is liberated",
    ]

    require(
        root_cause[
            "mechanism"
        ][
            "sequence"
        ]
        == expected_mechanism,
        (
            "NASA-reported Artemis I "
            "root-cause mechanism changed"
        ),
    )

    require(
        evidence[
            "permeable_regions_did_not_show_same_behavior"
        ][
            "category"
        ]
        == "ROOT_CAUSE_EVIDENCE",
        (
            "permeability comparison "
            "evidence changed"
        ),
    )

    thermal_tests = (
        evidence[
            "artemis_i_thermal_test_campaign"
        ][
            "key_values"
        ]
    )

    require(
        thermal_tests[
            "thermal_test_campaigns"
        ]
        == 8,
        "thermal-test campaign count changed",
    )

    require(
        thermal_tests[
            "individual_tests"
        ]
        == 121,
        "individual thermal-test count changed",
    )

    require(
        evidence[
            "artemis_i_ground_replication"
        ][
            "category"
        ]
        == "ROOT_CAUSE_EVIDENCE",
        (
            "ground-replication evidence "
            "category changed"
        ),
    )

    require(
        evidence[
            "artemis_ii_trajectory_mitigation"
        ][
            "category"
        ]
        == "ARTEMIS_II_MITIGATION",
        (
            "Artemis II trajectory "
            "mitigation evidence changed"
        ),
    )

    require(
        evidence[
            "artemis_ii_no_skip_entry"
        ][
            "category"
        ]
        == "ARTEMIS_II_MITIGATION",
        (
            "Artemis II no-skip "
            "evidence category changed"
        ),
    )

    require(
        evidence[
            "artemis_ii_postflight_tps_expected"
        ][
            "category"
        ]
        == "ARTEMIS_II_POSTFLIGHT",
        (
            "Artemis II postflight TPS "
            "evidence changed"
        ),
    )

    require(
        evidence[
            "artemis_ii_char_loss_reduced"
        ][
            "category"
        ]
        == "ARTEMIS_II_POSTFLIGHT",
        (
            "Artemis II char-loss "
            "evidence changed"
        ),
    )

    require(
        evidence[
            "artemis_ii_arcjet_consistency"
        ][
            "category"
        ]
        == "ARTEMIS_II_POSTFLIGHT",
        (
            "Artemis II arc-jet "
            "evidence changed"
        ),
    )


def validate_physics_boundary(
    tps_physics: dict,
):
    physics = (
        tps_physics[
            "physics_boundary"
        ]
    )

    require(
        physics[
            "missionlab_quantitative_frontier_stage_id"
        ]
        == "external_convective_heating",
        (
            "MissionLab quantitative "
            "frontier changed"
        ),
    )

    require(
        physics[
            "boundary_begins_at_stage_id"
        ]
        == (
            "surface_internal_"
            "thermal_response"
        ),
        (
            "material-response boundary "
            "changed"
        ),
    )

    stages = (
        physics[
            "stages"
        ]
    )

    require(
        len(
            stages
        )
        == 8,
        (
            "TPS physics boundary "
            "expected 8 stages"
        ),
    )

    require(
        stages[
            0
        ][
            "stage_id"
        ]
        == "trajectory_external_flow",
        (
            "TPS physics first stage "
            "changed"
        ),
    )

    require(
        stages[
            1
        ][
            "stage_id"
        ]
        == "external_convective_heating",
        (
            "TPS heating frontier "
            "stage changed"
        ),
    )

    require(
        stages[
            2
        ][
            "stage_id"
        ]
        == (
            "surface_internal_"
            "thermal_response"
        ),
        (
            "TPS material boundary "
            "start stage changed"
        ),
    )

    model_assertions = (
        tps_physics[
            "model_assertions"
        ]
    )

    for (
        key,
        value,
    ) in model_assertions.items():
        require(
            value is False,
            (
                "forbidden model assertion "
                f"became TRUE: {key}"
            ),
        )

    prohibited = (
        tps_physics[
            "prohibited_model_bridges"
        ]
    )

    require(
        len(
            prohibited
        )
        >= 7,
        (
            "TPS prohibited-model-bridge "
            "registry unexpectedly small"
        ),
    )

    for bridge in prohibited:
        require(
            bridge[
                "status"
            ]
            == "PROHIBITED",
            (
                "TPS model bridge no "
                "longer prohibited: "
                f"{bridge['from']} -> "
                f"{bridge['to']}"
            ),
        )


def validate_entry_heritage(
    entry_heritage: dict,
    heritage_index: dict[str, dict],
):
    require(
        "artemis_i_skip_apogee"
        in heritage_index,
        (
            "Artemis I skip-entry "
            "heritage missing"
        ),
    )

    require(
        heritage_index[
            "artemis_i_skip_apogee"
        ][
            "key_values"
        ][
            "entry_classification"
        ]
        == "SKIP_ENTRY",
        (
            "Artemis I skip-entry "
            "classification changed"
        ),
    )

    require(
        "artemis_ii_no_skip_entry"
        in heritage_index,
        (
            "Artemis II no-skip "
            "heritage missing"
        ),
    )

    require(
        heritage_index[
            "artemis_ii_no_skip_entry"
        ][
            "key_values"
        ][
            "entry_classification"
        ]
        == (
            "MODIFIED_TRAJECTORY_"
            "WITHOUT_SKIP_ENTRY"
        ),
        (
            "Artemis II no-skip "
            "classification changed"
        ),
    )

    guardrails = (
        entry_heritage.get(
            "interpretation_guardrails",
            [],
        )
    )

    require(
        isinstance(
            guardrails,
            list,
        ),
        (
            "entry heritage interpretation "
            "guardrails must be a list"
        ),
    )

    require(
        (
            "Artemis II must not be "
            "labeled a skip entry."
        )
        in guardrails,
        (
            "Artemis II no-skip "
            "guardrail missing"
        ),
    )

    require(
        (
            "No trajectory comparison may "
            "be converted into a TPS char-loss "
            "or damage prediction."
        )
        in guardrails,
        (
            "TPS damage-prediction "
            "guardrail missing"
        ),
    )

    require(
        (
            "No causal claim may be made "
            "that every Artemis I versus "
            "Artemis II entry-profile "
            "difference was driven "
            "exclusively by the "
            "heat-shield investigation."
        )
        in guardrails,
        (
            "TPS exclusive-causality "
            "guardrail missing"
        ),
    )


def validate_closure_chain(
    closure: dict,
    evidence: dict[str, dict],
) -> list[dict]:
    chain = (
        closure[
            "closure_chain"
        ]
    )

    require(
        len(
            chain
        )
        == 7,
        (
            "closure chain expected "
            f"7 steps, found {len(chain)}"
        ),
    )

    require(
        [
            step[
                "order"
            ]
            for step
            in chain
        ]
        == list(
            range(
                1,
                8,
            )
        ),
        "closure step numbering mismatch",
    )

    require(
        [
            step[
                "step_id"
            ]
            for step
            in chain
        ]
        == EXPECTED_STEP_IDS,
        (
            "closure step IDs or "
            "ordering mismatch"
        ),
    )

    require(
        [
            step[
                "stage"
            ]
            for step
            in chain
        ]
        == EXPECTED_STAGES,
        (
            "closure stage sequence "
            "mismatch"
        ),
    )

    root_claim_steps = []

    for step in chain:
        require(
            step[
                "provenance"
            ]
            == (
                "MISSIONLAB_DERIVED_"
                "TPS_RISK_CLOSURE"
            ),
            (
                f"{step['step_id']} "
                "provenance mismatch"
            ),
        )

        require(
            isinstance(
                step[
                    "evidence_ids"
                ],
                list,
            )
            and len(
                step[
                    "evidence_ids"
                ]
            )
            >= 1,
            (
                f"{step['step_id']} "
                "missing evidence IDs"
            ),
        )

        for evidence_id in (
            step[
                "evidence_ids"
            ]
        ):
            require(
                evidence_id in evidence,
                (
                    f"{step['step_id']} "
                    "references unknown "
                    "TPS evidence "
                    f"{evidence_id}"
                ),
            )

        require(
            step[
                "quantitative_damage_claim"
            ]
            is False,
            (
                f"{step['step_id']} "
                "makes quantitative "
                "damage claim"
            ),
        )

        require(
            step[
                "final_postflight_closure_claim"
            ]
            is False,
            (
                f"{step['step_id']} "
                "claims final postflight "
                "material closure"
            ),
        )

        if (
            step[
                "root_cause_claim"
            ]
            is True
        ):
            root_claim_steps.append(
                step[
                    "step_id"
                ]
            )

    require(
        root_claim_steps
        == [
            "artemis_i_root_cause"
        ],
        (
            "root-cause claim must be "
            "limited to NASA's Artemis I "
            "root-cause finding"
        ),
    )

    chain_index = (
        index_chain(
            closure
        )
    )

    require(
        chain_index[
            "artemis_i_root_cause"
        ][
            "evidence_class"
        ]
        == (
            "NASA_REPORTED_"
            "ROOT_CAUSE"
        ),
        (
            "Artemis I root-cause "
            "evidence class mismatch"
        ),
    )

    require(
        chain_index[
            "artemis_ii_mitigation"
        ][
            "evidence_class"
        ]
        == (
            "NASA_REPORTED_"
            "MITIGATION"
        ),
        (
            "Artemis II mitigation "
            "evidence class mismatch"
        ),
    )

    require(
        chain_index[
            "artemis_ii_as_flown"
        ][
            "evidence_class"
        ]
        == (
            "NASA_REPORTED_"
            "AS_FLOWN"
        ),
        (
            "Artemis II as-flown "
            "evidence class mismatch"
        ),
    )

    require(
        chain_index[
            "artemis_ii_initial_postflight"
        ][
            "evidence_class"
        ]
        == (
            "NASA_REPORTED_"
            "INITIAL_POSTFLIGHT"
        ),
        (
            "Artemis II postflight "
            "evidence class mismatch"
        ),
    )

    require(
        chain_index[
            "closure_boundary"
        ][
            "evidence_class"
        ]
        == (
            "MISSIONLAB_DERIVED_"
            "EVIDENCE_BOUNDARY"
        ),
        (
            "closure-boundary evidence "
            "class mismatch"
        ),
    )

    return chain


def validate_root_cause_summary(
    closure: dict,
):
    summary = (
        closure[
            "root_cause_summary"
        ]
    )

    required_true = [
        "low_permeability_central",
        "restricted_gas_escape",
        "internal_pressure_buildup",
        "cracking",
        "char_liberation",
    ]

    for key in required_true:
        require(
            summary.get(
                key
            )
            is True,
            (
                "root-cause summary "
                f"expected TRUE: {key}"
            ),
        )

    require(
        summary[
            "heritage_mission"
        ]
        == "Artemis I",
        "root-cause mission mismatch",
    )

    require(
        summary[
            "material"
        ]
        == "Avcoat",
        "root-cause material mismatch",
    )

    require(
        summary[
            "root_cause_source"
        ]
        == "NASA_REPORTED",
        "root-cause source mismatch",
    )

    require(
        summary[
            "missionlab_numerically_models_mechanism"
        ]
        is False,
        (
            "MissionLab incorrectly "
            "claims numerical Avcoat "
            "mechanism model"
        ),
    )


def validate_mitigation_summary(
    closure: dict,
):
    summary = (
        closure[
            "mitigation_summary"
        ]
    )

    required_true = [
        "existing_heat_shield_retained",
        "entry_environment_modified",
        "modified_no_skip_trajectory_flown",
    ]

    for key in required_true:
        require(
            summary.get(
                key
            )
            is True,
            (
                "mitigation summary "
                f"expected TRUE: {key}"
            ),
        )

    require(
        summary[
            "target_mission"
        ]
        == "Artemis II",
        "mitigation target mission mismatch",
    )

    require(
        summary[
            "artemis_i_style_skip_entry_used"
        ]
        is False,
        (
            "Artemis II incorrectly "
            "classified as using "
            "Artemis I-style skip entry"
        ),
    )

    require(
        summary[
            "mitigation_source"
        ]
        == "NASA_REPORTED",
        "mitigation source mismatch",
    )

    require(
        summary[
            "full_internal_guidance_design_public"
        ]
        is False,
        (
            "closure incorrectly claims "
            "complete guidance design "
            "is public"
        ),
    )


def validate_postflight_summary(
    closure: dict,
):
    summary = (
        closure[
            "postflight_summary"
        ]
    )

    required_true = [
        "initial_tps_performance_expected",
        "artemis_i_type_char_loss_reduced",
        (
            "consistent_with_post_artemis_i_"
            "arcjet_testing"
        ),
        (
            "initial_postflight_supports_"
            "mitigation_effectiveness"
        ),
    ]

    required_false = [
        (
            "unusual_tps_conditions_"
            "identified_initially"
        ),
        (
            "char_loss_reduction_"
            "quantified_publicly"
        ),
        (
            "complete_public_material_"
            "dataset_available"
        ),
        (
            "final_sample_level_postflight_"
            "closure_claimed"
        ),
    ]

    for key in required_true:
        require(
            summary.get(
                key
            )
            is True,
            (
                "postflight summary "
                f"expected TRUE: {key}"
            ),
        )

    for key in required_false:
        require(
            summary.get(
                key
            )
            is False,
            (
                "postflight summary "
                f"expected FALSE: {key}"
            ),
        )


def validate_closure_assessment(
    closure: dict,
):
    assessment = (
        closure[
            "closure_assessment"
        ]
    )

    required_true = [
        "heritage_anomaly_identified",
        "heritage_root_cause_identified",
        "mitigation_defined",
        "mitigation_flown",
        "initial_postflight_outcome_available",
        (
            "initial_postflight_outcome_"
            "supports_mitigation"
        ),
    ]

    for key in required_true:
        require(
            assessment.get(
                key
            )
            is True,
            (
                "closure assessment "
                f"expected TRUE: {key}"
            ),
        )

    require(
        assessment[
            "final_material_analysis_publicly_complete"
        ]
        is False,
        (
            "closure incorrectly claims "
            "final public material analysis"
        ),
    )

    require(
        assessment[
            "closure_level"
        ]
        == (
            "INITIAL_FLIGHT_MITIGATION_"
            "EFFECTIVENESS_SUPPORTED"
        ),
        "closure level mismatch",
    )


def validate_evidence_boundaries(
    closure: dict,
):
    boundaries = (
        closure[
            "evidence_boundaries"
        ]
    )

    expected_false = [
        "artemis_i_char_loss_equals_heat_shield_failure",
        (
            "artemis_i_root_cause_equals_"
            "peak_heat_flux_exceedance"
        ),
        (
            "artemis_ii_no_skip_equals_"
            "no_altitude_rebound"
        ),
        (
            "artemis_ii_profile_difference_"
            "entirely_due_to_tps"
        ),
        (
            "external_heating_model_predicts_"
            "internal_avcoat_temperature"
        ),
        (
            "external_heating_model_predicts_"
            "internal_gas_pressure"
        ),
        (
            "external_heating_model_predicts_"
            "cracking"
        ),
        (
            "external_heating_model_predicts_"
            "char_loss_quantity"
        ),
        (
            "significantly_reduced_equals_"
            "known_reduction_percentage"
        ),
        (
            "initial_postflight_assessment_"
            "equals_final_material_closure"
        ),
    ]

    require(
        set(
            boundaries
        )
        == set(
            expected_false
        ),
        (
            "TPS evidence-boundary "
            "registry mismatch"
        ),
    )

    for key in expected_false:
        require(
            boundaries.get(
                key
            )
            is False,
            (
                "TPS evidence boundary "
                f"expected FALSE: {key}"
            ),
        )


def validate_csv_matches_json(
    csv_rows: list[dict],
    chain: list[dict],
):
    require(
        len(
            csv_rows
        )
        == 7,
        (
            "closure CSV expected "
            f"7 rows, found {len(csv_rows)}"
        ),
    )

    require(
        len(
            chain
        )
        == 7,
        "closure JSON does not have 7 steps",
    )

    for index, (
        csv_row,
        json_row,
    ) in enumerate(
        zip(
            csv_rows,
            chain,
        ),
        start=1,
    ):
        scalar_fields = [
            "step_id",
            "stage",
            "mission_context",
            "title",
            "evidence_class",
            "statement",
            "closure_role",
            "provenance",
        ]

        require(
            int(
                csv_row[
                    "order"
                ]
            )
            == json_row[
                "order"
            ],
            (
                f"CSV row {index} "
                "order mismatch"
            ),
        )

        for field in scalar_fields:
            require(
                csv_row[
                    field
                ]
                == json_row[
                    field
                ],
                (
                    f"CSV row {index} "
                    f"{field} mismatch"
                ),
            )

        csv_evidence_ids = (
            csv_row[
                "evidence_ids"
            ].split(
                "|"
            )
            if csv_row[
                "evidence_ids"
            ]
            else []
        )

        require(
            csv_evidence_ids
            == json_row[
                "evidence_ids"
            ],
            (
                f"CSV row {index} "
                "evidence IDs mismatch"
            ),
        )

        require(
            bool_from_csv(
                csv_row[
                    "root_cause_claim"
                ],
                (
                    f"CSV row {index} "
                    "root_cause_claim"
                ),
            )
            is json_row[
                "root_cause_claim"
            ],
            (
                f"CSV row {index} "
                "root-cause flag mismatch"
            ),
        )

        require(
            bool_from_csv(
                csv_row[
                    "quantitative_damage_claim"
                ],
                (
                    f"CSV row {index} "
                    "quantitative_damage_claim"
                ),
            )
            is json_row[
                "quantitative_damage_claim"
            ],
            (
                f"CSV row {index} "
                "damage-claim flag mismatch"
            ),
        )

        require(
            bool_from_csv(
                csv_row[
                    "final_postflight_closure_claim"
                ],
                (
                    f"CSV row {index} "
                    "final_postflight_closure_claim"
                ),
            )
            is json_row[
                "final_postflight_closure_claim"
            ],
            (
                f"CSV row {index} "
                "final-closure flag mismatch"
            ),
        )


def validate_outputs(
    closure: dict,
):
    outputs = (
        closure[
            "outputs"
        ]
    )

    require(
        normalize_path(
            outputs[
                "closure_json"
            ]
        )
        == (
            "data/processed/thermal/"
            "artemis_tps_risk_closure.json"
        ),
        "closure JSON path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "closure_csv"
            ]
        )
        == (
            "data/processed/thermal/"
            "artemis_tps_risk_closure_steps.csv"
        ),
        "closure CSV path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "closure_figure"
            ]
        )
        == (
            "docs/assets/thermal/"
            "phase3c1_tps_risk_closure.svg"
        ),
        "closure figure path mismatch",
    )


def validate_svg():
    require(
        FIGURE_PATH.exists(),
        (
            "missing Phase 3C.1 "
            f"figure: {FIGURE_PATH}"
        ),
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 3C.1 figure is empty",
    )

    content = (
        FIGURE_PATH.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    require(
        "<svg"
        in content,
        "Phase 3C.1 figure is not SVG",
    )


def main():
    print()
    print(
        "Phase 3C.1 Artemis I -> "
        "Artemis II TPS Heritage-to-Flight "
        "Risk Closure Validation"
    )
    print(
        "=" * 72
    )

    tps_evidence = load_json(
        TPS_EVIDENCE_PATH
    )

    tps_physics = load_json(
        TPS_PHYSICS_PATH
    )

    entry_heritage = load_json(
        ENTRY_HERITAGE_PATH
    )

    closure = load_json(
        CLOSURE_JSON
    )

    csv_rows = load_csv(
        CLOSURE_CSV
    )

    validate_identity(
        tps_evidence,
        tps_physics,
        entry_heritage,
        closure,
    )

    print()
    print(
        "Analysis identity: PASS"
    )

    validate_dependencies(
        tps_evidence,
        tps_physics,
        entry_heritage,
        closure,
    )

    print(
        "Dependency registry: PASS"
    )

    evidence = index_evidence(
        tps_evidence
    )

    validate_phase2_evidence(
        evidence
    )

    print()
    print(
        "Phase 2F.1 TPS evidence set: PASS"
    )
    print(
        "Artemis I anomaly evidence: PASS"
    )
    print(
        "Artemis I root-cause evidence: PASS"
    )
    print(
        "Permeability evidence: PASS"
    )
    print(
        "Ground-replication evidence: PASS"
    )
    print(
        "Thermal-test campaign evidence: PASS"
    )
    print(
        "Artemis II mitigation evidence: PASS"
    )
    print(
        "Artemis II postflight evidence: PASS"
    )

    validate_physics_boundary(
        tps_physics
    )

    print()
    print(
        "TPS quantitative frontier: PASS"
    )
    print(
        "Material-response boundary: PASS"
    )
    print(
        "Forbidden model bridges: PASS"
    )
    print(
        "No Avcoat damage model: PASS"
    )

    heritage_index = (
        index_entry_heritage(
            entry_heritage
        )
    )

    validate_entry_heritage(
        entry_heritage,
        heritage_index,
    )

    print()
    print(
        "Artemis I skip-entry "
        "classification: PASS"
    )
    print(
        "Artemis II no-skip "
        "classification: PASS"
    )
    print(
        "Entry-profile interpretation "
        "guardrails: PASS"
    )

    chain = validate_closure_chain(
        closure,
        evidence,
    )

    print()
    print(
        "Seven-step closure chain: PASS"
    )
    print(
        "Closure ordering: PASS"
    )
    print(
        "Evidence traceability: PASS"
    )
    print(
        "NASA root-cause claim boundary: PASS"
    )
    print(
        "No quantitative damage claims: PASS"
    )
    print(
        "No final material-closure claim: PASS"
    )

    validate_root_cause_summary(
        closure
    )

    print()
    print(
        "Artemis I root-cause "
        "mechanism summary: PASS"
    )

    validate_mitigation_summary(
        closure
    )

    print(
        "Artemis II mitigation "
        "summary: PASS"
    )

    validate_postflight_summary(
        closure
    )

    print(
        "Artemis II initial postflight "
        "summary: PASS"
    )

    validate_closure_assessment(
        closure
    )

    print(
        "Closure-level assessment: PASS"
    )

    validate_evidence_boundaries(
        closure
    )

    print(
        "Evidence-boundary policy: PASS"
    )

    validate_csv_matches_json(
        csv_rows,
        chain,
    )

    print(
        "Closure CSV / JSON "
        "consistency: PASS"
    )

    validate_outputs(
        closure
    )

    validate_svg()

    print(
        "Documentation figure: PASS"
    )

    print()
    print(
        "Validated closure chain:"
    )
    print(
        "  1. Artemis I anomaly: PASS"
    )
    print(
        "  2. Artemis I root cause: PASS"
    )
    print(
        "  3. entry-environment role: PASS"
    )
    print(
        "  4. Artemis II mitigation: PASS"
    )
    print(
        "  5. Artemis II as-flown "
        "configuration: PASS"
    )
    print(
        "  6. initial postflight "
        "outcome: PASS"
    )
    print(
        "  7. evidence closure "
        "boundary: PASS"
    )

    print()
    print(
        "Validated root-cause mechanism:"
    )
    print(
        "  low permeability: TRUE"
    )
    print(
        "  restricted gas escape: TRUE"
    )
    print(
        "  internal pressure buildup: TRUE"
    )
    print(
        "  cracking: TRUE"
    )
    print(
        "  char liberation: TRUE"
    )
    print(
        "  MissionLab numerical "
        "material model: FALSE"
    )

    print()
    print(
        "Validated Artemis II mitigation:"
    )
    print(
        "  existing heat shield retained: TRUE"
    )
    print(
        "  entry environment modified: TRUE"
    )
    print(
        "  Artemis I-style skip entry: FALSE"
    )
    print(
        "  modified no-skip profile "
        "flown: TRUE"
    )

    print()
    print(
        "Validated initial postflight:"
    )
    print(
        "  TPS performed as expected: TRUE"
    )
    print(
        "  unusual TPS conditions "
        "identified initially: FALSE"
    )
    print(
        "  Artemis I-type char loss "
        "reduced: TRUE"
    )
    print(
        "  public numerical reduction "
        "percentage: FALSE"
    )
    print(
        "  arc-jet consistency: TRUE"
    )

    print()
    print(
        "Closure boundary:"
    )
    print(
        "  mitigation effectiveness "
        "supported: TRUE"
    )
    print(
        "  final sample-level material "
        "analysis publicly complete: FALSE"
    )
    print(
        "  external heating model "
        "predicts Avcoat damage: FALSE"
    )
    print(
        "  initial assessment equals "
        "final closure: FALSE"
    )

    print()
    print(
        "PHASE 3C.1 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
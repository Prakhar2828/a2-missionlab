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

HEATING_MODEL_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_convective_heating_model.json"
)

RISK_CLOSURE_PATH = (
    ROOT
    / "data"
    / "processed"
    / "thermal"
    / "artemis_tps_risk_closure.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "thermal"
)

SYNTHESIS_JSON = (
    OUTPUT_DIR
    / "artemis_tps_materials_synthesis.json"
)

SYNTHESIS_CSV = (
    OUTPUT_DIR
    / "artemis_tps_materials_synthesis_stages.csv"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "thermal"
    / "phase3c2_tps_materials_synthesis.svg"
)


EXPECTED_IDS = {
    "tps_evidence": (
        "phase2f1_orion_tps_heritage_evidence"
    ),
    "tps_physics": (
        "phase2f4_artemis_tps_physics_boundary"
    ),
    "heating_model": (
        "phase2e4_sutton_graves_convective_heating"
    ),
    "risk_closure": (
        "phase3c1_artemis_tps_"
        "heritage_to_flight_risk_closure"
    ),
    "phase3c2": (
        "phase3c2_artemis_tps_"
        "materials_engineering_synthesis"
    ),
}


EXPECTED_STAGE_IDS = [
    "orion_heat_shield_architecture",
    "external_entry_environment",
    "ablative_surface_response",
    "pyrolysis_and_gas_generation",
    "permeability_and_gas_transport",
    "internal_pressure_response",
    "cracking_and_char_liberation",
    "trajectory_risk_mitigation",
    "artemis_ii_flight_evidence",
]


EXPECTED_RELATION_IDS = [
    "external_flow_to_heating",
    "heating_to_pyrolysis",
    "gas_generation_to_transport",
    "transport_to_pressure",
    "pressure_to_cracking",
    "environment_to_mitigation",
    "mitigation_to_flight_evidence",
]


REQUIRED_EVIDENCE_IDS = {
    "orion_heat_shield_architecture",
    "avcoat_function",
    "artemis_i_unexpected_char_loss",
    "artemis_i_root_cause_low_permeability",
    "artemis_i_skip_entry_role",
    "permeable_regions_did_not_show_same_behavior",
    "artemis_i_instrumentation",
    "artemis_i_sample_campaign",
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
        "PHASE 3C.2 VALIDATION FAILED: "
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


def index_physics_stages(
    tps_physics: dict,
) -> dict[str, dict]:
    result = {}

    for stage in (
        tps_physics[
            "physics_boundary"
        ][
            "stages"
        ]
    ):
        stage_id = (
            stage[
                "stage_id"
            ]
        )

        require(
            stage_id not in result,
            (
                "duplicate physics stage: "
                f"{stage_id}"
            ),
        )

        result[
            stage_id
        ] = stage

    return result


def index_synthesis_stages(
    synthesis: dict,
) -> dict[str, dict]:
    result = {}

    for stage in synthesis[
        "synthesis_stages"
    ]:
        stage_id = (
            stage[
                "stage_id"
            ]
        )

        require(
            stage_id not in result,
            (
                "duplicate synthesis stage: "
                f"{stage_id}"
            ),
        )

        result[
            stage_id
        ] = stage

    return result


def index_relations(
    synthesis: dict,
) -> dict[str, dict]:
    result = {}

    for relation in synthesis[
        "engineering_relations"
    ]:
        relation_id = (
            relation[
                "relation_id"
            ]
        )

        require(
            relation_id not in result,
            (
                "duplicate engineering "
                f"relation: {relation_id}"
            ),
        )

        result[
            relation_id
        ] = relation

    return result


def validate_identity(
    tps_evidence: dict,
    tps_physics: dict,
    heating_model: dict,
    risk_closure: dict,
    synthesis: dict,
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
        "heating_model": (
            heating_model.get(
                "model_id"
            )
        ),
        "risk_closure": (
            risk_closure.get(
                "dataset_id"
            )
        ),
        "phase3c2": (
            synthesis.get(
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
                f"{key} identity mismatch"
            ),
        )

    require(
        synthesis.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        synthesis.get(
            "heritage_mission"
        )
        == "Artemis I",
        "heritage mission mismatch",
    )

    require(
        synthesis.get(
            "phase"
        )
        == "3C.2",
        "phase identity mismatch",
    )

    require(
        synthesis.get(
            "status"
        )
        == (
            "MATERIALS_ENGINEERING_"
            "SYNTHESIS_COMPLETE"
        ),
        "Phase 3C.2 status mismatch",
    )


def validate_dependencies(
    tps_evidence: dict,
    tps_physics: dict,
    heating_model: dict,
    risk_closure: dict,
    synthesis: dict,
):
    dependencies = (
        synthesis[
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
        "convective_heating_model": (
            heating_model[
                "model_id"
            ]
        ),
        "phase3c1_risk_closure": (
            risk_closure[
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
        risk_closure[
            "closure_assessment"
        ][
            "closure_level"
        ]
        == (
            "INITIAL_FLIGHT_MITIGATION_"
            "EFFECTIVENESS_SUPPORTED"
        ),
        (
            "Phase 3C.1 validated "
            "closure level changed"
        ),
    )


def validate_evidence_set(
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
            "required materials evidence "
            f"missing: {sorted(missing)}"
        ),
    )

    architecture = (
        evidence[
            "orion_heat_shield_architecture"
        ]
    )

    require(
        architecture[
            "key_values"
        ][
            "heat_shield_diameter_ft"
        ]
        == 16.5,
        "Orion heat-shield diameter changed",
    )

    require(
        architecture[
            "key_values"
        ][
            "avcoat_blocks"
        ]
        == 186,
        "Avcoat block count changed",
    )

    instrumentation = (
        evidence[
            "artemis_i_instrumentation"
        ]
    )

    require(
        isinstance(
            instrumentation[
                "instrumentation"
            ],
            list,
        ),
        "instrumentation registry is not a list",
    )

    require(
        {
            "pressure sensors",
            "strain gauges",
            "thermocouples",
        }.issubset(
            set(
                instrumentation[
                    "instrumentation"
                ]
            )
        ),
        (
            "required Artemis I "
            "instrumentation missing"
        ),
    )

    require(
        evidence[
            "artemis_i_sample_campaign"
        ][
            "key_values"
        ][
            "approximate_avcoat_samples"
        ]
        == 200,
        "Avcoat sample count changed",
    )

    require(
        evidence[
            "artemis_i_thermal_test_campaign"
        ][
            "key_values"
        ][
            "thermal_test_campaigns"
        ]
        == 8,
        "thermal-test campaign count changed",
    )

    require(
        evidence[
            "artemis_i_thermal_test_campaign"
        ][
            "key_values"
        ][
            "individual_tests"
        ]
        == 121,
        "individual thermal-test count changed",
    )


def validate_heating_model(
    heating_model: dict,
):
    require(
        heating_model[
            "provenance"
        ]
        == "MODEL_DERIVED",
        "heating-model provenance changed",
    )

    require(
        heating_model[
            "correlation"
        ][
            "name"
        ]
        == (
            "Sutton-Graves stagnation-point "
            "convective heating correlation"
        ),
        "Sutton-Graves identity mismatch",
    )

    limits = (
        heating_model[
            "interpretation_limits"
        ]
    )

    required_limits = [
        (
            "The result is MODEL-DERIVED "
            "and is not measured Artemis II "
            "heat flux."
        ),
        (
            "Avcoat ablation and pyrolysis "
            "are not modeled."
        ),
        (
            "Blowing and surface recession "
            "are not modeled."
        ),
        (
            "Radiative heating is not included."
        ),
        (
            "Finite wall temperature "
            "is not modeled."
        ),
    ]

    for limit in required_limits:
        require(
            limit in limits,
            (
                "missing heating-model "
                f"boundary: {limit}"
            ),
        )


def validate_physics_boundary(
    tps_physics: dict,
    physics_stages: dict[str, dict],
):
    boundary = (
        tps_physics[
            "physics_boundary"
        ]
    )

    require(
        boundary[
            "missionlab_quantitative_frontier_stage_id"
        ]
        == "external_convective_heating",
        (
            "MissionLab quantitative "
            "frontier changed"
        ),
    )

    require(
        boundary[
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

    expected_stage_ids = {
        "trajectory_external_flow",
        "external_convective_heating",
        "surface_internal_thermal_response",
        "pyrolysis_gas_generation",
        "gas_transport_permeability",
        "internal_pressure",
        "cracking_fracture",
        "char_liberation_damage",
    }

    require(
        set(
            physics_stages
        )
        == expected_stage_ids,
        "TPS physics stage set mismatch",
    )

    require(
        physics_stages[
            "trajectory_external_flow"
        ][
            "inside_current_missionlab_quantitative_model"
        ]
        is True,
        "trajectory stage left quantitative model",
    )

    require(
        physics_stages[
            "external_convective_heating"
        ][
            "inside_current_missionlab_quantitative_model"
        ]
        is True,
        (
            "external heating stage "
            "left quantitative model"
        ),
    )

    for stage_id in [
        "surface_internal_thermal_response",
        "pyrolysis_gas_generation",
        "gas_transport_permeability",
        "internal_pressure",
        "cracking_fracture",
        "char_liberation_damage",
    ]:
        require(
            physics_stages[
                stage_id
            ][
                "inside_current_missionlab_quantitative_model"
            ]
            is False,
            (
                f"{stage_id} incorrectly "
                "entered quantitative model"
            ),
        )

    for (
        key,
        value,
    ) in (
        tps_physics[
            "model_assertions"
        ].items()
    ):
        require(
            value is False,
            (
                "forbidden TPS model "
                f"assertion became TRUE: {key}"
            ),
        )


def validate_synthesis_stages(
    synthesis: dict,
    evidence: dict[str, dict],
    physics_stages: dict[str, dict],
):
    stages = (
        synthesis[
            "synthesis_stages"
        ]
    )

    require(
        len(
            stages
        )
        == 9,
        (
            "expected 9 synthesis stages, "
            f"found {len(stages)}"
        ),
    )

    require(
        [
            stage[
                "order"
            ]
            for stage
            in stages
        ]
        == list(
            range(
                1,
                10,
            )
        ),
        "synthesis stage numbering mismatch",
    )

    require(
        [
            stage[
                "stage_id"
            ]
            for stage
            in stages
        ]
        == EXPECTED_STAGE_IDS,
        (
            "synthesis stage IDs or "
            "ordering mismatch"
        ),
    )

    quantitative_stages = []

    for stage in stages:
        require(
            stage[
                "provenance"
            ]
            == (
                "MISSIONLAB_DERIVED_"
                "MATERIALS_ENGINEERING_SYNTHESIS"
            ),
            (
                f"{stage['stage_id']} "
                "provenance mismatch"
            ),
        )

        for evidence_id in (
            stage[
                "evidence_ids"
            ]
        ):
            require(
                evidence_id in evidence,
                (
                    f"{stage['stage_id']} "
                    "references unknown evidence "
                    f"{evidence_id}"
                ),
            )

        for physics_stage_id in (
            stage[
                "physics_stage_ids"
            ]
        ):
            require(
                physics_stage_id
                in physics_stages,
                (
                    f"{stage['stage_id']} "
                    "references unknown physics "
                    f"stage {physics_stage_id}"
                ),
            )

        require(
            isinstance(
                stage[
                    "guardrail"
                ],
                str,
            )
            and stage[
                "guardrail"
            ].strip(),
            (
                f"{stage['stage_id']} "
                "missing engineering guardrail"
            ),
        )

        if (
            stage[
                "can_missionlab_calculate"
            ]
            is True
        ):
            quantitative_stages.append(
                stage[
                    "stage_id"
                ]
            )

    require(
        quantitative_stages
        == [
            "external_entry_environment"
        ],
        (
            "only external entry environment "
            "may be quantitative"
        ),
    )

    indexed = index_synthesis_stages(
        synthesis
    )

    require(
        indexed[
            "ablative_surface_response"
        ][
            "can_missionlab_calculate"
        ]
        is False,
        (
            "MissionLab incorrectly calculates "
            "ablative material response"
        ),
    )

    require(
        indexed[
            "pyrolysis_and_gas_generation"
        ][
            "can_missionlab_calculate"
        ]
        is False,
        (
            "MissionLab incorrectly calculates "
            "pyrolysis"
        ),
    )

    require(
        indexed[
            "permeability_and_gas_transport"
        ][
            "can_missionlab_calculate"
        ]
        is False,
        (
            "MissionLab incorrectly calculates "
            "permeability"
        ),
    )

    require(
        indexed[
            "internal_pressure_response"
        ][
            "can_missionlab_calculate"
        ]
        is False,
        (
            "MissionLab incorrectly calculates "
            "internal Avcoat pressure"
        ),
    )

    require(
        indexed[
            "cracking_and_char_liberation"
        ][
            "can_missionlab_calculate"
        ]
        is False,
        (
            "MissionLab incorrectly predicts "
            "cracking or char liberation"
        ),
    )

    return stages


def validate_relations(
    synthesis: dict,
):
    relations = (
        synthesis[
            "engineering_relations"
        ]
    )

    require(
        len(
            relations
        )
        == 7,
        (
            "expected 7 engineering relations, "
            f"found {len(relations)}"
        ),
    )

    require(
        [
            relation[
                "order"
            ]
            for relation
            in relations
        ]
        == list(
            range(
                1,
                8,
            )
        ),
        "engineering relation numbering mismatch",
    )

    require(
        [
            relation[
                "relation_id"
            ]
            for relation
            in relations
        ]
        == EXPECTED_RELATION_IDS,
        (
            "engineering relation IDs or "
            "ordering mismatch"
        ),
    )

    valid_stage_ids = set(
        EXPECTED_STAGE_IDS
    )

    for relation in relations:
        require(
            relation[
                "from_stage"
            ]
            in valid_stage_ids,
            (
                f"{relation['relation_id']} "
                "has unknown from-stage"
            ),
        )

        require(
            relation[
                "to_stage"
            ]
            in valid_stage_ids,
            (
                f"{relation['relation_id']} "
                "has unknown to-stage"
            ),
        )

        require(
            relation[
                "quantitative_bridge_allowed"
            ]
            is False,
            (
                f"{relation['relation_id']} "
                "incorrectly permits a "
                "quantitative model bridge"
            ),
        )

        require(
            relation[
                "provenance"
            ]
            == (
                "MISSIONLAB_DERIVED_"
                "ENGINEERING_RELATION"
            ),
            (
                f"{relation['relation_id']} "
                "provenance mismatch"
            ),
        )

    indexed = index_relations(
        synthesis
    )

    require(
        indexed[
            "external_flow_to_heating"
        ][
            "causal_statement_allowed"
        ]
        is False,
        (
            "external model-to-material "
            "boundary incorrectly permits "
            "direct causal model claim"
        ),
    )

    for relation_id in [
        "heating_to_pyrolysis",
        "gas_generation_to_transport",
        "transport_to_pressure",
        "pressure_to_cracking",
        "environment_to_mitigation",
        "mitigation_to_flight_evidence",
    ]:
        require(
            indexed[
                relation_id
            ][
                "causal_statement_allowed"
            ]
            is True,
            (
                f"{relation_id} lost its "
                "NASA-supported causal/"
                "engineering relationship"
            ),
        )

    return relations


def validate_architecture_summary(
    synthesis: dict,
):
    summary = (
        synthesis[
            "architecture_summary"
        ]
    )

    require(
        summary[
            "material"
        ]
        == "Avcoat",
        "architecture material mismatch",
    )

    require(
        summary[
            "heat_shield_diameter_ft"
        ]
        == 16.5,
        "architecture diameter mismatch",
    )

    require(
        summary[
            "avcoat_blocks"
        ]
        == 186,
        "architecture block count mismatch",
    )

    require(
        summary[
            "primary_function"
        ]
        == "ABLATIVE_THERMAL_PROTECTION",
        "architecture function mismatch",
    )

    require(
        summary[
            "expected_material_loss_is_normal_ablation"
        ]
        is True,
        (
            "normal ablation boundary "
            "not preserved"
        ),
    )

    require(
        summary[
            "unexpected_char_liberation_is_same_as_normal_ablation"
        ]
        is False,
        (
            "unexpected char liberation "
            "incorrectly equated with "
            "normal ablation"
        ),
    )


def validate_external_model_summary(
    synthesis: dict,
):
    summary = (
        synthesis[
            "external_model_summary"
        ]
    )

    require(
        summary[
            "correlation"
        ]
        == "Sutton-Graves",
        "external correlation mismatch",
    )

    require(
        summary[
            "provenance"
        ]
        == "MODEL_DERIVED",
        "external model provenance mismatch",
    )

    required_false = [
        "measured_artemis_ii_heat_flux",
        "avcoat_ablation_modeled",
        "pyrolysis_modeled",
        "surface_recession_modeled",
        "internal_temperature_modeled",
        "internal_pressure_modeled",
        "fracture_modeled",
        "char_loss_modeled",
    ]

    for key in required_false:
        require(
            summary.get(
                key
            )
            is False,
            (
                "external-model boundary "
                f"expected FALSE: {key}"
            ),
        )


def validate_investigation_summary(
    synthesis: dict,
):
    summary = (
        synthesis[
            "artemis_i_investigation_summary"
        ]
    )

    require(
        {
            "pressure sensors",
            "strain gauges",
            "thermocouples",
        }.issubset(
            set(
                summary[
                    "instrumentation"
                ]
            )
        ),
        "investigation instrumentation mismatch",
    )

    require(
        summary[
            "approximate_avcoat_samples"
        ]
        == 200,
        "investigation sample count mismatch",
    )

    require(
        summary[
            "thermal_test_campaigns"
        ]
        == 8,
        "investigation campaign count mismatch",
    )

    require(
        summary[
            "individual_thermal_tests"
        ]
        == 121,
        "investigation test count mismatch",
    )

    require(
        summary[
            "ground_replication_reported"
        ]
        is True,
        "ground replication missing",
    )

    require(
        summary[
            "missionlab_possesses_raw_instrumentation_series"
        ]
        is False,
        (
            "MissionLab incorrectly claims "
            "raw instrumentation series"
        ),
    )

    require(
        summary[
            "missionlab_reproduces_material_test_campaign"
        ]
        is False,
        (
            "MissionLab incorrectly claims "
            "material test reproduction"
        ),
    )


def validate_material_mechanism(
    synthesis: dict,
):
    summary = (
        synthesis[
            "material_mechanism_summary"
        ]
    )

    expected = [
        "external entry heating",
        "Avcoat thermal response",
        "pyrolysis and gas generation",
        "gas transport through material",
        (
            "restricted venting in "
            "low-permeability regions"
        ),
        "internal gas-pressure buildup",
        "cracking",
        "char liberation",
    ]

    require(
        summary[
            "sequence"
        ]
        == expected,
        "material mechanism sequence mismatch",
    )

    require(
        summary[
            "nasa_reported_mechanism"
        ]
        is True,
        "NASA mechanism flag mismatch",
    )

    require(
        summary[
            "missionlab_quantitative_material_model"
        ]
        is False,
        (
            "MissionLab incorrectly claims "
            "quantitative material model"
        ),
    )


def validate_mitigation_and_flight(
    synthesis: dict,
):
    summary = (
        synthesis[
            "mitigation_and_flight_summary"
        ]
    )

    required_true = [
        "artemis_ii_entry_environment_modified",
        "artemis_ii_modified_no_skip_profile_flown",
        "initial_tps_performance_expected",
        (
            "artemis_i_type_char_loss_"
            "significantly_reduced"
        ),
        "arcjet_consistency_reported",
        (
            "initial_flight_mitigation_"
            "effectiveness_supported"
        ),
    ]

    required_false = [
        (
            "artemis_i_style_skip_entry_"
            "flown_on_artemis_ii"
        ),
        (
            "numerical_char_loss_reduction_"
            "percentage_public"
        ),
        (
            "final_public_sample_level_"
            "material_closure"
        ),
    ]

    for key in required_true:
        require(
            summary.get(
                key
            )
            is True,
            (
                "mitigation/flight summary "
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
                "mitigation/flight summary "
                f"expected FALSE: {key}"
            ),
        )


def validate_engineering_boundaries(
    synthesis: dict,
):
    boundaries = (
        synthesis[
            "engineering_boundaries"
        ]
    )

    expected_false = [
        (
            "expected_ablation_equals_"
            "unexpected_char_liberation"
        ),
        (
            "external_heat_flux_equals_"
            "surface_temperature"
        ),
        (
            "external_heat_flux_equals_"
            "internal_temperature"
        ),
        (
            "external_heat_load_equals_"
            "pyrolysis_rate"
        ),
        (
            "external_dynamic_pressure_equals_"
            "internal_gas_pressure"
        ),
        (
            "external_heat_load_equals_"
            "crack_probability"
        ),
        (
            "external_heating_history_equals_"
            "char_loss_quantity"
        ),
        "no_skip_entry_equals_no_rebound",
        (
            "trajectory_mitigation_equals_"
            "complete_material_model"
        ),
        (
            "significantly_reduced_equals_"
            "known_percentage"
        ),
        (
            "initial_postflight_result_equals_"
            "final_material_closure"
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
            "engineering-boundary "
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
                "engineering boundary "
                f"expected FALSE: {key}"
            ),
        )


def validate_roadmap_coverage(
    synthesis: dict,
):
    assessment = (
        synthesis[
            "roadmap_completion_assessment"
        ]
    )

    required_true = [
        "heat_shield_root_cause_chain_available",
        "artemis_ii_risk_mitigation_chain_available",
        (
            "initial_postflight_closure_"
            "chain_available"
        ),
        (
            "thermal_protection_material_"
            "science_explainer_available"
        ),
    ]

    for key in required_true:
        require(
            assessment.get(
                key
            )
            is True,
            (
                "roadmap coverage "
                f"expected TRUE: {key}"
            ),
        )

    require(
        assessment[
            "internal_material_response_"
            "quantitatively_reconstructed"
        ]
        is False,
        (
            "roadmap assessment incorrectly "
            "claims internal material "
            "quantitative reconstruction"
        ),
    )

    require(
        assessment[
            "materials_explainer_scope"
        ]
        == (
            "NASA_REPORTED_PHYSICS_WITH_"
            "MISSIONLAB_MODEL_BOUNDARIES"
        ),
        "materials explainer scope mismatch",
    )


def validate_csv_matches_json(
    csv_rows: list[dict],
    stages: list[dict],
):
    require(
        len(
            csv_rows
        )
        == 9,
        (
            "synthesis CSV expected "
            f"9 rows, found {len(csv_rows)}"
        ),
    )

    for index, (
        csv_row,
        json_row,
    ) in enumerate(
        zip(
            csv_rows,
            stages,
        ),
        start=1,
    ):
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

        scalar_fields = [
            "stage_id",
            "label",
            "engineering_domain",
            "quantitative_status",
            "missionlab_status",
            "description",
            "engineering_meaning",
            "guardrail",
            "provenance",
        ]

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

        csv_physics_ids = (
            csv_row[
                "physics_stage_ids"
            ].split(
                "|"
            )
            if csv_row[
                "physics_stage_ids"
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
            csv_physics_ids
            == json_row[
                "physics_stage_ids"
            ],
            (
                f"CSV row {index} "
                "physics stage IDs mismatch"
            ),
        )

        for field in [
            "can_missionlab_calculate",
            "nasa_mechanism_preserved",
            "flight_observation",
        ]:
            require(
                bool_from_csv(
                    csv_row[
                        field
                    ],
                    (
                        f"CSV row {index} "
                        f"{field}"
                    ),
                )
                is json_row[
                    field
                ],
                (
                    f"CSV row {index} "
                    f"{field} mismatch"
                ),
            )


def validate_outputs(
    synthesis: dict,
):
    outputs = (
        synthesis[
            "outputs"
        ]
    )

    require(
        normalize_path(
            outputs[
                "synthesis_json"
            ]
        )
        == (
            "data/processed/thermal/"
            "artemis_tps_materials_synthesis.json"
        ),
        "synthesis JSON path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "synthesis_csv"
            ]
        )
        == (
            "data/processed/thermal/"
            "artemis_tps_materials_synthesis_stages.csv"
        ),
        "synthesis CSV path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "synthesis_figure"
            ]
        )
        == (
            "docs/assets/thermal/"
            "phase3c2_tps_materials_synthesis.svg"
        ),
        "synthesis figure path mismatch",
    )


def validate_svg():
    require(
        FIGURE_PATH.exists(),
        (
            "missing Phase 3C.2 "
            f"figure: {FIGURE_PATH}"
        ),
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 3C.2 figure is empty",
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
        "Phase 3C.2 figure is not SVG",
    )


def main():
    print()
    print(
        "Phase 3C.2 Artemis II "
        "Thermal Protection and Materials "
        "Engineering Synthesis Validation"
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

    heating_model = load_json(
        HEATING_MODEL_PATH
    )

    risk_closure = load_json(
        RISK_CLOSURE_PATH
    )

    synthesis = load_json(
        SYNTHESIS_JSON
    )

    csv_rows = load_csv(
        SYNTHESIS_CSV
    )

    validate_identity(
        tps_evidence,
        tps_physics,
        heating_model,
        risk_closure,
        synthesis,
    )

    print()
    print(
        "Analysis identity: PASS"
    )

    validate_dependencies(
        tps_evidence,
        tps_physics,
        heating_model,
        risk_closure,
        synthesis,
    )

    print(
        "Dependency registry: PASS"
    )

    evidence = index_evidence(
        tps_evidence
    )

    validate_evidence_set(
        evidence
    )

    print()
    print(
        "Materials evidence set: PASS"
    )
    print(
        "Orion heat-shield architecture: PASS"
    )
    print(
        "Artemis I instrumentation: PASS"
    )
    print(
        "Artemis I sample campaign: PASS"
    )
    print(
        "Artemis I thermal testing: PASS"
    )

    validate_heating_model(
        heating_model
    )

    print()
    print(
        "Sutton-Graves model identity: PASS"
    )
    print(
        "External-heating interpretation "
        "limits: PASS"
    )

    physics_stages = (
        index_physics_stages(
            tps_physics
        )
    )

    validate_physics_boundary(
        tps_physics,
        physics_stages,
    )

    print()
    print(
        "TPS quantitative frontier: PASS"
    )
    print(
        "Material-response boundary: PASS"
    )
    print(
        "Internal material stages "
        "remain non-quantitative: PASS"
    )
    print(
        "Forbidden material-model "
        "assertions: PASS"
    )

    stages = (
        validate_synthesis_stages(
            synthesis,
            evidence,
            physics_stages,
        )
    )

    print()
    print(
        "Nine-stage materials "
        "synthesis: PASS"
    )
    print(
        "Stage ordering: PASS"
    )
    print(
        "Stage evidence traceability: PASS"
    )
    print(
        "Stage physics traceability: PASS"
    )
    print(
        "Quantitative frontier "
        "enforcement: PASS"
    )

    validate_relations(
        synthesis
    )

    print()
    print(
        "Seven engineering relations: PASS"
    )
    print(
        "Relation topology: PASS"
    )
    print(
        "Unsupported quantitative "
        "bridges prohibited: PASS"
    )
    print(
        "NASA-supported causal "
        "relations preserved: PASS"
    )

    validate_architecture_summary(
        synthesis
    )

    print()
    print(
        "Architecture summary: PASS"
    )

    validate_external_model_summary(
        synthesis
    )

    print(
        "External-model boundary "
        "summary: PASS"
    )

    validate_investigation_summary(
        synthesis
    )

    print(
        "Artemis I investigation "
        "summary: PASS"
    )

    validate_material_mechanism(
        synthesis
    )

    print(
        "Material-mechanism "
        "summary: PASS"
    )

    validate_mitigation_and_flight(
        synthesis
    )

    print(
        "Artemis II mitigation / "
        "flight summary: PASS"
    )

    validate_engineering_boundaries(
        synthesis
    )

    print(
        "Engineering-boundary policy: PASS"
    )

    validate_roadmap_coverage(
        synthesis
    )

    print(
        "Phase 3 roadmap coverage: PASS"
    )

    validate_csv_matches_json(
        csv_rows,
        stages,
    )

    print(
        "Synthesis CSV / JSON "
        "consistency: PASS"
    )

    validate_outputs(
        synthesis
    )

    validate_svg()

    print(
        "Documentation figure: PASS"
    )

    print()
    print(
        "Validated synthesis:"
    )
    print(
        "  synthesis stages: 9"
    )
    print(
        "  engineering relations: 7"
    )
    print(
        "  quantitative internal "
        "material stages: 0"
    )

    print()
    print(
        "Validated quantitative frontier:"
    )
    print(
        "  trajectory / external flow: TRUE"
    )
    print(
        "  external convective heating: TRUE"
    )
    print(
        "  surface temperature: FALSE"
    )
    print(
        "  internal Avcoat temperature: FALSE"
    )
    print(
        "  pyrolysis rate: FALSE"
    )
    print(
        "  permeability field: FALSE"
    )
    print(
        "  internal gas pressure: FALSE"
    )
    print(
        "  cracking / fracture: FALSE"
    )
    print(
        "  char-loss quantity: FALSE"
    )

    print()
    print(
        "Validated investigation context:"
    )
    print(
        "  pressure sensors: PASS"
    )
    print(
        "  strain gauges: PASS"
    )
    print(
        "  thermocouples: PASS"
    )
    print(
        "  approximate Avcoat samples: 200"
    )
    print(
        "  thermal test campaigns: 8"
    )
    print(
        "  individual thermal tests: 121"
    )

    print()
    print(
        "Validated material mechanism:"
    )
    print(
        "  heating -> gas generation: PASS"
    )
    print(
        "  low permeability -> "
        "restricted venting: PASS"
    )
    print(
        "  restricted venting -> "
        "pressure buildup: PASS"
    )
    print(
        "  pressure buildup -> cracking: PASS"
    )
    print(
        "  cracking -> char liberation: PASS"
    )

    print()
    print(
        "Validated Artemis II closure:"
    )
    print(
        "  entry environment modified: TRUE"
    )
    print(
        "  Artemis I-style skip entry: FALSE"
    )
    print(
        "  modified no-skip profile: TRUE"
    )
    print(
        "  initial TPS performance "
        "as expected: TRUE"
    )
    print(
        "  Artemis I-type char loss "
        "significantly reduced: TRUE"
    )
    print(
        "  numerical reduction "
        "percentage public: FALSE"
    )
    print(
        "  final sample-level "
        "material closure: FALSE"
    )

    print()
    print(
        "Roadmap coverage:"
    )
    print(
        "  heat-shield root-cause chain: PASS"
    )
    print(
        "  Artemis II risk mitigation "
        "chain: PASS"
    )
    print(
        "  initial postflight closure "
        "chain: PASS"
    )
    print(
        "  thermal / materials "
        "explainer: PASS"
    )

    print()
    print(
        "PHASE 3C.2 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


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

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "thermal"
)

SYNTHESIS_FIGURE = (
    ASSET_DIR
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
}


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


plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 3C.2 ANALYSIS FAILED: "
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
            f"missing dependency: {path}"
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


def get_evidence(
    evidence: dict[str, dict],
    item_id: str,
) -> dict:
    require(
        item_id in evidence,
        (
            "missing TPS evidence "
            f"item: {item_id}"
        ),
    )

    return evidence[
        item_id
    ]


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
                "duplicate TPS physics "
                f"stage: {stage_id}"
            ),
        )

        result[
            stage_id
        ] = stage

    return result


def validate_dependencies(
    tps_evidence: dict,
    tps_physics: dict,
    heating_model: dict,
    risk_closure: dict,
):
    require(
        tps_evidence.get(
            "dataset_id"
        )
        == EXPECTED_IDS[
            "tps_evidence"
        ],
        "TPS evidence dataset mismatch",
    )

    require(
        tps_physics.get(
            "dataset_id"
        )
        == EXPECTED_IDS[
            "tps_physics"
        ],
        "TPS physics dataset mismatch",
    )

    require(
        heating_model.get(
            "model_id"
        )
        == EXPECTED_IDS[
            "heating_model"
        ],
        "convective-heating model mismatch",
    )

    require(
        risk_closure.get(
            "dataset_id"
        )
        == EXPECTED_IDS[
            "risk_closure"
        ],
        "Phase 3C.1 risk-closure mismatch",
    )

    require(
        risk_closure.get(
            "phase"
        )
        == "3C.1",
        "Phase 3C.1 phase identity mismatch",
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
            "Phase 3C.1 closure level "
            "is not validated"
        ),
    )


def make_stage(
    *,
    order: int,
    stage_id: str,
    label: str,
    engineering_domain: str,
    quantitative_status: str,
    missionlab_status: str,
    evidence_ids: list[str],
    physics_stage_ids: list[str],
    description: str,
    engineering_meaning: str,
    can_missionlab_calculate: bool,
    nasa_mechanism_preserved: bool,
    flight_observation: bool,
    guardrail: str,
) -> dict:
    return {
        "order": (
            order
        ),
        "stage_id": (
            stage_id
        ),
        "label": (
            label
        ),
        "engineering_domain": (
            engineering_domain
        ),
        "quantitative_status": (
            quantitative_status
        ),
        "missionlab_status": (
            missionlab_status
        ),
        "evidence_ids": (
            evidence_ids
        ),
        "physics_stage_ids": (
            physics_stage_ids
        ),
        "description": (
            description
        ),
        "engineering_meaning": (
            engineering_meaning
        ),
        "can_missionlab_calculate": (
            can_missionlab_calculate
        ),
        "nasa_mechanism_preserved": (
            nasa_mechanism_preserved
        ),
        "flight_observation": (
            flight_observation
        ),
        "guardrail": (
            guardrail
        ),
        "provenance": (
            "MISSIONLAB_DERIVED_"
            "MATERIALS_ENGINEERING_SYNTHESIS"
        ),
    }


def build_material_stages(
    evidence: dict[str, dict],
    physics_stages: dict[str, dict],
) -> list[dict]:
    architecture = get_evidence(
        evidence,
        "orion_heat_shield_architecture",
    )

    avcoat = get_evidence(
        evidence,
        "avcoat_function",
    )

    anomaly = get_evidence(
        evidence,
        "artemis_i_unexpected_char_loss",
    )

    root_cause = get_evidence(
        evidence,
        "artemis_i_root_cause_low_permeability",
    )

    skip_role = get_evidence(
        evidence,
        "artemis_i_skip_entry_role",
    )

    permeable_regions = get_evidence(
        evidence,
        "permeable_regions_did_not_show_same_behavior",
    )

    mitigation = get_evidence(
        evidence,
        "artemis_ii_trajectory_mitigation",
    )

    no_skip = get_evidence(
        evidence,
        "artemis_ii_no_skip_entry",
    )

    postflight = get_evidence(
        evidence,
        "artemis_ii_postflight_tps_expected",
    )

    char_reduced = get_evidence(
        evidence,
        "artemis_ii_char_loss_reduced",
    )

    arcjet = get_evidence(
        evidence,
        "artemis_ii_arcjet_consistency",
    )

    required_physics = {
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
        required_physics.issubset(
            set(
                physics_stages
            )
        ),
        (
            "TPS physics stages required "
            "for synthesis are missing"
        ),
    )

    return [
        make_stage(
            order=1,
            stage_id=(
                "orion_heat_shield_architecture"
            ),
            label=(
                "Orion Heat-Shield Architecture"
            ),
            engineering_domain=(
                "THERMAL_PROTECTION_STRUCTURE"
            ),
            quantitative_status=(
                "NASA_REPORTED_ARCHITECTURE"
            ),
            missionlab_status=(
                "REFERENCE_ARCHITECTURE"
            ),
            evidence_ids=[
                architecture[
                    "id"
                ],
            ],
            physics_stage_ids=[],
            description=(
                "Orion's crew-module heat shield "
                "uses Avcoat ablative material "
                "bonded to its supporting "
                "heat-shield structure."
            ),
            engineering_meaning=(
                "The TPS architecture establishes "
                "the physical system that must "
                "absorb, reject, and dissipate the "
                "extreme energy associated with "
                "lunar-return atmospheric entry."
            ),
            can_missionlab_calculate=False,
            nasa_mechanism_preserved=True,
            flight_observation=False,
            guardrail=(
                "Architecture dimensions and "
                "block counts do not constitute "
                "a material-response model."
            ),
        ),
        make_stage(
            order=2,
            stage_id=(
                "external_entry_environment"
            ),
            label=(
                "External Entry Environment"
            ),
            engineering_domain=(
                "AEROTHERMODYNAMICS"
            ),
            quantitative_status=(
                "MISSIONLAB_MODEL_DERIVED"
            ),
            missionlab_status=(
                "QUANTITATIVE"
            ),
            evidence_ids=[],
            physics_stage_ids=[
                "trajectory_external_flow",
                "external_convective_heating",
            ],
            description=(
                "MissionLab reconstructs the "
                "flight-derived entry trajectory "
                "and applies atmospheric and "
                "Sutton-Graves engineering models "
                "to estimate the external "
                "convective-heating environment."
            ),
            engineering_meaning=(
                "Trajectory, atmospheric density, "
                "speed, and effective geometry "
                "define the external aerothermal "
                "boundary condition acting on "
                "the heat shield."
            ),
            can_missionlab_calculate=True,
            nasa_mechanism_preserved=False,
            flight_observation=False,
            guardrail=(
                "Modeled external heat flux is "
                "not measured heat flux and is "
                "not an internal Avcoat state."
            ),
        ),
        make_stage(
            order=3,
            stage_id=(
                "ablative_surface_response"
            ),
            label=(
                "Ablative Surface Response"
            ),
            engineering_domain=(
                "ABLATIVE_MATERIAL_RESPONSE"
            ),
            quantitative_status=(
                "NASA_REPORTED_QUALITATIVE"
            ),
            missionlab_status=(
                "BOUNDARY_NOT_MODELED"
            ),
            evidence_ids=[
                avcoat[
                    "id"
                ],
            ],
            physics_stage_ids=[
                "surface_internal_thermal_response",
            ],
            description=(
                "Avcoat is designed to ablate "
                "in a controlled manner during "
                "entry, carrying thermal energy "
                "away as material responds to "
                "the external heating environment."
            ),
            engineering_meaning=(
                "Expected ablation is a normal "
                "thermal-protection function and "
                "must be distinguished from the "
                "unexpected char-liberation "
                "phenomenon observed on Artemis I."
            ),
            can_missionlab_calculate=False,
            nasa_mechanism_preserved=True,
            flight_observation=False,
            guardrail=(
                "Expected ablation must not be "
                "equated with abnormal char loss, "
                "and MissionLab does not compute "
                "surface temperature or recession."
            ),
        ),
        make_stage(
            order=4,
            stage_id=(
                "pyrolysis_and_gas_generation"
            ),
            label=(
                "Pyrolysis and Gas Generation"
            ),
            engineering_domain=(
                "THERMOCHEMICAL_RESPONSE"
            ),
            quantitative_status=(
                "NASA_REPORTED_MECHANISM"
            ),
            missionlab_status=(
                "KNOWN_NOT_MODELED"
            ),
            evidence_ids=[
                root_cause[
                    "id"
                ],
                skip_role[
                    "id"
                ],
            ],
            physics_stage_ids=[
                "pyrolysis_gas_generation",
            ],
            description=(
                "As Avcoat heats, material "
                "response generates gases within "
                "the ablative material."
            ),
            engineering_meaning=(
                "The internal material state can "
                "continue evolving even when "
                "external heating decreases. "
                "This thermal-history dependence "
                "is central to understanding why "
                "peak heat flux alone cannot "
                "represent the Artemis I issue."
            ),
            can_missionlab_calculate=False,
            nasa_mechanism_preserved=True,
            flight_observation=False,
            guardrail=(
                "MissionLab does not calculate "
                "pyrolysis rate, gas-generation "
                "rate, or stored internal thermal "
                "energy."
            ),
        ),
        make_stage(
            order=5,
            stage_id=(
                "permeability_and_gas_transport"
            ),
            label=(
                "Permeability and Gas Transport"
            ),
            engineering_domain=(
                "POROUS_MATERIAL_TRANSPORT"
            ),
            quantitative_status=(
                "NASA_REPORTED_ROOT_CAUSE_PHYSICS"
            ),
            missionlab_status=(
                "KNOWN_NOT_MODELED"
            ),
            evidence_ids=[
                root_cause[
                    "id"
                ],
                permeable_regions[
                    "id"
                ],
            ],
            physics_stage_ids=[
                "gas_transport_permeability",
            ],
            description=(
                "NASA identified low "
                "permeability as a key condition "
                "that restricted gas escape from "
                "the Artemis I Avcoat."
            ),
            engineering_meaning=(
                "Permeability links material "
                "manufacturing characteristics "
                "to the ability of internally "
                "generated gases to vent through "
                "the porous char and Avcoat "
                "structure."
            ),
            can_missionlab_calculate=False,
            nasa_mechanism_preserved=True,
            flight_observation=False,
            guardrail=(
                "MissionLab has no public "
                "flight permeability field and "
                "does not infer one from external "
                "heating."
            ),
        ),
        make_stage(
            order=6,
            stage_id=(
                "internal_pressure_response"
            ),
            label=(
                "Internal Gas-Pressure Response"
            ),
            engineering_domain=(
                "INTERNAL_MATERIAL_PRESSURE"
            ),
            quantitative_status=(
                "NASA_REPORTED_ROOT_CAUSE_PHYSICS"
            ),
            missionlab_status=(
                "KNOWN_NOT_MODELED"
            ),
            evidence_ids=[
                root_cause[
                    "id"
                ],
            ],
            physics_stage_ids=[
                "internal_pressure",
            ],
            description=(
                "Restricted gas escape in "
                "low-permeability material allowed "
                "internal gas pressure to increase."
            ),
            engineering_meaning=(
                "The relevant pressure is an "
                "internal material-response state, "
                "not the external aerodynamic "
                "dynamic pressure reconstructed "
                "elsewhere in MissionLab."
            ),
            can_missionlab_calculate=False,
            nasa_mechanism_preserved=True,
            flight_observation=False,
            guardrail=(
                "External dynamic pressure and "
                "Sutton-Graves heat flux cannot "
                "be converted directly into "
                "Avcoat pore pressure."
            ),
        ),
        make_stage(
            order=7,
            stage_id=(
                "cracking_and_char_liberation"
            ),
            label=(
                "Cracking and Char Liberation"
            ),
            engineering_domain=(
                "MATERIAL_FAILURE_RESPONSE"
            ),
            quantitative_status=(
                "NASA_REPORTED_CAUSAL_OUTCOME"
            ),
            missionlab_status=(
                "OBSERVED_NOT_PREDICTED"
            ),
            evidence_ids=[
                anomaly[
                    "id"
                ],
                root_cause[
                    "id"
                ],
                permeable_regions[
                    "id"
                ],
            ],
            physics_stage_ids=[
                "cracking_fracture",
                "char_liberation_damage",
            ],
            description=(
                "NASA linked internal pressure "
                "buildup to cracking and the "
                "liberation of charred material "
                "on Artemis I."
            ),
            engineering_meaning=(
                "This is the abnormal material "
                "outcome that the Artemis II "
                "mitigation strategy was intended "
                "to reduce."
            ),
            can_missionlab_calculate=False,
            nasa_mechanism_preserved=True,
            flight_observation=True,
            guardrail=(
                "MissionLab does not calculate "
                "crack initiation, fracture "
                "probability, char-loss area, "
                "or char-loss mass."
            ),
        ),
        make_stage(
            order=8,
            stage_id=(
                "trajectory_risk_mitigation"
            ),
            label=(
                "Trajectory-Based Risk Mitigation"
            ),
            engineering_domain=(
                "ENTRY_GUIDANCE_AND_TPS_RISK"
            ),
            quantitative_status=(
                "NASA_REPORTED_MITIGATION"
            ),
            missionlab_status=(
                "PUBLIC_MITIGATION_PRESERVED"
            ),
            evidence_ids=[
                mitigation[
                    "id"
                ],
                no_skip[
                    "id"
                ],
            ],
            physics_stage_ids=[],
            description=(
                "NASA modified the Artemis II "
                "entry trajectory and flew a "
                "profile without the Artemis I-style "
                "skip entry to minimize conditions "
                "associated with cracking and "
                "char liberation."
            ),
            engineering_meaning=(
                "Risk was mitigated by changing "
                "the thermal-history environment "
                "experienced by the already "
                "integrated heat shield."
            ),
            can_missionlab_calculate=False,
            nasa_mechanism_preserved=True,
            flight_observation=True,
            guardrail=(
                "The public mitigation does not "
                "expose the complete internal "
                "guidance design, and not every "
                "trajectory difference can be "
                "attributed exclusively to TPS."
            ),
        ),
        make_stage(
            order=9,
            stage_id=(
                "artemis_ii_flight_evidence"
            ),
            label=(
                "Artemis II Flight Evidence"
            ),
            engineering_domain=(
                "POSTFLIGHT_TPS_ASSESSMENT"
            ),
            quantitative_status=(
                "NASA_REPORTED_INITIAL_POSTFLIGHT"
            ),
            missionlab_status=(
                "FLIGHT_EVIDENCE_PRESERVED"
            ),
            evidence_ids=[
                postflight[
                    "id"
                ],
                char_reduced[
                    "id"
                ],
                arcjet[
                    "id"
                ],
            ],
            physics_stage_ids=[],
            description=(
                "Initial Artemis II inspection "
                "reported expected TPS performance, "
                "significantly reduced Artemis I-type "
                "char loss, and consistency with "
                "post-Artemis I arc-jet testing."
            ),
            engineering_meaning=(
                "Flight evidence supports the "
                "effectiveness of the mitigation "
                "strategy while preserving the "
                "difference between an initial "
                "postflight result and complete "
                "sample-level material closure."
            ),
            can_missionlab_calculate=False,
            nasa_mechanism_preserved=True,
            flight_observation=True,
            guardrail=(
                "The qualitative phrase "
                "'significantly reduced' cannot "
                "be converted into an invented "
                "percentage or damage map."
            ),
        ),
    ]


def make_relation(
    *,
    order: int,
    relation_id: str,
    from_stage: str,
    to_stage: str,
    relationship: str,
    evidence_status: str,
    quantitative_bridge_allowed: bool,
    causal_statement_allowed: bool,
    explanation: str,
) -> dict:
    return {
        "order": (
            order
        ),
        "relation_id": (
            relation_id
        ),
        "from_stage": (
            from_stage
        ),
        "to_stage": (
            to_stage
        ),
        "relationship": (
            relationship
        ),
        "evidence_status": (
            evidence_status
        ),
        "quantitative_bridge_allowed": (
            quantitative_bridge_allowed
        ),
        "causal_statement_allowed": (
            causal_statement_allowed
        ),
        "explanation": (
            explanation
        ),
        "provenance": (
            "MISSIONLAB_DERIVED_"
            "ENGINEERING_RELATION"
        ),
    }


def build_engineering_relations() -> list[dict]:
    return [
        make_relation(
            order=1,
            relation_id=(
                "external_flow_to_heating"
            ),
            from_stage=(
                "external_entry_environment"
            ),
            to_stage=(
                "ablative_surface_response"
            ),
            relationship=(
                "EXTERNAL_AEROTHERMAL_"
                "BOUNDARY_CONDITION"
            ),
            evidence_status=(
                "MISSIONLAB_MODEL_TO_"
                "MATERIAL_BOUNDARY"
            ),
            quantitative_bridge_allowed=False,
            causal_statement_allowed=False,
            explanation=(
                "MissionLab estimates the "
                "external heating environment "
                "but does not solve the Avcoat "
                "surface or internal temperature "
                "response."
            ),
        ),
        make_relation(
            order=2,
            relation_id=(
                "heating_to_pyrolysis"
            ),
            from_stage=(
                "ablative_surface_response"
            ),
            to_stage=(
                "pyrolysis_and_gas_generation"
            ),
            relationship=(
                "THERMOCHEMICAL_RESPONSE"
            ),
            evidence_status=(
                "NASA_REPORTED_PHYSICS"
            ),
            quantitative_bridge_allowed=False,
            causal_statement_allowed=True,
            explanation=(
                "NASA's material-response "
                "description establishes gas "
                "generation during heating, "
                "but MissionLab lacks the "
                "thermochemical model required "
                "to compute it."
            ),
        ),
        make_relation(
            order=3,
            relation_id=(
                "gas_generation_to_transport"
            ),
            from_stage=(
                "pyrolysis_and_gas_generation"
            ),
            to_stage=(
                "permeability_and_gas_transport"
            ),
            relationship=(
                "INTERNAL_GAS_TRANSPORT"
            ),
            evidence_status=(
                "NASA_REPORTED_ROOT_CAUSE_PHYSICS"
            ),
            quantitative_bridge_allowed=False,
            causal_statement_allowed=True,
            explanation=(
                "Generated gases must escape "
                "through the material. NASA "
                "identified low permeability "
                "as restricting that escape."
            ),
        ),
        make_relation(
            order=4,
            relation_id=(
                "transport_to_pressure"
            ),
            from_stage=(
                "permeability_and_gas_transport"
            ),
            to_stage=(
                "internal_pressure_response"
            ),
            relationship=(
                "RESTRICTED_VENTING_TO_"
                "PRESSURE_BUILDUP"
            ),
            evidence_status=(
                "NASA_REPORTED_ROOT_CAUSE"
            ),
            quantitative_bridge_allowed=False,
            causal_statement_allowed=True,
            explanation=(
                "NASA's Artemis I root-cause "
                "finding links restricted gas "
                "escape in low-permeability "
                "Avcoat to internal pressure "
                "buildup."
            ),
        ),
        make_relation(
            order=5,
            relation_id=(
                "pressure_to_cracking"
            ),
            from_stage=(
                "internal_pressure_response"
            ),
            to_stage=(
                "cracking_and_char_liberation"
            ),
            relationship=(
                "PRESSURE_DRIVEN_"
                "CRACKING_AND_LIBERATION"
            ),
            evidence_status=(
                "NASA_REPORTED_ROOT_CAUSE"
            ),
            quantitative_bridge_allowed=False,
            causal_statement_allowed=True,
            explanation=(
                "NASA identified internal "
                "pressure buildup as leading "
                "to cracking and liberation "
                "of charred material."
            ),
        ),
        make_relation(
            order=6,
            relation_id=(
                "environment_to_mitigation"
            ),
            from_stage=(
                "external_entry_environment"
            ),
            to_stage=(
                "trajectory_risk_mitigation"
            ),
            relationship=(
                "THERMAL_HISTORY_RISK_"
                "MANAGEMENT"
            ),
            evidence_status=(
                "NASA_REPORTED_MITIGATION"
            ),
            quantitative_bridge_allowed=False,
            causal_statement_allowed=True,
            explanation=(
                "NASA changed the Artemis II "
                "entry profile to reduce the "
                "duration of conditions associated "
                "with the Artemis I material "
                "phenomenon."
            ),
        ),
        make_relation(
            order=7,
            relation_id=(
                "mitigation_to_flight_evidence"
            ),
            from_stage=(
                "trajectory_risk_mitigation"
            ),
            to_stage=(
                "artemis_ii_flight_evidence"
            ),
            relationship=(
                "FLIGHT_MITIGATION_OUTCOME"
            ),
            evidence_status=(
                "NASA_REPORTED_FLIGHT_RESULT"
            ),
            quantitative_bridge_allowed=False,
            causal_statement_allowed=True,
            explanation=(
                "NASA's initial postflight "
                "assessment reported expected "
                "TPS performance and significantly "
                "reduced Artemis I-type char loss, "
                "supporting mitigation effectiveness."
            ),
        ),
    ]


def validate_synthesis(
    stages: list[dict],
    relations: list[dict],
):
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
        "synthesis-stage ordering mismatch",
    )

    expected_stage_ids = [
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

    require(
        [
            stage[
                "stage_id"
            ]
            for stage
            in stages
        ]
        == expected_stage_ids,
        "synthesis-stage IDs mismatch",
    )

    quantitative = [
        stage[
            "stage_id"
        ]
        for stage
        in stages
        if stage[
            "can_missionlab_calculate"
        ]
    ]

    require(
        quantitative
        == [
            "external_entry_environment"
        ],
        (
            "only external entry environment "
            "may be quantitative in Phase 3C.2"
        ),
    )

    require(
        len(
            relations
        )
        == 7,
        (
            "expected 7 engineering "
            f"relations, found {len(relations)}"
        ),
    )

    for relation in relations:
        require(
            relation[
                "quantitative_bridge_allowed"
            ]
            is False,
            (
                f"{relation['relation_id']} "
                "incorrectly permits an "
                "unsupported quantitative bridge"
            ),
        )


def write_stage_csv(
    stages: list[dict],
):
    fieldnames = [
        "order",
        "stage_id",
        "label",
        "engineering_domain",
        "quantitative_status",
        "missionlab_status",
        "evidence_ids",
        "physics_stage_ids",
        "description",
        "engineering_meaning",
        "can_missionlab_calculate",
        "nasa_mechanism_preserved",
        "flight_observation",
        "guardrail",
        "provenance",
    ]

    with SYNTHESIS_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for stage in stages:
            row = dict(
                stage
            )

            row[
                "evidence_ids"
            ] = "|".join(
                stage[
                    "evidence_ids"
                ]
            )

            row[
                "physics_stage_ids"
            ] = "|".join(
                stage[
                    "physics_stage_ids"
                ]
            )

            writer.writerow(
                row
            )


def normalize_svg(
    path: Path,
):
    text = path.read_text(
        encoding="utf-8",
    )

    cleaned = "\n".join(
        line.rstrip(
            " \t"
        )
        for line
        in text.splitlines()
    )

    path.write_text(
        cleaned + "\n",
        encoding="utf-8",
    )


def build_figure(
    stages: list[dict],
):
    rows = []

    for stage in stages:
        rows.append(
            [
                str(
                    stage[
                        "order"
                    ]
                ),
                stage[
                    "label"
                ],
                stage[
                    "engineering_domain"
                ].replace(
                    "_",
                    " ",
                ).title(),
                (
                    "YES"
                    if stage[
                        "can_missionlab_calculate"
                    ]
                    else "NO"
                ),
                stage[
                    "missionlab_status"
                ].replace(
                    "_",
                    " ",
                ).title(),
            ]
        )

    fig, ax = plt.subplots(
        figsize=(
            18,
            9,
        )
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        (
            "Artemis II Orion TPS "
            "Materials Engineering Synthesis"
        ),
        fontsize=15,
        pad=18,
    )

    table = ax.table(
        cellText=rows,
        colLabels=[
            "Stage",
            "Material / Physics Layer",
            "Engineering Domain",
            "MissionLab Calculates?",
            "Evidence / Model Status",
        ],
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        7.4
    )

    table.scale(
        1.0,
        1.85,
    )

    ax.text(
        0.5,
        0.032,
        (
            "Quantitative MissionLab modeling "
            "ends at the external entry environment. "
            "Internal Avcoat thermal response, "
            "pyrolysis, permeability, pressure, "
            "fracture, and char loss remain "
            "NASA-reported physics rather than "
            "MissionLab predictions."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        SYNTHESIS_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        SYNTHESIS_FIGURE
    )


def main():
    print()
    print(
        "Phase 3C.2 Artemis II "
        "Thermal Protection and Materials "
        "Engineering Synthesis"
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

    validate_dependencies(
        tps_evidence,
        tps_physics,
        heating_model,
        risk_closure,
    )

    print()
    print(
        "Dependencies:"
    )
    print(
        "  Phase 2F.1 TPS evidence: PASS"
    )
    print(
        "  Phase 2F.4 TPS physics "
        "boundary: PASS"
    )
    print(
        "  Phase 2E.4 convective "
        "heating model: PASS"
    )
    print(
        "  Phase 3C.1 risk closure: PASS"
    )

    evidence = index_evidence(
        tps_evidence
    )

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

    print()
    print(
        "Materials evidence set: PASS"
    )

    physics_stages = (
        index_physics_stages(
            tps_physics
        )
    )

    heating_limits = (
        heating_model[
            "interpretation_limits"
        ]
    )

    required_heating_limits = [
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
    ]

    for limit in required_heating_limits:
        require(
            limit in heating_limits,
            (
                "convective-heating "
                f"boundary missing: {limit}"
            ),
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
        "Sutton-Graves model identity changed",
    )

    print(
        "External-heating model "
        "boundary: PASS"
    )

    stages = build_material_stages(
        evidence,
        physics_stages,
    )

    relations = (
        build_engineering_relations()
    )

    validate_synthesis(
        stages,
        relations,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_stage_csv(
        stages
    )

    build_figure(
        stages
    )

    instrumentation = get_evidence(
        evidence,
        "artemis_i_instrumentation",
    )

    sample_campaign = get_evidence(
        evidence,
        "artemis_i_sample_campaign",
    )

    thermal_tests = get_evidence(
        evidence,
        "artemis_i_thermal_test_campaign",
    )

    output = {
        "dataset_id": (
            "phase3c2_artemis_tps_"
            "materials_engineering_synthesis"
        ),
        "mission": (
            "Artemis II"
        ),
        "heritage_mission": (
            "Artemis I"
        ),
        "phase": (
            "3C.2"
        ),
        "status": (
            "MATERIALS_ENGINEERING_"
            "SYNTHESIS_COMPLETE"
        ),
        "dependencies": {
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
        },
        "synthesis_stages": (
            stages
        ),
        "engineering_relations": (
            relations
        ),
        "architecture_summary": {
            "material": (
                "Avcoat"
            ),
            "heat_shield_diameter_ft": (
                evidence[
                    "orion_heat_shield_architecture"
                ][
                    "key_values"
                ][
                    "heat_shield_diameter_ft"
                ]
            ),
            "avcoat_blocks": (
                evidence[
                    "orion_heat_shield_architecture"
                ][
                    "key_values"
                ][
                    "avcoat_blocks"
                ]
            ),
            "primary_function": (
                "ABLATIVE_THERMAL_PROTECTION"
            ),
            "expected_material_loss_is_normal_ablation": (
                True
            ),
            "unexpected_char_liberation_is_same_as_normal_ablation": (
                False
            ),
        },
        "external_model_summary": {
            "correlation": (
                "Sutton-Graves"
            ),
            "provenance": (
                heating_model[
                    "provenance"
                ]
            ),
            "output": (
                "EXTERNAL_STAGNATION_POINT_"
                "CONVECTIVE_HEAT_FLUX_ESTIMATE"
            ),
            "measured_artemis_ii_heat_flux": (
                False
            ),
            "avcoat_ablation_modeled": (
                False
            ),
            "pyrolysis_modeled": (
                False
            ),
            "surface_recession_modeled": (
                False
            ),
            "internal_temperature_modeled": (
                False
            ),
            "internal_pressure_modeled": (
                False
            ),
            "fracture_modeled": (
                False
            ),
            "char_loss_modeled": (
                False
            ),
        },
        "artemis_i_investigation_summary": {
            "instrumentation": (
                instrumentation[
                    "instrumentation"
                ]
            ),
            "approximate_avcoat_samples": (
                sample_campaign[
                    "key_values"
                ][
                    "approximate_avcoat_samples"
                ]
            ),
            "thermal_test_campaigns": (
                thermal_tests[
                    "key_values"
                ][
                    "thermal_test_campaigns"
                ]
            ),
            "individual_thermal_tests": (
                thermal_tests[
                    "key_values"
                ][
                    "individual_tests"
                ]
            ),
            "ground_replication_reported": (
                True
            ),
            "missionlab_possesses_raw_instrumentation_series": (
                False
            ),
            "missionlab_reproduces_material_test_campaign": (
                False
            ),
        },
        "material_mechanism_summary": {
            "sequence": [
                "external entry heating",
                "Avcoat thermal response",
                "pyrolysis and gas generation",
                "gas transport through material",
                "restricted venting in low-permeability regions",
                "internal gas-pressure buildup",
                "cracking",
                "char liberation",
            ],
            "nasa_reported_mechanism": (
                True
            ),
            "missionlab_quantitative_material_model": (
                False
            ),
        },
        "mitigation_and_flight_summary": {
            "artemis_ii_entry_environment_modified": (
                True
            ),
            "artemis_i_style_skip_entry_flown_on_artemis_ii": (
                False
            ),
            "artemis_ii_modified_no_skip_profile_flown": (
                True
            ),
            "initial_tps_performance_expected": (
                True
            ),
            "artemis_i_type_char_loss_significantly_reduced": (
                True
            ),
            "numerical_char_loss_reduction_percentage_public": (
                False
            ),
            "arcjet_consistency_reported": (
                True
            ),
            "initial_flight_mitigation_effectiveness_supported": (
                True
            ),
            "final_public_sample_level_material_closure": (
                False
            ),
        },
        "engineering_boundaries": {
            "expected_ablation_equals_unexpected_char_liberation": (
                False
            ),
            "external_heat_flux_equals_surface_temperature": (
                False
            ),
            "external_heat_flux_equals_internal_temperature": (
                False
            ),
            "external_heat_load_equals_pyrolysis_rate": (
                False
            ),
            "external_dynamic_pressure_equals_internal_gas_pressure": (
                False
            ),
            "external_heat_load_equals_crack_probability": (
                False
            ),
            "external_heating_history_equals_char_loss_quantity": (
                False
            ),
            "no_skip_entry_equals_no_rebound": (
                False
            ),
            "trajectory_mitigation_equals_complete_material_model": (
                False
            ),
            "significantly_reduced_equals_known_percentage": (
                False
            ),
            "initial_postflight_result_equals_final_material_closure": (
                False
            ),
        },
        "roadmap_completion_assessment": {
            "heat_shield_root_cause_chain_available": (
                True
            ),
            "artemis_ii_risk_mitigation_chain_available": (
                True
            ),
            "initial_postflight_closure_chain_available": (
                True
            ),
            "thermal_protection_material_science_explainer_available": (
                True
            ),
            "internal_material_response_quantitatively_reconstructed": (
                False
            ),
            "materials_explainer_scope": (
                "NASA_REPORTED_PHYSICS_WITH_"
                "MISSIONLAB_MODEL_BOUNDARIES"
            ),
        },
        "outputs": {
            "synthesis_json": str(
                SYNTHESIS_JSON.relative_to(
                    ROOT
                )
            ),
            "synthesis_csv": str(
                SYNTHESIS_CSV.relative_to(
                    ROOT
                )
            ),
            "synthesis_figure": str(
                SYNTHESIS_FIGURE.relative_to(
                    ROOT
                )
            ),
        },
    }

    with SYNTHESIS_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
        )

        f.write(
            "\n"
        )

    print()
    print(
        "Materials synthesis:"
    )
    print(
        f"  stages: {len(stages)}"
    )
    print(
        f"  engineering relations: {len(relations)}"
    )

    print()
    print(
        "MissionLab quantitative frontier:"
    )
    print(
        "  trajectory / external flow: YES"
    )
    print(
        "  external convective heating: YES"
    )
    print(
        "  surface temperature: NO"
    )
    print(
        "  internal Avcoat temperature: NO"
    )
    print(
        "  pyrolysis rate: NO"
    )
    print(
        "  permeability field: NO"
    )
    print(
        "  internal gas pressure: NO"
    )
    print(
        "  cracking / fracture: NO"
    )
    print(
        "  char-loss quantity: NO"
    )

    print()
    print(
        "Artemis I investigation context:"
    )
    print(
        "  pressure sensors: YES"
    )
    print(
        "  strain gauges: YES"
    )
    print(
        "  thermocouples: YES"
    )
    print(
        "  approximate Avcoat samples: "
        + str(
            sample_campaign[
                "key_values"
            ][
                "approximate_avcoat_samples"
            ]
        )
    )
    print(
        "  thermal test campaigns: "
        + str(
            thermal_tests[
                "key_values"
            ][
                "thermal_test_campaigns"
            ]
        )
    )
    print(
        "  individual tests: "
        + str(
            thermal_tests[
                "key_values"
            ][
                "individual_tests"
            ]
        )
    )

    print()
    print(
        "Material mechanism:"
    )
    print(
        "  heating -> gas generation: "
        "NASA-REPORTED"
    )
    print(
        "  low permeability -> "
        "restricted venting: NASA-REPORTED"
    )
    print(
        "  restricted venting -> "
        "pressure buildup: NASA-REPORTED"
    )
    print(
        "  pressure buildup -> cracking: "
        "NASA-REPORTED"
    )
    print(
        "  cracking -> char liberation: "
        "NASA-REPORTED"
    )

    print()
    print(
        "Artemis II mitigation / outcome:"
    )
    print(
        "  entry environment modified: YES"
    )
    print(
        "  Artemis I-style skip entry: NO"
    )
    print(
        "  modified no-skip profile flown: YES"
    )
    print(
        "  initial TPS performance "
        "as expected: YES"
    )
    print(
        "  Artemis I-type char loss "
        "significantly reduced: YES"
    )
    print(
        "  numerical reduction "
        "percentage public: NO"
    )
    print(
        "  arc-jet consistency: YES"
    )

    print()
    print(
        "Engineering boundary:"
    )
    print(
        "  expected ablation "
        "!= unexpected char liberation"
    )
    print(
        "  external heating "
        "!= internal material state"
    )
    print(
        "  external dynamic pressure "
        "!= Avcoat internal gas pressure"
    )
    print(
        "  heating history "
        "!= char-loss predictor"
    )
    print(
        "  trajectory mitigation "
        "!= material-response model"
    )
    print(
        "  initial postflight result "
        "!= final sample-level closure"
    )

    print()
    print(
        "Roadmap coverage:"
    )
    print(
        "  TPS root-cause chain: COMPLETE"
    )
    print(
        "  Artemis II risk mitigation "
        "chain: COMPLETE"
    )
    print(
        "  initial postflight closure "
        "chain: COMPLETE"
    )
    print(
        "  thermal / materials explainer: "
        "COMPLETE"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            SYNTHESIS_JSON.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            SYNTHESIS_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            SYNTHESIS_FIGURE.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 3C.2 MATERIALS "
        "ENGINEERING SYNTHESIS COMPLETE"
    )


if __name__ == "__main__":
    main()
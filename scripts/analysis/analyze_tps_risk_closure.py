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

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "thermal"
)

CLOSURE_FIGURE = (
    ASSET_DIR
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
}


REQUIRED_TPS_EVIDENCE_IDS = {
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
        "PHASE 3C.1 ANALYSIS FAILED: "
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
    evidence: dict,
) -> dict[str, dict]:
    result = {}

    for item in evidence[
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
            "missing required TPS "
            f"evidence item: {item_id}"
        ),
    )

    return evidence[
        item_id
    ]


def validate_dependencies(
    tps_evidence: dict,
    tps_physics: dict,
    entry_heritage: dict,
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
        tps_physics.get(
            "source_evidence_dataset_id"
        )
        == tps_evidence[
            "dataset_id"
        ],
        (
            "TPS physics boundary no longer "
            "references TPS evidence dataset"
        ),
    )


def make_step(
    *,
    order: int,
    step_id: str,
    stage: str,
    mission_context: str,
    title: str,
    evidence_ids: list[str],
    evidence_class: str,
    statement: str,
    closure_role: str,
    root_cause_claim: bool = False,
    quantitative_damage_claim: bool = False,
    final_postflight_closure_claim: bool = False,
) -> dict:
    return {
        "order": (
            order
        ),
        "step_id": (
            step_id
        ),
        "stage": (
            stage
        ),
        "mission_context": (
            mission_context
        ),
        "title": (
            title
        ),
        "evidence_ids": (
            evidence_ids
        ),
        "evidence_class": (
            evidence_class
        ),
        "statement": (
            statement
        ),
        "closure_role": (
            closure_role
        ),
        "root_cause_claim": (
            root_cause_claim
        ),
        "quantitative_damage_claim": (
            quantitative_damage_claim
        ),
        "final_postflight_closure_claim": (
            final_postflight_closure_claim
        ),
        "provenance": (
            "MISSIONLAB_DERIVED_"
            "TPS_RISK_CLOSURE"
        ),
    }


def build_closure_chain(
    evidence: dict[str, dict],
) -> list[dict]:
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

    permeability_evidence = get_evidence(
        evidence,
        "permeable_regions_did_not_show_same_behavior",
    )

    ground_replication = get_evidence(
        evidence,
        "artemis_i_ground_replication",
    )

    thermal_tests = get_evidence(
        evidence,
        "artemis_i_thermal_test_campaign",
    )

    mitigation = get_evidence(
        evidence,
        "artemis_ii_trajectory_mitigation",
    )

    no_skip = get_evidence(
        evidence,
        "artemis_ii_no_skip_entry",
    )

    postflight_expected = get_evidence(
        evidence,
        "artemis_ii_postflight_tps_expected",
    )

    char_reduced = get_evidence(
        evidence,
        "artemis_ii_char_loss_reduced",
    )

    arcjet_consistency = get_evidence(
        evidence,
        "artemis_ii_arcjet_consistency",
    )

    return [
        make_step(
            order=1,
            step_id=(
                "artemis_i_anomaly"
            ),
            stage=(
                "HERITAGE_ANOMALY"
            ),
            mission_context=(
                "Artemis I"
            ),
            title=(
                "Unexpected Artemis I "
                "Avcoat char loss"
            ),
            evidence_ids=[
                anomaly[
                    "id"
                ]
            ],
            evidence_class=(
                "NASA_REPORTED"
            ),
            statement=(
                "Postflight inspection of "
                "Artemis I identified "
                "unexpected char loss across "
                "portions of Orion's Avcoat "
                "heat shield."
            ),
            closure_role=(
                "IDENTIFY_HERITAGE_RISK"
            ),
        ),
        make_step(
            order=2,
            step_id=(
                "artemis_i_root_cause"
            ),
            stage=(
                "ROOT_CAUSE"
            ),
            mission_context=(
                "Artemis I"
            ),
            title=(
                "Low-permeability Avcoat "
                "drives internal pressure "
                "and cracking"
            ),
            evidence_ids=[
                root_cause[
                    "id"
                ],
                permeability_evidence[
                    "id"
                ],
                ground_replication[
                    "id"
                ],
                thermal_tests[
                    "id"
                ],
            ],
            evidence_class=(
                "NASA_REPORTED_"
                "ROOT_CAUSE"
            ),
            statement=(
                "NASA determined that gases "
                "generated within low-permeability "
                "Avcoat could not vent adequately, "
                "allowing internal pressure to "
                "build until cracking and char "
                "liberation occurred. Permeable "
                "regions did not exhibit the same "
                "behavior, and ground testing "
                "reproduced the mechanism."
            ),
            closure_role=(
                "ESTABLISH_CAUSAL_MECHANISM"
            ),
            root_cause_claim=True,
        ),
        make_step(
            order=3,
            step_id=(
                "artemis_i_environment_role"
            ),
            stage=(
                "ENVIRONMENT_INTERACTION"
            ),
            mission_context=(
                "Artemis I"
            ),
            title=(
                "Skip-entry heating history "
                "contributes to gas accumulation"
            ),
            evidence_ids=[
                skip_role[
                    "id"
                ]
            ],
            evidence_class=(
                "NASA_REPORTED"
            ),
            statement=(
                "NASA found that heating "
                "decreased between Artemis I "
                "atmospheric dips while thermal "
                "energy remained within Avcoat. "
                "This condition contributed to "
                "gas accumulation in "
                "low-permeability material."
            ),
            closure_role=(
                "LINK_MATERIAL_MECHANISM_"
                "TO_ENTRY_ENVIRONMENT"
            ),
        ),
        make_step(
            order=4,
            step_id=(
                "artemis_ii_mitigation"
            ),
            stage=(
                "RISK_MITIGATION"
            ),
            mission_context=(
                "Artemis II"
            ),
            title=(
                "Entry environment modified "
                "for Artemis II"
            ),
            evidence_ids=[
                mitigation[
                    "id"
                ],
                no_skip[
                    "id"
                ],
            ],
            evidence_class=(
                "NASA_REPORTED_"
                "MITIGATION"
            ),
            statement=(
                "NASA retained the already "
                "integrated Artemis II heat "
                "shield and changed the entry "
                "environment. Technical reporting "
                "states Artemis II flew a "
                "modified trajectory without the "
                "Artemis I-style skip entry to "
                "minimize crack-inducing conditions."
            ),
            closure_role=(
                "MITIGATE_KNOWN_MECHANISM"
            ),
        ),
        make_step(
            order=5,
            step_id=(
                "artemis_ii_as_flown"
            ),
            stage=(
                "AS_FLOWN_CONFIGURATION"
            ),
            mission_context=(
                "Artemis II"
            ),
            title=(
                "Modified no-skip entry "
                "flown on Artemis II"
            ),
            evidence_ids=[
                no_skip[
                    "id"
                ]
            ],
            evidence_class=(
                "NASA_REPORTED_"
                "AS_FLOWN"
            ),
            statement=(
                "NASA technical reporting "
                "states that Artemis II "
                "actually flew the modified "
                "trajectory without the "
                "Artemis I skip entry."
            ),
            closure_role=(
                "CONFIRM_MITIGATION_EXECUTED"
            ),
        ),
        make_step(
            order=6,
            step_id=(
                "artemis_ii_initial_postflight"
            ),
            stage=(
                "POSTFLIGHT_OUTCOME"
            ),
            mission_context=(
                "Artemis II"
            ),
            title=(
                "Initial TPS inspection "
                "finds expected performance"
            ),
            evidence_ids=[
                postflight_expected[
                    "id"
                ],
                char_reduced[
                    "id"
                ],
                arcjet_consistency[
                    "id"
                ],
            ],
            evidence_class=(
                "NASA_REPORTED_"
                "INITIAL_POSTFLIGHT"
            ),
            statement=(
                "NASA's initial Artemis II "
                "inspection found the thermal "
                "protection system performed "
                "as expected with no unusual "
                "conditions identified. "
                "Artemis I-type char loss was "
                "reported as significantly "
                "reduced in quantity and size, "
                "and performance was consistent "
                "with post-Artemis I arc-jet "
                "ground testing."
            ),
            closure_role=(
                "ASSESS_FLIGHT_MITIGATION_"
                "OUTCOME"
            ),
        ),
        make_step(
            order=7,
            step_id=(
                "closure_boundary"
            ),
            stage=(
                "EVIDENCE_BOUNDARY"
            ),
            mission_context=(
                "Artemis II Postflight"
            ),
            title=(
                "Mitigation effectiveness "
                "supported without claiming "
                "final material closure"
            ),
            evidence_ids=[
                postflight_expected[
                    "id"
                ],
                char_reduced[
                    "id"
                ],
                arcjet_consistency[
                    "id"
                ],
            ],
            evidence_class=(
                "MISSIONLAB_DERIVED_"
                "EVIDENCE_BOUNDARY"
            ),
            statement=(
                "The public postflight record "
                "supports the conclusion that "
                "the Artemis II mitigation "
                "reduced the Artemis I-type "
                "char-loss phenomenon. It does "
                "not provide a complete public "
                "sample-level material dataset "
                "or justify declaring all "
                "postflight material analysis "
                "finished."
            ),
            closure_role=(
                "DEFINE_CLOSURE_LEVEL"
            ),
        ),
    ]


def validate_chain(
    chain: list[dict],
):
    require(
        len(
            chain
        )
        == 7,
        (
            "expected 7 TPS closure "
            f"steps, found {len(chain)}"
        ),
    )

    require(
        [
            item[
                "order"
            ]
            for item
            in chain
        ]
        == list(
            range(
                1,
                8,
            )
        ),
        "TPS closure order mismatch",
    )

    expected_ids = [
        "artemis_i_anomaly",
        "artemis_i_root_cause",
        "artemis_i_environment_role",
        "artemis_ii_mitigation",
        "artemis_ii_as_flown",
        "artemis_ii_initial_postflight",
        "closure_boundary",
    ]

    require(
        [
            item[
                "step_id"
            ]
            for item
            in chain
        ]
        == expected_ids,
        "TPS closure step IDs mismatch",
    )

    for item in chain:
        require(
            item[
                "quantitative_damage_claim"
            ]
            is False,
            (
                f"{item['step_id']} makes "
                "quantitative damage claim"
            ),
        )

        require(
            item[
                "final_postflight_closure_claim"
            ]
            is False,
            (
                f"{item['step_id']} claims "
                "final postflight closure"
            ),
        )

    root_cause_steps = [
        item
        for item
        in chain
        if item[
            "root_cause_claim"
        ]
    ]

    require(
        len(
            root_cause_steps
        )
        == 1,
        (
            "expected exactly one "
            "root-cause step"
        ),
    )

    require(
        root_cause_steps[
            0
        ][
            "step_id"
        ]
        == "artemis_i_root_cause",
        (
            "root-cause claim must remain "
            "limited to Artemis I "
            "NASA-reported finding"
        ),
    )


def write_csv(
    chain: list[dict],
):
    fieldnames = [
        "order",
        "step_id",
        "stage",
        "mission_context",
        "title",
        "evidence_ids",
        "evidence_class",
        "statement",
        "closure_role",
        "root_cause_claim",
        "quantitative_damage_claim",
        "final_postflight_closure_claim",
        "provenance",
    ]

    with CLOSURE_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for item in chain:
            row = dict(
                item
            )

            row[
                "evidence_ids"
            ] = "|".join(
                item[
                    "evidence_ids"
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
    chain: list[dict],
):
    rows = []

    for item in chain:
        rows.append(
            [
                str(
                    item[
                        "order"
                    ]
                ),
                item[
                    "mission_context"
                ],
                item[
                    "stage"
                ].replace(
                    "_",
                    " ",
                ).title(),
                item[
                    "title"
                ],
            ]
        )

    fig, ax = plt.subplots(
        figsize=(
            18,
            8,
        )
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        (
            "Artemis I → Artemis II "
            "Thermal Protection Risk Closure"
        ),
        fontsize=15,
        pad=18,
    )

    table = ax.table(
        cellText=rows,
        colLabels=[
            "Step",
            "Mission Context",
            "Closure Stage",
            "Evidence-backed Result",
        ],
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        7.5
    )

    table.scale(
        1.0,
        1.85,
    )

    ax.text(
        0.5,
        0.035,
        (
            "NASA-reported material mechanism "
            "and postflight observations are "
            "preserved. MissionLab does not "
            "predict Avcoat internal pressure, "
            "cracking, or char-loss quantity."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        CLOSURE_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        CLOSURE_FIGURE
    )


def main():
    print()
    print(
        "Phase 3C.1 Artemis I -> "
        "Artemis II TPS Heritage-to-Flight "
        "Risk Closure"
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

    validate_dependencies(
        tps_evidence,
        tps_physics,
        entry_heritage,
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
        "  Phase 2F.2 entry heritage: PASS"
    )

    evidence = index_evidence(
        tps_evidence
    )

    missing = (
        REQUIRED_TPS_EVIDENCE_IDS
        - set(
            evidence
        )
    )

    require(
        not missing,
        (
            "missing required TPS "
            f"evidence: {sorted(missing)}"
        ),
    )

    print()
    print(
        "Required TPS evidence set: PASS"
    )

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
            "MissionLab TPS quantitative "
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
            "MissionLab material-response "
            "boundary changed"
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
                "Phase 2F physics boundary "
                f"changed: {key}"
            ),
        )

    print(
        "TPS quantitative-model "
        "boundary: PASS"
    )

    heritage_items = {
        item[
            "id"
        ]: item
        for item
        in entry_heritage[
            "evidence_items"
        ]
    }

    require(
        (
            "artemis_ii_no_skip_entry"
            in heritage_items
        ),
        (
            "entry heritage missing "
            "Artemis II no-skip evidence"
        ),
    )

    require(
        heritage_items[
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
            "Artemis II authoritative "
            "entry classification changed"
        ),
    )

    print(
        "Artemis II no-skip "
        "classification: PASS"
    )

    chain = build_closure_chain(
        evidence
    )

    validate_chain(
        chain
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_csv(
        chain
    )

    build_figure(
        chain
    )

    output = {
        "dataset_id": (
            "phase3c1_artemis_tps_"
            "heritage_to_flight_risk_closure"
        ),
        "mission": (
            "Artemis II"
        ),
        "heritage_mission": (
            "Artemis I"
        ),
        "phase": (
            "3C.1"
        ),
        "status": (
            "INITIAL_FLIGHT_MITIGATION_"
            "CLOSURE_SUPPORTED"
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
            "entry_profile_heritage": (
                entry_heritage[
                    "dataset_id"
                ]
            ),
        },
        "closure_chain": (
            chain
        ),
        "root_cause_summary": {
            "heritage_mission": (
                "Artemis I"
            ),
            "material": (
                "Avcoat"
            ),
            "low_permeability_central": (
                True
            ),
            "restricted_gas_escape": (
                True
            ),
            "internal_pressure_buildup": (
                True
            ),
            "cracking": (
                True
            ),
            "char_liberation": (
                True
            ),
            "root_cause_source": (
                "NASA_REPORTED"
            ),
            "missionlab_numerically_models_mechanism": (
                False
            ),
        },
        "mitigation_summary": {
            "target_mission": (
                "Artemis II"
            ),
            "existing_heat_shield_retained": (
                True
            ),
            "entry_environment_modified": (
                True
            ),
            "artemis_i_style_skip_entry_used": (
                False
            ),
            "modified_no_skip_trajectory_flown": (
                True
            ),
            "mitigation_source": (
                "NASA_REPORTED"
            ),
            "full_internal_guidance_design_public": (
                False
            ),
        },
        "postflight_summary": {
            "initial_tps_performance_expected": (
                True
            ),
            "unusual_tps_conditions_identified_initially": (
                False
            ),
            "artemis_i_type_char_loss_reduced": (
                True
            ),
            "char_loss_reduction_quantified_publicly": (
                False
            ),
            "consistent_with_post_artemis_i_arcjet_testing": (
                True
            ),
            "initial_postflight_supports_mitigation_effectiveness": (
                True
            ),
            "complete_public_material_dataset_available": (
                False
            ),
            "final_sample_level_postflight_closure_claimed": (
                False
            ),
        },
        "closure_assessment": {
            "heritage_anomaly_identified": (
                True
            ),
            "heritage_root_cause_identified": (
                True
            ),
            "mitigation_defined": (
                True
            ),
            "mitigation_flown": (
                True
            ),
            "initial_postflight_outcome_available": (
                True
            ),
            "initial_postflight_outcome_supports_mitigation": (
                True
            ),
            "final_material_analysis_publicly_complete": (
                False
            ),
            "closure_level": (
                "INITIAL_FLIGHT_MITIGATION_"
                "EFFECTIVENESS_SUPPORTED"
            ),
        },
        "evidence_boundaries": {
            "artemis_i_char_loss_equals_heat_shield_failure": (
                False
            ),
            "artemis_i_root_cause_equals_peak_heat_flux_exceedance": (
                False
            ),
            "artemis_ii_no_skip_equals_no_altitude_rebound": (
                False
            ),
            "artemis_ii_profile_difference_entirely_due_to_tps": (
                False
            ),
            "external_heating_model_predicts_internal_avcoat_temperature": (
                False
            ),
            "external_heating_model_predicts_internal_gas_pressure": (
                False
            ),
            "external_heating_model_predicts_cracking": (
                False
            ),
            "external_heating_model_predicts_char_loss_quantity": (
                False
            ),
            "significantly_reduced_equals_known_reduction_percentage": (
                False
            ),
            "initial_postflight_assessment_equals_final_material_closure": (
                False
            ),
        },
        "outputs": {
            "closure_json": str(
                CLOSURE_JSON.relative_to(
                    ROOT
                )
            ),
            "closure_csv": str(
                CLOSURE_CSV.relative_to(
                    ROOT
                )
            ),
            "closure_figure": str(
                CLOSURE_FIGURE.relative_to(
                    ROOT
                )
            ),
        },
    }

    with CLOSURE_JSON.open(
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
        "Closure chain:"
    )
    print(
        "  steps: 7"
    )
    print(
        "  Artemis I anomaly: "
        "PRESERVED"
    )
    print(
        "  Artemis I root cause: "
        "PRESERVED"
    )
    print(
        "  entry-environment role: "
        "PRESERVED"
    )
    print(
        "  Artemis II mitigation: "
        "PRESERVED"
    )
    print(
        "  Artemis II mitigation flown: "
        "YES"
    )
    print(
        "  initial postflight outcome: "
        "AVAILABLE"
    )

    print()
    print(
        "Artemis I root-cause mechanism:"
    )
    print(
        "  low permeability: YES"
    )
    print(
        "  restricted gas escape: YES"
    )
    print(
        "  internal pressure buildup: YES"
    )
    print(
        "  cracking: YES"
    )
    print(
        "  char liberation: YES"
    )
    print(
        "  MissionLab numerical "
        "material-response model: NO"
    )

    print()
    print(
        "Artemis II mitigation:"
    )
    print(
        "  entry environment modified: YES"
    )
    print(
        "  Artemis I-style skip entry: NO"
    )
    print(
        "  modified no-skip trajectory "
        "flown: YES"
    )

    print()
    print(
        "Artemis II initial postflight:"
    )
    print(
        "  TPS performed as expected: YES"
    )
    print(
        "  unusual TPS condition "
        "identified initially: NO"
    )
    print(
        "  Artemis I-type char loss "
        "reduced: YES"
    )
    print(
        "  numerical reduction "
        "percentage public: NO"
    )
    print(
        "  consistent with post-Artemis I "
        "arc-jet testing: YES"
    )

    print()
    print(
        "Closure level:"
    )
    print(
        "  INITIAL FLIGHT MITIGATION "
        "EFFECTIVENESS SUPPORTED"
    )
    print(
        "  final public sample-level "
        "material closure: NO"
    )

    print()
    print(
        "Evidence boundary:"
    )
    print(
        "  char loss != heat-shield failure"
    )
    print(
        "  root cause != simple peak "
        "heat-flux exceedance"
    )
    print(
        "  no-skip != no altitude rebound"
    )
    print(
        "  external heating model "
        "!= Avcoat damage model"
    )
    print(
        "  significantly reduced "
        "!= known reduction percentage"
    )
    print(
        "  initial postflight assessment "
        "!= final material closure"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            CLOSURE_JSON.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            CLOSURE_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            CLOSURE_FIGURE.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 3C.1 TPS RISK "
        "CLOSURE COMPLETE"
    )


if __name__ == "__main__":
    main()
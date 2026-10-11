from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]

EVIDENCE_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_tps_evidence.json"
)


EXPECTED_DATASET_ID = (
    "phase2f1_orion_tps_heritage_evidence"
)

EXPECTED_MISSION = "Artemis II"
EXPECTED_PROVENANCE = "NASA_REPORTED"

EXPECTED_EVIDENCE_COUNT = 17
EXPECTED_STAGE_COUNT = 7

ALLOWED_SOURCE_HOSTS = {
    "www.nasa.gov",
    "nasa.gov",
    "ntrs.nasa.gov",
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
    "artemis_ii_entry_velocity_prediction",
    "artemis_iii_permeability_manufacturing_change",
}

EXPECTED_STAGE_ORDER = [
    "DETECTION",
    "EVIDENCE_COLLECTION",
    "ROOT_CAUSE",
    "CONSTRAINT",
    "DECISION_AND_ACTION",
    "FLIGHT_OUTCOME",
    "LONG_TERM_CORRECTIVE_ACTION",
]

REQUIRED_CATEGORIES = {
    "TPS_ARCHITECTURE",
    "TPS_FUNCTION",
    "ARTEMIS_I_ANOMALY",
    "ROOT_CAUSE",
    "ENTRY_ENVIRONMENT",
    "ROOT_CAUSE_EVIDENCE",
    "INVESTIGATION_EVIDENCE",
    "ARTEMIS_II_MITIGATION",
    "ARTEMIS_II_POSTFLIGHT",
    "FUTURE_CORRECTIVE_ACTION",
}

REQUIRED_PROHIBITED_INFERENCES = {
    (
        "predict Artemis II char-loss quantity "
        "from Sutton-Graves heat flux alone"
    ),
    (
        "predict Avcoat recession depth without "
        "a material-response model"
    ),
    (
        "predict internal heat-shield temperature "
        "without TPS thermal-response data"
    ),
    (
        "treat Artemis II reduced char loss as "
        "numerical validation of the MissionLab "
        "heating model"
    ),
    (
        "invent quantitative permeability limits "
        "not published by NASA"
    ),
    (
        "calibrate the Sutton-Graves model to "
        "Artemis I or Artemis II char-loss observations"
    ),
}


def fail(message: str) -> None:
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def require_nonempty_string(
    value,
    label: str,
) -> None:
    if not isinstance(
        value,
        str,
    ):
        fail(
            f"{label} must be a string"
        )

    if not value.strip():
        fail(
            f"{label} must not be empty"
        )


def validate_date(
    value,
    evidence_id: str,
) -> None:
    if value is None:
        return

    if not isinstance(
        value,
        str,
    ):
        fail(
            f"{evidence_id}: "
            "source_date must be null, "
            "YYYY, or YYYY-MM-DD"
        )

    if (
        len(value) == 4
        and value.isdigit()
    ):
        year = int(
            value
        )

        if not (
            1900
            <= year
            <= 2100
        ):
            fail(
                f"{evidence_id}: "
                f"invalid source year "
                f"{value!r}"
            )

        return

    try:
        date.fromisoformat(
            value
        )
    except ValueError:
        fail(
            f"{evidence_id}: "
            "source_date must be null, "
            "YYYY, or YYYY-MM-DD; "
            f"found {value!r}"
        )


def validate_source_url(
    value,
    evidence_id: str,
) -> str:
    require_nonempty_string(
        value,
        f"{evidence_id}.source_url",
    )

    parsed = urlparse(
        value
    )

    if parsed.scheme != "https":
        fail(
            f"{evidence_id}: "
            "source URL must use HTTPS"
        )

    hostname = (
        parsed.hostname
        or ""
    ).lower()

    if hostname not in (
        ALLOWED_SOURCE_HOSTS
    ):
        fail(
            f"{evidence_id}: "
            f"unexpected source host "
            f"{hostname!r}"
        )

    return hostname


def validate_evidence_item(
    item,
    index: int,
) -> None:
    if not isinstance(
        item,
        dict,
    ):
        fail(
            f"evidence item {index} "
            "must be an object"
        )

    evidence_id = item.get(
        "id"
    )

    require_nonempty_string(
        evidence_id,
        f"evidence_items[{index}].id",
    )

    for field in [
        "category",
        "mission_context",
        "claim",
        "provenance",
        "source_title",
        "source_url",
        "source_organization",
        "interpretation",
    ]:
        if field not in item:
            fail(
                f"{evidence_id}: "
                f"missing required field "
                f"{field!r}"
            )

        require_nonempty_string(
            item[field],
            f"{evidence_id}.{field}",
        )

    if (
        item[
            "provenance"
        ]
        != EXPECTED_PROVENANCE
    ):
        fail(
            f"{evidence_id}: "
            "unexpected provenance "
            f"{item['provenance']!r}"
        )

    validate_source_url(
        item[
            "source_url"
        ],
        evidence_id,
    )

    validate_date(
        item.get(
            "source_date"
        ),
        evidence_id,
    )

    limitations = item.get(
        "limitations"
    )

    if not isinstance(
        limitations,
        list,
    ):
        fail(
            f"{evidence_id}: "
            "limitations must be a list"
        )

    if not limitations:
        fail(
            f"{evidence_id}: "
            "at least one limitation "
            "must be recorded"
        )

    for (
        limitation_index,
        limitation,
    ) in enumerate(
        limitations
    ):
        require_nonempty_string(
            limitation,
            (
                f"{evidence_id}."
                f"limitations["
                f"{limitation_index}]"
            ),
        )


def main() -> None:
    if not EVIDENCE_JSON.exists():
        fail(
            "missing TPS evidence file: "
            f"{EVIDENCE_JSON}"
        )

    try:
        with EVIDENCE_JSON.open(
            "r",
            encoding="utf-8-sig",
        ) as f:
            dataset = json.load(
                f
            )
    except json.JSONDecodeError as exc:
        fail(
            "invalid JSON: "
            f"{exc}"
        )

    if not isinstance(
        dataset,
        dict,
    ):
        fail(
            "top-level JSON must be "
            "an object"
        )

    if (
        dataset.get(
            "dataset_id"
        )
        != EXPECTED_DATASET_ID
    ):
        fail(
            "unexpected dataset_id"
        )

    if (
        dataset.get(
            "mission"
        )
        != EXPECTED_MISSION
    ):
        fail(
            "unexpected mission"
        )

    if (
        dataset.get(
            "provenance"
        )
        != EXPECTED_PROVENANCE
    ):
        fail(
            "unexpected top-level "
            "provenance"
        )

    require_nonempty_string(
        dataset.get(
            "scope"
        ),
        "scope",
    )

    evidence_items = dataset.get(
        "evidence_items"
    )

    if not isinstance(
        evidence_items,
        list,
    ):
        fail(
            "evidence_items must "
            "be a list"
        )

    if (
        len(
            evidence_items
        )
        != EXPECTED_EVIDENCE_COUNT
    ):
        fail(
            "expected "
            f"{EXPECTED_EVIDENCE_COUNT} "
            "evidence items, found "
            f"{len(evidence_items)}"
        )

    ids = []

    source_hosts = set()
    categories = set()
    source_urls = set()

    for index, item in enumerate(
        evidence_items
    ):
        validate_evidence_item(
            item,
            index,
        )

        evidence_id = item[
            "id"
        ]

        ids.append(
            evidence_id
        )

        categories.add(
            item[
                "category"
            ]
        )

        source_urls.add(
            item[
                "source_url"
            ]
        )

        hostname = urlparse(
            item[
                "source_url"
            ]
        ).hostname

        if hostname:
            source_hosts.add(
                hostname.lower()
            )

    if (
        len(ids)
        != len(set(ids))
    ):
        fail(
            "duplicate evidence IDs "
            "detected"
        )

    actual_ids = set(
        ids
    )

    if (
        actual_ids
        != REQUIRED_EVIDENCE_IDS
    ):
        missing = sorted(
            REQUIRED_EVIDENCE_IDS
            - actual_ids
        )

        unexpected = sorted(
            actual_ids
            - REQUIRED_EVIDENCE_IDS
        )

        fail(
            "evidence ID inventory "
            "does not match expected set. "
            f"missing={missing}, "
            f"unexpected={unexpected}"
        )

    if not (
        REQUIRED_CATEGORIES
        <= categories
    ):
        missing_categories = sorted(
            REQUIRED_CATEGORIES
            - categories
        )

        fail(
            "missing required evidence "
            "categories: "
            f"{missing_categories}"
        )

    decision_thread = dataset.get(
        "decision_thread"
    )

    if not isinstance(
        decision_thread,
        dict,
    ):
        fail(
            "decision_thread must "
            "be an object"
        )

    require_nonempty_string(
        decision_thread.get(
            "thread_id"
        ),
        "decision_thread.thread_id",
    )

    require_nonempty_string(
        decision_thread.get(
            "title"
        ),
        "decision_thread.title",
    )

    stages = decision_thread.get(
        "stages"
    )

    if not isinstance(
        stages,
        list,
    ):
        fail(
            "decision_thread.stages "
            "must be a list"
        )

    if (
        len(stages)
        != EXPECTED_STAGE_COUNT
    ):
        fail(
            "expected "
            f"{EXPECTED_STAGE_COUNT} "
            "decision stages, found "
            f"{len(stages)}"
        )

    observed_stage_order = []

    referenced_ids = set()

    for index, stage in enumerate(
        stages
    ):
        if not isinstance(
            stage,
            dict,
        ):
            fail(
                f"decision stage {index} "
                "must be an object"
            )

        stage_name = stage.get(
            "stage"
        )

        require_nonempty_string(
            stage_name,
            f"stage[{index}].stage",
        )

        observed_stage_order.append(
            stage_name
        )

        require_nonempty_string(
            stage.get(
                "summary"
            ),
            f"stage[{index}].summary",
        )

        evidence_ids = stage.get(
            "evidence_ids"
        )

        if not isinstance(
            evidence_ids,
            list,
        ):
            fail(
                f"{stage_name}: "
                "evidence_ids must "
                "be a list"
            )

        if not evidence_ids:
            fail(
                f"{stage_name}: "
                "must reference at least "
                "one evidence item"
            )

        if (
            len(
                evidence_ids
            )
            != len(
                set(
                    evidence_ids
                )
            )
        ):
            fail(
                f"{stage_name}: "
                "duplicate evidence "
                "reference detected"
            )

        for evidence_id in (
            evidence_ids
        ):
            if (
                evidence_id
                not in actual_ids
            ):
                fail(
                    f"{stage_name}: "
                    "dangling evidence "
                    f"reference "
                    f"{evidence_id!r}"
                )

            referenced_ids.add(
                evidence_id
            )

    if (
        observed_stage_order
        != EXPECTED_STAGE_ORDER
    ):
        fail(
            "decision-thread stage order "
            "does not match expected "
            "engineering sequence"
        )

    required_thread_ids = (
        REQUIRED_EVIDENCE_IDS
        - {
            "orion_heat_shield_architecture",
            "avcoat_function",
        }
    )

    missing_thread_references = sorted(
        required_thread_ids
        - referenced_ids
    )

    if missing_thread_references:
        fail(
            "decision thread fails to "
            "reference expected evidence: "
            f"{missing_thread_references}"
        )

    missionlab = dataset.get(
        "missionlab_interpretation"
    )

    if not isinstance(
        missionlab,
        dict,
    ):
        fail(
            "missionlab_interpretation "
            "must be an object"
        )

    relationship = missionlab.get(
        "relationship_to_phase2e4_heating_model"
    )

    allowed_uses = missionlab.get(
        "allowed_uses"
    )

    prohibited = missionlab.get(
        "prohibited_inferences"
    )

    for field_name, values in [
        (
            "relationship_to_phase2e4_heating_model",
            relationship,
        ),
        (
            "allowed_uses",
            allowed_uses,
        ),
        (
            "prohibited_inferences",
            prohibited,
        ),
    ]:
        if not isinstance(
            values,
            list,
        ):
            fail(
                f"{field_name} "
                "must be a list"
            )

        if not values:
            fail(
                f"{field_name} "
                "must not be empty"
            )

        for index, value in enumerate(
            values
        ):
            require_nonempty_string(
                value,
                (
                    f"{field_name}"
                    f"[{index}]"
                ),
            )

    if (
        set(
            prohibited
        )
        != REQUIRED_PROHIBITED_INFERENCES
    ):
        fail(
            "prohibited inference guardrails "
            "do not match expected set"
        )

    architecture = next(
        item
        for item in evidence_items
        if item["id"]
        == "orion_heat_shield_architecture"
    )

    architecture_values = (
        architecture.get(
            "key_values",
            {}
        )
    )

    if (
        architecture_values.get(
            "heat_shield_diameter_ft"
        )
        != 16.5
    ):
        fail(
            "unexpected Orion "
            "heat-shield diameter"
        )

    if (
        architecture_values.get(
            "avcoat_blocks"
        )
        != 186
    ):
        fail(
            "unexpected Avcoat block count"
        )

    thermal_tests = next(
        item
        for item in evidence_items
        if item["id"]
        == "artemis_i_thermal_test_campaign"
    )

    thermal_values = (
        thermal_tests.get(
            "key_values",
            {}
        )
    )

    if (
        thermal_values.get(
            "thermal_test_campaigns"
        )
        != 8
    ):
        fail(
            "unexpected thermal-test "
            "campaign count"
        )

    if (
        thermal_values.get(
            "individual_tests"
        )
        != 121
    ):
        fail(
            "unexpected thermal-test count"
        )

    entry_velocity = next(
        item
        for item in evidence_items
        if item["id"]
        == "artemis_ii_entry_velocity_prediction"
    )

    velocity_values = (
        entry_velocity.get(
            "key_values",
            {}
        )
    )

    if (
        velocity_values.get(
            "entry_interface_velocity_prediction_difference_mph"
        )
        != 1.0
    ):
        fail(
            "unexpected Artemis II "
            "entry-velocity comparison"
        )

    if (
        velocity_values.get(
            "comparison_semantics"
        )
        != "within"
    ):
        fail(
            "entry-velocity comparison "
            "must preserve 'within' "
            "semantics"
        )

    print()
    print(
        "Artemis II Orion TPS "
        "Evidence Validation"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Evidence items checked: "
        f"{len(evidence_items)}"
    )

    print(
        f"Decision-thread stages: "
        f"{len(stages)}"
    )

    print(
        f"Evidence categories: "
        f"{len(categories)}"
    )

    print(
        f"Unique source URLs: "
        f"{len(source_urls)}"
    )

    print(
        "Source hosts:"
    )

    for host in sorted(
        source_hosts
    ):
        print(
            f"  {host}"
        )

    print()
    print(
        "Decision-thread order:"
    )

    for stage in (
        observed_stage_order
    ):
        print(
            f"  {stage}"
        )

    print()
    print(
        "Key evidence invariants:"
    )

    print(
        "  Orion heat-shield diameter: "
        "16.5 ft"
    )

    print(
        "  Artemis II Avcoat blocks: "
        "186"
    )

    print(
        "  Artemis I thermal campaigns: "
        "8"
    )

    print(
        "  Artemis I individual tests: "
        "121"
    )

    print(
        "  Artemis II EI prediction: "
        "within 1 mph"
    )

    print()
    print(
        "Guardrails:"
    )

    print(
        "  Direct SG-to-char-loss "
        "prediction: PROHIBITED"
    )

    print(
        "  Unpublished permeability "
        "threshold inference: PROHIBITED"
    )

    print(
        "  Heritage calibration of SG: "
        "PROHIBITED"
    )

    print()
    print(
        "OK: TPS evidence inventory, "
        "NASA provenance, decision-thread "
        "references, numerical invariants, "
        "and interpretation guardrails "
        "validated."
    )


if __name__ == "__main__":
    main()
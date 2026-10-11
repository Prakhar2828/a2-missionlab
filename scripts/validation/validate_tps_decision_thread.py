from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]

EVIDENCE_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_tps_evidence.json"
)

THREAD_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "tps_decision_thread.json"
)

THREAD_SVG = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
    / "phase2f_tps_decision_thread.svg"
)


EXPECTED_STAGE_ORDER = [
    "DETECTION",
    "EVIDENCE_COLLECTION",
    "ROOT_CAUSE",
    "CONSTRAINT",
    "DECISION_AND_ACTION",
    "FLIGHT_OUTCOME",
    "LONG_TERM_CORRECTIVE_ACTION",
]


EXPECTED_CONTEXT_ONLY = {
    "orion_heat_shield_architecture",
    "avcoat_function",
}


ALLOWED_SOURCE_HOSTS = {
    "www.nasa.gov",
    "nasa.gov",
    "ntrs.nasa.gov",
}


def fail(
    message: str,
) -> None:
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def main() -> None:
    for path in [
        EVIDENCE_JSON,
        THREAD_JSON,
        THREAD_SVG,
    ]:
        if not path.exists():
            fail(
                f"missing required file: "
                f"{path}"
            )

    with EVIDENCE_JSON.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        evidence = json.load(
            f
        )

    with THREAD_JSON.open(
        "r",
        encoding="utf-8",
    ) as f:
        thread = json.load(
            f
        )

    if (
        thread.get(
            "product_id"
        )
        != "phase2f1_tps_decision_thread"
    ):
        fail(
            "unexpected product_id"
        )

    if (
        thread.get(
            "mission"
        )
        != "Artemis II"
    ):
        fail(
            "unexpected mission"
        )

    if (
        thread.get(
            "provenance"
        )
        != "DERIVED_FROM_NASA_REPORTED_EVIDENCE"
    ):
        fail(
            "unexpected provenance"
        )

    if (
        thread.get(
            "source_dataset"
        )
        != evidence.get(
            "dataset_id"
        )
    ):
        fail(
            "source-dataset mismatch"
        )

    evidence_items = (
        evidence[
            "evidence_items"
        ]
    )

    evidence_by_id = {
        item[
            "id"
        ]:
            item
        for item in evidence_items
    }

    source_stages = (
        evidence[
            "decision_thread"
        ][
            "stages"
        ]
    )

    derived_stages = (
        thread.get(
            "stages"
        )
    )

    if not isinstance(
        derived_stages,
        list,
    ):
        fail(
            "derived stages must "
            "be a list"
        )

    if len(
        derived_stages
    ) != 7:
        fail(
            "expected seven derived stages"
        )

    observed_stage_order = [
        stage[
            "stage"
        ]
        for stage in derived_stages
    ]

    if (
        observed_stage_order
        != EXPECTED_STAGE_ORDER
    ):
        fail(
            "unexpected derived-stage order"
        )

    referenced_ids = set()

    unique_source_urls = set()

    for index, (
        source_stage,
        derived_stage,
    ) in enumerate(
        zip(
            source_stages,
            derived_stages,
        ),
        start=1,
    ):
        if (
            derived_stage.get(
                "stage_index"
            )
            != index
        ):
            fail(
                f"incorrect stage index "
                f"at stage {index}"
            )

        if (
            derived_stage.get(
                "stage"
            )
            != source_stage.get(
                "stage"
            )
        ):
            fail(
                f"stage-name mismatch "
                f"at stage {index}"
            )

        if (
            derived_stage.get(
                "summary"
            )
            != source_stage.get(
                "summary"
            )
        ):
            fail(
                f"summary mismatch "
                f"for "
                f"{source_stage['stage']}"
            )

        derived_evidence = (
            derived_stage.get(
                "evidence"
            )
        )

        if not isinstance(
            derived_evidence,
            list,
        ):
            fail(
                f"{source_stage['stage']}: "
                "evidence must be a list"
            )

        source_ids = (
            source_stage[
                "evidence_ids"
            ]
        )

        derived_ids = [
            item[
                "evidence_id"
            ]
            for item in derived_evidence
        ]

        if (
            derived_ids
            != source_ids
        ):
            fail(
                f"{source_stage['stage']}: "
                "evidence-reference order "
                "or content changed"
            )

        if (
            derived_stage.get(
                "evidence_count"
            )
            != len(
                source_ids
            )
        ):
            fail(
                f"{source_stage['stage']}: "
                "incorrect evidence count"
            )

        for derived_item in (
            derived_evidence
        ):
            evidence_id = (
                derived_item[
                    "evidence_id"
                ]
            )

            if (
                evidence_id
                not in evidence_by_id
            ):
                fail(
                    "derived product contains "
                    f"unknown evidence ID "
                    f"{evidence_id}"
                )

            source_item = (
                evidence_by_id[
                    evidence_id
                ]
            )

            for field in [
                "category",
                "mission_context",
                "claim",
                "source_title",
                "source_url",
                "source_organization",
                "source_date",
                "provenance",
                "interpretation",
                "limitations",
            ]:
                if (
                    derived_item.get(
                        field
                    )
                    != source_item.get(
                        field
                    )
                ):
                    fail(
                        f"{evidence_id}: "
                        f"derived field "
                        f"{field!r} "
                        "does not reproduce "
                        "source evidence"
                    )

            hostname = (
                urlparse(
                    derived_item[
                        "source_url"
                    ]
                ).hostname
                or ""
            ).lower()

            if (
                hostname
                not in ALLOWED_SOURCE_HOSTS
            ):
                fail(
                    f"{evidence_id}: "
                    f"unexpected source host "
                    f"{hostname!r}"
                )

            unique_source_urls.add(
                derived_item[
                    "source_url"
                ]
            )

            referenced_ids.add(
                evidence_id
            )

    context_only = set(
        thread.get(
            "context_only_evidence_ids",
            [],
        )
    )

    if (
        context_only
        != EXPECTED_CONTEXT_ONLY
    ):
        fail(
            "unexpected context-only "
            "evidence inventory"
        )

    expected_referenced = (
        set(
            evidence_by_id
        )
        - EXPECTED_CONTEXT_ONLY
    )

    if (
        referenced_ids
        != expected_referenced
    ):
        fail(
            "derived thread does not "
            "reference the expected "
            "evidence inventory"
        )

    if (
        thread.get(
            "evidence_inventory_count"
        )
        != 17
    ):
        fail(
            "unexpected evidence inventory "
            "count"
        )

    if (
        thread.get(
            "decision_thread_referenced_evidence_count"
        )
        != 15
    ):
        fail(
            "unexpected referenced-evidence "
            "count"
        )

    if (
        thread.get(
            "stage_count"
        )
        != 7
    ):
        fail(
            "unexpected stage count"
        )

    if (
        thread.get(
            "unique_source_url_count"
        )
        != len(
            unique_source_urls
        )
    ):
        fail(
            "unique source URL count "
            "does not independently reproduce"
        )

    missionlab = (
        evidence[
            "missionlab_interpretation"
        ]
    )

    if (
        thread.get(
            "relationship_to_phase2e4"
        )
        != missionlab[
            "relationship_to_phase2e4_heating_model"
        ]
    ):
        fail(
            "Phase 2E.4 relationship "
            "guardrails changed"
        )

    if (
        thread.get(
            "allowed_uses"
        )
        != missionlab[
            "allowed_uses"
        ]
    ):
        fail(
            "allowed-use guardrails changed"
        )

    if (
        thread.get(
            "prohibited_inferences"
        )
        != missionlab[
            "prohibited_inferences"
        ]
    ):
        fail(
            "prohibited-inference "
            "guardrails changed"
        )

    svg_text = (
        THREAD_SVG.read_text(
            encoding="utf-8",
        )
    )

    if (
        "Artemis I Heat-Shield Finding"
        not in svg_text
    ):
        fail(
            "documentation SVG title "
            "not found"
        )

    print()
    print(
        "Artemis II TPS Decision-Thread "
        "Validation"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Stages checked: "
        f"{len(derived_stages)}"
    )

    print(
        f"Evidence records checked: "
        f"{len(evidence_items)}"
    )

    print(
        f"Thread-referenced evidence: "
        f"{len(referenced_ids)}"
    )

    print(
        f"Context-only evidence: "
        f"{len(context_only)}"
    )

    print(
        f"Unique thread source URLs: "
        f"{len(unique_source_urls)}"
    )

    print()
    print(
        "Decision-thread order:"
    )

    for index, stage in enumerate(
        observed_stage_order,
        start=1,
    ):
        print(
            f"  {index}. {stage}"
        )

    print()
    print(
        "Context-only records:"
    )

    for evidence_id in sorted(
        context_only
    ):
        print(
            f"  {evidence_id}"
        )

    print()
    print(
        "Guardrail preservation:"
    )

    print(
        "  Source claims copied exactly: PASS"
    )

    print(
        "  NASA source hosts only: PASS"
    )

    print(
        "  Phase 2E.4 relationship preserved: PASS"
    )

    print(
        "  Prohibited inferences preserved: PASS"
    )

    print()
    print(
        "OK: TPS decision-thread structure, "
        "evidence references, source claims, "
        "provenance, and interpretation "
        "guardrails independently validated."
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

EVIDENCE_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_tps_evidence.json"
)

OUTPUT_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "tps_decision_thread.json"
)

OUTPUT_SVG = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
    / "phase2f_tps_decision_thread.svg"
)


plt.rcParams["svg.hashsalt"] = (
    "a2-missionlab"
)

SVG_METADATA = {
    "Date": None,
}


DISPLAY_LABELS = {
    "DETECTION":
        "Detection",

    "EVIDENCE_COLLECTION":
        "Evidence\ncollection",

    "ROOT_CAUSE":
        "Root\ncause",

    "CONSTRAINT":
        "Constraint",

    "DECISION_AND_ACTION":
        "Decision\n& action",

    "FLIGHT_OUTCOME":
        "Flight\noutcome",

    "LONG_TERM_CORRECTIVE_ACTION":
        "Long-term\ncorrective action",
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


def main() -> None:
    if not EVIDENCE_JSON.exists():
        raise SystemExit(
            "Missing required evidence file:\n"
            f"{EVIDENCE_JSON}"
        )

    with EVIDENCE_JSON.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        dataset = json.load(
            f
        )

    evidence_items = dataset[
        "evidence_items"
    ]

    evidence_by_id = {
        item["id"]: item
        for item in evidence_items
    }

    thread = dataset[
        "decision_thread"
    ]

    stages = thread[
        "stages"
    ]

    observed_order = [
        stage["stage"]
        for stage in stages
    ]

    if (
        observed_order
        != EXPECTED_STAGE_ORDER
    ):
        raise SystemExit(
            "Unexpected TPS decision-thread "
            "stage order."
        )

    normalized_stages = []

    all_referenced_ids = []

    unique_source_urls = set()

    for index, stage in enumerate(
        stages,
        start=1,
    ):
        stage_evidence = []

        for evidence_id in (
            stage[
                "evidence_ids"
            ]
        ):
            if (
                evidence_id
                not in evidence_by_id
            ):
                raise SystemExit(
                    "Dangling evidence reference: "
                    f"{evidence_id}"
                )

            source_item = (
                evidence_by_id[
                    evidence_id
                ]
            )

            all_referenced_ids.append(
                evidence_id
            )

            unique_source_urls.add(
                source_item[
                    "source_url"
                ]
            )

            stage_evidence.append(
                {
                    "evidence_id":
                        evidence_id,

                    "category":
                        source_item[
                            "category"
                        ],

                    "mission_context":
                        source_item[
                            "mission_context"
                        ],

                    "claim":
                        source_item[
                            "claim"
                        ],

                    "source_title":
                        source_item[
                            "source_title"
                        ],

                    "source_url":
                        source_item[
                            "source_url"
                        ],

                    "source_organization":
                        source_item[
                            "source_organization"
                        ],

                    "source_date":
                        source_item.get(
                            "source_date"
                        ),

                    "provenance":
                        source_item[
                            "provenance"
                        ],

                    "interpretation":
                        source_item[
                            "interpretation"
                        ],

                    "limitations":
                        source_item[
                            "limitations"
                        ],
                }
            )

        normalized_stages.append(
            {
                "stage_index":
                    index,

                "stage":
                    stage[
                        "stage"
                    ],

                "display_label":
                    DISPLAY_LABELS[
                        stage[
                            "stage"
                        ]
                    ].replace(
                        "\n",
                        " ",
                    ),

                "summary":
                    stage[
                        "summary"
                    ],

                "evidence_count":
                    len(
                        stage_evidence
                    ),

                "evidence":
                    stage_evidence,
            }
        )

    referenced_unique = set(
        all_referenced_ids
    )

    unreferenced_context_ids = sorted(
        set(
            evidence_by_id
        )
        - referenced_unique
    )

    output = {
        "product_id":
            "phase2f1_tps_decision_thread",

        "mission":
            "Artemis II",

        "provenance":
            "DERIVED_FROM_NASA_REPORTED_EVIDENCE",

        "source_dataset":
            dataset[
                "dataset_id"
            ],

        "title":
            thread[
                "title"
            ],

        "purpose":
            (
                "Normalize authoritative NASA "
                "evidence into a mission-facing "
                "engineering decision thread."
            ),

        "stage_count":
            len(
                normalized_stages
            ),

        "evidence_inventory_count":
            len(
                evidence_items
            ),

        "decision_thread_referenced_evidence_count":
            len(
                referenced_unique
            ),

        "context_only_evidence_ids":
            unreferenced_context_ids,

        "unique_source_url_count":
            len(
                unique_source_urls
            ),

        "stages":
            normalized_stages,

        "relationship_to_phase2e4":
            dataset[
                "missionlab_interpretation"
            ][
                "relationship_to_phase2e4_heating_model"
            ],

        "allowed_uses":
            dataset[
                "missionlab_interpretation"
            ][
                "allowed_uses"
            ],

        "prohibited_inferences":
            dataset[
                "missionlab_interpretation"
            ][
                "prohibited_inferences"
            ],

        "interpretation":
            (
                "The product reconstructs an "
                "evidence-grounded engineering "
                "decision sequence. It does not "
                "model Avcoat material response "
                "or predict Artemis II TPS damage."
            ),
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
            output,
            f,
            indent=2,
        )

    OUTPUT_SVG.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    x = list(
        range(
            1,
            len(stages) + 1,
        )
    )

    y = [
        0
        for _ in x
    ]

    fig, ax = plt.subplots(
        figsize=(
            12,
            3.6,
        )
    )

    ax.plot(
        x,
        y,
        linewidth=1.5,
    )

    ax.scatter(
        x,
        y,
        s=60,
        zorder=3,
    )

    for index, stage in enumerate(
        stages,
        start=1,
    ):
        label = DISPLAY_LABELS[
            stage[
                "stage"
            ]
        ]

        vertical_offset = (
            18
            if index % 2
            else -38
        )

        ax.annotate(
            label,
            (
                index,
                0,
            ),
            xytext=(
                0,
                vertical_offset,
            ),
            textcoords="offset points",
            ha="center",
            va="center",
        )

    ax.set_xlim(
        0.5,
        len(stages) + 0.5,
    )

    ax.set_ylim(
        -1,
        1,
    )

    ax.set_yticks(
        []
    )

    ax.set_xticks(
        []
    )

    ax.set_title(
        "Artemis I Heat-Shield Finding "
        "to Artemis II TPS Outcome"
    )

    for spine in [
        "left",
        "right",
        "top",
        "bottom",
    ]:
        ax.spines[
            spine
        ].set_visible(
            False
        )

    fig.tight_layout()

    fig.savefig(
        OUTPUT_SVG,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(
        fig
    )

    normalize_svg(
        OUTPUT_SVG
    )

    print()
    print(
        "Artemis II TPS Decision Thread"
    )

    print(
        "------------------------------"
    )

    print(
        f"Evidence inventory: "
        f"{len(evidence_items)}"
    )

    print(
        f"Decision stages: "
        f"{len(normalized_stages)}"
    )

    print(
        f"Evidence referenced by thread: "
        f"{len(referenced_unique)}"
    )

    print(
        f"Context-only evidence records: "
        f"{len(unreferenced_context_ids)}"
    )

    print(
        f"Unique source URLs used by thread: "
        f"{len(unique_source_urls)}"
    )

    print()
    print(
        "Decision sequence:"
    )

    for stage in (
        normalized_stages
    ):
        print(
            f"  {stage['stage_index']}. "
            f"{stage['stage']}"
            f"  "
            f"({stage['evidence_count']} "
            f"evidence record"
            f"{'' if stage['evidence_count'] == 1 else 's'})"
        )

    print()
    print(
        "Context-only records:"
    )

    for evidence_id in (
        unreferenced_context_ids
    ):
        print(
            f"  {evidence_id}"
        )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "This thread is derived from "
        "NASA-reported evidence."
    )

    print(
        "It is not a TPS damage model."
    )

    print(
        "Phase 2E.4 Sutton-Graves heating "
        "must not be converted directly "
        "into char-loss predictions."
    )

    print()
    print(
        f"Wrote: "
        f"{OUTPUT_JSON.relative_to(ROOT)}"
    )

    print(
        f"Wrote: "
        f"{OUTPUT_SVG.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
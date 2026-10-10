from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[2]

BOUNDARY_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_tps_physics_boundary.json"
)

TPS_EVIDENCE_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_tps_evidence.json"
)

LOFT_HISTORY_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "loft_heating_history.json"
)

OUTPUT_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "tps_physics_boundary_summary.json"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
    / "phase2f_tps_physics_boundary.svg"
)


plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


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


def validate_stage_order(
    stages,
) -> None:
    orders = [
        int(
            stage[
                "order"
            ]
        )
        for stage in stages
    ]

    expected = list(
        range(
            1,
            len(stages) + 1,
        )
    )

    if orders != expected:
        raise SystemExit(
            "Physics-boundary stages are "
            "not sequentially ordered."
        )


def make_boundary_figure(
    stages,
    frontier_stage_id,
    boundary_stage_id,
) -> None:
    FIGURE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(
            10.0,
            9.0,
        )
    )

    ax.set_xlim(
        0.0,
        1.0,
    )

    ax.set_ylim(
        0.0,
        1.0,
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        "Orion TPS Evidence-to-Physics Boundary",
        pad=18,
    )

    top = 0.88
    height = 0.075
    gap = 0.025

    y_positions = {}

    for index, stage in enumerate(
        stages
    ):
        y = (
            top
            - index
            * (
                height
                + gap
            )
        )

        y_positions[
            stage[
                "stage_id"
            ]
        ] = y

        rectangle = Rectangle(
            (
                0.08,
                y,
            ),
            0.84,
            height,
            fill=False,
            linewidth=1.2,
        )

        ax.add_patch(
            rectangle
        )

        ax.text(
            0.10,
            y
            + height
            * 0.67,
            (
                f"{stage['order']}. "
                f"{stage['label']}"
            ),
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

        ax.text(
            0.10,
            y
            + height
            * 0.28,
            stage[
                "status"
            ],
            ha="left",
            va="center",
            fontsize=8.5,
        )

        if index < (
            len(stages)
            - 1
        ):
            next_y = (
                top
                - (
                    index
                    + 1
                )
                * (
                    height
                    + gap
                )
            )

            ax.annotate(
                "",
                xy=(
                    0.50,
                    next_y
                    + height,
                ),
                xytext=(
                    0.50,
                    y,
                ),
                arrowprops={
                    "arrowstyle":
                        "->",
                    "linewidth":
                        0.9,
                },
            )

    frontier_y = y_positions[
        frontier_stage_id
    ]

    boundary_y = y_positions[
        boundary_stage_id
    ]

    boundary_line_y = (
        (
            frontier_y
            + boundary_y
            + height
        )
        / 2.0
    )

    ax.axhline(
        boundary_line_y,
        xmin=0.04,
        xmax=0.96,
        linewidth=1.4,
        linestyle="--",
    )

    ax.text(
        0.50,
        boundary_line_y
        + 0.008,
        (
            "MISSIONLAB CURRENT "
            "QUANTITATIVE PHYSICS BOUNDARY"
        ),
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )

    ax.text(
        0.96,
        frontier_y
        + height
        * 0.5,
        "QUANTITATIVE\nRECONSTRUCTION",
        ha="right",
        va="center",
        fontsize=8,
    )

    ax.text(
        0.96,
        boundary_y
        + height
        * 0.5,
        "NASA MECHANISM /\nNOT MODELED",
        ha="right",
        va="center",
        fontsize=8,
    )

    ax.text(
        0.50,
        0.025,
        (
            "External aerothermal reconstruction "
            "stops before internal Avcoat "
            "material-response prediction."
        ),
        ha="center",
        va="bottom",
        fontsize=8.5,
    )

    fig.tight_layout()

    fig.savefig(
        FIGURE_PATH,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(
        fig
    )

    normalize_svg(
        FIGURE_PATH
    )


def main() -> None:
    boundary = load_json(
        BOUNDARY_JSON
    )

    evidence = load_json(
        TPS_EVIDENCE_JSON
    )

    loft = load_json(
        LOFT_HISTORY_JSON
    )

    expected_evidence_dataset = (
        boundary[
            "source_evidence_dataset_id"
        ]
    )

    if (
        evidence[
            "dataset_id"
        ]
        != expected_evidence_dataset
    ):
        raise SystemExit(
            "TPS evidence dataset does not "
            "match the boundary reference."
        )

    evidence_by_id = {
        item[
            "id"
        ]: item
        for item in evidence[
            "evidence_items"
        ]
    }

    missing_evidence = [
        item_id
        for item_id in boundary[
            "source_evidence_ids"
        ]
        if item_id
        not in evidence_by_id
    ]

    if missing_evidence:
        raise SystemExit(
            "Missing required TPS evidence IDs:\n"
            + "\n".join(
                missing_evidence
            )
        )

    mechanism_reference = (
        boundary[
            "nasa_reported_mechanism"
        ][
            "sequence"
        ]
    )

    mechanism_source_id = (
        boundary[
            "nasa_reported_mechanism"
        ][
            "source_evidence_id"
        ]
    )

    mechanism_source = (
        evidence_by_id[
            mechanism_source_id
        ]
    )

    mechanism_evidence = (
        mechanism_source.get(
            "mechanism",
            {}
        ).get(
            "sequence",
            [],
        )
    )

    if (
        mechanism_evidence
        != mechanism_reference
    ):
        raise SystemExit(
            "NASA mechanism sequence in "
            "the boundary reference does "
            "not exactly match the Phase "
            "2F.1 evidence dataset."
        )

    stages = (
        boundary[
            "physics_boundary"
        ][
            "stages"
        ]
    )

    validate_stage_order(
        stages
    )

    stage_by_id = {
        stage[
            "stage_id"
        ]: stage
        for stage in stages
    }

    frontier_stage_id = (
        boundary[
            "physics_boundary"
        ][
            "missionlab_quantitative_frontier_stage_id"
        ]
    )

    boundary_stage_id = (
        boundary[
            "physics_boundary"
        ][
            "boundary_begins_at_stage_id"
        ]
    )

    if (
        frontier_stage_id
        not in stage_by_id
    ):
        raise SystemExit(
            "Quantitative frontier stage "
            "is missing."
        )

    if (
        boundary_stage_id
        not in stage_by_id
    ):
        raise SystemExit(
            "Physics-boundary start stage "
            "is missing."
        )

    frontier_stage = (
        stage_by_id[
            frontier_stage_id
        ]
    )

    boundary_stage = (
        stage_by_id[
            boundary_stage_id
        ]
    )

    if int(
        frontier_stage[
            "order"
        ]
    ) != 2:
        raise SystemExit(
            "Expected external heating "
            "to remain stage 2."
        )

    if int(
        boundary_stage[
            "order"
        ]
    ) != 3:
        raise SystemExit(
            "Expected material-response "
            "boundary to begin at stage 3."
        )

    for stage in stages:
        order = int(
            stage[
                "order"
            ]
        )

        inside = bool(
            stage[
                "inside_current_missionlab_quantitative_model"
            ]
        )

        expected_inside = (
            order <= 2
        )

        if (
            inside
            != expected_inside
        ):
            raise SystemExit(
                "Unexpected quantitative-model "
                "membership for stage "
                f"{stage['stage_id']}."
            )

    assertions = (
        boundary[
            "model_assertions"
        ]
    )

    if any(
        bool(value)
        for value in assertions.values()
    ):
        raise SystemExit(
            "At least one prohibited "
            "material-response inference "
            "was marked as created."
        )

    strong_domain = (
        loft[
            "strong_domain_partition"
        ]
    )

    flux_change = (
        loft[
            "rebound_external_flux_change"
        ]
    )

    summary = {
        "product_id":
            "phase2f4_tps_physics_boundary_summary",

        "reference_dataset":
            boundary[
                "dataset_id"
            ],

        "source_evidence_dataset":
            evidence[
                "dataset_id"
            ],

        "provenance":
            (
                "MIXED_PROJECT_SCOPE_GUARDRAIL_"
                "NASA_REPORTED_MECHANISM_"
                "MISSIONLAB_DERIVED_CONTEXT"
            ),

        "source_evidence_items_verified":
            len(
                boundary[
                    "source_evidence_ids"
                ]
            ),

        "nasa_reported_mechanism": {
            "source_evidence_id":
                mechanism_source_id,

            "sequence":
                mechanism_evidence,

            "sequence_verified_against_phase2f1":
                True,
        },

        "current_missionlab_external_environment": {
            "strong_domain_heat_load_mj_m2":
                float(
                    strong_domain[
                        "existing_phase2e4_heat_load_mj_m2"
                    ]
                ),

            "loft_start_external_sg_flux_w_cm2":
                float(
                    flux_change[
                        "start_w_cm2"
                    ]
                ),

            "loft_end_external_sg_flux_w_cm2":
                float(
                    flux_change[
                        "end_w_cm2"
                    ]
                ),

            "loft_external_sg_flux_signed_percent_change":
                float(
                    flux_change[
                        "signed_percent_change"
                    ]
                ),

            "interpretation":
                (
                    "These are external "
                    "aerothermal model outputs, "
                    "not internal TPS response "
                    "quantities."
                ),
        },

        "quantitative_frontier": {
            "last_stage_inside_current_model":
                frontier_stage_id,

            "last_stage_order":
                int(
                    frontier_stage[
                        "order"
                    ]
                ),

            "first_stage_outside_current_model":
                boundary_stage_id,

            "first_stage_outside_order":
                int(
                    boundary_stage[
                        "order"
                    ]
                ),

            "boundary_statement":
                (
                    "MissionLab currently stops "
                    "after modeled external "
                    "convective heating and before "
                    "surface/internal Avcoat "
                    "material-response prediction."
                ),
        },

        "physics_stages":
            stages,

        "missionlab_quantitative_products":
            boundary[
                "missionlab_quantitative_products"
            ],

        "material_response_quantities_not_reconstructed":
            boundary[
                "material_response_quantities_not_reconstructed"
            ],

        "nasa_investigation_data_not_present_as_quantitative_missionlab_inputs":
            boundary[
                "nasa_investigation_data_not_present_as_quantitative_missionlab_inputs"
            ],

        "prohibited_model_bridges":
            boundary[
                "prohibited_model_bridges"
            ],

        "permitted_conclusions":
            boundary[
                "permitted_conclusions"
            ],

        "model_assertions":
            assertions,

        "figure":
            str(
                FIGURE_PATH.relative_to(
                    ROOT
                )
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
            summary,
            f,
            indent=2,
        )

    make_boundary_figure(
        stages,
        frontier_stage_id,
        boundary_stage_id,
    )

    print()
    print(
        "Phase 2F.4 TPS Evidence-to-Physics Boundary"
    )

    print(
        "=========================================="
    )

    print()
    print(
        "Evidence:"
    )

    print(
        f"  source dataset: "
        f"{evidence['dataset_id']}"
    )

    print(
        f"  source evidence items verified: "
        f"{len(boundary['source_evidence_ids'])}"
    )

    print()
    print(
        "NASA-reported mechanism:"
    )

    for index, step in enumerate(
        mechanism_evidence,
        start=1,
    ):
        print(
            f"  {index}. {step}"
        )

    print()
    print(
        "MissionLab quantitative frontier:"
    )

    print(
        f"  last modeled stage: "
        f"{frontier_stage['label']}"
    )

    print(
        f"  first unmodeled stage: "
        f"{boundary_stage['label']}"
    )

    print()
    print(
        "Physics stages:"
    )

    for stage in stages:
        print(
            f"  {stage['order']}. "
            f"{stage['label']}"
        )

        print(
            f"     {stage['status']}"
        )

    print()
    print(
        "Current external environment context:"
    )

    print(
        "  strong-domain modeled SG heat load:"
    )

    print(
        f"    "
        f"{strong_domain['existing_phase2e4_heat_load_mj_m2']:.9f} "
        "MJ/m^2"
    )

    print(
        "  loft-start external SG flux:"
    )

    print(
        f"    "
        f"{flux_change['start_w_cm2']:.6f} "
        "W/cm^2"
    )

    print(
        "  loft-end external SG flux:"
    )

    print(
        f"    "
        f"{flux_change['end_w_cm2']:.6f} "
        "W/cm^2"
    )

    print(
        "  signed external flux change:"
    )

    print(
        f"    "
        f"{flux_change['signed_percent_change']:+.6f}%"
    )

    print()
    print(
        "Scope counts:"
    )

    print(
        "  MissionLab quantitative products:"
    )

    print(
        f"    "
        f"{len(boundary['missionlab_quantitative_products'])}"
    )

    print(
        "  material-response quantities absent:"
    )

    print(
        f"    "
        f"{len(boundary['material_response_quantities_not_reconstructed'])}"
    )

    print(
        "  NASA investigation data types absent:"
    )

    print(
        f"    "
        f"{len(boundary['nasa_investigation_data_not_present_as_quantitative_missionlab_inputs'])}"
    )

    print(
        "  prohibited direct model bridges:"
    )

    print(
        f"    "
        f"{len(boundary['prohibited_model_bridges'])}"
    )

    print()
    print(
        "Model assertions:"
    )

    for key, value in assertions.items():
        print(
            f"  {key}: "
            f"{str(value).upper()}"
        )

    print()
    print(
        "Boundary conclusion:"
    )

    print(
        "  MissionLab reconstructs the "
        "external aerothermal environment."
    )

    print(
        "  MissionLab does not currently "
        "predict internal Avcoat response "
        "or char-loss damage."
    )

    print()
    print(
        "Wrote:"
    )

    print(
        f"  {OUTPUT_JSON.relative_to(ROOT)}"
    )

    print(
        f"  {FIGURE_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import json
from pathlib import Path


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

SUMMARY_JSON = (
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


EXPECTED_DATASET_ID = (
    "phase2f4_artemis_tps_physics_boundary"
)

EXPECTED_SOURCE_DATASET_ID = (
    "phase2f1_orion_tps_heritage_evidence"
)

EXPECTED_PRODUCT_ID = (
    "phase2f4_tps_physics_boundary_summary"
)

EXPECTED_PROVENANCE = (
    "PROJECT_SCOPE_GUARDRAIL_WITH_"
    "NASA_REPORTED_MECHANISM"
)

EXPECTED_SUMMARY_PROVENANCE = (
    "MIXED_PROJECT_SCOPE_GUARDRAIL_"
    "NASA_REPORTED_MECHANISM_"
    "MISSIONLAB_DERIVED_CONTEXT"
)

EXPECTED_STAGE_IDS = [
    "trajectory_external_flow",
    "external_convective_heating",
    "surface_internal_thermal_response",
    "pyrolysis_gas_generation",
    "gas_transport_permeability",
    "internal_pressure",
    "cracking_fracture",
    "char_liberation_damage",
]

EXPECTED_STAGE_STATUS = [
    "MISSIONLAB_RECONSTRUCTS",
    "MISSIONLAB_MODELS",
    "BOUNDARY_NOT_MODELED",
    "NASA_MECHANISM_KNOWN_NOT_MODELED",
    "NASA_MECHANISM_KNOWN_NOT_MODELED",
    "NASA_MECHANISM_KNOWN_NOT_MODELED",
    "NASA_MECHANISM_KNOWN_NOT_MODELED",
    "NASA_OBSERVED_OUTCOME_NOT_PREDICTED",
]

EXPECTED_MODEL_MEMBERSHIP = [
    True,
    True,
    False,
    False,
    False,
    False,
    False,
    False,
]

EXPECTED_MECHANISM = [
    "Avcoat heats during atmospheric entry",
    "pyrolysis and ablation generate gases inside the material",
    "low-permeability Avcoat restricts gas escape",
    "internal gas pressure increases",
    "cracks form",
    "charred material is liberated",
]

EXPECTED_BRIDGES = [
    (
        "external Sutton-Graves heat flux",
        "Avcoat internal temperature",
    ),
    (
        "external Sutton-Graves heat load",
        "pyrolysis rate",
    ),
    (
        "external Sutton-Graves heat load",
        "internal gas pressure",
    ),
    (
        "loft / rebound geometry",
        "crack probability",
    ),
    (
        "external heating history",
        "char-loss mass or area",
    ),
    (
        "external heat-flux decline",
        "TPS cooling",
    ),
    (
        "Artemis I / Artemis II entry-profile difference",
        "numerical char-loss reduction percentage",
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

    summary = load_json(
        SUMMARY_JSON
    )

    if (
        boundary.get(
            "dataset_id"
        )
        != EXPECTED_DATASET_ID
    ):
        fail(
            "unexpected boundary dataset_id"
        )

    if (
        boundary.get(
            "provenance"
        )
        != EXPECTED_PROVENANCE
    ):
        fail(
            "unexpected boundary provenance"
        )

    if (
        boundary.get(
            "source_evidence_dataset_id"
        )
        != EXPECTED_SOURCE_DATASET_ID
    ):
        fail(
            "unexpected source evidence dataset"
        )

    if (
        evidence.get(
            "dataset_id"
        )
        != EXPECTED_SOURCE_DATASET_ID
    ):
        fail(
            "Phase 2F.1 evidence dataset mismatch"
        )

    evidence_by_id = {
        item[
            "id"
        ]: item
        for item in evidence[
            "evidence_items"
        ]
    }

    source_ids = boundary.get(
        "source_evidence_ids",
        [],
    )

    if len(
        source_ids
    ) != len(
        set(
            source_ids
        )
    ):
        fail(
            "duplicate source evidence IDs"
        )

    for item_id in source_ids:
        if (
            item_id
            not in evidence_by_id
        ):
            fail(
                "missing Phase 2F.1 evidence "
                f"item: {item_id}"
            )

    if len(
        source_ids
    ) != 14:
        fail(
            "expected 14 Phase 2F.1 "
            "source evidence items"
        )

    mechanism = (
        boundary[
            "nasa_reported_mechanism"
        ]
    )

    if (
        mechanism.get(
            "source_evidence_id"
        )
        != "artemis_i_root_cause_low_permeability"
    ):
        fail(
            "unexpected mechanism source ID"
        )

    if (
        mechanism.get(
            "sequence"
        )
        != EXPECTED_MECHANISM
    ):
        fail(
            "boundary mechanism sequence changed"
        )

    evidence_mechanism = (
        evidence_by_id[
            "artemis_i_root_cause_low_permeability"
        ].get(
            "mechanism",
            {}
        ).get(
            "sequence",
            [],
        )
    )

    if (
        evidence_mechanism
        != EXPECTED_MECHANISM
    ):
        fail(
            "Phase 2F.1 evidence mechanism "
            "no longer matches expected sequence"
        )

    physics_boundary = (
        boundary.get(
            "physics_boundary"
        )
    )

    if not isinstance(
        physics_boundary,
        dict,
    ):
        fail(
            "missing physics_boundary block"
        )

    if (
        physics_boundary.get(
            "missionlab_quantitative_frontier_stage_id"
        )
        != "external_convective_heating"
    ):
        fail(
            "quantitative frontier changed"
        )

    if (
        physics_boundary.get(
            "boundary_begins_at_stage_id"
        )
        != "surface_internal_thermal_response"
    ):
        fail(
            "material-response boundary changed"
        )

    stages = physics_boundary.get(
        "stages",
        []
    )

    if len(
        stages
    ) != 8:
        fail(
            "expected eight physics stages"
        )

    observed_ids = [
        stage.get(
            "stage_id"
        )
        for stage in stages
    ]

    if (
        observed_ids
        != EXPECTED_STAGE_IDS
    ):
        fail(
            "physics-stage IDs or order changed"
        )

    observed_orders = [
        int(
            stage.get(
                "order"
            )
        )
        for stage in stages
    ]

    if (
        observed_orders
        != list(
            range(
                1,
                9,
            )
        )
    ):
        fail(
            "physics-stage numerical order changed"
        )

    observed_status = [
        stage.get(
            "status"
        )
        for stage in stages
    ]

    if (
        observed_status
        != EXPECTED_STAGE_STATUS
    ):
        fail(
            "physics-stage status changed"
        )

    observed_membership = [
        bool(
            stage.get(
                "inside_current_missionlab_quantitative_model"
            )
        )
        for stage in stages
    ]

    if (
        observed_membership
        != EXPECTED_MODEL_MEMBERSHIP
    ):
        fail(
            "current MissionLab model boundary changed"
        )

    missing_quantities = (
        boundary.get(
            "material_response_quantities_not_reconstructed",
            [],
        )
    )

    if len(
        missing_quantities
    ) != 17:
        fail(
            "expected 17 absent material-response quantities"
        )

    missing_names = {
        item[
            "quantity"
        ]
        for item in missing_quantities
    }

    required_missing = {
        "through-thickness Avcoat temperature",
        "pyrolysis rate",
        "pyrolysis-gas mass generation",
        "gas transport through Avcoat",
        "local permeability field",
        "internal pore or gas pressure",
        "crack initiation",
        "crack propagation",
        "recession depth",
        "char-liberation mass or area",
    }

    if not (
        required_missing
        <= missing_names
    ):
        fail(
            "required missing-physics inventory incomplete"
        )

    bridges = boundary.get(
        "prohibited_model_bridges",
        [],
    )

    if len(
        bridges
    ) != len(
        EXPECTED_BRIDGES
    ):
        fail(
            "unexpected prohibited bridge count"
        )

    observed_bridges = [
        (
            bridge.get(
                "from"
            ),
            bridge.get(
                "to"
            ),
        )
        for bridge in bridges
    ]

    if (
        observed_bridges
        != EXPECTED_BRIDGES
    ):
        fail(
            "prohibited bridge inventory changed"
        )

    for bridge in bridges:
        if (
            bridge.get(
                "status"
            )
            != "PROHIBITED"
        ):
            fail(
                "prohibited model bridge "
                "lost PROHIBITED status"
            )

    investigation_data = (
        boundary.get(
            "nasa_investigation_data_not_present_as_quantitative_missionlab_inputs",
            [],
        )
    )

    if len(
        investigation_data
    ) != 7:
        fail(
            "expected seven absent NASA "
            "investigation data categories"
        )

    assertions = boundary.get(
        "model_assertions"
    )

    if not isinstance(
        assertions,
        dict,
    ):
        fail(
            "missing model_assertions"
        )

    if any(
        bool(value)
        for value in assertions.values()
    ):
        fail(
            "one or more prohibited "
            "material-response assertions "
            "became true"
        )

    if len(
        assertions
    ) != 8:
        fail(
            "unexpected model assertion count"
        )

    if (
        summary.get(
            "product_id"
        )
        != EXPECTED_PRODUCT_ID
    ):
        fail(
            "unexpected processed product_id"
        )

    if (
        summary.get(
            "reference_dataset"
        )
        != EXPECTED_DATASET_ID
    ):
        fail(
            "processed reference dataset mismatch"
        )

    if (
        summary.get(
            "source_evidence_dataset"
        )
        != EXPECTED_SOURCE_DATASET_ID
    ):
        fail(
            "processed source evidence mismatch"
        )

    if (
        summary.get(
            "provenance"
        )
        != EXPECTED_SUMMARY_PROVENANCE
    ):
        fail(
            "processed provenance changed"
        )

    if (
        summary.get(
            "source_evidence_items_verified"
        )
        != 14
    ):
        fail(
            "processed evidence verification count changed"
        )

    summary_mechanism = (
        summary[
            "nasa_reported_mechanism"
        ]
    )

    if (
        summary_mechanism.get(
            "sequence"
        )
        != EXPECTED_MECHANISM
    ):
        fail(
            "processed mechanism sequence changed"
        )

    if (
        summary_mechanism.get(
            "sequence_verified_against_phase2f1"
        )
        is not True
    ):
        fail(
            "mechanism verification flag missing"
        )

    frontier = summary.get(
        "quantitative_frontier"
    )

    if not isinstance(
        frontier,
        dict,
    ):
        fail(
            "missing processed quantitative frontier"
        )

    if (
        frontier.get(
            "last_stage_inside_current_model"
        )
        != "external_convective_heating"
    ):
        fail(
            "processed model frontier changed"
        )

    if (
        frontier.get(
            "first_stage_outside_current_model"
        )
        != "surface_internal_thermal_response"
    ):
        fail(
            "processed boundary start changed"
        )

    if (
        frontier.get(
            "last_stage_order"
        )
        != 2
    ):
        fail(
            "unexpected last modeled stage order"
        )

    if (
        frontier.get(
            "first_stage_outside_order"
        )
        != 3
    ):
        fail(
            "unexpected first unmodeled stage order"
        )

    external = summary.get(
        "current_missionlab_external_environment"
    )

    if not isinstance(
        external,
        dict,
    ):
        fail(
            "missing external-environment context"
        )

    expected_strong_load = float(
        loft[
            "strong_domain_partition"
        ][
            "existing_phase2e4_heat_load_mj_m2"
        ]
    )

    expected_start_flux = float(
        loft[
            "rebound_external_flux_change"
        ][
            "start_w_cm2"
        ]
    )

    expected_end_flux = float(
        loft[
            "rebound_external_flux_change"
        ][
            "end_w_cm2"
        ]
    )

    expected_change = float(
        loft[
            "rebound_external_flux_change"
        ][
            "signed_percent_change"
        ]
    )

    if abs(
        float(
            external[
                "strong_domain_heat_load_mj_m2"
            ]
        )
        - expected_strong_load
    ) > 1e-9:
        fail(
            "strong-domain heat-load context changed"
        )

    if abs(
        float(
            external[
                "loft_start_external_sg_flux_w_cm2"
            ]
        )
        - expected_start_flux
    ) > 1e-9:
        fail(
            "loft-start external flux changed"
        )

    if abs(
        float(
            external[
                "loft_end_external_sg_flux_w_cm2"
            ]
        )
        - expected_end_flux
    ) > 1e-9:
        fail(
            "loft-end external flux changed"
        )

    if abs(
        float(
            external[
                "loft_external_sg_flux_signed_percent_change"
            ]
        )
        - expected_change
    ) > 1e-9:
        fail(
            "loft external flux-change context changed"
        )

    if (
        summary.get(
            "model_assertions"
        )
        != assertions
    ):
        fail(
            "processed model assertions "
            "do not match reference"
        )

    if (
        summary.get(
            "prohibited_model_bridges"
        )
        != bridges
    ):
        fail(
            "processed prohibited bridges "
            "do not match reference"
        )

    expected_figure = str(
        FIGURE_PATH.relative_to(
            ROOT
        )
    )

    if (
        summary.get(
            "figure"
        )
        != expected_figure
    ):
        fail(
            "processed figure path mismatch"
        )

    if not (
        FIGURE_PATH.exists()
    ):
        fail(
            "missing physics-boundary SVG"
        )

    figure_text = (
        FIGURE_PATH.read_text(
            encoding="utf-8",
        )
    )

    if "<svg" not in figure_text:
        fail(
            "invalid physics-boundary SVG"
        )

    if len(
        figure_text
    ) < 1000:
        fail(
            "physics-boundary SVG "
            "is unexpectedly small"
        )

    print()
    print(
        "Phase 2F.4 TPS Physics-Boundary Validation"
    )

    print(
        "=========================================="
    )

    print()
    print(
        "Evidence foundation:"
    )

    print(
        f"  Phase 2F.1 dataset: "
        f"{EXPECTED_SOURCE_DATASET_ID}"
    )

    print(
        "  source evidence items verified: 14"
    )

    print(
        "  NASA root-cause sequence: VERIFIED"
    )

    print()
    print(
        "Quantitative boundary:"
    )

    print(
        "  stage 1: TRAJECTORY / EXTERNAL FLOW"
    )

    print(
        "           MISSIONLAB_RECONSTRUCTS"
    )

    print(
        "  stage 2: EXTERNAL CONVECTIVE HEATING"
    )

    print(
        "           MISSIONLAB_MODELS"
    )

    print(
        "  --------------------------------------"
    )

    print(
        "  CURRENT MISSIONLAB PHYSICS BOUNDARY"
    )

    print(
        "  --------------------------------------"
    )

    print(
        "  stage 3: SURFACE / INTERNAL "
        "THERMAL RESPONSE"
    )

    print(
        "           NOT MODELED"
    )

    print()
    print(
        "Remaining NASA mechanism:"
    )

    print(
        "  pyrolysis / gas generation"
    )

    print(
        "  gas transport / permeability"
    )

    print(
        "  internal gas pressure"
    )

    print(
        "  cracking / fracture"
    )

    print(
        "  char liberation / damage"
    )

    print()
    print(
        "Current external context:"
    )

    print(
        f"  strong-domain heat load: "
        f"{expected_strong_load:.9f} MJ/m^2"
    )

    print(
        f"  loft-start SG flux: "
        f"{expected_start_flux:.6f} W/cm^2"
    )

    print(
        f"  loft-end SG flux: "
        f"{expected_end_flux:.6f} W/cm^2"
    )

    print(
        f"  loft flux change: "
        f"{expected_change:+.6f}%"
    )

    print()
    print(
        "Boundary inventory:"
    )

    print(
        "  physics stages: 8"
    )

    print(
        "  material-response quantities absent: 17"
    )

    print(
        "  investigation data categories absent: 7"
    )

    print(
        "  prohibited model bridges: 7"
    )

    print(
        "  prohibited model assertions false: 8 / 8"
    )

    print()
    print(
        "Guardrails:"
    )

    print(
        "  SG heating -> internal temperature: PROHIBITED"
    )

    print(
        "  SG heat load -> pyrolysis: PROHIBITED"
    )

    print(
        "  SG heat load -> internal pressure: PROHIBITED"
    )

    print(
        "  loft geometry -> cracking: PROHIBITED"
    )

    print(
        "  external heating -> char-loss quantity: PROHIBITED"
    )

    print(
        "  external flux decline -> TPS cooling: PROHIBITED"
    )

    print(
        "  trajectory difference -> numerical "
        "char-loss reduction: PROHIBITED"
    )

    print()
    print(
        "Figure checked: 1"
    )

    print()
    print(
        "OK: Phase 2F.4 NASA evidence linkage, "
        "quantitative physics boundary, missing-"
        "physics inventory, prohibited model "
        "bridges, external-environment context, "
        "and causal-boundary figure independently "
        "validated."
    )


if __name__ == "__main__":
    main()
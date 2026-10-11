from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


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

plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path):
    if not path.exists():
        fail(
            "Missing required file:\n"
            f"{path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def normalize_svg(path: Path) -> None:
    text = path.read_text(
        encoding="utf-8",
    )

    path.write_text(
        "\n".join(
            line.rstrip(" \t")
            for line in text.splitlines()
        )
        + "\n",
        encoding="utf-8",
    )


def build_architecture_figure(
    engine_classes,
    ratios,
) -> None:
    ARCHITECTURE_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(14, 8)
    )

    ax.set_xlim(
        0,
        1,
    )

    ax.set_ylim(
        0,
        1,
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        "Artemis II Orion European Service Module Propulsion Architecture",
        fontsize=15,
    )

    box = {
        "boxstyle":
            "round,pad=0.55",

        "fill":
            False,
    }

    by_id = {
        item[
            "engine_class_id"
        ]:
            item
        for item in engine_classes
    }

    main = (
        by_id[
            "main_engine_oms_e"
        ]
    )

    aux = (
        by_id[
            "auxiliary_r4d11"
        ]
    )

    rcs = (
        by_id[
            "reaction_control_system"
        ]
    )

    ax.text(
        0.18,
        0.66,
        (
            "MAIN ENGINE\n"
            f"{main['count']} x OMS-E\n"
            f"{main['nominal_thrust_newtons_each'] / 1000.0:.1f} kN each\n"
            "Gimballed\n"
            "Large velocity changes"
        ),
        ha="center",
        va="center",
        bbox=box,
        fontsize=10,
    )

    ax.text(
        0.50,
        0.66,
        (
            "AUXILIARY\n"
            f"{aux['count']} x R-4D-11\n"
            f"{aux['nominal_thrust_newtons_each']:.0f} N each\n"
            "Fixed\n"
            "Orbital / trajectory corrections\n"
            "Main-engine backup"
        ),
        ha="center",
        va="center",
        bbox=box,
        fontsize=10,
    )

    ax.text(
        0.82,
        0.66,
        (
            "REACTION CONTROL\n"
            f"{rcs['count']} engines\n"
            f"{rcs['pod_count']} pods x "
            f"{rcs['engines_per_pod']}\n"
            f"{rcs['nominal_thrust_newtons_each']:.0f} N each\n"
            "Attitude / fine control"
        ),
        ha="center",
        va="center",
        bbox=box,
        fontsize=10,
    )

    ax.text(
        0.50,
        0.38,
        (
            "33 engines total | 3 propulsion classes\n\n"
            "Per-engine nominal thrust ratios\n"
            f"OMS-E / auxiliary = "
            f"{ratios['main_to_auxiliary']:.3f}x\n"
            f"Auxiliary / RCS = "
            f"{ratios['auxiliary_to_rcs']:.3f}x\n"
            f"OMS-E / RCS = "
            f"{ratios['main_to_rcs']:.3f}x"
        ),
        ha="center",
        va="center",
        fontsize=10,
    )

    ax.text(
        0.50,
        0.14,
        (
            "Architecture context only. "
            "Per-engine thrust ratios are not spacecraft acceleration ratios. "
            "Installed engine count does not imply simultaneous one-direction thrust."
        ),
        ha="center",
        va="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        ARCHITECTURE_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        ARCHITECTURE_FIGURE
    )


def build_selection_figure(
    reference,
) -> None:
    SELECTION_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = [
        [
            "NASA press kit",
            "PREMISSION PLAN",
            "3 outbound corrections",
            "OMS-E",
            "NO",
        ],
        [
            "ESA operations",
            "OPERATIONAL EXPLANATION",
            "Trajectory corrections",
            "Auxiliary / RCS by flight rules",
            "NO",
        ],
        [
            "NASA OTC3",
            "AS-FLOWN REPORT",
            "OTC3",
            "Not identified",
            "UNRESOLVED",
        ],
        [
            "NASA RTC1",
            "AS-FLOWN REPORT",
            "RTC1",
            "\"thrusters\"",
            "UNRESOLVED",
        ],
        [
            "NASA RTC2",
            "AS-FLOWN REPORT",
            "RTC2",
            "\"thrusters\"",
            "UNRESOLVED",
        ],
        [
            "NASA RTC3",
            "AS-FLOWN REPORT",
            "RTC3",
            "\"thrusters\"",
            "UNRESOLVED",
        ],
    ]

    columns = [
        "Evidence",
        "Stage",
        "Scope",
        "Engine wording",
        "Exact as-flown assignment",
    ]

    fig, ax = plt.subplots(
        figsize=(16, 8)
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        "Artemis II Trajectory-Correction Burn-Selection Evidence",
        fontsize=15,
        pad=20,
    )

    table = ax.table(
        cellText=rows,
        colLabels=columns,
        loc="center",
        cellLoc="center",
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        8.5
    )

    table.scale(
        1.0,
        2.0,
    )

    ax.text(
        0.50,
        0.09,
        (
            "NASA premission planning and ESA operational-selection guidance "
            "are preserved as separate evidence layers. "
            "Neither is promoted to a burn-specific as-flown assignment."
        ),
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=8.5,
    )

    ax.text(
        0.50,
        0.035,
        (
            "OTC3, RTC1, RTC2, and RTC3 remain unresolved "
            "until burn-specific public evidence identifies the actual engine class."
        ),
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=8.5,
    )

    fig.tight_layout()

    fig.savefig(
        SELECTION_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        SELECTION_FIGURE
    )


def main() -> None:
    reference = load_json(
        REFERENCE_PATH
    )

    maneuver_reference = load_json(
        MANEUVER_PATH
    )

    if (
        reference.get(
            "dataset_id"
        )
        != (
            "phase2i2_artemis_ii_"
            "esm_propulsion_architecture"
        )
    ):
        fail(
            "Unexpected Phase 2I.2 dataset ID."
        )

    if (
        maneuver_reference.get(
            "dataset_id"
        )
        != (
            "phase2i1_artemis_ii_"
            "maneuver_plan_execution"
        )
    ):
        fail(
            "Unexpected Phase 2I.1 dataset ID."
        )

    architecture = (
        reference[
            "architecture"
        ]
    )

    engine_classes = (
        architecture[
            "engine_classes"
        ]
    )

    if (
        architecture[
            "engine_class_count"
        ]
        != 3
    ):
        fail(
            "Expected three ESM propulsion classes."
        )

    if len(
        engine_classes
    ) != 3:
        fail(
            "Expected three engine-class records."
        )

    by_id = {
        item[
            "engine_class_id"
        ]:
            item
        for item in engine_classes
    }

    expected_ids = {
        "main_engine_oms_e",
        "auxiliary_r4d11",
        "reaction_control_system",
    }

    if set(
        by_id
    ) != expected_ids:
        fail(
            "Unexpected ESM engine-class set."
        )

    main = (
        by_id[
            "main_engine_oms_e"
        ]
    )

    aux = (
        by_id[
            "auxiliary_r4d11"
        ]
    )

    rcs = (
        by_id[
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
            "ESM engine counts changed."
        )

    total_count = (
        main[
            "count"
        ]
        + aux[
            "count"
        ]
        + rcs[
            "count"
        ]
    )

    if (
        total_count
        != 33
        or total_count
        != architecture[
            "total_engine_count"
        ]
    ):
        fail(
            "ESM engine counts no longer sum to 33."
        )

    if (
        rcs[
            "pod_count"
        ]
        * rcs[
            "engines_per_pod"
        ]
        != rcs[
            "count"
        ]
    ):
        fail(
            "RCS pod layout no longer sums to 24."
        )

    if (
        main[
            "nominal_thrust_newtons_each"
        ]
        != 25700.0
    ):
        fail(
            "OMS-E nominal thrust changed."
        )

    if (
        aux[
            "nominal_thrust_newtons_each"
        ]
        != 490.0
    ):
        fail(
            "Auxiliary nominal thrust changed."
        )

    if (
        rcs[
            "nominal_thrust_newtons_each"
        ]
        != 220.0
    ):
        fail(
            "RCS nominal thrust changed."
        )

    if (
        main[
            "gimballed"
        ]
        is not True
    ):
        fail(
            "OMS-E gimbal property changed."
        )

    if (
        aux[
            "display_name"
        ]
        != "R-4D-11 Auxiliary Engine"
    ):
        fail(
            "Auxiliary engine model changed."
        )

    ratios = {
        "main_to_auxiliary":
            (
                main[
                    "nominal_thrust_newtons_each"
                ]
                / aux[
                    "nominal_thrust_newtons_each"
                ]
            ),

        "auxiliary_to_rcs":
            (
                aux[
                    "nominal_thrust_newtons_each"
                ]
                / rcs[
                    "nominal_thrust_newtons_each"
                ]
            ),

        "main_to_rcs":
            (
                main[
                    "nominal_thrust_newtons_each"
                ]
                / rcs[
                    "nominal_thrust_newtons_each"
                ]
            ),
    }

    confirmed = (
        reference[
            "confirmed_as_flown_major_maneuvers"
        ]
    )

    if len(
        confirmed
    ) != 2:
        fail(
            "Expected two confirmed major-maneuver "
            "engine assignments."
        )

    confirmed_by_id = {
        item[
            "maneuver_id"
        ]:
            item
        for item in confirmed
    }

    if set(
        confirmed_by_id
    ) != {
        "perigee_raise",
        "tli",
    }:
        fail(
            "Confirmed major-maneuver set changed."
        )

    perigee = (
        confirmed_by_id[
            "perigee_raise"
        ]
    )

    tli = (
        confirmed_by_id[
            "tli"
        ]
    )

    for item in [
        perigee,
        tli,
    ]:
        if (
            item[
                "engine_class_id"
            ]
            != "main_engine_oms_e"
            or item[
                "assignment_status"
            ]
            != "CONFIRMED_AS_FLOWN"
        ):
            fail(
                "Confirmed main-engine assignment changed."
            )

    if (
        perigee[
            "duration_seconds"
        ]
        != 43.0
    ):
        fail(
            "Perigee-raise duration changed."
        )

    if (
        tli[
            "duration_seconds"
        ]
        != 350.0
    ):
        fail(
            "TLI duration changed."
        )

    selection_evidence = (
        reference[
            "trajectory_correction_selection_evidence"
        ]
    )

    if len(
        selection_evidence
    ) != 2:
        fail(
            "Expected two source-level correction "
            "selection evidence records."
        )

    selection_by_id = {
        item[
            "evidence_id"
        ]:
            item
        for item in selection_evidence
    }

    nasa_plan = (
        selection_by_id[
            "nasa_premission_outbound_oms_plan"
        ]
    )

    esa_operations = (
        selection_by_id[
            "esa_operational_correction_selection"
        ]
    )

    if (
        nasa_plan[
            "engine_selection_claim"
        ]
        != "OMS_E"
    ):
        fail(
            "NASA premission engine claim changed."
        )

    if (
        nasa_plan[
            "burn_specific_as_flown_assignment"
        ]
        is not False
    ):
        fail(
            "NASA premission plan was incorrectly "
            "promoted to as-flown assignment."
        )

    if (
        esa_operations[
            "engine_selection_claim"
        ]
        != (
            "AUXILIARY_OR_RCS_DEPENDING_ON_"
            "REQUIRED_CORRECTION_AND_FLIGHT_RULES"
        )
    ):
        fail(
            "ESA operational selection rule changed."
        )

    if (
        esa_operations[
            "larger_correction_class"
        ]
        != "AUXILIARY"
        or esa_operations[
            "finer_correction_class"
        ]
        != "RCS"
    ):
        fail(
            "ESA larger/finer correction logic changed."
        )

    if (
        esa_operations[
            "burn_specific_as_flown_assignment"
        ]
        is not False
    ):
        fail(
            "ESA operational guidance was incorrectly "
            "promoted to as-flown assignment."
        )

    source_relationship = (
        reference[
            "source_relationship"
        ]
    )

    if (
        source_relationship[
            "treated_as_identical"
        ]
        is not False
        or source_relationship[
            "forced_reconciliation"
        ]
        is not False
        or source_relationship[
            "burn_specific_resolution_available"
        ]
        is not False
    ):
        fail(
            "Source-evidence boundary changed."
        )

    maneuver_by_id = {
        item[
            "maneuver_id"
        ]:
            item
        for item in maneuver_reference[
            "maneuvers"
        ]
    }

    corrections = (
        reference[
            "correction_burn_assignments"
        ]
    )

    expected_corrections = [
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
    ] != expected_corrections:
        fail(
            "Correction-burn assignment order changed."
        )

    unresolved_count = 0

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
            or item[
                "as_flown_engine_class_id"
            ]
            is not None
        ):
            fail(
                f"{maneuver_id} gained unsupported "
                "engine assignment."
            )

        unresolved_count += 1

        phase2i1_execution = (
            maneuver_by_id[
                maneuver_id
            ][
                "execution"
            ]
        )

        if abs(
            float(
                item[
                    "duration_seconds"
                ]
            )
            - float(
                phase2i1_execution[
                    "duration_seconds"
                ]
            )
        ) > 1e-9:
            fail(
                f"{maneuver_id} duration no longer "
                "matches Phase 2I.1."
            )

        expected_dv = (
            phase2i1_execution.get(
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
                    f"{maneuver_id} gained unsupported delta-v."
                )
        else:
            if abs(
                float(observed_dv)
                - float(expected_dv)
            ) > 1e-9:
                fail(
                    f"{maneuver_id} delta-v no longer "
                    "matches Phase 2I.1."
                )

    if unresolved_count != 4:
        fail(
            "Expected four unresolved as-flown "
            "correction assignments."
        )

    selection_boundary = (
        reference[
            "selection_boundary"
        ]
    )

    if (
        selection_boundary[
            "flight_rules_influence_engine_selection"
        ]
        is not True
        or selection_boundary[
            "required_correction_influences_engine_selection"
        ]
        is not True
    ):
        fail(
            "Public engine-selection logic changed."
        )

    if (
        selection_boundary[
            "exact_public_selection_thresholds_available"
        ]
        is not False
        or selection_boundary[
            "exact_public_selection_algorithm_available"
        ]
        is not False
    ):
        fail(
            "Unsupported public selection algorithm "
            "or thresholds were introduced."
        )

    for maneuver_id in expected_corrections:
        key = (
            f"{maneuver_id}_exact_engine_"
            "assignment_available"
        )

        if (
            selection_boundary[
                key
            ]
            is not False
        ):
            fail(
                f"{maneuver_id} exact assignment "
                "incorrectly marked available."
            )

    ARCHITECTURE_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    architecture_fields = [
        "engine_class_id",
        "display_name",
        "short_name",
        "count",
        "nominal_thrust_newtons_each",
        "gimballed",
        "fixed",
        "primary_role",
    ]

    with ARCHITECTURE_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=architecture_fields,
        )

        writer.writeheader()

        for item in engine_classes:
            writer.writerow(
                {
                    "engine_class_id":
                        item[
                            "engine_class_id"
                        ],

                    "display_name":
                        item[
                            "display_name"
                        ],

                    "short_name":
                        item[
                            "short_name"
                        ],

                    "count":
                        item[
                            "count"
                        ],

                    "nominal_thrust_newtons_each":
                        item[
                            "nominal_thrust_newtons_each"
                        ],

                    "gimballed":
                        str(
                            item[
                                "gimballed"
                            ]
                        ).lower(),

                    "fixed":
                        str(
                            item[
                                "fixed"
                            ]
                        ).lower(),

                    "primary_role":
                        item[
                            "primary_role"
                        ],
                }
            )

    selection_rows = [
        {
            "evidence_id":
                nasa_plan[
                    "evidence_id"
                ],
            "organization":
                nasa_plan[
                    "organization"
                ],
            "evidence_stage":
                nasa_plan[
                    "evidence_stage"
                ],
            "scope":
                nasa_plan[
                    "scope"
                ],
            "engine_claim":
                nasa_plan[
                    "engine_selection_claim"
                ],
            "assignment_status":
                "NOT_AS_FLOWN_ASSIGNMENT",
        },
        {
            "evidence_id":
                esa_operations[
                    "evidence_id"
                ],
            "organization":
                esa_operations[
                    "organization"
                ],
            "evidence_stage":
                esa_operations[
                    "evidence_stage"
                ],
            "scope":
                esa_operations[
                    "scope"
                ],
            "engine_claim":
                esa_operations[
                    "engine_selection_claim"
                ],
            "assignment_status":
                "NOT_AS_FLOWN_ASSIGNMENT",
        },
    ]

    for item in corrections:
        selection_rows.append(
            {
                "evidence_id":
                    (
                        "as_flown_"
                        + item[
                            "maneuver_id"
                        ]
                    ),
                "organization":
                    "NASA",
                "evidence_stage":
                    "AS_FLOWN_REPORT",
                "scope":
                    item[
                        "maneuver_id"
                    ].upper(),
                "engine_claim":
                    item[
                        "as_flown_wording"
                    ],
                "assignment_status":
                    item[
                        "assignment_status"
                    ],
            }
        )

    selection_fields = [
        "evidence_id",
        "organization",
        "evidence_stage",
        "scope",
        "engine_claim",
        "assignment_status",
    ]

    with SELECTION_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=selection_fields,
        )

        writer.writeheader()
        writer.writerows(
            selection_rows
        )

    build_architecture_figure(
        engine_classes,
        ratios,
    )

    build_selection_figure(
        reference
    )

    stage_counts = Counter(
        row[
            "evidence_stage"
        ]
        for row in selection_rows
    )

    summary = {
        "product_id":
            (
                "phase2i2_esm_propulsion_"
                "architecture_analysis"
            ),

        "mission":
            "Artemis II",

        "reference_dataset_id":
            reference[
                "dataset_id"
            ],

        "architecture": {
            "engine_class_count":
                architecture[
                    "engine_class_count"
                ],

            "total_engine_count":
                architecture[
                    "total_engine_count"
                ],

            "main_engine_count":
                main[
                    "count"
                ],

            "auxiliary_engine_count":
                aux[
                    "count"
                ],

            "rcs_engine_count":
                rcs[
                    "count"
                ],

            "rcs_pod_count":
                rcs[
                    "pod_count"
                ],

            "rcs_engines_per_pod":
                rcs[
                    "engines_per_pod"
                ],
        },

        "nominal_per_engine_thrust": {
            "main_newtons":
                main[
                    "nominal_thrust_newtons_each"
                ],

            "auxiliary_newtons":
                aux[
                    "nominal_thrust_newtons_each"
                ],

            "rcs_newtons":
                rcs[
                    "nominal_thrust_newtons_each"
                ],
        },

        "derived_per_engine_thrust_ratios":
            ratios,

        "confirmed_as_flown_major_maneuvers": {
            "count":
                len(confirmed),

            "maneuvers": [
                item[
                    "maneuver_id"
                ]
                for item in confirmed
            ],

            "engine_class":
                "main_engine_oms_e",
        },

        "correction_selection_evidence": {
            "nasa_premission_claim":
                nasa_plan[
                    "engine_selection_claim"
                ],

            "esa_operational_claim":
                esa_operations[
                    "engine_selection_claim"
                ],

            "source_relationship_classification":
                source_relationship[
                    "classification"
                ],

            "forced_reconciliation":
                False,
        },

        "as_flown_correction_assignments": {
            "count":
                len(corrections),

            "resolved_count":
                0,

            "unresolved_count":
                unresolved_count,

            "maneuver_ids":
                expected_corrections,
        },

        "evidence_stage_counts":
            dict(
                stage_counts
            ),

        "selection_boundary":
            selection_boundary,

        "derived_metric_policy":
            reference[
                "derived_metric_policy"
            ],

        "guardrails":
            reference[
                "guardrails"
            ],

        "outputs": {
            "architecture_csv":
                str(
                    ARCHITECTURE_CSV.relative_to(
                        ROOT
                    )
                ),

            "selection_evidence_csv":
                str(
                    SELECTION_CSV.relative_to(
                        ROOT
                    )
                ),

            "architecture_figure":
                str(
                    ARCHITECTURE_FIGURE.relative_to(
                        ROOT
                    )
                ),

            "selection_evidence_figure":
                str(
                    SELECTION_FIGURE.relative_to(
                        ROOT
                    )
                ),
        },
    }

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary,
            f,
            indent=2,
        )

    print()
    print(
        "Phase 2I.2 ESM Propulsion Architecture / "
        "Burn-Selection Analysis"
    )

    print("=" * 68)

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

    print()
    print(
        "  OMS-E:"
    )

    print(
        "    count: 1"
    )

    print(
        "    nominal thrust: 25.7 kN"
    )

    print(
        "    gimballed: TRUE"
    )

    print()
    print(
        "  Auxiliary:"
    )

    print(
        "    count: 8"
    )

    print(
        "    model: R-4D-11"
    )

    print(
        "    nominal thrust each: 490 N"
    )

    print()
    print(
        "  RCS:"
    )

    print(
        "    count: 24"
    )

    print(
        "    arrangement: 6 pods x 4"
    )

    print(
        "    nominal thrust each: 220 N"
    )

    print()
    print(
        "Derived per-engine thrust ratios:"
    )

    print(
        "  main / auxiliary:"
    )

    print(
        f"    {ratios['main_to_auxiliary']:.3f}x"
    )

    print(
        "  auxiliary / RCS:"
    )

    print(
        f"    {ratios['auxiliary_to_rcs']:.3f}x"
    )

    print(
        "  main / RCS:"
    )

    print(
        f"    {ratios['main_to_rcs']:.3f}x"
    )

    print(
        "  interpretation:"
    )

    print(
        "    ARCHITECTURE CONTEXT ONLY"
    )

    print()
    print(
        "Confirmed as-flown major maneuvers:"
    )

    print(
        "  perigee raise:"
    )

    print(
        "    MAIN_ENGINE_OMS_E"
    )

    print(
        "    43.0 s"
    )

    print(
        "  TLI:"
    )

    print(
        "    MAIN_ENGINE_OMS_E"
    )

    print(
        "    350.0 s"
    )

    print()
    print(
        "Correction-selection evidence:"
    )

    print(
        "  NASA premission:"
    )

    print(
        "    outbound corrections -> OMS-E"
    )

    print(
        "    as-flown assignment: FALSE"
    )

    print()
    print(
        "  ESA operational explanation:"
    )

    print(
        "    larger corrections -> AUXILIARY"
    )

    print(
        "    finer corrections -> RCS"
    )

    print(
        "    selected by flight rules / required correction"
    )

    print(
        "    as-flown assignment: FALSE"
    )

    print()
    print(
        "Source relationship:"
    )

    print(
        "  "
        f"{source_relationship['classification']}"
    )

    print(
        "  forced reconciliation: FALSE"
    )

    print()
    print(
        "As-flown trajectory corrections:"
    )

    for item in corrections:
        print(
            f"  {item['maneuver_id'].upper()}: "
            "UNRESOLVED_AS_FLOWN"
        )

    print()
    print(
        "Assignment totals:"
    )

    print(
        "  correction burns: 4"
    )

    print(
        "  resolved: 0"
    )

    print(
        "  unresolved: 4"
    )

    print()
    print(
        "Selection boundary:"
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
        "Wrote:"
    )

    print(
        "  "
        f"{ARCHITECTURE_CSV.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{SELECTION_CSV.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{SUMMARY_PATH.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{ARCHITECTURE_FIGURE.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{SELECTION_FIGURE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_mission_control_perspectives.json"
)

PROCESSED_PATH = (
    ROOT
    / "data"
    / "processed"
    / "mission_control"
    / "artemis_ii_mission_control_perspectives.json"
)

TIMELINE_CSV = (
    ROOT
    / "data"
    / "processed"
    / "mission_control"
    / "artemis_ii_discipline_prioritized_timeline.csv"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "mission_control"
    / "phase7a_discipline_priority_matrix.svg"
)


EXPECTED_DATASET_ID = (
    "phase7a_artemis_ii_"
    "mission_control_perspectives"
)

EXPECTED_DISCIPLINES = [
    "FLIGHT",
    "FDO",
    "FAO",
    "EECOM",
    "COMM",
    "SCIENCE",
    "ENGINEERING_SUPPORT",
]

EXPECTED_ROLE_TYPES = {
    "FLIGHT": (
        "OFFICIAL_MISSION_CONTROL_ROLE_"
        "USED_AS_MISSIONLAB_LENS"
    ),
    "FDO": (
        "OFFICIAL_MISSION_CONTROL_ROLE_"
        "USED_AS_MISSIONLAB_LENS"
    ),
    "FAO": (
        "OFFICIAL_MISSION_CONTROL_ROLE_"
        "USED_AS_MISSIONLAB_LENS"
    ),
    "EECOM": (
        "ORION_FLIGHT_CONTROL_ROLE_"
        "USED_AS_MISSIONLAB_LENS"
    ),
    "COMM": (
        "MISSIONLAB_ANALYTICAL_LENS"
    ),
    "SCIENCE": (
        "OFFICIAL_ARTEMIS_II_CONSOLE_ROLE_"
        "USED_AS_MISSIONLAB_LENS"
    ),
    "ENGINEERING_SUPPORT": (
        "MISSIONLAB_ANALYTICAL_LENS"
    ),
}

EXPECTED_HIGH_VALUE_PRIMARY = {
    "A2_UWMS_FD4_VENT_ISSUE": [
        "FLIGHT",
        "FAO",
        "EECOM",
        "ENGINEERING_SUPPORT",
    ],
    "A2_OTC3": [
        "FLIGHT",
        "FDO",
        "FAO",
    ],
    "A2_PERICYNTHION": [
        "FLIGHT",
        "FDO",
        "COMM",
        "SCIENCE",
    ],
    "A2_TOTAL_SOLAR_ECLIPSE": [
        "FDO",
        "FAO",
        "SCIENCE",
    ],
    "A2_RETURN_LINK_LOSS": [
        "FLIGHT",
        "FAO",
        "COMM",
        "ENGINEERING_SUPPORT",
    ],
    "A2_RTC2": [
        "FLIGHT",
        "FDO",
        "FAO",
        "COMM",
        "ENGINEERING_SUPPORT",
    ],
    "A2_ENTRY_INTERFACE": [
        "FLIGHT",
        "FDO",
        "FAO",
        "EECOM",
        "COMM",
        "ENGINEERING_SUPPORT",
    ],
    "A2_SPLASHDOWN": [
        "FLIGHT",
        "FAO",
        "EECOM",
        "ENGINEERING_SUPPORT",
    ],
}

EXPECTED_CSV_COLUMNS = [
    "order",
    "event_id",
    "name",
    "timestamp_utc",
    "date_utc",
    "met",
    "time_precision",
    "evidence_class",
    "classification",
    "source_dependency",
    "primary_lenses",
    "FLIGHT_priority",
    "FDO_priority",
    "FAO_priority",
    "EECOM_priority",
    "COMM_priority",
    "SCIENCE_priority",
    "ENGINEERING_SUPPORT_priority",
    "summary",
]


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 7A VALIDATION FAILED: "
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
    require(
        path.exists(),
        f"missing JSON file: {path}",
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
    require(
        path.exists(),
        f"missing CSV file: {path}",
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


def normalize_path(
    value: str,
) -> str:
    return value.replace(
        "\\",
        "/",
    )


def discipline_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "discipline_id"
        ]: item
        for item
        in result[
            "discipline_registry"
        ]
    }


def event_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "event_id"
        ]: item
        for item
        in result[
            "shared_timeline"
        ]
    }


def validate_identity(
    reference: dict,
    processed: dict,
):
    require(
        reference
        == processed,
        (
            "reference and processed "
            "Phase 7A manifests differ"
        ),
    )

    require(
        reference.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "Phase 7A dataset identity mismatch",
    )

    require(
        reference.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        reference.get(
            "phase"
        )
        == "7A",
        "phase identity mismatch",
    )

    require(
        reference.get(
            "status"
        )
        == (
            "DISCIPLINE_LENSES_AND_"
            "SHARED_TIMELINE_COMPLETE"
        ),
        "Phase 7A status mismatch",
    )


def validate_role_sources(
    result: dict,
):
    sources = result[
        "role_source_registry"
    ]

    require(
        len(
            sources
        )
        == 4,
        (
            "expected 4 public role sources, "
            f"found {len(sources)}"
        ),
    )

    source_ids = [
        item[
            "source_id"
        ]
        for item
        in sources
    ]

    require(
        len(
            source_ids
        )
        == len(
            set(
                source_ids
            )
        ),
        "duplicate role-source IDs",
    )

    expected_ids = {
        "NASA_JSC_MISSION_CONTROL_CENTER",
        "NASA_ARTEMIS_I_MCC_AT_A_GLANCE",
        "NASA_ARTEMIS_II_SCIENCE_OFFICERS",
        "NASA_ARTEMIS_II_MISSION_MASTERMINDS",
    }

    require(
        set(
            source_ids
        )
        == expected_ids,
        "role-source registry mismatch",
    )


def validate_disciplines(
    result: dict,
):
    roles = result[
        "discipline_registry"
    ]

    require(
        len(
            roles
        )
        == 7,
        (
            "expected 7 discipline lenses, "
            f"found {len(roles)}"
        ),
    )

    ids = [
        item[
            "discipline_id"
        ]
        for item
        in roles
    ]

    require(
        ids
        == EXPECTED_DISCIPLINES,
        "discipline registry ordering mismatch",
    )

    index = discipline_index(
        result
    )

    for discipline in EXPECTED_DISCIPLINES:
        require(
            index[
                discipline
            ][
                "role_type"
            ]
            == EXPECTED_ROLE_TYPES[
                discipline
            ],
            (
                "role type mismatch for "
                f"{discipline}"
            ),
        )

        require(
            len(
                index[
                    discipline
                ][
                    "missionlab_focus"
                ]
            )
            > 0,
            (
                "empty MissionLab focus for "
                f"{discipline}"
            ),
        )

        require(
            len(
                index[
                    discipline
                ][
                    "primary_questions"
                ]
            )
            > 0,
            (
                "empty primary-question set for "
                f"{discipline}"
            ),
        )


def validate_priority_scale(
    result: dict,
):
    require(
        result[
            "priority_scale"
        ]
        == {
            "0": "CONTEXT",
            "1": "AWARENESS",
            "2": "HIGH",
            "3": "PRIMARY",
        },
        "priority scale mismatch",
    )


def validate_dependencies(
    result: dict,
):
    dependencies = result[
        "input_dependencies"
    ]

    require(
        len(
            dependencies
        )
        == 6,
        (
            "expected 6 phase dependencies, "
            f"found {len(dependencies)}"
        ),
    )

    ids = [
        item[
            "dependency_id"
        ]
        for item
        in dependencies
    ]

    expected = [
        "PHASE2_INTEGRATED_OPERATIONS",
        "WASTE_MANAGEMENT_EVIDENCE",
        "TPS_EVIDENCE",
        "PHASE4_ENTRY_RECOVERY_EVIDENCE",
        "PHASE5_RADIATION_INTERFACE",
        "PHASE6_LUNAR_OBSERVATIONS",
    ]

    require(
        ids
        == expected,
        "dependency registry mismatch",
    )

    for item in dependencies:
        require(
            item[
                "dataset_id"
            ],
            (
                "dependency missing dataset ID: "
                f"{item['dependency_id']}"
            ),
        )

        require(
            item[
                "path"
            ].startswith(
                "data/reference/"
            ),
            (
                "dependency path not in "
                f"reference registry: {item['dependency_id']}"
            ),
        )


def validate_timeline(
    result: dict,
):
    events = result[
        "shared_timeline"
    ]

    require(
        len(
            events
        )
        == 24,
        (
            "expected 24 timeline events, "
            f"found {len(events)}"
        ),
    )

    orders = [
        item[
            "order"
        ]
        for item
        in events
    ]

    require(
        orders
        == list(
            range(
                1,
                25,
            )
        ),
        "timeline order is not contiguous 1-24",
    )

    ids = [
        item[
            "event_id"
        ]
        for item
        in events
    ]

    require(
        len(
            ids
        )
        == len(
            set(
                ids
            )
        ),
        "duplicate timeline event IDs",
    )

    for event in events:
        require(
            set(
                event[
                    "priorities"
                ].keys()
            )
            == set(
                EXPECTED_DISCIPLINES
            ),
            (
                "incomplete priority registry for "
                f"{event['event_id']}"
            ),
        )

        require(
            set(
                event[
                    "priority_labels"
                ].keys()
            )
            == set(
                EXPECTED_DISCIPLINES
            ),
            (
                "incomplete priority-label registry for "
                f"{event['event_id']}"
            ),
        )

        for discipline in EXPECTED_DISCIPLINES:
            value = event[
                "priorities"
            ][
                discipline
            ]

            require(
                value
                in {
                    0,
                    1,
                    2,
                    3,
                },
                (
                    "invalid priority value for "
                    f"{event['event_id']} / {discipline}"
                ),
            )

    untimed_events = [
        event
        for event
        in events
        if event[
            "timestamp_utc"
        ]
        is None
    ]

    require(
        len(
            untimed_events
        )
        > 0,
        "expected untimed public events",
    )

    for event in untimed_events:
        require(
            event[
                "met"
            ]
            is None,
            (
                "untimed event was assigned fabricated MET: "
                f"{event['event_id']}"
            ),
        )


def validate_high_value_anchors(
    result: dict,
):
    index = event_index(
        result
    )

    for (
        event_id,
        expected_lenses,
    ) in EXPECTED_HIGH_VALUE_PRIMARY.items():
        require(
            event_id
            in index,
            (
                "missing high-value anchor: "
                f"{event_id}"
            ),
        )

        require(
            index[
                event_id
            ][
                "primary_lenses"
            ]
            == expected_lenses,
            (
                "primary-lens mismatch for "
                f"{event_id}"
            ),
        )


def validate_selected_event_boundaries(
    result: dict,
):
    index = event_index(
        result
    )

    require(
        index[
            "A2_LAUNCH"
        ][
            "timestamp_utc"
        ]
        == "2026-04-01T22:35:12Z",
        "launch timestamp mismatch",
    )

    require(
        index[
            "A2_OTC3"
        ][
            "timestamp_utc"
        ]
        == "2026-04-06T03:03:00Z",
        "OTC3 timestamp mismatch",
    )

    require(
        index[
            "A2_PERICYNTHION"
        ][
            "timestamp_utc"
        ]
        == "2026-04-06T23:00:46.177998Z",
        "pericynthion timestamp mismatch",
    )

    require(
        index[
            "A2_TOTAL_SOLAR_ECLIPSE"
        ][
            "timestamp_utc"
        ]
        == "2026-04-07T00:34:27.220Z",
        "solar-eclipse start mismatch",
    )

    require(
        index[
            "A2_TOTAL_SOLAR_ECLIPSE"
        ][
            "end_timestamp_utc"
        ]
        == "2026-04-07T01:28:53.125Z",
        "solar-eclipse stop mismatch",
    )

    require(
        index[
            "A2_RETURN_LINK_LOSS"
        ][
            "time_precision"
        ]
        == "APPROXIMATE_PUBLIC_ANCHOR",
        "return-link timing boundary mismatch",
    )

    require(
        index[
            "A2_ENTRY_BLACKOUT"
        ][
            "timestamp_utc"
        ]
        is None,
        (
            "entry blackout was assigned "
            "fabricated exact UTC"
        ),
    )

    require(
        index[
            "A2_SPLASHDOWN"
        ][
            "timestamp_utc"
        ]
        == "2026-04-11T00:07:00Z",
        "splashdown timestamp mismatch",
    )


def validate_discipline_views(
    result: dict,
):
    views = result[
        "discipline_prioritized_views"
    ]

    require(
        list(
            views.keys()
        )
        == EXPECTED_DISCIPLINES,
        "discipline prioritized-view registry mismatch",
    )

    for discipline in EXPECTED_DISCIPLINES:
        records = views[
            discipline
        ]

        require(
            len(
                records
            )
            > 0,
            (
                "empty prioritized view for "
                f"{discipline}"
            ),
        )

        for record in records:
            require(
                record[
                    "priority"
                ]
                >= 1,
                (
                    "context-only event leaked into "
                    f"{discipline} prioritized view"
                ),
            )

        priorities = [
            record[
                "priority"
            ]
            for record
            in records
        ]

        require(
            priorities
            == sorted(
                priorities,
                reverse=True,
            ),
            (
                "prioritized view not sorted by "
                f"priority for {discipline}"
            ),
        )


def validate_integration_policy(
    result: dict,
):
    policy = result[
        "integration_policy"
    ]

    expected_true = [
        "shared_evidence_spine_required",
        "discipline_priorities_are_missionlab_synthesis",
        "derived_geometry_separated_from_reported_events",
        "date_only_events_not_given_fabricated_utc",
    ]

    expected_false = [
        "discipline_priorities_are_nasa_console_logs",
        "discipline_priority_implies_controller_action",
        "official_role_definition_implies_exact_artemis_ii_staffing",
        "comm_lens_claimed_as_exact_console_call_sign",
        "engineering_support_claimed_as_single_console_call_sign",
    ]

    for key in expected_true:
        require(
            policy[
                key
            ]
            is True,
            (
                "integration policy expected TRUE: "
                f"{key}"
            ),
        )

    for key in expected_false:
        require(
            policy[
                key
            ]
            is False,
            (
                "integration policy expected FALSE: "
                f"{key}"
            ),
        )


def validate_non_equivalences(
    result: dict,
):
    items = result[
        "critical_non_equivalences"
    ]

    expected_pairs = [
        (
            "MISSIONLAB_DISCIPLINE_PRIORITY",
            "NASA_PRIVATE_CONSOLE_ACTION",
        ),
        (
            "MISSIONLAB_DISCIPLINE_LENS",
            "EXACT_ARTEMIS_II_CONSOLE_STAFFING",
        ),
        (
            "PUBLIC_EVENT_SEQUENCE",
            "COMPLETE_FLIGHT_LOOP_HISTORY",
        ),
        (
            "CROSS_DISCIPLINE_RELEVANCE",
            "DECISION_AUTHORITY",
        ),
        (
            "EXPECTED_COMMUNICATIONS_CONSTRAINT",
            "COMMUNICATIONS_ANOMALY",
        ),
        (
            "PUBLIC_TROUBLESHOOTING_ACTION",
            "CONFIRMED_ROOT_CAUSE",
        ),
        (
            "MISSIONLAB_DERIVED_GEOMETRY",
            "ONBOARD_TELEMETRY",
        ),
    ]

    require(
        len(
            items
        )
        == 7,
        (
            "expected 7 critical non-equivalences, "
            f"found {len(items)}"
        ),
    )

    actual_pairs = [
        (
            item[
                "left"
            ],
            item[
                "right"
            ],
        )
        for item
        in items
    ]

    require(
        actual_pairs
        == expected_pairs,
        "critical non-equivalence registry mismatch",
    )

    for item in items:
        require(
            item[
                "equivalent"
            ]
            is False,
            (
                "critical non-equivalence "
                "incorrectly marked equivalent"
            ),
        )


def validate_roadmap(
    result: dict,
):
    roadmap = result[
        "roadmap_assessment"
    ]

    for key in [
        "flight_lens",
        "fdo_lens",
        "fao_lens",
        "eecom_lens",
        "comm_lens",
        "science_lens",
        "engineering_support_lens",
    ]:
        require(
            roadmap[
                key
            ]
            == "COMPLETE",
            f"{key} is not complete",
        )

    require(
        roadmap[
            "shared_timeline_with_discipline_prioritization"
        ]
        == "COMPLETE",
        (
            "shared prioritized timeline "
            "is not complete"
        ),
    )

    require(
        roadmap[
            "decision_threads"
        ]
        == "PENDING_PHASE7B",
        (
            "decision threads incorrectly "
            "marked complete in 7A"
        ),
    )

    require(
        roadmap[
            "postflight_engineering_timeline"
        ]
        == "PENDING_PHASE7B",
        (
            "postflight engineering timeline "
            "incorrectly marked complete in 7A"
        ),
    )


def validate_csv(
    rows: list[dict],
):
    require(
        len(
            rows
        )
        == 24,
        (
            "timeline CSV expected 24 rows, "
            f"found {len(rows)}"
        ),
    )

    require(
        list(
            rows[
                0
            ].keys()
        )
        == EXPECTED_CSV_COLUMNS,
        "timeline CSV schema mismatch",
    )

    orders = [
        int(
            row[
                "order"
            ]
        )
        for row
        in rows
    ]

    require(
        orders
        == list(
            range(
                1,
                25,
            )
        ),
        "timeline CSV order mismatch",
    )

    ids = [
        row[
            "event_id"
        ]
        for row
        in rows
    ]

    require(
        len(
            ids
        )
        == len(
            set(
                ids
            )
        ),
        "duplicate timeline CSV event IDs",
    )

    priority_columns = [
        "FLIGHT_priority",
        "FDO_priority",
        "FAO_priority",
        "EECOM_priority",
        "COMM_priority",
        "SCIENCE_priority",
        "ENGINEERING_SUPPORT_priority",
    ]

    for row in rows:
        for column in priority_columns:
            value = int(
                row[
                    column
                ]
            )

            require(
                value
                in {
                    0,
                    1,
                    2,
                    3,
                },
                (
                    "invalid timeline CSV priority "
                    f"{value} in {column}"
                ),
            )


def validate_outputs(
    result: dict,
):
    outputs = result[
        "outputs"
    ]

    require(
        normalize_path(
            outputs[
                "reference_json"
            ]
        )
        == (
            "data/reference/"
            "artemis_ii_mission_control_perspectives.json"
        ),
        "reference output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "processed_json"
            ]
        )
        == (
            "data/processed/mission_control/"
            "artemis_ii_mission_control_perspectives.json"
        ),
        "processed output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "timeline_csv"
            ]
        )
        == (
            "data/processed/mission_control/"
            "artemis_ii_discipline_prioritized_timeline.csv"
        ),
        "timeline CSV output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "figure"
            ]
        )
        == (
            "docs/assets/mission_control/"
            "phase7a_discipline_priority_matrix.svg"
        ),
        "figure output path mismatch",
    )


def validate_figure():
    require(
        FIGURE_PATH.exists(),
        f"missing Phase 7A figure: {FIGURE_PATH}",
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 7A figure is empty",
    )

    content = FIGURE_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    require(
        "<svg"
        in content,
        "Phase 7A figure is not SVG",
    )


def main():
    print()
    print(
        "Phase 7A Artemis II Mission Control "
        "Discipline Perspectives Validation"
    )
    print(
        "=" * 72
    )

    reference = load_json(
        REFERENCE_PATH
    )

    processed = load_json(
        PROCESSED_PATH
    )

    timeline_rows = load_csv(
        TIMELINE_CSV
    )

    validate_identity(
        reference,
        processed,
    )

    print()
    print(
        "Analysis identity: PASS"
    )
    print(
        "Reference / processed manifest consistency: PASS"
    )

    validate_role_sources(
        reference
    )

    print()
    print(
        "4 public role sources: PASS"
    )
    print(
        "NASA mission-control role grounding: PASS"
    )

    validate_disciplines(
        reference
    )

    print()
    print(
        "7 discipline lenses: PASS"
    )
    print(
        "FLIGHT role classification: PASS"
    )
    print(
        "FDO role classification: PASS"
    )
    print(
        "FAO role classification: PASS"
    )
    print(
        "EECOM role classification: PASS"
    )
    print(
        "COMM analytical-lens boundary: PASS"
    )
    print(
        "SCIENCE Artemis II console classification: PASS"
    )
    print(
        "ENGINEERING_SUPPORT analytical-lens boundary: PASS"
    )

    validate_priority_scale(
        reference
    )

    print()
    print(
        "4-level priority scale: PASS"
    )

    validate_dependencies(
        reference
    )

    print()
    print(
        "6 cross-phase dependencies: PASS"
    )

    validate_timeline(
        reference
    )

    print()
    print(
        "24 shared-timeline events: PASS"
    )
    print(
        "Contiguous event ordering: PASS"
    )
    print(
        "Timeline event-ID uniqueness: PASS"
    )
    print(
        "Complete 7-discipline priority registry: PASS"
    )
    print(
        "No fabricated UTC for untimed events: PASS"
    )
    print(
        "No fabricated MET for untimed events: PASS"
    )

    validate_high_value_anchors(
        reference
    )

    print()
    print(
        "Waste-system cross-discipline anchor: PASS"
    )
    print(
        "OTC3 cross-discipline anchor: PASS"
    )
    print(
        "Pericynthion cross-discipline anchor: PASS"
    )
    print(
        "Solar-eclipse cross-discipline anchor: PASS"
    )
    print(
        "Return-link anomaly cross-discipline anchor: PASS"
    )
    print(
        "RTC2 cross-discipline anchor: PASS"
    )
    print(
        "Entry Interface cross-discipline anchor: PASS"
    )
    print(
        "Splashdown cross-discipline anchor: PASS"
    )

    validate_selected_event_boundaries(
        reference
    )

    print()
    print(
        "Mission-clock anchor preservation: PASS"
    )
    print(
        "Derived lunar geometry preservation: PASS"
    )
    print(
        "Approximate return-link timing boundary: PASS"
    )
    print(
        "Entry-blackout exact-time non-inference: PASS"
    )

    validate_discipline_views(
        reference
    )

    print()
    print(
        "FLIGHT prioritized view: PASS"
    )
    print(
        "FDO prioritized view: PASS"
    )
    print(
        "FAO prioritized view: PASS"
    )
    print(
        "EECOM prioritized view: PASS"
    )
    print(
        "COMM prioritized view: PASS"
    )
    print(
        "SCIENCE prioritized view: PASS"
    )
    print(
        "ENGINEERING_SUPPORT prioritized view: PASS"
    )

    validate_integration_policy(
        reference
    )

    print()
    print(
        "MissionLab-priority / console-action boundary: PASS"
    )
    print(
        "Analytical-lens / staffing-record boundary: PASS"
    )
    print(
        "COMM call-sign non-claim: PASS"
    )
    print(
        "ENGINEERING_SUPPORT call-sign non-claim: PASS"
    )
    print(
        "Derived-geometry / reported-event separation: PASS"
    )

    validate_non_equivalences(
        reference
    )

    print()
    print(
        "7 critical non-equivalences: PASS"
    )
    print(
        "Priority / private-console-action boundary: PASS"
    )
    print(
        "Lens / exact-staffing boundary: PASS"
    )
    print(
        "Public-sequence / full-loop-history boundary: PASS"
    )
    print(
        "Cross-discipline relevance / authority boundary: PASS"
    )
    print(
        "Expected-constraint / anomaly boundary: PASS"
    )
    print(
        "Troubleshooting-action / root-cause boundary: PASS"
    )
    print(
        "Derived-geometry / telemetry boundary: PASS"
    )

    validate_roadmap(
        reference
    )

    print()
    print(
        "FLIGHT roadmap lens: PASS"
    )
    print(
        "FDO roadmap lens: PASS"
    )
    print(
        "FAO roadmap lens: PASS"
    )
    print(
        "EECOM roadmap lens: PASS"
    )
    print(
        "COMM roadmap lens: PASS"
    )
    print(
        "SCIENCE roadmap lens: PASS"
    )
    print(
        "ENGINEERING_SUPPORT roadmap lens: PASS"
    )
    print(
        "Shared discipline-prioritized timeline: PASS"
    )
    print(
        "Decision threads correctly left to 7B: PASS"
    )
    print(
        "Postflight engineering timeline correctly left to 7B: PASS"
    )

    validate_csv(
        timeline_rows
    )

    print()
    print(
        "Discipline-prioritized timeline CSV: PASS"
    )
    print(
        "Timeline CSV schema: PASS"
    )
    print(
        "Timeline CSV priority values: PASS"
    )

    validate_outputs(
        reference
    )

    validate_figure()

    print()
    print(
        "Documentation figure: PASS"
    )

    print()
    print(
        "Validated Phase 7A totals:"
    )
    print(
        "  discipline lenses: 7"
    )
    print(
        "  public role sources: 4"
    )
    print(
        "  shared-timeline events: 24"
    )
    print(
        "  cross-phase dependencies: 6"
    )
    print(
        "  priority levels: 4"
    )
    print(
        "  critical non-equivalences: 7"
    )

    print()
    print(
        "Validated role boundaries:"
    )
    print(
        "  FLIGHT: official role used as analytical lens"
    )
    print(
        "  FDO: official role used as analytical lens"
    )
    print(
        "  FAO: official role used as analytical lens"
    )
    print(
        "  EECOM: Orion flight-control role used as lens"
    )
    print(
        "  COMM: MissionLab analytical lens"
    )
    print(
        "  SCIENCE: official Artemis II console role used as lens"
    )
    print(
        "  ENGINEERING_SUPPORT: MissionLab analytical lens"
    )

    print()
    print(
        "Phase 7A status:"
    )
    print(
        "  FLIGHT lens: COMPLETE"
    )
    print(
        "  FDO lens: COMPLETE"
    )
    print(
        "  FAO lens: COMPLETE"
    )
    print(
        "  EECOM lens: COMPLETE"
    )
    print(
        "  COMM lens: COMPLETE"
    )
    print(
        "  SCIENCE lens: COMPLETE"
    )
    print(
        "  ENGINEERING_SUPPORT lens: COMPLETE"
    )
    print(
        "  shared prioritized timeline: COMPLETE"
    )
    print(
        "  decision-thread synthesis: PENDING 7B"
    )
    print(
        "  postflight engineering timeline: PENDING 7B"
    )

    print()
    print(
        "PHASE 7A VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
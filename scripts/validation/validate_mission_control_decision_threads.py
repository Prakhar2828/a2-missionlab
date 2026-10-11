from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_decision_threads.json"
)

PROCESSED_PATH = (
    ROOT
    / "data"
    / "processed"
    / "mission_control"
    / "artemis_ii_decision_threads.json"
)

THREAD_CSV = (
    ROOT
    / "data"
    / "processed"
    / "mission_control"
    / "artemis_ii_decision_threads.csv"
)

POSTFLIGHT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "mission_control"
    / "artemis_ii_postflight_engineering_timeline.csv"
)

PHASE7A_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_mission_control_perspectives.json"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "mission_control"
    / "phase7b_decision_thread_matrix.svg"
)


EXPECTED_DATASET_ID = (
    "phase7b_artemis_ii_"
    "mission_control_decision_threads"
)

EXPECTED_STAGE_ORDER = [
    "detection",
    "evidence",
    "constraint",
    "options",
    "decision",
    "action",
    "outcome",
]

EXPECTED_THREAD_IDS = [
    "OUTBOUND_TRAJECTORY_ADAPTATION",
    "FD1_UWMS_FAULT_RECOVERY",
    "FD4_WASTEWATER_VENT_RESPONSE",
    "LUNAR_COMMUNICATIONS_CONSTRAINT",
    "LUNAR_SCIENCE_EXECUTION",
    "RETURN_LINK_ANOMALY_RTC2",
    "TPS_RISK_MITIGATION_CLOSURE",
    "FINAL_CORRECTION_ENTRY_HANDOFF",
    "ENTRY_BLACKOUT_REACQUISITION",
    "DESCENT_SPLASHDOWN_RECOVERY",
]

EXPECTED_THREAD_MATURITY = {
    "OUTBOUND_TRAJECTORY_ADAPTATION": (
        5,
        1,
        1,
        0,
    ),
    "FD1_UWMS_FAULT_RECOVERY": (
        5,
        1,
        1,
        0,
    ),
    "FD4_WASTEWATER_VENT_RESPONSE": (
        6,
        0,
        1,
        0,
    ),
    "LUNAR_COMMUNICATIONS_CONSTRAINT": (
        5,
        1,
        0,
        1,
    ),
    "LUNAR_SCIENCE_EXECUTION": (
        5,
        1,
        1,
        0,
    ),
    "RETURN_LINK_ANOMALY_RTC2": (
        6,
        0,
        1,
        0,
    ),
    "TPS_RISK_MITIGATION_CLOSURE": (
        7,
        0,
        0,
        0,
    ),
    "FINAL_CORRECTION_ENTRY_HANDOFF": (
        5,
        1,
        1,
        0,
    ),
    "ENTRY_BLACKOUT_REACQUISITION": (
        5,
        1,
        0,
        1,
    ),
    "DESCENT_SPLASHDOWN_RECOVERY": (
        4,
        2,
        1,
        0,
    ),
}

EXPECTED_POSTFLIGHT_IDS = [
    "POSTFLIGHT_RECOVERY_TRANSITION",
    "POSTFLIGHT_INITIAL_ORION_ASSESSMENT",
    "POSTFLIGHT_URINE_VENT_INVESTIGATION",
    "POSTFLIGHT_MISSION_FAULT_MANAGEMENT_ANALYSIS",
    "POSTFLIGHT_TPS_ENGINEERING_KNOWLEDGE_UPDATE",
    "POSTFLIGHT_LUNAR_SCIENCE_RELEASE",
]

EXPECTED_THREAD_CSV_COLUMNS = [
    "thread_id",
    "title",
    "classification",
    "anomaly",
    "primary_lenses",
    "anchor_event_ids",
    "detection_status",
    "evidence_status",
    "constraint_status",
    "options_status",
    "decision_status",
    "action_status",
    "outcome_status",
    "publicly_established_stages",
    "missionlab_synthesis_stages",
    "not_publicly_enumerated_stages",
    "not_applicable_stages",
]

EXPECTED_POSTFLIGHT_CSV_COLUMNS = [
    "order",
    "record_id",
    "date",
    "date_precision",
    "category",
    "status",
    "open_issue",
    "source_ids",
    "summary",
]


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 7B VALIDATION FAILED: "
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


def thread_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "thread_id"
        ]: item
        for item
        in result[
            "decision_threads"
        ]
    }


def postflight_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "record_id"
        ]: item
        for item
        in result[
            "postflight_engineering_timeline"
        ]
    }


def validate_identity(
    reference: dict,
    processed: dict,
    phase7a: dict,
):
    require(
        reference
        == processed,
        (
            "reference and processed "
            "Phase 7B manifests differ"
        ),
    )

    require(
        reference.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "Phase 7B dataset identity mismatch",
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
        == "7B",
        "phase identity mismatch",
    )

    require(
        reference.get(
            "status"
        )
        == (
            "MISSION_CONTROL_DECISION_"
            "SYNTHESIS_COMPLETE"
        ),
        "Phase 7B status mismatch",
    )

    require(
        phase7a.get(
            "dataset_id"
        )
        == (
            "phase7a_artemis_ii_"
            "mission_control_perspectives"
        ),
        "Phase 7A dependency mismatch",
    )


def validate_stage_model(
    result: dict,
):
    require(
        result[
            "decision_stage_model"
        ]
        == EXPECTED_STAGE_ORDER,
        "decision-stage model mismatch",
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
            "expected 6 dependencies, "
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

    require(
        ids
        == [
            "PHASE7A",
            "PHASE2",
            "WASTE_MANAGEMENT",
            "TPS_EVIDENCE",
            "ENTRY_RECOVERY",
            "LUNAR_SCIENCE",
        ],
        "dependency registry mismatch",
    )

    for item in dependencies:
        require(
            bool(
                item[
                    "dataset_id"
                ]
            ),
            (
                "missing dependency dataset ID: "
                f"{item['dependency_id']}"
            ),
        )


def validate_public_sources(
    result: dict,
):
    sources = result[
        "public_postflight_source_registry"
    ]

    require(
        len(
            sources
        )
        == 5,
        (
            "expected 5 public postflight sources, "
            f"found {len(sources)}"
        ),
    )

    ids = [
        item[
            "source_id"
        ]
        for item
        in sources
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
        "duplicate postflight source IDs",
    )

    expected = {
        (
            "NASA_INITIAL_POSTFLIGHT_"
            "ASSESSMENT_2026_04_20"
        ),
        (
            "NASA_AMES_ARTEMIS_II_"
            "POSTFLIGHT_ANALYSIS_2026_04_21"
        ),
        (
            "NASA_ORION_TESTING_"
            "UPDATED_2026_09_24"
        ),
        (
            "NASA_ARTEMIS_II_PRELIMINARY_"
            "LUNAR_SCIENCE_2026_10_07"
        ),
        (
            "NASA_NTRS_ARTEMIS_II_"
            "HEATSHIELD_SUCCESS_2026"
        ),
    }

    require(
        set(
            ids
        )
        == expected,
        "public postflight source registry mismatch",
    )


def validate_threads(
    result: dict,
):
    threads = result[
        "decision_threads"
    ]

    require(
        len(
            threads
        )
        == 10,
        (
            "expected 10 decision threads, "
            f"found {len(threads)}"
        ),
    )

    ids = [
        item[
            "thread_id"
        ]
        for item
        in threads
    ]

    require(
        ids
        == EXPECTED_THREAD_IDS,
        "decision-thread identity/order mismatch",
    )

    require(
        len(
            ids
        )
        == len(
            set(
                ids
            )
        ),
        "duplicate decision-thread IDs",
    )

    allowed_statuses = {
        "PUBLICLY_ESTABLISHED",
        "MISSIONLAB_SYNTHESIS",
        "NOT_PUBLICLY_ENUMERATED",
        "NOT_APPLICABLE",
    }

    for thread in threads:
        require(
            list(
                thread[
                    "stages"
                ].keys()
            )
            == EXPECTED_STAGE_ORDER,
            (
                "stage order mismatch for "
                f"{thread['thread_id']}"
            ),
        )

        require(
            len(
                thread[
                    "primary_lenses"
                ]
            )
            > 0,
            (
                "missing primary lenses for "
                f"{thread['thread_id']}"
            ),
        )

        require(
            len(
                thread[
                    "anchor_event_ids"
                ]
            )
            > 0,
            (
                "missing anchor events for "
                f"{thread['thread_id']}"
            ),
        )

        for stage_name in EXPECTED_STAGE_ORDER:
            stage = thread[
                "stages"
            ][
                stage_name
            ]

            require(
                stage[
                    "status"
                ]
                in allowed_statuses,
                (
                    "invalid stage status for "
                    f"{thread['thread_id']} / "
                    f"{stage_name}"
                ),
            )

            require(
                bool(
                    stage[
                        "summary"
                    ]
                ),
                (
                    "empty stage summary for "
                    f"{thread['thread_id']} / "
                    f"{stage_name}"
                ),
            )

            require(
                bool(
                    stage[
                        "evidence_class"
                    ]
                ),
                (
                    "missing evidence class for "
                    f"{thread['thread_id']} / "
                    f"{stage_name}"
                ),
            )


def validate_maturity(
    result: dict,
):
    maturity = result[
        "decision_maturity"
    ]

    require(
        set(
            maturity.keys()
        )
        == set(
            EXPECTED_THREAD_IDS
        ),
        "decision-maturity registry mismatch",
    )

    for (
        thread_id,
        expected,
    ) in EXPECTED_THREAD_MATURITY.items():
        item = maturity[
            thread_id
        ]

        actual = (
            item[
                "publicly_established_stages"
            ],
            item[
                "missionlab_synthesis_stages"
            ],
            item[
                "not_publicly_enumerated_stages"
            ],
            item[
                "not_applicable_stages"
            ],
        )

        require(
            actual
            == expected,
            (
                "decision-maturity mismatch for "
                f"{thread_id}: {actual}"
            ),
        )

        require(
            item[
                "total_stages"
            ]
            == 7,
            (
                "total stage count mismatch for "
                f"{thread_id}"
            ),
        )

        require(
            item[
                "complete_private_decision_history_claimed"
            ]
            is False,
            (
                "private decision history "
                f"incorrectly claimed for {thread_id}"
            ),
        )


def validate_selected_threads(
    result: dict,
):
    index = thread_index(
        result
    )

    outbound = index[
        "OUTBOUND_TRAJECTORY_ADAPTATION"
    ]

    require(
        outbound[
            "anomaly"
        ]
        is False,
        "outbound correction thread wrongly marked anomaly",
    )

    require(
        outbound[
            "stages"
        ][
            "decision"
        ][
            "status"
        ]
        == "PUBLICLY_ESTABLISHED",
        "outbound correction decision not public",
    )

    uwms = index[
        "FD1_UWMS_FAULT_RECOVERY"
    ]

    require(
        uwms[
            "anomaly"
        ]
        is True,
        "FD1 UWMS fault not marked anomaly",
    )

    require(
        (
            "RESTORED_OPERATION != KNOWN_ROOT_CAUSE"
            in uwms[
                "guardrails"
            ]
        ),
        "FD1 root-cause guardrail missing",
    )

    vent = index[
        "FD4_WASTEWATER_VENT_RESPONSE"
    ]

    require(
        vent[
            "stages"
        ][
            "outcome"
        ][
            "status"
        ]
        == "PUBLICLY_ESTABLISHED",
        "vent-line outcome state mismatch",
    )

    require(
        (
            "POSSIBLE_ICE != CONFIRMED_ICE"
            in vent[
                "guardrails"
            ]
        ),
        "possible-ice boundary missing",
    )

    lunar_comm = index[
        "LUNAR_COMMUNICATIONS_CONSTRAINT"
    ]

    require(
        lunar_comm[
            "anomaly"
        ]
        is False,
        (
            "expected lunar communication "
            "constraint wrongly marked anomaly"
        ),
    )

    require(
        lunar_comm[
            "stages"
        ][
            "options"
        ][
            "status"
        ]
        == "NOT_APPLICABLE",
        (
            "expected lunar constraint "
            "options state mismatch"
        ),
    )

    rtc2 = index[
        "RETURN_LINK_ANOMALY_RTC2"
    ]

    require(
        rtc2[
            "anomaly"
        ]
        is True,
        "return-link loss not marked anomaly",
    )

    require(
        (
            "TEMPORAL_SEQUENCE != CAUSATION"
            in rtc2[
                "guardrails"
            ]
        ),
        "RTC2 causation guardrail missing",
    )

    tps = index[
        "TPS_RISK_MITIGATION_CLOSURE"
    ]

    for stage_name in EXPECTED_STAGE_ORDER:
        require(
            tps[
                "stages"
            ][
                stage_name
            ][
                "status"
            ]
            == "PUBLICLY_ESTABLISHED",
            (
                "TPS thread expected full public "
                f"maturity at {stage_name}"
            ),
        )

    blackout = index[
        "ENTRY_BLACKOUT_REACQUISITION"
    ]

    require(
        blackout[
            "anomaly"
        ]
        is False,
        "planned entry blackout wrongly marked anomaly",
    )

    require(
        (
            "PLANNED_ENTRY_BLACKOUT != COMMUNICATIONS_ANOMALY"
            in blackout[
                "guardrails"
            ]
        ),
        "entry-blackout anomaly boundary missing",
    )


def validate_postflight_timeline(
    result: dict,
):
    records = result[
        "postflight_engineering_timeline"
    ]

    require(
        len(
            records
        )
        == 6,
        (
            "expected 6 postflight records, "
            f"found {len(records)}"
        ),
    )

    ids = [
        item[
            "record_id"
        ]
        for item
        in records
    ]

    require(
        ids
        == EXPECTED_POSTFLIGHT_IDS,
        "postflight record identity/order mismatch",
    )

    require(
        [
            item[
                "order"
            ]
            for item
            in records
        ]
        == list(
            range(
                1,
                7,
            )
        ),
        "postflight order mismatch",
    )

    index = postflight_index(
        result
    )

    require(
        index[
            "POSTFLIGHT_RECOVERY_TRANSITION"
        ][
            "date"
        ]
        == "2026-04-11",
        "recovery transition date mismatch",
    )

    require(
        index[
            "POSTFLIGHT_INITIAL_ORION_ASSESSMENT"
        ][
            "date"
        ]
        == "2026-04-20",
        "initial Orion assessment date mismatch",
    )

    require(
        index[
            "POSTFLIGHT_URINE_VENT_INVESTIGATION"
        ][
            "status"
        ]
        == "OPEN_IN_CURATED_PUBLIC_EVIDENCE",
        "urine vent investigation status mismatch",
    )

    require(
        index[
            "POSTFLIGHT_URINE_VENT_INVESTIGATION"
        ][
            "open_issue"
        ]
        is True,
        "urine vent investigation not marked open",
    )

    require(
        index[
            "POSTFLIGHT_MISSION_FAULT_MANAGEMENT_ANALYSIS"
        ][
            "status"
        ]
        == "POSTFLIGHT_ANALYSIS_ONGOING",
        "Mission/Fault Management state mismatch",
    )

    require(
        index[
            "POSTFLIGHT_MISSION_FAULT_MANAGEMENT_ANALYSIS"
        ][
            "open_issue"
        ]
        is True,
        "Mission/Fault Management analysis not marked open",
    )

    require(
        index[
            "POSTFLIGHT_TPS_ENGINEERING_KNOWLEDGE_UPDATE"
        ][
            "date"
        ]
        == "2026-09-24",
        "TPS knowledge-update date mismatch",
    )

    require(
        index[
            "POSTFLIGHT_LUNAR_SCIENCE_RELEASE"
        ][
            "date"
        ]
        == "2026-10-07",
        "lunar science release date mismatch",
    )


def validate_open_issue_registry(
    result: dict,
):
    issues = result[
        "postflight_open_issue_registry"
    ]

    require(
        len(
            issues
        )
        == 2,
        (
            "expected 2 open public issues, "
            f"found {len(issues)}"
        ),
    )

    ids = [
        item[
            "issue_id"
        ]
        for item
        in issues
    ]

    require(
        ids
        == [
            "URINE_VENT_LINE_ROOT_CAUSE",
            (
                "MISSION_AND_FAULT_MANAGEMENT_"
                "POSTFLIGHT_ANALYSIS"
            ),
        ],
        "open-issue registry mismatch",
    )

    require(
        issues[
            0
        ][
            "publicly_confirmed_root_cause"
        ]
        is False,
        (
            "urine vent root cause "
            "incorrectly marked confirmed"
        ),
    )

    require(
        issues[
            1
        ][
            "publicly_confirmed_final_result"
        ]
        is False,
        (
            "Mission/Fault Management "
            "analysis incorrectly marked final"
        ),
    )


def validate_policy(
    result: dict,
):
    policy = result[
        "phase7_integration_policy"
    ]

    expected_true = [
        "decision_thread_requires_seven_stage_schema",
        (
            "public_evidence_and_"
            "missionlab_synthesis_separated"
        ),
    ]

    expected_false = [
        "private_console_dialogue_reconstructed",
        "private_option_tree_reconstructed",
        (
            "specific_controller_"
            "decision_authority_inferred"
        ),
        (
            "unknown_root_cause_"
            "promoted_to_confirmed"
        ),
        (
            "expected_constraint_"
            "promoted_to_anomaly"
        ),
        (
            "temporal_sequence_"
            "promoted_to_causation"
        ),
        (
            "postflight_open_investigations_"
            "forced_closed"
        ),
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
            "MISSIONLAB_DECISION_THREAD",
            "NASA_PRIVATE_CONSOLE_TRANSCRIPT",
        ),
        (
            "PUBLIC_SEQUENCE",
            "COMPLETE_INTERNAL_DECISION_LOGIC",
        ),
        (
            "PUBLIC_ACTION",
            "COMPLETE_OPTION_SET",
        ),
        (
            "DISCIPLINE_RELEVANCE",
            "DECISION_AUTHORITY",
        ),
        (
            "TEMPORAL_SEQUENCE",
            "CAUSATION",
        ),
        (
            "TROUBLESHOOTING_ACTION",
            "CONFIRMED_ROOT_CAUSE",
        ),
        (
            "EXPECTED_OPERATIONAL_CONSTRAINT",
            "ANOMALY",
        ),
        (
            "INITIAL_POSTFLIGHT_ASSESSMENT",
            "FINAL_ENGINEERING_DATASET",
        ),
        (
            "OPEN_PUBLIC_INVESTIGATION",
            "RESOLVED_ROOT_CAUSE",
        ),
    ]

    require(
        len(
            items
        )
        == 9,
        (
            "expected 9 critical non-equivalences, "
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
            "shared discipline-prioritized "
            "timeline incomplete"
        ),
    )

    require(
        roadmap[
            "decision_threads_detection_to_outcome"
        ]
        == "COMPLETE",
        "decision-thread roadmap item incomplete",
    )

    require(
        roadmap[
            "postflight_engineering_timeline"
        ]
        == "COMPLETE",
        (
            "postflight engineering timeline "
            "roadmap item incomplete"
        ),
    )

    require(
        roadmap[
            "phase7_overall"
        ]
        == (
            "COMPLETE_RELATIVE_TO_"
            "DEFENSIBLE_PUBLIC_EVIDENCE"
        ),
        "Phase 7 overall status mismatch",
    )


def validate_thread_csv(
    rows: list[dict],
):
    require(
        len(
            rows
        )
        == 10,
        (
            "decision-thread CSV expected 10 rows, "
            f"found {len(rows)}"
        ),
    )

    require(
        list(
            rows[
                0
            ].keys()
        )
        == EXPECTED_THREAD_CSV_COLUMNS,
        "decision-thread CSV schema mismatch",
    )

    ids = [
        row[
            "thread_id"
        ]
        for row
        in rows
    ]

    require(
        ids
        == EXPECTED_THREAD_IDS,
        "decision-thread CSV identity/order mismatch",
    )

    for row in rows:
        expected = EXPECTED_THREAD_MATURITY[
            row[
                "thread_id"
            ]
        ]

        actual = (
            int(
                row[
                    "publicly_established_stages"
                ]
            ),
            int(
                row[
                    "missionlab_synthesis_stages"
                ]
            ),
            int(
                row[
                    "not_publicly_enumerated_stages"
                ]
            ),
            int(
                row[
                    "not_applicable_stages"
                ]
            ),
        )

        require(
            actual
            == expected,
            (
                "decision-thread CSV maturity mismatch "
                f"for {row['thread_id']}"
            ),
        )


def validate_postflight_csv(
    rows: list[dict],
):
    require(
        len(
            rows
        )
        == 6,
        (
            "postflight CSV expected 6 rows, "
            f"found {len(rows)}"
        ),
    )

    require(
        list(
            rows[
                0
            ].keys()
        )
        == EXPECTED_POSTFLIGHT_CSV_COLUMNS,
        "postflight CSV schema mismatch",
    )

    require(
        [
            row[
                "record_id"
            ]
            for row
            in rows
        ]
        == EXPECTED_POSTFLIGHT_IDS,
        "postflight CSV identity/order mismatch",
    )

    open_rows = [
        row
        for row
        in rows
        if row[
            "open_issue"
        ].lower()
        == "true"
    ]

    require(
        len(
            open_rows
        )
        == 2,
        (
            "postflight CSV expected 2 open issues, "
            f"found {len(open_rows)}"
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
            "artemis_ii_decision_threads.json"
        ),
        "reference JSON output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "processed_json"
            ]
        )
        == (
            "data/processed/mission_control/"
            "artemis_ii_decision_threads.json"
        ),
        "processed JSON output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "decision_thread_csv"
            ]
        )
        == (
            "data/processed/mission_control/"
            "artemis_ii_decision_threads.csv"
        ),
        "decision-thread CSV output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "postflight_timeline_csv"
            ]
        )
        == (
            "data/processed/mission_control/"
            "artemis_ii_postflight_engineering_timeline.csv"
        ),
        "postflight CSV output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "figure"
            ]
        )
        == (
            "docs/assets/mission_control/"
            "phase7b_decision_thread_matrix.svg"
        ),
        "figure output path mismatch",
    )


def validate_figure():
    require(
        FIGURE_PATH.exists(),
        f"missing Phase 7B figure: {FIGURE_PATH}",
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 7B figure is empty",
    )

    content = FIGURE_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    require(
        "<svg"
        in content,
        "Phase 7B figure is not SVG",
    )


def main():
    print()
    print(
        "Phase 7B Artemis II Mission Control "
        "Decision Thread Validation"
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

    phase7a = load_json(
        PHASE7A_PATH
    )

    thread_rows = load_csv(
        THREAD_CSV
    )

    postflight_rows = load_csv(
        POSTFLIGHT_CSV
    )

    validate_identity(
        reference,
        processed,
        phase7a,
    )

    print()
    print(
        "Analysis identity: PASS"
    )
    print(
        "Reference / processed manifest consistency: PASS"
    )
    print(
        "Phase 7A dependency: PASS"
    )

    validate_stage_model(
        reference
    )

    print()
    print(
        "Seven-stage decision model: PASS"
    )
    print(
        "Detection -> evidence -> constraint -> "
        "options -> decision -> action -> outcome: PASS"
    )

    validate_dependencies(
        reference
    )

    print()
    print(
        "6 cross-phase dependencies: PASS"
    )

    validate_public_sources(
        reference
    )

    print()
    print(
        "5 postflight public source records: PASS"
    )

    validate_threads(
        reference
    )

    print()
    print(
        "10 decision threads: PASS"
    )
    print(
        "Decision-thread ID uniqueness: PASS"
    )
    print(
        "Seven stages present in every thread: PASS"
    )
    print(
        "Stage evidence classifications: PASS"
    )

    validate_maturity(
        reference
    )

    print()
    print(
        "Decision-maturity accounting: PASS"
    )
    print(
        "No complete private-decision-history claim: PASS"
    )

    validate_selected_threads(
        reference
    )

    print()
    print(
        "Outbound correction adaptation thread: PASS"
    )
    print(
        "Flight Day 1 UWMS recovery thread: PASS"
    )
    print(
        "Flight Day 4 vent-line response thread: PASS"
    )
    print(
        "Lunar communications constraint thread: PASS"
    )
    print(
        "Return-link anomaly / RTC2 thread: PASS"
    )
    print(
        "TPS mitigation and closure thread: PASS"
    )
    print(
        "Entry blackout / reacquisition thread: PASS"
    )

    validate_postflight_timeline(
        reference
    )

    print()
    print(
        "6-record postflight engineering timeline: PASS"
    )
    print(
        "Recovery transition: PASS"
    )
    print(
        "Initial Orion postflight assessment: PASS"
    )
    print(
        "Urine vent-line investigation remains open: PASS"
    )
    print(
        "Mission/Fault Management analysis remains ongoing: PASS"
    )
    print(
        "TPS engineering knowledge update: PASS"
    )
    print(
        "October lunar-science release: PASS"
    )

    validate_open_issue_registry(
        reference
    )

    print()
    print(
        "2-item open engineering issue registry: PASS"
    )
    print(
        "No fabricated urine vent-line root cause: PASS"
    )
    print(
        "No fabricated final Mission/Fault Management result: PASS"
    )

    validate_policy(
        reference
    )

    print()
    print(
        "Public evidence / MissionLab synthesis separation: PASS"
    )
    print(
        "Private console dialogue non-reconstruction: PASS"
    )
    print(
        "Private option-tree non-reconstruction: PASS"
    )
    print(
        "Controller decision-authority non-inference: PASS"
    )
    print(
        "Unknown root-cause non-promotion: PASS"
    )
    print(
        "Expected-constraint / anomaly separation: PASS"
    )
    print(
        "Temporal-sequence / causation separation: PASS"
    )
    print(
        "Open-investigation preservation: PASS"
    )

    validate_non_equivalences(
        reference
    )

    print()
    print(
        "9 critical non-equivalences: PASS"
    )
    print(
        "Decision-thread / private-transcript boundary: PASS"
    )
    print(
        "Public-sequence / internal-logic boundary: PASS"
    )
    print(
        "Public-action / complete-option-set boundary: PASS"
    )
    print(
        "Discipline-relevance / decision-authority boundary: PASS"
    )
    print(
        "Temporal-sequence / causation boundary: PASS"
    )
    print(
        "Troubleshooting / root-cause boundary: PASS"
    )
    print(
        "Expected-constraint / anomaly boundary: PASS"
    )
    print(
        "Initial-assessment / final-dataset boundary: PASS"
    )
    print(
        "Open-investigation / resolved-root-cause boundary: PASS"
    )

    validate_roadmap(
        reference
    )

    print()
    print(
        "All seven discipline lenses: PASS"
    )
    print(
        "Shared prioritized mission timeline: PASS"
    )
    print(
        "Decision-thread roadmap coverage: PASS"
    )
    print(
        "Postflight engineering timeline roadmap coverage: PASS"
    )
    print(
        "Phase 7 roadmap coverage: PASS"
    )

    validate_thread_csv(
        thread_rows
    )

    validate_postflight_csv(
        postflight_rows
    )

    print()
    print(
        "Decision-thread CSV: PASS"
    )
    print(
        "Decision-thread CSV schema: PASS"
    )
    print(
        "Postflight engineering CSV: PASS"
    )
    print(
        "Postflight engineering CSV schema: PASS"
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
        "Validated decision-thread maturity:"
    )

    for thread_id in EXPECTED_THREAD_IDS:
        values = EXPECTED_THREAD_MATURITY[
            thread_id
        ]

        print(
            "  "
            + thread_id
            + ": "
            + f"{values[0]} public / "
            + f"{values[1]} synthesis / "
            + f"{values[2]} not-public / "
            + f"{values[3]} N/A"
        )

    print()
    print(
        "Validated postflight engineering timeline:"
    )
    print(
        "  2026-04-11 recovery transition"
    )
    print(
        "  2026-04-20 initial Orion assessment"
    )
    print(
        "  2026-04-20 urine vent investigation OPEN"
    )
    print(
        "  2026-04-21 Mission/Fault Management "
        "analysis ONGOING"
    )
    print(
        "  2026-09-24 TPS engineering knowledge update"
    )
    print(
        "  2026-10-07 lunar-science results release"
    )

    print()
    print(
        "Phase 7 status:"
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
        "  decision threads: COMPLETE"
    )
    print(
        "  postflight engineering timeline: COMPLETE"
    )
    print(
        "  open public investigations preserved: YES"
    )
    print(
        "  overall: COMPLETE RELATIVE TO "
        "DEFENSIBLE PUBLIC EVIDENCE"
    )

    print()
    print(
        "PHASE 7B VALIDATION PASSED"
    )
    print(
        "PHASE 7 ROADMAP COVERAGE PASSED"
    )


if __name__ == "__main__":
    main()
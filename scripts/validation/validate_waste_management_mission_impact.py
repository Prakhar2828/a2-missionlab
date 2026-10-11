from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PHASE3B1_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_waste_management_evidence.json"
)

PHASE3B2_PATH = (
    ROOT
    / "data"
    / "processed"
    / "eclss"
    / "waste_management_operational_threads.json"
)

PHASE2_MANEUVER_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_operational_threads.json"
)

PHASE2_INTEGRATED_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_phase2_integrated_operations.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "eclss"
)

CORRELATION_CSV = (
    OUTPUT_DIR
    / "waste_management_cross_domain_correlations.csv"
)

SUMMARY_JSON = (
    OUTPUT_DIR
    / "waste_management_mission_impact.json"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "eclss"
    / "phase3b3_waste_management_cross_domain.svg"
)


EXPECTED_IDS = {
    "phase3b1": (
        "phase3b1_artemis_ii_"
        "waste_management_evidence"
    ),
    "phase3b2": (
        "phase3b2_artemis_ii_"
        "waste_management_operational_threads"
    ),
    "phase2_maneuvers": (
        "phase2i4_artemis_ii_"
        "maneuver_operational_threads"
    ),
    "phase2_integrated": (
        "phase2k_artemis_ii_"
        "phase2_integrated_operations"
    ),
    "phase3b3": (
        "phase3b3_artemis_ii_"
        "waste_management_mission_impact"
    ),
}

FD1_THREAD_ID = (
    "flight_day_1_toilet_fault_and_recovery"
)

FD4_THREAD_ID = (
    "flight_day_4_urine_wastewater_vent_line_issue"
)

EXPECTED_CORRELATION_IDS = [
    "WM_FD1_CREW_GROUND_RECOVERY",
    "WM_FD4_ATTITUDE_SUPPORT",
    "WM_FD4_TRAJECTORY_SCHEDULE_INTERACTION",
    "WM_FD4_CREW_CONTINGENCY",
    "WM_FD4_MISSION_CONTINUATION",
    "WM_FD4_POSTFLIGHT_ENGINEERING_FOLLOWUP",
]

EXPECTED_RELATIONSHIPS = {
    "WM_FD1_CREW_GROUND_RECOVERY": {
        "thread": FD1_THREAD_ID,
        "domain": (
            "CREW_SYSTEMS_AND_"
            "MISSION_OPERATIONS"
        ),
        "relationship_type": (
            "CREW_GROUND_"
            "TROUBLESHOOTING"
        ),
        "relationship_status": (
            "NASA_REPORTED"
        ),
        "causal": True,
        "mission_impact": False,
    },
    "WM_FD4_ATTITUDE_SUPPORT": {
        "thread": FD4_THREAD_ID,
        "domain": (
            "GNC_ATTITUDE_OPERATIONS"
        ),
        "relationship_type": (
            "SPACECRAFT_ATTITUDE_"
            "SUPPORT_TO_SYSTEM_"
            "TROUBLESHOOTING"
        ),
        "relationship_status": (
            "NASA_REPORTED_AND_"
            "PHASE2_CORROBORATED"
        ),
        "causal": True,
        "mission_impact": False,
    },
    "WM_FD4_TRAJECTORY_SCHEDULE_INTERACTION": {
        "thread": FD4_THREAD_ID,
        "domain": (
            "FLIGHT_DYNAMICS_AND_"
            "TRAJECTORY_SCHEDULING"
        ),
        "relationship_type": (
            "PARALLEL_OPERATIONAL_"
            "SCHEDULING_CONTEXT"
        ),
        "relationship_status": (
            "CORRELATED_WITHOUT_"
            "CAUSAL_CANCELLATION_CLAIM"
        ),
        "causal": False,
        "mission_impact": False,
    },
    "WM_FD4_CREW_CONTINGENCY": {
        "thread": FD4_THREAD_ID,
        "domain": (
            "CREW_SYSTEMS_AND_"
            "CONTINGENCY_OPERATIONS"
        ),
        "relationship_type": (
            "CONTINGENCY_POSTURE"
        ),
        "relationship_status": (
            "NASA_REPORTED"
        ),
        "causal": True,
        "mission_impact": False,
    },
    "WM_FD4_MISSION_CONTINUATION": {
        "thread": FD4_THREAD_ID,
        "domain": (
            "MISSION_OPERATIONS"
        ),
        "relationship_type": (
            "DOWNSTREAM_MISSION_"
            "CONTINUATION"
        ),
        "relationship_status": (
            "TEMPORAL_AND_"
            "OPERATIONAL_CONTEXT"
        ),
        "causal": False,
        "mission_impact": False,
    },
    "WM_FD4_POSTFLIGHT_ENGINEERING_FOLLOWUP": {
        "thread": FD4_THREAD_ID,
        "domain": (
            "POSTFLIGHT_ENGINEERING"
        ),
        "relationship_type": (
            "POSTFLIGHT_"
            "INVESTIGATION"
        ),
        "relationship_status": (
            "NASA_REPORTED"
        ),
        "causal": True,
        "mission_impact": False,
    },
}

EXPECTED_PHASE2_ANCHORS = {
    "otc2_cancelled": {
        "date_utc": (
            "2026-04-04"
        ),
        "status": (
            "CANCELLED"
        ),
        "reason_classification": (
            "TRAJECTORY_REMAINED_ON_TRACK"
        ),
        "parallel_operational_activity": (
            "ATTITUDE_ADJUSTMENT_FOR_"
            "WASTEWATER_VENT_CLEARING"
        ),
        "failed_burn": False,
        "propulsion_anomaly": False,
    },
    "otc3_executed": {
        "timestamp_utc": (
            "2026-04-06T03:03:00Z"
        ),
        "status": (
            "EXECUTED"
        ),
        "duration_seconds": (
            17.5
        ),
    },
    "pericynthion": {
        "timestamp_utc": (
            "2026-04-06T23:00:46.177998Z"
        ),
    },
    "entry_interface": {
        "timestamp_utc": (
            "2026-04-10T23:53:00Z"
        ),
    },
    "splashdown": {
        "timestamp_utc": (
            "2026-04-11T00:07:00Z"
        ),
    },
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 3B.3 VALIDATION FAILED: "
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
            f"missing JSON: {path}"
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
    if not path.exists():
        fail(
            f"missing CSV: {path}"
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


def bool_from_csv(
    value: str,
    label: str,
) -> bool:
    normalized = (
        value
        .strip()
        .lower()
    )

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    fail(
        f"{label} is not boolean: "
        f"{value!r}"
    )

    raise RuntimeError


def normalized_path(
    value: str,
) -> str:
    return value.replace(
        "\\",
        "/",
    )


def index_events(
    reference: dict,
) -> dict[str, dict]:
    result = {}

    for event in reference[
        "events"
    ]:
        event_id = (
            event[
                "event_id"
            ]
        )

        require(
            event_id not in result,
            (
                "duplicate Phase 3B.1 "
                f"event: {event_id}"
            ),
        )

        result[
            event_id
        ] = event

    return result


def index_threads(
    phase3b2: dict,
) -> dict[str, dict]:
    result = {}

    for thread in phase3b2[
        "threads"
    ]:
        thread_id = (
            thread[
                "thread_id"
            ]
        )

        require(
            thread_id not in result,
            (
                "duplicate Phase 3B.2 "
                f"thread: {thread_id}"
            ),
        )

        result[
            thread_id
        ] = thread

    return result


def get_thread(
    items: list[dict],
    thread_id: str,
) -> dict:
    for item in items:
        if (
            item.get(
                "thread_id"
            )
            == thread_id
        ):
            return item

    fail(
        f"missing thread: {thread_id}"
    )

    raise RuntimeError


def get_step(
    thread: dict,
    step_id: str,
) -> dict:
    for step in thread[
        "operational_sequence"
    ]:
        if (
            step.get(
                "step_id"
            )
            == step_id
        ):
            return step

    fail(
        f"missing step {step_id} "
        f"in {thread['thread_id']}"
    )

    raise RuntimeError


def get_anchor(
    integrated: dict,
    event_id: str,
) -> dict:
    for anchor in integrated[
        "mission_clock_anchors"
    ]:
        if (
            anchor.get(
                "event_id"
            )
            == event_id
        ):
            return anchor

    fail(
        f"missing mission anchor: {event_id}"
    )

    raise RuntimeError


def index_correlations(
    summary: dict,
) -> dict[str, dict]:
    result = {}

    for row in summary[
        "cross_domain_correlations"
    ]:
        correlation_id = (
            row[
                "correlation_id"
            ]
        )

        require(
            correlation_id not in result,
            (
                "duplicate correlation: "
                f"{correlation_id}"
            ),
        )

        result[
            correlation_id
        ] = row

    return result


def validate_identity(
    phase3b1: dict,
    phase3b2: dict,
    phase2_maneuvers: dict,
    phase2_integrated: dict,
    summary: dict,
):
    observed = {
        "phase3b1": (
            phase3b1.get(
                "dataset_id"
            )
        ),
        "phase3b2": (
            phase3b2.get(
                "dataset_id"
            )
        ),
        "phase2_maneuvers": (
            phase2_maneuvers.get(
                "dataset_id"
            )
        ),
        "phase2_integrated": (
            phase2_integrated.get(
                "dataset_id"
            )
        ),
        "phase3b3": (
            summary.get(
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
        summary.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        summary.get(
            "phase"
        )
        == "3B.3",
        "phase identity mismatch",
    )

    require(
        summary.get(
            "status"
        )
        == (
            "CROSS_DOMAIN_"
            "CORRELATION_COMPLETE"
        ),
        "Phase 3B.3 status mismatch",
    )


def validate_dependencies(
    phase3b1: dict,
    phase3b2: dict,
    phase2_maneuvers: dict,
    phase2_integrated: dict,
    summary: dict,
):
    dependencies = (
        summary[
            "dependencies"
        ]
    )

    expected = {
        "phase3b1": (
            phase3b1[
                "dataset_id"
            ]
        ),
        "phase3b2": (
            phase3b2[
                "dataset_id"
            ]
        ),
        "phase2_maneuvers": (
            phase2_maneuvers[
                "dataset_id"
            ]
        ),
        "phase2_integrated": (
            phase2_integrated[
                "dataset_id"
            ]
        ),
    }

    require(
        dependencies
        == expected,
        "dependency registry mismatch",
    )


def validate_phase2_cross_reference(
    phase2_maneuvers: dict,
    phase2_integrated: dict,
    summary: dict,
):
    outbound = get_thread(
        phase2_maneuvers[
            "threads"
        ],
        "outbound_adaptive_trajectory_management",
    )

    otc2 = get_step(
        outbound,
        "otc2_cancelled",
    )

    otc3 = get_step(
        outbound,
        "otc3_executed",
    )

    require(
        otc2.get(
            "date_utc"
        )
        == "2026-04-04",
        "OTC2 date changed",
    )

    require(
        otc2.get(
            "status"
        )
        == "CANCELLED",
        "OTC2 status changed",
    )

    require(
        otc2.get(
            "reason_classification"
        )
        == (
            "TRAJECTORY_REMAINED_"
            "ON_TRACK"
        ),
        "OTC2 cancellation "
        "reason changed",
    )

    require(
        otc2.get(
            "parallel_operational_activity"
        )
        == (
            "ATTITUDE_ADJUSTMENT_FOR_"
            "WASTEWATER_VENT_CLEARING"
        ),
        (
            "OTC2 wastewater parallel "
            "activity missing"
        ),
    )

    require(
        otc2.get(
            "failed_burn"
        )
        is False,
        "OTC2 incorrectly became "
        "a failed burn",
    )

    require(
        otc2.get(
            "propulsion_anomaly"
        )
        is False,
        "OTC2 incorrectly became "
        "a propulsion anomaly",
    )

    require(
        otc3.get(
            "timestamp_utc"
        )
        == (
            "2026-04-06T03:03:00Z"
        ),
        "OTC3 timestamp mismatch",
    )

    require(
        otc3.get(
            "status"
        )
        == "EXECUTED",
        "OTC3 status mismatch",
    )

    require(
        float(
            otc3.get(
                "duration_seconds"
            )
        )
        == 17.5,
        "OTC3 duration mismatch",
    )

    pericynthion = get_anchor(
        phase2_integrated,
        "pericynthion",
    )

    entry_interface = get_anchor(
        phase2_integrated,
        "entry_interface",
    )

    splashdown = get_anchor(
        phase2_integrated,
        "splashdown",
    )

    require(
        pericynthion[
            "timestamp_utc"
        ]
        == (
            "2026-04-06T23:00:46.177998Z"
        ),
        "pericynthion anchor mismatch",
    )

    require(
        entry_interface[
            "timestamp_utc"
        ]
        == (
            "2026-04-10T23:53:00Z"
        ),
        "entry-interface anchor mismatch",
    )

    require(
        splashdown[
            "timestamp_utc"
        ]
        == (
            "2026-04-11T00:07:00Z"
        ),
        "splashdown anchor mismatch",
    )

    observed_anchors = (
        summary[
            "phase2_anchors"
        ]
    )

    require(
        set(
            observed_anchors
        )
        == set(
            EXPECTED_PHASE2_ANCHORS
        ),
        "Phase 2 anchor set mismatch",
    )

    for (
        anchor_id,
        expected,
    ) in (
        EXPECTED_PHASE2_ANCHORS.items()
    ):
        observed = (
            observed_anchors[
                anchor_id
            ]
        )

        require(
            observed
            == expected,
            (
                f"summary anchor mismatch: "
                f"{anchor_id}"
            ),
        )


def validate_phase3_thread_dependencies(
    phase3b1: dict,
    phase3b2: dict,
):
    events = index_events(
        phase3b1
    )

    threads = index_threads(
        phase3b2
    )

    require(
        FD1_THREAD_ID in threads,
        "missing Flight Day 1 thread",
    )

    require(
        FD4_THREAD_ID in threads,
        "missing Flight Day 4 thread",
    )

    expected_events = {
        "A2_UWMS_FD1_FAULT_LIGHT",
        "A2_UWMS_FD1_RESTORED",
        "A2_UWMS_FD4_WASTEWATER_VENT_EARLY_END",
        "A2_UWMS_FD4_VENT_HEATER_RESPONSE",
        "A2_UWMS_FD4_SOLAR_POINTING",
        "A2_UWMS_FD4_BACKUP_COLLECTION_POSTURE",
        "A2_UWMS_POSTFLIGHT_URINE_VENT_INVESTIGATION",
    }

    require(
        set(
            events
        )
        == expected_events,
        "Phase 3B.1 event set changed",
    )

    fd1 = (
        threads[
            FD1_THREAD_ID
        ]
    )

    fd4 = (
        threads[
            FD4_THREAD_ID
        ]
    )

    require(
        fd1[
            "normal_operations_restored"
        ]
        is True,
        "FD1 restoration boundary changed",
    )

    require(
        fd1[
            "root_cause_publicly_established"
        ]
        is False,
        "FD1 root-cause boundary changed",
    )

    require(
        fd4[
            "tank_full"
        ]
        is False,
        "FD4 tank-full boundary changed",
    )

    require(
        fd4[
            "toilet_operational"
        ]
        is True,
        "FD4 toilet-operational "
        "boundary changed",
    )

    require(
        fd4[
            "ice_confirmed"
        ]
        is False,
        "FD4 ice boundary changed",
    )

    require(
        fd4[
            "root_cause_publicly_established"
        ]
        is False,
        "FD4 root-cause boundary changed",
    )

    return (
        events,
        threads,
    )


def validate_correlations(
    summary: dict,
    events: dict[str, dict],
    threads: dict[str, dict],
):
    correlations = index_correlations(
        summary
    )

    require(
        list(
            correlations
        )
        == EXPECTED_CORRELATION_IDS,
        "correlation order or set changed",
    )

    require(
        len(
            correlations
        )
        == 6,
        "expected exactly 6 correlations",
    )

    valid_anchor_ids = {
        "otc2_cancelled",
        "otc3_executed",
        "pericynthion",
        "entry_interface",
        "splashdown",
    }

    for correlation_id in (
        EXPECTED_CORRELATION_IDS
    ):
        row = (
            correlations[
                correlation_id
            ]
        )

        expected = (
            EXPECTED_RELATIONSHIPS[
                correlation_id
            ]
        )

        require(
            row[
                "source_thread_id"
            ]
            == expected[
                "thread"
            ],
            (
                f"{correlation_id} "
                "thread mismatch"
            ),
        )

        require(
            row[
                "source_thread_id"
            ]
            in threads,
            (
                f"{correlation_id} "
                "references unknown "
                "Phase 3B.2 thread"
            ),
        )

        require(
            row[
                "domain"
            ]
            == expected[
                "domain"
            ],
            (
                f"{correlation_id} "
                "domain mismatch"
            ),
        )

        require(
            row[
                "relationship_type"
            ]
            == expected[
                "relationship_type"
            ],
            (
                f"{correlation_id} "
                "relationship-type mismatch"
            ),
        )

        require(
            row[
                "relationship_status"
            ]
            == expected[
                "relationship_status"
            ],
            (
                f"{correlation_id} "
                "relationship-status mismatch"
            ),
        )

        require(
            row[
                "causal_relationship_established"
            ]
            is expected[
                "causal"
            ],
            (
                f"{correlation_id} "
                "causality flag mismatch"
            ),
        )

        require(
            row[
                "mission_impact_claimed"
            ]
            is expected[
                "mission_impact"
            ],
            (
                f"{correlation_id} "
                "mission-impact flag mismatch"
            ),
        )

        require(
            row[
                "provenance"
            ]
            == (
                "MISSIONLAB_DERIVED_"
                "CROSS_DOMAIN_CORRELATION"
            ),
            (
                f"{correlation_id} "
                "provenance mismatch"
            ),
        )

        require(
            isinstance(
                row[
                    "phase3b_event_ids"
                ],
                list,
            ),
            (
                f"{correlation_id} "
                "event IDs are not a list"
            ),
        )

        require(
            len(
                row[
                    "phase3b_event_ids"
                ]
            )
            >= 1,
            (
                f"{correlation_id} "
                "has no Phase 3B events"
            ),
        )

        for event_id in (
            row[
                "phase3b_event_ids"
            ]
        ):
            require(
                event_id in events,
                (
                    f"{correlation_id} "
                    "references unknown event "
                    f"{event_id}"
                ),
            )

        require(
            isinstance(
                row[
                    "phase2_anchor_ids"
                ],
                list,
            ),
            (
                f"{correlation_id} "
                "Phase 2 anchors are "
                "not a list"
            ),
        )

        for anchor_id in (
            row[
                "phase2_anchor_ids"
            ]
        ):
            require(
                anchor_id
                in valid_anchor_ids,
                (
                    f"{correlation_id} "
                    "references unknown "
                    f"Phase 2 anchor {anchor_id}"
                ),
            )

        require(
            isinstance(
                row[
                    "public_basis"
                ],
                str,
            )
            and row[
                "public_basis"
            ].strip(),
            (
                f"{correlation_id} "
                "missing public basis"
            ),
        )

        require(
            isinstance(
                row[
                    "missionlab_interpretation"
                ],
                str,
            )
            and row[
                "missionlab_interpretation"
            ].strip(),
            (
                f"{correlation_id} "
                "missing MissionLab "
                "interpretation"
            ),
        )

    trajectory = (
        correlations[
            "WM_FD4_TRAJECTORY_"
            "SCHEDULE_INTERACTION"
        ]
    )

    require(
        trajectory[
            "causal_relationship_established"
        ]
        is False,
        (
            "waste issue incorrectly "
            "claimed as cause of "
            "OTC2 cancellation"
        ),
    )

    continuation = (
        correlations[
            "WM_FD4_MISSION_CONTINUATION"
        ]
    )

    require(
        continuation[
            "causal_relationship_established"
        ]
        is False,
        (
            "mission continuation "
            "incorrectly given causal "
            "relationship"
        ),
    )

    for row in correlations.values():
        require(
            row[
                "mission_impact_claimed"
            ]
            is False,
            (
                f"{row['correlation_id']} "
                "makes unsupported "
                "mission-impact claim"
            ),
        )

    return correlations


def validate_mission_impact(
    summary: dict,
):
    assessment = (
        summary[
            "mission_impact_assessment"
        ]
    )

    fd1 = (
        assessment[
            "flight_day_1"
        ]
    )

    required_fd1_true = [
        "fault_indication_reported",
        "crew_ground_troubleshooting_reported",
        "normal_operations_restored",
    ]

    required_fd1_false = [
        "mission_ending_impact_established",
        "root_cause_public",
    ]

    for key in required_fd1_true:
        require(
            fd1.get(
                key
            )
            is True,
            (
                "FD1 mission-impact "
                f"expected TRUE: {key}"
            ),
        )

    for key in required_fd1_false:
        require(
            fd1.get(
                key
            )
            is False,
            (
                "FD1 mission-impact "
                f"expected FALSE: {key}"
            ),
        )

    fd4 = (
        assessment[
            "flight_day_4"
        ]
    )

    required_fd4_true = [
        "vent_activity_ended_early",
        "spacecraft_attitude_response_reported",
        "trajectory_schedule_interaction_present",
        "otc2_cancelled_for_trajectory_reason",
        "toilet_operational",
        "crew_contingency_available",
        "later_mission_operations_recorded",
        "postflight_investigation_continued",
    ]

    required_fd4_false = [
        "waste_issue_caused_otc2_cancellation",
        "tank_full",
        "mission_ending_impact_established",
        "root_cause_public",
    ]

    for key in required_fd4_true:
        require(
            fd4.get(
                key
            )
            is True,
            (
                "FD4 mission-impact "
                f"expected TRUE: {key}"
            ),
        )

    for key in required_fd4_false:
        require(
            fd4.get(
                key
            )
            is False,
            (
                "FD4 mission-impact "
                f"expected FALSE: {key}"
            ),
        )


def validate_cross_domain_boundaries(
    summary: dict,
):
    boundaries = (
        summary[
            "cross_domain_boundaries"
        ]
    )

    required_false = [
        "attitude_response_equals_gnc_anomaly",
        "waste_issue_caused_otc2_cancellation",
        "otc2_cancellation_equals_failed_burn",
        "otc2_cancellation_equals_propulsion_anomaly",
        "mission_continuation_equals_zero_operational_impact",
        "mission_continuation_equals_zero_risk",
        "contingency_availability_equals_complete_system_failure",
        "postflight_investigation_equals_final_root_cause",
        "cross_domain_correlation_equals_causation",
        "precise_interval_from_fd4_issue_to_otc3_computable",
    ]

    require(
        set(
            boundaries
        )
        == set(
            required_false
        ),
        "cross-domain boundary set mismatch",
    )

    for key in required_false:
        require(
            boundaries.get(
                key
            )
            is False,
            (
                "cross-domain boundary "
                f"expected FALSE: {key}"
            ),
        )


def validate_evidence_boundary(
    summary: dict,
):
    boundary = (
        summary[
            "evidence_boundary"
        ]
    )

    required_true = [
        "public_operational_interactions_preserved",
        "phase2_cross_reference_preserved",
        "missionlab_correlations_are_derived",
    ]

    required_false = [
        "unreported_internal_rationale_inferred",
        "unreported_failure_propagation_inferred",
        "quantitative_mission_risk_inferred",
        "final_root_cause_inferred",
        "exact_fd4_event_time_known",
    ]

    for key in required_true:
        require(
            boundary.get(
                key
            )
            is True,
            (
                "evidence boundary "
                f"expected TRUE: {key}"
            ),
        )

    for key in required_false:
        require(
            boundary.get(
                key
            )
            is False,
            (
                "evidence boundary "
                f"expected FALSE: {key}"
            ),
        )


def validate_csv(
    csv_rows: list[dict],
    correlations: dict[str, dict],
):
    require(
        len(
            csv_rows
        )
        == 6,
        (
            "cross-domain CSV expected "
            f"6 rows, found {len(csv_rows)}"
        ),
    )

    expected_rows = [
        correlations[
            correlation_id
        ]
        for correlation_id
        in EXPECTED_CORRELATION_IDS
    ]

    for index, (
        csv_row,
        json_row,
    ) in enumerate(
        zip(
            csv_rows,
            expected_rows,
        ),
        start=1,
    ):
        scalar_fields = [
            "correlation_id",
            "source_thread_id",
            "domain",
            "relationship_type",
            "relationship_status",
            "public_basis",
            "missionlab_interpretation",
            "evidence_class",
            "provenance",
        ]

        for field in scalar_fields:
            require(
                csv_row[
                    field
                ]
                == json_row[
                    field
                ],
                (
                    f"CSV row {index} "
                    f"{field} mismatch"
                ),
            )

        csv_events = (
            csv_row[
                "phase3b_event_ids"
            ].split(
                "|"
            )
            if csv_row[
                "phase3b_event_ids"
            ]
            else []
        )

        csv_anchors = (
            csv_row[
                "phase2_anchor_ids"
            ].split(
                "|"
            )
            if csv_row[
                "phase2_anchor_ids"
            ]
            else []
        )

        require(
            csv_events
            == json_row[
                "phase3b_event_ids"
            ],
            (
                f"CSV row {index} "
                "Phase 3B event IDs mismatch"
            ),
        )

        require(
            csv_anchors
            == json_row[
                "phase2_anchor_ids"
            ],
            (
                f"CSV row {index} "
                "Phase 2 anchors mismatch"
            ),
        )

        require(
            bool_from_csv(
                csv_row[
                    "causal_relationship_established"
                ],
                (
                    f"CSV row {index} "
                    "causal_relationship_established"
                ),
            )
            is json_row[
                "causal_relationship_established"
            ],
            (
                f"CSV row {index} "
                "causal flag mismatch"
            ),
        )

        require(
            bool_from_csv(
                csv_row[
                    "mission_impact_claimed"
                ],
                (
                    f"CSV row {index} "
                    "mission_impact_claimed"
                ),
            )
            is json_row[
                "mission_impact_claimed"
            ],
            (
                f"CSV row {index} "
                "mission-impact flag mismatch"
            ),
        )


def validate_output_registry(
    summary: dict,
):
    outputs = (
        summary[
            "outputs"
        ]
    )

    require(
        normalized_path(
            outputs[
                "cross_domain_csv"
            ]
        )
        == (
            "data/processed/eclss/"
            "waste_management_cross_domain_correlations.csv"
        ),
        "cross-domain CSV output path mismatch",
    )

    require(
        normalized_path(
            outputs[
                "mission_impact_json"
            ]
        )
        == (
            "data/processed/eclss/"
            "waste_management_mission_impact.json"
        ),
        "mission-impact JSON "
        "output path mismatch",
    )

    require(
        normalized_path(
            outputs[
                "cross_domain_figure"
            ]
        )
        == (
            "docs/assets/eclss/"
            "phase3b3_waste_management_cross_domain.svg"
        ),
        "cross-domain figure "
        "output path mismatch",
    )


def validate_svg():
    require(
        FIGURE_PATH.exists(),
        (
            "missing Phase 3B.3 "
            f"figure: {FIGURE_PATH}"
        ),
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 3B.3 figure is empty",
    )

    content = (
        FIGURE_PATH.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    require(
        "<svg"
        in content,
        "Phase 3B.3 figure "
        "is not valid SVG",
    )


def main():
    print()
    print(
        "Phase 3B.3 Artemis II "
        "Waste Management Mission-Impact "
        "and Cross-Domain Correlation Validation"
    )
    print(
        "=" * 72
    )

    phase3b1 = load_json(
        PHASE3B1_PATH
    )

    phase3b2 = load_json(
        PHASE3B2_PATH
    )

    phase2_maneuvers = load_json(
        PHASE2_MANEUVER_PATH
    )

    phase2_integrated = load_json(
        PHASE2_INTEGRATED_PATH
    )

    summary = load_json(
        SUMMARY_JSON
    )

    csv_rows = load_csv(
        CORRELATION_CSV
    )

    validate_identity(
        phase3b1,
        phase3b2,
        phase2_maneuvers,
        phase2_integrated,
        summary,
    )

    print()
    print(
        "Analysis identity: PASS"
    )

    validate_dependencies(
        phase3b1,
        phase3b2,
        phase2_maneuvers,
        phase2_integrated,
        summary,
    )

    print(
        "Dependency registry: PASS"
    )

    (
        events,
        threads,
    ) = (
        validate_phase3_thread_dependencies(
            phase3b1,
            phase3b2,
        )
    )

    print(
        "Phase 3B.1 evidence dependency: PASS"
    )
    print(
        "Phase 3B.2 operational "
        "dependency: PASS"
    )

    validate_phase2_cross_reference(
        phase2_maneuvers,
        phase2_integrated,
        summary,
    )

    print()
    print(
        "Phase 2 maneuver "
        "cross-reference: PASS"
    )
    print(
        "OTC2 cancellation reason: PASS"
    )
    print(
        "OTC2 wastewater parallel "
        "activity: PASS"
    )
    print(
        "OTC2 failed-burn boundary: PASS"
    )
    print(
        "OTC2 propulsion-anomaly "
        "boundary: PASS"
    )
    print(
        "Downstream mission anchors: PASS"
    )

    correlations = (
        validate_correlations(
            summary,
            events,
            threads,
        )
    )

    print()
    print(
        "Cross-domain correlation set: PASS"
    )
    print(
        "Correlation thread "
        "traceability: PASS"
    )
    print(
        "Correlation event "
        "traceability: PASS"
    )
    print(
        "Phase 2 anchor "
        "traceability: PASS"
    )
    print(
        "Correlation provenance: PASS"
    )

    validate_mission_impact(
        summary
    )

    print()
    print(
        "Flight Day 1 mission-impact "
        "assessment: PASS"
    )
    print(
        "Flight Day 4 mission-impact "
        "assessment: PASS"
    )

    validate_cross_domain_boundaries(
        summary
    )

    print(
        "Cross-domain boundary policy: PASS"
    )

    validate_evidence_boundary(
        summary
    )

    print(
        "Evidence-boundary policy: PASS"
    )

    validate_csv(
        csv_rows,
        correlations,
    )

    print(
        "Correlation CSV / JSON "
        "consistency: PASS"
    )

    validate_output_registry(
        summary
    )

    validate_svg()

    print(
        "Documentation figure: PASS"
    )

    print()
    print(
        "Validated correlations:"
    )
    print(
        "  total: 6"
    )
    print(
        "  crew-ground recovery: PASS"
    )
    print(
        "  spacecraft attitude "
        "interaction: PASS"
    )
    print(
        "  trajectory scheduling "
        "interaction: PASS"
    )
    print(
        "  crew contingency "
        "posture: PASS"
    )
    print(
        "  downstream mission "
        "continuation: PASS"
    )
    print(
        "  postflight engineering "
        "follow-up: PASS"
    )

    print()
    print(
        "Validated Phase 2 anchors:"
    )
    print(
        "  OTC2 cancellation:"
    )
    print(
        "    2026-04-04"
    )
    print(
        "    reason = "
        "TRAJECTORY_REMAINED_ON_TRACK"
    )
    print(
        "  OTC3:"
    )
    print(
        "    2026-04-06T03:03:00Z"
    )
    print(
        "  pericynthion:"
    )
    print(
        "    2026-04-06T23:00:46.177998Z"
    )
    print(
        "  entry interface:"
    )
    print(
        "    2026-04-10T23:53:00Z"
    )
    print(
        "  splashdown:"
    )
    print(
        "    2026-04-11T00:07:00Z"
    )

    print()
    print(
        "Critical interpretation boundaries:"
    )
    print(
        "  attitude response "
        "!= GNC anomaly"
    )
    print(
        "  wastewater activity "
        "!= cause of OTC2 cancellation"
    )
    print(
        "  OTC2 cancellation "
        "!= failed burn"
    )
    print(
        "  OTC2 cancellation "
        "!= propulsion anomaly"
    )
    print(
        "  mission continuation "
        "!= zero operational impact"
    )
    print(
        "  mission continuation "
        "!= zero risk"
    )
    print(
        "  contingency availability "
        "!= complete UWMS failure"
    )
    print(
        "  cross-domain correlation "
        "!= causation"
    )
    print(
        "  postflight investigation "
        "!= final root cause"
    )
    print(
        "  exact Flight Day 4 "
        "event UTC remains unresolved"
    )

    print()
    print(
        "PHASE 3B.3 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
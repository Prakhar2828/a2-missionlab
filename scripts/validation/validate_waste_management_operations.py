from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_waste_management_evidence.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "eclss"
)

THREADS_JSON = (
    OUTPUT_DIR
    / "waste_management_operational_threads.json"
)

STEPS_CSV = (
    OUTPUT_DIR
    / "waste_management_operational_steps.csv"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "eclss"
    / "phase3b2_waste_management_decision_threads.svg"
)


EXPECTED_REFERENCE_ID = (
    "phase3b1_artemis_ii_"
    "waste_management_evidence"
)

EXPECTED_DATASET_ID = (
    "phase3b2_artemis_ii_"
    "waste_management_operational_threads"
)

FD1_THREAD_ID = (
    "flight_day_1_toilet_fault_and_recovery"
)

FD4_THREAD_ID = (
    "flight_day_4_urine_wastewater_vent_line_issue"
)

EXPECTED_STEP_COUNTS = {
    FD1_THREAD_ID: 6,
    FD4_THREAD_ID: 10,
}

EXPECTED_STEP_IDS = {
    FD1_THREAD_ID: [
        "fd1_observation",
        "fd1_constraint",
        "fd1_evidence_review",
        "fd1_response",
        "fd1_outcome",
        "fd1_uncertainty",
    ],
    FD4_THREAD_ID: [
        "fd4_nominal_activity",
        "fd4_observation",
        "fd4_operational_state",
        "fd4_hypothesis",
        "fd4_heater_response",
        "fd4_solar_response",
        "fd4_contingency",
        "fd4_inflight_outcome",
        "fd4_postflight",
        "fd4_uncertainty",
    ],
}

EXPECTED_EVENT_IDS = {
    "A2_UWMS_FD1_FAULT_LIGHT",
    "A2_UWMS_FD1_RESTORED",
    "A2_UWMS_FD4_WASTEWATER_VENT_EARLY_END",
    "A2_UWMS_FD4_VENT_HEATER_RESPONSE",
    "A2_UWMS_FD4_SOLAR_POINTING",
    "A2_UWMS_FD4_BACKUP_COLLECTION_POSTURE",
    "A2_UWMS_POSTFLIGHT_URINE_VENT_INVESTIGATION",
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 3B.2 VALIDATION FAILED: "
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
            f"missing JSON file: {path}"
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
            f"missing CSV file: {path}"
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
        value.strip()
        .lower()
    )

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    fail(
        f"{label} is not a boolean: "
        f"{value!r}"
    )

    raise RuntimeError


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
                "duplicate reference "
                f"event: {event_id}"
            ),
        )

        result[
            event_id
        ] = event

    return result


def index_sources(
    reference: dict,
) -> dict[str, dict]:
    result = {}

    for source in reference[
        "sources"
    ]:
        source_id = (
            source[
                "source_id"
            ]
        )

        require(
            source_id not in result,
            (
                "duplicate reference "
                f"source: {source_id}"
            ),
        )

        result[
            source_id
        ] = source

    return result


def index_threads(
    output: dict,
) -> dict[str, dict]:
    result = {}

    for thread in output[
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
                "duplicate operational "
                f"thread: {thread_id}"
            ),
        )

        result[
            thread_id
        ] = thread

    return result


def validate_identity(
    reference: dict,
    output: dict,
):
    require(
        reference.get(
            "dataset_id"
        )
        == EXPECTED_REFERENCE_ID,
        "Phase 3B.1 reference ID mismatch",
    )

    require(
        output.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "Phase 3B.2 dataset ID mismatch",
    )

    require(
        output.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        output.get(
            "phase"
        )
        == "3B.2",
        "phase identity mismatch",
    )

    require(
        output.get(
            "status"
        )
        == (
            "OPERATIONAL_RECONSTRUCTION_"
            "COMPLETE"
        ),
        "operational reconstruction "
        "status mismatch",
    )


def validate_dependency(
    reference: dict,
    output: dict,
):
    dependency = (
        output[
            "dependency"
        ]
    )

    require(
        dependency[
            "dataset_id"
        ]
        == reference[
            "dataset_id"
        ],
        "dependency dataset ID mismatch",
    )

    require(
        dependency[
            "source_event_count"
        ]
        == len(
            reference[
                "events"
            ]
        ),
        "dependency event count mismatch",
    )

    require(
        dependency[
            "source_count"
        ]
        == len(
            reference[
                "sources"
            ]
        ),
        "dependency source count mismatch",
    )


def validate_reconstruction_model(
    output: dict,
):
    model = (
        output[
            "reconstruction_model"
        ]
    )

    require(
        model[
            "sequence"
        ]
        == [
            "observation",
            "constraint_or_evidence_state",
            "nasa_reported_response",
            "operational_outcome",
            "remaining_uncertainty",
        ],
        "reconstruction sequence mismatch",
    )

    required_false = [
        "internal_console_rationale_reconstructed",
        "unreported_options_invented",
        "exact_unreported_times_invented",
        "root_cause_inferred",
    ]

    for key in required_false:
        require(
            model.get(
                key
            )
            is False,
            (
                "reconstruction model "
                f"expected FALSE: {key}"
            ),
        )


def validate_thread_structure(
    threads: dict[str, dict],
):
    require(
        set(
            threads
        )
        == {
            FD1_THREAD_ID,
            FD4_THREAD_ID,
        },
        "operational thread set mismatch",
    )

    for (
        thread_id,
        expected_count,
    ) in EXPECTED_STEP_COUNTS.items():
        thread = (
            threads[
                thread_id
            ]
        )

        steps = (
            thread[
                "operational_sequence"
            ]
        )

        require(
            len(
                steps
            )
            == expected_count,
            (
                f"{thread_id} expected "
                f"{expected_count} steps, "
                f"found {len(steps)}"
            ),
        )

        observed_step_ids = [
            step[
                "step_id"
            ]
            for step in steps
        ]

        require(
            observed_step_ids
            == EXPECTED_STEP_IDS[
                thread_id
            ],
            (
                f"{thread_id} step "
                "ordering mismatch"
            ),
        )

        observed_numbers = [
            step[
                "step_number"
            ]
            for step in steps
        ]

        require(
            observed_numbers
            == list(
                range(
                    1,
                    expected_count + 1,
                )
            ),
            (
                f"{thread_id} step "
                "numbering mismatch"
            ),
        )


def validate_fd1_thread(
    thread: dict,
):
    require(
        thread[
            "classification"
        ]
        == (
            "IN_FLIGHT_OPERATIONAL_"
            "ISSUE_RESOLVED"
        ),
        "FD1 classification mismatch",
    )

    require(
        thread[
            "anomaly_confirmed"
        ]
        is False,
        "FD1 incorrectly claims "
        "confirmed anomaly",
    )

    require(
        thread[
            "fault_indication_reported"
        ]
        is True,
        "FD1 fault indication missing",
    )

    require(
        thread[
            "complete_uwms_failure_established"
        ]
        is False,
        "FD1 incorrectly establishes "
        "complete UWMS failure",
    )

    require(
        thread[
            "normal_operations_restored"
        ]
        is True,
        "FD1 restoration missing",
    )

    require(
        thread[
            "root_cause_publicly_established"
        ]
        is False,
        "FD1 incorrectly claims "
        "public root cause",
    )

    require(
        thread[
            "exact_event_utc_publicly_established"
        ]
        is False,
        "FD1 incorrectly claims "
        "exact event UTC",
    )

    require(
        thread[
            "internal_decision_tree_publicly_available"
        ]
        is False,
        "FD1 incorrectly claims "
        "internal decision tree",
    )

    require(
        thread[
            "outcome"
        ]
        == (
            "RESOLVED_IN_FLIGHT_WITH_"
            "ROOT_CAUSE_UNRESOLVED"
        ),
        "FD1 outcome mismatch",
    )


def validate_fd4_thread(
    thread: dict,
):
    require(
        thread[
            "classification"
        ]
        == (
            "IN_FLIGHT_OPERATIONAL_"
            "ISSUE_MANAGED"
        ),
        "FD4 classification mismatch",
    )

    require(
        thread[
            "anomaly_confirmed"
        ]
        is False,
        "FD4 incorrectly claims "
        "confirmed anomaly",
    )

    require(
        thread[
            "vent_ended_early"
        ]
        is True,
        "FD4 early vent ending missing",
    )

    require(
        thread[
            "tank_full"
        ]
        is False,
        "FD4 incorrectly marks tank full",
    )

    require(
        thread[
            "toilet_operational"
        ]
        is True,
        "FD4 toilet-operational "
        "status missing",
    )

    require(
        thread[
            "possible_ice_considered"
        ]
        is True,
        "FD4 possible-ice hypothesis "
        "missing",
    )

    require(
        thread[
            "ice_confirmed"
        ]
        is False,
        "FD4 incorrectly confirms ice",
    )

    require(
        thread[
            "other_causes_reviewed"
        ]
        is True,
        "FD4 other-cause review "
        "boundary missing",
    )

    require(
        thread[
            "postflight_investigation_continued"
        ]
        is True,
        "FD4 postflight investigation "
        "missing",
    )

    require(
        thread[
            "root_cause_publicly_established"
        ]
        is False,
        "FD4 incorrectly claims "
        "public root cause",
    )

    require(
        thread[
            "exact_event_utc_publicly_established"
        ]
        is False,
        "FD4 incorrectly claims "
        "exact event UTC",
    )

    require(
        thread[
            "internal_decision_tree_publicly_available"
        ]
        is False,
        "FD4 incorrectly claims "
        "internal decision tree",
    )

    require(
        thread[
            "outcome"
        ]
        == (
            "MANAGED_IN_FLIGHT_WITH_"
            "POSTFLIGHT_INVESTIGATION"
        ),
        "FD4 outcome mismatch",
    )


def validate_step_traceability(
    threads: dict[str, dict],
    events: dict[str, dict],
    sources: dict[str, dict],
):
    all_step_ids = set()

    for (
        thread_id,
        thread,
    ) in threads.items():
        for step in thread[
            "operational_sequence"
        ]:
            step_id = (
                step[
                    "step_id"
                ]
            )

            require(
                step_id not in all_step_ids,
                (
                    "duplicate operational "
                    f"step ID: {step_id}"
                ),
            )

            all_step_ids.add(
                step_id
            )

            require(
                step[
                    "thread_id"
                ]
                == thread_id,
                (
                    f"{step_id} thread "
                    "identity mismatch"
                ),
            )

            require(
                step[
                    "provenance"
                ]
                == (
                    "MISSIONLAB_DERIVED_"
                    "OPERATIONAL_RECONSTRUCTION"
                ),
                (
                    f"{step_id} provenance "
                    "mismatch"
                ),
            )

            require(
                step[
                    "inferred_internal_rationale"
                ]
                is False,
                (
                    f"{step_id} infers "
                    "internal rationale"
                ),
            )

            require(
                step[
                    "exact_utc_known"
                ]
                is False,
                (
                    f"{step_id} fabricates "
                    "exact UTC"
                ),
            )

            require(
                step[
                    "root_cause_claim"
                ]
                is False,
                (
                    f"{step_id} claims "
                    "root cause"
                ),
            )

            require(
                isinstance(
                    step[
                        "event_ids"
                    ],
                    list,
                )
                and len(
                    step[
                        "event_ids"
                    ]
                )
                >= 1,
                (
                    f"{step_id} missing "
                    "event traceability"
                ),
            )

            require(
                isinstance(
                    step[
                        "source_ids"
                    ],
                    list,
                )
                and len(
                    step[
                        "source_ids"
                    ]
                )
                >= 1,
                (
                    f"{step_id} missing "
                    "source traceability"
                ),
            )

            for event_id in step[
                "event_ids"
            ]:
                require(
                    event_id in events,
                    (
                        f"{step_id} references "
                        "unknown event "
                        f"{event_id}"
                    ),
                )

            for source_id in step[
                "source_ids"
            ]:
                require(
                    source_id in sources,
                    (
                        f"{step_id} references "
                        "unknown source "
                        f"{source_id}"
                    ),
                )


def validate_reference_alignment(
    threads: dict[str, dict],
    events: dict[str, dict],
):
    fd1_fault = (
        events[
            "A2_UWMS_FD1_FAULT_LIGHT"
        ][
            "nasa_reported"
        ]
    )

    fd1_restored = (
        events[
            "A2_UWMS_FD1_RESTORED"
        ][
            "nasa_reported"
        ]
    )

    fd4_vent = (
        events[
            "A2_UWMS_FD4_"
            "WASTEWATER_VENT_EARLY_END"
        ][
            "nasa_reported"
        ]
    )

    fd4_heater = (
        events[
            "A2_UWMS_FD4_"
            "VENT_HEATER_RESPONSE"
        ][
            "nasa_reported"
        ]
    )

    fd4_postflight = (
        events[
            "A2_UWMS_POSTFLIGHT_"
            "URINE_VENT_INVESTIGATION"
        ][
            "nasa_reported"
        ]
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
        fd1_fault[
            "root_cause"
        ]
        is None
        and fd1[
            "root_cause_publicly_established"
        ]
        is False,
        "FD1 root-cause boundary "
        "does not match reference",
    )

    require(
        fd1_restored[
            "operational_status"
        ]
        == "NORMAL_OPERATIONS_RESTORED"
        and fd1[
            "normal_operations_restored"
        ]
        is True,
        "FD1 restoration does not "
        "match reference",
    )

    require(
        fd4_vent[
            "tank_full"
        ]
        is False
        and fd4[
            "tank_full"
        ]
        is False,
        "FD4 tank status does not "
        "match reference",
    )

    require(
        fd4_vent[
            "toilet_operational"
        ]
        is True
        and fd4[
            "toilet_operational"
        ]
        is True,
        "FD4 toilet status does not "
        "match reference",
    )

    require(
        fd4_heater[
            "confirmed_ice_blockage"
        ]
        is False
        and fd4[
            "ice_confirmed"
        ]
        is False,
        "FD4 ice boundary does not "
        "match reference",
    )

    require(
        fd4_heater[
            "other_causes_under_review"
        ]
        is True
        and fd4[
            "other_causes_reviewed"
        ]
        is True,
        "FD4 other-causes boundary "
        "does not match reference",
    )

    require(
        fd4_postflight[
            "investigation_status"
        ]
        == "ONGOING"
        and fd4[
            "postflight_investigation_continued"
        ]
        is True,
        "FD4 postflight investigation "
        "does not match reference",
    )


def validate_cross_thread(
    output: dict,
):
    assessment = (
        output[
            "cross_thread_assessment"
        ]
    )

    require(
        assessment[
            "thread_count"
        ]
        == 2,
        "cross-thread count mismatch",
    )

    required_false = [
        "flight_day_1_and_flight_day_4_are_same_issue",
        "causal_relationship_between_threads_established",
        "shared_root_cause_established",
    ]

    for key in required_false:
        require(
            assessment.get(
                key
            )
            is False,
            (
                "cross-thread boundary "
                f"expected FALSE: {key}"
            ),
        )

    require(
        assessment[
            "shared_system_domain"
        ]
        == "Orion waste management",
        "shared system-domain mismatch",
    )


def validate_evidence_boundary(
    output: dict,
):
    boundary = (
        output[
            "evidence_boundary"
        ]
    )

    required_true = [
        "public_observations_preserved",
        "public_responses_preserved",
        "public_outcomes_preserved",
        "missionlab_sequence_is_derived",
    ]

    required_false = [
        "missionlab_sequence_equals_internal_console_log",
        "missionlab_sequence_equals_flight_rule_logic",
        "internal_fault_codes_available",
        "complete_internal_telemetry_available",
        "flight_day_1_root_cause_known",
        "flight_day_4_root_cause_known",
        "flight_day_4_ice_confirmed",
        "flight_day_4_complete_toilet_failure",
        "causal_relationship_between_fd1_and_fd4_known",
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


def validate_csv_matches_json(
    csv_rows: list[dict],
    threads: dict[str, dict],
):
    expected_rows = []

    for thread_id in [
        FD1_THREAD_ID,
        FD4_THREAD_ID,
    ]:
        expected_rows.extend(
            threads[
                thread_id
            ][
                "operational_sequence"
            ]
        )

    require(
        len(
            csv_rows
        )
        == 16,
        (
            "operational steps CSV "
            f"contains {len(csv_rows)} "
            "rows instead of 16"
        ),
    )

    require(
        len(
            expected_rows
        )
        == 16,
        "thread JSON does not contain "
        "16 operational steps",
    )

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
            "thread_id",
            "step_id",
            "step_type",
            "title",
            "statement",
            "evidence_class",
            "public_status",
            "provenance",
        ]

        for field in scalar_fields:
            require(
                csv_row[
                    field
                ]
                == str(
                    json_row[
                        field
                    ]
                ),
                (
                    f"CSV row {index} "
                    f"{field} mismatch"
                ),
            )

        require(
            int(
                csv_row[
                    "step_number"
                ]
            )
            == json_row[
                "step_number"
            ],
            (
                f"CSV row {index} "
                "step number mismatch"
            ),
        )

        csv_events = (
            csv_row[
                "event_ids"
            ].split(
                "|"
            )
        )

        csv_sources = (
            csv_row[
                "source_ids"
            ].split(
                "|"
            )
        )

        require(
            csv_events
            == json_row[
                "event_ids"
            ],
            (
                f"CSV row {index} "
                "event IDs mismatch"
            ),
        )

        require(
            csv_sources
            == json_row[
                "source_ids"
            ],
            (
                f"CSV row {index} "
                "source IDs mismatch"
            ),
        )

        require(
            bool_from_csv(
                csv_row[
                    "inferred_internal_rationale"
                ],
                "inferred_internal_rationale",
            )
            == json_row[
                "inferred_internal_rationale"
            ],
            (
                f"CSV row {index} "
                "internal rationale mismatch"
            ),
        )

        require(
            bool_from_csv(
                csv_row[
                    "exact_utc_known"
                ],
                "exact_utc_known",
            )
            == json_row[
                "exact_utc_known"
            ],
            (
                f"CSV row {index} "
                "exact UTC mismatch"
            ),
        )

        require(
            bool_from_csv(
                csv_row[
                    "root_cause_claim"
                ],
                "root_cause_claim",
            )
            == json_row[
                "root_cause_claim"
            ],
            (
                f"CSV row {index} "
                "root cause flag mismatch"
            ),
        )


def validate_outputs(
    output: dict,
):
    outputs = (
        output[
            "outputs"
        ]
    )

    require(
        outputs[
            "operational_threads_json"
        ]
        == (
            "data\\processed\\eclss\\"
            "waste_management_operational_threads.json"
        )
        or outputs[
            "operational_threads_json"
        ]
        == (
            "data/processed/eclss/"
            "waste_management_operational_threads.json"
        ),
        "operational threads output "
        "path mismatch",
    )

    require(
        outputs[
            "operational_steps_csv"
        ]
        == (
            "data\\processed\\eclss\\"
            "waste_management_operational_steps.csv"
        )
        or outputs[
            "operational_steps_csv"
        ]
        == (
            "data/processed/eclss/"
            "waste_management_operational_steps.csv"
        ),
        "operational steps output "
        "path mismatch",
    )

    require(
        outputs[
            "decision_thread_figure"
        ]
        == (
            "docs\\assets\\eclss\\"
            "phase3b2_waste_management_decision_threads.svg"
        )
        or outputs[
            "decision_thread_figure"
        ]
        == (
            "docs/assets/eclss/"
            "phase3b2_waste_management_decision_threads.svg"
        ),
        "decision-thread figure "
        "path mismatch",
    )


def validate_svg():
    require(
        FIGURE_PATH.exists(),
        (
            "missing Phase 3B.2 "
            f"figure: {FIGURE_PATH}"
        ),
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 3B.2 figure is empty",
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
        "Phase 3B.2 figure is "
        "not valid SVG text",
    )


def main():
    print()
    print(
        "Phase 3B.2 Artemis II "
        "Waste Management Operational "
        "Decision Reconstruction Validation"
    )
    print(
        "=" * 72
    )

    reference = load_json(
        REFERENCE_PATH
    )

    output = load_json(
        THREADS_JSON
    )

    csv_rows = load_csv(
        STEPS_CSV
    )

    validate_identity(
        reference,
        output,
    )

    print()
    print(
        "Analysis identity: PASS"
    )

    validate_dependency(
        reference,
        output,
    )

    print(
        "Phase 3B.1 dependency: PASS"
    )

    validate_reconstruction_model(
        output
    )

    print(
        "Reconstruction model: PASS"
    )

    events = index_events(
        reference
    )

    sources = index_sources(
        reference
    )

    require(
        set(
            events
        )
        == EXPECTED_EVENT_IDS,
        "reference event set changed",
    )

    threads = index_threads(
        output
    )

    validate_thread_structure(
        threads
    )

    print()
    print(
        "Operational thread set: PASS"
    )
    print(
        "Step ordering and numbering: PASS"
    )
    print(
        "16-step reconstruction: PASS"
    )

    validate_fd1_thread(
        threads[
            FD1_THREAD_ID
        ]
    )

    print()
    print(
        "Flight Day 1 fault thread: PASS"
    )
    print(
        "Flight Day 1 recovery: PASS"
    )
    print(
        "Flight Day 1 root-cause "
        "boundary: PASS"
    )

    validate_fd4_thread(
        threads[
            FD4_THREAD_ID
        ]
    )

    print()
    print(
        "Flight Day 4 vent thread: PASS"
    )
    print(
        "Tank-not-full status: PASS"
    )
    print(
        "Toilet-operational status: PASS"
    )
    print(
        "Possible-ice hypothesis: PASS"
    )
    print(
        "Ice-confirmation boundary: PASS"
    )
    print(
        "Postflight investigation: PASS"
    )
    print(
        "Flight Day 4 root-cause "
        "boundary: PASS"
    )

    validate_step_traceability(
        threads,
        events,
        sources,
    )

    print()
    print(
        "Step-event traceability: PASS"
    )
    print(
        "Step-source traceability: PASS"
    )
    print(
        "No inferred internal rationale: PASS"
    )
    print(
        "No fabricated exact UTCs: PASS"
    )
    print(
        "No root-cause claims: PASS"
    )

    validate_reference_alignment(
        threads,
        events,
    )

    print(
        "Reference evidence alignment: PASS"
    )

    validate_cross_thread(
        output
    )

    print()
    print(
        "FD1 / FD4 issue separation: PASS"
    )
    print(
        "Shared-root-cause boundary: PASS"
    )
    print(
        "Cross-thread causality boundary: PASS"
    )

    validate_evidence_boundary(
        output
    )

    print(
        "Evidence-boundary policy: PASS"
    )

    validate_csv_matches_json(
        csv_rows,
        threads,
    )

    print(
        "Operational CSV / JSON "
        "consistency: PASS"
    )

    validate_outputs(
        output
    )

    validate_svg()

    print(
        "Documentation figure: PASS"
    )

    print()
    print(
        "Validated reconstruction:"
    )
    print(
        "  operational threads: 2"
    )
    print(
        "  Flight Day 1 steps: 6"
    )
    print(
        "  Flight Day 4 steps: 10"
    )
    print(
        "  total operational steps: 16"
    )

    print()
    print(
        "Key operational boundaries:"
    )
    print(
        "  FD1 fault indication "
        "!= complete UWMS failure"
    )
    print(
        "  FD1 restoration "
        "!= known root cause"
    )
    print(
        "  FD4 vent ended early "
        "!= complete toilet failure"
    )
    print(
        "  tank full: FALSE"
    )
    print(
        "  toilet operational: TRUE"
    )
    print(
        "  possible ice "
        "!= confirmed ice"
    )
    print(
        "  internal console rationale "
        "reconstructed: FALSE"
    )
    print(
        "  FD1 / FD4 causal "
        "relationship established: FALSE"
    )

    print()
    print(
        "PHASE 3B.2 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
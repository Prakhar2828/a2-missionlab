from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


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

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "eclss"
)

THREAD_FIGURE = (
    ASSET_DIR
    / "phase3b2_waste_management_decision_threads.svg"
)

EXPECTED_REFERENCE_ID = (
    "phase3b1_artemis_ii_"
    "waste_management_evidence"
)

FD1_THREAD_ID = (
    "flight_day_1_toilet_fault_and_recovery"
)

FD4_THREAD_ID = (
    "flight_day_4_urine_wastewater_vent_line_issue"
)

plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 3B.2 ANALYSIS FAILED: "
        f"{message}"
    )


def load_reference() -> dict:
    if not REFERENCE_PATH.exists():
        fail(
            "missing Phase 3B.1 "
            f"reference product: {REFERENCE_PATH}"
        )

    with REFERENCE_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        data = json.load(
            f
        )

    if (
        data.get(
            "dataset_id"
        )
        != EXPECTED_REFERENCE_ID
    ):
        fail(
            "unexpected Phase 3B.1 "
            "reference dataset"
        )

    if (
        data.get(
            "phase"
        )
        != "3B.1"
    ):
        fail(
            "Phase 3B.1 identity mismatch"
        )

    return data


def event_index(
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

        if event_id in result:
            fail(
                "duplicate evidence event: "
                f"{event_id}"
            )

        result[
            event_id
        ] = event

    return result


def require_event(
    events: dict[str, dict],
    event_id: str,
) -> dict:
    if event_id not in events:
        fail(
            "missing required evidence "
            f"event: {event_id}"
        )

    return events[
        event_id
    ]


def source_union(
    events: list[dict],
) -> list[str]:
    result = []

    for event in events:
        for source_id in event[
            "source_ids"
        ]:
            if source_id not in result:
                result.append(
                    source_id
                )

    return result


def make_step(
    *,
    thread_id: str,
    step_number: int,
    step_id: str,
    step_type: str,
    title: str,
    statement: str,
    evidence_class: str,
    event_ids: list[str],
    source_ids: list[str],
    public_status: str,
    inferred_internal_rationale: bool = False,
    exact_utc_known: bool = False,
    root_cause_claim: bool = False,
) -> dict:
    return {
        "thread_id": (
            thread_id
        ),
        "step_number": (
            step_number
        ),
        "step_id": (
            step_id
        ),
        "step_type": (
            step_type
        ),
        "title": (
            title
        ),
        "statement": (
            statement
        ),
        "evidence_class": (
            evidence_class
        ),
        "event_ids": (
            event_ids
        ),
        "source_ids": (
            source_ids
        ),
        "public_status": (
            public_status
        ),
        "inferred_internal_rationale": (
            inferred_internal_rationale
        ),
        "exact_utc_known": (
            exact_utc_known
        ),
        "root_cause_claim": (
            root_cause_claim
        ),
        "provenance": (
            "MISSIONLAB_DERIVED_"
            "OPERATIONAL_RECONSTRUCTION"
        ),
    }


def build_fd1_thread(
    events: dict[str, dict],
) -> dict:
    fault = require_event(
        events,
        "A2_UWMS_FD1_FAULT_LIGHT",
    )

    restored = require_event(
        events,
        "A2_UWMS_FD1_RESTORED",
    )

    shared_sources = (
        source_union(
            [
                fault,
                restored,
            ]
        )
    )

    steps = [
        make_step(
            thread_id=FD1_THREAD_ID,
            step_number=1,
            step_id="fd1_observation",
            step_type="OBSERVATION",
            title=(
                "Toilet checkout "
                "produces fault indication"
            ),
            statement=(
                "During toilet-system "
                "checkout, the crew "
                "reported a blinking "
                "fault light."
            ),
            evidence_class="NASA_REPORTED",
            event_ids=[
                fault[
                    "event_id"
                ]
            ],
            source_ids=(
                fault[
                    "source_ids"
                ]
            ),
            public_status=(
                "DIRECTLY_REPORTED"
            ),
        ),
        make_step(
            thread_id=FD1_THREAD_ID,
            step_number=2,
            step_id="fd1_constraint",
            step_type="OPERATIONAL_CONSTRAINT",
            title=(
                "Fault exists without "
                "public component diagnosis"
            ),
            statement=(
                "The public record "
                "establishes a fault "
                "indication but does not "
                "identify an internal fault "
                "code, failed component, "
                "or complete UWMS failure."
            ),
            evidence_class=(
                "MISSIONLAB_DERIVED_"
                "BOUNDARY"
            ),
            event_ids=[
                fault[
                    "event_id"
                ]
            ],
            source_ids=(
                fault[
                    "source_ids"
                ]
            ),
            public_status=(
                "DERIVED_FROM_PUBLIC_LIMITS"
            ),
        ),
        make_step(
            thread_id=FD1_THREAD_ID,
            step_number=3,
            step_id="fd1_evidence_review",
            step_type="EVIDENCE_ASSESSMENT",
            title=(
                "Mission Control "
                "assesses available data"
            ),
            statement=(
                "NASA reported that "
                "Mission Control assessed "
                "available data while "
                "working with the crew "
                "to troubleshoot the issue."
            ),
            evidence_class="NASA_REPORTED",
            event_ids=[
                fault[
                    "event_id"
                ]
            ],
            source_ids=(
                fault[
                    "source_ids"
                ]
            ),
            public_status=(
                "DIRECTLY_REPORTED"
            ),
        ),
        make_step(
            thread_id=FD1_THREAD_ID,
            step_number=4,
            step_id="fd1_response",
            step_type="NASA_REPORTED_RESPONSE",
            title=(
                "Crew and ground "
                "perform troubleshooting"
            ),
            statement=(
                "Crew and Mission Control "
                "performed troubleshooting. "
                "The public record does not "
                "provide the complete "
                "internal decision tree or "
                "specific corrective action."
            ),
            evidence_class=(
                "NASA_REPORTED_WITH_"
                "PUBLIC_LIMIT"
            ),
            event_ids=[
                fault[
                    "event_id"
                ],
                restored[
                    "event_id"
                ],
            ],
            source_ids=(
                shared_sources
            ),
            public_status=(
                "RESPONSE_REPORTED_"
                "RATIONALE_INCOMPLETE"
            ),
        ),
        make_step(
            thread_id=FD1_THREAD_ID,
            step_number=5,
            step_id="fd1_outcome",
            step_type="OUTCOME",
            title=(
                "Normal toilet "
                "operations restored"
            ),
            statement=(
                "NASA reported that "
                "crew and Mission Control "
                "restored Orion's toilet "
                "to normal operations."
            ),
            evidence_class="NASA_REPORTED",
            event_ids=[
                restored[
                    "event_id"
                ]
            ],
            source_ids=(
                restored[
                    "source_ids"
                ]
            ),
            public_status=(
                "RESOLVED_IN_FLIGHT"
            ),
        ),
        make_step(
            thread_id=FD1_THREAD_ID,
            step_number=6,
            step_id="fd1_uncertainty",
            step_type="REMAINING_UNCERTAINTY",
            title=(
                "Root cause remains "
                "unresolved publicly"
            ),
            statement=(
                "Successful restoration "
                "does not establish the "
                "original fault mechanism. "
                "The failed component, "
                "internal fault code, and "
                "root cause remain "
                "unavailable in the "
                "curated public record."
            ),
            evidence_class=(
                "MISSIONLAB_DERIVED_"
                "EVIDENCE_BOUNDARY"
            ),
            event_ids=[
                fault[
                    "event_id"
                ],
                restored[
                    "event_id"
                ],
            ],
            source_ids=(
                shared_sources
            ),
            public_status=(
                "ROOT_CAUSE_UNRESOLVED"
            ),
        ),
    ]

    return {
        "thread_id": (
            FD1_THREAD_ID
        ),
        "thread_name": (
            "Flight Day 1 Toilet "
            "Fault and Recovery"
        ),
        "classification": (
            "IN_FLIGHT_OPERATIONAL_"
            "ISSUE_RESOLVED"
        ),
        "anomaly_confirmed": (
            False
        ),
        "fault_indication_reported": (
            True
        ),
        "complete_uwms_failure_established": (
            False
        ),
        "normal_operations_restored": (
            True
        ),
        "root_cause_publicly_established": (
            False
        ),
        "exact_event_utc_publicly_established": (
            False
        ),
        "internal_decision_tree_publicly_available": (
            False
        ),
        "outcome": (
            "RESOLVED_IN_FLIGHT_WITH_"
            "ROOT_CAUSE_UNRESOLVED"
        ),
        "operational_sequence": (
            steps
        ),
    }


def build_fd4_thread(
    events: dict[str, dict],
) -> dict:
    vent = require_event(
        events,
        "A2_UWMS_FD4_"
        "WASTEWATER_VENT_EARLY_END",
    )

    heater = require_event(
        events,
        "A2_UWMS_FD4_"
        "VENT_HEATER_RESPONSE",
    )

    solar = require_event(
        events,
        "A2_UWMS_FD4_"
        "SOLAR_POINTING",
    )

    backup = require_event(
        events,
        "A2_UWMS_FD4_"
        "BACKUP_COLLECTION_POSTURE",
    )

    postflight = require_event(
        events,
        "A2_UWMS_POSTFLIGHT_"
        "URINE_VENT_INVESTIGATION",
    )

    all_events = [
        vent,
        heater,
        solar,
        backup,
        postflight,
    ]

    shared_sources = (
        source_union(
            all_events
        )
    )

    steps = [
        make_step(
            thread_id=FD4_THREAD_ID,
            step_number=1,
            step_id="fd4_nominal_activity",
            step_type="PLANNED_OPERATION",
            title=(
                "Wastewater venting "
                "performed"
            ),
            statement=(
                "Wastewater was vented "
                "overboard to create "
                "additional capacity in "
                "the waste-management "
                "system tank."
            ),
            evidence_class="NASA_REPORTED",
            event_ids=[
                vent[
                    "event_id"
                ]
            ],
            source_ids=(
                vent[
                    "source_ids"
                ]
            ),
            public_status=(
                "DIRECTLY_REPORTED"
            ),
        ),
        make_step(
            thread_id=FD4_THREAD_ID,
            step_number=2,
            step_id="fd4_observation",
            step_type="OBSERVATION",
            title=(
                "Vent activity ends "
                "earlier than expected"
            ),
            statement=(
                "NASA reported that the "
                "overboard wastewater "
                "vent activity ended "
                "earlier than expected."
            ),
            evidence_class="NASA_REPORTED",
            event_ids=[
                vent[
                    "event_id"
                ]
            ],
            source_ids=(
                vent[
                    "source_ids"
                ]
            ),
            public_status=(
                "DIRECTLY_REPORTED"
            ),
        ),
        make_step(
            thread_id=FD4_THREAD_ID,
            step_number=3,
            step_id="fd4_operational_state",
            step_type="OPERATIONAL_CONSTRAINT",
            title=(
                "Toilet remains usable "
                "and tank is not full"
            ),
            statement=(
                "NASA explicitly reported "
                "that the wastewater tank "
                "was not full and that the "
                "toilet remained operational."
            ),
            evidence_class="NASA_REPORTED",
            event_ids=[
                vent[
                    "event_id"
                ],
                backup[
                    "event_id"
                ],
            ],
            source_ids=(
                source_union(
                    [
                        vent,
                        backup,
                    ]
                )
            ),
            public_status=(
                "SYSTEM_FUNCTION_PARTIALLY_"
                "AVAILABLE"
            ),
        ),
        make_step(
            thread_id=FD4_THREAD_ID,
            step_number=4,
            step_id="fd4_hypothesis",
            step_type="EVIDENCE_ASSESSMENT",
            title=(
                "Possible ice considered "
                "among candidate causes"
            ),
            statement=(
                "Possible ice in the "
                "vent line was considered "
                "as one hypothesis while "
                "teams also reviewed other "
                "potential causes."
            ),
            evidence_class=(
                "NASA_REPORTED_"
                "WORKING_HYPOTHESIS"
            ),
            event_ids=[
                vent[
                    "event_id"
                ],
                heater[
                    "event_id"
                ],
            ],
            source_ids=(
                source_union(
                    [
                        vent,
                        heater,
                    ]
                )
            ),
            public_status=(
                "CAUSE_UNCONFIRMED"
            ),
        ),
        make_step(
            thread_id=FD4_THREAD_ID,
            step_number=5,
            step_id="fd4_heater_response",
            step_type="NASA_REPORTED_RESPONSE",
            title=(
                "Vent heaters used"
            ),
            statement=(
                "Engineers used vent "
                "heaters to melt any "
                "potential ice that could "
                "be affecting the line."
            ),
            evidence_class="NASA_REPORTED",
            event_ids=[
                heater[
                    "event_id"
                ]
            ],
            source_ids=(
                heater[
                    "source_ids"
                ]
            ),
            public_status=(
                "TROUBLESHOOTING_ACTION"
            ),
        ),
        make_step(
            thread_id=FD4_THREAD_ID,
            step_number=6,
            step_id="fd4_solar_response",
            step_type="NASA_REPORTED_RESPONSE",
            title=(
                "Vent pointed toward Sun"
            ),
            statement=(
                "Orion's attitude was "
                "adjusted so the vent "
                "faced the Sun as part "
                "of continued vent-line "
                "troubleshooting."
            ),
            evidence_class="NASA_REPORTED",
            event_ids=[
                solar[
                    "event_id"
                ]
            ],
            source_ids=(
                solar[
                    "source_ids"
                ]
            ),
            public_status=(
                "TROUBLESHOOTING_ACTION"
            ),
        ),
        make_step(
            thread_id=FD4_THREAD_ID,
            step_number=7,
            step_id="fd4_contingency",
            step_type="CONTINGENCY_POSTURE",
            title=(
                "Backup collection "
                "devices available"
            ),
            statement=(
                "The crew was instructed "
                "to use backup collection "
                "devices overnight if "
                "needed while the toilet "
                "remained operational."
            ),
            evidence_class="NASA_REPORTED",
            event_ids=[
                backup[
                    "event_id"
                ]
            ],
            source_ids=(
                backup[
                    "source_ids"
                ]
            ),
            public_status=(
                "CONTINGENCY_AVAILABLE"
            ),
        ),
        make_step(
            thread_id=FD4_THREAD_ID,
            step_number=8,
            step_id="fd4_inflight_outcome",
            step_type="OUTCOME",
            title=(
                "Issue managed without "
                "complete toilet loss"
            ),
            statement=(
                "Public reporting supports "
                "continued toilet operation "
                "and use of operational "
                "workarounds, but does not "
                "establish that the vent-line "
                "issue was fully resolved "
                "during flight."
            ),
            evidence_class=(
                "MISSIONLAB_DERIVED_"
                "OPERATIONAL_SYNTHESIS"
            ),
            event_ids=[
                vent[
                    "event_id"
                ],
                heater[
                    "event_id"
                ],
                solar[
                    "event_id"
                ],
                backup[
                    "event_id"
                ],
            ],
            source_ids=(
                source_union(
                    [
                        vent,
                        heater,
                        solar,
                        backup,
                    ]
                )
            ),
            public_status=(
                "MANAGED_IN_FLIGHT"
            ),
        ),
        make_step(
            thread_id=FD4_THREAD_ID,
            step_number=9,
            step_id="fd4_postflight",
            step_type="POSTFLIGHT_FOLLOWUP",
            title=(
                "Hardware and data "
                "investigation continues"
            ),
            statement=(
                "NASA's initial postflight "
                "assessment reported "
                "continued hardware "
                "assessment and data "
                "gathering related to the "
                "urine vent-line issue."
            ),
            evidence_class="NASA_REPORTED",
            event_ids=[
                postflight[
                    "event_id"
                ]
            ],
            source_ids=(
                postflight[
                    "source_ids"
                ]
            ),
            public_status=(
                "POSTFLIGHT_INVESTIGATION_"
                "ONGOING"
            ),
        ),
        make_step(
            thread_id=FD4_THREAD_ID,
            step_number=10,
            step_id="fd4_uncertainty",
            step_type="REMAINING_UNCERTAINTY",
            title=(
                "Final root cause "
                "remains unresolved"
            ),
            statement=(
                "The curated public "
                "record does not establish "
                "confirmed ice, a failed "
                "component, or a final "
                "root cause for the "
                "vent-line issue."
            ),
            evidence_class=(
                "MISSIONLAB_DERIVED_"
                "EVIDENCE_BOUNDARY"
            ),
            event_ids=[
                event[
                    "event_id"
                ]
                for event
                in all_events
            ],
            source_ids=(
                shared_sources
            ),
            public_status=(
                "ROOT_CAUSE_UNRESOLVED"
            ),
        ),
    ]

    return {
        "thread_id": (
            FD4_THREAD_ID
        ),
        "thread_name": (
            "Flight Day 4 Urine / "
            "Wastewater Vent-Line Issue"
        ),
        "classification": (
            "IN_FLIGHT_OPERATIONAL_"
            "ISSUE_MANAGED"
        ),
        "anomaly_confirmed": (
            False
        ),
        "vent_ended_early": (
            True
        ),
        "tank_full": (
            False
        ),
        "toilet_operational": (
            True
        ),
        "possible_ice_considered": (
            True
        ),
        "ice_confirmed": (
            False
        ),
        "other_causes_reviewed": (
            True
        ),
        "postflight_investigation_continued": (
            True
        ),
        "root_cause_publicly_established": (
            False
        ),
        "exact_event_utc_publicly_established": (
            False
        ),
        "internal_decision_tree_publicly_available": (
            False
        ),
        "outcome": (
            "MANAGED_IN_FLIGHT_WITH_"
            "POSTFLIGHT_INVESTIGATION"
        ),
        "operational_sequence": (
            steps
        ),
    }


def flatten_steps(
    threads: list[dict],
) -> list[dict]:
    rows = []

    for thread in threads:
        for step in thread[
            "operational_sequence"
        ]:
            rows.append(
                step
            )

    return rows


def write_steps_csv(
    rows: list[dict],
):
    fieldnames = [
        "thread_id",
        "step_number",
        "step_id",
        "step_type",
        "title",
        "statement",
        "evidence_class",
        "event_ids",
        "source_ids",
        "public_status",
        "inferred_internal_rationale",
        "exact_utc_known",
        "root_cause_claim",
        "provenance",
    ]

    with STEPS_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:
            output = dict(
                row
            )

            output[
                "event_ids"
            ] = "|".join(
                row[
                    "event_ids"
                ]
            )

            output[
                "source_ids"
            ] = "|".join(
                row[
                    "source_ids"
                ]
            )

            writer.writerow(
                output
            )


def normalize_svg(
    path: Path,
):
    text = path.read_text(
        encoding="utf-8",
    )

    cleaned = "\n".join(
        line.rstrip(
            " \t"
        )
        for line
        in text.splitlines()
    )

    path.write_text(
        cleaned + "\n",
        encoding="utf-8",
    )


def build_thread_figure(
    threads: list[dict],
):
    rows = []

    for thread in threads:
        rows.append(
            [
                thread[
                    "thread_name"
                ],
                str(
                    len(
                        thread[
                            "operational_sequence"
                        ]
                    )
                ),
                thread[
                    "classification"
                ],
                thread[
                    "outcome"
                ],
                (
                    "YES"
                    if thread[
                        "root_cause_publicly_established"
                    ]
                    else "NO"
                ),
            ]
        )

    fig, ax = plt.subplots(
        figsize=(
            17,
            5.5,
        )
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        (
            "Artemis II Waste Management "
            "Operational Decision Threads"
        ),
        fontsize=15,
        pad=18,
    )

    table = ax.table(
        cellText=rows,
        colLabels=[
            "Operational Thread",
            "Steps",
            "Classification",
            "Public Outcome",
            "Root Cause Public?",
        ],
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        8
    )

    table.scale(
        1.0,
        2.2,
    )

    ax.text(
        0.5,
        0.06,
        (
            "MissionLab reconstructs only "
            "publicly supported observations, "
            "responses, outcomes, and evidence "
            "limits. Internal console rationale "
            "and unavailable telemetry are not "
            "inferred."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        THREAD_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        THREAD_FIGURE
    )


def validate_no_forbidden_claims(
    threads: list[dict],
):
    for thread in threads:
        if (
            thread[
                "root_cause_publicly_established"
            ]
            is not False
        ):
            fail(
                "thread incorrectly "
                "claims public root cause"
            )

        if (
            thread[
                "exact_event_utc_publicly_established"
            ]
            is not False
        ):
            fail(
                "thread incorrectly "
                "claims exact event UTC"
            )

        if (
            thread[
                "internal_decision_tree_publicly_available"
            ]
            is not False
        ):
            fail(
                "thread incorrectly claims "
                "internal decision tree"
            )

        for step in thread[
            "operational_sequence"
        ]:
            if (
                step[
                    "inferred_internal_rationale"
                ]
                is not False
            ):
                fail(
                    f"{step['step_id']} "
                    "infers internal rationale"
                )

            if (
                step[
                    "exact_utc_known"
                ]
                is not False
            ):
                fail(
                    f"{step['step_id']} "
                    "fabricates exact UTC"
                )

            if (
                step[
                    "root_cause_claim"
                ]
                is not False
            ):
                fail(
                    f"{step['step_id']} "
                    "claims root cause"
                )


def main():
    print()
    print(
        "Phase 3B.2 Artemis II "
        "Waste Management Operational "
        "Decision Reconstruction"
    )
    print(
        "=" * 72
    )

    reference = (
        load_reference()
    )

    events = (
        event_index(
            reference
        )
    )

    print()
    print(
        "Dependency:"
    )
    print(
        "  Phase 3B.1 public "
        "evidence reference: PASS"
    )

    fd1 = (
        build_fd1_thread(
            events
        )
    )

    fd4 = (
        build_fd4_thread(
            events
        )
    )

    threads = [
        fd1,
        fd4,
    ]

    validate_no_forbidden_claims(
        threads
    )

    steps = (
        flatten_steps(
            threads
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_steps_csv(
        steps
    )

    output = {
        "dataset_id": (
            "phase3b2_artemis_ii_"
            "waste_management_"
            "operational_threads"
        ),
        "mission": (
            "Artemis II"
        ),
        "phase": (
            "3B.2"
        ),
        "status": (
            "OPERATIONAL_RECONSTRUCTION_"
            "COMPLETE"
        ),
        "dependency": {
            "dataset_id": (
                reference[
                    "dataset_id"
                ]
            ),
            "source_event_count": (
                len(
                    reference[
                        "events"
                    ]
                )
            ),
            "source_count": (
                len(
                    reference[
                        "sources"
                    ]
                )
            ),
        },
        "reconstruction_model": {
            "sequence": [
                "observation",
                "constraint_or_evidence_state",
                "nasa_reported_response",
                "operational_outcome",
                "remaining_uncertainty",
            ],
            "internal_console_rationale_reconstructed": (
                False
            ),
            "unreported_options_invented": (
                False
            ),
            "exact_unreported_times_invented": (
                False
            ),
            "root_cause_inferred": (
                False
            ),
        },
        "threads": (
            threads
        ),
        "cross_thread_assessment": {
            "thread_count": (
                2
            ),
            "flight_day_1_and_flight_day_4_are_same_issue": (
                False
            ),
            "causal_relationship_between_threads_established": (
                False
            ),
            "shared_system_domain": (
                "Orion waste management"
            ),
            "shared_root_cause_established": (
                False
            ),
        },
        "evidence_boundary": {
            "public_observations_preserved": (
                True
            ),
            "public_responses_preserved": (
                True
            ),
            "public_outcomes_preserved": (
                True
            ),
            "missionlab_sequence_is_derived": (
                True
            ),
            "missionlab_sequence_equals_internal_console_log": (
                False
            ),
            "missionlab_sequence_equals_flight_rule_logic": (
                False
            ),
            "internal_fault_codes_available": (
                False
            ),
            "complete_internal_telemetry_available": (
                False
            ),
            "flight_day_1_root_cause_known": (
                False
            ),
            "flight_day_4_root_cause_known": (
                False
            ),
            "flight_day_4_ice_confirmed": (
                False
            ),
            "flight_day_4_complete_toilet_failure": (
                False
            ),
            "causal_relationship_between_fd1_and_fd4_known": (
                False
            ),
        },
        "outputs": {
            "operational_threads_json": str(
                THREADS_JSON.relative_to(
                    ROOT
                )
            ),
            "operational_steps_csv": str(
                STEPS_CSV.relative_to(
                    ROOT
                )
            ),
            "decision_thread_figure": str(
                THREAD_FIGURE.relative_to(
                    ROOT
                )
            ),
        },
    }

    with THREADS_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
        )

        f.write(
            "\n"
        )

    build_thread_figure(
        threads
    )

    print()
    print(
        "Operational threads:"
    )

    print()
    print(
        "  Flight Day 1:"
    )
    print(
        "    steps: "
        f"{len(fd1['operational_sequence'])}"
    )
    print(
        "    fault indication: YES"
    )
    print(
        "    complete UWMS failure "
        "established: NO"
    )
    print(
        "    normal operations "
        "restored: YES"
    )
    print(
        "    public root cause: NO"
    )

    print()
    print(
        "  Flight Day 4:"
    )
    print(
        "    steps: "
        f"{len(fd4['operational_sequence'])}"
    )
    print(
        "    vent ended early: YES"
    )
    print(
        "    tank full: NO"
    )
    print(
        "    toilet operational: YES"
    )
    print(
        "    possible ice considered: YES"
    )
    print(
        "    ice confirmed: NO"
    )
    print(
        "    postflight investigation: YES"
    )
    print(
        "    public root cause: NO"
    )

    print()
    print(
        "Cross-thread boundary:"
    )
    print(
        "  FD1 issue == FD4 issue: FALSE"
    )
    print(
        "  shared root cause "
        "established: FALSE"
    )
    print(
        "  causal relationship "
        "established: FALSE"
    )

    print()
    print(
        "Decision-reconstruction boundary:"
    )
    print(
        "  public observations: PRESERVED"
    )
    print(
        "  public responses: PRESERVED"
    )
    print(
        "  public outcomes: PRESERVED"
    )
    print(
        "  internal console rationale: "
        "NOT RECONSTRUCTED"
    )
    print(
        "  unreported options: "
        "NOT INVENTED"
    )
    print(
        "  exact unreported UTCs: "
        "NOT INVENTED"
    )
    print(
        "  root causes: NOT INFERRED"
    )

    print()
    print(
        "Generated:"
    )
    print(
        "  operational steps: "
        f"{len(steps)}"
    )
    print(
        "  operational threads: "
        f"{len(threads)}"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            THREADS_JSON.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            STEPS_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            THREAD_FIGURE.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 3B.2 OPERATIONAL "
        "RECONSTRUCTION COMPLETE"
    )


if __name__ == "__main__":
    main()
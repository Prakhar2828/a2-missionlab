from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


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

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "eclss"
)

FIGURE_PATH = (
    ASSET_DIR
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
}


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
        "PHASE 3B.3 ANALYSIS FAILED: "
        f"{message}"
    )


def load_json(
    path: Path,
) -> dict:
    if not path.exists():
        fail(
            f"missing dependency: {path}"
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

        if event_id in result:
            fail(
                "duplicate Phase 3B.1 "
                f"event: {event_id}"
            )

        result[
            event_id
        ] = event

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
        "missing Phase 2 mission "
        f"anchor: {event_id}"
    )

    raise RuntimeError


def require_event(
    events: dict[str, dict],
    event_id: str,
) -> dict:
    if event_id not in events:
        fail(
            "missing Phase 3B.1 "
            f"event: {event_id}"
        )

    return events[
        event_id
    ]


def validate_dependencies(
    phase3b1: dict,
    phase3b2: dict,
    phase2_maneuvers: dict,
    phase2_integrated: dict,
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
    }

    for (
        key,
        expected,
    ) in EXPECTED_IDS.items():
        if (
            observed[
                key
            ]
            != expected
        ):
            fail(
                f"{key} dataset ID mismatch"
            )


def make_correlation(
    *,
    correlation_id: str,
    source_thread_id: str,
    domain: str,
    phase3b_event_ids: list[str],
    phase2_anchor_ids: list[str],
    relationship_type: str,
    relationship_status: str,
    public_basis: str,
    missionlab_interpretation: str,
    causal_relationship_established: bool,
    mission_impact_claimed: bool,
    evidence_class: str,
) -> dict:
    return {
        "correlation_id": (
            correlation_id
        ),
        "source_thread_id": (
            source_thread_id
        ),
        "domain": (
            domain
        ),
        "phase3b_event_ids": (
            phase3b_event_ids
        ),
        "phase2_anchor_ids": (
            phase2_anchor_ids
        ),
        "relationship_type": (
            relationship_type
        ),
        "relationship_status": (
            relationship_status
        ),
        "public_basis": (
            public_basis
        ),
        "missionlab_interpretation": (
            missionlab_interpretation
        ),
        "causal_relationship_established": (
            causal_relationship_established
        ),
        "mission_impact_claimed": (
            mission_impact_claimed
        ),
        "evidence_class": (
            evidence_class
        ),
        "provenance": (
            "MISSIONLAB_DERIVED_"
            "CROSS_DOMAIN_CORRELATION"
        ),
    }


def build_correlations(
    events: dict[str, dict],
    phase2_maneuvers: dict,
    phase2_integrated: dict,
) -> tuple[
    list[dict],
    dict,
]:
    fd1_fault = require_event(
        events,
        "A2_UWMS_FD1_FAULT_LIGHT",
    )

    fd1_restored = require_event(
        events,
        "A2_UWMS_FD1_RESTORED",
    )

    fd4_vent = require_event(
        events,
        "A2_UWMS_FD4_"
        "WASTEWATER_VENT_EARLY_END",
    )

    fd4_heater = require_event(
        events,
        "A2_UWMS_FD4_"
        "VENT_HEATER_RESPONSE",
    )

    fd4_solar = require_event(
        events,
        "A2_UWMS_FD4_"
        "SOLAR_POINTING",
    )

    fd4_backup = require_event(
        events,
        "A2_UWMS_FD4_"
        "BACKUP_COLLECTION_POSTURE",
    )

    postflight = require_event(
        events,
        "A2_UWMS_POSTFLIGHT_"
        "URINE_VENT_INVESTIGATION",
    )

    outbound = get_thread(
        phase2_maneuvers[
            "threads"
        ],
        "outbound_adaptive_trajectory_management",
    )

    otc2_cancelled = get_step(
        outbound,
        "otc2_cancelled",
    )

    otc3_executed = get_step(
        outbound,
        "otc3_executed",
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

    if (
        otc2_cancelled.get(
            "status"
        )
        != "CANCELLED"
    ):
        fail(
            "OTC2 Phase 2 status "
            "is no longer CANCELLED"
        )

    if (
        otc2_cancelled.get(
            "reason_classification"
        )
        != (
            "TRAJECTORY_REMAINED_"
            "ON_TRACK"
        )
    ):
        fail(
            "OTC2 cancellation reason "
            "changed from Phase 2"
        )

    if (
        otc2_cancelled.get(
            "parallel_operational_activity"
        )
        != (
            "ATTITUDE_ADJUSTMENT_FOR_"
            "WASTEWATER_VENT_CLEARING"
        )
    ):
        fail(
            "Phase 2 wastewater "
            "parallel-activity anchor missing"
        )

    if (
        otc2_cancelled.get(
            "failed_burn"
        )
        is not False
    ):
        fail(
            "OTC2 incorrectly "
            "classified as failed burn"
        )

    if (
        otc2_cancelled.get(
            "propulsion_anomaly"
        )
        is not False
    ):
        fail(
            "OTC2 incorrectly "
            "classified as propulsion anomaly"
        )

    if (
        otc3_executed.get(
            "status"
        )
        != "EXECUTED"
    ):
        fail(
            "OTC3 execution anchor changed"
        )

    correlations = [
        make_correlation(
            correlation_id=(
                "WM_FD1_CREW_GROUND_RECOVERY"
            ),
            source_thread_id=(
                FD1_THREAD_ID
            ),
            domain=(
                "CREW_SYSTEMS_AND_"
                "MISSION_OPERATIONS"
            ),
            phase3b_event_ids=[
                fd1_fault[
                    "event_id"
                ],
                fd1_restored[
                    "event_id"
                ],
            ],
            phase2_anchor_ids=[],
            relationship_type=(
                "CREW_GROUND_"
                "TROUBLESHOOTING"
            ),
            relationship_status=(
                "NASA_REPORTED"
            ),
            public_basis=(
                "Crew and Mission Control "
                "troubleshot the Flight Day 1 "
                "toilet fault indication and "
                "restored normal toilet "
                "operations."
            ),
            missionlab_interpretation=(
                "The event demonstrates "
                "crew-ground operational "
                "recovery of a crew-system "
                "issue without exposing the "
                "internal fault tree or "
                "root cause."
            ),
            causal_relationship_established=(
                True
            ),
            mission_impact_claimed=(
                False
            ),
            evidence_class=(
                "NASA_REPORTED_WITH_"
                "MISSIONLAB_SYNTHESIS"
            ),
        ),
        make_correlation(
            correlation_id=(
                "WM_FD4_ATTITUDE_SUPPORT"
            ),
            source_thread_id=(
                FD4_THREAD_ID
            ),
            domain=(
                "GNC_ATTITUDE_OPERATIONS"
            ),
            phase3b_event_ids=[
                fd4_vent[
                    "event_id"
                ],
                fd4_heater[
                    "event_id"
                ],
                fd4_solar[
                    "event_id"
                ],
            ],
            phase2_anchor_ids=[
                "otc2_cancelled",
            ],
            relationship_type=(
                "SPACECRAFT_ATTITUDE_"
                "SUPPORT_TO_SYSTEM_"
                "TROUBLESHOOTING"
            ),
            relationship_status=(
                "NASA_REPORTED_AND_"
                "PHASE2_CORROBORATED"
            ),
            public_basis=(
                "NASA reported that Orion "
                "was oriented so the vent "
                "faced the Sun during "
                "vent-line troubleshooting. "
                "The Phase 2 maneuver product "
                "independently preserves an "
                "attitude adjustment for "
                "wastewater vent clearing as "
                "parallel activity on April 4."
            ),
            missionlab_interpretation=(
                "Waste-management "
                "troubleshooting crossed into "
                "spacecraft attitude operations. "
                "This establishes operational "
                "interaction, not a GNC anomaly."
            ),
            causal_relationship_established=(
                True
            ),
            mission_impact_claimed=(
                False
            ),
            evidence_class=(
                "NASA_REPORTED_WITH_"
                "CROSS_PHASE_CORRELATION"
            ),
        ),
        make_correlation(
            correlation_id=(
                "WM_FD4_TRAJECTORY_"
                "SCHEDULE_INTERACTION"
            ),
            source_thread_id=(
                FD4_THREAD_ID
            ),
            domain=(
                "FLIGHT_DYNAMICS_AND_"
                "TRAJECTORY_SCHEDULING"
            ),
            phase3b_event_ids=[
                fd4_vent[
                    "event_id"
                ],
                fd4_solar[
                    "event_id"
                ],
            ],
            phase2_anchor_ids=[
                "otc2_cancelled",
            ],
            relationship_type=(
                "PARALLEL_OPERATIONAL_"
                "SCHEDULING_CONTEXT"
            ),
            relationship_status=(
                "CORRELATED_WITHOUT_"
                "CAUSAL_CANCELLATION_CLAIM"
            ),
            public_basis=(
                "The April 4 Phase 2 maneuver "
                "record identifies OTC2 as "
                "cancelled because the "
                "trajectory remained on track "
                "and separately records the "
                "wastewater-clearing attitude "
                "adjustment as parallel "
                "operational activity."
            ),
            missionlab_interpretation=(
                "The waste-management response "
                "interacted with the mission "
                "operations schedule, but the "
                "public evidence does not "
                "support saying the wastewater "
                "issue caused OTC2 cancellation."
            ),
            causal_relationship_established=(
                False
            ),
            mission_impact_claimed=(
                False
            ),
            evidence_class=(
                "MISSIONLAB_DERIVED_"
                "CROSS_DOMAIN_CORRELATION"
            ),
        ),
        make_correlation(
            correlation_id=(
                "WM_FD4_CREW_CONTINGENCY"
            ),
            source_thread_id=(
                FD4_THREAD_ID
            ),
            domain=(
                "CREW_SYSTEMS_AND_"
                "CONTINGENCY_OPERATIONS"
            ),
            phase3b_event_ids=[
                fd4_backup[
                    "event_id"
                ]
            ],
            phase2_anchor_ids=[],
            relationship_type=(
                "CONTINGENCY_POSTURE"
            ),
            relationship_status=(
                "NASA_REPORTED"
            ),
            public_basis=(
                "Backup collection devices "
                "were available if needed "
                "while NASA reported that "
                "the toilet remained "
                "operational and the tank "
                "was not full."
            ),
            missionlab_interpretation=(
                "The crew had a contingency "
                "path without evidence of "
                "complete waste-management "
                "capability loss."
            ),
            causal_relationship_established=(
                True
            ),
            mission_impact_claimed=(
                False
            ),
            evidence_class=(
                "NASA_REPORTED_WITH_"
                "MISSIONLAB_SYNTHESIS"
            ),
        ),
        make_correlation(
            correlation_id=(
                "WM_FD4_MISSION_CONTINUATION"
            ),
            source_thread_id=(
                FD4_THREAD_ID
            ),
            domain=(
                "MISSION_OPERATIONS"
            ),
            phase3b_event_ids=[
                fd4_vent[
                    "event_id"
                ],
                fd4_heater[
                    "event_id"
                ],
                fd4_solar[
                    "event_id"
                ],
                fd4_backup[
                    "event_id"
                ],
            ],
            phase2_anchor_ids=[
                "otc3_executed",
                "pericynthion",
                "entry_interface",
                "splashdown",
            ],
            relationship_type=(
                "DOWNSTREAM_MISSION_"
                "CONTINUATION"
            ),
            relationship_status=(
                "TEMPORAL_AND_"
                "OPERATIONAL_CONTEXT"
            ),
            public_basis=(
                "Following the April 4 "
                "waste-management issue, "
                "the validated Phase 2 record "
                "contains later executed "
                "trajectory correction, lunar "
                "flyby, entry, and splashdown "
                "anchors."
            ),
            missionlab_interpretation=(
                "The public mission record "
                "supports mission continuation "
                "after the waste-management "
                "issue. It does not quantify "
                "risk contribution or prove "
                "that the issue had zero "
                "operational consequence."
            ),
            causal_relationship_established=(
                False
            ),
            mission_impact_claimed=(
                False
            ),
            evidence_class=(
                "MISSIONLAB_DERIVED_"
                "TEMPORAL_CORRELATION"
            ),
        ),
        make_correlation(
            correlation_id=(
                "WM_FD4_POSTFLIGHT_"
                "ENGINEERING_FOLLOWUP"
            ),
            source_thread_id=(
                FD4_THREAD_ID
            ),
            domain=(
                "POSTFLIGHT_ENGINEERING"
            ),
            phase3b_event_ids=[
                postflight[
                    "event_id"
                ]
            ],
            phase2_anchor_ids=[
                "splashdown",
            ],
            relationship_type=(
                "POSTFLIGHT_"
                "INVESTIGATION"
            ),
            relationship_status=(
                "NASA_REPORTED"
            ),
            public_basis=(
                "NASA's initial postflight "
                "assessment reported continued "
                "hardware assessment and data "
                "gathering for the urine "
                "vent-line issue."
            ),
            missionlab_interpretation=(
                "The issue remained an "
                "engineering investigation "
                "item after mission completion. "
                "No final root cause is assigned."
            ),
            causal_relationship_established=(
                True
            ),
            mission_impact_claimed=(
                False
            ),
            evidence_class=(
                "NASA_REPORTED_WITH_"
                "MISSIONLAB_SYNTHESIS"
            ),
        ),
    ]

    anchors = {
        "otc2_cancelled": {
            "date_utc": (
                otc2_cancelled.get(
                    "date_utc"
                )
            ),
            "status": (
                otc2_cancelled[
                    "status"
                ]
            ),
            "reason_classification": (
                otc2_cancelled[
                    "reason_classification"
                ]
            ),
            "parallel_operational_activity": (
                otc2_cancelled[
                    "parallel_operational_activity"
                ]
            ),
            "failed_burn": (
                otc2_cancelled[
                    "failed_burn"
                ]
            ),
            "propulsion_anomaly": (
                otc2_cancelled[
                    "propulsion_anomaly"
                ]
            ),
        },
        "otc3_executed": {
            "timestamp_utc": (
                otc3_executed[
                    "timestamp_utc"
                ]
            ),
            "status": (
                otc3_executed[
                    "status"
                ]
            ),
            "duration_seconds": (
                otc3_executed[
                    "duration_seconds"
                ]
            ),
        },
        "pericynthion": {
            "timestamp_utc": (
                pericynthion[
                    "timestamp_utc"
                ]
            ),
        },
        "entry_interface": {
            "timestamp_utc": (
                entry_interface[
                    "timestamp_utc"
                ]
            ),
        },
        "splashdown": {
            "timestamp_utc": (
                splashdown[
                    "timestamp_utc"
                ]
            ),
        },
    }

    return (
        correlations,
        anchors,
    )


def write_correlation_csv(
    rows: list[dict],
):
    fieldnames = [
        "correlation_id",
        "source_thread_id",
        "domain",
        "phase3b_event_ids",
        "phase2_anchor_ids",
        "relationship_type",
        "relationship_status",
        "public_basis",
        "missionlab_interpretation",
        "causal_relationship_established",
        "mission_impact_claimed",
        "evidence_class",
        "provenance",
    ]

    with CORRELATION_CSV.open(
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
                "phase3b_event_ids"
            ] = "|".join(
                row[
                    "phase3b_event_ids"
                ]
            )

            output[
                "phase2_anchor_ids"
            ] = "|".join(
                row[
                    "phase2_anchor_ids"
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


def build_figure(
    correlations: list[dict],
):
    rows = []

    for item in correlations:
        rows.append(
            [
                item[
                    "correlation_id"
                ].replace(
                    "WM_",
                    "",
                ).replace(
                    "_",
                    " ",
                ).title(),
                item[
                    "domain"
                ].replace(
                    "_",
                    " ",
                ).title(),
                item[
                    "relationship_type"
                ].replace(
                    "_",
                    " ",
                ).title(),
                (
                    "YES"
                    if item[
                        "causal_relationship_established"
                    ]
                    else "NO"
                ),
            ]
        )

    fig, ax = plt.subplots(
        figsize=(
            18,
            8,
        )
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        (
            "Artemis II Waste Management "
            "Cross-Domain Mission Correlations"
        ),
        fontsize=15,
        pad=18,
    )

    table = ax.table(
        cellText=rows,
        colLabels=[
            "Correlation",
            "Domain",
            "Relationship",
            "Causal Link Established?",
        ],
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        7.5
    )

    table.scale(
        1.0,
        1.9,
    )

    ax.text(
        0.5,
        0.035,
        (
            "Cross-domain correlation does not "
            "by itself establish mission impact, "
            "root cause, failure propagation, "
            "or causal linkage."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        FIGURE_PATH,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        FIGURE_PATH
    )


def validate_cross_domain_boundaries(
    correlations: list[dict],
):
    ids = {
        row[
            "correlation_id"
        ]
        for row
        in correlations
    }

    expected = {
        "WM_FD1_CREW_GROUND_RECOVERY",
        "WM_FD4_ATTITUDE_SUPPORT",
        "WM_FD4_TRAJECTORY_SCHEDULE_INTERACTION",
        "WM_FD4_CREW_CONTINGENCY",
        "WM_FD4_MISSION_CONTINUATION",
        "WM_FD4_POSTFLIGHT_ENGINEERING_FOLLOWUP",
    }

    if ids != expected:
        fail(
            "unexpected cross-domain "
            "correlation set"
        )

    trajectory = next(
        row
        for row
        in correlations
        if (
            row[
                "correlation_id"
            ]
            == (
                "WM_FD4_TRAJECTORY_"
                "SCHEDULE_INTERACTION"
            )
        )
    )

    if (
        trajectory[
            "causal_relationship_established"
        ]
        is not False
    ):
        fail(
            "waste issue incorrectly "
            "claimed as cause of OTC2 "
            "cancellation"
        )

    continuation = next(
        row
        for row
        in correlations
        if (
            row[
                "correlation_id"
            ]
            == (
                "WM_FD4_MISSION_CONTINUATION"
            )
        )
    )

    if (
        continuation[
            "mission_impact_claimed"
        ]
        is not False
    ):
        fail(
            "mission continuation "
            "incorrectly converted into "
            "quantified mission impact"
        )

    for row in correlations:
        if (
            row[
                "mission_impact_claimed"
            ]
            is not False
        ):
            fail(
                f"{row['correlation_id']} "
                "makes unsupported mission "
                "impact claim"
            )


def main():
    print()
    print(
        "Phase 3B.3 Artemis II "
        "Waste Management Mission-Impact "
        "and Cross-Domain Correlation"
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

    validate_dependencies(
        phase3b1,
        phase3b2,
        phase2_maneuvers,
        phase2_integrated,
    )

    print()
    print(
        "Dependencies:"
    )
    print(
        "  Phase 3B.1 evidence "
        "reference: PASS"
    )
    print(
        "  Phase 3B.2 operational "
        "threads: PASS"
    )
    print(
        "  Phase 2 maneuver "
        "operations: PASS"
    )
    print(
        "  Phase 2 integrated "
        "mission anchors: PASS"
    )

    events = index_events(
        phase3b1
    )

    get_thread(
        phase3b2[
            "threads"
        ],
        FD1_THREAD_ID,
    )

    get_thread(
        phase3b2[
            "threads"
        ],
        FD4_THREAD_ID,
    )

    (
        correlations,
        anchors,
    ) = build_correlations(
        events,
        phase2_maneuvers,
        phase2_integrated,
    )

    validate_cross_domain_boundaries(
        correlations
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_correlation_csv(
        correlations
    )

    build_figure(
        correlations
    )

    output = {
        "dataset_id": (
            "phase3b3_artemis_ii_"
            "waste_management_"
            "mission_impact"
        ),
        "mission": (
            "Artemis II"
        ),
        "phase": (
            "3B.3"
        ),
        "status": (
            "CROSS_DOMAIN_"
            "CORRELATION_COMPLETE"
        ),
        "dependencies": {
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
        },
        "phase2_anchors": (
            anchors
        ),
        "cross_domain_correlations": (
            correlations
        ),
        "mission_impact_assessment": {
            "flight_day_1": {
                "fault_indication_reported": (
                    True
                ),
                "crew_ground_troubleshooting_reported": (
                    True
                ),
                "normal_operations_restored": (
                    True
                ),
                "mission_ending_impact_established": (
                    False
                ),
                "root_cause_public": (
                    False
                ),
            },
            "flight_day_4": {
                "vent_activity_ended_early": (
                    True
                ),
                "spacecraft_attitude_response_reported": (
                    True
                ),
                "trajectory_schedule_interaction_present": (
                    True
                ),
                "waste_issue_caused_otc2_cancellation": (
                    False
                ),
                "otc2_cancelled_for_trajectory_reason": (
                    True
                ),
                "tank_full": (
                    False
                ),
                "toilet_operational": (
                    True
                ),
                "crew_contingency_available": (
                    True
                ),
                "later_mission_operations_recorded": (
                    True
                ),
                "mission_ending_impact_established": (
                    False
                ),
                "postflight_investigation_continued": (
                    True
                ),
                "root_cause_public": (
                    False
                ),
            },
        },
        "cross_domain_boundaries": {
            "attitude_response_equals_gnc_anomaly": (
                False
            ),
            "waste_issue_caused_otc2_cancellation": (
                False
            ),
            "otc2_cancellation_equals_failed_burn": (
                False
            ),
            "otc2_cancellation_equals_propulsion_anomaly": (
                False
            ),
            "mission_continuation_equals_zero_operational_impact": (
                False
            ),
            "mission_continuation_equals_zero_risk": (
                False
            ),
            "contingency_availability_equals_complete_system_failure": (
                False
            ),
            "postflight_investigation_equals_final_root_cause": (
                False
            ),
            "cross_domain_correlation_equals_causation": (
                False
            ),
            "precise_interval_from_fd4_issue_to_otc3_computable": (
                False
            ),
        },
        "evidence_boundary": {
            "public_operational_interactions_preserved": (
                True
            ),
            "phase2_cross_reference_preserved": (
                True
            ),
            "missionlab_correlations_are_derived": (
                True
            ),
            "unreported_internal_rationale_inferred": (
                False
            ),
            "unreported_failure_propagation_inferred": (
                False
            ),
            "quantitative_mission_risk_inferred": (
                False
            ),
            "final_root_cause_inferred": (
                False
            ),
            "exact_fd4_event_time_known": (
                False
            ),
        },
        "outputs": {
            "cross_domain_csv": str(
                CORRELATION_CSV.relative_to(
                    ROOT
                )
            ),
            "mission_impact_json": str(
                SUMMARY_JSON.relative_to(
                    ROOT
                )
            ),
            "cross_domain_figure": str(
                FIGURE_PATH.relative_to(
                    ROOT
                )
            ),
        },
    }

    with SUMMARY_JSON.open(
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

    print()
    print(
        "Cross-domain correlations:"
    )
    print(
        f"  total: {len(correlations)}"
    )

    print()
    print(
        "Flight Day 1:"
    )
    print(
        "  crew-ground recovery "
        "interaction: YES"
    )
    print(
        "  normal toilet operations "
        "restored: YES"
    )
    print(
        "  mission-ending impact "
        "established: NO"
    )
    print(
        "  root cause public: NO"
    )

    print()
    print(
        "Flight Day 4:"
    )
    print(
        "  spacecraft attitude "
        "interaction: YES"
    )
    print(
        "  trajectory schedule "
        "interaction: YES"
    )
    print(
        "  waste issue caused OTC2 "
        "cancellation: NO"
    )
    print(
        "  OTC2 cancellation reason: "
        "TRAJECTORY_REMAINED_ON_TRACK"
    )
    print(
        "  OTC2 failed burn: NO"
    )
    print(
        "  OTC2 propulsion anomaly: NO"
    )
    print(
        "  crew contingency "
        "available: YES"
    )
    print(
        "  tank full: NO"
    )
    print(
        "  toilet operational: YES"
    )
    print(
        "  later mission operations "
        "recorded: YES"
    )
    print(
        "  postflight investigation: YES"
    )
    print(
        "  root cause public: NO"
    )

    print()
    print(
        "Downstream mission anchors:"
    )
    print(
        "  OTC3: "
        + anchors[
            "otc3_executed"
        ][
            "timestamp_utc"
        ]
    )
    print(
        "  pericynthion: "
        + anchors[
            "pericynthion"
        ][
            "timestamp_utc"
        ]
    )
    print(
        "  entry interface: "
        + anchors[
            "entry_interface"
        ][
            "timestamp_utc"
        ]
    )
    print(
        "  splashdown: "
        + anchors[
            "splashdown"
        ][
            "timestamp_utc"
        ]
    )

    print()
    print(
        "Evidence boundary:"
    )
    print(
        "  attitude response "
        "!= GNC anomaly"
    )
    print(
        "  scheduling interaction "
        "!= OTC2 cancellation cause"
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
        "  cross-domain correlation "
        "!= causation"
    )
    print(
        "  postflight investigation "
        "!= final root cause"
    )
    print(
        "  exact FD4 event UTC "
        "remains unresolved"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            CORRELATION_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            SUMMARY_JSON.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            FIGURE_PATH.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 3B.3 CROSS-DOMAIN "
        "CORRELATION COMPLETE"
    )


if __name__ == "__main__":
    main()
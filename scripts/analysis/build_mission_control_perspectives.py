from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

MISSION_PATH = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

PHASE2_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_phase2_integrated_operations.json"
)

WASTE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_waste_management_evidence.json"
)

TPS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_tps_evidence.json"
)

ENTRY_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_descent_recovery_evidence.json"
)

PHASE5_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_nairas_interface.json"
)

PHASE6_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_lunar_observation_reconstruction.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "mission_control"
)

OUTPUT_JSON = (
    OUTPUT_DIR
    / "artemis_ii_mission_control_perspectives.json"
)

TIMELINE_CSV = (
    OUTPUT_DIR
    / "artemis_ii_discipline_prioritized_timeline.csv"
)

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_mission_control_perspectives.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "mission_control"
)

FIGURE_PATH = (
    ASSET_DIR
    / "phase7a_discipline_priority_matrix.svg"
)


DISCIPLINE_ORDER = [
    "FLIGHT",
    "FDO",
    "FAO",
    "EECOM",
    "COMM",
    "SCIENCE",
    "ENGINEERING_SUPPORT",
]

PRIORITY_LABELS = {
    0: "CONTEXT",
    1: "AWARENESS",
    2: "HIGH",
    3: "PRIMARY",
}


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
        "PHASE 7A ANALYSIS FAILED: "
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
        f"missing dependency: {path}",
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


def parse_utc(
    value: str,
) -> datetime:
    normalized = value.strip()

    if normalized.endswith(
        "Z"
    ):
        normalized = (
            normalized[
                :-1
            ]
            + "+00:00"
        )

    result = datetime.fromisoformat(
        normalized
    )

    if result.tzinfo is None:
        result = result.replace(
            tzinfo=timezone.utc
        )

    return result.astimezone(
        timezone.utc
    )


def met_string(
    timestamp: str | None,
    launch: datetime,
) -> str | None:
    if timestamp is None:
        return None

    value = parse_utc(
        timestamp
    )

    seconds = (
        value
        - launch
    ).total_seconds()

    sign = ""

    if seconds < 0:
        sign = "-"
        seconds = abs(
            seconds
        )

    total = int(
        round(
            seconds
        )
    )

    days, remainder = divmod(
        total,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes, seconds_value = divmod(
        remainder,
        60,
    )

    return (
        f"{sign}"
        f"{days:02d}:"
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds_value:02d}"
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


def public_role_sources() -> list[dict]:
    return [
        {
            "source_id": (
                "NASA_JSC_MISSION_CONTROL_CENTER"
            ),
            "publisher": "NASA",
            "title": (
                "JSC Mission Control Center"
            ),
            "url": (
                "https://www.nasa.gov/"
                "johnson/jsc-mission-control-center/"
            ),
            "supports": [
                "FLIGHT",
                "FDO",
                "FAO",
            ],
        },
        {
            "source_id": (
                "NASA_ARTEMIS_I_MCC_AT_A_GLANCE"
            ),
            "publisher": "NASA",
            "title": (
                "Artemis I Mission Control "
                "at a Glance"
            ),
            "url": (
                "https://www.nasa.gov/missions/"
                "artemis/orion/"
                "artemis-i-mission-control-at-a-glance/"
            ),
            "supports": [
                "EECOM",
                "FDO",
                "FAO",
                "COMMUNICATIONS_FUNCTIONS",
            ],
        },
        {
            "source_id": (
                "NASA_ARTEMIS_II_SCIENCE_OFFICERS"
            ),
            "publisher": "NASA Science",
            "title": (
                "Meet NASA's New Artemis II "
                "Science Officers"
            ),
            "url": (
                "https://science.nasa.gov/"
                "missions/artemis/"
                "meet-nasas-new-artemis-ii-"
                "science-officers/"
            ),
            "supports": [
                "SCIENCE",
                "ENGINEERING_AND_SCIENCE_SUPPORT_ROOMS",
            ],
        },
        {
            "source_id": (
                "NASA_ARTEMIS_II_MISSION_MASTERMINDS"
            ),
            "publisher": "NASA",
            "title": (
                "Meet NASA's Artemis II "
                "Moon Mission Masterminds"
            ),
            "url": (
                "https://www.nasa.gov/missions/"
                "artemis/artemis-2/"
                "meet-nasas-artemis-ii-"
                "moon-mission-masterminds/"
            ),
            "supports": [
                "FLIGHT",
                "FLIGHT_CONTROL_TEAM",
            ],
        },
    ]


def discipline_registry() -> list[dict]:
    return [
        {
            "discipline_id": "FLIGHT",
            "display_name": (
                "Flight Director Perspective"
            ),
            "role_type": (
                "OFFICIAL_MISSION_CONTROL_ROLE_"
                "USED_AS_MISSIONLAB_LENS"
            ),
            "public_role_basis": (
                "NASA describes the flight director "
                "as leading the flight-control team "
                "and maintaining overall responsibility "
                "for mission conduct."
            ),
            "missionlab_focus": [
                "overall mission state",
                "crew safety",
                "mission objectives",
                "cross-discipline integration",
                "risk and constraint visibility",
                "decision readiness",
            ],
            "primary_questions": [
                (
                    "What changed in the integrated "
                    "mission state?"
                ),
                (
                    "Does the condition threaten crew "
                    "safety or mission success?"
                ),
                (
                    "Which disciplines need to be "
                    "coordinated?"
                ),
                (
                    "Is a decision or contingency "
                    "posture required?"
                ),
            ],
            "source_ids": [
                "NASA_JSC_MISSION_CONTROL_CENTER",
                "NASA_ARTEMIS_II_MISSION_MASTERMINDS",
            ],
        },
        {
            "discipline_id": "FDO",
            "display_name": (
                "Flight Dynamics Officer Perspective"
            ),
            "role_type": (
                "OFFICIAL_MISSION_CONTROL_ROLE_"
                "USED_AS_MISSIONLAB_LENS"
            ),
            "public_role_basis": (
                "NASA describes FDO as monitoring "
                "Orion trajectory across mission phases."
            ),
            "missionlab_focus": [
                "trajectory",
                "maneuver timing",
                "orbit determination context",
                "lunar geometry",
                "entry targeting context",
                "dynamic flight phases",
            ],
            "primary_questions": [
                (
                    "Where is Orion relative to the "
                    "planned trajectory?"
                ),
                (
                    "Is a correction opportunity "
                    "still required?"
                ),
                (
                    "What geometric constraint is "
                    "driving the event?"
                ),
                (
                    "What is the trajectory handoff "
                    "into the next dynamic phase?"
                ),
            ],
            "source_ids": [
                "NASA_JSC_MISSION_CONTROL_CENTER",
                "NASA_ARTEMIS_I_MCC_AT_A_GLANCE",
            ],
        },
        {
            "discipline_id": "FAO",
            "display_name": (
                "Flight Activities Officer Perspective"
            ),
            "role_type": (
                "OFFICIAL_MISSION_CONTROL_ROLE_"
                "USED_AS_MISSIONLAB_LENS"
            ),
            "public_role_basis": (
                "NASA describes FAO as leading "
                "flight-plan timeline preparation "
                "and coordinating real-time changes."
            ),
            "missionlab_focus": [
                "mission timeline",
                "crew activities",
                "schedule changes",
                "science windows",
                "contingency activities",
                "handoffs between planned activities",
            ],
            "primary_questions": [
                (
                    "What activity was planned next?"
                ),
                (
                    "Did troubleshooting or geometry "
                    "change the timeline?"
                ),
                (
                    "What activities need to be "
                    "re-sequenced?"
                ),
                (
                    "Which objectives compete for "
                    "crew or mission time?"
                ),
            ],
            "source_ids": [
                "NASA_JSC_MISSION_CONTROL_CENTER",
                "NASA_ARTEMIS_I_MCC_AT_A_GLANCE",
            ],
        },
        {
            "discipline_id": "EECOM",
            "display_name": (
                "Emergency, Environmental, "
                "and Consumables Perspective"
            ),
            "role_type": (
                "ORION_FLIGHT_CONTROL_ROLE_"
                "USED_AS_MISSIONLAB_LENS"
            ),
            "public_role_basis": (
                "NASA's Orion mission-control "
                "documentation assigns EECOM "
                "environmental, life-support, "
                "consumables, thermal, and emergency "
                "monitoring responsibilities."
            ),
            "missionlab_focus": [
                "crew environment",
                "life support",
                "waste management",
                "consumables",
                "thermal state",
                "crew habitability",
                "contingency posture",
            ],
            "primary_questions": [
                (
                    "Is the crew environment safe "
                    "and supportable?"
                ),
                (
                    "Is the affected system still "
                    "providing required function?"
                ),
                (
                    "What contingency capability "
                    "remains available?"
                ),
                (
                    "Is the issue resolved in flight "
                    "or carried into postflight?"
                ),
            ],
            "source_ids": [
                "NASA_ARTEMIS_I_MCC_AT_A_GLANCE",
            ],
        },
        {
            "discipline_id": "COMM",
            "display_name": (
                "Communications Perspective"
            ),
            "role_type": (
                "MISSIONLAB_ANALYTICAL_LENS"
            ),
            "public_role_basis": (
                "MissionLab groups public voice, "
                "telemetry-link, network-handover, "
                "DSN, expected blackout, anomaly, "
                "and reacquisition evidence into a "
                "communications discipline view."
            ),
            "missionlab_focus": [
                "communications availability",
                "network transitions",
                "DSN context",
                "expected occultation loss",
                "entry plasma blackout",
                "unexpected return-link anomaly",
                "reacquisition",
            ],
            "primary_questions": [
                (
                    "Is loss of communications "
                    "expected from geometry or plasma?"
                ),
                (
                    "Is the observed loss anomalous?"
                ),
                (
                    "What link or network transition "
                    "is publicly established?"
                ),
                (
                    "When was contact publicly "
                    "reported restored?"
                ),
            ],
            "source_ids": [
                "NASA_ARTEMIS_I_MCC_AT_A_GLANCE",
            ],
        },
        {
            "discipline_id": "SCIENCE",
            "display_name": (
                "Science Officer Perspective"
            ),
            "role_type": (
                "OFFICIAL_ARTEMIS_II_CONSOLE_ROLE_"
                "USED_AS_MISSIONLAB_LENS"
            ),
            "public_role_basis": (
                "Artemis II introduced a dedicated "
                "SCIENCE console responsible for "
                "integrating lunar science and geology "
                "objectives with mission execution."
            ),
            "missionlab_focus": [
                "lunar targeting",
                "crew observations",
                "science imaging",
                "impact flashes",
                "terminator terrain",
                "eclipse observations",
                "LRO context",
            ],
            "primary_questions": [
                (
                    "What science opportunity exists "
                    "at this mission geometry?"
                ),
                (
                    "Was the opportunity actually "
                    "observed?"
                ),
                (
                    "What imagery, audio, annotation, "
                    "or target evidence exists?"
                ),
                (
                    "What postflight interpretation "
                    "is supported?"
                ),
            ],
            "source_ids": [
                "NASA_ARTEMIS_II_SCIENCE_OFFICERS",
            ],
        },
        {
            "discipline_id": (
                "ENGINEERING_SUPPORT"
            ),
            "display_name": (
                "Engineering Support Perspective"
            ),
            "role_type": (
                "MISSIONLAB_ANALYTICAL_LENS"
            ),
            "public_role_basis": (
                "NASA describes support-room experts "
                "providing real-time technical analysis "
                "and strategic guidance to front-room "
                "flight controllers. MissionLab uses "
                "ENGINEERING_SUPPORT as a cross-system "
                "technical evidence lens rather than "
                "an asserted single console call sign."
            ),
            "missionlab_focus": [
                "system troubleshooting",
                "root-cause evidence",
                "model limitations",
                "thermal protection",
                "hardware behavior",
                "postflight investigation",
                "engineering closure",
            ],
            "primary_questions": [
                (
                    "What evidence constrains the "
                    "technical explanation?"
                ),
                (
                    "What root cause is confirmed, "
                    "hypothesized, or unavailable?"
                ),
                (
                    "What model or test evidence "
                    "supports the response?"
                ),
                (
                    "What remains open for postflight "
                    "engineering?"
                ),
            ],
            "source_ids": [
                "NASA_ARTEMIS_II_SCIENCE_OFFICERS",
            ],
        },
    ]


def priorities(
    flight: int,
    fdo: int,
    fao: int,
    eecom: int,
    comm: int,
    science: int,
    engineering: int,
) -> dict[str, int]:
    values = {
        "FLIGHT": flight,
        "FDO": fdo,
        "FAO": fao,
        "EECOM": eecom,
        "COMM": comm,
        "SCIENCE": science,
        "ENGINEERING_SUPPORT": engineering,
    }

    for key, value in values.items():
        require(
            key
            in DISCIPLINE_ORDER,
            f"unknown discipline: {key}",
        )

        require(
            value
            in PRIORITY_LABELS,
            (
                f"invalid priority {value} "
                f"for {key}"
            ),
        )

    return values


def event_registry() -> list[dict]:
    return [
        {
            "order": 1,
            "event_id": "A2_LAUNCH",
            "name": "Launch",
            "timestamp_utc": (
                "2026-04-01T22:35:12Z"
            ),
            "date_utc": "2026-04-01",
            "time_precision": "SECOND_LEVEL",
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "DYNAMIC_FLIGHT_PHASE"
            ),
            "summary": (
                "Artemis II mission launch and "
                "start of the shared mission clock."
            ),
            "source_dependency": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "priorities": priorities(
                3, 3, 3, 2, 2, 0, 2
            ),
        },
        {
            "order": 2,
            "event_id": (
                "A2_UWMS_FD1_FAULT"
            ),
            "name": (
                "Flight Day 1 toilet fault indication"
            ),
            "timestamp_utc": None,
            "date_utc": "2026-04-01",
            "time_precision": (
                "RELATIVE_EVENT_ORDER_ONLY"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "IN_FLIGHT_SYSTEM_TROUBLESHOOTING"
            ),
            "summary": (
                "Crew reported a blinking toilet "
                "fault light. Mission Control and "
                "crew troubleshot the condition."
            ),
            "source_dependency": (
                "WASTE_MANAGEMENT_EVIDENCE"
            ),
            "priorities": priorities(
                3, 0, 2, 3, 1, 0, 3
            ),
        },
        {
            "order": 3,
            "event_id": (
                "A2_UWMS_FD1_RESTORED"
            ),
            "name": (
                "Toilet normal operations restored"
            ),
            "timestamp_utc": None,
            "date_utc": "2026-04-02",
            "time_precision": (
                "RELATIVE_EVENT_ORDER_ONLY"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "IN_FLIGHT_SYSTEM_RECOVERY"
            ),
            "summary": (
                "Crew and Mission Control restored "
                "the toilet to normal operations. "
                "Public root cause remained unavailable."
            ),
            "source_dependency": (
                "WASTE_MANAGEMENT_EVIDENCE"
            ),
            "priorities": priorities(
                3, 0, 2, 3, 0, 0, 3
            ),
        },
        {
            "order": 4,
            "event_id": (
                "A2_PROXIMITY_OPERATIONS"
            ),
            "name": (
                "Proximity operations and "
                "manual-control demonstration"
            ),
            "timestamp_utc": None,
            "date_utc": "2026-04-02",
            "time_precision": (
                "PUBLIC_SEQUENCE_NO_SINGLE_"
                "ANCHOR_USED"
            ),
            "evidence_class": (
                "NASA_REPORTED_WITH_"
                "MISSIONLAB_SYNTHESIS"
            ),
            "classification": (
                "CREW_MANUAL_FLIGHT_TEST"
            ),
            "summary": (
                "Crew-controlled approach and "
                "retreat were performed within the "
                "publicly reconstructed proximity "
                "operations sequence."
            ),
            "source_dependency": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "priorities": priorities(
                3, 3, 3, 1, 2, 0, 3
            ),
        },
        {
            "order": 5,
            "event_id": (
                "A2_UWMS_FD4_VENT_ISSUE"
            ),
            "name": (
                "Flight Day 4 wastewater "
                "vent-line issue"
            ),
            "timestamp_utc": None,
            "date_utc": "2026-04-04",
            "time_precision": (
                "RELATIVE_EVENT_ORDER_ONLY"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "MANAGED_SYSTEM_ANOMALY"
            ),
            "summary": (
                "Wastewater venting ended earlier "
                "than expected. Vent heaters, "
                "Sun-pointing, contingency collection "
                "posture, and continued engineering "
                "assessment followed."
            ),
            "source_dependency": (
                "WASTE_MANAGEMENT_EVIDENCE"
            ),
            "priorities": priorities(
                3, 1, 3, 3, 1, 0, 3
            ),
        },
        {
            "order": 6,
            "event_id": "A2_OTC3",
            "name": (
                "Outbound Trajectory Correction 3"
            ),
            "timestamp_utc": (
                "2026-04-06T03:03:00Z"
            ),
            "date_utc": "2026-04-06",
            "time_precision": "MINUTE_LEVEL",
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "TRAJECTORY_CORRECTION"
            ),
            "summary": (
                "OTC3 executed after two earlier "
                "outbound correction opportunities "
                "were cancelled."
            ),
            "source_dependency": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "priorities": priorities(
                3, 3, 3, 0, 2, 1, 2
            ),
        },
        {
            "order": 7,
            "event_id": (
                "A2_LUNAR_SOI_ENTRY"
            ),
            "name": (
                "Lunar sphere-of-influence entry"
            ),
            "timestamp_utc": (
                "2026-04-06T04:38:07.532302Z"
            ),
            "date_utc": "2026-04-06",
            "time_precision": (
                "MISSIONLAB_DERIVED"
            ),
            "evidence_class": (
                "MISSIONLAB_DERIVED_GEOMETRY"
            ),
            "classification": (
                "LUNAR_GEOMETRY_TRANSITION"
            ),
            "summary": (
                "MissionLab-derived lunar "
                "sphere-of-influence entry."
            ),
            "source_dependency": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "priorities": priorities(
                2, 3, 2, 0, 2, 3, 1
            ),
        },
        {
            "order": 8,
            "event_id": "A2_EARTHSET",
            "name": (
                "NASA-reported Earthset"
            ),
            "timestamp_utc": (
                "2026-04-06T22:41:00Z"
            ),
            "date_utc": "2026-04-06",
            "time_precision": (
                "NASA_REPORTED_MINUTE"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "LUNAR_SCIENCE_OBSERVATION"
            ),
            "summary": (
                "Earthset image captured as Earth "
                "crossed the apparent lunar limb."
            ),
            "source_dependency": (
                "PHASE6_LUNAR_OBSERVATIONS"
            ),
            "priorities": priorities(
                1, 3, 2, 0, 3, 3, 1
            ),
        },
        {
            "order": 9,
            "event_id": (
                "A2_PERICYNTHION"
            ),
            "name": "Pericynthion",
            "timestamp_utc": (
                "2026-04-06T23:00:46.177998Z"
            ),
            "date_utc": "2026-04-06",
            "time_precision": (
                "MISSIONLAB_DERIVED"
            ),
            "evidence_class": (
                "MISSIONLAB_DERIVED_GEOMETRY"
            ),
            "classification": (
                "LUNAR_CLOSEST_APPROACH"
            ),
            "summary": (
                "MissionLab refined closest lunar "
                "approach geometry."
            ),
            "source_dependency": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "priorities": priorities(
                3, 3, 2, 0, 3, 3, 2
            ),
        },
        {
            "order": 10,
            "event_id": "A2_EARTHRISE",
            "name": (
                "NASA-reported Earthrise"
            ),
            "timestamp_utc": (
                "2026-04-06T23:22:00Z"
            ),
            "date_utc": "2026-04-06",
            "time_precision": (
                "NASA_REPORTED_MINUTE"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "LUNAR_SCIENCE_OBSERVATION"
            ),
            "summary": (
                "NASA-reported Earthrise image "
                "as Earth re-emerged beyond "
                "the lunar limb."
            ),
            "source_dependency": (
                "PHASE6_LUNAR_OBSERVATIONS"
            ),
            "priorities": priorities(
                2, 3, 2, 0, 3, 3, 1
            ),
        },
        {
            "order": 11,
            "event_id": (
                "A2_TOTAL_SOLAR_ECLIPSE"
            ),
            "name": (
                "Derived total solar eclipse"
            ),
            "timestamp_utc": (
                "2026-04-07T00:34:27.220Z"
            ),
            "end_timestamp_utc": (
                "2026-04-07T01:28:53.125Z"
            ),
            "date_utc": "2026-04-07",
            "time_precision": (
                "MISSIONLAB_DERIVED_BOUNDARIES"
            ),
            "evidence_class": (
                "MISSIONLAB_DERIVED_GEOMETRY"
            ),
            "classification": (
                "SCIENCE_GEOMETRY_WINDOW"
            ),
            "summary": (
                "MissionLab-derived total solar "
                "eclipse interval of 54.43 minutes, "
                "consistent with NASA's nearly "
                "54-minute public description."
            ),
            "source_dependency": (
                "PHASE6_LUNAR_OBSERVATIONS"
            ),
            "priorities": priorities(
                2, 3, 3, 1, 2, 3, 2
            ),
        },
        {
            "order": 12,
            "event_id": (
                "A2_LUNAR_SOI_EXIT"
            ),
            "name": (
                "Lunar sphere-of-influence exit"
            ),
            "timestamp_utc": (
                "2026-04-07T17:23:41.922211Z"
            ),
            "date_utc": "2026-04-07",
            "time_precision": (
                "MISSIONLAB_DERIVED"
            ),
            "evidence_class": (
                "MISSIONLAB_DERIVED_GEOMETRY"
            ),
            "classification": (
                "LUNAR_GEOMETRY_TRANSITION"
            ),
            "summary": (
                "MissionLab-derived transition "
                "out of the lunar sphere of influence."
            ),
            "source_dependency": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "priorities": priorities(
                2, 3, 2, 0, 2, 2, 1
            ),
        },
        {
            "order": 13,
            "event_id": "A2_RTC1",
            "name": (
                "Return Trajectory Correction 1"
            ),
            "timestamp_utc": (
                "2026-04-08T00:03:00Z"
            ),
            "date_utc": "2026-04-08",
            "time_precision": "MINUTE_LEVEL",
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "TRAJECTORY_CORRECTION"
            ),
            "summary": (
                "First publicly reconstructed "
                "return trajectory correction."
            ),
            "source_dependency": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "priorities": priorities(
                3, 3, 3, 0, 2, 0, 2
            ),
        },
        {
            "order": 14,
            "event_id": (
                "A2_RETURN_LINK_LOSS"
            ),
            "name": (
                "Unexpected return-link loss"
            ),
            "timestamp_utc": (
                "2026-04-10T00:53:00Z"
            ),
            "date_utc": "2026-04-10",
            "time_precision": (
                "APPROXIMATE_PUBLIC_ANCHOR"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "COMMUNICATIONS_ANOMALY"
            ),
            "summary": (
                "Unexpected return-link "
                "communications interruption "
                "before RTC2 preparation."
            ),
            "source_dependency": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "priorities": priorities(
                3, 2, 3, 1, 3, 0, 3
            ),
        },
        {
            "order": 15,
            "event_id": "A2_RTC2",
            "name": (
                "Return Trajectory Correction 2"
            ),
            "timestamp_utc": (
                "2026-04-10T02:53:00Z"
            ),
            "date_utc": "2026-04-10",
            "time_precision": "MINUTE_LEVEL",
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "TRAJECTORY_CORRECTION_AFTER_"
                "COMMUNICATIONS_RECOVERY"
            ),
            "summary": (
                "RTC2 executed after public "
                "communications recovery and "
                "resumption of burn preparation."
            ),
            "source_dependency": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "priorities": priorities(
                3, 3, 3, 1, 3, 0, 3
            ),
        },
        {
            "order": 16,
            "event_id": "A2_RTC3",
            "name": (
                "Final Return Trajectory Correction"
            ),
            "timestamp_utc": (
                "2026-04-10T18:53:00Z"
            ),
            "date_utc": "2026-04-10",
            "time_precision": "MINUTE_LEVEL",
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "FINAL_PRE_ENTRY_CORRECTION"
            ),
            "summary": (
                "Final publicly reported return "
                "correction approximately five "
                "hours before Entry Interface."
            ),
            "source_dependency": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "priorities": priorities(
                3, 3, 3, 1, 2, 0, 3
            ),
        },
        {
            "order": 17,
            "event_id": (
                "A2_DSN_NSN_HANDOVER"
            ),
            "name": (
                "DSN to Near Space Network handover"
            ),
            "timestamp_utc": (
                "2026-04-10T23:15:00Z"
            ),
            "date_utc": "2026-04-10",
            "time_precision": (
                "PUBLIC_UPDATE_MINUTE"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "COMMUNICATIONS_NETWORK_HANDOVER"
            ),
            "summary": (
                "Publicly reported handover from "
                "Deep Space Network support toward "
                "Near Space Network/TDRS support."
            ),
            "source_dependency": (
                "PHASE4_ENTRY_RECOVERY_EVIDENCE"
            ),
            "priorities": priorities(
                3, 2, 3, 1, 3, 0, 2
            ),
        },
        {
            "order": 18,
            "event_id": (
                "A2_CM_SM_SEPARATION"
            ),
            "name": (
                "Crew Module / Service Module separation"
            ),
            "timestamp_utc": (
                "2026-04-10T23:33:00Z"
            ),
            "date_utc": "2026-04-10",
            "time_precision": (
                "PUBLIC_UPDATE_MINUTE"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "ENTRY_CONFIGURATION_TRANSITION"
            ),
            "summary": (
                "Orion crew module separated from "
                "the service module ahead of entry."
            ),
            "source_dependency": (
                "PHASE4_ENTRY_RECOVERY_EVIDENCE"
            ),
            "priorities": priorities(
                3, 3, 3, 2, 2, 0, 3
            ),
        },
        {
            "order": 19,
            "event_id": (
                "A2_ENTRY_INTERFACE"
            ),
            "name": "Entry Interface",
            "timestamp_utc": (
                "2026-04-10T23:53:00Z"
            ),
            "date_utc": "2026-04-10",
            "time_precision": (
                "PUBLIC_UPDATE_MINUTE"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "DYNAMIC_ENTRY_PHASE"
            ),
            "summary": (
                "Orion reached the public "
                "Entry Interface anchor."
            ),
            "source_dependency": (
                "PHASE4_ENTRY_RECOVERY_EVIDENCE"
            ),
            "priorities": priorities(
                3, 3, 3, 3, 3, 0, 3
            ),
        },
        {
            "order": 20,
            "event_id": (
                "A2_ENTRY_BLACKOUT"
            ),
            "name": (
                "Planned entry plasma blackout"
            ),
            "timestamp_utc": None,
            "date_utc": "2026-04-10",
            "time_precision": (
                "RELATIVE_TO_ENTRY_INTERFACE"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "EXPECTED_COMMUNICATIONS_CONSTRAINT"
            ),
            "summary": (
                "NASA reported a planned plasma "
                "communications blackout shortly "
                "after Entry Interface, expected "
                "to last about six minutes."
            ),
            "source_dependency": (
                "PHASE4_ENTRY_RECOVERY_EVIDENCE"
            ),
            "priorities": priorities(
                3, 3, 2, 2, 3, 0, 3
            ),
        },
        {
            "order": 21,
            "event_id": (
                "A2_ENTRY_REACQUISITION"
            ),
            "name": (
                "Entry communications reacquisition"
            ),
            "timestamp_utc": (
                "2026-04-11T00:00:00Z"
            ),
            "date_utc": "2026-04-11",
            "time_precision": (
                "PUBLIC_UPDATE_MINUTE"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "COMMUNICATIONS_REACQUISITION"
            ),
            "summary": (
                "NASA publicly reported "
                "communications contact restored "
                "during the entry sequence."
            ),
            "source_dependency": (
                "PHASE4_ENTRY_RECOVERY_EVIDENCE"
            ),
            "priorities": priorities(
                3, 3, 2, 2, 3, 0, 2
            ),
        },
        {
            "order": 22,
            "event_id": (
                "A2_DROGUE_DEPLOYMENT"
            ),
            "name": (
                "Drogue parachute deployment"
            ),
            "timestamp_utc": (
                "2026-04-11T00:03:00Z"
            ),
            "date_utc": "2026-04-11",
            "time_precision": (
                "PUBLIC_UPDATE_MINUTE"
            ),
            "evidence_class": (
                "NASA_REPORTED_AS_FLOWN_EVENT"
            ),
            "classification": (
                "ENTRY_DESCENT_EVENT"
            ),
            "summary": (
                "NASA reported drogue deployment "
                "during Orion descent."
            ),
            "source_dependency": (
                "PHASE4_ENTRY_RECOVERY_EVIDENCE"
            ),
            "priorities": priorities(
                3, 3, 2, 2, 2, 0, 3
            ),
        },
        {
            "order": 23,
            "event_id": (
                "A2_MAIN_DEPLOYMENT"
            ),
            "name": (
                "Main parachute deployment"
            ),
            "timestamp_utc": (
                "2026-04-11T00:04:00Z"
            ),
            "date_utc": "2026-04-11",
            "time_precision": (
                "PUBLIC_UPDATE_MINUTE"
            ),
            "evidence_class": (
                "NASA_REPORTED_AS_FLOWN_EVENT"
            ),
            "classification": (
                "ENTRY_DESCENT_EVENT"
            ),
            "summary": (
                "NASA reported deployment of "
                "all three main parachutes."
            ),
            "source_dependency": (
                "PHASE4_ENTRY_RECOVERY_EVIDENCE"
            ),
            "priorities": priorities(
                3, 3, 2, 2, 2, 0, 3
            ),
        },
        {
            "order": 24,
            "event_id": (
                "A2_SPLASHDOWN"
            ),
            "name": "Splashdown",
            "timestamp_utc": (
                "2026-04-11T00:07:00Z"
            ),
            "date_utc": "2026-04-11",
            "time_precision": (
                "PUBLIC_UPDATE_MINUTE"
            ),
            "evidence_class": "NASA_REPORTED",
            "classification": (
                "MISSION_RETURN_MILESTONE"
            ),
            "summary": (
                "Orion splashed down in the Pacific, "
                "transitioning operations from flight "
                "to crew and spacecraft recovery."
            ),
            "source_dependency": (
                "PHASE4_ENTRY_RECOVERY_EVIDENCE"
            ),
            "priorities": priorities(
                3, 2, 3, 3, 2, 0, 3
            ),
        },
    ]


def dependency_registry(
    phase2: dict,
    waste: dict,
    tps: dict,
    entry: dict,
    phase5: dict,
    phase6: dict,
) -> list[dict]:
    return [
        {
            "dependency_id": (
                "PHASE2_INTEGRATED_OPERATIONS"
            ),
            "path": (
                "data/reference/"
                "artemis_ii_phase2_integrated_operations.json"
            ),
            "dataset_id": phase2[
                "dataset_id"
            ],
            "role": (
                "flight dynamics, maneuvers, GNC, "
                "propulsion, communications, "
                "shared mission clock"
            ),
        },
        {
            "dependency_id": (
                "WASTE_MANAGEMENT_EVIDENCE"
            ),
            "path": (
                "data/reference/"
                "artemis_ii_waste_management_evidence.json"
            ),
            "dataset_id": waste[
                "dataset_id"
            ],
            "role": (
                "crew-environment troubleshooting "
                "and postflight investigation context"
            ),
        },
        {
            "dependency_id": (
                "TPS_EVIDENCE"
            ),
            "path": (
                "data/reference/"
                "artemis_tps_evidence.json"
            ),
            "dataset_id": tps[
                "dataset_id"
            ],
            "role": (
                "thermal-protection risk, mitigation, "
                "and postflight engineering evidence"
            ),
        },
        {
            "dependency_id": (
                "PHASE4_ENTRY_RECOVERY_EVIDENCE"
            ),
            "path": (
                "data/reference/"
                "artemis_ii_entry_descent_recovery_evidence.json"
            ),
            "dataset_id": entry[
                "dataset_id"
            ],
            "role": (
                "entry, blackout, descent, "
                "splashdown, and recovery evidence"
            ),
        },
        {
            "dependency_id": (
                "PHASE5_RADIATION_INTERFACE"
            ),
            "path": (
                "data/reference/"
                "artemis_ii_nairas_interface.json"
            ),
            "dataset_id": phase5[
                "dataset_id"
            ],
            "role": (
                "space-weather and radiation "
                "interpretation boundaries"
            ),
        },
        {
            "dependency_id": (
                "PHASE6_LUNAR_OBSERVATIONS"
            ),
            "path": (
                "data/reference/"
                "artemis_ii_lunar_observation_reconstruction.json"
            ),
            "dataset_id": phase6[
                "dataset_id"
            ],
            "role": (
                "lunar science, crew observations, "
                "image/audio/annotation correlation, "
                "and LRO context"
            ),
        },
    ]


def enrich_events(
    events: list[dict],
    launch: datetime,
) -> list[dict]:
    output = []

    for event in events:
        item = dict(
            event
        )

        item[
            "met"
        ] = met_string(
            event.get(
                "timestamp_utc"
            ),
            launch,
        )

        ranked = sorted(
            event[
                "priorities"
            ].items(),
            key=lambda pair: (
                -pair[
                    1
                ],
                DISCIPLINE_ORDER.index(
                    pair[
                        0
                    ]
                ),
            ),
        )

        item[
            "primary_lenses"
        ] = [
            discipline
            for discipline, value
            in ranked
            if value == 3
        ]

        item[
            "priority_labels"
        ] = {
            discipline: (
                PRIORITY_LABELS[
                    value
                ]
            )
            for discipline, value
            in event[
                "priorities"
            ].items()
        }

        output.append(
            item
        )

    return output


def lens_event_views(
    events: list[dict],
) -> dict:
    views = {}

    for discipline in DISCIPLINE_ORDER:
        ranked = sorted(
            events,
            key=lambda event: (
                -event[
                    "priorities"
                ][
                    discipline
                ],
                event[
                    "order"
                ],
            ),
        )

        views[
            discipline
        ] = [
            {
                "event_id": (
                    event[
                        "event_id"
                    ]
                ),
                "order": (
                    event[
                        "order"
                    ]
                ),
                "priority": (
                    event[
                        "priorities"
                    ][
                        discipline
                    ]
                ),
                "priority_label": (
                    PRIORITY_LABELS[
                        event[
                            "priorities"
                        ][
                            discipline
                        ]
                    ]
                ),
                "name": (
                    event[
                        "name"
                    ]
                ),
            }
            for event
            in ranked
            if event[
                "priorities"
            ][
                discipline
            ]
            >= 1
        ]

    return views


def write_timeline_csv(
    events: list[dict],
):
    fieldnames = [
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

    with TIMELINE_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for event in events:
            writer.writerow(
                {
                    "order": (
                        event[
                            "order"
                        ]
                    ),
                    "event_id": (
                        event[
                            "event_id"
                        ]
                    ),
                    "name": (
                        event[
                            "name"
                        ]
                    ),
                    "timestamp_utc": (
                        event.get(
                            "timestamp_utc"
                        )
                        or ""
                    ),
                    "date_utc": (
                        event[
                            "date_utc"
                        ]
                    ),
                    "met": (
                        event.get(
                            "met"
                        )
                        or ""
                    ),
                    "time_precision": (
                        event[
                            "time_precision"
                        ]
                    ),
                    "evidence_class": (
                        event[
                            "evidence_class"
                        ]
                    ),
                    "classification": (
                        event[
                            "classification"
                        ]
                    ),
                    "source_dependency": (
                        event[
                            "source_dependency"
                        ]
                    ),
                    "primary_lenses": (
                        "|".join(
                            event[
                                "primary_lenses"
                            ]
                        )
                    ),
                    "FLIGHT_priority": (
                        event[
                            "priorities"
                        ][
                            "FLIGHT"
                        ]
                    ),
                    "FDO_priority": (
                        event[
                            "priorities"
                        ][
                            "FDO"
                        ]
                    ),
                    "FAO_priority": (
                        event[
                            "priorities"
                        ][
                            "FAO"
                        ]
                    ),
                    "EECOM_priority": (
                        event[
                            "priorities"
                        ][
                            "EECOM"
                        ]
                    ),
                    "COMM_priority": (
                        event[
                            "priorities"
                        ][
                            "COMM"
                        ]
                    ),
                    "SCIENCE_priority": (
                        event[
                            "priorities"
                        ][
                            "SCIENCE"
                        ]
                    ),
                    "ENGINEERING_SUPPORT_priority": (
                        event[
                            "priorities"
                        ][
                            "ENGINEERING_SUPPORT"
                        ]
                    ),
                    "summary": (
                        event[
                            "summary"
                        ]
                    ),
                }
            )


def build_figure(
    events: list[dict],
):
    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    matrix = [
        [
            event[
                "priorities"
            ][
                discipline
            ]
            for discipline
            in DISCIPLINE_ORDER
        ]
        for event
        in events
    ]

    labels = [
        (
            str(
                event[
                    "order"
                ]
            )
            + " "
            + event[
                "name"
            ]
        )
        for event
        in events
    ]

    fig, ax = plt.subplots(
        figsize=(
            12,
            15,
        )
    )

    image = ax.imshow(
        matrix,
        aspect="auto",
        vmin=0,
        vmax=3,
    )

    ax.set_xticks(
        range(
            len(
                DISCIPLINE_ORDER
            )
        )
    )

    ax.set_xticklabels(
        DISCIPLINE_ORDER,
        rotation=35,
        ha="right",
    )

    ax.set_yticks(
        range(
            len(
                labels
            )
        )
    )

    ax.set_yticklabels(
        labels,
        fontsize=8,
    )

    ax.set_title(
        (
            "Artemis II MissionLab "
            "Discipline-Priority Matrix"
        )
    )

    colorbar = fig.colorbar(
        image,
        ax=ax,
        fraction=0.025,
        pad=0.02,
    )

    colorbar.set_ticks(
        [
            0,
            1,
            2,
            3,
        ]
    )

    colorbar.set_ticklabels(
        [
            "Context",
            "Awareness",
            "High",
            "Primary",
        ]
    )

    fig.text(
        0.5,
        0.01,
        (
            "Priorities are MissionLab analytical "
            "synthesis, not reconstructed NASA console "
            "assignments, staffing records, or private "
            "real-time flight-controller logs."
        ),
        ha="center",
        fontsize=8,
    )

    fig.tight_layout(
        rect=(
            0,
            0.03,
            1,
            0.98,
        )
    )

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


def main():
    print()
    print(
        "Phase 7A Artemis II Mission Control "
        "Discipline Perspectives"
    )
    print(
        "=" * 72
    )

    mission = load_json(
        MISSION_PATH
    )

    phase2 = load_json(
        PHASE2_PATH
    )

    waste = load_json(
        WASTE_PATH
    )

    tps = load_json(
        TPS_PATH
    )

    entry = load_json(
        ENTRY_PATH
    )

    phase5 = load_json(
        PHASE5_PATH
    )

    phase6 = load_json(
        PHASE6_PATH
    )

    require(
        mission.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        phase2.get(
            "dataset_id"
        )
        == (
            "phase2k_artemis_ii_"
            "phase2_integrated_operations"
        ),
        "Phase 2 dependency mismatch",
    )

    require(
        waste.get(
            "dataset_id"
        )
        == (
            "phase3b1_artemis_ii_"
            "waste_management_evidence"
        ),
        "waste-management dependency mismatch",
    )

    require(
        entry.get(
            "dataset_id"
        )
        == (
            "phase4a1_artemis_ii_"
            "entry_descent_recovery_evidence"
        ),
        "Phase 4 dependency mismatch",
    )

    require(
        phase5.get(
            "dataset_id"
        )
        == (
            "phase5b_artemis_ii_"
            "nairas_radiation_interface"
        ),
        "Phase 5 dependency mismatch",
    )

    require(
        phase6.get(
            "dataset_id"
        )
        == (
            "phase6b_artemis_ii_"
            "lunar_observation_reconstruction"
        ),
        "Phase 6 dependency mismatch",
    )

    launch = parse_utc(
        mission[
            "launch_epoch_utc"
        ]
    )

    roles = discipline_registry()
    sources = public_role_sources()

    events = enrich_events(
        event_registry(),
        launch,
    )

    dependencies = dependency_registry(
        phase2,
        waste,
        tps,
        entry,
        phase5,
        phase6,
    )

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

    require(
        [
            role[
                "discipline_id"
            ]
            for role
            in roles
        ]
        == DISCIPLINE_ORDER,
        "discipline registry ordering mismatch",
    )

    require(
        len(
            events
        )
        == 24,
        (
            "expected 24 shared-timeline events, "
            f"found {len(events)}"
        ),
    )

    orders = [
        event[
            "order"
        ]
        for event
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
        "timeline order is not contiguous",
    )

    event_ids = [
        event[
            "event_id"
        ]
        for event
        in events
    ]

    require(
        len(
            event_ids
        )
        == len(
            set(
                event_ids
            )
        ),
        "duplicate event IDs",
    )

    for event in events:
        require(
            set(
                event[
                    "priorities"
                ].keys()
            )
            == set(
                DISCIPLINE_ORDER
            ),
            (
                "incomplete discipline priority "
                f"registry for {event['event_id']}"
            ),
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REFERENCE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_timeline_csv(
        events
    )

    build_figure(
        events
    )

    result = {
        "dataset_id": (
            "phase7a_artemis_ii_"
            "mission_control_perspectives"
        ),
        "mission": "Artemis II",
        "phase": "7A",
        "status": (
            "DISCIPLINE_LENSES_AND_"
            "SHARED_TIMELINE_COMPLETE"
        ),
        "purpose": (
            "Create discipline-specific analytical "
            "views over the already validated shared "
            "Artemis II mission evidence spine."
        ),
        "role_source_registry": (
            sources
        ),
        "discipline_registry": (
            roles
        ),
        "priority_scale": {
            "0": "CONTEXT",
            "1": "AWARENESS",
            "2": "HIGH",
            "3": "PRIMARY",
        },
        "shared_timeline": (
            events
        ),
        "discipline_prioritized_views": (
            lens_event_views(
                events
            )
        ),
        "input_dependencies": (
            dependencies
        ),
        "integration_policy": {
            "shared_evidence_spine_required": True,
            "discipline_priorities_are_missionlab_synthesis": (
                True
            ),
            "discipline_priorities_are_nasa_console_logs": (
                False
            ),
            "discipline_priority_implies_controller_action": (
                False
            ),
            "official_role_definition_implies_exact_artemis_ii_staffing": (
                False
            ),
            "comm_lens_claimed_as_exact_console_call_sign": (
                False
            ),
            "engineering_support_claimed_as_single_console_call_sign": (
                False
            ),
            "derived_geometry_separated_from_reported_events": (
                True
            ),
            "date_only_events_not_given_fabricated_utc": (
                True
            ),
        },
        "critical_non_equivalences": [
            {
                "left": (
                    "MISSIONLAB_DISCIPLINE_PRIORITY"
                ),
                "right": (
                    "NASA_PRIVATE_CONSOLE_ACTION"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "MISSIONLAB_DISCIPLINE_LENS"
                ),
                "right": (
                    "EXACT_ARTEMIS_II_CONSOLE_STAFFING"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "PUBLIC_EVENT_SEQUENCE"
                ),
                "right": (
                    "COMPLETE_FLIGHT_LOOP_HISTORY"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "CROSS_DISCIPLINE_RELEVANCE"
                ),
                "right": (
                    "DECISION_AUTHORITY"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "EXPECTED_COMMUNICATIONS_CONSTRAINT"
                ),
                "right": (
                    "COMMUNICATIONS_ANOMALY"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "PUBLIC_TROUBLESHOOTING_ACTION"
                ),
                "right": (
                    "CONFIRMED_ROOT_CAUSE"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "MISSIONLAB_DERIVED_GEOMETRY"
                ),
                "right": (
                    "ONBOARD_TELEMETRY"
                ),
                "equivalent": False,
            },
        ],
        "roadmap_assessment": {
            "flight_lens": "COMPLETE",
            "fdo_lens": "COMPLETE",
            "fao_lens": "COMPLETE",
            "eecom_lens": "COMPLETE",
            "comm_lens": "COMPLETE",
            "science_lens": "COMPLETE",
            "engineering_support_lens": "COMPLETE",
            "shared_timeline_with_discipline_prioritization": (
                "COMPLETE"
            ),
            "decision_threads": (
                "PENDING_PHASE7B"
            ),
            "postflight_engineering_timeline": (
                "PENDING_PHASE7B"
            ),
        },
        "outputs": {
            "reference_json": (
                "data/reference/"
                "artemis_ii_mission_control_perspectives.json"
            ),
            "processed_json": (
                "data/processed/mission_control/"
                "artemis_ii_mission_control_perspectives.json"
            ),
            "timeline_csv": (
                "data/processed/mission_control/"
                "artemis_ii_discipline_prioritized_timeline.csv"
            ),
            "figure": (
                "docs/assets/mission_control/"
                "phase7a_discipline_priority_matrix.svg"
            ),
        },
    }

    with REFERENCE_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
        )

        f.write(
            "\n"
        )

    with OUTPUT_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
        )

        f.write(
            "\n"
        )

    print()
    print(
        "Dependencies:"
    )

    for item in dependencies:
        print(
            "  "
            + item[
                "dependency_id"
            ]
            + ": PASS"
        )

    print()
    print(
        "Discipline lenses:"
    )

    for role in roles:
        print(
            "  "
            + role[
                "discipline_id"
            ]
            + ": "
            + role[
                "role_type"
            ]
        )

    print()
    print(
        "Shared timeline:"
    )
    print(
        "  event records: "
        f"{len(events)}"
    )
    print(
        "  disciplines: "
        f"{len(roles)}"
    )
    print(
        "  priority levels: 4"
    )
    print(
        "  date-only events assigned "
        "fabricated UTC: NO"
    )

    print()
    print(
        "Selected high-value cross-discipline anchors:"
    )

    for event_id in [
        "A2_UWMS_FD4_VENT_ISSUE",
        "A2_OTC3",
        "A2_PERICYNTHION",
        "A2_TOTAL_SOLAR_ECLIPSE",
        "A2_RETURN_LINK_LOSS",
        "A2_RTC2",
        "A2_ENTRY_INTERFACE",
        "A2_SPLASHDOWN",
    ]:
        event = next(
            item
            for item
            in events
            if item[
                "event_id"
            ]
            == event_id
        )

        print(
            "  "
            + event_id
            + ": "
            + ", ".join(
                event[
                    "primary_lenses"
                ]
            )
        )

    print()
    print(
        "Mission-control interpretation boundary:"
    )
    print(
        "  MissionLab priority "
        "!= private NASA console action"
    )
    print(
        "  analytical lens "
        "!= exact Artemis II staffing record"
    )
    print(
        "  cross-discipline relevance "
        "!= decision authority"
    )
    print(
        "  public event sequence "
        "!= complete flight-loop history"
    )
    print(
        "  derived geometry "
        "!= onboard telemetry"
    )

    print()
    print(
        "Phase 7 roadmap state:"
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
        "  discipline-prioritized shared timeline: COMPLETE"
    )
    print(
        "  decision-thread synthesis: PENDING 7B"
    )
    print(
        "  postflight engineering timeline: PENDING 7B"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            REFERENCE_PATH.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            OUTPUT_JSON.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            TIMELINE_CSV.relative_to(
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
        "PHASE 7A MISSION CONTROL "
        "DISCIPLINE PERSPECTIVES COMPLETE"
    )


if __name__ == "__main__":
    main()
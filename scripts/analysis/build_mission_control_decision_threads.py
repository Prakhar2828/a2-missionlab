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

PHASE7A_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_mission_control_perspectives.json"
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
    / "artemis_ii_decision_threads.json"
)

THREAD_CSV = (
    OUTPUT_DIR
    / "artemis_ii_decision_threads.csv"
)

POSTFLIGHT_CSV = (
    OUTPUT_DIR
    / "artemis_ii_postflight_engineering_timeline.csv"
)

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_decision_threads.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "mission_control"
)

FIGURE_PATH = (
    ASSET_DIR
    / "phase7b_decision_thread_matrix.svg"
)


STAGE_ORDER = [
    "detection",
    "evidence",
    "constraint",
    "options",
    "decision",
    "action",
    "outcome",
]

DISCIPLINE_ORDER = [
    "FLIGHT",
    "FDO",
    "FAO",
    "EECOM",
    "COMM",
    "SCIENCE",
    "ENGINEERING_SUPPORT",
]


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
        "PHASE 7B ANALYSIS FAILED: "
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
            normalized[:-1]
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


def stage(
    status: str,
    summary: str,
    evidence_class: str,
    public_detail_complete: bool,
) -> dict:
    require(
        status
        in {
            "PUBLICLY_ESTABLISHED",
            "MISSIONLAB_SYNTHESIS",
            "NOT_PUBLICLY_ENUMERATED",
            "NOT_APPLICABLE",
        },
        f"invalid stage status: {status}",
    )

    return {
        "status": status,
        "summary": summary,
        "evidence_class": evidence_class,
        "public_detail_complete": (
            public_detail_complete
        ),
    }


def source_registry() -> list[dict]:
    return [
        {
            "source_id": (
                "NASA_INITIAL_POSTFLIGHT_"
                "ASSESSMENT_2026_04_20"
            ),
            "publisher": "NASA",
            "publication_date": (
                "2026-04-20"
            ),
            "title": (
                "NASA on Track for Future Missions "
                "with Initial Artemis II Assessments"
            ),
            "url": (
                "https://www.nasa.gov/missions/"
                "nasa-on-track-for-future-missions-"
                "with-initial-artemis-ii-assessments/"
            ),
            "role": (
                "Initial Orion, heat-shield, "
                "wastewater vent-line, SLS, and "
                "postflight engineering assessment."
            ),
        },
        {
            "source_id": (
                "NASA_AMES_ARTEMIS_II_"
                "POSTFLIGHT_ANALYSIS_2026_04_21"
            ),
            "publisher": "NASA",
            "publication_date": (
                "2026-04-21"
            ),
            "title": (
                "What Are Ames' Contributions "
                "to Artemis II?"
            ),
            "url": (
                "https://www.nasa.gov/centers-and-"
                "facilities/ames/"
                "what-are-ames-contributions-to-artemis-ii/"
            ),
            "role": (
                "Public evidence that postflight "
                "Mission and Fault Management "
                "performance analysis continued."
            ),
        },
        {
            "source_id": (
                "NASA_ORION_TESTING_"
                "UPDATED_2026_09_24"
            ),
            "publisher": "NASA",
            "publication_date": (
                "2026-09-24"
            ),
            "title": "Testing",
            "url": (
                "https://www.nasa.gov/reference/testing/"
            ),
            "role": (
                "Updated Orion engineering reference "
                "describing heat-shield investigation "
                "knowledge, Artemis II mitigation, and "
                "future heat-shield manufacturing lessons."
            ),
        },
        {
            "source_id": (
                "NASA_ARTEMIS_II_PRELIMINARY_"
                "LUNAR_SCIENCE_2026_10_07"
            ),
            "publisher": "NASA Science",
            "publication_date": (
                "2026-10-07"
            ),
            "title": (
                "Artemis II Preliminary "
                "Lunar Science Report"
            ),
            "url": (
                "https://science.nasa.gov/feature/"
                "artemis-ii-preliminary-lunar-science-report/"
            ),
            "role": (
                "Postflight lunar-science results "
                "including impact-flash and "
                "eclipse/corona interpretation."
            ),
        },
        {
            "source_id": (
                "NASA_NTRS_ARTEMIS_II_"
                "HEATSHIELD_SUCCESS_2026"
            ),
            "publisher": (
                "NASA Technical Reports Server"
            ),
            "publication_date": (
                "2026"
            ),
            "title": (
                "Under Pressure: The Artemis I "
                "Heatshield Char Loss Investigation "
                "and Artemis II's Successful Entry"
            ),
            "url": (
                "https://ntrs.nasa.gov/"
                "citations/20260006849"
            ),
            "role": (
                "Technical public linkage from "
                "Artemis I root cause through "
                "Artemis II trajectory mitigation "
                "to reduced postflight char loss."
            ),
        },
    ]


def decision_threads() -> list[dict]:
    return [
        {
            "thread_id": (
                "OUTBOUND_TRAJECTORY_ADAPTATION"
            ),
            "title": (
                "Outbound correction cancellation "
                "and OTC3 execution"
            ),
            "classification": (
                "NOMINAL_ADAPTIVE_MISSION_OPERATIONS"
            ),
            "anomaly": False,
            "primary_lenses": [
                "FLIGHT",
                "FDO",
                "FAO",
            ],
            "anchor_event_ids": [
                "A2_OTC3",
                "A2_LUNAR_SOI_ENTRY",
            ],
            "stages": {
                "detection": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Public mission reporting "
                        "established that Orion's "
                        "trajectory remained sufficiently "
                        "on track for earlier planned "
                        "outbound corrections to be cancelled."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "evidence": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Two planned outbound trajectory "
                        "corrections were cancelled while "
                        "OTC3 was later executed before "
                        "lunar sphere-of-influence entry."
                    ),
                    (
                        "NASA_REPORTED_PLUS_"
                        "MISSIONLAB_GEOMETRY"
                    ),
                    True,
                ),
                "constraint": stage(
                    "MISSIONLAB_SYNTHESIS",
                    (
                        "Trajectory correction activity "
                        "must balance the current flight "
                        "solution with downstream lunar "
                        "geometry and mission timeline."
                    ),
                    "MISSIONLAB_OPERATIONAL_SYNTHESIS",
                    False,
                ),
                "options": stage(
                    "NOT_PUBLICLY_ENUMERATED",
                    (
                        "The complete set of alternatives, "
                        "targeting thresholds, and console "
                        "trade discussions is not public."
                    ),
                    "PUBLIC_EVIDENCE_BOUNDARY",
                    False,
                ),
                "decision": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "OTC1 and OTC2 were cancelled "
                        "and OTC3 was retained and executed."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "action": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "OTC3 executed on "
                        "2026-04-06T03:03:00Z."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "outcome": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The mission continued into the "
                        "lunar encounter sequence. "
                        "MissionLab derived lunar SOI entry "
                        "at 2026-04-06T04:38:07.532302Z."
                    ),
                    (
                        "NASA_REPORTED_PLUS_"
                        "MISSIONLAB_DERIVED_GEOMETRY"
                    ),
                    True,
                ),
            },
            "guardrails": [
                (
                    "CANCELLED_CORRECTION"
                    " != FAILED_BURN"
                ),
                (
                    "CANCELLED_CORRECTION"
                    " != PROPULSION_ANOMALY"
                ),
                (
                    "PUBLIC_CORRECTION_SEQUENCE"
                    " != COMPLETE_TARGETING_LOGIC"
                ),
            ],
        },
        {
            "thread_id": (
                "FD1_UWMS_FAULT_RECOVERY"
            ),
            "title": (
                "Flight Day 1 toilet fault "
                "and in-flight recovery"
            ),
            "classification": (
                "IN_FLIGHT_SYSTEM_TROUBLESHOOTING"
            ),
            "anomaly": True,
            "primary_lenses": [
                "FLIGHT",
                "FAO",
                "EECOM",
                "ENGINEERING_SUPPORT",
            ],
            "anchor_event_ids": [
                "A2_UWMS_FD1_FAULT",
                "A2_UWMS_FD1_RESTORED",
            ],
            "stages": {
                "detection": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Crew reported a blinking "
                        "fault light during toilet-system "
                        "checkout."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "evidence": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Mission Control assessed "
                        "available data and coordinated "
                        "troubleshooting with the crew."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "constraint": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The public evidence established "
                        "a system fault indication but "
                        "did not identify the failed "
                        "component or root cause."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "options": stage(
                    "NOT_PUBLICLY_ENUMERATED",
                    (
                        "Private troubleshooting branches "
                        "and internal fault-isolation "
                        "options were not publicly released."
                    ),
                    "PUBLIC_EVIDENCE_BOUNDARY",
                    False,
                ),
                "decision": stage(
                    "MISSIONLAB_SYNTHESIS",
                    (
                        "The public sequence supports "
                        "continued troubleshooting rather "
                        "than abandonment of the system."
                    ),
                    "MISSIONLAB_OPERATIONAL_SYNTHESIS",
                    False,
                ),
                "action": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Crew and Mission Control "
                        "performed troubleshooting."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "outcome": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Normal toilet operations were "
                        "restored. The underlying root "
                        "cause remained unavailable in "
                        "the curated public source set."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
            },
            "guardrails": [
                (
                    "FAULT_LIGHT"
                    " != IDENTIFIED_FAILED_COMPONENT"
                ),
                (
                    "RESTORED_OPERATION"
                    " != KNOWN_ROOT_CAUSE"
                ),
                (
                    "TOILET_FAULT"
                    " != COMPLETE_UWMS_FAILURE"
                ),
            ],
        },
        {
            "thread_id": (
                "FD4_WASTEWATER_VENT_RESPONSE"
            ),
            "title": (
                "Flight Day 4 wastewater "
                "vent-line response"
            ),
            "classification": (
                "MANAGED_IN_FLIGHT_SYSTEM_ANOMALY"
            ),
            "anomaly": True,
            "primary_lenses": [
                "FLIGHT",
                "FAO",
                "EECOM",
                "ENGINEERING_SUPPORT",
            ],
            "anchor_event_ids": [
                "A2_UWMS_FD4_VENT_ISSUE",
            ],
            "stages": {
                "detection": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Wastewater venting ended "
                        "earlier than expected."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "evidence": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "NASA reported that the tank "
                        "was not full, the toilet remained "
                        "operational, possible ice was "
                        "considered, and other causes "
                        "were also under review."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "constraint": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Waste-management capacity and "
                        "continued crew operations had "
                        "to be protected while the physical "
                        "cause remained uncertain."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "options": stage(
                    "NOT_PUBLICLY_ENUMERATED",
                    (
                        "NASA publicly described several "
                        "responses but did not publish "
                        "the complete internal option set "
                        "or decision trade matrix."
                    ),
                    "PUBLIC_EVIDENCE_BOUNDARY",
                    False,
                ),
                "decision": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The mission adopted a managed "
                        "mitigation posture while "
                        "continuing to investigate."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "action": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Engineers used vent heaters, "
                        "oriented the vent toward the Sun, "
                        "reviewed other potential causes, "
                        "and maintained backup collection "
                        "capability if needed."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "outcome": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The toilet remained operational "
                        "and the mission continued. "
                        "NASA's April 20 postflight "
                        "assessment still described "
                        "the urine vent-line root-cause "
                        "investigation as ongoing."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
            },
            "guardrails": [
                (
                    "POSSIBLE_ICE"
                    " != CONFIRMED_ICE"
                ),
                (
                    "HEATER_USE"
                    " != PROOF_OF_ICE"
                ),
                (
                    "SUN_POINTING"
                    " != ROOT_CAUSE_CONFIRMATION"
                ),
                (
                    "BACKUP_COLLECTION"
                    " != TOILET_INOPERATIVE"
                ),
            ],
        },
        {
            "thread_id": (
                "LUNAR_COMMUNICATIONS_CONSTRAINT"
            ),
            "title": (
                "Expected lunar communications "
                "constraint and reacquisition"
            ),
            "classification": (
                "EXPECTED_OPERATIONAL_CONSTRAINT"
            ),
            "anomaly": False,
            "primary_lenses": [
                "FLIGHT",
                "FDO",
                "COMM",
                "SCIENCE",
            ],
            "anchor_event_ids": [
                "A2_EARTHSET",
                "A2_PERICYNTHION",
                "A2_EARTHRISE",
            ],
            "stages": {
                "detection": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Lunar geometry created an "
                        "expected period in which direct "
                        "Earth communications were blocked."
                    ),
                    (
                        "NASA_REPORTED_PLUS_"
                        "MISSIONLAB_GEOMETRY"
                    ),
                    True,
                ),
                "evidence": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Earthset, lunar occultation "
                        "geometry, Earthrise, and the "
                        "communications sequence are "
                        "mutually consistent."
                    ),
                    (
                        "NASA_REPORTED_PLUS_"
                        "MISSIONLAB_GEOMETRY"
                    ),
                    True,
                ),
                "constraint": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The lunar body physically "
                        "blocked the direct line of sight "
                        "between Orion and Earth."
                    ),
                    "GEOMETRIC_CONSTRAINT",
                    True,
                ),
                "options": stage(
                    "NOT_APPLICABLE",
                    (
                        "MissionLab treats the expected "
                        "occultation as a planned geometric "
                        "constraint rather than an anomaly "
                        "requiring fault-response options."
                    ),
                    "MISSIONLAB_CLASSIFICATION",
                    True,
                ),
                "decision": stage(
                    "MISSIONLAB_SYNTHESIS",
                    (
                        "Mission planning accepted the "
                        "expected loss-of-contact window "
                        "within the lunar-flyby sequence."
                    ),
                    "MISSIONLAB_OPERATIONAL_SYNTHESIS",
                    False,
                ),
                "action": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The mission proceeded through "
                        "the lunar-flyby observation "
                        "sequence and later reacquired "
                        "Earth communications."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "outcome": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The expected communications "
                        "constraint ended as Earth "
                        "re-emerged from behind the Moon."
                    ),
                    (
                        "NASA_REPORTED_PLUS_"
                        "MISSIONLAB_GEOMETRY"
                    ),
                    True,
                ),
            },
            "guardrails": [
                (
                    "EXPECTED_LUNAR_BLACKOUT"
                    " != COMMUNICATIONS_ANOMALY"
                ),
                (
                    "EARTHRISE_IMAGE_TIME"
                    " != EXACT_LINK_REACQUISITION_TIME"
                ),
            ],
        },
        {
            "thread_id": (
                "LUNAR_SCIENCE_EXECUTION"
            ),
            "title": (
                "Lunar science opportunity "
                "to confirmed observation"
            ),
            "classification": (
                "MISSION_SCIENCE_EXECUTION"
            ),
            "anomaly": False,
            "primary_lenses": [
                "FLIGHT",
                "FDO",
                "FAO",
                "SCIENCE",
            ],
            "anchor_event_ids": [
                "A2_EARTHSET",
                "A2_PERICYNTHION",
                "A2_EARTHRISE",
                "A2_TOTAL_SOLAR_ECLIPSE",
            ],
            "stages": {
                "detection": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Preflight targeting identified "
                        "science opportunities tied to "
                        "lunar-flyby geometry."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "evidence": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Postflight imagery, audio, "
                        "crew annotations, and LRO context "
                        "confirm observations of Earthset, "
                        "Earthrise, terminator terrain, "
                        "eclipse phenomena, and impact flashes."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "constraint": stage(
                    "MISSIONLAB_SYNTHESIS",
                    (
                        "Observation opportunities were "
                        "bounded by flight geometry, "
                        "illumination, crew timeline, "
                        "and available viewing conditions."
                    ),
                    "MISSIONLAB_OPERATIONAL_SYNTHESIS",
                    False,
                ),
                "options": stage(
                    "NOT_PUBLICLY_ENUMERATED",
                    (
                        "The complete real-time science "
                        "prioritization trade space is "
                        "not reconstructed from public data."
                    ),
                    "PUBLIC_EVIDENCE_BOUNDARY",
                    False,
                ),
                "decision": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The mission executed the public "
                        "lunar observation program."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "action": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Crew captured imagery, provided "
                        "spoken observations, and produced "
                        "annotations during the lunar sequence."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "outcome": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Postflight science products "
                        "document confirmed lunar observations, "
                        "five impact flashes, coronal structure, "
                        "zodiacal light, and selected terrain "
                        "interpretations."
                    ),
                    "NASA_POSTFLIGHT_REPORTED",
                    True,
                ),
            },
            "guardrails": [
                (
                    "TARGETING_OPPORTUNITY"
                    " != CONFIRMED_OBSERVATION"
                ),
                (
                    "IMAGE_TIME"
                    " != CREW_REMARK_TIME"
                ),
                (
                    "LRO_CONTEXT"
                    " != ARTEMIS_II_IMAGE"
                ),
            ],
        },
        {
            "thread_id": (
                "RETURN_LINK_ANOMALY_RTC2"
            ),
            "title": (
                "Unexpected return-link loss, "
                "recovery, and RTC2 continuation"
            ),
            "classification": (
                "COMMUNICATIONS_ANOMALY_WITH_"
                "MISSION_CONTINUATION"
            ),
            "anomaly": True,
            "primary_lenses": [
                "FLIGHT",
                "FDO",
                "FAO",
                "COMM",
                "ENGINEERING_SUPPORT",
            ],
            "anchor_event_ids": [
                "A2_RETURN_LINK_LOSS",
                "A2_RTC2",
            ],
            "stages": {
                "detection": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "NASA reported an unexpected "
                        "return-link communications loss "
                        "before RTC2."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "evidence": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Public reporting establishes "
                        "the communications interruption, "
                        "recovery, resumed burn preparation, "
                        "and subsequent RTC2 execution."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "constraint": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The communications condition "
                        "had to be resolved sufficiently "
                        "for nominal mission operations "
                        "and burn preparation to continue."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "options": stage(
                    "NOT_PUBLICLY_ENUMERATED",
                    (
                        "The complete fault-recovery "
                        "option set and internal console "
                        "discussion are not public."
                    ),
                    "PUBLIC_EVIDENCE_BOUNDARY",
                    False,
                ),
                "decision": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Following communications recovery, "
                        "burn preparation resumed."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "action": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "RTC2 executed at "
                        "2026-04-10T02:53:00Z."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "outcome": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "RTC2 was completed successfully "
                        "and the return mission continued."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
            },
            "guardrails": [
                (
                    "TEMPORAL_SEQUENCE"
                    " != CAUSATION"
                ),
                (
                    "RETURN_LINK_LOSS"
                    " != PROVEN_COMPLETE_TWO_WAY_OUTAGE"
                ),
                (
                    "COMMUNICATIONS_ANOMALY"
                    " != PROPULSION_ANOMALY"
                ),
                (
                    "RTC2_SUCCESS"
                    " != PUBLIC_ROOT_CAUSE"
                ),
            ],
        },
        {
            "thread_id": (
                "TPS_RISK_MITIGATION_CLOSURE"
            ),
            "title": (
                "Artemis I heat-shield finding "
                "to Artemis II mitigation and "
                "postflight outcome"
            ),
            "classification": (
                "ENGINEERING_RISK_MITIGATION_THREAD"
            ),
            "anomaly": False,
            "primary_lenses": [
                "FLIGHT",
                "FDO",
                "ENGINEERING_SUPPORT",
            ],
            "anchor_event_ids": [
                "A2_ENTRY_INTERFACE",
                "A2_SPLASHDOWN",
            ],
            "stages": {
                "detection": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Artemis I postflight inspection "
                        "identified unexpected Avcoat "
                        "char liberation."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "evidence": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "NASA's investigation linked "
                        "low-permeability Avcoat, internal "
                        "gas-pressure buildup, cracking, "
                        "and the Artemis I skip-entry "
                        "thermal history."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "constraint": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The Artemis II heat shield was "
                        "already integrated, requiring "
                        "a flight-rationale and mitigation "
                        "approach compatible with the "
                        "existing spacecraft."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "options": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "NASA publicly described the "
                        "engineering principle that the "
                        "material or the entry environment "
                        "could be changed to control the "
                        "known mechanism."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "decision": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "For Artemis II, NASA changed "
                        "the entry environment by flying "
                        "a modified trajectory without "
                        "the Artemis I-style skip entry."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "action": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Artemis II executed the modified "
                        "entry profile and completed "
                        "atmospheric entry."
                    ),
                    (
                        "NASA_REPORTED_PLUS_"
                        "MISSIONLAB_ENTRY_CONTEXT"
                    ),
                    True,
                ),
                "outcome": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Initial postflight assessment "
                        "reported expected TPS performance "
                        "and significantly reduced char loss. "
                        "NASA technical reporting later "
                        "described the Artemis II entry "
                        "as successful."
                    ),
                    "NASA_POSTFLIGHT_REPORTED",
                    True,
                ),
            },
            "guardrails": [
                (
                    "REDUCED_CHAR_LOSS"
                    " != ZERO_CHAR_LOSS"
                ),
                (
                    "INITIAL_POSTFLIGHT_ASSESSMENT"
                    " != COMPLETE_MATERIAL_DATASET"
                ),
                (
                    "MISSIONLAB_HEATING_MODEL"
                    " != TPS_SENSOR_TELEMETRY"
                ),
            ],
        },
        {
            "thread_id": (
                "FINAL_CORRECTION_ENTRY_HANDOFF"
            ),
            "title": (
                "Final return correction "
                "to Entry Interface"
            ),
            "classification": (
                "NOMINAL_DYNAMIC_PHASE_HANDOFF"
            ),
            "anomaly": False,
            "primary_lenses": [
                "FLIGHT",
                "FDO",
                "FAO",
                "ENGINEERING_SUPPORT",
            ],
            "anchor_event_ids": [
                "A2_RTC3",
                "A2_ENTRY_INTERFACE",
            ],
            "stages": {
                "detection": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The return trajectory entered "
                        "its final publicly reported "
                        "correction opportunity before entry."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "evidence": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "RTC3 occurred at 18:53 UTC "
                        "and Entry Interface at 23:53 UTC."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "constraint": stage(
                    "MISSIONLAB_SYNTHESIS",
                    (
                        "The final return state had to "
                        "support the required transition "
                        "into the entry sequence."
                    ),
                    "MISSIONLAB_OPERATIONAL_SYNTHESIS",
                    False,
                ),
                "options": stage(
                    "NOT_PUBLICLY_ENUMERATED",
                    (
                        "Public evidence does not expose "
                        "the complete targeting trade space, "
                        "covariance, or final guidance "
                        "decision thresholds."
                    ),
                    "PUBLIC_EVIDENCE_BOUNDARY",
                    False,
                ),
                "decision": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "RTC3 was executed as the final "
                        "publicly reported trajectory "
                        "correction before entry."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "action": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The spacecraft proceeded through "
                        "entry preparation and reached "
                        "Entry Interface five hours later."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "outcome": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The mission transitioned from "
                        "return trajectory management "
                        "into atmospheric entry."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
            },
            "guardrails": [
                (
                    "FINAL_PUBLIC_CORRECTION"
                    " != FINAL_ONBOARD_NAVIGATION_STATE"
                ),
                (
                    "PUBLIC_HANDOFF"
                    " != ENTRY_GUIDANCE_LAW"
                ),
            ],
        },
        {
            "thread_id": (
                "ENTRY_BLACKOUT_REACQUISITION"
            ),
            "title": (
                "Planned entry plasma blackout "
                "and communications reacquisition"
            ),
            "classification": (
                "EXPECTED_ENTRY_COMMUNICATIONS_CONSTRAINT"
            ),
            "anomaly": False,
            "primary_lenses": [
                "FLIGHT",
                "FDO",
                "EECOM",
                "COMM",
                "ENGINEERING_SUPPORT",
            ],
            "anchor_event_ids": [
                "A2_ENTRY_INTERFACE",
                "A2_ENTRY_BLACKOUT",
                "A2_ENTRY_REACQUISITION",
            ],
            "stages": {
                "detection": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "NASA expected communications "
                        "loss shortly after Entry Interface "
                        "as plasma developed around Orion."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "evidence": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The public sequence reports "
                        "Entry Interface, planned blackout, "
                        "and communications reacquisition."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "constraint": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The ionized plasma environment "
                        "temporarily obstructed normal "
                        "communications during atmospheric entry."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "options": stage(
                    "NOT_APPLICABLE",
                    (
                        "The blackout is treated as an "
                        "expected entry constraint rather "
                        "than an unexpected fault requiring "
                        "a reconstructed response tree."
                    ),
                    "MISSIONLAB_CLASSIFICATION",
                    True,
                ),
                "decision": stage(
                    "MISSIONLAB_SYNTHESIS",
                    (
                        "The entry sequence proceeded "
                        "through the expected blackout window."
                    ),
                    "MISSIONLAB_OPERATIONAL_SYNTHESIS",
                    False,
                ),
                "action": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "NASA later reported communications "
                        "reestablished at the public "
                        "00:00 UTC minute."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "outcome": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Contact was restored before "
                        "the publicly reported parachute "
                        "deployment sequence."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
            },
            "guardrails": [
                (
                    "PLANNED_ENTRY_BLACKOUT"
                    " != COMMUNICATIONS_ANOMALY"
                ),
                (
                    "PUBLIC_REACQUISITION_MINUTE"
                    " != EXACT_BLACKOUT_END_SECOND"
                ),
            ],
        },
        {
            "thread_id": (
                "DESCENT_SPLASHDOWN_RECOVERY"
            ),
            "title": (
                "Parachute descent, splashdown, "
                "and recovery transition"
            ),
            "classification": (
                "NOMINAL_RETURN_AND_RECOVERY_SEQUENCE"
            ),
            "anomaly": False,
            "primary_lenses": [
                "FLIGHT",
                "FDO",
                "FAO",
                "EECOM",
                "ENGINEERING_SUPPORT",
            ],
            "anchor_event_ids": [
                "A2_DROGUE_DEPLOYMENT",
                "A2_MAIN_DEPLOYMENT",
                "A2_SPLASHDOWN",
            ],
            "stages": {
                "detection": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Following entry and communications "
                        "reacquisition, Orion entered the "
                        "publicly reported parachute "
                        "descent sequence."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "evidence": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "NASA reported drogue deployment, "
                        "all three main parachutes, "
                        "splashdown, crew extraction, "
                        "and spacecraft recovery."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "constraint": stage(
                    "MISSIONLAB_SYNTHESIS",
                    (
                        "The sequence had to transition "
                        "safely from atmospheric flight "
                        "to water landing and maritime recovery."
                    ),
                    "MISSIONLAB_OPERATIONAL_SYNTHESIS",
                    False,
                ),
                "options": stage(
                    "NOT_PUBLICLY_ENUMERATED",
                    (
                        "MissionLab does not reconstruct "
                        "private recovery-team contingency "
                        "decision trees or unreported "
                        "parachute-response logic."
                    ),
                    "PUBLIC_EVIDENCE_BOUNDARY",
                    False,
                ),
                "decision": stage(
                    "MISSIONLAB_SYNTHESIS",
                    (
                        "The public record shows the "
                        "nominal descent and recovery "
                        "sequence proceeding to completion."
                    ),
                    "MISSIONLAB_OPERATIONAL_SYNTHESIS",
                    False,
                ),
                "action": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "Drogues deployed, mains deployed, "
                        "Orion splashed down, recovery "
                        "forces approached, crew were "
                        "extracted, and Orion was recovered."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
                "outcome": stage(
                    "PUBLICLY_ESTABLISHED",
                    (
                        "The crew and spacecraft were "
                        "recovered, closing the flight "
                        "phase and opening detailed "
                        "postflight engineering analysis."
                    ),
                    "NASA_REPORTED",
                    True,
                ),
            },
            "guardrails": [
                (
                    "PARACHUTE_ARCHITECTURE"
                    " != INDIVIDUAL_PARACHUTE_TELEMETRY"
                ),
                (
                    "PUBLIC_RECOVERY_SEQUENCE"
                    " != PRIVATE_RECOVERY_DECISION_LOG"
                ),
            ],
        },
    ]


def postflight_timeline() -> list[dict]:
    return [
        {
            "order": 1,
            "record_id": (
                "POSTFLIGHT_RECOVERY_TRANSITION"
            ),
            "date": "2026-04-11",
            "date_precision": (
                "MISSION_RETURN_DATE"
            ),
            "category": (
                "SPACECRAFT_RECOVERY"
            ),
            "status": "COMPLETE",
            "summary": (
                "Orion recovery transitioned the "
                "mission from flight operations "
                "into spacecraft inspection and "
                "postflight engineering analysis."
            ),
            "source_ids": [],
            "open_issue": False,
        },
        {
            "order": 2,
            "record_id": (
                "POSTFLIGHT_INITIAL_ORION_ASSESSMENT"
            ),
            "date": "2026-04-20",
            "date_precision": (
                "PUBLICATION_DATE"
            ),
            "category": (
                "ORION_POSTFLIGHT_ASSESSMENT"
            ),
            "status": (
                "INITIAL_ASSESSMENT"
            ),
            "summary": (
                "NASA reported that initial Orion "
                "thermal-protection assessments "
                "found expected performance and "
                "significantly reduced Artemis I-type "
                "char-loss behavior."
            ),
            "source_ids": [
                (
                    "NASA_INITIAL_POSTFLIGHT_"
                    "ASSESSMENT_2026_04_20"
                ),
            ],
            "open_issue": False,
        },
        {
            "order": 3,
            "record_id": (
                "POSTFLIGHT_URINE_VENT_INVESTIGATION"
            ),
            "date": "2026-04-20",
            "date_precision": (
                "PUBLICATION_DATE"
            ),
            "category": (
                "WASTE_MANAGEMENT_INVESTIGATION"
            ),
            "status": (
                "OPEN_IN_CURATED_PUBLIC_EVIDENCE"
            ),
            "summary": (
                "NASA reported hardware assessment "
                "and data gathering were continuing "
                "to identify the urine vent-line "
                "root cause and support corrective "
                "action for a future mission."
            ),
            "source_ids": [
                (
                    "NASA_INITIAL_POSTFLIGHT_"
                    "ASSESSMENT_2026_04_20"
                ),
            ],
            "open_issue": True,
        },
        {
            "order": 4,
            "record_id": (
                "POSTFLIGHT_MISSION_FAULT_"
                "MANAGEMENT_ANALYSIS"
            ),
            "date": "2026-04-21",
            "date_precision": (
                "PUBLICATION_DATE"
            ),
            "category": (
                "MISSION_AND_FAULT_MANAGEMENT"
            ),
            "status": (
                "POSTFLIGHT_ANALYSIS_ONGOING"
            ),
            "summary": (
                "NASA Ames reported continued "
                "postflight analysis of Mission "
                "and Fault Management logic "
                "performance during Artemis II."
            ),
            "source_ids": [
                (
                    "NASA_AMES_ARTEMIS_II_"
                    "POSTFLIGHT_ANALYSIS_2026_04_21"
                ),
            ],
            "open_issue": True,
        },
        {
            "order": 5,
            "record_id": (
                "POSTFLIGHT_TPS_ENGINEERING_"
                "KNOWLEDGE_UPDATE"
            ),
            "date": "2026-09-24",
            "date_precision": (
                "NASA_PAGE_UPDATE_DATE"
            ),
            "category": (
                "THERMAL_PROTECTION_ENGINEERING"
            ),
            "status": (
                "ENGINEERING_KNOWLEDGE_INTEGRATED"
            ),
            "summary": (
                "NASA's updated Orion testing "
                "reference linked heat-shield "
                "permeability knowledge and Artemis II "
                "mitigation experience to future "
                "heat-shield manufacturing improvements."
            ),
            "source_ids": [
                (
                    "NASA_ORION_TESTING_"
                    "UPDATED_2026_09_24"
                ),
                (
                    "NASA_NTRS_ARTEMIS_II_"
                    "HEATSHIELD_SUCCESS_2026"
                ),
            ],
            "open_issue": False,
        },
        {
            "order": 6,
            "record_id": (
                "POSTFLIGHT_LUNAR_SCIENCE_RELEASE"
            ),
            "date": "2026-10-07",
            "date_precision": (
                "PUBLICATION_DATE"
            ),
            "category": (
                "LUNAR_SCIENCE_POSTFLIGHT"
            ),
            "status": (
                "PRELIMINARY_SCIENCE_RESULTS_RELEASED"
            ),
            "summary": (
                "NASA released the preliminary "
                "Artemis II lunar-science results "
                "and archive, resolving selected "
                "early observations including the "
                "five-flash postflight result and "
                "coronal / zodiacal-light interpretation."
            ),
            "source_ids": [
                (
                    "NASA_ARTEMIS_II_PRELIMINARY_"
                    "LUNAR_SCIENCE_2026_10_07"
                ),
            ],
            "open_issue": False,
        },
    ]


def validate_thread_structure(
    threads: list[dict],
):
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

    for item in threads:
        require(
            list(
                item[
                    "stages"
                ].keys()
            )
            == STAGE_ORDER,
            (
                "decision stage order mismatch for "
                f"{item['thread_id']}"
            ),
        )

        require(
            len(
                item[
                    "primary_lenses"
                ]
            )
            > 0,
            (
                "decision thread missing lenses: "
                f"{item['thread_id']}"
            ),
        )

        for lens in item[
            "primary_lenses"
        ]:
            require(
                lens
                in DISCIPLINE_ORDER,
                (
                    "unknown discipline lens "
                    f"{lens} in {item['thread_id']}"
                ),
            )


def decision_maturity(
    thread: dict,
) -> dict:
    stages = thread[
        "stages"
    ]

    publicly_established = sum(
        1
        for item
        in stages.values()
        if item[
            "status"
        ]
        == "PUBLICLY_ESTABLISHED"
    )

    missionlab_synthesis = sum(
        1
        for item
        in stages.values()
        if item[
            "status"
        ]
        == "MISSIONLAB_SYNTHESIS"
    )

    unavailable = sum(
        1
        for item
        in stages.values()
        if item[
            "status"
        ]
        == "NOT_PUBLICLY_ENUMERATED"
    )

    not_applicable = sum(
        1
        for item
        in stages.values()
        if item[
            "status"
        ]
        == "NOT_APPLICABLE"
    )

    return {
        "publicly_established_stages": (
            publicly_established
        ),
        "missionlab_synthesis_stages": (
            missionlab_synthesis
        ),
        "not_publicly_enumerated_stages": (
            unavailable
        ),
        "not_applicable_stages": (
            not_applicable
        ),
        "total_stages": (
            len(
                STAGE_ORDER
            )
        ),
        "complete_private_decision_history_claimed": (
            False
        ),
    }


def write_thread_csv(
    threads: list[dict],
):
    fieldnames = [
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

    with THREAD_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for item in threads:
            maturity = decision_maturity(
                item
            )

            writer.writerow(
                {
                    "thread_id": (
                        item[
                            "thread_id"
                        ]
                    ),
                    "title": (
                        item[
                            "title"
                        ]
                    ),
                    "classification": (
                        item[
                            "classification"
                        ]
                    ),
                    "anomaly": (
                        item[
                            "anomaly"
                        ]
                    ),
                    "primary_lenses": (
                        "|".join(
                            item[
                                "primary_lenses"
                            ]
                        )
                    ),
                    "anchor_event_ids": (
                        "|".join(
                            item[
                                "anchor_event_ids"
                            ]
                        )
                    ),
                    "detection_status": (
                        item[
                            "stages"
                        ][
                            "detection"
                        ][
                            "status"
                        ]
                    ),
                    "evidence_status": (
                        item[
                            "stages"
                        ][
                            "evidence"
                        ][
                            "status"
                        ]
                    ),
                    "constraint_status": (
                        item[
                            "stages"
                        ][
                            "constraint"
                        ][
                            "status"
                        ]
                    ),
                    "options_status": (
                        item[
                            "stages"
                        ][
                            "options"
                        ][
                            "status"
                        ]
                    ),
                    "decision_status": (
                        item[
                            "stages"
                        ][
                            "decision"
                        ][
                            "status"
                        ]
                    ),
                    "action_status": (
                        item[
                            "stages"
                        ][
                            "action"
                        ][
                            "status"
                        ]
                    ),
                    "outcome_status": (
                        item[
                            "stages"
                        ][
                            "outcome"
                        ][
                            "status"
                        ]
                    ),
                    "publicly_established_stages": (
                        maturity[
                            "publicly_established_stages"
                        ]
                    ),
                    "missionlab_synthesis_stages": (
                        maturity[
                            "missionlab_synthesis_stages"
                        ]
                    ),
                    "not_publicly_enumerated_stages": (
                        maturity[
                            "not_publicly_enumerated_stages"
                        ]
                    ),
                    "not_applicable_stages": (
                        maturity[
                            "not_applicable_stages"
                        ]
                    ),
                }
            )


def write_postflight_csv(
    records: list[dict],
):
    fieldnames = [
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

    with POSTFLIGHT_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for item in records:
            writer.writerow(
                {
                    "order": (
                        item[
                            "order"
                        ]
                    ),
                    "record_id": (
                        item[
                            "record_id"
                        ]
                    ),
                    "date": (
                        item[
                            "date"
                        ]
                    ),
                    "date_precision": (
                        item[
                            "date_precision"
                        ]
                    ),
                    "category": (
                        item[
                            "category"
                        ]
                    ),
                    "status": (
                        item[
                            "status"
                        ]
                    ),
                    "open_issue": (
                        item[
                            "open_issue"
                        ]
                    ),
                    "source_ids": (
                        "|".join(
                            item[
                                "source_ids"
                            ]
                        )
                    ),
                    "summary": (
                        item[
                            "summary"
                        ]
                    ),
                }
            )


def build_figure(
    threads: list[dict],
):
    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    status_code = {
        "NOT_PUBLICLY_ENUMERATED": 0,
        "NOT_APPLICABLE": 1,
        "MISSIONLAB_SYNTHESIS": 2,
        "PUBLICLY_ESTABLISHED": 3,
    }

    matrix = [
        [
            status_code[
                thread[
                    "stages"
                ][
                    stage_name
                ][
                    "status"
                ]
            ]
            for stage_name
            in STAGE_ORDER
        ]
        for thread
        in threads
    ]

    labels = [
        thread[
            "thread_id"
        ]
        for thread
        in threads
    ]

    fig, ax = plt.subplots(
        figsize=(
            13,
            8,
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
                STAGE_ORDER
            )
        )
    )

    ax.set_xticklabels(
        [
            value.upper()
            for value
            in STAGE_ORDER
        ],
        rotation=30,
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
            "Decision-Thread Evidence Matrix"
        )
    )

    colorbar = fig.colorbar(
        image,
        ax=ax,
        fraction=0.03,
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
            "Not public",
            "N/A",
            "MissionLab synthesis",
            "Publicly established",
        ]
    )

    fig.text(
        0.5,
        0.01,
        (
            "Decision threads reconstruct public "
            "evidence flow, not private NASA console "
            "dialogue, complete option trees, or "
            "undisclosed decision authority."
        ),
        ha="center",
        fontsize=8,
    )

    fig.tight_layout(
        rect=(
            0,
            0.04,
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


def build_dependencies(
    phase7a: dict,
    phase2: dict,
    waste: dict,
    tps: dict,
    entry: dict,
    phase6: dict,
) -> list[dict]:
    return [
        {
            "dependency_id": "PHASE7A",
            "dataset_id": (
                phase7a[
                    "dataset_id"
                ]
            ),
        },
        {
            "dependency_id": "PHASE2",
            "dataset_id": (
                phase2[
                    "dataset_id"
                ]
            ),
        },
        {
            "dependency_id": (
                "WASTE_MANAGEMENT"
            ),
            "dataset_id": (
                waste[
                    "dataset_id"
                ]
            ),
        },
        {
            "dependency_id": (
                "TPS_EVIDENCE"
            ),
            "dataset_id": (
                tps[
                    "dataset_id"
                ]
            ),
        },
        {
            "dependency_id": (
                "ENTRY_RECOVERY"
            ),
            "dataset_id": (
                entry[
                    "dataset_id"
                ]
            ),
        },
        {
            "dependency_id": (
                "LUNAR_SCIENCE"
            ),
            "dataset_id": (
                phase6[
                    "dataset_id"
                ]
            ),
        },
    ]


def main():
    print()
    print(
        "Phase 7B Artemis II Mission Control "
        "Decision Threads and Phase 7 Closure"
    )
    print(
        "=" * 72
    )

    mission = load_json(
        MISSION_PATH
    )

    phase7a = load_json(
        PHASE7A_PATH
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
        phase7a.get(
            "dataset_id"
        )
        == (
            "phase7a_artemis_ii_"
            "mission_control_perspectives"
        ),
        "Phase 7A dependency mismatch",
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
        tps.get(
            "dataset_id"
        )
        == (
            "phase2f1_orion_tps_heritage_evidence"
        ),
        "TPS dependency mismatch",
    )

    require(
        entry.get(
            "dataset_id"
        )
        == (
            "phase4a1_artemis_ii_"
            "entry_descent_recovery_evidence"
        ),
        "entry/recovery dependency mismatch",
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

    threads = decision_threads()
    postflight = postflight_timeline()
    sources = source_registry()

    validate_thread_structure(
        threads
    )

    require(
        len(
            postflight
        )
        == 6,
        (
            "expected 6 postflight records, "
            f"found {len(postflight)}"
        ),
    )

    require(
        [
            item[
                "order"
            ]
            for item
            in postflight
        ]
        == list(
            range(
                1,
                7,
            )
        ),
        "postflight timeline order mismatch",
    )

    source_ids = {
        item[
            "source_id"
        ]
        for item
        in sources
    }

    for item in postflight:
        for source_id in item[
            "source_ids"
        ]:
            require(
                source_id
                in source_ids,
                (
                    "postflight timeline uses "
                    f"unknown source: {source_id}"
                ),
            )

    phase7a_event_ids = {
        item[
            "event_id"
        ]
        for item
        in phase7a[
            "shared_timeline"
        ]
    }

    for thread in threads:
        for event_id in thread[
            "anchor_event_ids"
        ]:
            require(
                event_id
                in phase7a_event_ids,
                (
                    "decision thread references "
                    f"unknown Phase 7A event: {event_id}"
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

    write_thread_csv(
        threads
    )

    write_postflight_csv(
        postflight
    )

    build_figure(
        threads
    )

    dependencies = build_dependencies(
        phase7a,
        phase2,
        waste,
        tps,
        entry,
        phase6,
    )

    result = {
        "dataset_id": (
            "phase7b_artemis_ii_"
            "mission_control_decision_threads"
        ),
        "mission": "Artemis II",
        "phase": "7B",
        "status": (
            "MISSION_CONTROL_DECISION_"
            "SYNTHESIS_COMPLETE"
        ),
        "purpose": (
            "Integrate validated Artemis II "
            "public evidence into MissionLab "
            "decision threads and a postflight "
            "engineering timeline while preserving "
            "private-console and root-cause boundaries."
        ),
        "decision_stage_model": (
            STAGE_ORDER
        ),
        "input_dependencies": (
            dependencies
        ),
        "public_postflight_source_registry": (
            sources
        ),
        "decision_threads": (
            threads
        ),
        "decision_maturity": {
            thread[
                "thread_id"
            ]: decision_maturity(
                thread
            )
            for thread
            in threads
        },
        "postflight_engineering_timeline": (
            postflight
        ),
        "postflight_open_issue_registry": [
            {
                "issue_id": (
                    "URINE_VENT_LINE_ROOT_CAUSE"
                ),
                "status": (
                    "OPEN_IN_CURATED_PUBLIC_EVIDENCE"
                ),
                "publicly_confirmed_root_cause": (
                    False
                ),
                "latest_curated_public_state": (
                    "NASA reported hardware assessment "
                    "and data gathering in support of "
                    "root-cause identification and "
                    "future corrective action."
                ),
            },
            {
                "issue_id": (
                    "MISSION_AND_FAULT_MANAGEMENT_"
                    "POSTFLIGHT_ANALYSIS"
                ),
                "status": (
                    "ANALYSIS_REPORTED_ONGOING"
                ),
                "publicly_confirmed_final_result": (
                    False
                ),
                "latest_curated_public_state": (
                    "NASA Ames publicly described "
                    "postflight performance analysis "
                    "as ongoing."
                ),
            },
        ],
        "phase7_integration_policy": {
            "decision_thread_requires_seven_stage_schema": (
                True
            ),
            "public_evidence_and_missionlab_synthesis_separated": (
                True
            ),
            "private_console_dialogue_reconstructed": (
                False
            ),
            "private_option_tree_reconstructed": (
                False
            ),
            "specific_controller_decision_authority_inferred": (
                False
            ),
            "unknown_root_cause_promoted_to_confirmed": (
                False
            ),
            "expected_constraint_promoted_to_anomaly": (
                False
            ),
            "temporal_sequence_promoted_to_causation": (
                False
            ),
            "postflight_open_investigations_forced_closed": (
                False
            ),
        },
        "critical_non_equivalences": [
            {
                "left": (
                    "MISSIONLAB_DECISION_THREAD"
                ),
                "right": (
                    "NASA_PRIVATE_CONSOLE_TRANSCRIPT"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "PUBLIC_SEQUENCE"
                ),
                "right": (
                    "COMPLETE_INTERNAL_DECISION_LOGIC"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "PUBLIC_ACTION"
                ),
                "right": (
                    "COMPLETE_OPTION_SET"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "DISCIPLINE_RELEVANCE"
                ),
                "right": (
                    "DECISION_AUTHORITY"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "TEMPORAL_SEQUENCE"
                ),
                "right": (
                    "CAUSATION"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "TROUBLESHOOTING_ACTION"
                ),
                "right": (
                    "CONFIRMED_ROOT_CAUSE"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "EXPECTED_OPERATIONAL_CONSTRAINT"
                ),
                "right": (
                    "ANOMALY"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "INITIAL_POSTFLIGHT_ASSESSMENT"
                ),
                "right": (
                    "FINAL_ENGINEERING_DATASET"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "OPEN_PUBLIC_INVESTIGATION"
                ),
                "right": (
                    "RESOLVED_ROOT_CAUSE"
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
            "decision_threads_detection_to_outcome": (
                "COMPLETE"
            ),
            "postflight_engineering_timeline": (
                "COMPLETE"
            ),
            "phase7_overall": (
                "COMPLETE_RELATIVE_TO_"
                "DEFENSIBLE_PUBLIC_EVIDENCE"
            ),
        },
        "outputs": {
            "reference_json": (
                "data/reference/"
                "artemis_ii_decision_threads.json"
            ),
            "processed_json": (
                "data/processed/mission_control/"
                "artemis_ii_decision_threads.json"
            ),
            "decision_thread_csv": (
                "data/processed/mission_control/"
                "artemis_ii_decision_threads.csv"
            ),
            "postflight_timeline_csv": (
                "data/processed/mission_control/"
                "artemis_ii_postflight_engineering_timeline.csv"
            ),
            "figure": (
                "docs/assets/mission_control/"
                "phase7b_decision_thread_matrix.svg"
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
        "Decision-thread model:"
    )
    print(
        "  threads: "
        f"{len(threads)}"
    )
    print(
        "  stages per thread: "
        f"{len(STAGE_ORDER)}"
    )
    print(
        "  stage sequence: "
        + " -> ".join(
            STAGE_ORDER
        )
    )

    print()
    print(
        "Decision threads:"
    )

    for item in threads:
        maturity = decision_maturity(
            item
        )

        print(
            "  "
            + item[
                "thread_id"
            ]
            + ": "
            + str(
                maturity[
                    "publicly_established_stages"
                ]
            )
            + " public / "
            + str(
                maturity[
                    "missionlab_synthesis_stages"
                ]
            )
            + " synthesis / "
            + str(
                maturity[
                    "not_publicly_enumerated_stages"
                ]
            )
            + " not-public / "
            + str(
                maturity[
                    "not_applicable_stages"
                ]
            )
            + " N/A"
        )

    print()
    print(
        "Postflight engineering timeline:"
    )
    print(
        "  records: "
        f"{len(postflight)}"
    )

    for item in postflight:
        print(
            "  "
            + item[
                "date"
            ]
            + "  "
            + item[
                "record_id"
            ]
            + "  "
            + item[
                "status"
            ]
        )

    print()
    print(
        "Open public engineering issues:"
    )
    print(
        "  urine vent-line root cause: OPEN"
    )
    print(
        "  Mission and Fault Management "
        "postflight analysis: ONGOING IN CURATED SOURCE"
    )

    print()
    print(
        "Closed / matured public engineering threads:"
    )
    print(
        "  Artemis I TPS root cause -> "
        "Artemis II mitigation -> postflight outcome: COMPLETE"
    )
    print(
        "  lunar-science preliminary postflight "
        "interpretation: COMPLETE"
    )

    print()
    print(
        "Decision evidence boundaries:"
    )
    print(
        "  MissionLab decision thread "
        "!= NASA private console transcript"
    )
    print(
        "  public action "
        "!= complete option set"
    )
    print(
        "  discipline relevance "
        "!= decision authority"
    )
    print(
        "  temporal sequence "
        "!= causation"
    )
    print(
        "  troubleshooting action "
        "!= confirmed root cause"
    )
    print(
        "  expected operational constraint "
        "!= anomaly"
    )
    print(
        "  initial postflight assessment "
        "!= final engineering dataset"
    )
    print(
        "  open investigation "
        "!= resolved root cause"
    )

    print()
    print(
        "Phase 7 roadmap:"
    )
    print(
        "  discipline lenses: COMPLETE"
    )
    print(
        "  discipline-prioritized shared timeline: COMPLETE"
    )
    print(
        "  detection -> evidence -> constraint -> "
        "options -> decision -> action -> outcome: COMPLETE"
    )
    print(
        "  postflight engineering timeline: COMPLETE"
    )
    print(
        "  overall: COMPLETE RELATIVE TO "
        "DEFENSIBLE PUBLIC EVIDENCE"
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
            THREAD_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            POSTFLIGHT_CSV.relative_to(
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
        "PHASE 7B DECISION THREAD "
        "SYNTHESIS COMPLETE"
    )
    print(
        "PHASE 7 ROADMAP RECONSTRUCTION COMPLETE"
    )


if __name__ == "__main__":
    main()
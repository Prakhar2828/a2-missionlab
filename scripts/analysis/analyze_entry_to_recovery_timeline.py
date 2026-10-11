from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

EVIDENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_descent_recovery_evidence.json"
)

PHASE2_CORRELATION_PATH = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_event_correlations.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "recovery"
)

TIMELINE_JSON = (
    OUTPUT_DIR
    / "entry_to_recovery_operational_timeline.json"
)

TIMELINE_CSV = (
    OUTPUT_DIR
    / "entry_to_recovery_operational_timeline.csv"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "recovery"
)

TIMELINE_FIGURE = (
    ASSET_DIR
    / "phase4a2_entry_to_recovery_timeline.svg"
)


EXPECTED_EVIDENCE_ID = (
    "phase4a1_artemis_ii_entry_descent_recovery_evidence"
)

EXPECTED_EVENT_IDS = [
    "A2_FD10_DSN_TO_NSN_HANDOVER",
    "A2_FD10_CM_SM_SEPARATION",
    "A2_FD10_CREW_MODULE_RAISE_BURN",
    "A2_ENTRY_INTERFACE",
    "A2_ENTRY_PLASMA_BLACKOUT",
    "A2_ENTRY_COMM_REACQUISITION",
    "A2_DROGUE_DEPLOYMENT",
    "A2_MAIN_PARACHUTE_DEPLOYMENT",
    "A2_SPLASHDOWN",
    "A2_POST_SPLASHDOWN_POWERDOWN",
    "A2_RECOVERY_TEAM_APPROACH",
    "A2_CREW_EXTRACTED",
    "A2_CREW_HELICOPTER_TRANSFER",
    "A2_CREW_ABOARD_RECOVERY_SHIP",
    "A2_ORION_SECURED_IN_WELL_DECK",
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
        "PHASE 4A.2 ANALYSIS FAILED: "
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


def parse_utc(
    value: str,
) -> datetime:
    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def minutes_between(
    earlier: str,
    later: str,
) -> float:
    return (
        parse_utc(
            later
        )
        - parse_utc(
            earlier
        )
    ).total_seconds() / 60.0


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
        for line in text.splitlines()
    )

    path.write_text(
        cleaned + "\n",
        encoding="utf-8",
    )


def index_events(
    evidence: dict,
) -> dict[str, dict]:
    result = {}

    for event in evidence[
        "events"
    ]:
        event_id = event[
            "event_id"
        ]

        require(
            event_id not in result,
            (
                "duplicate evidence event: "
                f"{event_id}"
            ),
        )

        result[
            event_id
        ] = event

    return result


def phase2_state_for_event(
    event_id: str,
    correlations: dict,
):
    mapping = {
        "A2_ENTRY_INTERFACE": (
            "entry_interface",
            "derived",
        ),
        "A2_DROGUE_DEPLOYMENT": (
            "drogue_deploy",
            "altitude_anchor",
        ),
        "A2_MAIN_PARACHUTE_DEPLOYMENT": (
            "main_deploy",
            "altitude_anchor",
        ),
        "A2_SPLASHDOWN": (
            "splashdown",
            "derived_surface_crossing",
        ),
    }

    if event_id not in mapping:
        return None

    section_name, state_name = mapping[
        event_id
    ]

    require(
        section_name in correlations,
        (
            "Phase 2 correlation missing "
            f"section {section_name}"
        ),
    )

    require(
        state_name
        in correlations[
            section_name
        ],
        (
            "Phase 2 correlation missing "
            f"{section_name}.{state_name}"
        ),
    )

    state = correlations[
        section_name
    ][
        state_name
    ]

    require(
        isinstance(
            state,
            dict,
        ),
        (
            "Phase 2 correlated state "
            f"{section_name}.{state_name} "
            "is not an object"
        ),
    )

    return {
        "phase2_section": (
            section_name
        ),
        "phase2_state_key": (
            state_name
        ),
        "state_provenance": (
            "PHASE2_DERIVED_FROM_"
            "NASA_FLIGHT_DERIVED_EPHEMERIS"
        ),
        "state": (
            state
        ),
    }


STATE_MAP = {
    "A2_FD10_DSN_TO_NSN_HANDOVER": {
        "mission_phase": "ENTRY_PREPARATION",
        "communications_state": "NSN_HANDOVER_COMPLETE",
        "vehicle_configuration": "CREW_MODULE_SERVICE_MODULE_INTEGRATED",
        "parachute_state": "STOWED",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "NOT_STARTED",
    },
    "A2_FD10_CM_SM_SEPARATION": {
        "mission_phase": "ENTRY_PREPARATION",
        "communications_state": "ENTRY_COMMUNICATIONS_AVAILABLE",
        "vehicle_configuration": "CREW_MODULE_ONLY",
        "parachute_state": "STOWED",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "NOT_STARTED",
    },
    "A2_FD10_CREW_MODULE_RAISE_BURN": {
        "mission_phase": "ENTRY_PREPARATION",
        "communications_state": "ENTRY_COMMUNICATIONS_AVAILABLE",
        "vehicle_configuration": "ENTRY_ATTITUDE_CONFIGURED",
        "parachute_state": "STOWED",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "NOT_STARTED",
    },
    "A2_ENTRY_INTERFACE": {
        "mission_phase": "ATMOSPHERIC_ENTRY",
        "communications_state": "CONTACT_BEFORE_PLASMA_BLACKOUT",
        "vehicle_configuration": "CREW_MODULE_ATMOSPHERIC_ENTRY",
        "parachute_state": "STOWED",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "NOT_STARTED",
    },
    "A2_ENTRY_PLASMA_BLACKOUT": {
        "mission_phase": "ATMOSPHERIC_ENTRY",
        "communications_state": "PLANNED_PLASMA_BLACKOUT",
        "vehicle_configuration": "CREW_MODULE_ATMOSPHERIC_ENTRY",
        "parachute_state": "STOWED",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "NOT_STARTED",
    },
    "A2_ENTRY_COMM_REACQUISITION": {
        "mission_phase": "ATMOSPHERIC_ENTRY",
        "communications_state": "CONTACT_REACQUIRED",
        "vehicle_configuration": "CREW_MODULE_ATMOSPHERIC_ENTRY",
        "parachute_state": "STOWED",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "NOT_STARTED",
    },
    "A2_DROGUE_DEPLOYMENT": {
        "mission_phase": "PARACHUTE_DESCENT",
        "communications_state": "CONTACT_AVAILABLE",
        "vehicle_configuration": "CREW_MODULE_DESCENT",
        "parachute_state": "DROGUES_DEPLOYED",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "NOT_STARTED",
    },
    "A2_MAIN_PARACHUTE_DEPLOYMENT": {
        "mission_phase": "PARACHUTE_DESCENT",
        "communications_state": "CONTACT_AVAILABLE",
        "vehicle_configuration": "CREW_MODULE_DESCENT",
        "parachute_state": "THREE_MAIN_PARACHUTES_DEPLOYED",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "NOT_STARTED",
    },
    "A2_SPLASHDOWN": {
        "mission_phase": "SPLASHDOWN",
        "communications_state": "POST_ENTRY_CONTACT_AVAILABLE",
        "vehicle_configuration": "CREW_MODULE_AFLOAT",
        "parachute_state": "PARACHUTE_DESCENT_COMPLETE",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "SPLASHDOWN_COMPLETE",
    },
    "A2_POST_SPLASHDOWN_POWERDOWN": {
        "mission_phase": "POST_SPLASHDOWN_RECOVERY",
        "communications_state": "POST_SPLASHDOWN_CONTACT",
        "vehicle_configuration": "RECOVERY_CONFIGURATION_TRANSITION",
        "parachute_state": "DESCENT_SYSTEM_COMPLETE",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "SPACECRAFT_SAFING",
    },
    "A2_RECOVERY_TEAM_APPROACH": {
        "mission_phase": "POST_SPLASHDOWN_RECOVERY",
        "communications_state": "RECOVERY_OPERATIONS",
        "vehicle_configuration": "CREW_MODULE_AFLOAT",
        "parachute_state": "DESCENT_SYSTEM_COMPLETE",
        "crew_state": "ABOARD_ORION",
        "recovery_state": "RECOVERY_TEAM_APPROACH",
    },
    "A2_CREW_EXTRACTED": {
        "mission_phase": "CREW_RECOVERY",
        "communications_state": "RECOVERY_OPERATIONS",
        "vehicle_configuration": "CREW_MODULE_AFLOAT",
        "parachute_state": "DESCENT_SYSTEM_COMPLETE",
        "crew_state": "EXTRACTED_TO_FRONT_PORCH_RAFT",
        "recovery_state": "CREW_EXTRACTED",
    },
    "A2_CREW_HELICOPTER_TRANSFER": {
        "mission_phase": "CREW_RECOVERY",
        "communications_state": "RECOVERY_OPERATIONS",
        "vehicle_configuration": "CREW_MODULE_AFLOAT",
        "parachute_state": "DESCENT_SYSTEM_COMPLETE",
        "crew_state": "HELICOPTER_TRANSFER",
        "recovery_state": "CREW_TRANSFER_TO_SHIP",
    },
    "A2_CREW_ABOARD_RECOVERY_SHIP": {
        "mission_phase": "CREW_RECOVERY",
        "communications_state": "RECOVERY_OPERATIONS",
        "vehicle_configuration": "CREW_MODULE_AFLOAT",
        "parachute_state": "DESCENT_SYSTEM_COMPLETE",
        "crew_state": "ABOARD_RECOVERY_SHIP",
        "recovery_state": "CREW_RECOVERY_AT_SHIP_COMPLETE",
    },
    "A2_ORION_SECURED_IN_WELL_DECK": {
        "mission_phase": "SPACECRAFT_RECOVERY",
        "communications_state": "RECOVERY_OPERATIONS",
        "vehicle_configuration": "SECURED_IN_WELL_DECK",
        "parachute_state": "DESCENT_SYSTEM_COMPLETE",
        "crew_state": "ABOARD_RECOVERY_SHIP",
        "recovery_state": "SPACECRAFT_RECOVERY_AT_SHIP_COMPLETE",
    },
}


def build_timeline(
    evidence: dict,
    correlations: dict,
) -> list[dict]:
    event_index = index_events(
        evidence
    )

    require(
        list(
            event_index
        )
        == EXPECTED_EVENT_IDS,
        "Phase 4A.1 event order changed",
    )

    entry_utc = event_index[
        "A2_ENTRY_INTERFACE"
    ][
        "reported_utc_minute"
    ]

    splash_utc = event_index[
        "A2_SPLASHDOWN"
    ][
        "reported_utc_minute"
    ]

    timeline = []

    for order, event_id in enumerate(
        EXPECTED_EVENT_IDS,
        start=1,
    ):
        event = event_index[
            event_id
        ]

        state = STATE_MAP[
            event_id
        ]

        public_utc = event.get(
            "reported_utc_minute"
        )

        if public_utc is not None:
            elapsed_from_entry = (
                minutes_between(
                    entry_utc,
                    public_utc,
                )
            )

            elapsed_from_splashdown = (
                minutes_between(
                    splash_utc,
                    public_utc,
                )
            )

            time_basis = (
                "NASA_REPORTED_PUBLIC_MINUTE"
            )

        else:
            elapsed_from_entry = None
            elapsed_from_splashdown = None

            if event_id == (
                "A2_ENTRY_PLASMA_BLACKOUT"
            ):
                time_basis = (
                    "NASA_REPORTED_RELATIVE_"
                    "ORDER_APPROXIMATE_DURATION"
                )

            elif event_id == (
                "A2_POST_SPLASHDOWN_POWERDOWN"
            ):
                time_basis = (
                    "NASA_REPORTED_RELATIVE_ORDER"
                )

            else:
                time_basis = (
                    "UNTIMED_PUBLIC_EVENT"
                )

        phase2_crosslink = (
            phase2_state_for_event(
                event_id,
                correlations,
            )
        )

        timeline.append(
            {
                "order": (
                    order
                ),
                "event_id": (
                    event_id
                ),
                "event_type": (
                    event[
                        "event_type"
                    ]
                ),
                "public_utc_minute": (
                    public_utc
                ),
                "time_basis": (
                    time_basis
                ),
                "elapsed_from_entry_interface_public_minutes": (
                    elapsed_from_entry
                ),
                "elapsed_from_splashdown_public_minutes": (
                    elapsed_from_splashdown
                ),
                "mission_phase": (
                    state[
                        "mission_phase"
                    ]
                ),
                "communications_state": (
                    state[
                        "communications_state"
                    ]
                ),
                "vehicle_configuration": (
                    state[
                        "vehicle_configuration"
                    ]
                ),
                "parachute_state": (
                    state[
                        "parachute_state"
                    ]
                ),
                "crew_state": (
                    state[
                        "crew_state"
                    ]
                ),
                "recovery_state": (
                    state[
                        "recovery_state"
                    ]
                ),
                "phase2_state_crosslink": (
                    phase2_crosslink
                ),
                "evidence_class": (
                    event[
                        "evidence_class"
                    ]
                ),
                "source_event": (
                    event
                ),
                "provenance": (
                    "MISSIONLAB_DERIVED_"
                    "OPERATIONAL_TIMELINE"
                ),
            }
        )

    return timeline


def build_public_minute_intervals(
    timeline: list[dict],
) -> list[dict]:
    timed = [
        item
        for item
        in timeline
        if item[
            "public_utc_minute"
        ]
        is not None
    ]

    intervals = []

    for order, (
        first,
        second,
    ) in enumerate(
        zip(
            timed[:-1],
            timed[1:],
        ),
        start=1,
    ):
        delta = minutes_between(
            first[
                "public_utc_minute"
            ],
            second[
                "public_utc_minute"
            ],
        )

        intervals.append(
            {
                "order": (
                    order
                ),
                "from_event_id": (
                    first[
                        "event_id"
                    ]
                ),
                "to_event_id": (
                    second[
                        "event_id"
                    ]
                ),
                "public_update_minute_difference": (
                    delta
                ),
                "exact_operational_duration": (
                    False
                ),
                "interpretation": (
                    "Difference between NASA "
                    "public update minute anchors. "
                    "Not an exact event-to-event "
                    "telemetry duration."
                ),
                "provenance": (
                    "MISSIONLAB_DERIVED_"
                    "PUBLIC_MINUTE_DIFFERENCE"
                ),
            }
        )

    return intervals


def event_by_id(
    timeline: list[dict],
    event_id: str,
) -> dict:
    for item in timeline:
        if item[
            "event_id"
        ] == event_id:
            return item

    fail(
        f"timeline event missing: {event_id}"
    )

    raise RuntimeError


def build_duration_summary(
    timeline: list[dict],
) -> dict:
    def delta(
        first_id: str,
        second_id: str,
    ) -> float:
        first = event_by_id(
            timeline,
            first_id,
        )

        second = event_by_id(
            timeline,
            second_id,
        )

        require(
            first[
                "public_utc_minute"
            ]
            is not None,
            f"{first_id} has no public minute",
        )

        require(
            second[
                "public_utc_minute"
            ]
            is not None,
            f"{second_id} has no public minute",
        )

        return minutes_between(
            first[
                "public_utc_minute"
            ],
            second[
                "public_utc_minute"
            ],
        )

    return {
        "handover_to_separation_public_minutes": (
            delta(
                "A2_FD10_DSN_TO_NSN_HANDOVER",
                "A2_FD10_CM_SM_SEPARATION",
            )
        ),
        "separation_to_raise_burn_public_minutes": (
            delta(
                "A2_FD10_CM_SM_SEPARATION",
                "A2_FD10_CREW_MODULE_RAISE_BURN",
            )
        ),
        "raise_burn_to_entry_interface_public_minutes": (
            delta(
                "A2_FD10_CREW_MODULE_RAISE_BURN",
                "A2_ENTRY_INTERFACE",
            )
        ),
        "entry_interface_to_reacquisition_public_minutes": (
            delta(
                "A2_ENTRY_INTERFACE",
                "A2_ENTRY_COMM_REACQUISITION",
            )
        ),
        "reacquisition_to_drogues_public_minutes": (
            delta(
                "A2_ENTRY_COMM_REACQUISITION",
                "A2_DROGUE_DEPLOYMENT",
            )
        ),
        "drogues_to_mains_public_minutes": (
            delta(
                "A2_DROGUE_DEPLOYMENT",
                "A2_MAIN_PARACHUTE_DEPLOYMENT",
            )
        ),
        "mains_to_splashdown_public_minutes": (
            delta(
                "A2_MAIN_PARACHUTE_DEPLOYMENT",
                "A2_SPLASHDOWN",
            )
        ),
        "splashdown_to_recovery_approach_public_minutes": (
            delta(
                "A2_SPLASHDOWN",
                "A2_RECOVERY_TEAM_APPROACH",
            )
        ),
        "splashdown_to_crew_extracted_public_minutes": (
            delta(
                "A2_SPLASHDOWN",
                "A2_CREW_EXTRACTED",
            )
        ),
        "splashdown_to_crew_aboard_ship_public_minutes": (
            delta(
                "A2_SPLASHDOWN",
                "A2_CREW_ABOARD_RECOVERY_SHIP",
            )
        ),
        "splashdown_to_orion_secured_public_minutes": (
            delta(
                "A2_SPLASHDOWN",
                "A2_ORION_SECURED_IN_WELL_DECK",
            )
        ),
        "crew_extracted_to_helicopter_public_minutes": (
            delta(
                "A2_CREW_EXTRACTED",
                "A2_CREW_HELICOPTER_TRANSFER",
            )
        ),
        "helicopter_to_crew_aboard_ship_public_minutes": (
            delta(
                "A2_CREW_HELICOPTER_TRANSFER",
                "A2_CREW_ABOARD_RECOVERY_SHIP",
            )
        ),
        "crew_aboard_ship_to_orion_secured_public_minutes": (
            delta(
                "A2_CREW_ABOARD_RECOVERY_SHIP",
                "A2_ORION_SECURED_IN_WELL_DECK",
            )
        ),
        "interpretation": (
            "All values are differences between "
            "NASA-reported public update minute "
            "anchors. They are not exact telemetry "
            "durations."
        ),
    }


def build_state_transitions(
    timeline: list[dict],
) -> list[dict]:
    transitions = []

    fields = [
        "mission_phase",
        "communications_state",
        "vehicle_configuration",
        "parachute_state",
        "crew_state",
        "recovery_state",
    ]

    previous = None

    for item in timeline:
        if previous is None:
            previous = item
            continue

        for field in fields:
            if (
                item[
                    field
                ]
                != previous[
                    field
                ]
            ):
                transitions.append(
                    {
                        "transition_id": (
                            f"{field}__"
                            f"{previous['event_id']}__"
                            f"{item['event_id']}"
                        ),
                        "state_dimension": (
                            field
                        ),
                        "from_event_id": (
                            previous[
                                "event_id"
                            ]
                        ),
                        "to_event_id": (
                            item[
                                "event_id"
                            ]
                        ),
                        "from_state": (
                            previous[
                                field
                            ]
                        ),
                        "to_state": (
                            item[
                                field
                            ]
                        ),
                        "provenance": (
                            "MISSIONLAB_DERIVED_"
                            "OPERATIONAL_STATE_TRANSITION"
                        ),
                    }
                )

        previous = item

    return transitions


def validate_timeline(
    timeline: list[dict],
    intervals: list[dict],
    duration_summary: dict,
):
    require(
        len(
            timeline
        )
        == 15,
        (
            "expected 15 timeline events, "
            f"found {len(timeline)}"
        ),
    )

    require(
        [
            item[
                "order"
            ]
            for item
            in timeline
        ]
        == list(
            range(
                1,
                16,
            )
        ),
        "timeline ordering mismatch",
    )

    require(
        [
            item[
                "event_id"
            ]
            for item
            in timeline
        ]
        == EXPECTED_EVENT_IDS,
        "timeline event IDs changed",
    )

    timed_events = [
        item
        for item
        in timeline
        if item[
            "public_utc_minute"
        ]
        is not None
    ]

    require(
        len(
            timed_events
        )
        == 13,
        (
            "expected 13 minute-anchored events, "
            f"found {len(timed_events)}"
        ),
    )

    require(
        len(
            intervals
        )
        == 12,
        (
            "expected 12 consecutive public-minute "
            f"intervals, found {len(intervals)}"
        ),
    )

    phase2_crosslinks = [
        item
        for item
        in timeline
        if item[
            "phase2_state_crosslink"
        ]
        is not None
    ]

    require(
        [
            item[
                "event_id"
            ]
            for item
            in phase2_crosslinks
        ]
        == [
            "A2_ENTRY_INTERFACE",
            "A2_DROGUE_DEPLOYMENT",
            "A2_MAIN_PARACHUTE_DEPLOYMENT",
            "A2_SPLASHDOWN",
        ],
        "Phase 2 state crosslink set mismatch",
    )

    require(
        duration_summary[
            "handover_to_separation_public_minutes"
        ]
        == 18.0,
        "handover-to-separation interval mismatch",
    )

    require(
        duration_summary[
            "separation_to_raise_burn_public_minutes"
        ]
        == 4.0,
        "separation-to-raise interval mismatch",
    )

    require(
        duration_summary[
            "raise_burn_to_entry_interface_public_minutes"
        ]
        == 16.0,
        "raise-to-EI interval mismatch",
    )

    require(
        duration_summary[
            "entry_interface_to_reacquisition_public_minutes"
        ]
        == 7.0,
        "EI-to-reacquisition interval mismatch",
    )

    require(
        duration_summary[
            "reacquisition_to_drogues_public_minutes"
        ]
        == 3.0,
        "reacquisition-to-drogues interval mismatch",
    )

    require(
        duration_summary[
            "drogues_to_mains_public_minutes"
        ]
        == 1.0,
        "drogues-to-mains interval mismatch",
    )

    require(
        duration_summary[
            "mains_to_splashdown_public_minutes"
        ]
        == 3.0,
        "mains-to-splashdown interval mismatch",
    )

    require(
        duration_summary[
            "splashdown_to_recovery_approach_public_minutes"
        ]
        == 5.0,
        "splashdown-to-approach interval mismatch",
    )

    require(
        duration_summary[
            "splashdown_to_crew_extracted_public_minutes"
        ]
        == 87.0,
        "splashdown-to-extraction interval mismatch",
    )

    require(
        duration_summary[
            "splashdown_to_crew_aboard_ship_public_minutes"
        ]
        == 111.0,
        "splashdown-to-ship interval mismatch",
    )

    require(
        duration_summary[
            "splashdown_to_orion_secured_public_minutes"
        ]
        == 500.0,
        "splashdown-to-Orion-secured interval mismatch",
    )

    for interval in intervals:
        require(
            interval[
                "exact_operational_duration"
            ]
            is False,
            (
                "public-minute difference "
                "incorrectly promoted to exact duration"
            ),
        )


def write_csv(
    timeline: list[dict],
):
    fieldnames = [
        "order",
        "event_id",
        "event_type",
        "public_utc_minute",
        "time_basis",
        "elapsed_from_entry_interface_public_minutes",
        "elapsed_from_splashdown_public_minutes",
        "mission_phase",
        "communications_state",
        "vehicle_configuration",
        "parachute_state",
        "crew_state",
        "recovery_state",
        "phase2_crosslink_present",
        "phase2_section",
        "phase2_state_key",
        "evidence_class",
        "provenance",
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

        for item in timeline:
            crosslink = item[
                "phase2_state_crosslink"
            ]

            writer.writerow(
                {
                    "order": (
                        item[
                            "order"
                        ]
                    ),
                    "event_id": (
                        item[
                            "event_id"
                        ]
                    ),
                    "event_type": (
                        item[
                            "event_type"
                        ]
                    ),
                    "public_utc_minute": (
                        item[
                            "public_utc_minute"
                        ]
                        or ""
                    ),
                    "time_basis": (
                        item[
                            "time_basis"
                        ]
                    ),
                    "elapsed_from_entry_interface_public_minutes": (
                        ""
                        if item[
                            "elapsed_from_entry_interface_public_minutes"
                        ]
                        is None
                        else item[
                            "elapsed_from_entry_interface_public_minutes"
                        ]
                    ),
                    "elapsed_from_splashdown_public_minutes": (
                        ""
                        if item[
                            "elapsed_from_splashdown_public_minutes"
                        ]
                        is None
                        else item[
                            "elapsed_from_splashdown_public_minutes"
                        ]
                    ),
                    "mission_phase": (
                        item[
                            "mission_phase"
                        ]
                    ),
                    "communications_state": (
                        item[
                            "communications_state"
                        ]
                    ),
                    "vehicle_configuration": (
                        item[
                            "vehicle_configuration"
                        ]
                    ),
                    "parachute_state": (
                        item[
                            "parachute_state"
                        ]
                    ),
                    "crew_state": (
                        item[
                            "crew_state"
                        ]
                    ),
                    "recovery_state": (
                        item[
                            "recovery_state"
                        ]
                    ),
                    "phase2_crosslink_present": (
                        crosslink is not None
                    ),
                    "phase2_section": (
                        ""
                        if crosslink is None
                        else crosslink[
                            "phase2_section"
                        ]
                    ),
                    "phase2_state_key": (
                        ""
                        if crosslink is None
                        else crosslink[
                            "phase2_state_key"
                        ]
                    ),
                    "evidence_class": (
                        item[
                            "evidence_class"
                        ]
                    ),
                    "provenance": (
                        item[
                            "provenance"
                        ]
                    ),
                }
            )


def build_figure(
    timeline: list[dict],
):
    timed = [
        item
        for item
        in timeline
        if item[
            "public_utc_minute"
        ]
        is not None
    ]

    entry = parse_utc(
        event_by_id(
            timeline,
            "A2_ENTRY_INTERFACE",
        )[
            "public_utc_minute"
        ]
    )

    x = [
        (
            parse_utc(
                item[
                    "public_utc_minute"
                ]
            )
            - entry
        ).total_seconds() / 60.0
        for item in timed
    ]

    labels = [
        {
            "A2_FD10_DSN_TO_NSN_HANDOVER":
                "DSN→NSN",
            "A2_FD10_CM_SM_SEPARATION":
                "CM/SM sep",
            "A2_FD10_CREW_MODULE_RAISE_BURN":
                "Raise burn",
            "A2_ENTRY_INTERFACE":
                "EI",
            "A2_ENTRY_COMM_REACQUISITION":
                "Comm reacq",
            "A2_DROGUE_DEPLOYMENT":
                "Drogues",
            "A2_MAIN_PARACHUTE_DEPLOYMENT":
                "Mains",
            "A2_SPLASHDOWN":
                "Splashdown",
            "A2_RECOVERY_TEAM_APPROACH":
                "Recovery approach",
            "A2_CREW_EXTRACTED":
                "Crew extracted",
            "A2_CREW_HELICOPTER_TRANSFER":
                "Helicopter",
            "A2_CREW_ABOARD_RECOVERY_SHIP":
                "Crew aboard ship",
            "A2_ORION_SECURED_IN_WELL_DECK":
                "Orion secured",
        }[
            item[
                "event_id"
            ]
        ]
        for item in timed
    ]

    fig, ax = plt.subplots(
        figsize=(
            17,
            6,
        )
    )

    y = [
        0
        for _ in x
    ]

    ax.plot(
        x,
        y,
        marker="o",
    )

    for i, (
        x_value,
        label,
    ) in enumerate(
        zip(
            x,
            labels,
        )
    ):
        offset = (
            22
            if i % 2 == 0
            else -34
        )

        ax.annotate(
            label,
            (
                x_value,
                0,
            ),
            xytext=(
                0,
                offset,
            ),
            textcoords="offset points",
            ha="center",
            va=(
                "bottom"
                if offset > 0
                else "top"
            ),
            fontsize=7,
            rotation=45,
        )

    ax.axvline(
        0.0,
        linestyle="--",
        linewidth=1.0,
    )

    splash_elapsed = (
        event_by_id(
            timeline,
            "A2_SPLASHDOWN",
        )[
            "elapsed_from_entry_interface_public_minutes"
        ]
    )

    ax.axvline(
        splash_elapsed,
        linestyle="--",
        linewidth=1.0,
    )

    ax.set_yticks(
        []
    )

    ax.set_xlabel(
        (
            "Minutes relative to Entry Interface "
            "using NASA public-minute anchors"
        )
    )

    ax.set_title(
        (
            "Artemis II Entry-to-Recovery "
            "Operational Timeline"
        )
    )

    ax.grid(
        True,
        axis="x",
        alpha=0.25,
    )

    ax.text(
        0.5,
        0.04,
        (
            "Public-minute differences are "
            "timeline relationships, not exact "
            "telemetry durations. Plasma blackout "
            "and post-splashdown powerdown remain "
            "relative-order events because exact "
            "public seconds are unavailable."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        TIMELINE_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        TIMELINE_FIGURE
    )


def main():
    print()
    print(
        "Phase 4A.2 Artemis II "
        "Entry-to-Recovery Operational "
        "Timeline Reconstruction"
    )
    print(
        "=" * 72
    )

    evidence = load_json(
        EVIDENCE_PATH
    )

    correlations = load_json(
        PHASE2_CORRELATION_PATH
    )

    require(
        evidence.get(
            "dataset_id"
        )
        == EXPECTED_EVIDENCE_ID,
        "Phase 4A.1 evidence identity mismatch",
    )

    require(
        evidence.get(
            "status"
        )
        == "REFERENCE_EVIDENCE_ASSEMBLED",
        "Phase 4A.1 evidence status mismatch",
    )

    require(
        correlations.get(
            "trajectory_provenance"
        )
        == "NASA flight-derived ephemeris",
        "Phase 2 trajectory provenance mismatch",
    )

    print()
    print(
        "Dependencies:"
    )
    print(
        "  Phase 4A.1 public evidence: PASS"
    )
    print(
        "  Phase 2 entry correlations: PASS"
    )

    timeline = build_timeline(
        evidence,
        correlations,
    )

    intervals = (
        build_public_minute_intervals(
            timeline
        )
    )

    duration_summary = (
        build_duration_summary(
            timeline
        )
    )

    transitions = (
        build_state_transitions(
            timeline
        )
    )

    validate_timeline(
        timeline,
        intervals,
        duration_summary,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_csv(
        timeline
    )

    build_figure(
        timeline
    )

    phase2_crosslinked_events = [
        item[
            "event_id"
        ]
        for item in timeline
        if item[
            "phase2_state_crosslink"
        ]
        is not None
    ]

    result = {
        "dataset_id": (
            "phase4a2_artemis_ii_"
            "entry_to_recovery_operational_timeline"
        ),
        "mission": (
            "Artemis II"
        ),
        "phase": (
            "4A.2"
        ),
        "status": (
            "ENTRY_TO_RECOVERY_TIMELINE_COMPLETE"
        ),
        "dependencies": {
            "phase4a1_evidence": (
                evidence[
                    "dataset_id"
                ]
            ),
            "phase2_entry_correlations": (
                "data/processed/entry/"
                "entry_event_correlations.json"
            ),
        },
        "timeline": (
            timeline
        ),
        "public_minute_intervals": (
            intervals
        ),
        "public_minute_duration_summary": (
            duration_summary
        ),
        "operational_state_transitions": (
            transitions
        ),
        "phase2_state_integration": {
            "crosslinked_event_count": (
                len(
                    phase2_crosslinked_events
                )
            ),
            "crosslinked_event_ids": (
                phase2_crosslinked_events
            ),
            "rule": (
                "Phase 2 trajectory states are "
                "preserved as derived trajectory "
                "cross-links and are not reclassified "
                "as NASA-reported event telemetry."
            ),
        },
        "state_dimensions": [
            "mission_phase",
            "communications_state",
            "vehicle_configuration",
            "parachute_state",
            "crew_state",
            "recovery_state",
        ],
        "timeline_boundaries": {
            "public_update_minute_equals_exact_event_epoch": (
                False
            ),
            "public_minute_difference_equals_exact_operational_duration": (
                False
            ),
            "entry_interface_to_reacquisition_public_minute_difference_equals_exact_blackout_duration": (
                False
            ),
            "phase2_derived_state_equals_nasa_reported_telemetry": (
                False
            ),
            "parachute_architecture_equals_individual_deployment_telemetry": (
                False
            ),
            "post_splashdown_powerdown_has_exact_public_timestamp": (
                False
            ),
            "recovery_procedure_implies_unreported_exact_event_times": (
                False
            ),
            "phase4_recomputes_phase2_entry_physics": (
                False
            ),
        },
        "outputs": {
            "timeline_json": str(
                TIMELINE_JSON.relative_to(
                    ROOT
                )
            ),
            "timeline_csv": str(
                TIMELINE_CSV.relative_to(
                    ROOT
                )
            ),
            "timeline_figure": str(
                TIMELINE_FIGURE.relative_to(
                    ROOT
                )
            ),
        },
    }

    with TIMELINE_JSON.open(
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
        "Operational timeline:"
    )
    print(
        f"  total events: {len(timeline)}"
    )
    print(
        "  public-minute anchors: 13"
    )
    print(
        "  relative-order-only events: 2"
    )
    print(
        f"  public-minute intervals: {len(intervals)}"
    )
    print(
        f"  state transitions: {len(transitions)}"
    )
    print(
        "  Phase 2 trajectory-state crosslinks: 4"
    )

    print()
    print(
        "Entry / descent public-minute relationships:"
    )
    print(
        "  DSN→NSN to CM/SM separation: "
        f"{duration_summary['handover_to_separation_public_minutes']:.0f} min"
    )
    print(
        "  separation to raise burn: "
        f"{duration_summary['separation_to_raise_burn_public_minutes']:.0f} min"
    )
    print(
        "  raise burn to Entry Interface: "
        f"{duration_summary['raise_burn_to_entry_interface_public_minutes']:.0f} min"
    )
    print(
        "  Entry Interface to comm reacquisition: "
        f"{duration_summary['entry_interface_to_reacquisition_public_minutes']:.0f} min"
    )
    print(
        "  reacquisition to drogues: "
        f"{duration_summary['reacquisition_to_drogues_public_minutes']:.0f} min"
    )
    print(
        "  drogues to mains: "
        f"{duration_summary['drogues_to_mains_public_minutes']:.0f} min"
    )
    print(
        "  mains to splashdown: "
        f"{duration_summary['mains_to_splashdown_public_minutes']:.0f} min"
    )

    print()
    print(
        "Recovery public-minute relationships:"
    )
    print(
        "  splashdown to recovery approach: "
        f"{duration_summary['splashdown_to_recovery_approach_public_minutes']:.0f} min"
    )
    print(
        "  splashdown to crew extracted: "
        f"{duration_summary['splashdown_to_crew_extracted_public_minutes']:.0f} min"
    )
    print(
        "  splashdown to crew aboard ship: "
        f"{duration_summary['splashdown_to_crew_aboard_ship_public_minutes']:.0f} min"
    )
    print(
        "  splashdown to Orion secured: "
        f"{duration_summary['splashdown_to_orion_secured_public_minutes']:.0f} min"
    )

    print()
    print(
        "State progression:"
    )
    print(
        "  deep-space return communications"
    )
    print(
        "  → entry preparation"
    )
    print(
        "  → crew-module-only configuration"
    )
    print(
        "  → atmospheric entry"
    )
    print(
        "  → planned plasma blackout"
    )
    print(
        "  → communications reacquisition"
    )
    print(
        "  → drogue descent"
    )
    print(
        "  → three-main descent"
    )
    print(
        "  → splashdown"
    )
    print(
        "  → spacecraft safing"
    )
    print(
        "  → recovery-team approach"
    )
    print(
        "  → crew extraction"
    )
    print(
        "  → helicopter transfer"
    )
    print(
        "  → crew aboard recovery ship"
    )
    print(
        "  → Orion secured in well deck"
    )

    print()
    print(
        "Phase 2 crosslinks:"
    )
    print(
        "  Entry Interface derived state: PRESERVED"
    )
    print(
        "  drogue altitude-anchor state: PRESERVED"
    )
    print(
        "  main altitude-anchor state: PRESERVED"
    )
    print(
        "  splashdown-correlated surface state: PRESERVED"
    )

    print()
    print(
        "Evidence boundary:"
    )
    print(
        "  public minute != exact telemetry epoch"
    )
    print(
        "  public-minute difference != exact operational duration"
    )
    print(
        "  EI→reacquisition difference != exact blackout duration"
    )
    print(
        "  Phase 2 derived state != NASA-reported telemetry"
    )
    print(
        "  architecture != individual parachute telemetry"
    )
    print(
        "  relative-order event != fabricated timestamp"
    )
    print(
        "  Phase 4 reuse != Phase 2 physics recomputation"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            TIMELINE_JSON.relative_to(
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
            TIMELINE_FIGURE.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 4A.2 ENTRY-TO-RECOVERY "
        "TIMELINE COMPLETE"
    )


if __name__ == "__main__":
    main()
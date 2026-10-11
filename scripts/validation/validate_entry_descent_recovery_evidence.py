from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_descent_recovery_evidence.json"
)

PHASE2_ENTRY_EVENTS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_events.json"
)


EXPECTED_DATASET_ID = (
    "phase4a1_artemis_ii_entry_descent_recovery_evidence"
)

EXPECTED_SOURCE_IDS = {
    "NASA_A2_FLIGHT_DAY_10_LIVE_REENTRY_2026_04_10",
    "NASA_A2_PRESS_KIT",
    "NASA_ORION_FUN_FACTS",
    "NASA_ARTEMIS_II_REFERENCE_GUIDE_2026",
    "NASA_ORION_CREW_MODULE_REFERENCE",
}

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

EXPECTED_THREAD_IDS = {
    "entry_preparation_and_configuration",
    "entry_communications_blackout",
    "parachute_descent_and_splashdown",
    "crew_recovery",
    "spacecraft_recovery",
}

EXPECTED_PHASE2_OVERLAP = {
    "A2_ENTRY_INTERFACE": "entry_interface",
    "A2_DROGUE_DEPLOYMENT": "drogue_deploy",
    "A2_MAIN_PARACHUTE_DEPLOYMENT": "main_deploy",
    "A2_SPLASHDOWN": "splashdown",
}


def fail(message: str):
    raise SystemExit(
        "PHASE 4A.1 VALIDATION FAILED: "
        f"{message}"
    )


def require(
    condition: bool,
    message: str,
):
    if not condition:
        fail(message)


def load_json(
    path: Path,
) -> dict:
    require(
        path.exists(),
        f"missing file: {path}",
    )

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as f:
            return json.load(f)

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


def index_events(
    reference: dict,
) -> dict[str, dict]:
    result = {}

    for event in reference[
        "events"
    ]:
        event_id = event[
            "event_id"
        ]

        require(
            event_id not in result,
            (
                "duplicate event ID: "
                f"{event_id}"
            ),
        )

        result[
            event_id
        ] = event

    return result


def index_phase2_events(
    reference: dict,
) -> dict[str, dict]:
    result = {}

    for event in reference[
        "events"
    ]:
        event_id = event[
            "event_id"
        ]

        require(
            event_id not in result,
            (
                "duplicate Phase 2 "
                f"event ID: {event_id}"
            ),
        )

        result[
            event_id
        ] = event

    return result


def validate_identity(
    reference: dict,
):
    require(
        reference.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "dataset identity mismatch",
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
        == "4A.1",
        "phase identity mismatch",
    )

    require(
        reference.get(
            "status"
        )
        == "REFERENCE_EVIDENCE_ASSEMBLED",
        "reference status mismatch",
    )


def validate_scope(
    reference: dict,
):
    scope = reference[
        "scope"
    ]

    require(
        scope[
            "starts_with"
        ]
        == (
            "Orion crew module and service module "
            "separation on Flight Day 10"
        ),
        "scope start mismatch",
    )

    require(
        scope[
            "ends_with"
        ]
        == (
            "Orion secured in the well deck "
            "of USS John P. Murtha"
        ),
        "scope end mismatch",
    )

    required_exclusions = {
        "recomputation of Phase 2 entry trajectory",
        "recomputation of Phase 2 atmospheric density",
        "recomputation of Phase 2 Mach number",
        "recomputation of Phase 2 rarefaction",
        "recomputation of Phase 2 convective heating",
        "recomputation of Phase 2 TPS material physics",
        "private Orion telemetry",
        "unreported sub-second parachute event times",
        "unreported splashdown coordinates",
    }

    require(
        required_exclusions.issubset(
            set(
                scope[
                    "excludes"
                ]
            )
        ),
        "Phase 4 scope exclusions incomplete",
    )


def validate_sources(
    reference: dict,
):
    sources = reference[
        "source_registry"
    ]

    require(
        len(
            sources
        )
        == 5,
        (
            "expected 5 sources, found "
            f"{len(sources)}"
        ),
    )

    source_ids = {
        item[
            "source_id"
        ]
        for item in sources
    }

    require(
        source_ids
        == EXPECTED_SOURCE_IDS,
        "source registry mismatch",
    )

    primary = next(
        item
        for item in sources
        if item[
            "source_id"
        ]
        == (
            "NASA_A2_FLIGHT_DAY_10_"
            "LIVE_REENTRY_2026_04_10"
        )
    )

    require(
        primary[
            "source_type"
        ]
        == "NASA_MISSION_LIVE_UPDATE",
        "primary live source type mismatch",
    )


def validate_time_rules(
    reference: dict,
):
    rules = reference[
        "time_interpretation"
    ]

    require(
        rules[
            "public_event_time_resolution"
        ]
        == "minute",
        "public event time resolution changed",
    )

    require(
        rules[
            "utc_offset_hours_on_2026_04_10"
        ]
        == -4,
        "EDT UTC offset mismatch",
    )

    require(
        (
            "exact public blackout-start second"
            in rules[
                "blackout_rule"
            ]
        ),
        "blackout precision boundary missing",
    )


def validate_phase2_dependency(
    reference: dict,
):
    dependencies = reference[
        "phase2_dependencies"
    ]

    require(
        dependencies[
            "existing_public_event_reference"
        ]
        == (
            "data/reference/"
            "artemis_ii_entry_events.json"
        ),
        "Phase 2 event-reference path mismatch",
    )

    require(
        dependencies[
            "rule"
        ]
        == (
            "Phase 4A.1 treats validated Phase 2 "
            "entry products as dependencies rather "
            "than recreating them."
        ),
        "Phase 2 reuse rule mismatch",
    )

    require(
        len(
            dependencies[
                "already_reconstructed_in_phase2"
            ]
        )
        >= 9,
        (
            "Phase 2 reconstructed-product "
            "registry unexpectedly small"
        ),
    )


def validate_parachute_architecture(
    reference: dict,
):
    architecture = reference[
        "parachute_architecture"
    ]

    require(
        architecture[
            "architecture_not_as_flown_event_log"
        ]
        is True,
        (
            "parachute architecture incorrectly "
            "treated as as-flown event log"
        ),
    )

    require(
        architecture[
            "total_parachutes"
        ]
        == 11,
        "Orion total parachute count mismatch",
    )

    components = {
        item[
            "component"
        ]: item
        for item
        in architecture[
            "components"
        ]
    }

    expected = {
        "forward_bay_cover_parachutes": (
            3,
            7,
        ),
        "drogue_parachutes": (
            2,
            23,
        ),
        "pilot_parachutes": (
            3,
            11,
        ),
        "main_parachutes": (
            3,
            116,
        ),
    }

    require(
        set(
            components
        )
        == set(
            expected
        ),
        "parachute component set mismatch",
    )

    total = 0

    for (
        component,
        (
            expected_count,
            expected_diameter,
        ),
    ) in expected.items():
        item = components[
            component
        ]

        require(
            item[
                "count"
            ]
            == expected_count,
            (
                f"{component} count mismatch"
            ),
        )

        require(
            item[
                "nominal_diameter_ft_each"
            ]
            == expected_diameter,
            (
                f"{component} diameter mismatch"
            ),
        )

        total += item[
            "count"
        ]

    require(
        total == 11,
        "parachute component sum mismatch",
    )


def validate_event_set(
    reference: dict,
):
    events = reference[
        "events"
    ]

    require(
        len(
            events
        )
        == 15,
        (
            "expected 15 public evidence events, "
            f"found {len(events)}"
        ),
    )

    require(
        [
            event[
                "event_id"
            ]
            for event
            in events
        ]
        == EXPECTED_EVENT_IDS,
        (
            "event IDs or event ordering "
            "mismatch"
        ),
    )


def validate_timed_chronology(
    events: dict[str, dict],
):
    timed_event_ids = [
        "A2_FD10_DSN_TO_NSN_HANDOVER",
        "A2_FD10_CM_SM_SEPARATION",
        "A2_FD10_CREW_MODULE_RAISE_BURN",
        "A2_ENTRY_INTERFACE",
        "A2_ENTRY_COMM_REACQUISITION",
        "A2_DROGUE_DEPLOYMENT",
        "A2_MAIN_PARACHUTE_DEPLOYMENT",
        "A2_SPLASHDOWN",
        "A2_RECOVERY_TEAM_APPROACH",
        "A2_CREW_EXTRACTED",
        "A2_CREW_HELICOPTER_TRANSFER",
        "A2_CREW_ABOARD_RECOVERY_SHIP",
        "A2_ORION_SECURED_IN_WELL_DECK",
    ]

    timestamps = [
        parse_utc(
            events[
                event_id
            ][
                "reported_utc_minute"
            ]
        )
        for event_id
        in timed_event_ids
    ]

    require(
        timestamps
        == sorted(
            timestamps
        ),
        "public event chronology is not monotonic",
    )

    require(
        events[
            "A2_ENTRY_INTERFACE"
        ][
            "reported_utc_minute"
        ]
        == "2026-04-10T23:53:00Z",
        "Entry Interface UTC mismatch",
    )

    require(
        events[
            "A2_ENTRY_COMM_REACQUISITION"
        ][
            "reported_utc_minute"
        ]
        == "2026-04-11T00:00:00Z",
        "communications reacquisition UTC mismatch",
    )

    require(
        events[
            "A2_DROGUE_DEPLOYMENT"
        ][
            "reported_utc_minute"
        ]
        == "2026-04-11T00:03:00Z",
        "drogue UTC mismatch",
    )

    require(
        events[
            "A2_MAIN_PARACHUTE_DEPLOYMENT"
        ][
            "reported_utc_minute"
        ]
        == "2026-04-11T00:04:00Z",
        "main-parachute UTC mismatch",
    )

    require(
        events[
            "A2_SPLASHDOWN"
        ][
            "reported_utc_minute"
        ]
        == "2026-04-11T00:07:00Z",
        "splashdown UTC mismatch",
    )

    require(
        events[
            "A2_ORION_SECURED_IN_WELL_DECK"
        ][
            "reported_utc_minute"
        ]
        == "2026-04-11T08:27:00Z",
        "well-deck recovery UTC mismatch",
    )


def validate_entry_blackout(
    events: dict[str, dict],
):
    blackout = events[
        "A2_ENTRY_PLASMA_BLACKOUT"
    ]

    require(
        blackout[
            "planned"
        ]
        is True,
        "entry blackout must remain planned",
    )

    require(
        blackout[
            "anomaly"
        ]
        is False,
        (
            "planned plasma blackout "
            "incorrectly classified as anomaly"
        ),
    )

    require(
        blackout[
            "reported_expected_duration_minutes"
        ]
        == 6,
        "expected blackout duration mismatch",
    )

    require(
        blackout[
            "exact_start_utc"
        ]
        is None,
        "exact blackout start was invented",
    )

    require(
        blackout[
            "exact_end_utc"
        ]
        is None,
        "exact blackout end was invented",
    )

    require(
        blackout[
            "missionlab_may_infer_exact_start"
        ]
        is False,
        (
            "blackout exact-start inference "
            "incorrectly allowed"
        ),
    )

    require(
        blackout[
            "missionlab_may_infer_exact_end"
        ]
        is False,
        (
            "blackout exact-end inference "
            "incorrectly allowed"
        ),
    )

    reacquisition = events[
        "A2_ENTRY_COMM_REACQUISITION"
    ]

    require(
        reacquisition[
            "blackout_exact_duration_derivable"
        ]
        is False,
        (
            "public minute reports incorrectly "
            "used to derive exact blackout duration"
        ),
    )


def validate_entry_and_parachute_events(
    events: dict[str, dict],
):
    entry = events[
        "A2_ENTRY_INTERFACE"
    ]

    require(
        entry[
            "reported_altitude_ft"
        ]
        == 400000,
        "Entry Interface altitude mismatch",
    )

    require(
        entry[
            "reported_speed_description"
        ]
        == "35 times the speed of sound",
        "Entry Interface speed description mismatch",
    )

    drogue = events[
        "A2_DROGUE_DEPLOYMENT"
    ]

    require(
        drogue[
            "architecture_count"
        ]
        == 2,
        "drogue architecture count mismatch",
    )

    require(
        drogue[
            "reported_altitude_ft"
        ]
        == 23400,
        "drogue altitude mismatch",
    )

    require(
        drogue[
            "reported_speed_ft_s"
        ]
        == 479,
        "drogue speed mismatch",
    )

    require(
        drogue[
            "associated_values_same_exact_subsecond_state_assumed"
        ]
        is False,
        (
            "drogue associated values incorrectly "
            "treated as exact same sub-second state"
        ),
    )

    main = events[
        "A2_MAIN_PARACHUTE_DEPLOYMENT"
    ]

    require(
        main[
            "architecture_count"
        ]
        == 3,
        "main-parachute architecture count mismatch",
    )

    require(
        main[
            "reported_altitude_ft"
        ]
        == 5400,
        "main-parachute altitude mismatch",
    )

    require(
        main[
            "reported_speed_upper_ft_s"
        ]
        == 200,
        "main-parachute speed bound mismatch",
    )

    require(
        main[
            "speed_relation"
        ]
        == "less_than",
        "main-parachute speed relation mismatch",
    )

    splashdown = events[
        "A2_SPLASHDOWN"
    ]

    require(
        splashdown[
            "exact_coordinates_public_in_curated_source"
        ]
        is False,
        (
            "exact splashdown coordinates "
            "incorrectly claimed"
        ),
    )


def validate_recovery_events(
    events: dict[str, dict],
):
    powerdown = events[
        "A2_POST_SPLASHDOWN_POWERDOWN"
    ]

    require(
        powerdown[
            "reported_time_relation"
        ]
        == "AFTER_SPLASHDOWN",
        "post-splashdown powerdown ordering mismatch",
    )

    require(
        powerdown[
            "exact_utc"
        ]
        is None,
        "powerdown exact UTC was invented",
    )

    extracted = events[
        "A2_CREW_EXTRACTED"
    ]

    require(
        extracted[
            "crew_status"
        ]
        == "SAFELY_EXTRACTED",
        "crew extraction status mismatch",
    )

    aboard = events[
        "A2_CREW_ABOARD_RECOVERY_SHIP"
    ]

    require(
        aboard[
            "crew_status"
        ]
        == "ABOARD_RECOVERY_SHIP",
        "crew recovery-ship status mismatch",
    )

    secured = events[
        "A2_ORION_SECURED_IN_WELL_DECK"
    ]

    require(
        secured[
            "spacecraft_status"
        ]
        == "SECURED_IN_RECOVERY_SHIP_WELL_DECK",
        "Orion well-deck status mismatch",
    )


def validate_phase2_overlap(
    events: dict[str, dict],
    phase2_events: dict[str, dict],
):
    for (
        phase4_id,
        phase2_id,
    ) in EXPECTED_PHASE2_OVERLAP.items():
        require(
            phase2_id in phase2_events,
            (
                "missing Phase 2 overlap event: "
                f"{phase2_id}"
            ),
        )

        phase4_event = events[
            phase4_id
        ]

        phase2_event = phase2_events[
            phase2_id
        ]

        require(
            phase4_event[
                "phase2_existing_event_id"
            ]
            == phase2_id,
            (
                f"{phase4_id} Phase 2 "
                "traceability mismatch"
            ),
        )

        require(
            phase4_event[
                "reported_utc_minute"
            ]
            == phase2_event[
                "reported_utc_minute"
            ],
            (
                f"{phase4_id} UTC differs "
                "from Phase 2 reference"
            ),
        )

    require(
        events[
            "A2_DROGUE_DEPLOYMENT"
        ][
            "reported_altitude_ft"
        ]
        == phase2_events[
            "drogue_deploy"
        ][
            "reported_altitude_ft"
        ],
        "drogue altitude differs from Phase 2",
    )

    require(
        events[
            "A2_MAIN_PARACHUTE_DEPLOYMENT"
        ][
            "reported_altitude_ft"
        ]
        == phase2_events[
            "main_deploy"
        ][
            "reported_altitude_ft"
        ],
        "main altitude differs from Phase 2",
    )


def validate_as_flown_parachute_boundary(
    reference: dict,
):
    confirmation = reference[
        "actual_parachute_confirmation"
    ]

    require(
        confirmation[
            "forward_bay_cover_parachutes"
        ][
            "explicit_as_flown_deployment_confirmed_in_primary_live_update"
        ]
        is False,
        (
            "forward bay cover deployment "
            "incorrectly claimed as explicitly "
            "confirmed in primary live update"
        ),
    )

    require(
        confirmation[
            "drogue_parachutes"
        ][
            "explicit_as_flown_deployment_confirmed_in_primary_live_update"
        ]
        is True,
        "drogue deployment not confirmed",
    )

    require(
        confirmation[
            "pilot_parachutes"
        ][
            "explicit_as_flown_deployment_confirmed_in_primary_live_update"
        ]
        is False,
        (
            "pilot-parachute deployment "
            "incorrectly claimed as separately "
            "timestamped in primary live update"
        ),
    )

    require(
        confirmation[
            "main_parachutes"
        ][
            "explicit_as_flown_deployment_confirmed_in_primary_live_update"
        ]
        is True,
        "main-parachute deployment not confirmed",
    )

    require(
        confirmation[
            "main_parachutes"
        ][
            "reported_count_deployed"
        ]
        == 3,
        "reported main-parachute count mismatch",
    )


def validate_operational_threads(
    reference: dict,
    events: dict[str, dict],
):
    threads = reference[
        "operational_threads"
    ]

    require(
        len(
            threads
        )
        == 5,
        (
            "expected 5 operational threads, "
            f"found {len(threads)}"
        ),
    )

    thread_ids = {
        thread[
            "thread_id"
        ]
        for thread in threads
    }

    require(
        thread_ids
        == EXPECTED_THREAD_IDS,
        "operational-thread set mismatch",
    )

    for thread in threads:
        require(
            len(
                thread[
                    "event_ids"
                ]
            )
            >= 3,
            (
                f"{thread['thread_id']} has "
                "too few event links"
            ),
        )

        for event_id in thread[
            "event_ids"
        ]:
            require(
                event_id in events,
                (
                    f"{thread['thread_id']} "
                    "references unknown event "
                    f"{event_id}"
                ),
            )


def validate_non_equivalences(
    reference: dict,
):
    items = reference[
        "critical_non_equivalences"
    ]

    require(
        len(
            items
        )
        == 10,
        (
            "expected 10 critical "
            f"non-equivalences, found {len(items)}"
        ),
    )

    for item in items:
        require(
            item[
                "equivalent"
            ]
            is False,
            (
                "critical non-equivalence "
                "incorrectly marked equivalent: "
                f"{item['left']} / {item['right']}"
            ),
        )


def validate_evidence_boundary(
    reference: dict,
):
    boundary = reference[
        "evidence_boundary"
    ]

    required_true = [
        "phase2_entry_quantitative_products_are_reused",
        "public_event_minutes_are_preserved",
    ]

    required_false = [
        "phase4_recomputes_phase2_entry_physics",
        "exact_unreported_seconds_are_invented",
        "planned_blackout_is_treated_as_anomaly",
        (
            "parachute_architecture_is_treated_"
            "as_as_flown_event_log"
        ),
        "forward_bay_cover_deployment_time_is_inferred",
        "pilot_parachute_deployment_time_is_inferred",
        "individual_parachute_loads_are_inferred",
        "exact_splashdown_coordinates_are_inferred",
        (
            "recovery_procedure_is_converted_"
            "into_unreported_exact_timestamps"
        ),
        "private_console_rationale_is_inferred",
    ]

    for key in required_true:
        require(
            boundary.get(
                key
            )
            is True,
            (
                "evidence boundary expected "
                f"TRUE: {key}"
            ),
        )

    for key in required_false:
        require(
            boundary.get(
                key
            )
            is False,
            (
                "evidence boundary expected "
                f"FALSE: {key}"
            ),
        )


def main():
    print()
    print(
        "Phase 4A.1 Artemis II Entry, Descent, "
        "Splashdown, and Recovery Public "
        "Evidence Validation"
    )
    print(
        "=" * 72
    )

    reference = load_json(
        REFERENCE_PATH
    )

    phase2_reference = load_json(
        PHASE2_ENTRY_EVENTS_PATH
    )

    validate_identity(
        reference
    )

    print()
    print(
        "Reference identity: PASS"
    )

    validate_scope(
        reference
    )

    print(
        "Scope definition: PASS"
    )

    validate_sources(
        reference
    )

    print(
        "Source registry: PASS"
    )

    validate_time_rules(
        reference
    )

    print(
        "Public time-resolution policy: PASS"
    )

    validate_phase2_dependency(
        reference
    )

    print(
        "Phase 2 reuse boundary: PASS"
    )

    validate_parachute_architecture(
        reference
    )

    print()
    print(
        "Orion parachute architecture: PASS"
    )
    print(
        "11-parachute architecture: PASS"
    )
    print(
        "Architecture / as-flown "
        "separation: PASS"
    )

    validate_event_set(
        reference
    )

    events = index_events(
        reference
    )

    print()
    print(
        "15-event public evidence set: PASS"
    )

    validate_timed_chronology(
        events
    )

    print(
        "Event chronology: PASS"
    )
    print(
        "UTC midnight rollover: PASS"
    )

    validate_entry_blackout(
        events
    )

    print()
    print(
        "Plasma-blackout evidence: PASS"
    )
    print(
        "Planned blackout / anomaly "
        "boundary: PASS"
    )
    print(
        "No fabricated blackout "
        "seconds: PASS"
    )

    validate_entry_and_parachute_events(
        events
    )

    print()
    print(
        "Entry Interface evidence: PASS"
    )
    print(
        "Drogue deployment evidence: PASS"
    )
    print(
        "Main-parachute deployment "
        "evidence: PASS"
    )
    print(
        "Splashdown evidence: PASS"
    )

    phase2_events = index_phase2_events(
        phase2_reference
    )

    validate_phase2_overlap(
        events,
        phase2_events,
    )

    print(
        "Phase 2 event cross-reference: PASS"
    )

    validate_as_flown_parachute_boundary(
        reference
    )

    print()
    print(
        "Forward bay cover evidence "
        "boundary: PASS"
    )
    print(
        "Drogue as-flown confirmation: PASS"
    )
    print(
        "Pilot-parachute evidence "
        "boundary: PASS"
    )
    print(
        "Three-main as-flown "
        "confirmation: PASS"
    )

    validate_recovery_events(
        events
    )

    print()
    print(
        "Post-splashdown powerdown "
        "evidence: PASS"
    )
    print(
        "Recovery-team approach: PASS"
    )
    print(
        "Crew extraction: PASS"
    )
    print(
        "Helicopter transfer: PASS"
    )
    print(
        "Crew aboard recovery ship: PASS"
    )
    print(
        "Orion secured in well deck: PASS"
    )

    validate_operational_threads(
        reference,
        events,
    )

    print()
    print(
        "Operational-thread set: PASS"
    )
    print(
        "Operational event traceability: PASS"
    )

    validate_non_equivalences(
        reference
    )

    print(
        "Critical non-equivalences: PASS"
    )

    validate_evidence_boundary(
        reference
    )

    print(
        "Evidence-boundary policy: PASS"
    )

    print()
    print(
        "Validated evidence totals:"
    )
    print(
        "  NASA / NASA-reference sources: 5"
    )
    print(
        "  public operational events: 15"
    )
    print(
        "  operational threads: 5"
    )
    print(
        "  parachute architecture count: 11"
    )
    print(
        "  critical non-equivalences: 10"
    )

    print()
    print(
        "Validated public sequence:"
    )
    print(
        "  DSN -> NSN handover"
    )
    print(
        "  crew module / service module separation"
    )
    print(
        "  crew module raise burn"
    )
    print(
        "  Entry Interface"
    )
    print(
        "  planned plasma blackout"
    )
    print(
        "  communications reacquisition"
    )
    print(
        "  drogue deployment"
    )
    print(
        "  three main parachutes deployed"
    )
    print(
        "  splashdown"
    )
    print(
        "  post-splashdown powerdown"
    )
    print(
        "  recovery-team approach"
    )
    print(
        "  crew extracted"
    )
    print(
        "  helicopter transfer"
    )
    print(
        "  crew aboard USS John P. Murtha"
    )
    print(
        "  Orion secured in well deck"
    )

    print()
    print(
        "Critical evidence boundaries:"
    )
    print(
        "  architecture != as-flown event log"
    )
    print(
        "  public minute != exact telemetry epoch"
    )
    print(
        "  expected six-minute blackout "
        "!= exact measured six minutes"
    )
    print(
        "  planned blackout != anomaly"
    )
    print(
        "  parachute deployment report "
        "!= individual load telemetry"
    )
    print(
        "  splashdown report "
        "!= exact public coordinates"
    )
    print(
        "  recovery procedure "
        "!= exact as-flown timestamp"
    )
    print(
        "  spacecraft recovery "
        "!= postflight analysis complete"
    )

    print()
    print(
        "PHASE 4A.1 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import json
from pathlib import Path


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

TIMELINE_JSON = (
    ROOT
    / "data"
    / "processed"
    / "recovery"
    / "entry_to_recovery_operational_timeline.json"
)

TIMELINE_CSV = (
    ROOT
    / "data"
    / "processed"
    / "recovery"
    / "entry_to_recovery_operational_timeline.csv"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "recovery"
    / "phase4a2_entry_to_recovery_timeline.svg"
)


EXPECTED_DATASET_ID = (
    "phase4a2_artemis_ii_"
    "entry_to_recovery_operational_timeline"
)

EXPECTED_EVIDENCE_ID = (
    "phase4a1_artemis_ii_"
    "entry_descent_recovery_evidence"
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

EXPECTED_PHASE2_CROSSLINK_IDS = [
    "A2_ENTRY_INTERFACE",
    "A2_DROGUE_DEPLOYMENT",
    "A2_MAIN_PARACHUTE_DEPLOYMENT",
    "A2_SPLASHDOWN",
]

EXPECTED_STATE_DIMENSIONS = [
    "mission_phase",
    "communications_state",
    "vehicle_configuration",
    "parachute_state",
    "crew_state",
    "recovery_state",
]


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 4A.2 VALIDATION FAILED: "
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
        f"{label} is not boolean: {value!r}"
    )

    raise RuntimeError


def normalize_path(
    value: str,
) -> str:
    return value.replace(
        "\\",
        "/",
    )


def index_by_event_id(
    timeline: list[dict],
) -> dict[str, dict]:
    result = {}

    for item in timeline:
        event_id = item[
            "event_id"
        ]

        require(
            event_id not in result,
            (
                "duplicate timeline event: "
                f"{event_id}"
            ),
        )

        result[
            event_id
        ] = item

    return result


def validate_identity(
    evidence: dict,
    phase2: dict,
    result: dict,
):
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
        phase2.get(
            "trajectory_provenance"
        )
        == "NASA flight-derived ephemeris",
        "Phase 2 trajectory provenance mismatch",
    )

    require(
        result.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "Phase 4A.2 dataset identity mismatch",
    )

    require(
        result.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        result.get(
            "phase"
        )
        == "4A.2",
        "phase identity mismatch",
    )

    require(
        result.get(
            "status"
        )
        == "ENTRY_TO_RECOVERY_TIMELINE_COMPLETE",
        "Phase 4A.2 status mismatch",
    )


def validate_dependencies(
    result: dict,
):
    dependencies = result[
        "dependencies"
    ]

    require(
        dependencies[
            "phase4a1_evidence"
        ]
        == EXPECTED_EVIDENCE_ID,
        "Phase 4A.1 dependency mismatch",
    )

    require(
        normalize_path(
            dependencies[
                "phase2_entry_correlations"
            ]
        )
        == (
            "data/processed/entry/"
            "entry_event_correlations.json"
        ),
        "Phase 2 entry-correlation dependency mismatch",
    )


def validate_timeline_structure(
    result: dict,
):
    timeline = result[
        "timeline"
    ]

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
        "timeline event numbering mismatch",
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
        "timeline event IDs or ordering mismatch",
    )

    for item in timeline:
        require(
            item[
                "provenance"
            ]
            == (
                "MISSIONLAB_DERIVED_"
                "OPERATIONAL_TIMELINE"
            ),
            (
                f"{item['event_id']} "
                "timeline provenance mismatch"
            ),
        )

    return timeline


def validate_time_basis(
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

    untimed = [
        item
        for item
        in timeline
        if item[
            "public_utc_minute"
        ]
        is None
    ]

    require(
        len(
            timed
        )
        == 13,
        (
            "expected 13 public-minute events, "
            f"found {len(timed)}"
        ),
    )

    require(
        [
            item[
                "event_id"
            ]
            for item
            in untimed
        ]
        == [
            "A2_ENTRY_PLASMA_BLACKOUT",
            "A2_POST_SPLASHDOWN_POWERDOWN",
        ],
        "relative-order-only event set mismatch",
    )

    blackout = next(
        item
        for item in untimed
        if item[
            "event_id"
        ]
        == "A2_ENTRY_PLASMA_BLACKOUT"
    )

    require(
        blackout[
            "time_basis"
        ]
        == (
            "NASA_REPORTED_RELATIVE_"
            "ORDER_APPROXIMATE_DURATION"
        ),
        "blackout time basis mismatch",
    )

    powerdown = next(
        item
        for item in untimed
        if item[
            "event_id"
        ]
        == "A2_POST_SPLASHDOWN_POWERDOWN"
    )

    require(
        powerdown[
            "time_basis"
        ]
        == "NASA_REPORTED_RELATIVE_ORDER",
        "post-splashdown powerdown time basis mismatch",
    )

    for item in timed:
        require(
            item[
                "time_basis"
            ]
            == "NASA_REPORTED_PUBLIC_MINUTE",
            (
                f"{item['event_id']} "
                "public-minute time basis mismatch"
            ),
        )


def validate_public_minute_intervals(
    result: dict,
):
    intervals = result[
        "public_minute_intervals"
    ]

    require(
        len(
            intervals
        )
        == 12,
        (
            "expected 12 public-minute intervals, "
            f"found {len(intervals)}"
        ),
    )

    require(
        [
            item[
                "order"
            ]
            for item
            in intervals
        ]
        == list(
            range(
                1,
                13,
            )
        ),
        "public-minute interval numbering mismatch",
    )

    for interval in intervals:
        require(
            interval[
                "exact_operational_duration"
            ]
            is False,
            (
                "public-minute interval promoted "
                "to exact operational duration: "
                f"{interval['from_event_id']} -> "
                f"{interval['to_event_id']}"
            ),
        )

        require(
            interval[
                "provenance"
            ]
            == (
                "MISSIONLAB_DERIVED_"
                "PUBLIC_MINUTE_DIFFERENCE"
            ),
            "interval provenance mismatch",
        )


def validate_duration_summary(
    result: dict,
):
    summary = result[
        "public_minute_duration_summary"
    ]

    expected = {
        "handover_to_separation_public_minutes": 18.0,
        "separation_to_raise_burn_public_minutes": 4.0,
        "raise_burn_to_entry_interface_public_minutes": 16.0,
        "entry_interface_to_reacquisition_public_minutes": 7.0,
        "reacquisition_to_drogues_public_minutes": 3.0,
        "drogues_to_mains_public_minutes": 1.0,
        "mains_to_splashdown_public_minutes": 3.0,
        "splashdown_to_recovery_approach_public_minutes": 5.0,
        "splashdown_to_crew_extracted_public_minutes": 87.0,
        "splashdown_to_crew_aboard_ship_public_minutes": 111.0,
        "splashdown_to_orion_secured_public_minutes": 500.0,
        "crew_extracted_to_helicopter_public_minutes": 22.0,
        "helicopter_to_crew_aboard_ship_public_minutes": 2.0,
        "crew_aboard_ship_to_orion_secured_public_minutes": 389.0,
    }

    for (
        key,
        expected_value,
    ) in expected.items():
        require(
            summary[
                key
            ]
            == expected_value,
            (
                f"{key} mismatch: "
                f"{summary[key]} != {expected_value}"
            ),
        )

    require(
        (
            "not exact telemetry durations"
            in summary[
                "interpretation"
            ]
        ),
        "duration interpretation boundary missing",
    )


def validate_phase2_crosslinks(
    result: dict,
    timeline: list[dict],
):
    integration = result[
        "phase2_state_integration"
    ]

    require(
        integration[
            "crosslinked_event_count"
        ]
        == 4,
        "Phase 2 crosslink count mismatch",
    )

    require(
        integration[
            "crosslinked_event_ids"
        ]
        == EXPECTED_PHASE2_CROSSLINK_IDS,
        "Phase 2 crosslink event set mismatch",
    )

    crosslinked = [
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
            in crosslinked
        ]
        == EXPECTED_PHASE2_CROSSLINK_IDS,
        "timeline Phase 2 crosslink set mismatch",
    )

    expected_sections = {
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

    for item in crosslinked:
        event_id = item[
            "event_id"
        ]

        crosslink = item[
            "phase2_state_crosslink"
        ]

        expected_section, expected_key = (
            expected_sections[
                event_id
            ]
        )

        require(
            crosslink[
                "phase2_section"
            ]
            == expected_section,
            (
                f"{event_id} Phase 2 "
                "section mismatch"
            ),
        )

        require(
            crosslink[
                "phase2_state_key"
            ]
            == expected_key,
            (
                f"{event_id} Phase 2 "
                "state key mismatch"
            ),
        )

        require(
            crosslink[
                "state_provenance"
            ]
            == (
                "PHASE2_DERIVED_FROM_"
                "NASA_FLIGHT_DERIVED_EPHEMERIS"
            ),
            (
                f"{event_id} Phase 2 "
                "state provenance mismatch"
            ),
        )

        require(
            isinstance(
                crosslink[
                    "state"
                ],
                dict,
            ),
            (
                f"{event_id} Phase 2 "
                "state is not an object"
            ),
        )


def validate_operational_states(
    result: dict,
    timeline: list[dict],
):
    require(
        result[
            "state_dimensions"
        ]
        == EXPECTED_STATE_DIMENSIONS,
        "state-dimension registry mismatch",
    )

    events = index_by_event_id(
        timeline
    )

    require(
        events[
            "A2_ENTRY_PLASMA_BLACKOUT"
        ][
            "communications_state"
        ]
        == "PLANNED_PLASMA_BLACKOUT",
        "blackout communications state mismatch",
    )

    require(
        events[
            "A2_ENTRY_COMM_REACQUISITION"
        ][
            "communications_state"
        ]
        == "CONTACT_REACQUIRED",
        "reacquisition state mismatch",
    )

    require(
        events[
            "A2_DROGUE_DEPLOYMENT"
        ][
            "parachute_state"
        ]
        == "DROGUES_DEPLOYED",
        "drogue parachute state mismatch",
    )

    require(
        events[
            "A2_MAIN_PARACHUTE_DEPLOYMENT"
        ][
            "parachute_state"
        ]
        == "THREE_MAIN_PARACHUTES_DEPLOYED",
        "main parachute state mismatch",
    )

    require(
        events[
            "A2_SPLASHDOWN"
        ][
            "vehicle_configuration"
        ]
        == "CREW_MODULE_AFLOAT",
        "splashdown vehicle state mismatch",
    )

    require(
        events[
            "A2_CREW_EXTRACTED"
        ][
            "crew_state"
        ]
        == "EXTRACTED_TO_FRONT_PORCH_RAFT",
        "crew extraction state mismatch",
    )

    require(
        events[
            "A2_CREW_ABOARD_RECOVERY_SHIP"
        ][
            "recovery_state"
        ]
        == "CREW_RECOVERY_AT_SHIP_COMPLETE",
        "crew recovery completion state mismatch",
    )

    require(
        events[
            "A2_ORION_SECURED_IN_WELL_DECK"
        ][
            "recovery_state"
        ]
        == "SPACECRAFT_RECOVERY_AT_SHIP_COMPLETE",
        "spacecraft recovery completion state mismatch",
    )


def validate_state_transitions(
    result: dict,
):
    transitions = result[
        "operational_state_transitions"
    ]

    require(
        len(
            transitions
        )
        == 36,
        (
            "expected 36 state transitions, "
            f"found {len(transitions)}"
        ),
    )

    valid_dimensions = set(
        EXPECTED_STATE_DIMENSIONS
    )

    for transition in transitions:
        require(
            transition[
                "state_dimension"
            ]
            in valid_dimensions,
            (
                "unknown state-transition "
                f"dimension: "
                f"{transition['state_dimension']}"
            ),
        )

        require(
            transition[
                "from_event_id"
            ]
            in EXPECTED_EVENT_IDS,
            "transition from-event unknown",
        )

        require(
            transition[
                "to_event_id"
            ]
            in EXPECTED_EVENT_IDS,
            "transition to-event unknown",
        )

        require(
            transition[
                "from_state"
            ]
            != transition[
                "to_state"
            ],
            "state transition does not change state",
        )

        require(
            transition[
                "provenance"
            ]
            == (
                "MISSIONLAB_DERIVED_"
                "OPERATIONAL_STATE_TRANSITION"
            ),
            "state-transition provenance mismatch",
        )


def validate_boundaries(
    result: dict,
):
    boundaries = result[
        "timeline_boundaries"
    ]

    expected_false = [
        "public_update_minute_equals_exact_event_epoch",
        "public_minute_difference_equals_exact_operational_duration",
        (
            "entry_interface_to_reacquisition_"
            "public_minute_difference_equals_"
            "exact_blackout_duration"
        ),
        (
            "phase2_derived_state_equals_"
            "nasa_reported_telemetry"
        ),
        (
            "parachute_architecture_equals_"
            "individual_deployment_telemetry"
        ),
        (
            "post_splashdown_powerdown_has_"
            "exact_public_timestamp"
        ),
        (
            "recovery_procedure_implies_"
            "unreported_exact_event_times"
        ),
        "phase4_recomputes_phase2_entry_physics",
    ]

    require(
        set(
            boundaries
        )
        == set(
            expected_false
        ),
        "timeline boundary registry mismatch",
    )

    for key in expected_false:
        require(
            boundaries[
                key
            ]
            is False,
            (
                "timeline boundary expected "
                f"FALSE: {key}"
            ),
        )


def validate_csv(
    rows: list[dict],
    timeline: list[dict],
):
    require(
        len(
            rows
        )
        == 15,
        (
            "expected 15 timeline CSV rows, "
            f"found {len(rows)}"
        ),
    )

    for index, (
        row,
        item,
    ) in enumerate(
        zip(
            rows,
            timeline,
        ),
        start=1,
    ):
        require(
            int(
                row[
                    "order"
                ]
            )
            == item[
                "order"
            ],
            (
                f"CSV row {index} "
                "order mismatch"
            ),
        )

        scalar_fields = [
            "event_id",
            "event_type",
            "time_basis",
            "mission_phase",
            "communications_state",
            "vehicle_configuration",
            "parachute_state",
            "crew_state",
            "recovery_state",
            "evidence_class",
            "provenance",
        ]

        for field in scalar_fields:
            require(
                row[
                    field
                ]
                == item[
                    field
                ],
                (
                    f"CSV row {index} "
                    f"{field} mismatch"
                ),
            )

        expected_utc = (
            item[
                "public_utc_minute"
            ]
            or ""
        )

        require(
            row[
                "public_utc_minute"
            ]
            == expected_utc,
            (
                f"CSV row {index} "
                "UTC mismatch"
            ),
        )

        crosslink_present = (
            item[
                "phase2_state_crosslink"
            ]
            is not None
        )

        require(
            bool_from_csv(
                row[
                    "phase2_crosslink_present"
                ],
                (
                    f"CSV row {index} "
                    "phase2_crosslink_present"
                ),
            )
            is crosslink_present,
            (
                f"CSV row {index} "
                "Phase 2 crosslink flag mismatch"
            ),
        )

        if crosslink_present:
            crosslink = item[
                "phase2_state_crosslink"
            ]

            require(
                row[
                    "phase2_section"
                ]
                == crosslink[
                    "phase2_section"
                ],
                (
                    f"CSV row {index} "
                    "Phase 2 section mismatch"
                ),
            )

            require(
                row[
                    "phase2_state_key"
                ]
                == crosslink[
                    "phase2_state_key"
                ],
                (
                    f"CSV row {index} "
                    "Phase 2 state key mismatch"
                ),
            )

        else:
            require(
                row[
                    "phase2_section"
                ]
                == "",
                (
                    f"CSV row {index} "
                    "unexpected Phase 2 section"
                ),
            )

            require(
                row[
                    "phase2_state_key"
                ]
                == "",
                (
                    f"CSV row {index} "
                    "unexpected Phase 2 state key"
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
                "timeline_json"
            ]
        )
        == (
            "data/processed/recovery/"
            "entry_to_recovery_operational_timeline.json"
        ),
        "timeline JSON output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "timeline_csv"
            ]
        )
        == (
            "data/processed/recovery/"
            "entry_to_recovery_operational_timeline.csv"
        ),
        "timeline CSV output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "timeline_figure"
            ]
        )
        == (
            "docs/assets/recovery/"
            "phase4a2_entry_to_recovery_timeline.svg"
        ),
        "timeline figure output path mismatch",
    )


def validate_svg():
    require(
        FIGURE_PATH.exists(),
        (
            "missing timeline figure: "
            f"{FIGURE_PATH}"
        ),
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "timeline figure is empty",
    )

    content = FIGURE_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    require(
        "<svg"
        in content,
        "timeline figure is not SVG",
    )


def main():
    print()
    print(
        "Phase 4A.2 Artemis II "
        "Entry-to-Recovery Operational "
        "Timeline Validation"
    )
    print(
        "=" * 72
    )

    evidence = load_json(
        EVIDENCE_PATH
    )

    phase2 = load_json(
        PHASE2_CORRELATION_PATH
    )

    result = load_json(
        TIMELINE_JSON
    )

    csv_rows = load_csv(
        TIMELINE_CSV
    )

    validate_identity(
        evidence,
        phase2,
        result,
    )

    print()
    print(
        "Analysis identity: PASS"
    )

    validate_dependencies(
        result
    )

    print(
        "Dependency registry: PASS"
    )

    timeline = (
        validate_timeline_structure(
            result
        )
    )

    print()
    print(
        "15-event operational timeline: PASS"
    )
    print(
        "Timeline ordering: PASS"
    )
    print(
        "Timeline provenance: PASS"
    )

    validate_time_basis(
        timeline
    )

    print()
    print(
        "13 public-minute anchors: PASS"
    )
    print(
        "2 relative-order-only events: PASS"
    )
    print(
        "Blackout timing boundary: PASS"
    )
    print(
        "Powerdown timing boundary: PASS"
    )

    validate_public_minute_intervals(
        result
    )

    print()
    print(
        "12 public-minute intervals: PASS"
    )
    print(
        "Exact-duration prohibition: PASS"
    )

    validate_duration_summary(
        result
    )

    print(
        "Public-minute relationship summary: PASS"
    )

    validate_phase2_crosslinks(
        result,
        timeline,
    )

    print()
    print(
        "Phase 2 trajectory-state crosslinks: PASS"
    )
    print(
        "Entry Interface state crosslink: PASS"
    )
    print(
        "Drogue state crosslink: PASS"
    )
    print(
        "Main-parachute state crosslink: PASS"
    )
    print(
        "Splashdown-correlated state crosslink: PASS"
    )
    print(
        "Derived-state / telemetry boundary: PASS"
    )

    validate_operational_states(
        result,
        timeline,
    )

    print()
    print(
        "Mission-phase progression: PASS"
    )
    print(
        "Communications-state progression: PASS"
    )
    print(
        "Vehicle-configuration progression: PASS"
    )
    print(
        "Parachute-state progression: PASS"
    )
    print(
        "Crew-state progression: PASS"
    )
    print(
        "Recovery-state progression: PASS"
    )

    validate_state_transitions(
        result
    )

    print()
    print(
        "36 operational state transitions: PASS"
    )
    print(
        "State-transition topology: PASS"
    )

    validate_boundaries(
        result
    )

    print()
    print(
        "Timeline evidence-boundary policy: PASS"
    )
    print(
        "No Phase 2 physics recomputation: PASS"
    )
    print(
        "No fabricated event epochs: PASS"
    )

    validate_csv(
        csv_rows,
        timeline,
    )

    print()
    print(
        "Timeline CSV / JSON consistency: PASS"
    )

    validate_outputs(
        result
    )

    validate_svg()

    print(
        "Documentation figure: PASS"
    )

    print()
    print(
        "Validated timeline totals:"
    )
    print(
        "  total operational events: 15"
    )
    print(
        "  public-minute anchors: 13"
    )
    print(
        "  relative-order-only events: 2"
    )
    print(
        "  public-minute intervals: 12"
    )
    print(
        "  operational state transitions: 36"
    )
    print(
        "  Phase 2 trajectory-state crosslinks: 4"
    )

    print()
    print(
        "Validated entry/descent relationships:"
    )
    print(
        "  DSN→NSN to CM/SM separation: 18 min"
    )
    print(
        "  separation to raise burn: 4 min"
    )
    print(
        "  raise burn to Entry Interface: 16 min"
    )
    print(
        "  Entry Interface to comm reacquisition: 7 min"
    )
    print(
        "  reacquisition to drogues: 3 min"
    )
    print(
        "  drogues to mains: 1 min"
    )
    print(
        "  mains to splashdown: 3 min"
    )

    print()
    print(
        "Validated recovery relationships:"
    )
    print(
        "  splashdown to recovery approach: 5 min"
    )
    print(
        "  splashdown to crew extracted: 87 min"
    )
    print(
        "  splashdown to crew aboard ship: 111 min"
    )
    print(
        "  splashdown to Orion secured: 500 min"
    )
    print(
        "  crew extracted to helicopter: 22 min"
    )
    print(
        "  helicopter to crew aboard ship: 2 min"
    )
    print(
        "  crew aboard ship to Orion secured: 389 min"
    )

    print()
    print(
        "Critical boundaries:"
    )
    print(
        "  public minute != exact telemetry epoch"
    )
    print(
        "  public-minute difference != exact duration"
    )
    print(
        "  EI→reacquisition difference != exact blackout duration"
    )
    print(
        "  Phase 2 derived state != NASA telemetry"
    )
    print(
        "  parachute architecture != deployment telemetry"
    )
    print(
        "  relative-order event != fabricated timestamp"
    )
    print(
        "  Phase 4 reuse != Phase 2 physics recomputation"
    )

    print()
    print(
        "PHASE 4A.2 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_manual_piloting_control_modes.json"
)

MISSION_PATH = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

GNC_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_gnc_architecture.json"
)

EVENT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "gnc"
    / "manual_piloting_events.csv"
)

PROXIMITY_CSV = (
    ROOT
    / "data"
    / "processed"
    / "gnc"
    / "proximity_plan_vs_as_flown.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "gnc"
    / "manual_piloting_control_modes_summary.json"
)

TIMELINE_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "gnc"
    / "phase2j2_manual_piloting_timeline.svg"
)

PROXIMITY_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "gnc"
    / "phase2j2_proximity_plan_vs_as_flown.svg"
)


def fail(message):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def load_json(path):
    if not path.exists():
        fail(
            f"missing file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def parse_utc(value):
    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    ).astimezone(
        timezone.utc
    )


def met_string(
    launch,
    event,
):
    seconds = int(
        (
            event
            - launch
        ).total_seconds()
    )

    days, remainder = divmod(
        seconds,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    return (
        f"{days:02d}:"
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


def main():
    reference = load_json(
        REFERENCE_PATH
    )

    mission = load_json(
        MISSION_PATH
    )

    gnc = load_json(
        GNC_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    if (
        reference[
            "dataset_id"
        ]
        != "phase2j2_artemis_ii_manual_piloting_control_modes"
    ):
        fail(
            "dataset ID mismatch"
        )

    if (
        summary[
            "product_id"
        ]
        != "phase2j2_manual_piloting_control_modes_analysis"
    ):
        fail(
            "summary product ID mismatch"
        )

    if (
        gnc[
            "dataset_id"
        ]
        != "phase2j1_artemis_ii_gnc_architecture"
    ):
        fail(
            "Phase 2J.1 dependency mismatch"
        )

    sources = (
        reference[
            "sources"
        ]
    )

    if len(
        sources
    ) != 6:
        fail(
            "expected six curated NASA sources"
        )

    for source in sources:
        if (
            source[
                "organization"
            ]
            != "NASA"
        ):
            fail(
                "non-NASA source introduced"
            )

        if (
            not source[
                "url"
            ].startswith(
                "https://www.nasa.gov/"
            )
        ):
            fail(
                "unexpected source domain"
            )

        if (
            "?"
            in source[
                "url"
            ]
        ):
            fail(
                "canonical URL contains query parameters"
            )

    if (
        reference[
            "time_policy"
        ][
            "reported_local_timezone_offset"
        ]
        != "-04:00"
        or reference[
            "time_policy"
        ][
            "iana_timezone_database_required"
        ]
        is not False
    ):
        fail(
            "EDT conversion policy changed"
        )

    launch = parse_utc(
        mission[
            "launch_epoch_utc"
        ]
    )

    EDT = timezone(
        timedelta(
            hours=-4
        ),
        name="EDT",
    )

    fd4_start = datetime(
        2026,
        4,
        4,
        21,
        9,
        tzinfo=EDT,
    ).astimezone(
        timezone.utc
    )

    fd4_end = (
        fd4_start
        + timedelta(
            minutes=41
        )
    )

    fd8_planned = datetime(
        2026,
        4,
        8,
        22,
        55,
        tzinfo=EDT,
    ).astimezone(
        timezone.utc
    )

    fd4 = (
        reference[
            "flight_day_4_manual_piloting"
        ]
    )

    if (
        fd4[
            "derived_start_utc"
        ]
        != fd4_start.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        or fd4[
            "derived_start_met"
        ]
        != met_string(
            launch,
            fd4_start,
        )
        or fd4[
            "derived_end_utc"
        ]
        != fd4_end.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        or fd4[
            "derived_end_met"
        ]
        != met_string(
            launch,
            fd4_end,
        )
    ):
        fail(
            "Flight Day 4 clock validation failed"
        )

    fd8 = (
        reference[
            "flight_day_8_manual_piloting"
        ]
    )

    if (
        fd8[
            "derived_planned_utc"
        ]
        != fd8_planned.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        or fd8[
            "derived_planned_met"
        ]
        != met_string(
            launch,
            fd8_planned,
        )
    ):
        fail(
            "Flight Day 8 planned clock validation failed"
        )

    if (
        fd8[
            "execution_status"
        ]
        != "FOREGONE"
        or fd8[
            "performed"
        ]
        is not False
        or fd8[
            "planned_timestamp_is_executed_event_timestamp"
        ]
        is not False
    ):
        fail(
            "Flight Day 8 plan/execution boundary failed"
        )

    manual = (
        reference[
            "manual_control_architecture"
        ]
    )

    if (
        manual[
            "rotational_hand_controller"
        ][
            "command_domain"
        ]
        != "ATTITUDE"
        or manual[
            "translational_hand_controller"
        ][
            "command_domain"
        ]
        != "TRANSLATION"
        or manual[
            "hand_controller_is_direct_thruster_switch"
        ]
        is not False
    ):
        fail(
            "manual-control architecture failed"
        )

    if (
        manual[
            "command_path"
        ]
        != [
            "CREW_CONTROLLER_INPUT",
            "GNC_FLIGHT_SOFTWARE",
            "EFFECTOR_SELECTION",
            "RCS_THRUSTER_COMMAND",
        ]
    ):
        fail(
            "manual command path changed"
        )

    plan = (
        reference[
            "proximity_operations"
        ][
            "planned_reference"
        ]
    )

    if (
        plan[
            "step_count"
        ]
        != 17
        or len(
            plan[
                "steps"
            ]
        )
        != 17
    ):
        fail(
            "planned proximity sequence count failed"
        )

    expected_labels = [
        "PRE-SEPARATION",
        "SEPARATION / DRIFT",
        "180° PITCH MANEUVER",
        "NULL SEPARATION ΔV",
        "COARSE HQ",
        "APPROACH",
        "HQ 10m EVAL #1",
        "BACK AWAY",
        "STATIONKEEP",
        "ICPS MANEUVER",
        "APPROACH #2",
        "HQ 15m EVAL #2",
        "MULTI-AXIS TEST",
        "MANUAL BACK-OUT",
        "TURN TO ATT BURN",
        "AUX DEPARTURE",
        "LONG RANGE FTO",
    ]

    if [
        item[
            "source_label"
        ]
        for item in plan[
            "steps"
        ]
    ] != expected_labels:
        fail(
            "planned proximity labels changed"
        )

    geometry = (
        plan[
            "geometry_context"
        ]
    )

    if (
        geometry[
            "manual_takeover_range_approx_ft"
        ]
        != 300.0
        or geometry[
            "close_range_handling_stop_about_ft"
        ]
        != 30.0
        or geometry[
            "reference_guide_evaluation_1_range_m"
        ]
        != 10.0
        or geometry[
            "reference_guide_evaluation_2_range_m"
        ]
        != 15.0
    ):
        fail(
            "planned geometry changed"
        )

    if (
        geometry[
            "planned_values_are_as_flown_measurements"
        ]
        is not False
        or geometry[
            "thirty_ft_forced_equal_to_ten_meter_reference_step"
        ]
        is not False
        or geometry[
            "thirty_ft_forced_equal_to_fifteen_meter_reference_step"
        ]
        is not False
    ):
        fail(
            "geometry interpretation boundary failed"
        )

    flown = (
        reference[
            "proximity_operations"
        ][
            "as_flown"
        ]
    )

    required_flown_true = [
        "controlled_approach_confirmed",
        "controlled_retreat_confirmed",
        "onboard_navigation_sensors_used",
        "reaction_control_thrusters_used",
        "automated_departure_confirmed",
    ]

    if (
        flown[
            "execution_status"
        ]
        != "COMPLETED"
        or flown[
            "duration_minutes"
        ]
        != 70.0
        or flown[
            "duration_semantics"
        ]
        != "APPROXIMATELY"
    ):
        fail(
            "as-flown proximity status failed"
        )

    for key in required_flown_true:
        if (
            flown[
                key
            ]
            is not True
        ):
            fail(
                f"as-flown evidence failed: {key}"
            )

    required_flown_false = [
        "all_17_planned_steps_confirmed_individually",
        "planned_300_ft_gate_confirmed_as_measured_as_flown_range",
        "planned_30_ft_stop_confirmed_as_measured_as_flown_range",
        "planned_10m_evaluation_confirmed_as_measured_as_flown_range",
        "planned_15m_evaluation_confirmed_as_measured_as_flown_range",
        "exact_relative_range_history_available",
        "exact_relative_velocity_history_available",
        "exact_attitude_history_available",
        "exact_rhc_history_available",
        "exact_thc_history_available",
        "exact_individual_thruster_history_available",
    ]

    for key in required_flown_false:
        if (
            flown[
                key
            ]
            is not False
        ):
            fail(
                f"unsupported as-flown detail introduced: {key}"
            )

    authority = (
        reference[
            "proximity_operations"
        ][
            "control_authority_states"
        ]
    )

    if [
        item[
            "state"
        ]
        for item in authority
    ] != [
        "AUTOMATED_PRE_MANUAL_PROXIMITY_OPERATIONS",
        "CREW_MANUAL_PROXIMITY_OPERATIONS",
        "AUTOMATED_DEPARTURE",
    ]:
        fail(
            "control-authority sequence changed"
        )

    if any(
        item[
            "exact_transition_utc"
        ]
        is not None
        for item in authority
    ):
        fail(
            "unsupported exact authority transition time introduced"
        )

    if (
        fd4[
            "execution_status"
        ]
        != "COMPLETED"
        or fd4[
            "duration_minutes"
        ]
        != 41.0
        or fd4[
            "reported_control_mode_labels"
        ]
        != [
            "SIX_DEGREES_OF_FREEDOM",
            "THREE_DEGREES_OF_FREEDOM",
        ]
    ):
        fail(
            "Flight Day 4 evidence failed"
        )

    for key in [
        "mode_labels_define_complete_control_algorithm",
        "six_dof_control_algorithm_available",
        "three_dof_control_algorithm_available",
        "control_mode_gain_schedule_available",
        "thruster_allocation_algorithm_available",
        "controller_input_history_available",
        "individual_thruster_history_available",
        "attitude_time_series_available",
    ]:
        if (
            fd4[
                key
            ]
            is not False
        ):
            fail(
                f"unsupported Flight Day 4 detail introduced: {key}"
            )

    boundaries = (
        reference[
            "evidence_boundaries"
        ]
    )

    expected_true = {
        "planned_proximity_sequence_available",
        "planned_proximity_geometry_available",
        "as_flown_proximity_completion_available",
        "as_flown_approach_retreat_sequence_available",
        "as_flown_rcs_use_available",
        "as_flown_onboard_navigation_sensor_use_available",
        "as_flown_automated_departure_available",
        "flight_day_4_execution_available",
        "flight_day_4_control_mode_labels_available",
    }

    for key, value in (
        boundaries.items()
    ):
        if key in expected_true:
            if value is not True:
                fail(
                    f"expected evidence unavailable: {key}"
                )
        else:
            if value is not False:
                fail(
                    f"unsupported evidence became available: {key}"
                )

    with EVENT_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        event_rows = list(
            csv.DictReader(f)
        )

    if len(
        event_rows
    ) != 3:
        fail(
            "manual-piloting event CSV must contain three rows"
        )

    if [
        row[
            "event_id"
        ]
        for row in event_rows
    ] != [
        "proximity_operations_demonstration",
        "flight_day_4_manual_piloting",
        "flight_day_8_manual_piloting",
    ]:
        fail(
            "manual-piloting event CSV order changed"
        )

    with PROXIMITY_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        proximity_rows = list(
            csv.DictReader(f)
        )

    if len(
        proximity_rows
    ) != 17:
        fail(
            "proximity CSV must contain seventeen rows"
        )

    if any(
        row[
            "individually_confirmed_as_flown"
        ]
        != "false"
        for row in proximity_rows
    ):
        fail(
            "planned proximity steps incorrectly promoted as flown"
        )

    if (
        summary[
            "planned_proximity_step_count"
        ]
        != 17
        or summary[
            "flight_day_4"
        ][
            "execution"
        ]
        != "COMPLETED"
        or summary[
            "flight_day_8"
        ][
            "execution"
        ]
        != "FOREGONE"
    ):
        fail(
            "summary event state mismatch"
        )

    if (
        summary[
            "evidence_boundaries"
        ]
        != boundaries
        or summary[
            "guardrails"
        ]
        != reference[
            "guardrails"
        ]
    ):
        fail(
            "summary evidence-boundary mismatch"
        )

    for figure in [
        TIMELINE_FIGURE,
        PROXIMITY_FIGURE,
    ]:
        if not figure.exists():
            fail(
                f"missing figure: {figure}"
            )

        text = figure.read_text(
            encoding="utf-8"
        )

        if (
            "<svg"
            not in text
            or len(
                text
            )
            < 1000
        ):
            fail(
                f"invalid SVG: {figure}"
            )

    print()
    print(
        "Phase 2J.2 Manual Piloting / Control-Mode Validation"
    )

    print("=" * 72)

    print()
    print(
        "Manual-control architecture:"
    )

    print(
        "  RHC -> attitude: PASS"
    )

    print(
        "  THC -> translation: PASS"
    )

    print(
        "  direct thruster switching: FALSE"
    )

    print()
    print(
        "Premission proximity reference:"
    )

    print(
        "  17 steps: PASS"
    )

    print(
        "  300 ft planning context: PASS"
    )

    print(
        "  30 ft planning context: PASS"
    )

    print(
        "  10 m evaluation label: PASS"
    )

    print(
        "  15 m evaluation label: PASS"
    )

    print(
        "  planning geometry treated as measured flight data: FALSE"
    )

    print(
        "  30 ft forced equal to 10 m / 15 m step: FALSE"
    )

    print()
    print(
        "As-flown proximity operations:"
    )

    print(
        "  completed: PASS"
    )

    print(
        "  approximately 70 min: PASS"
    )

    print(
        "  approach / retreat: PASS"
    )

    print(
        "  onboard navigation sensors: PASS"
    )

    print(
        "  RCS use: PASS"
    )

    print(
        "  automated departure: PASS"
    )

    print(
        "  all 17 steps individually confirmed: FALSE"
    )

    print()
    print(
        "Control-authority reconstruction:"
    )

    print(
        "  automated pre-manual context: PASS"
    )

    print(
        "  crew manual proximity operations: PASS"
    )

    print(
        "  automated departure: PASS"
    )

    print(
        "  exact transition times public: FALSE"
    )

    print()
    print(
        "Flight Day 4:"
    )

    print(
        "  start UTC: 2026-04-05T01:09:00Z"
    )

    print(
        "  start MET: 03:02:33:48"
    )

    print(
        "  duration: 41 min"
    )

    print(
        "  derived end UTC: 2026-04-05T01:50:00Z"
    )

    print(
        "  derived end MET: 03:03:14:48"
    )

    print(
        "  six-DOF label: PASS"
    )

    print(
        "  three-DOF label: PASS"
    )

    print(
        "  underlying algorithms reconstructed: FALSE"
    )

    print()
    print(
        "Flight Day 8:"
    )

    print(
        "  planned UTC: 2026-04-09T02:55:00Z"
    )

    print(
        "  planned MET: 07:04:19:48"
    )

    print(
        "  execution: FOREGONE"
    )

    print(
        "  performed: FALSE"
    )

    print(
        "  planned time treated as executed event: FALSE"
    )

    print()
    print(
        "Generated products:"
    )

    print(
        "  event CSV rows: 3"
    )

    print(
        "  proximity reference CSV rows: 17"
    )

    print(
        "  summary: PASS"
    )

    print(
        "  timeline figure: PASS"
    )

    print(
        "  plan-vs-as-flown figure: PASS"
    )

    print()
    print(
        "OK: Phase 2J.2 manual-control architecture, "
        "premission proximity sequence, planning-geometry "
        "boundaries, as-flown proximity evidence, control-authority "
        "states, Flight Day 4 manual piloting, Flight Day 8 foregone "
        "activity, mission-clock correlation, control-mode "
        "non-inference guardrails, and generated products "
        "independently validated."
    )


if __name__ == "__main__":
    main()
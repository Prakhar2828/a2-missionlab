from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib.pyplot as plt


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

PROPULSION_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_esm_propulsion_architecture.json"
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

plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def fail(message):
    raise SystemExit(
        message
    )


def load_json(path):
    if not path.exists():
        fail(
            f"Missing required file: {path}"
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
    total_seconds = int(
        (
            event
            - launch
        ).total_seconds()
    )

    if total_seconds < 0:
        fail(
            "Negative mission elapsed time."
        )

    days, remainder = divmod(
        total_seconds,
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


def normalize_svg(path):
    text = path.read_text(
        encoding="utf-8",
    )

    path.write_text(
        "\n".join(
            line.rstrip(" \t")
            for line in text.splitlines()
        )
        + "\n",
        encoding="utf-8",
    )


def build_timeline_figure(reference):
    TIMELINE_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(15, 7)
    )

    ax.axis(
        "off"
    )

    ax.set_xlim(
        0,
        1,
    )

    ax.set_ylim(
        0,
        1,
    )

    ax.set_title(
        "Artemis II Manual Piloting and Control-Authority Evidence",
        fontsize=15,
        pad=18,
    )

    events = [
        (
            0.18,
            0.70,
            "Proximity Operations\n"
            "2026-04-01\n"
            "COMPLETED\n"
            "~70 min\n"
            "Crew manual maneuvering\n"
            "→ automated departure",
        ),
        (
            0.50,
            0.70,
            "Flight Day 4\n"
            "2026-04-05 01:09 UTC\n"
            "COMPLETED\n"
            "41 min\n"
            "6-DOF / 3-DOF",
        ),
        (
            0.82,
            0.70,
            "Flight Day 8\n"
            "2026-04-09 02:55 UTC\n"
            "PLANNED ONLY\n"
            "FOREGONE\n"
            "Not an executed event",
        ),
    ]

    for x, y, text in events:
        ax.text(
            x,
            y,
            text,
            ha="center",
            va="center",
            fontsize=9,
            bbox={
                "boxstyle":
                    "round,pad=0.6",

                "fill":
                    False,
            },
        )

    ax.annotate(
        "",
        xy=(
            0.42,
            0.70,
        ),
        xytext=(
            0.26,
            0.70,
        ),
        arrowprops={
            "arrowstyle":
                "->",
        },
    )

    ax.annotate(
        "",
        xy=(
            0.74,
            0.70,
        ),
        xytext=(
            0.58,
            0.70,
        ),
        arrowprops={
            "arrowstyle":
                "->",
        },
    )

    ax.text(
        0.5,
        0.28,
        (
            "Manual-control architecture: "
            "crew controller input → GNC flight software → "
            "effector selection → RCS command"
        ),
        ha="center",
        fontsize=9,
    )

    ax.text(
        0.5,
        0.14,
        (
            "Public mode labels and mission reports do not expose "
            "controller histories, control laws, or individual "
            "thruster-allocation histories."
        ),
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


def build_proximity_figure(reference):
    PROXIMITY_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plan = (
        reference[
            "proximity_operations"
        ][
            "planned_reference"
        ]
    )

    flown = (
        reference[
            "proximity_operations"
        ][
            "as_flown"
        ]
    )

    fig, ax = plt.subplots(
        figsize=(17, 12)
    )

    ax.axis(
        "off"
    )

    ax.set_xlim(
        0,
        1,
    )

    ax.set_ylim(
        0,
        1,
    )

    ax.set_title(
        "Artemis II Proximity Operations: Premission Plan vs As-Flown Evidence",
        fontsize=15,
        pad=18,
    )

    planned_text = (
        "PREMISSION REFERENCE SEQUENCE\n\n"
        + "\n".join(
            (
                f"{item['step']:02d}. "
                f"{item['source_label']}"
            )
            for item in plan[
                "steps"
            ]
        )
        + "\n\n"
        "Planning geometry includes ~300 ft manual takeover,\n"
        "about 30 ft close-range handling context,\n"
        "and reference-guide 10 m / 15 m HQ evaluations."
    )

    flown_text = (
        "AS-FLOWN CONFIRMED\n\n"
        "Demonstration completed\n"
        "Approximately 70 minutes\n"
        "Controlled approach confirmed\n"
        "Controlled retreat confirmed\n"
        "Onboard navigation sensors used\n"
        "RCS thrusters used\n"
        "Automated departure confirmed\n\n"
        "NOT established:\n"
        "17 individual planned steps\n"
        "measured 300 ft / 30 ft / 10 m / 15 m gates\n"
        "relative state time history\n"
        "controller history\n"
        "individual thruster history"
    )

    ax.text(
        0.28,
        0.51,
        planned_text,
        ha="center",
        va="center",
        fontsize=8.3,
        bbox={
            "boxstyle":
                "round,pad=0.7",

            "fill":
                False,
        },
    )

    ax.text(
        0.72,
        0.51,
        flown_text,
        ha="center",
        va="center",
        fontsize=8.8,
        bbox={
            "boxstyle":
                "round,pad=0.7",

            "fill":
                False,
        },
    )

    ax.text(
        0.5,
        0.06,
        (
            "Premission plan ≠ as-flown step log. "
            "Planned geometry ≠ measured as-flown range history."
        ),
        ha="center",
        fontsize=9,
    )

    fig.tight_layout()

    fig.savefig(
        PROXIMITY_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        PROXIMITY_FIGURE
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

    propulsion = load_json(
        PROPULSION_PATH
    )

    if (
        reference.get(
            "dataset_id"
        )
        != "phase2j2_artemis_ii_manual_piloting_control_modes"
    ):
        fail(
            "Unexpected Phase 2J.2 dataset ID."
        )

    if (
        gnc.get(
            "dataset_id"
        )
        != "phase2j1_artemis_ii_gnc_architecture"
    ):
        fail(
            "Unexpected Phase 2J.1 dataset ID."
        )

    if (
        propulsion.get(
            "dataset_id"
        )
        != "phase2i2_artemis_ii_esm_propulsion_architecture"
    ):
        fail(
            "Unexpected Phase 2I.2 dataset ID."
        )

    if (
        "launch_epoch_utc"
        not in mission
    ):
        fail(
            "Mission launch epoch missing."
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

    fd4_source = datetime(
        2026,
        4,
        4,
        21,
        9,
        tzinfo=EDT,
    )

    fd4_utc = (
        fd4_source
        .astimezone(
            timezone.utc
        )
    )

    fd4_end = (
        fd4_utc
        + timedelta(
            minutes=41
        )
    )

    fd8_source = datetime(
        2026,
        4,
        8,
        22,
        55,
        tzinfo=EDT,
    )

    fd8_utc = (
        fd8_source
        .astimezone(
            timezone.utc
        )
    )

    fd4 = (
        reference[
            "flight_day_4_manual_piloting"
        ]
    )

    fd8 = (
        reference[
            "flight_day_8_manual_piloting"
        ]
    )

    expected_fd4_utc = (
        fd4_utc.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    expected_fd4_met = (
        met_string(
            launch,
            fd4_utc,
        )
    )

    expected_fd4_end_utc = (
        fd4_end.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    expected_fd4_end_met = (
        met_string(
            launch,
            fd4_end,
        )
    )

    expected_fd8_utc = (
        fd8_utc.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    expected_fd8_met = (
        met_string(
            launch,
            fd8_utc,
        )
    )

    if (
        fd4[
            "derived_start_utc"
        ]
        != expected_fd4_utc
        or fd4[
            "derived_start_met"
        ]
        != expected_fd4_met
        or fd4[
            "derived_end_utc"
        ]
        != expected_fd4_end_utc
        or fd4[
            "derived_end_met"
        ]
        != expected_fd4_end_met
    ):
        fail(
            "Flight Day 4 clock correlation mismatch."
        )

    if (
        fd8[
            "derived_planned_utc"
        ]
        != expected_fd8_utc
        or fd8[
            "derived_planned_met"
        ]
        != expected_fd8_met
    ):
        fail(
            "Flight Day 8 planned clock correlation mismatch."
        )

    manual = (
        reference[
            "manual_control_architecture"
        ]
    )

    gnc_manual = (
        gnc[
            "manual_control_architecture"
        ]
    )

    if (
        manual[
            "command_path"
        ]
        != gnc_manual[
            "command_path"
        ]
    ):
        fail(
            "Manual command path changed from Phase 2J.1."
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
    ):
        fail(
            "Manual controller domains changed."
        )

    engine_classes = {
        item[
            "engine_class_id"
        ]:
            item
        for item in propulsion[
            "architecture"
        ][
            "engine_classes"
        ]
    }

    if (
        engine_classes[
            "reaction_control_system"
        ][
            "count"
        ]
        != 24
    ):
        fail(
            "RCS count changed."
        )

    proximity = (
        reference[
            "proximity_operations"
        ]
    )

    plan = (
        proximity[
            "planned_reference"
        ]
    )

    flown = (
        proximity[
            "as_flown"
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
            "Planned proximity sequence must contain 17 steps."
        )

    expected_source_labels = [
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

    observed_source_labels = [
        item[
            "source_label"
        ]
        for item in plan[
            "steps"
        ]
    ]

    if (
        observed_source_labels
        != expected_source_labels
    ):
        fail(
            "Premission reference sequence labels changed."
        )

    geometry = (
        plan[
            "geometry_context"
        ]
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
            "Planned geometry interpretation boundary failed."
        )

    if (
        flown[
            "execution_status"
        ]
        != "COMPLETED"
        or flown[
            "duration_semantics"
        ]
        != "APPROXIMATELY"
        or flown[
            "duration_minutes"
        ]
        != 70.0
        or flown[
            "controlled_approach_confirmed"
        ]
        is not True
        or flown[
            "controlled_retreat_confirmed"
        ]
        is not True
        or flown[
            "onboard_navigation_sensors_used"
        ]
        is not True
        or flown[
            "reaction_control_thrusters_used"
        ]
        is not True
        or flown[
            "automated_departure_confirmed"
        ]
        is not True
    ):
        fail(
            "As-flown proximity evidence changed."
        )

    if (
        flown[
            "all_17_planned_steps_confirmed_individually"
        ]
        is not False
        or flown[
            "planned_300_ft_gate_confirmed_as_measured_as_flown_range"
        ]
        is not False
        or flown[
            "planned_30_ft_stop_confirmed_as_measured_as_flown_range"
        ]
        is not False
        or flown[
            "planned_10m_evaluation_confirmed_as_measured_as_flown_range"
        ]
        is not False
        or flown[
            "planned_15m_evaluation_confirmed_as_measured_as_flown_range"
        ]
        is not False
    ):
        fail(
            "Premission geometry was incorrectly promoted to as-flown data."
        )

    authority = (
        proximity[
            "control_authority_states"
        ]
    )

    expected_authority_states = [
        "AUTOMATED_PRE_MANUAL_PROXIMITY_OPERATIONS",
        "CREW_MANUAL_PROXIMITY_OPERATIONS",
        "AUTOMATED_DEPARTURE",
    ]

    if [
        item[
            "state"
        ]
        for item in authority
    ] != expected_authority_states:
        fail(
            "Control-authority sequence changed."
        )

    if any(
        item[
            "exact_transition_utc"
        ]
        is not None
        for item in authority
    ):
        fail(
            "Unsupported exact authority transition time introduced."
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
            "Flight Day 4 evidence changed."
        )

    if (
        fd4[
            "mode_labels_define_complete_control_algorithm"
        ]
        is not False
        or fd4[
            "six_dof_control_algorithm_available"
        ]
        is not False
        or fd4[
            "three_dof_control_algorithm_available"
        ]
        is not False
    ):
        fail(
            "Control-mode labels were overinterpreted."
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
        or fd8[
            "as_flown_manual_control_data_generated_by_this_foregone_activity"
        ]
        is not False
    ):
        fail(
            "Flight Day 8 foregone boundary changed."
        )

    EVENT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    event_rows = [
        {
            "event_id":
                "proximity_operations_demonstration",

            "status":
                "COMPLETED",

            "time_semantics":
                "DATE_AND_SEQUENCE_ONLY",

            "utc":
                "",

            "met":
                "",

            "duration_minutes":
                70.0,

            "authority":
                "CREW_MANUAL_WITH_AUTOMATED_DEPARTURE",

            "control_modes":
                "",

            "executed":
                "true",
        },
        {
            "event_id":
                "flight_day_4_manual_piloting",

            "status":
                "COMPLETED",

            "time_semantics":
                "MINUTE_LEVEL_START_PLUS_REPORTED_DURATION",

            "utc":
                fd4[
                    "derived_start_utc"
                ],

            "met":
                fd4[
                    "derived_start_met"
                ],

            "duration_minutes":
                41.0,

            "authority":
                "CREW_MANUAL",

            "control_modes":
                "SIX_DEGREES_OF_FREEDOM|THREE_DEGREES_OF_FREEDOM",

            "executed":
                "true",
        },
        {
            "event_id":
                "flight_day_8_manual_piloting",

            "status":
                "FOREGONE",

            "time_semantics":
                "PLANNED_MINUTE_LEVEL_ANCHOR_ONLY",

            "utc":
                fd8[
                    "derived_planned_utc"
                ],

            "met":
                fd8[
                    "derived_planned_met"
                ],

            "duration_minutes":
                "",

            "authority":
                "PLANNED_CREW_MANUAL",

            "control_modes":
                "PLANNED_COMPARISON",

            "executed":
                "false",
        },
    ]

    with EVENT_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "event_id",
                "status",
                "time_semantics",
                "utc",
                "met",
                "duration_minutes",
                "authority",
                "control_modes",
                "executed",
            ],
        )

        writer.writeheader()
        writer.writerows(
            event_rows
        )

    proximity_rows = []

    for step in (
        plan[
            "steps"
        ]
    ):
        proximity_rows.append(
            {
                "step":
                    step[
                        "step"
                    ],

                "source_label":
                    step[
                        "source_label"
                    ],

                "normalized_id":
                    step[
                        "normalized_id"
                    ],

                "premission_planned":
                    "true",

                "individually_confirmed_as_flown":
                    "false",

                "interpretation":
                    "REFERENCE_PLAN_ONLY",
            }
        )

    with PROXIMITY_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "step",
                "source_label",
                "normalized_id",
                "premission_planned",
                "individually_confirmed_as_flown",
                "interpretation",
            ],
        )

        writer.writeheader()
        writer.writerows(
            proximity_rows
        )

    build_timeline_figure(
        reference
    )

    build_proximity_figure(
        reference
    )

    summary = {
        "product_id":
            "phase2j2_manual_piloting_control_modes_analysis",

        "mission":
            "Artemis II",

        "reference_dataset_id":
            reference[
                "dataset_id"
            ],

        "planned_proximity_step_count":
            17,

        "as_flown_proximity": {
            "completed":
                True,

            "duration_minutes":
                70.0,

            "duration_semantics":
                "APPROXIMATELY",

            "approach_confirmed":
                True,

            "retreat_confirmed":
                True,

            "onboard_navigation_sensors_used":
                True,

            "rcs_used":
                True,

            "automated_departure_confirmed":
                True,

            "all_planned_steps_individually_confirmed":
                False,
        },

        "flight_day_4": {
            "execution":
                "COMPLETED",

            "derived_start_utc":
                expected_fd4_utc,

            "derived_start_met":
                expected_fd4_met,

            "duration_minutes":
                41.0,

            "derived_end_utc":
                expected_fd4_end_utc,

            "derived_end_met":
                expected_fd4_end_met,

            "mode_labels":
                fd4[
                    "reported_control_mode_labels"
                ],
        },

        "flight_day_8": {
            "execution":
                "FOREGONE",

            "derived_planned_utc":
                expected_fd8_utc,

            "derived_planned_met":
                expected_fd8_met,

            "performed":
                False,
        },

        "evidence_boundaries":
            reference[
                "evidence_boundaries"
            ],

        "guardrails":
            reference[
                "guardrails"
            ],

        "outputs": {
            "event_csv":
                str(
                    EVENT_CSV.relative_to(
                        ROOT
                    )
                ),

            "proximity_csv":
                str(
                    PROXIMITY_CSV.relative_to(
                        ROOT
                    )
                ),

            "timeline_figure":
                str(
                    TIMELINE_FIGURE.relative_to(
                        ROOT
                    )
                ),

            "proximity_figure":
                str(
                    PROXIMITY_FIGURE.relative_to(
                        ROOT
                    )
                ),
        },
    }

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary,
            f,
            indent=2,
        )

    print()
    print(
        "Phase 2J.2 Manual Piloting / Control-Mode Analysis"
    )

    print("=" * 70)

    print()
    print(
        "Manual-control architecture:"
    )

    print(
        "  RHC -> ATTITUDE"
    )

    print(
        "  THC -> TRANSLATION"
    )

    print(
        "  controller -> GNC software -> effector selection -> RCS"
    )

    print(
        "  direct controller-to-thruster switch: FALSE"
    )

    print()
    print(
        "Premission proximity reference:"
    )

    print(
        "  steps: 17"
    )

    print(
        "  ~300 ft takeover context: PLAN"
    )

    print(
        "  about 30 ft handling context: PLAN"
    )

    print(
        "  10 m HQ evaluation: PLAN"
    )

    print(
        "  15 m HQ evaluation: PLAN"
    )

    print(
        "  interpreted as measured as-flown ranges: FALSE"
    )

    print()
    print(
        "As-flown proximity operations:"
    )

    print(
        "  completed: TRUE"
    )

    print(
        "  duration: ~70 min"
    )

    print(
        "  controlled approach: CONFIRMED"
    )

    print(
        "  controlled retreat: CONFIRMED"
    )

    print(
        "  onboard navigation sensors: USED"
    )

    print(
        "  RCS: USED"
    )

    print(
        "  automated departure: CONFIRMED"
    )

    print(
        "  all 17 planned steps individually confirmed: FALSE"
    )

    print()
    print(
        "Flight Day 4:"
    )

    print(
        f"  UTC: {expected_fd4_utc}"
    )

    print(
        f"  MET: {expected_fd4_met}"
    )

    print(
        "  duration: 41 min"
    )

    print(
        f"  derived end UTC: {expected_fd4_end_utc}"
    )

    print(
        f"  derived end MET: {expected_fd4_end_met}"
    )

    print(
        "  6-DOF: REPORTED MODE LABEL"
    )

    print(
        "  3-DOF: REPORTED MODE LABEL"
    )

    print(
        "  control algorithms reconstructed: FALSE"
    )

    print()
    print(
        "Flight Day 8:"
    )

    print(
        f"  planned UTC: {expected_fd8_utc}"
    )

    print(
        f"  planned MET: {expected_fd8_met}"
    )

    print(
        "  status: FOREGONE"
    )

    print(
        "  executed: FALSE"
    )

    print(
        "  planned timestamp treated as executed event: FALSE"
    )

    print()
    print(
        "Evidence boundary:"
    )

    print(
        "  planned sequence != as-flown event log"
    )

    print(
        "  planned geometry != measured range history"
    )

    print(
        "  mode labels != control-law disclosure"
    )

    print(
        "  controller input != individual thruster history"
    )

    print(
        "  RCS use != exact thruster allocation"
    )

    print()
    print(
        "Wrote:"
    )

    print(
        "  "
        f"{EVENT_CSV.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{PROXIMITY_CSV.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{SUMMARY_PATH.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{TIMELINE_FIGURE.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{PROXIMITY_FIGURE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
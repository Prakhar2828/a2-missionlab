from __future__ import annotations

import csv
import json
import math
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_trajectory_correlation.json"
)

MISSION_CONFIG_PATH = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

MANEUVER_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_plan_execution.json"
)

PROPULSION_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_esm_propulsion_architecture.json"
)

TRAJECTORY_EVENTS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "trajectory_events.json"
)

MISSION_PHASE_PATH = (
    ROOT
    / "data"
    / "processed"
    / "trajectory"
    / "mission_phase_summary.json"
)

ENTRY_EVENTS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_events.json"
)

COMMUNICATIONS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_event_catalog.json"
)

MANIFEST_PATH = (
    ROOT
    / "data"
    / "processed"
    / "trajectory"
    / "manifest.json"
)

MISSION_CLOCK_CSV = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "maneuver_mission_clock_correlation.csv"
)

OEM_BRACKET_CSV = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "maneuver_oem_solution_brackets.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "maneuver_trajectory_correlation_summary.json"
)

MISSION_CLOCK_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "maneuvers"
    / "phase2i3_maneuver_mission_clock.svg"
)

OEM_BRACKET_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "maneuvers"
    / "phase2i3_oem_solution_brackets.svg"
)

plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}

BURN_IDS = [
    "otc3",
    "rtc1",
    "rtc2",
    "rtc3",
]


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path):
    if not path.exists():
        fail(
            f"Missing required file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt.astimezone(
        timezone.utc
    )


def normalize_utc(value: datetime) -> str:
    return (
        value.astimezone(
            timezone.utc
        )
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


def magnitude(vector) -> float:
    return math.sqrt(
        sum(
            component * component
            for component in vector
        )
    )


def format_met(
    timestamp: datetime,
    launch: datetime,
) -> str:
    seconds = (
        timestamp - launch
    ).total_seconds()

    days = int(
        seconds // 86400
    )

    seconds -= (
        days * 86400
    )

    hours = int(
        seconds // 3600
    )

    seconds -= (
        hours * 3600
    )

    minutes = int(
        seconds // 60
    )

    seconds -= (
        minutes * 60
    )

    return (
        f"{days:02d}:"
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:06.3f}"
    )


def classify_phase(
    timestamp: datetime,
    soi_entry: datetime,
    pericynthion: datetime,
    soi_exit: datetime,
) -> str:
    if timestamp < soi_entry:
        return "OUTBOUND_TRANSIT"

    if timestamp <= pericynthion:
        return "LUNAR_APPROACH"

    if timestamp <= soi_exit:
        return "LUNAR_DEPARTURE"

    return "TRANS_EARTH_RETURN"


def state_from_row(row):
    position = [
        float(
            row["x_km"]
        ),
        float(
            row["y_km"]
        ),
        float(
            row["z_km"]
        ),
    ]

    velocity = [
        float(
            row["vx_km_s"]
        ),
        float(
            row["vy_km_s"]
        ),
        float(
            row["vz_km_s"]
        ),
    ]

    return (
        position,
        velocity,
    )


def load_product(path: Path):
    if not path.exists():
        fail(
            f"Missing OEM product: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        rows = list(
            csv.DictReader(f)
        )

    if not rows:
        fail(
            f"Empty OEM product: {path}"
        )

    times = [
        parse_utc(
            row[
                "timestamp_utc"
            ]
        )
        for row in rows
    ]

    return (
        rows,
        times,
    )


def interpolate_state(
    rows,
    times,
    target_time,
):
    if (
        target_time < times[0]
        or target_time > times[-1]
    ):
        return None

    index = bisect_right(
        times,
        target_time,
    )

    if index == 0:
        return state_from_row(
            rows[0]
        )

    if index >= len(rows):
        return state_from_row(
            rows[-1]
        )

    row0 = rows[
        index - 1
    ]

    row1 = rows[
        index
    ]

    t0 = times[
        index - 1
    ]

    t1 = times[
        index
    ]

    if target_time == t0:
        return state_from_row(
            row0
        )

    if target_time == t1:
        return state_from_row(
            row1
        )

    interval_seconds = (
        t1 - t0
    ).total_seconds()

    if interval_seconds <= 0:
        fail(
            "Invalid OEM interpolation interval."
        )

    u = (
        target_time - t0
    ).total_seconds() / interval_seconds

    p0, v0 = state_from_row(
        row0
    )

    p1, v1 = state_from_row(
        row1
    )

    h00 = (
        2 * u**3
        - 3 * u**2
        + 1
    )

    h10 = (
        u**3
        - 2 * u**2
        + u
    )

    h01 = (
        -2 * u**3
        + 3 * u**2
    )

    h11 = (
        u**3
        - u**2
    )

    position = [
        (
            h00 * p0[i]
            + h10
            * interval_seconds
            * v0[i]
            + h01 * p1[i]
            + h11
            * interval_seconds
            * v1[i]
        )
        for i in range(3)
    ]

    dh00 = (
        6 * u**2
        - 6 * u
    )

    dh10 = (
        3 * u**2
        - 4 * u
        + 1
    )

    dh01 = (
        -6 * u**2
        + 6 * u
    )

    dh11 = (
        3 * u**2
        - 2 * u
    )

    velocity = [
        (
            dh00 * p0[i]
            + dh10
            * interval_seconds
            * v0[i]
            + dh01 * p1[i]
            + dh11
            * interval_seconds
            * v1[i]
        )
        / interval_seconds
        for i in range(3)
    ]

    return (
        position,
        velocity,
    )


def normalize_svg(path: Path) -> None:
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


def filename_semantics(name: str):
    upper = (
        name
        .upper()
        .replace(
            "-",
            "_",
        )
    )

    result = []

    if "PRE_OTC3" in upper:
        result.append(
            "PRE_OTC3"
        )

    if "PRE_LUNAR_FLYBY" in upper:
        result.append(
            "PRE_LUNAR_FLYBY"
        )

    if "POST_ICPS_SEP" in upper:
        result.append(
            "POST_ICPS_SEP"
        )

    if "TO_EI" in upper:
        result.append(
            "TO_EI"
        )

    return result


def build_mission_clock_figure(
    launch,
    mission_anchors,
    maneuver_rows,
):
    MISSION_CLOCK_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(15, 7)
    )

    def days_since_launch(value):
        return (
            parse_utc(value)
            - launch
        ).total_seconds() / 86400.0

    burn_x = [
        days_since_launch(
            row[
                "timestamp_utc"
            ]
        )
        for row in maneuver_rows
    ]

    burn_y = [
        1.0
        for _ in maneuver_rows
    ]

    ax.scatter(
        burn_x,
        burn_y,
        s=80,
        zorder=4,
    )

    for x, row in zip(
        burn_x,
        maneuver_rows,
    ):
        ax.text(
            x,
            1.08,
            row[
                "maneuver_id"
            ].upper(),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

        ax.text(
            x,
            0.91,
            row[
                "met_anchor"
            ],
            ha="center",
            va="top",
            fontsize=7,
            rotation=35,
        )

    context = [
        (
            "SOI Entry",
            mission_anchors[
                "lunar_soi_entry"
            ][
                "timestamp_utc"
            ],
        ),
        (
            "Pericynthion",
            mission_anchors[
                "pericynthion"
            ][
                "timestamp_utc"
            ],
        ),
        (
            "SOI Exit",
            mission_anchors[
                "lunar_soi_exit"
            ][
                "timestamp_utc"
            ],
        ),
        (
            "Entry Interface",
            mission_anchors[
                "entry_interface"
            ][
                "timestamp_utc"
            ],
        ),
        (
            "Splashdown",
            mission_anchors[
                "splashdown"
            ][
                "timestamp_utc"
            ],
        ),
    ]

    for label, timestamp in context:
        x = days_since_launch(
            timestamp
        )

        ax.axvline(
            x,
            linestyle="--",
            linewidth=1,
        )

        ax.text(
            x,
            1.34,
            label,
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=90,
        )

    ax.axhline(
        1.0,
        linewidth=1,
    )

    ax.set_ylim(
        0.55,
        1.75,
    )

    ax.set_yticks(
        []
    )

    ax.set_xlabel(
        "Mission elapsed days from configured launch epoch"
    )

    ax.set_title(
        "Artemis II Maneuver Mission-Clock Correlation"
    )

    ax.text(
        0.5,
        0.04,
        (
            "Correction-burn and entry-event timestamps are "
            "public minute-level anchors where noted. "
            "Derived lunar geometry retains MissionLab provenance."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        MISSION_CLOCK_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        MISSION_CLOCK_FIGURE
    )


def build_oem_figure(
    bracket_rows,
):
    OEM_BRACKET_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    table_rows = []

    for row in bracket_rows:
        before = (
            row[
                "latest_created_at_or_before_product"
            ]
            or "NONE"
        )

        after = (
            row[
                "earliest_created_after_product"
            ]
            or "NONE"
        )

        position = (
            f"{row['position_difference_km']:.6f}"
            if row[
                "position_difference_km"
            ]
            is not None
            else "N/A"
        )

        velocity = (
            f"{row['velocity_difference_m_s']:.6f}"
            if row[
                "velocity_difference_m_s"
            ]
            is not None
            else "N/A"
        )

        table_rows.append(
            [
                row[
                    "maneuver_id"
                ].upper(),
                before,
                after,
                position,
                velocity,
                "NOT ESTABLISHED",
            ]
        )

    columns = [
        "Maneuver",
        "Latest OEM created at/before",
        "Earliest OEM created after",
        "Δ position at common epoch (km)",
        "Δ velocity at common epoch (m/s)",
        "Maneuver assimilation",
    ]

    fig, ax = plt.subplots(
        figsize=(18, 8)
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        "Artemis II Public OEM Creation-Time Brackets",
        fontsize=15,
        pad=20,
    )

    table = ax.table(
        cellText=table_rows,
        colLabels=columns,
        loc="center",
        cellLoc="center",
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        7.4
    )

    table.scale(
        1.0,
        2.1,
    )

    ax.text(
        0.5,
        0.08,
        (
            "Creation-time bracket ≠ maneuver-assimilation bracket. "
            "Same-epoch OEM differences are solution-to-solution only."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
    )

    ax.text(
        0.5,
        0.035,
        (
            "They are not navigation error, raw telemetry, "
            "or measured burn Δv."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
    )

    fig.tight_layout()

    fig.savefig(
        OEM_BRACKET_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        OEM_BRACKET_FIGURE
    )


def main():
    reference = load_json(
        REFERENCE_PATH
    )

    mission_config = load_json(
        MISSION_CONFIG_PATH
    )

    maneuver_reference = load_json(
        MANEUVER_PATH
    )

    propulsion_reference = load_json(
        PROPULSION_PATH
    )

    trajectory_events = load_json(
        TRAJECTORY_EVENTS_PATH
    )

    mission_phase = load_json(
        MISSION_PHASE_PATH
    )

    entry_reference = load_json(
        ENTRY_EVENTS_PATH
    )

    communications = load_json(
        COMMUNICATIONS_PATH
    )

    manifest = load_json(
        MANIFEST_PATH
    )

    if (
        reference.get(
            "dataset_id"
        )
        != (
            "phase2i3_artemis_ii_"
            "maneuver_trajectory_correlation"
        )
    ):
        fail(
            "Unexpected Phase 2I.3 dataset ID."
        )

    if (
        maneuver_reference.get(
            "dataset_id"
        )
        != (
            "phase2i1_artemis_ii_"
            "maneuver_plan_execution"
        )
    ):
        fail(
            "Unexpected Phase 2I.1 dataset ID."
        )

    if (
        propulsion_reference.get(
            "dataset_id"
        )
        != (
            "phase2i2_artemis_ii_"
            "esm_propulsion_architecture"
        )
    ):
        fail(
            "Unexpected Phase 2I.2 dataset ID."
        )

    launch = parse_utc(
        mission_config[
            "launch_epoch_utc"
        ]
    )

    anchors = (
        reference[
            "mission_anchors"
        ]
    )

    soi_entry = parse_utc(
        mission_phase[
            "lunar_soi"
        ][
            "derived_entry_utc"
        ]
    )

    pericynthion = parse_utc(
        mission_phase[
            "pericynthion"
        ][
            "timestamp_utc"
        ]
    )

    soi_exit = parse_utc(
        mission_phase[
            "lunar_soi"
        ][
            "derived_exit_utc"
        ]
    )

    entry_events = {
        event[
            "event_id"
        ]:
            event
        for event in entry_reference[
            "events"
        ]
    }

    entry_interface = parse_utc(
        entry_events[
            "entry_interface"
        ][
            "reported_utc_minute"
        ]
    )

    splashdown = parse_utc(
        entry_events[
            "splashdown"
        ][
            "reported_utc_minute"
        ]
    )

    anchor_cross_checks = {
        "lunar_soi_entry":
            soi_entry,

        "pericynthion":
            pericynthion,

        "lunar_soi_exit":
            soi_exit,

        "entry_interface":
            entry_interface,

        "splashdown":
            splashdown,
    }

    for key, observed in (
        anchor_cross_checks.items()
    ):
        expected = parse_utc(
            anchors[
                key
            ][
                "timestamp_utc"
            ]
        )

        if observed != expected:
            fail(
                f"{key} anchor changed."
            )

    communication_events = {
        event[
            "id"
        ]:
            event
        for event in communications[
            "events"
        ]
    }

    loss = (
        communication_events[
            "unexpected_return_link_loss"
        ]
    )

    if (
        loss[
            "precision"
        ]
        != "APPROXIMATE"
        or loss[
            "anchor_is_not_exact"
        ]
        is not True
    ):
        fail(
            "RTC2 return-link anchor semantics changed."
        )

    loss_anchor = parse_utc(
        loss[
            "approximate_anchor_utc"
        ]
    )

    reference_loss_anchor = parse_utc(
        anchors[
            "rtc2_return_link_loss_reference_anchor"
        ][
            "timestamp_utc"
        ]
    )

    if (
        loss_anchor
        != reference_loss_anchor
    ):
        fail(
            "RTC2 return-link anchor changed."
        )

    maneuvers = {
        item[
            "maneuver_id"
        ]:
            item
        for item in maneuver_reference[
            "maneuvers"
        ]
    }

    trajectory = {
        item[
            "id"
        ]:
            item
        for item in trajectory_events
    }

    assignments = {
        item[
            "maneuver_id"
        ]:
            item
        for item in propulsion_reference[
            "correction_burn_assignments"
        ]
    }

    reference_correlations = {
        item[
            "maneuver_id"
        ]:
            item
        for item in reference[
            "maneuver_correlations"
        ]
    }

    maneuver_rows = []

    burn_times = {}

    for maneuver_id in BURN_IDS:
        execution = (
            maneuvers[
                maneuver_id
            ][
                "execution"
            ]
        )

        timestamp = parse_utc(
            execution[
                "timestamp_utc"
            ]
        )

        burn_times[
            maneuver_id
        ] = timestamp

        if (
            trajectory[
                maneuver_id
            ][
                "timestamp_utc"
            ]
            != execution[
                "timestamp_utc"
            ]
        ):
            fail(
                f"{maneuver_id} Phase 1 / 2I.1 "
                "timestamp mismatch."
            )

        assignment = (
            assignments[
                maneuver_id
            ]
        )

        if (
            assignment[
                "assignment_status"
            ]
            != "UNRESOLVED_AS_FLOWN"
            or assignment[
                "as_flown_engine_class_id"
            ]
            is not None
        ):
            fail(
                f"{maneuver_id} engine assignment "
                "unexpectedly resolved."
            )

        mission_phase_name = classify_phase(
            timestamp,
            soi_entry,
            pericynthion,
            soi_exit,
        )

        met_anchor = format_met(
            timestamp,
            launch,
        )

        expected = (
            reference_correlations[
                maneuver_id
            ]
        )

        if (
            execution[
                "timestamp_utc"
            ]
            != expected[
                "timestamp_utc"
            ]
        ):
            fail(
                f"{maneuver_id} reference timestamp changed."
            )

        if (
            execution[
                "timestamp_precision"
            ]
            != "MINUTE_LEVEL"
        ):
            fail(
                f"{maneuver_id} source precision changed."
            )

        if (
            met_anchor
            != expected[
                "met_anchor"
            ]
        ):
            fail(
                f"{maneuver_id} MET anchor changed."
            )

        if (
            mission_phase_name
            != expected[
                "geometric_mission_phase"
            ]
        ):
            fail(
                f"{maneuver_id} mission phase changed."
            )

        maneuver_rows.append(
            {
                "maneuver_id":
                    maneuver_id,

                "timestamp_utc":
                    execution[
                        "timestamp_utc"
                    ],

                "timestamp_precision":
                    execution[
                        "timestamp_precision"
                    ],

                "met_anchor":
                    met_anchor,

                "geometric_mission_phase":
                    mission_phase_name,

                "duration_seconds":
                    float(
                        execution[
                            "duration_seconds"
                        ]
                    ),

                "reported_delta_v_ft_s":
                    execution.get(
                        "reported_delta_v_ft_s"
                    ),

                "engine_assignment_status":
                    "UNRESOLVED_AS_FLOWN",
            }
        )

    intervals = {
        "otc3_to_lunar_soi_entry":
            (
                soi_entry
                - burn_times[
                    "otc3"
                ]
            ).total_seconds(),

        "otc3_to_pericynthion":
            (
                pericynthion
                - burn_times[
                    "otc3"
                ]
            ).total_seconds(),

        "lunar_soi_exit_to_rtc1":
            (
                burn_times[
                    "rtc1"
                ]
                - soi_exit
            ).total_seconds(),

        "rtc1_to_rtc2":
            (
                burn_times[
                    "rtc2"
                ]
                - burn_times[
                    "rtc1"
                ]
            ).total_seconds(),

        "rtc2_to_rtc3":
            (
                burn_times[
                    "rtc3"
                ]
                - burn_times[
                    "rtc2"
                ]
            ).total_seconds(),

        "rtc3_to_entry_interface":
            (
                entry_interface
                - burn_times[
                    "rtc3"
                ]
            ).total_seconds(),

        "rtc3_to_splashdown":
            (
                splashdown
                - burn_times[
                    "rtc3"
                ]
            ).total_seconds(),

        "rtc2_loss_anchor_to_rtc2":
            (
                burn_times[
                    "rtc2"
                ]
                - loss_anchor
            ).total_seconds(),
    }

    expected_intervals = {
        "otc3_to_lunar_soi_entry":
            5707.532302,

        "otc3_to_pericynthion":
            71866.177998,

        "lunar_soi_exit_to_rtc1":
            23958.077789,

        "rtc1_to_rtc2":
            183000.0,

        "rtc2_to_rtc3":
            57600.0,

        "rtc3_to_entry_interface":
            18000.0,

        "rtc3_to_splashdown":
            18840.0,

        "rtc2_loss_anchor_to_rtc2":
            7200.0,
    }

    for key, expected in (
        expected_intervals.items()
    ):
        if abs(
            intervals[
                key
            ]
            - expected
        ) > 1e-6:
            fail(
                f"{key} changed."
            )

    products = []

    for item in manifest:
        product_path = Path(
            item[
                "output_csv"
            ]
        )

        if not product_path.is_absolute():
            product_path = (
                ROOT
                / product_path
            )

        metadata_path = Path(
            item[
                "metadata_file"
            ]
        )

        if not metadata_path.is_absolute():
            metadata_path = (
                ROOT
                / metadata_path
            )

        metadata = load_json(
            metadata_path
        )

        rows, times = load_product(
            product_path
        )

        products.append(
            {
                "name":
                    product_path.name,

                "creation_time":
                    parse_utc(
                        metadata[
                            "CREATION_DATE"
                        ]
                    ),

                "metadata":
                    metadata,

                "rows":
                    rows,

                "times":
                    times,

                "coverage_start":
                    times[0],

                "coverage_stop":
                    times[-1],
            }
        )

    products.sort(
        key=lambda item:
            item[
                "creation_time"
            ]
    )

    if len(
        products
    ) != 9:
        fail(
            "Expected nine standard OEM products."
        )

    reference_brackets = {
        item[
            "maneuver_id"
        ]:
            item
        for item in reference[
            "oem_creation_time_brackets"
        ]
    }

    bracket_rows = []

    for maneuver_id in BURN_IDS:
        burn_time = (
            burn_times[
                maneuver_id
            ]
        )

        covering = [
            product
            for product in products
            if (
                product[
                    "coverage_start"
                ]
                <= burn_time
                <= product[
                    "coverage_stop"
                ]
            )
        ]

        before = [
            product
            for product in covering
            if (
                product[
                    "creation_time"
                ]
                <= burn_time
            )
        ]

        after = [
            product
            for product in covering
            if (
                product[
                    "creation_time"
                ]
                > burn_time
            )
        ]

        latest_before = (
            max(
                before,
                key=lambda product:
                    product[
                        "creation_time"
                    ],
            )
            if before
            else None
        )

        earliest_after = (
            min(
                after,
                key=lambda product:
                    product[
                        "creation_time"
                    ],
            )
            if after
            else None
        )

        position_difference = None
        velocity_difference = None

        if (
            latest_before is not None
            and earliest_after is not None
        ):
            state_before = interpolate_state(
                latest_before[
                    "rows"
                ],
                latest_before[
                    "times"
                ],
                burn_time,
            )

            state_after = interpolate_state(
                earliest_after[
                    "rows"
                ],
                earliest_after[
                    "times"
                ],
                burn_time,
            )

            if (
                state_before is not None
                and state_after is not None
            ):
                p0, v0 = state_before
                p1, v1 = state_after

                position_difference = magnitude(
                    [
                        p1[i] - p0[i]
                        for i in range(3)
                    ]
                )

                velocity_difference = (
                    magnitude(
                        [
                            v1[i] - v0[i]
                            for i in range(3)
                        ]
                    )
                    * 1000.0
                )

        expected = (
            reference_brackets[
                maneuver_id
            ]
        )

        expected_before = (
            expected[
                "latest_product_created_at_or_before_maneuver"
            ]
        )

        expected_after = (
            expected[
                "earliest_product_created_after_maneuver"
            ]
        )

        if latest_before is None:
            fail(
                f"{maneuver_id} has no product created "
                "at/before maneuver."
            )

        if (
            latest_before[
                "name"
            ]
            != expected_before[
                "product"
            ]
        ):
            fail(
                f"{maneuver_id} latest before product changed."
            )

        before_offset = (
            latest_before[
                "creation_time"
            ]
            - burn_time
        ).total_seconds()

        if abs(
            before_offset
            - expected_before[
                "creation_offset_from_maneuver_seconds"
            ]
        ) > 1e-6:
            fail(
                f"{maneuver_id} before-product "
                "creation offset changed."
            )

        if expected_after is None:
            if earliest_after is not None:
                fail(
                    f"{maneuver_id} unexpectedly gained "
                    "a later OEM product."
                )
        else:
            if earliest_after is None:
                fail(
                    f"{maneuver_id} lost expected "
                    "later OEM product."
                )

            if (
                earliest_after[
                    "name"
                ]
                != expected_after[
                    "product"
                ]
            ):
                fail(
                    f"{maneuver_id} earliest after "
                    "product changed."
                )

            after_offset = (
                earliest_after[
                    "creation_time"
                ]
                - burn_time
            ).total_seconds()

            if abs(
                after_offset
                - expected_after[
                    "creation_offset_from_maneuver_seconds"
                ]
            ) > 1e-6:
                fail(
                    f"{maneuver_id} after-product "
                    "creation offset changed."
                )

        expected_difference = (
            expected[
                "same_epoch_solution_difference"
            ]
        )

        if (
            expected_difference[
                "available"
            ]
            is True
        ):
            if (
                position_difference is None
                or velocity_difference is None
            ):
                fail(
                    f"{maneuver_id} expected OEM comparison "
                    "is unavailable."
                )

            if abs(
                position_difference
                - expected_difference[
                    "position_difference_km"
                ]
            ) > 5e-6:
                fail(
                    f"{maneuver_id} position difference changed."
                )

            if abs(
                velocity_difference
                - expected_difference[
                    "velocity_difference_m_s"
                ]
            ) > 5e-6:
                fail(
                    f"{maneuver_id} velocity difference changed."
                )

        else:
            if (
                position_difference is not None
                or velocity_difference is not None
            ):
                fail(
                    f"{maneuver_id} unexpectedly gained "
                    "a direct OEM comparison."
                )

        if (
            expected[
                "maneuver_assimilation_status"
            ]
            != "NOT_ESTABLISHED"
        ):
            fail(
                f"{maneuver_id} maneuver assimilation "
                "was incorrectly established."
            )

        bracket_rows.append(
            {
                "maneuver_id":
                    maneuver_id,

                "maneuver_timestamp_utc":
                    normalize_utc(
                        burn_time
                    ),

                "latest_created_at_or_before_product":
                    latest_before[
                        "name"
                    ],

                "latest_created_at_or_before_creation_utc":
                    normalize_utc(
                        latest_before[
                            "creation_time"
                        ]
                    ),

                "latest_created_at_or_before_offset_seconds":
                    before_offset,

                "latest_before_filename_semantics":
                    "|".join(
                        filename_semantics(
                            latest_before[
                                "name"
                            ]
                        )
                    ),

                "earliest_created_after_product":
                    (
                        earliest_after[
                            "name"
                        ]
                        if earliest_after
                        is not None
                        else ""
                    ),

                "earliest_created_after_creation_utc":
                    (
                        normalize_utc(
                            earliest_after[
                                "creation_time"
                            ]
                        )
                        if earliest_after
                        is not None
                        else ""
                    ),

                "earliest_created_after_offset_seconds":
                    (
                        (
                            earliest_after[
                                "creation_time"
                            ]
                            - burn_time
                        ).total_seconds()
                        if earliest_after
                        is not None
                        else ""
                    ),

                "earliest_after_filename_semantics":
                    (
                        "|".join(
                            filename_semantics(
                                earliest_after[
                                    "name"
                                ]
                            )
                        )
                        if earliest_after
                        is not None
                        else ""
                    ),

                "position_difference_km":
                    position_difference,

                "velocity_difference_m_s":
                    velocity_difference,

                "comparison_semantics":
                    (
                        "SOLUTION_TO_SOLUTION_DIFFERENCE_"
                        "AT_COMMON_MANEUVER_EPOCH"
                        if position_difference
                        is not None
                        else "NO_LATER_PUBLIC_OEM_AVAILABLE"
                    ),

                "maneuver_assimilation_status":
                    "NOT_ESTABLISHED",

                "measured_burn_delta_v":
                    "false",

                "navigation_error":
                    "false",
            }
        )

    otc3_row = next(
        row
        for row in bracket_rows
        if row[
            "maneuver_id"
        ] == "otc3"
    )

    if (
        "PRE_OTC3"
        not in otc3_row[
            "earliest_after_filename_semantics"
        ]
    ):
        fail(
            "OTC3 metadata-audit boundary disappeared: "
            "earliest later-created product is no longer "
            "labeled PRE_OTC3."
        )

    if (
        reference[
            "oem_metadata_audit"
        ][
            "explicit_maneuver_assimilation_field_observed"
        ]
        is not False
        or reference[
            "oem_metadata_audit"
        ][
            "creation_date_establishes_maneuver_assimilation"
        ]
        is not False
    ):
        fail(
            "OEM metadata-assimilation boundary changed."
        )

    MISSION_CLOCK_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    mission_fields = [
        "maneuver_id",
        "timestamp_utc",
        "timestamp_precision",
        "met_anchor",
        "geometric_mission_phase",
        "duration_seconds",
        "reported_delta_v_ft_s",
        "engine_assignment_status",
    ]

    with MISSION_CLOCK_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=mission_fields,
        )

        writer.writeheader()
        writer.writerows(
            maneuver_rows
        )

    bracket_fields = [
        "maneuver_id",
        "maneuver_timestamp_utc",
        "latest_created_at_or_before_product",
        "latest_created_at_or_before_creation_utc",
        "latest_created_at_or_before_offset_seconds",
        "latest_before_filename_semantics",
        "earliest_created_after_product",
        "earliest_created_after_creation_utc",
        "earliest_created_after_offset_seconds",
        "earliest_after_filename_semantics",
        "position_difference_km",
        "velocity_difference_m_s",
        "comparison_semantics",
        "maneuver_assimilation_status",
        "measured_burn_delta_v",
        "navigation_error",
    ]

    with OEM_BRACKET_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=bracket_fields,
        )

        writer.writeheader()
        writer.writerows(
            bracket_rows
        )

    build_mission_clock_figure(
        launch,
        anchors,
        maneuver_rows,
    )

    build_oem_figure(
        bracket_rows
    )

    summary = {
        "product_id":
            (
                "phase2i3_maneuver_trajectory_"
                "correlation_analysis"
            ),

        "mission":
            "Artemis II",

        "reference_dataset_id":
            reference[
                "dataset_id"
            ],

        "mission_clock": {
            "launch_epoch_utc":
                mission_config[
                    "launch_epoch_utc"
                ],

            "maneuver_count":
                len(
                    maneuver_rows
                ),

            "maneuvers":
                maneuver_rows,

            "intervals_seconds":
                intervals,
        },

        "rtc2_communications_context": {
            "loss_reference_anchor_utc":
                normalize_utc(
                    loss_anchor
                ),

            "precision":
                "APPROXIMATE",

            "anchor_is_not_exact":
                True,

            "approximate_anchor_to_rtc2_seconds":
                intervals[
                    "rtc2_loss_anchor_to_rtc2"
                ],
        },

        "oem_archive": {
            "standard_product_count":
                len(
                    products
                ),

            "creation_date_establishes_maneuver_assimilation":
                False,

            "explicit_maneuver_assimilation_field_observed":
                False,
        },

        "oem_creation_time_brackets":
            bracket_rows,

        "analysis_boundary":
            reference[
                "analysis_boundary"
            ],

        "guardrails":
            reference[
                "guardrails"
            ],

        "outputs": {
            "mission_clock_csv":
                str(
                    MISSION_CLOCK_CSV.relative_to(
                        ROOT
                    )
                ),

            "oem_bracket_csv":
                str(
                    OEM_BRACKET_CSV.relative_to(
                        ROOT
                    )
                ),

            "mission_clock_figure":
                str(
                    MISSION_CLOCK_FIGURE.relative_to(
                        ROOT
                    )
                ),

            "oem_bracket_figure":
                str(
                    OEM_BRACKET_FIGURE.relative_to(
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
        "Phase 2I.3 Maneuver Mission-Clock / "
        "Trajectory-Solution Analysis"
    )

    print("=" * 72)

    print()
    print(
        "Mission-clock correlation:"
    )

    for row in maneuver_rows:
        print()
        print(
            f"  {row['maneuver_id'].upper()}:"
        )

        print(
            "    UTC:"
        )

        print(
            "      "
            f"{row['timestamp_utc']}"
        )

        print(
            "    MET anchor:"
        )

        print(
            "      "
            f"{row['met_anchor']}"
        )

        print(
            "    phase:"
        )

        print(
            "      "
            f"{row['geometric_mission_phase']}"
        )

        print(
            "    engine:"
        )

        print(
            "      UNRESOLVED_AS_FLOWN"
        )

    print()
    print(
        "Mission-event intervals:"
    )

    for key, value in intervals.items():
        prefix = (
            "~"
            if key
            == "rtc2_loss_anchor_to_rtc2"
            else ""
        )

        print(
            f"  {key}:"
        )

        print(
            f"    {prefix}{value:.6f} s"
        )

    print()
    print(
        "Public OEM archive:"
    )

    print(
        "  standard products:"
    )

    print(
        f"    {len(products)}"
    )

    print(
        "  explicit maneuver-assimilation metadata:"
    )

    print(
        "    NONE"
    )

    print(
        "  CREATION_DATE proves assimilation:"
    )

    print(
        "    FALSE"
    )

    print()
    print(
        "Creation-time OEM brackets:"
    )

    for row in bracket_rows:
        print()
        print(
            f"  {row['maneuver_id'].upper()}:"
        )

        print(
            "    latest created at/before:"
        )

        print(
            "      "
            f"{row['latest_created_at_or_before_product']}"
        )

        print(
            "    earliest created after:"
        )

        if (
            row[
                "earliest_created_after_product"
            ]
        ):
            print(
                "      "
                f"{row['earliest_created_after_product']}"
            )
        else:
            print(
                "      NONE"
            )

        print(
            "    maneuver assimilation:"
        )

        print(
            "      NOT_ESTABLISHED"
        )

        if (
            row[
                "position_difference_km"
            ]
            is not None
        ):
            print(
                "    same-epoch solution difference:"
            )

            print(
                "      position:"
            )

            print(
                "        "
                f"{row['position_difference_km']:.6f} km"
            )

            print(
                "      velocity:"
            )

            print(
                "        "
                f"{row['velocity_difference_m_s']:.6f} m/s"
            )

            print(
                "      measured burn delta-v:"
            )

            print(
                "        FALSE"
            )
        else:
            print(
                "    same-epoch solution difference:"
            )

            print(
                "      NOT AVAILABLE"
            )

    print()
    print(
        "OTC3 metadata audit:"
    )

    print(
        "  earliest later-created product:"
    )

    print(
        "    Artemis_II_OEM_2026_04_06_Pre-OTC3_to_EI.csv"
    )

    print(
        "  product label:"
    )

    print(
        "    PRE_OTC3"
    )

    print(
        "  created after reported OTC3 minute:"
    )

    print(
        "    TRUE"
    )

    print(
        "  therefore CREATION_DATE proves assimilation:"
    )

    print(
        "    FALSE"
    )

    print()
    print(
        "Analysis boundary:"
    )

    print(
        "  mission-clock correlation: ALLOWED"
    )

    print(
        "  geometric-phase correlation: ALLOWED"
    )

    print(
        "  public OEM solution evolution: ALLOWED"
    )

    print(
        "  OEM difference as navigation error: NOT ALLOWED"
    )

    print(
        "  OEM difference as measured burn delta-v: NOT ALLOWED"
    )

    print(
        "  thrust-derived burn performance: NOT ALLOWED"
    )

    print(
        "  burn impulse from nominal thrust: NOT ALLOWED"
    )

    print()
    print(
        "Wrote:"
    )

    print(
        "  "
        f"{MISSION_CLOCK_CSV.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{OEM_BRACKET_CSV.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{SUMMARY_PATH.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{MISSION_CLOCK_FIGURE.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{OEM_BRACKET_FIGURE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

CATALOG_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_event_catalog.json"
)

MISSION_PATH = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

PHASE2G_REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_events.json"
)

TRAJECTORY_EVENTS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "trajectory_events.json"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "communications_event_timeline.csv"
)

OUTPUT_SUMMARY = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "communications_event_summary.json"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "communications"
    / "phase2h1_communications_event_timeline.svg"
)

VALID_PRECISION = {
    "EXACT",
    "MINUTE_LEVEL",
    "APPROXIMATE",
    "DATE_LEVEL",
    "SEQUENCE_ONLY",
}

VALID_STATES = {
    "PLANNED",
    "OBSERVED_REPORTED",
    "REPORTED",
    "SEQUENCE_REPORTED",
}

plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path):
    if not path.exists():
        fail(
            "Missing required file:\n"
            f"{path}"
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


def iso_z(
    value: datetime,
) -> str:
    return (
        value.astimezone(
            timezone.utc
        )
        .isoformat(
            timespec="seconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def format_met(
    timestamp: datetime,
    launch_epoch: datetime,
) -> str:
    total_seconds = int(
        round(
            (
                timestamp
                - launch_epoch
            ).total_seconds()
        )
    )

    sign = ""

    if total_seconds < 0:
        sign = "-"
        total_seconds = abs(
            total_seconds
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
        f"{sign}"
        f"{days:02d}:"
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


def normalize_svg(
    path: Path,
) -> None:
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


def resolve_event_time(
    event,
):
    timestamp_text = event.get(
        "timestamp_utc"
    )

    approximate_text = event.get(
        "approximate_anchor_utc"
    )

    if timestamp_text:
        return (
            parse_utc(
                timestamp_text
            ),
            False,
            "PRIMARY_TIMESTAMP",
        )

    if approximate_text:
        return (
            parse_utc(
                approximate_text
            ),
            True,
            "APPROXIMATE_ANCHOR",
        )

    if event.get(
        "date_utc"
    ):
        return (
            None,
            False,
            "DATE_ONLY",
        )

    return (
        None,
        False,
        "SEQUENCE_ONLY",
    )


def validate_catalog(
    catalog,
) -> None:
    source_ids = {
        source["source_id"]
        for source in catalog[
            "sources"
        ]
    }

    event_ids = set()

    for event in catalog[
        "events"
    ]:
        event_id = event["id"]

        if event_id in event_ids:
            fail(
                "Duplicate event ID: "
                f"{event_id}"
            )

        event_ids.add(
            event_id
        )

        precision = event[
            "precision"
        ]

        state = event[
            "event_state"
        ]

        if precision not in (
            VALID_PRECISION
        ):
            fail(
                "Invalid precision for "
                f"{event_id}: {precision}"
            )

        if state not in (
            VALID_STATES
        ):
            fail(
                "Invalid state for "
                f"{event_id}: {state}"
            )

        if (
            event["source_id"]
            not in source_ids
        ):
            fail(
                "Unknown source ID for "
                f"{event_id}"
            )

        timestamp_text = event.get(
            "timestamp_utc"
        )

        approximate_text = event.get(
            "approximate_anchor_utc"
        )

        if precision in {
            "DATE_LEVEL",
            "SEQUENCE_ONLY",
        }:
            if timestamp_text is not None:
                fail(
                    "False timestamp precision "
                    f"for {event_id}"
                )

            if approximate_text is not None:
                fail(
                    "False approximate anchor "
                    f"for {event_id}"
                )

        if precision == "MINUTE_LEVEL":
            if timestamp_text is None:
                fail(
                    "Missing minute timestamp "
                    f"for {event_id}"
                )

            timestamp = parse_utc(
                timestamp_text
            )

            if (
                timestamp.second != 0
                or timestamp.microsecond != 0
            ):
                fail(
                    "Minute-level event contains "
                    "sub-minute precision: "
                    f"{event_id}"
                )

        if precision == "APPROXIMATE":
            if (
                approximate_text is not None
                and event.get(
                    "anchor_is_not_exact"
                )
                is not True
            ):
                fail(
                    "Approximate anchor lacks "
                    "explicit non-exact guard: "
                    f"{event_id}"
                )


def event_map(catalog):
    return {
        event["id"]:
            event
        for event in catalog[
            "events"
        ]
    }


def require_timestamp(
    events,
    event_id,
):
    event = events[
        event_id
    ]

    value = event.get(
        "timestamp_utc"
    )

    if value is None:
        fail(
            "Expected timestamp for "
            f"{event_id}"
        )

    return parse_utc(
        value
    )


def require_approximate_anchor(
    events,
    event_id,
):
    event = events[
        event_id
    ]

    value = event.get(
        "approximate_anchor_utc"
    )

    if value is None:
        fail(
            "Expected approximate anchor "
            f"for {event_id}"
        )

    return parse_utc(
        value
    )


def build_figure(
    rows,
):
    timed_rows = [
        row
        for row in rows
        if row[
            "resolved_timestamp"
        ] is not None
    ]

    FIGURE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(
            14,
            7,
        )
    )

    y_positions = {
        "GEOMETRIC_CONTEXT": 0,
        "RF": 1,
        "OPTICAL": 2,
    }

    y_labels = [
        "Geometric context",
        "RF communications",
        "Optical communications",
    ]

    for row in timed_rows:
        marker = "o"

        if row[
            "is_approximate"
        ]:
            marker = "x"

        elif (
            row[
                "event_state"
            ]
            == "PLANNED"
        ):
            marker = "s"

        y = y_positions[
            row["domain"]
        ]

        ax.scatter(
            row[
                "resolved_timestamp"
            ],
            y,
            marker=marker,
            s=55,
        )

        ax.annotate(
            row["id"],
            (
                row[
                    "resolved_timestamp"
                ],
                y,
            ),
            xytext=(
                4,
                7,
            ),
            textcoords="offset points",
            fontsize=7,
            rotation=28,
        )

    ax.set_yticks(
        [
            0,
            1,
            2,
        ]
    )

    ax.set_yticklabels(
        y_labels
    )

    ax.set_title(
        "Artemis II Operational "
        "Communications Event Timeline"
    )

    ax.set_xlabel(
        "UTC"
    )

    ax.grid(
        True,
        axis="x",
        alpha=0.25,
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(
            "%b %d\n%H:%M",
            tz=timezone.utc,
        )
    )

    ax.text(
        0.01,
        -0.20,
        (
            "Marker semantics: circle = reported; "
            "square = planned; x = approximate anchor. "
            "Date-level and sequence-only events are not "
            "placed on the time axis."
        ),
        transform=ax.transAxes,
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


def main() -> None:
    catalog = load_json(
        CATALOG_PATH
    )

    mission = load_json(
        MISSION_PATH
    )

    phase2g_reference = load_json(
        PHASE2G_REFERENCE_PATH
    )

    trajectory_events = load_json(
        TRAJECTORY_EVENTS_PATH
    )

    validate_catalog(
        catalog
    )

    launch_epoch = parse_utc(
        mission[
            "launch_epoch_utc"
        ]
    )

    events = event_map(
        catalog
    )

    rtc2_matches = [
        event
        for event in trajectory_events
        if event.get(
            "id"
        ) == "rtc2"
    ]

    if len(
        rtc2_matches
    ) != 1:
        fail(
            "Expected exactly one RTC2 event."
        )

    rtc2 = parse_utc(
        rtc2_matches[
            0
        ][
            "timestamp_utc"
        ]
    )

    phase2g_window = (
        phase2g_reference[
            "public_lunar_occultation_window"
        ]
    )

    phase2g_los = parse_utc(
        phase2g_window[
            "loss_of_signal_utc"
        ]
    )

    phase2g_aos = parse_utc(
        phase2g_window[
            "acquisition_of_signal_utc"
        ]
    )

    planned_earthset = require_timestamp(
        events,
        "lunar_earthset_planned",
    )

    reported_earthset = require_timestamp(
        events,
        "lunar_earthset_reported",
    )

    planned_blackout = require_timestamp(
        events,
        "lunar_blackout_start_planned",
    )

    reported_blackout = require_timestamp(
        events,
        "lunar_blackout_start_reported",
    )

    planned_earthrise = require_timestamp(
        events,
        "lunar_earthrise_planned",
    )

    reported_earthrise = require_timestamp(
        events,
        "lunar_earthrise_reported",
    )

    planned_aos = require_timestamp(
        events,
        "dsn_reacquisition_planned",
    )

    return_loss_anchor = (
        require_approximate_anchor(
            events,
            "unexpected_return_link_loss",
        )
    )

    if (
        planned_blackout
        != phase2g_los
    ):
        fail(
            "2H planned blackout start "
            "does not match Phase 2G LOS."
        )

    if (
        reported_blackout
        != phase2g_los
    ):
        fail(
            "2H reported blackout start "
            "does not match Phase 2G LOS."
        )

    if (
        planned_aos
        != phase2g_aos
    ):
        fail(
            "2H planned AOS does not "
            "match Phase 2G AOS."
        )

    planned_vs_reported = {
        "earthset_reported_minus_planned_seconds":
            (
                reported_earthset
                - planned_earthset
            ).total_seconds(),

        "blackout_start_reported_minus_planned_seconds":
            (
                reported_blackout
                - planned_blackout
            ).total_seconds(),

        "earthrise_reported_minus_planned_seconds":
            (
                reported_earthrise
                - planned_earthrise
            ).total_seconds(),
    }

    operational_separations = {
        "reported_earthset_to_reported_blackout_seconds":
            (
                reported_blackout
                - reported_earthset
            ).total_seconds(),

        "reported_earthrise_to_planned_aos_seconds":
            (
                planned_aos
                - reported_earthrise
            ).total_seconds(),

        "approximate_return_link_loss_anchor_to_rtc2_seconds":
            (
                rtc2
                - return_loss_anchor
            ).total_seconds(),
    }

    rows = []

    for event in catalog[
        "events"
    ]:
        (
            resolved_timestamp,
            is_approximate,
            representation,
        ) = resolve_event_time(
            event
        )

        met = ""

        if resolved_timestamp is not None:
            met = format_met(
                resolved_timestamp,
                launch_epoch,
            )

        rows.append(
            {
                **event,
                "resolved_timestamp":
                    resolved_timestamp,
                "is_approximate":
                    is_approximate,
                "time_representation":
                    representation,
                "met":
                    met,
            }
        )

    precision_counts = Counter(
        row["precision"]
        for row in rows
    )

    domain_counts = Counter(
        row["domain"]
        for row in rows
    )

    state_counts = Counter(
        row["event_state"]
        for row in rows
    )

    representation_counts = Counter(
        row[
            "time_representation"
        ]
        for row in rows
    )

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "id",
        "name",
        "domain",
        "network",
        "event_state",
        "precision",
        "time_representation",
        "timestamp_utc",
        "approximate_anchor_utc",
        "date_utc",
        "met",
        "met_is_approximate",
        "ordering",
        "source_id",
        "provenance",
    ]

    with OUTPUT_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "id":
                        row["id"],

                    "name":
                        row["name"],

                    "domain":
                        row["domain"],

                    "network":
                        row.get(
                            "network"
                        )
                        or "",

                    "event_state":
                        row[
                            "event_state"
                        ],

                    "precision":
                        row[
                            "precision"
                        ],

                    "time_representation":
                        row[
                            "time_representation"
                        ],

                    "timestamp_utc":
                        row.get(
                            "timestamp_utc"
                        )
                        or "",

                    "approximate_anchor_utc":
                        row.get(
                            "approximate_anchor_utc"
                        )
                        or "",

                    "date_utc":
                        row.get(
                            "date_utc"
                        )
                        or "",

                    "met":
                        row["met"],

                    "met_is_approximate":
                        str(
                            row[
                                "is_approximate"
                            ]
                        ).lower(),

                    "ordering":
                        row.get(
                            "ordering"
                        )
                        or "",

                    "source_id":
                        row[
                            "source_id"
                        ],

                    "provenance":
                        row[
                            "provenance"
                        ],
                }
            )

    build_figure(
        rows
    )

    summary = {
        "product_id":
            "phase2h1_communications_event_timeline",

        "mission":
            "Artemis II",

        "reference_dataset_id":
            catalog[
                "dataset_id"
            ],

        "launch_epoch_utc":
            iso_z(
                launch_epoch
            ),

        "event_count":
            len(rows),

        "precision_counts":
            dict(
                precision_counts
            ),

        "domain_counts":
            dict(
                domain_counts
            ),

        "event_state_counts":
            dict(
                state_counts
            ),

        "time_representation_counts":
            dict(
                representation_counts
            ),

        "planned_vs_reported":
            planned_vs_reported,

        "operational_separations":
            operational_separations,

        "rtc2_reference_utc":
            iso_z(
                rtc2
            ),

        "flight_day_9_return_link_loss": {
            "precision":
                "APPROXIMATE",

            "approximate_anchor_utc":
                iso_z(
                    return_loss_anchor
                ),

            "anchor_is_exact":
                False,

            "interpretation":
                (
                    "The anchor is RTC2 minus two "
                    "hours and represents NASA's "
                    "phrase 'about two hours before'; "
                    "it is not an observed timestamp."
                ),
        },

        "flight_day_6": {
            "planned_earthset_utc":
                iso_z(
                    planned_earthset
                ),

            "reported_earthset_utc":
                iso_z(
                    reported_earthset
                ),

            "planned_blackout_start_utc":
                iso_z(
                    planned_blackout
                ),

            "reported_blackout_start_utc":
                iso_z(
                    reported_blackout
                ),

            "planned_earthrise_utc":
                iso_z(
                    planned_earthrise
                ),

            "reported_earthrise_utc":
                iso_z(
                    reported_earthrise
                ),

            "planned_dsn_aos_utc":
                iso_z(
                    planned_aos
                ),

            "live_dsn_reacquisition_precision":
                "SEQUENCE_ONLY",

            "live_dsn_reacquisition_ordering":
                (
                    "MOMENTS_AFTER_"
                    "REPORTED_EARTHRISE"
                ),
        },

        "guardrails":
            catalog[
                "guardrails"
            ],

        "outputs": {
            "timeline_csv":
                str(
                    OUTPUT_CSV.relative_to(
                        ROOT
                    )
                ),

            "figure":
                str(
                    FIGURE_PATH.relative_to(
                        ROOT
                    )
                ),
        },
    }

    OUTPUT_SUMMARY.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_SUMMARY.open(
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
        "Phase 2H.1 Operational "
        "Communications Event Timeline"
    )

    print("=" * 60)

    print()
    print(
        "Catalog:"
    )

    print(
        f"  events: {len(rows)}"
    )

    print()
    print(
        "Precision counts:"
    )

    for precision in [
        "EXACT",
        "MINUTE_LEVEL",
        "APPROXIMATE",
        "DATE_LEVEL",
        "SEQUENCE_ONLY",
    ]:
        print(
            f"  {precision}: "
            f"{precision_counts.get(precision, 0)}"
        )

    print()
    print(
        "Domain counts:"
    )

    for domain in sorted(
        domain_counts
    ):
        print(
            f"  {domain}: "
            f"{domain_counts[domain]}"
        )

    print()
    print(
        "Flight Day 6 planned vs reported:"
    )

    print(
        "  Earthset reported - planned:"
    )

    print(
        "    "
        f"{planned_vs_reported['earthset_reported_minus_planned_seconds']:+.0f} s"
    )

    print(
        "  blackout reported - planned:"
    )

    print(
        "    "
        f"{planned_vs_reported['blackout_start_reported_minus_planned_seconds']:+.0f} s"
    )

    print(
        "  Earthrise reported - planned:"
    )

    print(
        "    "
        f"{planned_vs_reported['earthrise_reported_minus_planned_seconds']:+.0f} s"
    )

    print()
    print(
        "Flight Day 6 operational separations:"
    )

    print(
        "  reported Earthset -> blackout:"
    )

    print(
        "    "
        f"{operational_separations['reported_earthset_to_reported_blackout_seconds']:.0f} s"
    )

    print(
        "  reported Earthrise -> planned AOS:"
    )

    print(
        "    "
        f"{operational_separations['reported_earthrise_to_planned_aos_seconds']:.0f} s"
    )

    print()
    print(
        "Flight Day 9:"
    )

    print(
        "  RTC2:"
    )

    print(
        f"    {iso_z(rtc2)}"
    )

    print(
        "  approximate return-link LOS anchor:"
    )

    print(
        f"    ~{iso_z(return_loss_anchor)}"
    )

    print(
        "  anchor-to-RTC2 separation:"
    )

    print(
        "    ~"
        f"{operational_separations['approximate_return_link_loss_anchor_to_rtc2_seconds'] / 3600.0:.3f} h"
    )

    print()
    print(
        "Interpretation boundaries:"
    )

    print(
        "  planned != reported"
    )

    print(
        "  approximate anchor != "
        "observed timestamp"
    )

    print(
        "  date-level != timed event"
    )

    print(
        "  sequence-only != timed event"
    )

    print(
        "  Earthset/Earthrise != "
        "RF LOS/AOS"
    )

    print(
        "  O2O activity != "
        "primary RF availability"
    )

    print()
    print(
        "Wrote:"
    )

    print(
        "  "
        f"{OUTPUT_CSV.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{OUTPUT_SUMMARY.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{FIGURE_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
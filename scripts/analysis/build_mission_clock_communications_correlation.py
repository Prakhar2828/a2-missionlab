from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

MISSION_PATH = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

CATALOG_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_event_catalog.json"
)

TRAJECTORY_EVENTS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "trajectory_events.json"
)

MISSION_PHASE_SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "trajectory"
    / "mission_phase_summary.json"
)

GEOCENTRIC_SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "lunar_occultation_summary.json"
)

TOPOCENTRIC_SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "dsn_topocentric_summary.json"
)

COMM_EVENT_SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "communications_event_summary.json"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "mission_clock_communications_correlation.csv"
)

OUTPUT_SUMMARY = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "mission_clock_communications_correlation_summary.json"
)

MISSION_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "communications"
    / "phase2h2_mission_clock_correlation.svg"
)

FLYBY_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "communications"
    / "phase2h2_flyby_correlation.svg"
)

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


def iso_z_microseconds(
    value: datetime,
) -> str:
    return (
        value.astimezone(
            timezone.utc
        )
        .isoformat(
            timespec="microseconds"
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


def mission_phase(
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


def delta_seconds(
    earlier: datetime,
    later: datetime,
) -> float:
    return (
        later - earlier
    ).total_seconds()


def make_row(
    *,
    event_id: str,
    name: str,
    timestamp: datetime,
    timestamp_text: str,
    launch_epoch: datetime,
    soi_entry: datetime,
    pericynthion: datetime,
    soi_exit: datetime,
    kind: str,
    domain: str,
    provenance: str,
    precision: str,
    source_layer: str,
    approximate: bool = False,
    source_id: str = "",
    notes: str = "",
):
    return {
        "id":
            event_id,

        "name":
            name,

        "timestamp":
            timestamp,

        "timestamp_utc":
            timestamp_text,

        "met":
            format_met(
                timestamp,
                launch_epoch,
            ),

        "mission_phase":
            mission_phase(
                timestamp,
                soi_entry,
                pericynthion,
                soi_exit,
            ),

        "kind":
            kind,

        "domain":
            domain,

        "provenance":
            provenance,

        "precision":
            precision,

        "source_layer":
            source_layer,

        "is_approximate":
            approximate,

        "source_id":
            source_id,

        "notes":
            notes,
    }


def build_mission_figure(
    rows,
):
    MISSION_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    y_positions = {
        "OPTICAL": 0,
        "BURN": 1,
        "GEOMETRY": 2,
        "RF": 3,
    }

    y_labels = [
        "Optical",
        "Burns",
        "Geometry",
        "RF communications",
    ]

    fig, ax = plt.subplots(
        figsize=(15, 7.5)
    )

    for row in rows:
        marker = "o"

        if row[
            "is_approximate"
        ]:
            marker = "x"

        elif row[
            "provenance"
        ] == "NASA_PLANNED":
            marker = "s"

        y = y_positions[
            row["domain"]
        ]

        ax.scatter(
            row["timestamp"],
            y,
            marker=marker,
            s=55,
        )

        ax.annotate(
            row["name"],
            (
                row["timestamp"],
                y,
            ),
            xytext=(4, 7),
            textcoords="offset points",
            fontsize=7,
            rotation=30,
        )

    ax.set_yticks(
        [0, 1, 2, 3]
    )

    ax.set_yticklabels(
        y_labels
    )

    ax.set_title(
        "Artemis II Mission-Clock "
        "Communications Correlation"
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
        -0.21,
        (
            "circle = reported or derived event; "
            "square = planned event; "
            "x = approximate computational anchor. "
            "Sequence-only events are not assigned "
            "a time-axis position."
        ),
        transform=ax.transAxes,
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        MISSION_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(fig)

    normalize_svg(
        MISSION_FIGURE
    )


def build_flyby_figure(
    flyby_rows,
    geocentric_ingress,
    geocentric_egress,
    dss43_ingress,
    dss43_egress,
):
    FLYBY_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(15, 7)
    )

    ax.axvspan(
        geocentric_ingress,
        geocentric_egress,
        alpha=0.10,
        label="Geocentric occultation",
    )

    ax.axvspan(
        dss43_ingress,
        dss43_egress,
        alpha=0.15,
        label="DSS-43 topocentric occultation",
    )

    for index, row in enumerate(
        flyby_rows
    ):
        ax.axvline(
            row["timestamp"],
            linewidth=1.0,
            linestyle=(
                "--"
                if row[
                    "provenance"
                ] == "NASA_PLANNED"
                else "-"
            ),
        )

        ax.annotate(
            row["name"],
            (
                row["timestamp"],
                0.50,
            ),
            xytext=(
                3,
                8 + 12 * (index % 3),
            ),
            textcoords="offset points",
            fontsize=7,
            rotation=48,
            verticalalignment="bottom",
        )

    ax.set_ylim(
        0.0,
        1.0,
    )

    ax.set_yticks([])

    ax.set_title(
        "Artemis II Flight Day 6 "
        "Geometry-to-Operations Correlation"
    )

    ax.set_xlabel(
        "UTC on 2026-04-06"
    )

    ax.grid(
        True,
        axis="x",
        alpha=0.25,
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(
            "%H:%M",
            tz=timezone.utc,
        )
    )

    ax.legend(
        loc="lower center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        FLYBY_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(fig)

    normalize_svg(
        FLYBY_FIGURE
    )


def main() -> None:
    mission = load_json(
        MISSION_PATH
    )

    catalog = load_json(
        CATALOG_PATH
    )

    trajectory_events = load_json(
        TRAJECTORY_EVENTS_PATH
    )

    mission_phase_summary = load_json(
        MISSION_PHASE_SUMMARY_PATH
    )

    geocentric_summary = load_json(
        GEOCENTRIC_SUMMARY_PATH
    )

    topocentric_summary = load_json(
        TOPOCENTRIC_SUMMARY_PATH
    )

    communications_summary = load_json(
        COMM_EVENT_SUMMARY_PATH
    )

    launch_epoch = parse_utc(
        mission[
            "launch_epoch_utc"
        ]
    )

    events_by_id = {
        event["id"]:
            event
        for event in catalog[
            "events"
        ]
    }

    trajectory_by_id = {
        event["id"]:
            event
        for event in trajectory_events
    }

    if (
        communications_summary[
            "event_count"
        ]
        != 16
    ):
        fail(
            "Expected Phase 2H.1 summary "
            "to contain 16 events."
        )

    soi = (
        mission_phase_summary[
            "lunar_soi"
        ]
    )

    soi_entry = parse_utc(
        soi[
            "derived_entry_utc"
        ]
    )

    soi_exit = parse_utc(
        soi[
            "derived_exit_utc"
        ]
    )

    pericynthion_text = (
        mission_phase_summary[
            "pericynthion"
        ][
            "timestamp_utc"
        ]
    )

    pericynthion = parse_utc(
        pericynthion_text
    )

    maximum_earth_text = (
        mission_phase_summary[
            "maximum_earth_center_distance"
        ][
            "timestamp_utc"
        ]
    )

    maximum_earth_distance = parse_utc(
        maximum_earth_text
    )

    geocentric_window = (
        geocentric_summary[
            "geocentric_occultation_window"
        ]
    )

    geocentric_ingress_text = (
        geocentric_window[
            "ingress_utc"
        ]
    )

    geocentric_egress_text = (
        geocentric_window[
            "egress_utc"
        ]
    )

    geocentric_ingress = parse_utc(
        geocentric_ingress_text
    )

    geocentric_egress = parse_utc(
        geocentric_egress_text
    )

    dss43_matches = [
        result
        for result in topocentric_summary[
            "station_results"
        ]
        if result[
            "station"
        ] == "DSS-43"
    ]

    if len(
        dss43_matches
    ) != 1:
        fail(
            "Expected exactly one DSS-43 "
            "topocentric result."
        )

    dss43 = dss43_matches[0]

    dss43_ingress_text = (
        dss43[
            "ingress_utc"
        ]
    )

    dss43_egress_text = (
        dss43[
            "egress_utc"
        ]
    )

    dss43_ingress = parse_utc(
        dss43_ingress_text
    )

    dss43_egress = parse_utc(
        dss43_egress_text
    )

    required_catalog_events = [
        "o2o_100_gb_downlink_milestone",
        "lunar_earthset_reported",
        "lunar_blackout_start_reported",
        "lunar_earthrise_reported",
        "dsn_reacquisition_planned",
        "dsn_reacquisition_live_report",
        "unexpected_return_link_loss",
    ]

    for event_id in (
        required_catalog_events
    ):
        if event_id not in events_by_id:
            fail(
                "Missing catalog event: "
                f"{event_id}"
            )

    required_trajectory_events = [
        "otc3",
        "rtc1",
        "rtc2",
    ]

    for event_id in (
        required_trajectory_events
    ):
        if event_id not in trajectory_by_id:
            fail(
                "Missing trajectory event: "
                f"{event_id}"
            )

    earthset_event = (
        events_by_id[
            "lunar_earthset_reported"
        ]
    )

    blackout_event = (
        events_by_id[
            "lunar_blackout_start_reported"
        ]
    )

    earthrise_event = (
        events_by_id[
            "lunar_earthrise_reported"
        ]
    )

    aos_event = (
        events_by_id[
            "dsn_reacquisition_planned"
        ]
    )

    o2o_event = (
        events_by_id[
            "o2o_100_gb_downlink_milestone"
        ]
    )

    return_loss_event = (
        events_by_id[
            "unexpected_return_link_loss"
        ]
    )

    earthset = parse_utc(
        earthset_event[
            "timestamp_utc"
        ]
    )

    blackout = parse_utc(
        blackout_event[
            "timestamp_utc"
        ]
    )

    earthrise = parse_utc(
        earthrise_event[
            "timestamp_utc"
        ]
    )

    planned_aos = parse_utc(
        aos_event[
            "timestamp_utc"
        ]
    )

    o2o_anchor = parse_utc(
        o2o_event[
            "approximate_anchor_utc"
        ]
    )

    return_loss_anchor = parse_utc(
        return_loss_event[
            "approximate_anchor_utc"
        ]
    )

    otc_event = (
        trajectory_by_id["otc3"]
    )

    rtc1_event = (
        trajectory_by_id["rtc1"]
    )

    rtc2_event = (
        trajectory_by_id["rtc2"]
    )

    otc = parse_utc(
        otc_event[
            "timestamp_utc"
        ]
    )

    rtc1 = parse_utc(
        rtc1_event[
            "timestamp_utc"
        ]
    )

    rtc2 = parse_utc(
        rtc2_event[
            "timestamp_utc"
        ]
    )

    if not (
        o2o_anchor
        < otc
        < soi_entry
        < earthset
        < geocentric_ingress
        < dss43_ingress
        < blackout
        < pericynthion
        < maximum_earth_distance
        < geocentric_egress
        < dss43_egress
        < earthrise
        < planned_aos
        < soi_exit
        < rtc1
        < return_loss_anchor
        < rtc2
    ):
        fail(
            "Integrated mission-clock "
            "event ordering is inconsistent."
        )

    rows = [
        make_row(
            event_id=(
                "o2o_100_gb_downlink_milestone"
            ),
            name=(
                "O2O 100 GB "
                "approximate anchor"
            ),
            timestamp=o2o_anchor,
            timestamp_text=(
                o2o_event[
                    "approximate_anchor_utc"
                ]
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="OPTICAL_MILESTONE",
            domain="OPTICAL",
            provenance="NASA_REPORTED",
            precision="APPROXIMATE",
            source_layer="PHASE_2H1",
            approximate=True,
            source_id=o2o_event[
                "source_id"
            ],
            notes=(
                "Computational reference anchor "
                "for NASA's 'just after noon' "
                "timing; not an exact event time."
            ),
        ),

        make_row(
            event_id="otc3",
            name="Outbound Correction Burn",
            timestamp=otc,
            timestamp_text=(
                otc_event[
                    "timestamp_utc"
                ]
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="BURN",
            domain="BURN",
            provenance="NASA_REPORTED",
            precision="SOURCE_REPORTED",
            source_layer="PHASE_1",
            source_id="trajectory_events",
        ),

        make_row(
            event_id="lunar_soi_entry",
            name="Lunar SOI entry",
            timestamp=soi_entry,
            timestamp_text=(
                iso_z_microseconds(
                    soi_entry
                )
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="LUNAR_SOI_CROSSING",
            domain="GEOMETRY",
            provenance="MISSIONLAB_DERIVED",
            precision="DERIVED_INTERPOLATED",
            source_layer="PHASE_1",
            source_id=(
                "mission_phase_summary"
            ),
        ),

        make_row(
            event_id=(
                "lunar_earthset_reported"
            ),
            name="Reported Earthset",
            timestamp=earthset,
            timestamp_text=(
                earthset_event[
                    "timestamp_utc"
                ]
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="EARTHSET",
            domain="GEOMETRY",
            provenance="NASA_REPORTED",
            precision=(
                earthset_event[
                    "precision"
                ]
            ),
            source_layer="PHASE_2H1",
            source_id=earthset_event[
                "source_id"
            ],
        ),

        make_row(
            event_id=(
                "geocentric_occultation_ingress"
            ),
            name=(
                "Geocentric occultation ingress"
            ),
            timestamp=geocentric_ingress,
            timestamp_text=(
                geocentric_ingress_text
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="OCCULTATION_INGRESS",
            domain="GEOMETRY",
            provenance="MISSIONLAB_DERIVED",
            precision="DERIVED_REFINED",
            source_layer="PHASE_2G1",
            source_id=(
                "phase2g1_geocentric_"
                "lunar_occultation"
            ),
        ),

        make_row(
            event_id=(
                "dss43_topocentric_ingress"
            ),
            name=(
                "DSS-43 topocentric ingress"
            ),
            timestamp=dss43_ingress,
            timestamp_text=(
                dss43_ingress_text
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="OCCULTATION_INGRESS",
            domain="GEOMETRY",
            provenance="MISSIONLAB_DERIVED",
            precision="DERIVED_REFINED",
            source_layer="PHASE_2G2",
            source_id=(
                "phase2g2_dsn_"
                "topocentric_geometry"
            ),
            notes=(
                "Representative DSS-43 "
                "geometry; not an operational "
                "station assignment claim."
            ),
        ),

        make_row(
            event_id=(
                "lunar_blackout_start_reported"
            ),
            name=(
                "Reported RF blackout start"
            ),
            timestamp=blackout,
            timestamp_text=(
                blackout_event[
                    "timestamp_utc"
                ]
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="RF_LOS",
            domain="RF",
            provenance="NASA_REPORTED",
            precision=(
                blackout_event[
                    "precision"
                ]
            ),
            source_layer="PHASE_2H1",
            source_id=blackout_event[
                "source_id"
            ],
        ),

        make_row(
            event_id="pericynthion",
            name="Pericynthion",
            timestamp=pericynthion,
            timestamp_text=(
                pericynthion_text
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="PERICYNTHION",
            domain="GEOMETRY",
            provenance="MISSIONLAB_DERIVED",
            precision="DERIVED_REFINED",
            source_layer="PHASE_1",
            source_id=(
                "mission_phase_summary"
            ),
        ),

        make_row(
            event_id=(
                "maximum_earth_center_distance"
            ),
            name=(
                "Maximum Earth-center distance"
            ),
            timestamp=maximum_earth_distance,
            timestamp_text=(
                maximum_earth_text
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="MAXIMUM_EARTH_DISTANCE",
            domain="GEOMETRY",
            provenance=(
                "DERIVED_FROM_FLIGHT_DATA"
            ),
            precision="DERIVED_SAMPLED",
            source_layer="PHASE_1",
            source_id=(
                "mission_phase_summary"
            ),
        ),

        make_row(
            event_id=(
                "geocentric_occultation_egress"
            ),
            name=(
                "Geocentric occultation egress"
            ),
            timestamp=geocentric_egress,
            timestamp_text=(
                geocentric_egress_text
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="OCCULTATION_EGRESS",
            domain="GEOMETRY",
            provenance="MISSIONLAB_DERIVED",
            precision="DERIVED_REFINED",
            source_layer="PHASE_2G1",
            source_id=(
                "phase2g1_geocentric_"
                "lunar_occultation"
            ),
        ),

        make_row(
            event_id=(
                "dss43_topocentric_egress"
            ),
            name=(
                "DSS-43 topocentric egress"
            ),
            timestamp=dss43_egress,
            timestamp_text=(
                dss43_egress_text
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="OCCULTATION_EGRESS",
            domain="GEOMETRY",
            provenance="MISSIONLAB_DERIVED",
            precision="DERIVED_REFINED",
            source_layer="PHASE_2G2",
            source_id=(
                "phase2g2_dsn_"
                "topocentric_geometry"
            ),
            notes=(
                "Representative DSS-43 "
                "geometry; not an operational "
                "station assignment claim."
            ),
        ),

        make_row(
            event_id=(
                "lunar_earthrise_reported"
            ),
            name="Reported Earthrise",
            timestamp=earthrise,
            timestamp_text=(
                earthrise_event[
                    "timestamp_utc"
                ]
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="EARTHRISE",
            domain="GEOMETRY",
            provenance="NASA_REPORTED",
            precision=(
                earthrise_event[
                    "precision"
                ]
            ),
            source_layer="PHASE_2H1",
            source_id=earthrise_event[
                "source_id"
            ],
        ),

        make_row(
            event_id=(
                "dsn_reacquisition_planned"
            ),
            name="Planned public DSN AOS",
            timestamp=planned_aos,
            timestamp_text=(
                aos_event[
                    "timestamp_utc"
                ]
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="RF_AOS",
            domain="RF",
            provenance="NASA_PLANNED",
            precision=(
                aos_event[
                    "precision"
                ]
            ),
            source_layer="PHASE_2H1",
            source_id=aos_event[
                "source_id"
            ],
        ),

        make_row(
            event_id="lunar_soi_exit",
            name="Lunar SOI exit",
            timestamp=soi_exit,
            timestamp_text=(
                iso_z_microseconds(
                    soi_exit
                )
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="LUNAR_SOI_CROSSING",
            domain="GEOMETRY",
            provenance="MISSIONLAB_DERIVED",
            precision="DERIVED_INTERPOLATED",
            source_layer="PHASE_1",
            source_id=(
                "mission_phase_summary"
            ),
        ),

        make_row(
            event_id="rtc1",
            name="Return Correction Burn 1",
            timestamp=rtc1,
            timestamp_text=(
                rtc1_event[
                    "timestamp_utc"
                ]
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="BURN",
            domain="BURN",
            provenance="NASA_REPORTED",
            precision="SOURCE_REPORTED",
            source_layer="PHASE_1",
            source_id="trajectory_events",
        ),

        make_row(
            event_id=(
                "unexpected_return_link_loss"
            ),
            name=(
                "Unexpected return-link "
                "LOS anchor"
            ),
            timestamp=return_loss_anchor,
            timestamp_text=(
                return_loss_event[
                    "approximate_anchor_utc"
                ]
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="RF_LOS_ANOMALY",
            domain="RF",
            provenance="NASA_REPORTED",
            precision="APPROXIMATE",
            source_layer="PHASE_2H1",
            approximate=True,
            source_id=return_loss_event[
                "source_id"
            ],
            notes=(
                "RTC2 minus approximately "
                "two hours. This is not an "
                "observed exact outage time."
            ),
        ),

        make_row(
            event_id="rtc2",
            name="Return Correction Burn 2",
            timestamp=rtc2,
            timestamp_text=(
                rtc2_event[
                    "timestamp_utc"
                ]
            ),
            launch_epoch=launch_epoch,
            soi_entry=soi_entry,
            pericynthion=pericynthion,
            soi_exit=soi_exit,
            kind="BURN",
            domain="BURN",
            provenance="NASA_REPORTED",
            precision="SOURCE_REPORTED",
            source_layer="PHASE_1",
            source_id="trajectory_events",
        ),
    ]

    rows.sort(
        key=lambda row:
            row["timestamp"]
    )

    if len(rows) != 17:
        fail(
            "Expected 17 synchronized "
            "timeline events."
        )

    flyby_ids = [
        "lunar_earthset_reported",
        "geocentric_occultation_ingress",
        "dss43_topocentric_ingress",
        "lunar_blackout_start_reported",
        "pericynthion",
        "maximum_earth_center_distance",
        "geocentric_occultation_egress",
        "dss43_topocentric_egress",
        "lunar_earthrise_reported",
        "dsn_reacquisition_planned",
    ]

    rows_by_id = {
        row["id"]:
            row
        for row in rows
    }

    flyby_rows = [
        rows_by_id[event_id]
        for event_id in flyby_ids
    ]

    for row in flyby_rows:
        if not (
            soi_entry
            <= row["timestamp"]
            <= soi_exit
        ):
            fail(
                f"{row['id']} unexpectedly "
                "falls outside lunar SOI."
            )

    correlations = {
        "otc_to_lunar_soi_entry_seconds":
            delta_seconds(
                otc,
                soi_entry,
            ),

        "soi_entry_to_reported_earthset_seconds":
            delta_seconds(
                soi_entry,
                earthset,
            ),

        "geocentric_ingress_to_reported_blackout_seconds":
            delta_seconds(
                geocentric_ingress,
                blackout,
            ),

        "dss43_ingress_to_reported_blackout_seconds":
            delta_seconds(
                dss43_ingress,
                blackout,
            ),

        "reported_blackout_to_pericynthion_seconds":
            delta_seconds(
                blackout,
                pericynthion,
            ),

        "pericynthion_to_maximum_earth_distance_seconds":
            delta_seconds(
                pericynthion,
                maximum_earth_distance,
            ),

        "geocentric_egress_to_reported_earthrise_seconds":
            delta_seconds(
                geocentric_egress,
                earthrise,
            ),

        "dss43_egress_to_reported_earthrise_seconds":
            delta_seconds(
                dss43_egress,
                earthrise,
            ),

        "pericynthion_to_reported_earthrise_seconds":
            delta_seconds(
                pericynthion,
                earthrise,
            ),

        "planned_aos_to_lunar_soi_exit_seconds":
            delta_seconds(
                planned_aos,
                soi_exit,
            ),

        "lunar_soi_exit_to_rtc1_seconds":
            delta_seconds(
                soi_exit,
                rtc1,
            ),

        "approximate_return_link_loss_to_rtc2_seconds":
            delta_seconds(
                return_loss_anchor,
                rtc2,
            ),
    }

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "id",
        "name",
        "timestamp_utc",
        "met",
        "mission_phase",
        "kind",
        "domain",
        "source_layer",
        "provenance",
        "precision",
        "is_approximate",
        "source_id",
        "notes",
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

                    "timestamp_utc":
                        row[
                            "timestamp_utc"
                        ],

                    "met":
                        row["met"],

                    "mission_phase":
                        row[
                            "mission_phase"
                        ],

                    "kind":
                        row["kind"],

                    "domain":
                        row["domain"],

                    "source_layer":
                        row[
                            "source_layer"
                        ],

                    "provenance":
                        row[
                            "provenance"
                        ],

                    "precision":
                        row[
                            "precision"
                        ],

                    "is_approximate":
                        str(
                            row[
                                "is_approximate"
                            ]
                        ).lower(),

                    "source_id":
                        row[
                            "source_id"
                        ],

                    "notes":
                        row["notes"],
                }
            )

    build_mission_figure(
        rows
    )

    build_flyby_figure(
        flyby_rows,
        geocentric_ingress,
        geocentric_egress,
        dss43_ingress,
        dss43_egress,
    )

    phase_counts = Counter(
        row["mission_phase"]
        for row in rows
    )

    domain_counts = Counter(
        row["domain"]
        for row in rows
    )

    approximate_ids = [
        row["id"]
        for row in rows
        if row[
            "is_approximate"
        ]
    ]

    live_reacquisition = (
        events_by_id[
            "dsn_reacquisition_live_report"
        ]
    )

    summary = {
        "product_id":
            (
                "phase2h2_mission_clock_"
                "communications_correlation"
            ),

        "mission":
            "Artemis II",

        "event_count":
            len(rows),

        "input_products": {
            "communications_catalog":
                catalog[
                    "dataset_id"
                ],

            "communications_timeline":
                communications_summary[
                    "product_id"
                ],

            "geocentric_occultation":
                geocentric_summary[
                    "product_id"
                ],

            "topocentric_geometry":
                topocentric_summary[
                    "product_id"
                ],

            "mission_phase_summary":
                (
                    "phase1_mission_phase_summary"
                ),
        },

        "mission_anchors": {
            "launch_epoch_utc":
                mission[
                    "launch_epoch_utc"
                ],

            "lunar_soi_entry_utc":
                iso_z_microseconds(
                    soi_entry
                ),

            "pericynthion_utc":
                pericynthion_text,

            "lunar_soi_exit_utc":
                iso_z_microseconds(
                    soi_exit
                ),
        },

        "phase_counts":
            dict(
                phase_counts
            ),

        "domain_counts":
            dict(
                domain_counts
            ),

        "approximate_event_ids":
            approximate_ids,

        "flyby_sequence": [
            {
                "order":
                    index,

                "id":
                    row["id"],

                "name":
                    row["name"],

                "timestamp_utc":
                    row[
                        "timestamp_utc"
                    ],

                "mission_phase":
                    row[
                        "mission_phase"
                    ],

                "provenance":
                    row[
                        "provenance"
                    ],

                "precision":
                    row[
                        "precision"
                    ],
            }
            for index, row in enumerate(
                flyby_rows,
                start=1,
            )
        ],

        "correlations_seconds":
            correlations,

        "flyby_events_inside_lunar_soi": {
            row["id"]:
                True
            for row in flyby_rows
        },

        "untimed_operational_relations": [
            {
                "id":
                    live_reacquisition[
                        "id"
                    ],

                "name":
                    live_reacquisition[
                        "name"
                    ],

                "precision":
                    live_reacquisition[
                        "precision"
                    ],

                "event_state":
                    live_reacquisition[
                        "event_state"
                    ],

                "ordering":
                    live_reacquisition[
                        "ordering"
                    ],

                "timestamp_utc":
                    None,

                "met":
                    None,

                "interpretation":
                    (
                        "NASA reports DSN "
                        "reacquisition moments "
                        "after reported Earthrise. "
                        "No exact UTC or MET is "
                        "assigned."
                    ),
            }
        ],

        "guardrails": [
            (
                "Phase 2H.2 correlates existing "
                "events and does not change their "
                "source provenance or timing precision."
            ),
            (
                "MissionLab-derived geometric event "
                "times are not relabeled as NASA "
                "operational event times."
            ),
            (
                "Minute-level NASA timestamps remain "
                "minute-level even when converted to MET."
            ),
            (
                "Approximate communications anchors "
                "remain explicitly approximate."
            ),
            (
                "The live DSN reacquisition remains "
                "SEQUENCE_ONLY with no invented UTC "
                "or MET."
            ),
            (
                "DSS-43 geometry remains a "
                "representative topocentric reference "
                "and is not an operational station "
                "assignment claim."
            ),
            (
                "O2O optical activity remains distinct "
                "from primary RF communications "
                "availability."
            ),
        ],

        "outputs": {
            "correlation_csv":
                str(
                    OUTPUT_CSV.relative_to(
                        ROOT
                    )
                ),

            "mission_figure":
                str(
                    MISSION_FIGURE.relative_to(
                        ROOT
                    )
                ),

            "flyby_figure":
                str(
                    FLYBY_FIGURE.relative_to(
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
        "Phase 2H.2 Mission-Clock "
        "Communications Correlation"
    )

    print("=" * 61)

    print()
    print(
        "Synchronized events:"
    )

    print(
        f"  {len(rows)}"
    )

    print()
    print(
        "Mission phase counts:"
    )

    for phase in [
        "OUTBOUND_TRANSIT",
        "LUNAR_APPROACH",
        "LUNAR_DEPARTURE",
        "TRANS_EARTH_RETURN",
    ]:
        print(
            f"  {phase}: "
            f"{phase_counts.get(phase, 0)}"
        )

    print()
    print(
        "Flight Day 6 sequence:"
    )

    for index, row in enumerate(
        flyby_rows,
        start=1,
    ):
        print(
            f"  {index:02d}. "
            f"{row['timestamp'].strftime('%H:%M:%S.%f')[:-3]} "
            f"{row['name']}"
        )

    print()
    print(
        "Key correlations:"
    )

    for key, value in (
        correlations.items()
    ):
        print(
            f"  {key}:"
        )

        print(
            f"    {value:+.3f} s"
        )

        print(
            f"    {value / 60.0:+.3f} min"
        )

    print()
    print(
        "Flight Day 6 SOI containment:"
    )

    for row in flyby_rows:
        print(
            f"  {row['name']}: True"
        )

    print()
    print(
        "Approximate anchors:"
    )

    for event_id in approximate_ids:
        print(
            f"  {event_id}"
        )

    print()
    print(
        "Untimed operational relation:"
    )

    print(
        "  live DSN reacquisition:"
    )

    print(
        "    SEQUENCE_ONLY"
    )

    print(
        "    MOMENTS_AFTER_REPORTED_EARTHRISE"
    )

    print(
        "    no exact UTC or MET assigned"
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
        f"{MISSION_FIGURE.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{FLYBY_FIGURE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
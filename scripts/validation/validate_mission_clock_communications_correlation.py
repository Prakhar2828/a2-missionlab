from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


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

SUMMARY_PATH = (
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

EXPECTED_PRODUCT_ID = (
    "phase2h2_mission_clock_"
    "communications_correlation"
)

EXPECTED_EVENT_IDS = [
    "o2o_100_gb_downlink_milestone",
    "otc3",
    "lunar_soi_entry",
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
    "lunar_soi_exit",
    "rtc1",
    "unexpected_return_link_loss",
    "rtc2",
]

EXPECTED_FLYBY_IDS = [
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

EXPECTED_PHASE_COUNTS = {
    "OUTBOUND_TRANSIT": 2,
    "LUNAR_APPROACH": 6,
    "LUNAR_DEPARTURE": 6,
    "TRANS_EARTH_RETURN": 3,
}


def fail(message: str) -> None:
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def load_json(path: Path):
    if not path.exists():
        fail(
            f"missing file: {path}"
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


def mission_phase(
    timestamp,
    soi_entry,
    pericynthion,
    soi_exit,
):
    if timestamp < soi_entry:
        return "OUTBOUND_TRANSIT"

    if timestamp <= pericynthion:
        return "LUNAR_APPROACH"

    if timestamp <= soi_exit:
        return "LUNAR_DEPARTURE"

    return "TRANS_EARTH_RETURN"


def check_close(
    label,
    observed,
    expected,
    tolerance=0.002,
):
    if abs(
        observed - expected
    ) > tolerance:
        fail(
            f"{label} mismatch: "
            f"{observed} vs {expected}"
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

    phase_summary = load_json(
        MISSION_PHASE_SUMMARY_PATH
    )

    geocentric = load_json(
        GEOCENTRIC_SUMMARY_PATH
    )

    topocentric = load_json(
        TOPOCENTRIC_SUMMARY_PATH
    )

    comm_summary = load_json(
        COMM_EVENT_SUMMARY_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    if (
        summary.get(
            "product_id"
        )
        != EXPECTED_PRODUCT_ID
    ):
        fail(
            "product ID mismatch"
        )

    if (
        comm_summary.get(
            "event_count"
        )
        != 16
    ):
        fail(
            "Phase 2H.1 event count changed"
        )

    launch_epoch = parse_utc(
        mission[
            "launch_epoch_utc"
        ]
    )

    if launch_epoch != datetime(
        2026,
        4,
        1,
        22,
        35,
        12,
        tzinfo=timezone.utc,
    ):
        fail(
            "launch epoch changed"
        )

    catalog_by_id = {
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

    soi_entry = parse_utc(
        phase_summary[
            "lunar_soi"
        ][
            "derived_entry_utc"
        ]
    )

    soi_exit = parse_utc(
        phase_summary[
            "lunar_soi"
        ][
            "derived_exit_utc"
        ]
    )

    pericynthion = parse_utc(
        phase_summary[
            "pericynthion"
        ][
            "timestamp_utc"
        ]
    )

    maximum_earth = parse_utc(
        phase_summary[
            "maximum_earth_center_distance"
        ][
            "timestamp_utc"
        ]
    )

    geo_ingress = parse_utc(
        geocentric[
            "geocentric_occultation_window"
        ][
            "ingress_utc"
        ]
    )

    geo_egress = parse_utc(
        geocentric[
            "geocentric_occultation_window"
        ][
            "egress_utc"
        ]
    )

    dss43_matches = [
        row
        for row in topocentric[
            "station_results"
        ]
        if row["station"] == "DSS-43"
    ]

    if len(dss43_matches) != 1:
        fail(
            "expected one DSS-43 result"
        )

    dss43 = dss43_matches[0]

    dss43_ingress = parse_utc(
        dss43[
            "ingress_utc"
        ]
    )

    dss43_egress = parse_utc(
        dss43[
            "egress_utc"
        ]
    )

    earthset = parse_utc(
        catalog_by_id[
            "lunar_earthset_reported"
        ][
            "timestamp_utc"
        ]
    )

    blackout = parse_utc(
        catalog_by_id[
            "lunar_blackout_start_reported"
        ][
            "timestamp_utc"
        ]
    )

    earthrise = parse_utc(
        catalog_by_id[
            "lunar_earthrise_reported"
        ][
            "timestamp_utc"
        ]
    )

    planned_aos = parse_utc(
        catalog_by_id[
            "dsn_reacquisition_planned"
        ][
            "timestamp_utc"
        ]
    )

    o2o_anchor = parse_utc(
        catalog_by_id[
            "o2o_100_gb_downlink_milestone"
        ][
            "approximate_anchor_utc"
        ]
    )

    return_loss_anchor = parse_utc(
        catalog_by_id[
            "unexpected_return_link_loss"
        ][
            "approximate_anchor_utc"
        ]
    )

    otc = parse_utc(
        trajectory_by_id[
            "otc3"
        ][
            "timestamp_utc"
        ]
    )

    rtc1 = parse_utc(
        trajectory_by_id[
            "rtc1"
        ][
            "timestamp_utc"
        ]
    )

    rtc2 = parse_utc(
        trajectory_by_id[
            "rtc2"
        ][
            "timestamp_utc"
        ]
    )

    expected_times = {
        "o2o_100_gb_downlink_milestone":
            o2o_anchor,

        "otc3":
            otc,

        "lunar_soi_entry":
            soi_entry,

        "lunar_earthset_reported":
            earthset,

        "geocentric_occultation_ingress":
            geo_ingress,

        "dss43_topocentric_ingress":
            dss43_ingress,

        "lunar_blackout_start_reported":
            blackout,

        "pericynthion":
            pericynthion,

        "maximum_earth_center_distance":
            maximum_earth,

        "geocentric_occultation_egress":
            geo_egress,

        "dss43_topocentric_egress":
            dss43_egress,

        "lunar_earthrise_reported":
            earthrise,

        "dsn_reacquisition_planned":
            planned_aos,

        "lunar_soi_exit":
            soi_exit,

        "rtc1":
            rtc1,

        "unexpected_return_link_loss":
            return_loss_anchor,

        "rtc2":
            rtc2,
    }

    ordered_times = [
        expected_times[
            event_id
        ]
        for event_id in (
            EXPECTED_EVENT_IDS
        )
    ]

    if ordered_times != sorted(
        ordered_times
    ):
        fail(
            "integrated event ordering changed"
        )

    if not OUTPUT_CSV.exists():
        fail(
            "correlation CSV missing"
        )

    with OUTPUT_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        rows = list(
            csv.DictReader(f)
        )

    if len(rows) != 17:
        fail(
            "correlation CSV must contain "
            "17 rows"
        )

    csv_ids = [
        row["id"]
        for row in rows
    ]

    if csv_ids != EXPECTED_EVENT_IDS:
        fail(
            "correlation CSV event order "
            "or identity changed"
        )

    rows_by_id = {
        row["id"]:
            row
        for row in rows
    }

    for event_id, expected_time in (
        expected_times.items()
    ):
        observed_time = parse_utc(
            rows_by_id[
                event_id
            ][
                "timestamp_utc"
            ]
        )

        check_close(
            f"{event_id} timestamp",
            (
                observed_time
                - expected_time
            ).total_seconds(),
            0.0,
            tolerance=0.002,
        )

        expected_phase = mission_phase(
            expected_time,
            soi_entry,
            pericynthion,
            soi_exit,
        )

        if (
            rows_by_id[
                event_id
            ][
                "mission_phase"
            ]
            != expected_phase
        ):
            fail(
                f"{event_id} mission "
                "phase mismatch"
            )

    phase_counts = Counter(
        row[
            "mission_phase"
        ]
        for row in rows
    )

    if dict(
        phase_counts
    ) != EXPECTED_PHASE_COUNTS:
        fail(
            "mission phase counts changed"
        )

    approximate_ids = [
        row["id"]
        for row in rows
        if row[
            "is_approximate"
        ] == "true"
    ]

    if approximate_ids != [
        "o2o_100_gb_downlink_milestone",
        "unexpected_return_link_loss",
    ]:
        fail(
            "approximate event set changed"
        )

    if (
        rows_by_id[
            "lunar_earthset_reported"
        ][
            "precision"
        ]
        != "MINUTE_LEVEL"
    ):
        fail(
            "reported Earthset lost "
            "minute-level precision"
        )

    if (
        rows_by_id[
            "lunar_blackout_start_reported"
        ][
            "precision"
        ]
        != "MINUTE_LEVEL"
    ):
        fail(
            "reported blackout lost "
            "minute-level precision"
        )

    if (
        rows_by_id[
            "lunar_earthrise_reported"
        ][
            "precision"
        ]
        != "MINUTE_LEVEL"
    ):
        fail(
            "reported Earthrise lost "
            "minute-level precision"
        )

    if (
        rows_by_id[
            "dsn_reacquisition_planned"
        ][
            "precision"
        ]
        != "MINUTE_LEVEL"
    ):
        fail(
            "planned AOS lost "
            "minute-level precision"
        )

    for event_id in (
        EXPECTED_FLYBY_IDS
    ):
        timestamp = (
            expected_times[
                event_id
            ]
        )

        if not (
            soi_entry
            <= timestamp
            <= soi_exit
        ):
            fail(
                f"{event_id} unexpectedly "
                "outside lunar SOI"
            )

    expected_correlations = {
        "otc_to_lunar_soi_entry_seconds":
            (
                soi_entry - otc
            ).total_seconds(),

        "soi_entry_to_reported_earthset_seconds":
            (
                earthset - soi_entry
            ).total_seconds(),

        "geocentric_ingress_to_reported_blackout_seconds":
            (
                blackout - geo_ingress
            ).total_seconds(),

        "dss43_ingress_to_reported_blackout_seconds":
            (
                blackout - dss43_ingress
            ).total_seconds(),

        "reported_blackout_to_pericynthion_seconds":
            (
                pericynthion - blackout
            ).total_seconds(),

        "pericynthion_to_maximum_earth_distance_seconds":
            (
                maximum_earth
                - pericynthion
            ).total_seconds(),

        "geocentric_egress_to_reported_earthrise_seconds":
            (
                earthrise - geo_egress
            ).total_seconds(),

        "dss43_egress_to_reported_earthrise_seconds":
            (
                earthrise - dss43_egress
            ).total_seconds(),

        "pericynthion_to_reported_earthrise_seconds":
            (
                earthrise - pericynthion
            ).total_seconds(),

        "planned_aos_to_lunar_soi_exit_seconds":
            (
                soi_exit - planned_aos
            ).total_seconds(),

        "lunar_soi_exit_to_rtc1_seconds":
            (
                rtc1 - soi_exit
            ).total_seconds(),

        "approximate_return_link_loss_to_rtc2_seconds":
            (
                rtc2
                - return_loss_anchor
            ).total_seconds(),
    }

    observed_correlations = (
        summary[
            "correlations_seconds"
        ]
    )

    for key, expected in (
        expected_correlations.items()
    ):
        if key not in (
            observed_correlations
        ):
            fail(
                f"missing correlation {key}"
            )

        check_close(
            key,
            float(
                observed_correlations[
                    key
                ]
            ),
            expected,
            tolerance=0.002,
        )

    if (
        summary.get(
            "event_count"
        )
        != 17
    ):
        fail(
            "summary event count mismatch"
        )

    if (
        summary.get(
            "phase_counts"
        )
        != EXPECTED_PHASE_COUNTS
    ):
        fail(
            "summary phase counts mismatch"
        )

    summary_flyby_ids = [
        row["id"]
        for row in summary[
            "flyby_sequence"
        ]
    ]

    if (
        summary_flyby_ids
        != EXPECTED_FLYBY_IDS
    ):
        fail(
            "summary flyby sequence changed"
        )

    containment = (
        summary[
            "flyby_events_inside_lunar_soi"
        ]
    )

    for event_id in (
        EXPECTED_FLYBY_IDS
    ):
        if (
            containment.get(
                event_id
            )
            is not True
        ):
            fail(
                f"{event_id} SOI "
                "containment not true"
            )

    relations = (
        summary[
            "untimed_operational_relations"
        ]
    )

    if len(relations) != 1:
        fail(
            "expected exactly one untimed "
            "operational relation"
        )

    relation = relations[0]

    if (
        relation["id"]
        != "dsn_reacquisition_live_report"
    ):
        fail(
            "unexpected untimed relation"
        )

    if (
        relation["precision"]
        != "SEQUENCE_ONLY"
    ):
        fail(
            "live DSN reacquisition gained "
            "unsupported precision"
        )

    if (
        relation[
            "ordering"
        ]
        != (
            "MOMENTS_AFTER_"
            "REPORTED_EARTHRISE"
        )
    ):
        fail(
            "live DSN reacquisition ordering "
            "changed"
        )

    if (
        relation[
            "timestamp_utc"
        ]
        is not None
        or relation[
            "met"
        ]
        is not None
    ):
        fail(
            "live DSN reacquisition received "
            "invented UTC or MET"
        )

    for figure in [
        MISSION_FIGURE,
        FLYBY_FIGURE,
    ]:
        if not figure.exists():
            fail(
                f"missing figure: {figure}"
            )

        text = figure.read_text(
            encoding="utf-8"
        )

        if (
            "<svg" not in text
            or len(text) < 1000
        ):
            fail(
                f"invalid figure: {figure}"
            )

    print()
    print(
        "Phase 2H.2 Mission-Clock "
        "Communications Correlation Validation"
    )

    print("=" * 72)

    print()
    print(
        "Synchronized events:"
    )

    print(
        "  17"
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
            f"{EXPECTED_PHASE_COUNTS[phase]}"
        )

    print()
    print(
        "Flight Day 6 sequence:"
    )

    for index, event_id in enumerate(
        EXPECTED_FLYBY_IDS,
        start=1,
    ):
        timestamp = (
            expected_times[
                event_id
            ]
        )

        print(
            f"  {index:02d}. "
            f"{timestamp.strftime('%H:%M:%S.%f')[:-3]} "
            f"{event_id}"
        )

    print()
    print(
        "Independent correlations:"
    )

    for key, value in (
        expected_correlations.items()
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

    print(
        "  all 10 synchronized "
        "flyby events: TRUE"
    )

    print()
    print(
        "Precision guardrails:"
    )

    print(
        "  O2O 100 GB anchor: "
        "APPROXIMATE"
    )

    print(
        "  return-link LOS anchor: "
        "APPROXIMATE"
    )

    print(
        "  live DSN reacquisition: "
        "SEQUENCE_ONLY"
    )

    print(
        "  live DSN reacquisition UTC: "
        "NONE"
    )

    print(
        "  live DSN reacquisition MET: "
        "NONE"
    )

    print()
    print(
        "Products:"
    )

    print(
        "  correlation CSV rows: 17"
    )

    print(
        "  summary: PASS"
    )

    print(
        "  mission figure: PASS"
    )

    print(
        "  flyby figure: PASS"
    )

    print()
    print(
        "OK: Phase 2H.2 mission-clock "
        "event identity, mission-phase "
        "assignment, Phase 1 / 2G / 2H.1 "
        "cross-phase timing, Flight Day 6 "
        "ordering, lunar SOI containment, "
        "precision preservation, untimed "
        "DSN reacquisition guardrail, "
        "correlation metrics, and generated "
        "products independently validated."
    )


if __name__ == "__main__":
    main()
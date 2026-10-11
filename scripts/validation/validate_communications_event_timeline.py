from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


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

SUMMARY_PATH = (
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

EXPECTED_DATASET_ID = (
    "phase2h1_artemis_ii_communications_event_catalog"
)

EXPECTED_PRODUCT_ID = (
    "phase2h1_communications_event_timeline"
)

EXPECTED_IDS = {
    "nsn_leads_initial_orion_communications",
    "dsn_madrid_early_mission_signal_acquisition",
    "primary_support_transition_nsn_to_dsn",
    "dsn_emergency_communications_test",
    "o2o_two_us_ground_station_links",
    "o2o_100_gb_downlink_milestone",
    "lunar_earthset_planned",
    "lunar_earthset_reported",
    "lunar_blackout_start_planned",
    "lunar_blackout_start_reported",
    "lunar_earthrise_planned",
    "lunar_earthrise_reported",
    "dsn_reacquisition_planned",
    "dsn_reacquisition_live_report",
    "unexpected_return_link_loss",
    "two_way_communications_reestablished",
}

EXPECTED_PRECISION_COUNTS = {
    "EXACT": 0,
    "MINUTE_LEVEL": 7,
    "APPROXIMATE": 2,
    "DATE_LEVEL": 3,
    "SEQUENCE_ONLY": 4,
}

EXPECTED_DOMAIN_COUNTS = {
    "GEOMETRIC_CONTEXT": 4,
    "OPTICAL": 2,
    "RF": 10,
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


def main() -> None:
    catalog = load_json(
        CATALOG_PATH
    )

    mission = load_json(
        MISSION_PATH
    )

    phase2g = load_json(
        PHASE2G_REFERENCE_PATH
    )

    trajectory_events = load_json(
        TRAJECTORY_EVENTS_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    if (
        catalog.get(
            "dataset_id"
        )
        != EXPECTED_DATASET_ID
    ):
        fail(
            "catalog dataset ID mismatch"
        )

    if (
        summary.get(
            "product_id"
        )
        != EXPECTED_PRODUCT_ID
    ):
        fail(
            "summary product ID mismatch"
        )

    events = catalog[
        "events"
    ]

    if len(events) != 16:
        fail(
            "expected exactly 16 events"
        )

    events_by_id = {
        event["id"]:
            event
        for event in events
    }

    if set(
        events_by_id
    ) != EXPECTED_IDS:
        fail(
            "event ID set changed"
        )

    source_ids = {
        source["source_id"]
        for source in catalog[
            "sources"
        ]
    }

    for event in events:
        if (
            event["source_id"]
            not in source_ids
        ):
            fail(
                "unknown source for "
                f"{event['id']}"
            )

        precision = event[
            "precision"
        ]

        timestamp_text = event.get(
            "timestamp_utc"
        )

        anchor_text = event.get(
            "approximate_anchor_utc"
        )

        if precision in {
            "DATE_LEVEL",
            "SEQUENCE_ONLY",
        }:
            if timestamp_text is not None:
                fail(
                    "false timestamp on "
                    f"{event['id']}"
                )

            if anchor_text is not None:
                fail(
                    "false anchor on "
                    f"{event['id']}"
                )

        if precision == "MINUTE_LEVEL":
            if timestamp_text is None:
                fail(
                    "minute event missing time: "
                    f"{event['id']}"
                )

            timestamp = parse_utc(
                timestamp_text
            )

            if (
                timestamp.second != 0
                or timestamp.microsecond != 0
            ):
                fail(
                    "false sub-minute precision: "
                    f"{event['id']}"
                )

        if (
            precision == "APPROXIMATE"
            and anchor_text is not None
            and event.get(
                "anchor_is_not_exact"
            )
            is not True
        ):
            fail(
                "approximate anchor lacks guard: "
                f"{event['id']}"
            )

    precision_counts = Counter(
        event["precision"]
        for event in events
    )

    observed_precision_counts = {
        key:
            precision_counts.get(
                key,
                0,
            )
        for key in (
            EXPECTED_PRECISION_COUNTS
        )
    }

    if (
        observed_precision_counts
        != EXPECTED_PRECISION_COUNTS
    ):
        fail(
            "precision counts changed"
        )

    domain_counts = Counter(
        event["domain"]
        for event in events
    )

    if dict(
        domain_counts
    ) != EXPECTED_DOMAIN_COUNTS:
        fail(
            "domain counts changed"
        )

    planned_earthset = parse_utc(
        events_by_id[
            "lunar_earthset_planned"
        ][
            "timestamp_utc"
        ]
    )

    reported_earthset = parse_utc(
        events_by_id[
            "lunar_earthset_reported"
        ][
            "timestamp_utc"
        ]
    )

    planned_blackout = parse_utc(
        events_by_id[
            "lunar_blackout_start_planned"
        ][
            "timestamp_utc"
        ]
    )

    reported_blackout = parse_utc(
        events_by_id[
            "lunar_blackout_start_reported"
        ][
            "timestamp_utc"
        ]
    )

    planned_earthrise = parse_utc(
        events_by_id[
            "lunar_earthrise_planned"
        ][
            "timestamp_utc"
        ]
    )

    reported_earthrise = parse_utc(
        events_by_id[
            "lunar_earthrise_reported"
        ][
            "timestamp_utc"
        ]
    )

    planned_aos = parse_utc(
        events_by_id[
            "dsn_reacquisition_planned"
        ][
            "timestamp_utc"
        ]
    )

    if (
        (
            reported_earthset
            - planned_earthset
        ).total_seconds()
        != -240.0
    ):
        fail(
            "planned/reported Earthset "
            "difference changed"
        )

    if (
        (
            reported_blackout
            - planned_blackout
        ).total_seconds()
        != 0.0
    ):
        fail(
            "planned/reported blackout "
            "difference changed"
        )

    if (
        (
            reported_earthrise
            - planned_earthrise
        ).total_seconds()
        != -60.0
    ):
        fail(
            "planned/reported Earthrise "
            "difference changed"
        )

    if (
        (
            reported_blackout
            - reported_earthset
        ).total_seconds()
        != 180.0
    ):
        fail(
            "Earthset-to-blackout "
            "separation changed"
        )

    if (
        (
            planned_aos
            - reported_earthrise
        ).total_seconds()
        != 60.0
    ):
        fail(
            "Earthrise-to-planned-AOS "
            "separation changed"
        )

    phase2g_window = (
        phase2g[
            "public_lunar_occultation_window"
        ]
    )

    if (
        planned_blackout
        != parse_utc(
            phase2g_window[
                "loss_of_signal_utc"
            ]
        )
    ):
        fail(
            "2H blackout and Phase 2G "
            "LOS disagree"
        )

    if (
        planned_aos
        != parse_utc(
            phase2g_window[
                "acquisition_of_signal_utc"
            ]
        )
    ):
        fail(
            "2H AOS and Phase 2G "
            "AOS disagree"
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
            "expected exactly one RTC2"
        )

    rtc2 = parse_utc(
        rtc2_matches[
            0
        ][
            "timestamp_utc"
        ]
    )

    return_loss_anchor = parse_utc(
        events_by_id[
            "unexpected_return_link_loss"
        ][
            "approximate_anchor_utc"
        ]
    )

    if (
        (
            rtc2
            - return_loss_anchor
        ).total_seconds()
        != 7200.0
    ):
        fail(
            "return-link-loss approximate "
            "anchor no longer two hours "
            "before RTC2"
        )

    if (
        events_by_id[
            "unexpected_return_link_loss"
        ][
            "anchor_is_not_exact"
        ]
        is not True
    ):
        fail(
            "return-link-loss anchor "
            "lost approximate guard"
        )

    if (
        events_by_id[
            "dsn_emergency_communications_test"
        ][
            "precision"
        ]
        != "DATE_LEVEL"
    ):
        fail(
            "emergency communications test "
            "must remain DATE_LEVEL"
        )

    if (
        events_by_id[
            "primary_support_transition_nsn_to_dsn"
        ][
            "precision"
        ]
        != "SEQUENCE_ONLY"
    ):
        fail(
            "NSN-to-DSN transition gained "
            "unsupported timestamp precision"
        )

    if (
        events_by_id[
            "dsn_reacquisition_live_report"
        ][
            "precision"
        ]
        != "SEQUENCE_ONLY"
    ):
        fail(
            "live DSN reacquisition gained "
            "unsupported timestamp precision"
        )

    launch_epoch = parse_utc(
        mission[
            "launch_epoch_utc"
        ]
    )

    if (
        launch_epoch
        != datetime(
            2026,
            4,
            1,
            22,
            35,
            12,
            tzinfo=timezone.utc,
        )
    ):
        fail(
            "mission launch epoch changed"
        )

    if (
        summary.get(
            "reference_dataset_id"
        )
        != EXPECTED_DATASET_ID
    ):
        fail(
            "summary reference ID mismatch"
        )

    if (
        summary.get(
            "event_count"
        )
        != 16
    ):
        fail(
            "summary event count mismatch"
        )

    for key, expected in (
        EXPECTED_PRECISION_COUNTS.items()
    ):
        if (
            summary[
                "precision_counts"
            ].get(
                key,
                0,
            )
            != expected
        ):
            fail(
                "summary precision count "
                f"mismatch for {key}"
            )

    for key, expected in (
        EXPECTED_DOMAIN_COUNTS.items()
    ):
        if (
            summary[
                "domain_counts"
            ].get(
                key,
                0,
            )
            != expected
        ):
            fail(
                "summary domain count "
                f"mismatch for {key}"
            )

    planned_vs_reported = (
        summary[
            "planned_vs_reported"
        ]
    )

    if (
        planned_vs_reported[
            "earthset_reported_minus_planned_seconds"
        ]
        != -240.0
    ):
        fail(
            "summary Earthset delta mismatch"
        )

    if (
        planned_vs_reported[
            "blackout_start_reported_minus_planned_seconds"
        ]
        != 0.0
    ):
        fail(
            "summary blackout delta mismatch"
        )

    if (
        planned_vs_reported[
            "earthrise_reported_minus_planned_seconds"
        ]
        != -60.0
    ):
        fail(
            "summary Earthrise delta mismatch"
        )

    if (
        summary.get(
            "guardrails"
        )
        != catalog.get(
            "guardrails"
        )
    ):
        fail(
            "summary guardrails changed"
        )

    if not OUTPUT_CSV.exists():
        fail(
            "timeline CSV missing"
        )

    with OUTPUT_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        output_rows = list(
            csv.DictReader(f)
        )

    if len(
        output_rows
    ) != 16:
        fail(
            "timeline CSV must contain "
            "16 rows"
        )

    csv_by_id = {
        row["id"]:
            row
        for row in output_rows
    }

    if set(
        csv_by_id
    ) != EXPECTED_IDS:
        fail(
            "CSV event ID set mismatch"
        )

    if (
        csv_by_id[
            "unexpected_return_link_loss"
        ][
            "met_is_approximate"
        ]
        != "true"
    ):
        fail(
            "return-link-loss MET not "
            "marked approximate"
        )

    if (
        csv_by_id[
            "primary_support_transition_nsn_to_dsn"
        ][
            "met"
        ]
        != ""
    ):
        fail(
            "sequence-only handoff has "
            "invented MET"
        )

    if (
        csv_by_id[
            "dsn_emergency_communications_test"
        ][
            "met"
        ]
        != ""
    ):
        fail(
            "date-level emergency test "
            "has invented MET"
        )

    if not FIGURE_PATH.exists():
        fail(
            "timeline SVG missing"
        )

    svg = FIGURE_PATH.read_text(
        encoding="utf-8",
    )

    if (
        "<svg" not in svg
        or len(svg) < 1000
    ):
        fail(
            "timeline SVG invalid"
        )

    print()
    print(
        "Phase 2H.1 Operational "
        "Communications Event Validation"
    )

    print("=" * 60)

    print()
    print(
        "Catalog:"
    )

    print(
        "  events: 16"
    )

    print()
    print(
        "Precision:"
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
            f"{EXPECTED_PRECISION_COUNTS[precision]}"
        )

    print()
    print(
        "Flight Day 6:"
    )

    print(
        "  reported Earthset - planned:"
    )

    print(
        "    -240 s"
    )

    print(
        "  reported blackout - planned:"
    )

    print(
        "    +0 s"
    )

    print(
        "  reported Earthrise - planned:"
    )

    print(
        "    -60 s"
    )

    print(
        "  reported Earthset -> blackout:"
    )

    print(
        "    180 s"
    )

    print(
        "  reported Earthrise -> "
        "planned AOS:"
    )

    print(
        "    60 s"
    )

    print()
    print(
        "Flight Day 9:"
    )

    print(
        "  RTC2:"
    )

    print(
        "    "
        f"{rtc2.isoformat()}"
    )

    print(
        "  approximate return-link "
        "loss anchor:"
    )

    print(
        "    ~"
        f"{return_loss_anchor.isoformat()}"
    )

    print(
        "  separation:"
    )

    print(
        "    ~2.000 h"
    )

    print()
    print(
        "Precision guardrails:"
    )

    print(
        "  NSN-to-DSN handoff: "
        "SEQUENCE_ONLY"
    )

    print(
        "  emergency comm test: "
        "DATE_LEVEL"
    )

    print(
        "  live DSN reacquisition: "
        "SEQUENCE_ONLY"
    )

    print(
        "  return-link-loss anchor: "
        "APPROXIMATE"
    )

    print()
    print(
        "Products:"
    )

    print(
        "  timeline CSV rows: 16"
    )

    print(
        "  summary: PASS"
    )

    print(
        "  timeline figure: PASS"
    )

    print()
    print(
        "OK: Phase 2H.1 communications "
        "event identity, source precision, "
        "planned-versus-reported timing, "
        "mission-clock anchors, Phase 2G "
        "cross-checks, Flight Day 9 "
        "approximation guardrails, generated "
        "products, and non-invention rules "
        "independently validated."
    )


if __name__ == "__main__":
    main()
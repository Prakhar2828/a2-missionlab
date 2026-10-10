from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_operational_threads.json"
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

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "communications_operational_threads.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "communications_operational_threads_summary.json"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "communications"
    / "phase2h4_communications_operational_threads.svg"
)

EXPECTED_DATASET_ID = (
    "phase2h4_artemis_ii_communications_operational_threads"
)

EXPECTED_PRODUCT_ID = (
    "phase2h4_communications_operational_threads_analysis"
)

EXPECTED_THREAD_IDS = [
    "emergency_communications_readiness",
    "lunar_occultation_blackout_and_reacquisition",
    "flight_day_9_return_link_loss_and_recovery",
]


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


def parse_utc(value):
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


def check_close(
    label,
    observed,
    expected,
    tolerance=0.002,
):
    if abs(
        float(observed)
        - float(expected)
    ) > tolerance:
        fail(
            f"{label}: "
            f"{observed} != {expected}"
        )


def main() -> None:
    reference = load_json(
        REFERENCE_PATH
    )

    catalog = load_json(
        CATALOG_PATH
    )

    trajectory_events = load_json(
        TRAJECTORY_EVENTS_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    if (
        reference.get(
            "dataset_id"
        )
        != EXPECTED_DATASET_ID
    ):
        fail(
            "reference dataset ID mismatch"
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

    threads = (
        reference[
            "threads"
        ]
    )

    if len(threads) != 3:
        fail(
            "expected exactly three threads"
        )

    thread_ids = [
        thread[
            "thread_id"
        ]
        for thread in threads
    ]

    if thread_ids != EXPECTED_THREAD_IDS:
        fail(
            "thread identity or ordering changed"
        )

    threads_by_id = {
        thread[
            "thread_id"
        ]:
            thread
        for thread in threads
    }

    readiness = (
        threads_by_id[
            "emergency_communications_readiness"
        ]
    )

    lunar = (
        threads_by_id[
            "lunar_occultation_blackout_and_reacquisition"
        ]
    )

    anomaly = (
        threads_by_id[
            "flight_day_9_return_link_loss_and_recovery"
        ]
    )

    if (
        readiness[
            "classification"
        ]
        != "CONTINGENCY_READINESS"
        or readiness[
            "anomaly"
        ]
        is not False
    ):
        fail(
            "readiness thread classification mismatch"
        )

    if (
        lunar[
            "classification"
        ]
        != "EXPECTED_OPERATIONAL_CONSTRAINT"
        or lunar[
            "anomaly"
        ]
        is not False
    ):
        fail(
            "lunar blackout incorrectly classified"
        )

    if (
        anomaly[
            "classification"
        ]
        != "UNEXPECTED_COMMUNICATIONS_ANOMALY"
        or anomaly[
            "anomaly"
        ]
        is not True
    ):
        fail(
            "Flight Day 9 anomaly classification mismatch"
        )

    events = {
        event["id"]:
            event
        for event in catalog[
            "events"
        ]
    }

    trajectory = {
        event["id"]:
            event
        for event in trajectory_events
    }

    emergency = (
        events[
            "dsn_emergency_communications_test"
        ]
    )

    if (
        emergency[
            "precision"
        ]
        != "DATE_LEVEL"
    ):
        fail(
            "emergency communications test "
            "lost DATE_LEVEL precision"
        )

    planned_blackout = (
        events[
            "lunar_blackout_start_planned"
        ]
    )

    reported_blackout = (
        events[
            "lunar_blackout_start_reported"
        ]
    )

    planned_earthrise = (
        events[
            "lunar_earthrise_planned"
        ]
    )

    reported_earthrise = (
        events[
            "lunar_earthrise_reported"
        ]
    )

    planned_aos = (
        events[
            "dsn_reacquisition_planned"
        ]
    )

    live_aos = (
        events[
            "dsn_reacquisition_live_report"
        ]
    )

    planned_blackout_time = parse_utc(
        planned_blackout[
            "timestamp_utc"
        ]
    )

    reported_blackout_time = parse_utc(
        reported_blackout[
            "timestamp_utc"
        ]
    )

    planned_earthrise_time = parse_utc(
        planned_earthrise[
            "timestamp_utc"
        ]
    )

    reported_earthrise_time = parse_utc(
        reported_earthrise[
            "timestamp_utc"
        ]
    )

    planned_aos_time = parse_utc(
        planned_aos[
            "timestamp_utc"
        ]
    )

    expected_metrics = {
        "blackout_reported_minus_planned_seconds":
            (
                reported_blackout_time
                - planned_blackout_time
            ).total_seconds(),

        "earthrise_reported_minus_planned_seconds":
            (
                reported_earthrise_time
                - planned_earthrise_time
            ).total_seconds(),

        "planned_blackout_to_aos_seconds":
            (
                planned_aos_time
                - planned_blackout_time
            ).total_seconds(),

        "reported_blackout_to_earthrise_seconds":
            (
                reported_earthrise_time
                - reported_blackout_time
            ).total_seconds(),
    }

    if (
        expected_metrics[
            "blackout_reported_minus_planned_seconds"
        ]
        != 0.0
    ):
        fail(
            "blackout planned/reported delta changed"
        )

    if (
        expected_metrics[
            "earthrise_reported_minus_planned_seconds"
        ]
        != -60.0
    ):
        fail(
            "Earthrise planned/reported delta changed"
        )

    if (
        live_aos[
            "precision"
        ]
        != "SEQUENCE_ONLY"
        or live_aos[
            "timestamp_utc"
        ]
        is not None
        or live_aos[
            "approximate_anchor_utc"
        ]
        is not None
    ):
        fail(
            "live reacquisition gained invented timing"
        )

    if (
        live_aos[
            "ordering"
        ]
        != "MOMENTS_AFTER_REPORTED_EARTHRISE"
    ):
        fail(
            "live reacquisition ordering changed"
        )

    loss = (
        events[
            "unexpected_return_link_loss"
        ]
    )

    recovery = (
        events[
            "two_way_communications_reestablished"
        ]
    )

    rtc2 = (
        trajectory[
            "rtc2"
        ]
    )

    if (
        loss[
            "precision"
        ]
        != "APPROXIMATE"
        or loss.get(
            "anchor_is_not_exact"
        )
        is not True
    ):
        fail(
            "loss anchor precision guard failed"
        )

    if (
        recovery[
            "precision"
        ]
        != "SEQUENCE_ONLY"
        or recovery[
            "timestamp_utc"
        ]
        is not None
        or recovery[
            "approximate_anchor_utc"
        ]
        is not None
    ):
        fail(
            "recovery gained invented timing"
        )

    if (
        recovery[
            "ordering"
        ]
        != (
            "SHORTLY_AFTER_UNEXPECTED_"
            "RETURN_LINK_LOSS_BEFORE_RTC2"
        )
    ):
        fail(
            "recovery ordering changed"
        )

    loss_anchor = parse_utc(
        loss[
            "approximate_anchor_utc"
        ]
    )

    rtc2_time = parse_utc(
        rtc2[
            "timestamp_utc"
        ]
    )

    loss_to_rtc2 = (
        rtc2_time
        - loss_anchor
    ).total_seconds()

    if loss_to_rtc2 != 7200.0:
        fail(
            "Flight Day 9 anchor-to-RTC2 "
            "separation changed"
        )

    expected_metrics[
        "flight_day_9_loss_anchor_to_rtc2_seconds"
    ] = loss_to_rtc2

    if (
        anomaly[
            "context"
        ]
        != "DURING_DATA_RATE_CHANGE"
    ):
        fail(
            "anomaly context changed"
        )

    if (
        anomaly[
            "causal_relationship"
        ]
        != "NOT_ESTABLISHED"
    ):
        fail(
            "unsupported causal claim detected"
        )

    if (
        anomaly[
            "affected_direction_supported"
        ]
        != "RETURN_LINK"
    ):
        fail(
            "affected direction changed"
        )

    if (
        anomaly[
            "complete_two_way_outage_established"
        ]
        is not False
    ):
        fail(
            "unsupported complete two-way outage claim"
        )

    if (
        anomaly[
            "public_root_cause_available"
        ]
        is not False
    ):
        fail(
            "unsupported public root cause claim"
        )

    if (
        anomaly[
            "failed_subsystem_identified"
        ]
        is not False
    ):
        fail(
            "unsupported failed subsystem claim"
        )

    if (
        anomaly[
            "anomaly_duration_known"
        ]
        is not False
    ):
        fail(
            "unsupported anomaly duration claim"
        )

    sequence = (
        anomaly[
            "operational_sequence"
        ]
    )

    sequence_ids = [
        step[
            "step_id"
        ]
        for step in sequence
    ]

    if sequence_ids != [
        "unexpected_return_link_loss",
        "two_way_communications_reestablished",
        "burn_preparation_resumed",
        "rtc2",
    ]:
        fail(
            "Flight Day 9 operational sequence changed"
        )

    burn_prep = (
        sequence[2]
    )

    if (
        burn_prep[
            "precision"
        ]
        != "SEQUENCE_ONLY"
        or burn_prep[
            "timestamp_utc"
        ]
        is not None
    ):
        fail(
            "burn-preparation resumption gained "
            "unsupported timing"
        )

    boundary = (
        reference[
            "decision_evidence_boundary"
        ]
    )

    if (
        boundary[
            "public_event_sequence_available"
        ]
        is not True
    ):
        fail(
            "public event sequence should be available"
        )

    unavailable_fields = [
        "public_full_console_transcript_available",
        "public_flight_director_rationale_tree_available",
        "public_fault_isolation_sequence_available",
        "public_root_cause_analysis_available",
        "public_failed_subsystem_identification_available",
    ]

    for field in unavailable_fields:
        if (
            boundary[
                field
            ]
            is not False
        ):
            fail(
                f"{field} incorrectly marked available"
            )

    if not OUTPUT_CSV.exists():
        fail(
            "operational threads CSV missing"
        )

    with OUTPUT_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        rows = list(
            csv.DictReader(f)
        )

    if len(rows) != 3:
        fail(
            "operational threads CSV must "
            "contain three rows"
        )

    if [
        row[
            "thread_id"
        ]
        for row in rows
    ] != EXPECTED_THREAD_IDS:
        fail(
            "CSV thread ordering or identity changed"
        )

    anomaly_flags = [
        row[
            "anomaly"
        ]
        for row in rows
    ]

    if anomaly_flags != [
        "false",
        "false",
        "true",
    ]:
        fail(
            "CSV anomaly flags changed"
        )

    if (
        summary[
            "thread_count"
        ]
        != 3
    ):
        fail(
            "summary thread count mismatch"
        )

    if (
        summary[
            "anomaly_thread_count"
        ]
        != 1
    ):
        fail(
            "summary anomaly count mismatch"
        )

    if (
        summary[
            "non_anomaly_thread_count"
        ]
        != 2
    ):
        fail(
            "summary non-anomaly count mismatch"
        )

    if (
        summary[
            "thread_ids"
        ]
        != EXPECTED_THREAD_IDS
    ):
        fail(
            "summary thread identities changed"
        )

    observed_metrics = (
        summary[
            "derived_metrics"
        ]
    )

    for key, expected in (
        expected_metrics.items()
    ):
        if key not in observed_metrics:
            fail(
                f"missing metric: {key}"
            )

        check_close(
            key,
            observed_metrics[
                key
            ],
            expected,
        )

    flight_day_6 = (
        summary[
            "flight_day_6"
        ]
    )

    if (
        flight_day_6[
            "classification"
        ]
        != "EXPECTED_OPERATIONAL_CONSTRAINT"
        or flight_day_6[
            "anomaly"
        ]
        is not False
    ):
        fail(
            "summary Flight Day 6 classification changed"
        )

    if (
        flight_day_6[
            "live_reacquisition_precision"
        ]
        != "SEQUENCE_ONLY"
        or flight_day_6[
            "live_reacquisition_utc"
        ]
        is not None
    ):
        fail(
            "summary live reacquisition gained timing"
        )

    flight_day_9 = (
        summary[
            "flight_day_9"
        ]
    )

    if (
        flight_day_9[
            "classification"
        ]
        != "UNEXPECTED_COMMUNICATIONS_ANOMALY"
        or flight_day_9[
            "anomaly"
        ]
        is not True
    ):
        fail(
            "summary Flight Day 9 classification changed"
        )

    if (
        flight_day_9[
            "causal_relationship"
        ]
        != "NOT_ESTABLISHED"
    ):
        fail(
            "summary introduced unsupported causation"
        )

    if (
        flight_day_9[
            "recovery_utc"
        ]
        is not None
    ):
        fail(
            "summary invented recovery UTC"
        )

    if (
        summary[
            "decision_evidence_boundary"
        ]
        != boundary
    ):
        fail(
            "decision-evidence boundary mismatch"
        )

    if (
        summary[
            "guardrails"
        ]
        != reference[
            "guardrails"
        ]
    ):
        fail(
            "guardrails changed between "
            "reference and summary"
        )

    if not FIGURE_PATH.exists():
        fail(
            "operational threads figure missing"
        )

    svg = FIGURE_PATH.read_text(
        encoding="utf-8"
    )

    if (
        "<svg" not in svg
        or len(svg) < 1000
    ):
        fail(
            "operational threads SVG invalid"
        )

    print()
    print(
        "Phase 2H.4 Communications Operational Threads Validation"
    )

    print("=" * 70)

    print()
    print(
        "Threads:"
    )

    print(
        "  total: 3"
    )

    print(
        "  non-anomaly: 2"
    )

    print(
        "  anomaly: 1"
    )

    print()
    print(
        "Thread classifications:"
    )

    print(
        "  contingency readiness: PASS"
    )

    print(
        "  expected lunar constraint: PASS"
    )

    print(
        "  unexpected Flight Day 9 anomaly: PASS"
    )

    print()
    print(
        "Flight Day 6:"
    )

    print(
        "  reported - planned blackout:"
    )

    print(
        "    +0 s"
    )

    print(
        "  reported - planned Earthrise:"
    )

    print(
        "    -60 s"
    )

    print(
        "  planned blackout -> planned AOS:"
    )

    print(
        "    2460 s"
    )

    print(
        "    41.0 min"
    )

    print(
        "  reported blackout -> reported Earthrise:"
    )

    print(
        "    2400 s"
    )

    print(
        "    40.0 min"
    )

    print(
        "  live reacquisition:"
    )

    print(
        "    SEQUENCE_ONLY"
    )

    print(
        "    exact UTC: NONE"
    )

    print()
    print(
        "Flight Day 9:"
    )

    print(
        "  loss precision:"
    )

    print(
        "    APPROXIMATE"
    )

    print(
        "  loss anchor exact:"
    )

    print(
        "    FALSE"
    )

    print(
        "  causal relationship:"
    )

    print(
        "    NOT_ESTABLISHED"
    )

    print(
        "  supported affected direction:"
    )

    print(
        "    RETURN_LINK"
    )

    print(
        "  complete two-way outage established:"
    )

    print(
        "    FALSE"
    )

    print(
        "  recovery:"
    )

    print(
        "    SEQUENCE_ONLY"
    )

    print(
        "    exact UTC: NONE"
    )

    print(
        "  anomaly duration known:"
    )

    print(
        "    FALSE"
    )

    print(
        "  burn preparation resumed:"
    )

    print(
        "    TRUE"
    )

    print(
        "  approximate loss anchor -> RTC2:"
    )

    print(
        "    ~7200 s"
    )

    print(
        "    ~2.000 h"
    )

    print()
    print(
        "Decision-evidence boundary:"
    )

    print(
        "  public event sequence: TRUE"
    )

    print(
        "  full console transcript: FALSE"
    )

    print(
        "  Flight Director rationale tree: FALSE"
    )

    print(
        "  fault-isolation sequence: FALSE"
    )

    print(
        "  root-cause analysis: FALSE"
    )

    print(
        "  failed subsystem identification: FALSE"
    )

    print()
    print(
        "Products:"
    )

    print(
        "  operational threads CSV rows: 3"
    )

    print(
        "  summary: PASS"
    )

    print(
        "  operational threads figure: PASS"
    )

    print()
    print(
        "OK: Phase 2H.4 operational thread identity, "
        "expected-versus-unexpected classification, "
        "planned-versus-reported lunar blackout timing, "
        "sequence-only reacquisition and recovery precision, "
        "Flight Day 9 return-link anomaly semantics, "
        "non-causation guardrail, burn-preparation resumption, "
        "decision-evidence boundary, generated products, "
        "and non-invention rules independently validated."
    )


if __name__ == "__main__":
    main()
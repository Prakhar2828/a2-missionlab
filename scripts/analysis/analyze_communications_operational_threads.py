from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt


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

OUTPUT_SUMMARY = (
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


def parse_utc(value: str | None):
    if value is None:
        return None

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


def seconds_between(
    earlier: datetime,
    later: datetime,
) -> float:
    return (
        later - earlier
    ).total_seconds()


def build_figure(
    reference,
    metrics,
) -> None:
    FIGURE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(16, 9)
    )

    ax.set_xlim(
        0,
        1,
    )

    ax.set_ylim(
        0,
        1,
    )

    ax.axis(
        "off"
    )

    box = {
        "boxstyle":
            "round,pad=0.45",

        "fill":
            False,
    }

    ax.text(
        0.50,
        0.96,
        "Artemis II Communications Operational Threads",
        ha="center",
        va="center",
        fontsize=15,
    )

    # Thread 1
    ax.text(
        0.03,
        0.79,
        (
            "THREAD 1\n"
            "CONTINGENCY READINESS\n"
            "Anomaly: FALSE"
        ),
        ha="left",
        va="center",
        bbox=box,
        fontsize=9,
    )

    ax.text(
        0.29,
        0.79,
        (
            "Emergency communications\n"
            "system test\n"
            "2026-04-03\n"
            "DATE_LEVEL"
        ),
        ha="center",
        va="center",
        bbox=box,
        fontsize=9,
    )

    ax.text(
        0.62,
        0.79,
        (
            "Exact test time:\n"
            "NOT PUBLIC"
        ),
        ha="center",
        va="center",
        bbox=box,
        fontsize=9,
    )

    ax.annotate(
        "",
        xy=(0.50, 0.79),
        xytext=(0.39, 0.79),
        arrowprops={
            "arrowstyle":
                "->",
        },
    )

    # Thread 2
    ax.text(
        0.03,
        0.52,
        (
            "THREAD 2\n"
            "EXPECTED LUNAR\n"
            "COMM CONSTRAINT\n"
            "Anomaly: FALSE"
        ),
        ha="left",
        va="center",
        bbox=box,
        fontsize=9,
    )

    thread2_boxes = [
        (
            0.25,
            "Planned blackout\n22:44 UTC"
        ),
        (
            0.40,
            "Reported blackout\n22:44 UTC"
        ),
        (
            0.55,
            "Reported Earthrise\n23:24 UTC"
        ),
        (
            0.70,
            "Planned AOS\n23:25 UTC"
        ),
        (
            0.86,
            (
                "Live reacquisition\n"
                "SEQUENCE_ONLY\n"
                "moments after Earthrise"
            ),
        ),
    ]

    for x, label in thread2_boxes:
        ax.text(
            x,
            0.52,
            label,
            ha="center",
            va="center",
            bbox=box,
            fontsize=8,
        )

    for left, right in zip(
        thread2_boxes[:-1],
        thread2_boxes[1:],
    ):
        ax.annotate(
            "",
            xy=(
                right[0] - 0.055,
                0.52,
            ),
            xytext=(
                left[0] + 0.055,
                0.52,
            ),
            arrowprops={
                "arrowstyle":
                    "->",
            },
        )

    ax.text(
        0.50,
        0.40,
        (
            "Planned blackout-to-AOS: "
            f"{metrics['planned_blackout_to_aos_seconds'] / 60.0:.1f} min"
            "    |    "
            "Reported blackout-to-Earthrise: "
            f"{metrics['reported_blackout_to_earthrise_seconds'] / 60.0:.1f} min"
            "    |    "
            "Earthrise reported 1 min earlier than planned"
        ),
        ha="center",
        va="center",
        fontsize=8,
    )

    # Thread 3
    ax.text(
        0.03,
        0.20,
        (
            "THREAD 3\n"
            "UNEXPECTED RETURN-LINK\n"
            "COMMUNICATIONS ANOMALY\n"
            "Anomaly: TRUE"
        ),
        ha="left",
        va="center",
        bbox=box,
        fontsize=9,
    )

    thread3_boxes = [
        (
            0.27,
            (
                "Return-link LOS\n"
                "~00:53 UTC anchor\n"
                "APPROXIMATE"
            ),
        ),
        (
            0.47,
            (
                "Two-way comm restored\n"
                "SEQUENCE_ONLY"
            ),
        ),
        (
            0.66,
            (
                "Burn prep resumed\n"
                "SEQUENCE_ONLY"
            ),
        ),
        (
            0.84,
            (
                "RTC2\n"
                "02:53 UTC"
            ),
        ),
    ]

    for x, label in thread3_boxes:
        ax.text(
            x,
            0.20,
            label,
            ha="center",
            va="center",
            bbox=box,
            fontsize=8,
        )

    for left, right in zip(
        thread3_boxes[:-1],
        thread3_boxes[1:],
    ):
        ax.annotate(
            "",
            xy=(
                right[0] - 0.06,
                0.20,
            ),
            xytext=(
                left[0] + 0.06,
                0.20,
            ),
            arrowprops={
                "arrowstyle":
                    "->",
            },
        )

    ax.text(
        0.52,
        0.08,
        (
            "Not to scale. Sequence-only steps receive no invented timestamps. "
            "The ~00:53 UTC value is an approximate RTC2-minus-two-hours anchor, "
            "not an observed LOS time. 'During a data-rate change' is context, "
            "not a causal finding."
        ),
        ha="center",
        va="center",
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
    reference = load_json(
        REFERENCE_PATH
    )

    catalog = load_json(
        CATALOG_PATH
    )

    trajectory_events = load_json(
        TRAJECTORY_EVENTS_PATH
    )

    if (
        reference.get(
            "dataset_id"
        )
        != (
            "phase2h4_artemis_ii_"
            "communications_operational_threads"
        )
    ):
        fail(
            "Unexpected Phase 2H.4 dataset ID."
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

    required_event_ids = {
        "dsn_emergency_communications_test",
        "lunar_blackout_start_planned",
        "lunar_blackout_start_reported",
        "lunar_earthrise_planned",
        "lunar_earthrise_reported",
        "dsn_reacquisition_planned",
        "dsn_reacquisition_live_report",
        "unexpected_return_link_loss",
        "two_way_communications_reestablished",
    }

    missing = (
        required_event_ids
        - set(events)
    )

    if missing:
        fail(
            "Missing communications events: "
            f"{sorted(missing)}"
        )

    if "rtc2" not in trajectory:
        fail(
            "Missing RTC2 trajectory event."
        )

    threads = (
        reference[
            "threads"
        ]
    )

    if len(threads) != 3:
        fail(
            "Expected exactly three "
            "communications operational threads."
        )

    threads_by_id = {
        thread[
            "thread_id"
        ]:
            thread
        for thread in threads
    }

    expected_thread_ids = {
        "emergency_communications_readiness",
        "lunar_occultation_blackout_and_reacquisition",
        "flight_day_9_return_link_loss_and_recovery",
    }

    if set(
        threads_by_id
    ) != expected_thread_ids:
        fail(
            "Unexpected operational thread set."
        )

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
            "Emergency communications readiness "
            "thread classification changed."
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
            "Lunar blackout must remain an "
            "expected non-anomaly constraint."
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
            "Flight Day 9 thread must remain "
            "an unexpected communications anomaly."
        )

    emergency_test = (
        events[
            "dsn_emergency_communications_test"
        ]
    )

    if (
        emergency_test[
            "precision"
        ]
        != "DATE_LEVEL"
    ):
        fail(
            "Emergency communications test "
            "must remain DATE_LEVEL."
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

    minute_events = [
        planned_blackout,
        reported_blackout,
        planned_earthrise,
        reported_earthrise,
        planned_aos,
    ]

    for event in minute_events:
        if (
            event[
                "precision"
            ]
            != "MINUTE_LEVEL"
        ):
            fail(
                f"{event['id']} lost "
                "MINUTE_LEVEL precision."
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
            "Live DSN reacquisition gained "
            "unsupported timing precision."
        )

    if (
        live_aos[
            "ordering"
        ]
        != (
            "MOMENTS_AFTER_"
            "REPORTED_EARTHRISE"
        )
    ):
        fail(
            "Live DSN reacquisition "
            "ordering changed."
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

    blackout_plan_delta = seconds_between(
        planned_blackout_time,
        reported_blackout_time,
    )

    earthrise_plan_delta = seconds_between(
        planned_earthrise_time,
        reported_earthrise_time,
    )

    planned_blackout_to_aos = seconds_between(
        planned_blackout_time,
        planned_aos_time,
    )

    reported_blackout_to_earthrise = seconds_between(
        reported_blackout_time,
        reported_earthrise_time,
    )

    if blackout_plan_delta != 0.0:
        fail(
            "Reported blackout minute no longer "
            "matches planned blackout minute."
        )

    if earthrise_plan_delta != -60.0:
        fail(
            "Reported Earthrise must remain "
            "one minute earlier than planned."
        )

    if planned_blackout_to_aos != 2460.0:
        fail(
            "Planned blackout-to-AOS "
            "window changed."
        )

    if reported_blackout_to_earthrise != 2400.0:
        fail(
            "Reported blackout-to-Earthrise "
            "separation changed."
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
            "Flight Day 9 LOS anchor "
            "precision changed."
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
            "Flight Day 9 recovery gained "
            "unsupported timing precision."
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
            "Flight Day 9 recovery "
            "ordering changed."
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

    loss_to_rtc2 = seconds_between(
        loss_anchor,
        rtc2_time,
    )

    if loss_to_rtc2 != 7200.0:
        fail(
            "Approximate Flight Day 9 LOS "
            "anchor must remain two hours "
            "before RTC2."
        )

    if (
        anomaly[
            "context"
        ]
        != "DURING_DATA_RATE_CHANGE"
    ):
        fail(
            "Flight Day 9 context changed."
        )

    if (
        anomaly[
            "causal_relationship"
        ]
        != "NOT_ESTABLISHED"
    ):
        fail(
            "Unsupported Flight Day 9 "
            "causation was introduced."
        )

    if (
        anomaly[
            "affected_direction_supported"
        ]
        != "RETURN_LINK"
    ):
        fail(
            "Supported anomaly direction changed."
        )

    if (
        anomaly[
            "complete_two_way_outage_established"
        ]
        is not False
    ):
        fail(
            "Complete two-way outage was "
            "incorrectly asserted."
        )

    if (
        anomaly[
            "anomaly_duration_known"
        ]
        is not False
    ):
        fail(
            "Anomaly duration was "
            "incorrectly marked known."
        )

    burn_prep_steps = [
        step
        for step in anomaly[
            "operational_sequence"
        ]
        if step[
            "step_id"
        ] == "burn_preparation_resumed"
    ]

    if len(
        burn_prep_steps
    ) != 1:
        fail(
            "Expected exactly one burn-preparation "
            "resumption step."
        )

    burn_prep = (
        burn_prep_steps[0]
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
            "Burn-preparation resumption "
            "gained unsupported timestamp precision."
        )

    decision_boundary = (
        reference[
            "decision_evidence_boundary"
        ]
    )

    false_boundary_keys = [
        "public_full_console_transcript_available",
        "public_flight_director_rationale_tree_available",
        "public_fault_isolation_sequence_available",
        "public_root_cause_analysis_available",
        "public_failed_subsystem_identification_available",
    ]

    for key in false_boundary_keys:
        if (
            decision_boundary[
                key
            ]
            is not False
        ):
            fail(
                f"Decision evidence boundary "
                f"changed for {key}."
            )

    anomaly_count = sum(
        1
        for thread in threads
        if thread[
            "anomaly"
        ]
    )

    non_anomaly_count = (
        len(threads)
        - anomaly_count
    )

    class_counts = Counter(
        thread[
            "classification"
        ]
        for thread in threads
    )

    metrics = {
        "blackout_reported_minus_planned_seconds":
            blackout_plan_delta,

        "earthrise_reported_minus_planned_seconds":
            earthrise_plan_delta,

        "planned_blackout_to_aos_seconds":
            planned_blackout_to_aos,

        "reported_blackout_to_earthrise_seconds":
            reported_blackout_to_earthrise,

        "flight_day_9_loss_anchor_to_rtc2_seconds":
            loss_to_rtc2,
    }

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "thread_id",
        "name",
        "classification",
        "expectedness",
        "anomaly",
        "precision_pattern",
        "primary_source_id",
        "public_decision_rationale_available",
        "public_console_log_available",
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

        for thread in threads:
            writer.writerow(
                {
                    "thread_id":
                        thread[
                            "thread_id"
                        ],

                    "name":
                        thread[
                            "name"
                        ],

                    "classification":
                        thread[
                            "classification"
                        ],

                    "expectedness":
                        thread[
                            "expectedness"
                        ],

                    "anomaly":
                        str(
                            thread[
                                "anomaly"
                            ]
                        ).lower(),

                    "precision_pattern":
                        thread[
                            "precision_pattern"
                        ],

                    "primary_source_id":
                        thread[
                            "primary_source_id"
                        ],

                    "public_decision_rationale_available":
                        str(
                            thread[
                                "public_decision_rationale_available"
                            ]
                        ).lower(),

                    "public_console_log_available":
                        str(
                            thread[
                                "public_console_log_available"
                            ]
                        ).lower(),
                }
            )

    build_figure(
        reference,
        metrics,
    )

    summary = {
        "product_id":
            (
                "phase2h4_communications_"
                "operational_threads_analysis"
            ),

        "mission":
            "Artemis II",

        "reference_dataset_id":
            reference[
                "dataset_id"
            ],

        "thread_count":
            len(threads),

        "anomaly_thread_count":
            anomaly_count,

        "non_anomaly_thread_count":
            non_anomaly_count,

        "classification_counts":
            dict(
                class_counts
            ),

        "thread_ids": [
            thread[
                "thread_id"
            ]
            for thread in threads
        ],

        "derived_metrics":
            metrics,

        "flight_day_6": {
            "classification":
                lunar[
                    "classification"
                ],

            "anomaly":
                False,

            "planned_blackout_utc":
                planned_blackout[
                    "timestamp_utc"
                ],

            "reported_blackout_utc":
                reported_blackout[
                    "timestamp_utc"
                ],

            "planned_earthrise_utc":
                planned_earthrise[
                    "timestamp_utc"
                ],

            "reported_earthrise_utc":
                reported_earthrise[
                    "timestamp_utc"
                ],

            "planned_reacquisition_utc":
                planned_aos[
                    "timestamp_utc"
                ],

            "live_reacquisition_precision":
                live_aos[
                    "precision"
                ],

            "live_reacquisition_ordering":
                live_aos[
                    "ordering"
                ],

            "live_reacquisition_utc":
                None,
        },

        "flight_day_9": {
            "classification":
                anomaly[
                    "classification"
                ],

            "anomaly":
                True,

            "loss_precision":
                loss[
                    "precision"
                ],

            "loss_approximate_anchor_utc":
                loss[
                    "approximate_anchor_utc"
                ],

            "loss_anchor_exact":
                False,

            "context":
                anomaly[
                    "context"
                ],

            "causal_relationship":
                anomaly[
                    "causal_relationship"
                ],

            "affected_direction_supported":
                anomaly[
                    "affected_direction_supported"
                ],

            "complete_two_way_outage_established":
                False,

            "recovery_precision":
                recovery[
                    "precision"
                ],

            "recovery_ordering":
                recovery[
                    "ordering"
                ],

            "recovery_utc":
                None,

            "anomaly_duration_known":
                False,

            "burn_preparation_resumed":
                True,

            "burn_preparation_precision":
                "SEQUENCE_ONLY",

            "rtc2_utc":
                rtc2[
                    "timestamp_utc"
                ],
        },

        "decision_evidence_boundary":
            decision_boundary,

        "guardrails":
            reference[
                "guardrails"
            ],

        "outputs": {
            "threads_csv":
                str(
                    OUTPUT_CSV.relative_to(
                        ROOT
                    )
                ),

            "operational_threads_figure":
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
        "Phase 2H.4 Communications Operational Threads Analysis"
    )

    print("=" * 65)

    print()
    print(
        "Operational threads:"
    )

    print(
        f"  total: {len(threads)}"
    )

    print(
        f"  anomaly: {anomaly_count}"
    )

    print(
        f"  non-anomaly: {non_anomaly_count}"
    )

    print()
    print(
        "Classifications:"
    )

    for classification in [
        "CONTINGENCY_READINESS",
        "EXPECTED_OPERATIONAL_CONSTRAINT",
        "UNEXPECTED_COMMUNICATIONS_ANOMALY",
    ]:
        print(
            f"  {classification}: "
            f"{class_counts.get(classification, 0)}"
        )

    print()
    print(
        "Thread 1 - Emergency communications readiness:"
    )

    print(
        "  classification:"
    )

    print(
        "    CONTINGENCY_READINESS"
    )

    print(
        "  anomaly:"
    )

    print(
        "    FALSE"
    )

    print(
        "  test date:"
    )

    print(
        "    "
        f"{emergency_test['date_utc']}"
    )

    print(
        "  precision:"
    )

    print(
        "    DATE_LEVEL"
    )

    print()
    print(
        "Thread 2 - Lunar blackout and reacquisition:"
    )

    print(
        "  classification:"
    )

    print(
        "    EXPECTED_OPERATIONAL_CONSTRAINT"
    )

    print(
        "  anomaly:"
    )

    print(
        "    FALSE"
    )

    print(
        "  reported - planned blackout:"
    )

    print(
        f"    {blackout_plan_delta:+.0f} s"
    )

    print(
        "  reported - planned Earthrise:"
    )

    print(
        f"    {earthrise_plan_delta:+.0f} s"
    )

    print(
        "  planned blackout -> planned AOS:"
    )

    print(
        f"    {planned_blackout_to_aos:.0f} s"
    )

    print(
        f"    {planned_blackout_to_aos / 60.0:.1f} min"
    )

    print(
        "  reported blackout -> reported Earthrise:"
    )

    print(
        f"    {reported_blackout_to_earthrise:.0f} s"
    )

    print(
        f"    {reported_blackout_to_earthrise / 60.0:.1f} min"
    )

    print(
        "  live reacquisition:"
    )

    print(
        "    SEQUENCE_ONLY"
    )

    print(
        "    MOMENTS_AFTER_REPORTED_EARTHRISE"
    )

    print(
        "    exact UTC: NONE"
    )

    print()
    print(
        "Thread 3 - Flight Day 9 return-link anomaly:"
    )

    print(
        "  classification:"
    )

    print(
        "    UNEXPECTED_COMMUNICATIONS_ANOMALY"
    )

    print(
        "  anomaly:"
    )

    print(
        "    TRUE"
    )

    print(
        "  loss precision:"
    )

    print(
        "    APPROXIMATE"
    )

    print(
        "  approximate anchor:"
    )

    print(
        "    ~"
        f"{loss['approximate_anchor_utc']}"
    )

    print(
        "  cause established:"
    )

    print(
        "    FALSE"
    )

    print(
        "  affected direction:"
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
        "  recovery precision:"
    )

    print(
        "    SEQUENCE_ONLY"
    )

    print(
        "  anomaly duration:"
    )

    print(
        "    UNKNOWN"
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
        f"    ~{loss_to_rtc2:.0f} s"
    )

    print(
        f"    ~{loss_to_rtc2 / 3600.0:.3f} h"
    )

    print()
    print(
        "Decision-evidence boundary:"
    )

    print(
        "  public event sequence:"
    )

    print(
        "    TRUE"
    )

    print(
        "  full console transcript:"
    )

    print(
        "    FALSE"
    )

    print(
        "  Flight Director rationale tree:"
    )

    print(
        "    FALSE"
    )

    print(
        "  fault-isolation sequence:"
    )

    print(
        "    FALSE"
    )

    print(
        "  root-cause analysis:"
    )

    print(
        "    FALSE"
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
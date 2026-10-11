from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_plan_execution.json"
)

TRAJECTORY_EVENTS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "trajectory_events.json"
)

COMMUNICATIONS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_event_catalog.json"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "maneuver_plan_execution.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "maneuver_plan_execution_summary.json"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "maneuvers"
    / "phase2i1_maneuver_plan_execution.svg"
)

EXPECTED_DATASET_ID = (
    "phase2i1_artemis_ii_maneuver_plan_execution"
)

EXPECTED_PRODUCT_ID = (
    "phase2i1_maneuver_plan_execution_analysis"
)

EXPECTED_IDS = [
    "otc1",
    "otc2",
    "otc3",
    "rtc1",
    "rtc2",
    "rtc3",
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


def check_close(
    label,
    observed,
    expected,
    tolerance=1e-9,
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

    trajectory_events = load_json(
        TRAJECTORY_EVENTS_PATH
    )

    communications = load_json(
        COMMUNICATIONS_PATH
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

    maneuvers = (
        reference[
            "maneuvers"
        ]
    )

    if len(maneuvers) != 6:
        fail(
            "expected six maneuver records"
        )

    ids = [
        maneuver[
            "maneuver_id"
        ]
        for maneuver in maneuvers
    ]

    if ids != EXPECTED_IDS:
        fail(
            "maneuver identity or order changed"
        )

    by_id = {
        maneuver[
            "maneuver_id"
        ]:
            maneuver
        for maneuver in maneuvers
    }

    expected_statuses = {
        "otc1": "CANCELLED",
        "otc2": "CANCELLED",
        "otc3": "EXECUTED",
        "rtc1": "EXECUTED",
        "rtc2": "EXECUTED",
        "rtc3": "EXECUTED",
    }

    for maneuver_id, expected_status in (
        expected_statuses.items()
    ):
        maneuver = (
            by_id[
                maneuver_id
            ]
        )

        if (
            maneuver[
                "status"
            ]
            != expected_status
        ):
            fail(
                f"{maneuver_id} status changed"
            )

        expected_executed = (
            expected_status
            == "EXECUTED"
        )

        if (
            maneuver[
                "executed"
            ]
            is not expected_executed
        ):
            fail(
                f"{maneuver_id} execution flag changed"
            )

    # --------------------------------------------------------
    # OTC1 planned / cancelled separation
    # --------------------------------------------------------

    otc1 = (
        by_id[
            "otc1"
        ]
    )

    if (
        otc1[
            "plan"
        ][
            "planned_timestamp_utc"
        ]
        != "2026-04-03T22:49:00Z"
    ):
        fail(
            "OTC1 planned UTC changed"
        )

    if (
        otc1[
            "plan"
        ][
            "duration_relation"
        ]
        != "APPROXIMATELY"
    ):
        fail(
            "OTC1 planned duration "
            "lost approximate semantics"
        )

    check_close(
        "OTC1 planned duration",
        otc1[
            "plan"
        ][
            "planned_duration_seconds"
        ],
        8.0,
    )

    check_close(
        "OTC1 planned delta-v",
        otc1[
            "plan"
        ][
            "planned_delta_v_ft_s"
        ],
        0.7,
    )

    if (
        otc1[
            "executed"
        ]
        is not False
    ):
        fail(
            "OTC1 incorrectly marked executed"
        )

    if (
        otc1[
            "executed_delta_v_ft_s"
        ]
        is not None
    ):
        fail(
            "OTC1 gained executed delta-v"
        )

    if (
        otc1[
            "decision"
        ][
            "exact_decision_timestamp_known"
        ]
        is not False
    ):
        fail(
            "OTC1 gained exact cancellation UTC"
        )

    # --------------------------------------------------------
    # OTC2
    # --------------------------------------------------------

    otc2 = (
        by_id[
            "otc2"
        ]
    )

    if (
        otc2[
            "plan"
        ][
            "timestamp_precision"
        ]
        != "DATE_LEVEL"
    ):
        fail(
            "OTC2 planning precision changed"
        )

    if (
        otc2[
            "decision"
        ][
            "exact_decision_timestamp_known"
        ]
        is not False
    ):
        fail(
            "OTC2 gained exact cancellation UTC"
        )

    if (
        otc2[
            "decision"
        ][
            "reason_classification"
        ]
        != "TRAJECTORY_REMAINED_ON_TRACK"
    ):
        fail(
            "OTC2 cancellation reason changed"
        )

    # --------------------------------------------------------
    # Executed values
    # --------------------------------------------------------

    trajectory = {
        event[
            "id"
        ]:
            event
        for event in trajectory_events
    }

    expected_execution = {
        "otc3": (
            "2026-04-06T03:03:00Z",
            17.5,
            None,
        ),
        "rtc1": (
            "2026-04-08T00:03:00Z",
            15.0,
            1.6,
        ),
        "rtc2": (
            "2026-04-10T02:53:00Z",
            9.0,
            5.3,
        ),
        "rtc3": (
            "2026-04-10T18:53:00Z",
            8.0,
            4.2,
        ),
    }

    for maneuver_id, values in (
        expected_execution.items()
    ):
        timestamp, duration, delta_v = (
            values
        )

        execution = (
            by_id[
                maneuver_id
            ][
                "execution"
            ]
        )

        phase1_event = (
            trajectory[
                maneuver_id
            ]
        )

        if (
            execution[
                "timestamp_utc"
            ]
            != timestamp
        ):
            fail(
                f"{maneuver_id} reference UTC changed"
            )

        if (
            phase1_event[
                "timestamp_utc"
            ]
            != timestamp
        ):
            fail(
                f"{maneuver_id} Phase 1 UTC changed"
            )

        check_close(
            f"{maneuver_id} reference duration",
            execution[
                "duration_seconds"
            ],
            duration,
        )

        check_close(
            f"{maneuver_id} Phase 1 duration",
            phase1_event[
                "duration_seconds"
            ],
            duration,
        )

        reference_dv = (
            execution.get(
                "reported_delta_v_ft_s"
            )
        )

        phase1_dv = (
            phase1_event.get(
                "delta_v_ft_s"
            )
        )

        if delta_v is None:
            if (
                reference_dv is not None
                or phase1_dv is not None
            ):
                fail(
                    f"{maneuver_id} gained "
                    "unsupported delta-v"
                )

        else:
            check_close(
                f"{maneuver_id} reference delta-v",
                reference_dv,
                delta_v,
            )

            check_close(
                f"{maneuver_id} Phase 1 delta-v",
                phase1_dv,
                delta_v,
            )

    # --------------------------------------------------------
    # Independent aggregates
    # --------------------------------------------------------

    outbound = [
        maneuver
        for maneuver in maneuvers
        if maneuver[
            "leg"
        ] == "OUTBOUND"
    ]

    returns = [
        maneuver
        for maneuver in maneuvers
        if maneuver[
            "leg"
        ] == "RETURN"
    ]

    outbound_planned = sum(
        maneuver[
            "planned"
        ]
        for maneuver in outbound
    )

    outbound_cancelled = sum(
        maneuver[
            "status"
        ] == "CANCELLED"
        for maneuver in outbound
    )

    outbound_executed = sum(
        maneuver[
            "status"
        ] == "EXECUTED"
        for maneuver in outbound
    )

    cancellation_fraction = (
        outbound_cancelled
        / outbound_planned
    )

    return_executed = sum(
        maneuver[
            "status"
        ] == "EXECUTED"
        for maneuver in returns
    )

    return_duration = sum(
        float(
            maneuver[
                "execution"
            ][
                "duration_seconds"
            ]
        )
        for maneuver in returns
    )

    return_scalar_dv_ft_s = sum(
        float(
            maneuver[
                "execution"
            ][
                "reported_delta_v_ft_s"
            ]
        )
        for maneuver in returns
    )

    return_scalar_dv_m_s = (
        return_scalar_dv_ft_s
        * 0.3048
    )

    all_executed_duration = sum(
        float(
            maneuver[
                "execution"
            ][
                "duration_seconds"
            ]
        )
        for maneuver in maneuvers
        if maneuver[
            "status"
        ] == "EXECUTED"
    )

    if outbound_planned != 3:
        fail(
            "outbound planned count changed"
        )

    if outbound_cancelled != 2:
        fail(
            "outbound cancelled count changed"
        )

    if outbound_executed != 1:
        fail(
            "outbound executed count changed"
        )

    if return_executed != 3:
        fail(
            "return executed count changed"
        )

    check_close(
        "outbound cancellation fraction",
        cancellation_fraction,
        2.0 / 3.0,
    )

    check_close(
        "return duration",
        return_duration,
        32.0,
    )

    check_close(
        "return scalar delta-v ft/s",
        return_scalar_dv_ft_s,
        11.1,
    )

    check_close(
        "return scalar delta-v m/s",
        return_scalar_dv_m_s,
        3.38328,
    )

    check_close(
        "all executed correction duration",
        all_executed_duration,
        49.5,
    )

    # --------------------------------------------------------
    # RTC2 communications context
    # --------------------------------------------------------

    comms = {
        event[
            "id"
        ]:
            event
        for event in communications[
            "events"
        ]
    }

    loss = (
        comms[
            "unexpected_return_link_loss"
        ]
    )

    recovery = (
        comms[
            "two_way_communications_reestablished"
        ]
    )

    if (
        loss[
            "precision"
        ]
        != "APPROXIMATE"
    ):
        fail(
            "RTC2 preburn loss precision changed"
        )

    if (
        recovery[
            "precision"
        ]
        != "SEQUENCE_ONLY"
    ):
        fail(
            "RTC2 recovery precision changed"
        )

    if (
        by_id[
            "rtc2"
        ][
            "communications_context"
        ][
            "anomaly_caused_burn_failure"
        ]
        is not False
    ):
        fail(
            "communications anomaly incorrectly "
            "marked as RTC2 failure"
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    if (
        summary[
            "maneuver_count"
        ]
        != 6
    ):
        fail(
            "summary maneuver count changed"
        )

    if (
        summary[
            "status_counts"
        ][
            "CANCELLED"
        ]
        != 2
        or summary[
            "status_counts"
        ][
            "EXECUTED"
        ]
        != 4
    ):
        fail(
            "summary status counts changed"
        )

    check_close(
        "summary cancellation fraction",
        summary[
            "outbound"
        ][
            "cancellation_fraction"
        ],
        2.0 / 3.0,
    )

    check_close(
        "summary cancellation percent",
        summary[
            "outbound"
        ][
            "cancellation_percent"
        ],
        200.0 / 3.0,
    )

    check_close(
        "summary return duration",
        summary[
            "return"
        ][
            "combined_burn_duration_seconds"
        ],
        32.0,
    )

    check_close(
        "summary scalar delta-v ft/s",
        summary[
            "return"
        ][
            "scalar_sum_reported_delta_v_ft_s"
        ],
        11.1,
    )

    check_close(
        "summary scalar delta-v m/s",
        summary[
            "return"
        ][
            "scalar_sum_reported_delta_v_m_s"
        ],
        3.38328,
    )

    if (
        summary[
            "return"
        ][
            "net_vector_delta_v_computed"
        ]
        is not False
    ):
        fail(
            "net vector delta-v incorrectly computed"
        )

    if (
        summary[
            "all_executed_corrections"
        ][
            "combined_delta_v_computed"
        ]
        is not False
    ):
        fail(
            "all-correction delta-v incorrectly computed"
        )

    check_close(
        "summary known firing duration",
        summary[
            "all_executed_corrections"
        ][
            "known_combined_burn_duration_seconds"
        ],
        49.5,
    )

    if (
        summary[
            "rtc2_cross_phase_context"
        ][
            "communications_anomaly_implied_burn_failure"
        ]
        is not False
    ):
        fail(
            "summary incorrectly links anomaly "
            "to burn failure"
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
            "summary guardrails changed"
        )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    if not OUTPUT_CSV.exists():
        fail(
            "maneuver CSV missing"
        )

    with OUTPUT_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        rows = list(
            csv.DictReader(f)
        )

    if len(rows) != 6:
        fail(
            "maneuver CSV must contain six rows"
        )

    if [
        row[
            "maneuver_id"
        ]
        for row in rows
    ] != EXPECTED_IDS:
        fail(
            "maneuver CSV identities changed"
        )

    rows_by_id = {
        row[
            "maneuver_id"
        ]:
            row
        for row in rows
    }

    if (
        rows_by_id[
            "otc1"
        ][
            "status"
        ]
        != "CANCELLED"
    ):
        fail(
            "CSV OTC1 status changed"
        )

    if (
        rows_by_id[
            "otc1"
        ][
            "delta_v_semantics"
        ]
        != "PLANNED_VELOCITY_CHANGE"
    ):
        fail(
            "CSV OTC1 planned delta-v "
            "semantics changed"
        )

    if (
        rows_by_id[
            "otc3"
        ][
            "delta_v_ft_s"
        ]
        != ""
    ):
        fail(
            "CSV OTC3 gained delta-v"
        )

    if (
        rows_by_id[
            "otc3"
        ][
            "delta_v_semantics"
        ]
        != "NOT_PUBLICLY_REPORTED"
    ):
        fail(
            "CSV OTC3 missing-value "
            "semantics changed"
        )

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    if not FIGURE_PATH.exists():
        fail(
            "maneuver plan/execution figure missing"
        )

    svg = FIGURE_PATH.read_text(
        encoding="utf-8"
    )

    if (
        "<svg" not in svg
        or len(svg) < 1000
    ):
        fail(
            "maneuver plan/execution SVG invalid"
        )

    print()
    print(
        "Phase 2I.1 Maneuver Plan / Execution Validation"
    )

    print("=" * 62)

    print()
    print(
        "Maneuvers:"
    )

    print(
        "  total: 6"
    )

    print(
        "  executed: 4"
    )

    print(
        "  cancelled: 2"
    )

    print()
    print(
        "Outbound:"
    )

    print(
        "  planned: 3"
    )

    print(
        "  cancelled: 2"
    )

    print(
        "  executed: 1"
    )

    print(
        "  cancellation fraction:"
    )

    print(
        "    0.666667"
    )

    print(
        "    66.667%"
    )

    print()
    print(
        "OTC1:"
    )

    print(
        "  planned duration:"
    )

    print(
        "    ~8 s"
    )

    print(
        "  planned delta-v:"
    )

    print(
        "    0.7 ft/s"
    )

    print(
        "  executed:"
    )

    print(
        "    FALSE"
    )

    print(
        "  exact cancellation UTC:"
    )

    print(
        "    NONE"
    )

    print()
    print(
        "OTC2:"
    )

    print(
        "  executed:"
    )

    print(
        "    FALSE"
    )

    print(
        "  exact cancellation UTC:"
    )

    print(
        "    NONE"
    )

    print()
    print(
        "OTC3:"
    )

    print(
        "  executed:"
    )

    print(
        "    TRUE"
    )

    print(
        "  duration:"
    )

    print(
        "    17.5 s"
    )

    print(
        "  public delta-v:"
    )

    print(
        "    NONE"
    )

    print()
    print(
        "Return:"
    )

    print(
        "  executed: 3 of 3"
    )

    print(
        "  combined firing time:"
    )

    print(
        "    32.0 s"
    )

    print(
        "  scalar delta-v magnitude sum:"
    )

    print(
        "    11.1 ft/s"
    )

    print(
        "    3.38328 m/s"
    )

    print(
        "  net vector delta-v:"
    )

    print(
        "    NOT COMPUTED"
    )

    print()
    print(
        "All executed corrections:"
    )

    print(
        "  known firing time:"
    )

    print(
        "    49.5 s"
    )

    print(
        "  combined delta-v:"
    )

    print(
        "    NOT COMPUTED"
    )

    print()
    print(
        "RTC2 cross-phase context:"
    )

    print(
        "  communications loss: APPROXIMATE"
    )

    print(
        "  communications recovery: SEQUENCE_ONLY"
    )

    print(
        "  RTC2 executed afterward: TRUE"
    )

    print(
        "  burn failure inferred: FALSE"
    )

    print()
    print(
        "Propulsion assignment boundary:"
    )

    print(
        "  OTC3 engine assignment: UNRESOLVED"
    )

    print(
        "  RTC1 engine assignment: UNRESOLVED"
    )

    print(
        "  RTC2 engine assignment: UNRESOLVED"
    )

    print(
        "  RTC3 engine assignment: UNRESOLVED"
    )

    print()
    print(
        "Products:"
    )

    print(
        "  maneuver CSV rows: 6"
    )

    print(
        "  summary: PASS"
    )

    print(
        "  plan/execution figure: PASS"
    )

    print()
    print(
        "OK: Phase 2I.1 maneuver identity, planned-versus-"
        "executed semantics, outbound cancellation decisions, "
        "Phase 1 executed-burn cross-checks, return-burn "
        "aggregates, scalar-versus-vector delta-v boundary, "
        "RTC2 communications context, missing-value semantics, "
        "propulsion-assignment boundary, generated products, "
        "and cancellation guardrails independently validated."
    )


if __name__ == "__main__":
    main()
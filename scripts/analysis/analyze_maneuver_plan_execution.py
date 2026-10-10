from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


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

OUTPUT_SUMMARY = (
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


def build_figure(
    maneuvers,
    outbound_cancel_fraction,
    return_duration_seconds,
    return_scalar_delta_v_ft_s,
) -> None:
    FIGURE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(14, 8)
    )

    ax.set_xlim(
        -0.7,
        6.7,
    )

    ax.set_ylim(
        -0.8,
        2.0,
    )

    ax.axis(
        "off"
    )

    labels = [
        "OTC1",
        "OTC2",
        "OTC3",
        "RTC1",
        "RTC2",
        "RTC3",
    ]

    x_values = list(
        range(len(labels))
    )

    maneuvers_by_id = {
        maneuver["maneuver_id"]:
            maneuver
        for maneuver in maneuvers
    }

    ids = [
        "otc1",
        "otc2",
        "otc3",
        "rtc1",
        "rtc2",
        "rtc3",
    ]

    for x, maneuver_id, label in zip(
        x_values,
        ids,
        labels,
    ):
        maneuver = maneuvers_by_id[
            maneuver_id
        ]

        status = maneuver[
            "status"
        ]

        if status == "CANCELLED":
            marker = "X"
            detail = "CANCELLED"

        else:
            marker = "●"
            detail = "EXECUTED"

        ax.text(
            x,
            1.25,
            label,
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
        )

        ax.text(
            x,
            0.85,
            marker,
            ha="center",
            va="center",
            fontsize=22,
        )

        ax.text(
            x,
            0.48,
            detail,
            ha="center",
            va="center",
            fontsize=8,
        )

        if maneuver_id == "otc1":
            lower = (
                "planned ~8 s\n"
                "planned 0.7 ft/s"
            )

        elif maneuver_id == "otc2":
            lower = (
                "trajectory\n"
                "remained on track"
            )

        elif maneuver_id == "otc3":
            lower = (
                "17.5 s\n"
                "Δv not public here"
            )

        else:
            execution = (
                maneuver[
                    "execution"
                ]
            )

            lower = (
                f"{execution['duration_seconds']:g} s\n"
                f"{execution['reported_delta_v_ft_s']:g} ft/s"
            )

        ax.text(
            x,
            0.10,
            lower,
            ha="center",
            va="center",
            fontsize=8,
        )

    ax.plot(
        [-0.3, 2.3],
        [1.62, 1.62],
        linewidth=1.2,
    )

    ax.text(
        1.0,
        1.78,
        "OUTBOUND",
        ha="center",
        va="center",
        fontsize=11,
    )

    ax.plot(
        [2.7, 5.3],
        [1.62, 1.62],
        linewidth=1.2,
    )

    ax.text(
        4.0,
        1.78,
        "RETURN",
        ha="center",
        va="center",
        fontsize=11,
    )

    ax.text(
        0.50,
        -0.32,
        (
            "Outbound: "
            f"2 of 3 cancelled "
            f"({outbound_cancel_fraction * 100.0:.3f}%)"
            "    |    "
            "Return: 3 of 3 executed"
            "    |    "
            f"Return firing time: {return_duration_seconds:.1f} s"
            "    |    "
            "Return scalar Δv sum: "
            f"{return_scalar_delta_v_ft_s:.1f} ft/s"
        ),
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=9,
    )

    ax.text(
        0.50,
        -0.48,
        (
            "Cancelled ≠ failed. "
            "OTC1 values are planned values. "
            "The 11.1 ft/s return total is a scalar sum of "
            "reported magnitudes, not a net vector Δv."
        ),
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=8,
    )

    ax.set_title(
        "Artemis II Trajectory Correction Plan vs Execution",
        fontsize=15,
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

    trajectory_events = load_json(
        TRAJECTORY_EVENTS_PATH
    )

    communications = load_json(
        COMMUNICATIONS_PATH
    )

    if (
        reference.get(
            "dataset_id"
        )
        != "phase2i1_artemis_ii_maneuver_plan_execution"
    ):
        fail(
            "Unexpected Phase 2I.1 dataset ID."
        )

    maneuvers = (
        reference[
            "maneuvers"
        ]
    )

    if len(maneuvers) != 6:
        fail(
            "Expected exactly six trajectory "
            "correction maneuver records."
        )

    maneuver_ids = [
        maneuver[
            "maneuver_id"
        ]
        for maneuver in maneuvers
    ]

    expected_ids = [
        "otc1",
        "otc2",
        "otc3",
        "rtc1",
        "rtc2",
        "rtc3",
    ]

    if maneuver_ids != expected_ids:
        fail(
            "Maneuver identity or ordering changed."
        )

    maneuvers_by_id = {
        maneuver[
            "maneuver_id"
        ]:
            maneuver
        for maneuver in maneuvers
    }

    trajectory = {
        event[
            "id"
        ]:
            event
        for event in trajectory_events
    }

    communications_by_id = {
        event[
            "id"
        ]:
            event
        for event in communications[
            "events"
        ]
    }

    # --------------------------------------------------------
    # Status integrity
    # --------------------------------------------------------

    expected_status = {
        "otc1": "CANCELLED",
        "otc2": "CANCELLED",
        "otc3": "EXECUTED",
        "rtc1": "EXECUTED",
        "rtc2": "EXECUTED",
        "rtc3": "EXECUTED",
    }

    for maneuver_id, status in (
        expected_status.items()
    ):
        maneuver = (
            maneuvers_by_id[
                maneuver_id
            ]
        )

        if maneuver[
            "status"
        ] != status:
            fail(
                f"{maneuver_id} status changed."
            )

        should_execute = (
            status == "EXECUTED"
        )

        if (
            maneuver[
                "executed"
            ]
            is not should_execute
        ):
            fail(
                f"{maneuver_id} execution flag "
                "does not match status."
            )

    # --------------------------------------------------------
    # OTC1 planned versus cancelled boundary
    # --------------------------------------------------------

    otc1 = (
        maneuvers_by_id[
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
            "OTC1 planned timestamp changed."
        )

    if (
        otc1[
            "plan"
        ][
            "timestamp_precision"
        ]
        != "MINUTE_LEVEL"
    ):
        fail(
            "OTC1 planned timestamp "
            "precision changed."
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
            "OTC1 duration lost approximate semantics."
        )

    if abs(
        float(
            otc1[
                "plan"
            ][
                "planned_duration_seconds"
            ]
        )
        - 8.0
    ) > 1e-9:
        fail(
            "OTC1 planned duration changed."
        )

    if abs(
        float(
            otc1[
                "plan"
            ][
                "planned_delta_v_ft_s"
            ]
        )
        - 0.7
    ) > 1e-9:
        fail(
            "OTC1 planned delta-v changed."
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
            "OTC1 gained unsupported exact "
            "cancellation time."
        )

    if (
        otc1[
            "decision"
        ][
            "reason_classification"
        ]
        != "TRAJECTORY_ALREADY_ON_CORRECT_FLIGHT_PATH"
    ):
        fail(
            "OTC1 cancellation reason changed."
        )

    # --------------------------------------------------------
    # OTC2 cancellation boundary
    # --------------------------------------------------------

    otc2 = (
        maneuvers_by_id[
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
            "OTC2 planning precision changed."
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
            "OTC2 gained unsupported exact "
            "cancellation time."
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
            "OTC2 cancellation reason changed."
        )

    if (
        otc2[
            "decision"
        ][
            "parallel_operational_activity"
        ]
        != (
            "ATTITUDE_ADJUSTMENT_FOR_"
            "WASTEWATER_VENT_CLEARING"
        )
    ):
        fail(
            "OTC2 parallel operational "
            "activity changed."
        )

    # --------------------------------------------------------
    # Executed burn cross-checks against Phase 1
    # --------------------------------------------------------

    expected_execution = {
        "otc3": {
            "timestamp_utc":
                "2026-04-06T03:03:00Z",
            "duration_seconds":
                17.5,
            "delta_v_ft_s":
                None,
        },
        "rtc1": {
            "timestamp_utc":
                "2026-04-08T00:03:00Z",
            "duration_seconds":
                15.0,
            "delta_v_ft_s":
                1.6,
        },
        "rtc2": {
            "timestamp_utc":
                "2026-04-10T02:53:00Z",
            "duration_seconds":
                9.0,
            "delta_v_ft_s":
                5.3,
        },
        "rtc3": {
            "timestamp_utc":
                "2026-04-10T18:53:00Z",
            "duration_seconds":
                8.0,
            "delta_v_ft_s":
                4.2,
        },
    }

    for maneuver_id, expected in (
        expected_execution.items()
    ):
        if maneuver_id not in trajectory:
            fail(
                f"Missing Phase 1 trajectory event: "
                f"{maneuver_id}"
            )

        reference_execution = (
            maneuvers_by_id[
                maneuver_id
            ][
                "execution"
            ]
        )

        trajectory_event = (
            trajectory[
                maneuver_id
            ]
        )

        if (
            reference_execution[
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
            trajectory_event[
                "timestamp_utc"
            ]
            != expected[
                "timestamp_utc"
            ]
        ):
            fail(
                f"{maneuver_id} Phase 1 timestamp changed."
            )

        reference_duration = float(
            reference_execution[
                "duration_seconds"
            ]
        )

        trajectory_duration = float(
            trajectory_event[
                "duration_seconds"
            ]
        )

        if abs(
            reference_duration
            - expected[
                "duration_seconds"
            ]
        ) > 1e-9:
            fail(
                f"{maneuver_id} reference duration changed."
            )

        if abs(
            trajectory_duration
            - expected[
                "duration_seconds"
            ]
        ) > 1e-9:
            fail(
                f"{maneuver_id} Phase 1 duration changed."
            )

        expected_dv = (
            expected[
                "delta_v_ft_s"
            ]
        )

        reference_dv = (
            reference_execution.get(
                "reported_delta_v_ft_s"
            )
        )

        trajectory_dv = (
            trajectory_event.get(
                "delta_v_ft_s"
            )
        )

        if expected_dv is None:
            if (
                reference_dv is not None
                or trajectory_dv is not None
            ):
                fail(
                    f"{maneuver_id} gained unsupported "
                    "delta-v."
                )

        else:
            if abs(
                float(reference_dv)
                - expected_dv
            ) > 1e-9:
                fail(
                    f"{maneuver_id} reference delta-v changed."
                )

            if abs(
                float(trajectory_dv)
                - expected_dv
            ) > 1e-9:
                fail(
                    f"{maneuver_id} Phase 1 delta-v changed."
                )

    # --------------------------------------------------------
    # Derived aggregates
    # --------------------------------------------------------

    outbound = [
        maneuver
        for maneuver in maneuvers
        if maneuver[
            "leg"
        ] == "OUTBOUND"
    ]

    return_maneuvers = [
        maneuver
        for maneuver in maneuvers
        if maneuver[
            "leg"
        ] == "RETURN"
    ]

    outbound_planned_count = sum(
        1
        for maneuver in outbound
        if maneuver[
            "planned"
        ]
    )

    outbound_cancelled_count = sum(
        1
        for maneuver in outbound
        if maneuver[
            "status"
        ] == "CANCELLED"
    )

    outbound_executed_count = sum(
        1
        for maneuver in outbound
        if maneuver[
            "status"
        ] == "EXECUTED"
    )

    outbound_cancel_fraction = (
        outbound_cancelled_count
        / outbound_planned_count
    )

    return_planned_count = sum(
        1
        for maneuver in return_maneuvers
        if maneuver[
            "planned"
        ]
    )

    return_executed_count = sum(
        1
        for maneuver in return_maneuvers
        if maneuver[
            "status"
        ] == "EXECUTED"
    )

    return_duration_seconds = sum(
        float(
            maneuver[
                "execution"
            ][
                "duration_seconds"
            ]
        )
        for maneuver in return_maneuvers
    )

    return_scalar_delta_v_ft_s = sum(
        float(
            maneuver[
                "execution"
            ][
                "reported_delta_v_ft_s"
            ]
        )
        for maneuver in return_maneuvers
    )

    return_scalar_delta_v_m_s = (
        return_scalar_delta_v_ft_s
        * 0.3048
    )

    known_executed_duration_seconds = sum(
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

    if outbound_planned_count != 3:
        fail(
            "Expected three planned outbound corrections."
        )

    if outbound_cancelled_count != 2:
        fail(
            "Expected two cancelled outbound corrections."
        )

    if outbound_executed_count != 1:
        fail(
            "Expected one executed outbound correction."
        )

    if return_planned_count != 3:
        fail(
            "Expected three planned return corrections."
        )

    if return_executed_count != 3:
        fail(
            "Expected all three return corrections executed."
        )

    if abs(
        return_duration_seconds
        - 32.0
    ) > 1e-9:
        fail(
            "Return correction duration total changed."
        )

    if abs(
        return_scalar_delta_v_ft_s
        - 11.1
    ) > 1e-9:
        fail(
            "Return scalar delta-v total changed."
        )

    if abs(
        return_scalar_delta_v_m_s
        - 3.38328
    ) > 1e-9:
        fail(
            "Return scalar delta-v SI conversion changed."
        )

    if abs(
        known_executed_duration_seconds
        - 49.5
    ) > 1e-9:
        fail(
            "Known executed correction-burn "
            "duration total changed."
        )

    # --------------------------------------------------------
    # Phase 2H RTC2 cross-phase check
    # --------------------------------------------------------

    loss = (
        communications_by_id[
            "unexpected_return_link_loss"
        ]
    )

    recovery = (
        communications_by_id[
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
            "RTC2 preburn communications "
            "anomaly precision changed."
        )

    if (
        recovery[
            "precision"
        ]
        != "SEQUENCE_ONLY"
    ):
        fail(
            "RTC2 communications recovery "
            "precision changed."
        )

    rtc2_context = (
        maneuvers_by_id[
            "rtc2"
        ][
            "communications_context"
        ]
    )

    if (
        rtc2_context[
            "burn_executed_after_recovery"
        ]
        is not True
    ):
        fail(
            "RTC2 recovery-to-execution "
            "relationship changed."
        )

    if (
        rtc2_context[
            "anomaly_caused_burn_failure"
        ]
        is not False
    ):
        fail(
            "RTC2 was incorrectly marked failed "
            "because of communications anomaly."
        )

    # --------------------------------------------------------
    # Postflight cancellation context
    # --------------------------------------------------------

    postflight = (
        reference[
            "postflight_context"
        ]
    )

    if (
        postflight[
            "outbound_corrections_planned"
        ]
        != 3
        or postflight[
            "outbound_corrections_cancelled"
        ]
        != 2
    ):
        fail(
            "Postflight outbound cancellation "
            "context changed."
        )

    # --------------------------------------------------------
    # Processed maneuver table
    # --------------------------------------------------------

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "maneuver_id",
        "name",
        "leg",
        "sequence_index",
        "planned",
        "status",
        "executed",
        "timestamp_utc",
        "timestamp_precision",
        "duration_seconds",
        "duration_semantics",
        "delta_v_ft_s",
        "delta_v_semantics",
    ]

    rows = []

    for maneuver in maneuvers:
        if (
            maneuver[
                "status"
            ]
            == "EXECUTED"
        ):
            execution = (
                maneuver[
                    "execution"
                ]
            )

            timestamp_utc = (
                execution[
                    "timestamp_utc"
                ]
            )

            timestamp_precision = (
                execution[
                    "timestamp_precision"
                ]
            )

            duration_seconds = (
                execution[
                    "duration_seconds"
                ]
            )

            duration_semantics = (
                "EXECUTED_REPORTED"
            )

            delta_v_ft_s = (
                execution.get(
                    "reported_delta_v_ft_s"
                )
            )

            if delta_v_ft_s is None:
                delta_v_semantics = (
                    "NOT_PUBLICLY_REPORTED"
                )
            else:
                delta_v_semantics = (
                    execution[
                        "delta_v_semantics"
                    ]
                )

        else:
            plan = (
                maneuver[
                    "plan"
                ]
            )

            timestamp_utc = (
                plan.get(
                    "planned_timestamp_utc"
                )
            )

            timestamp_precision = (
                plan[
                    "timestamp_precision"
                ]
            )

            duration_seconds = (
                plan.get(
                    "planned_duration_seconds"
                )
            )

            if (
                duration_seconds
                is None
            ):
                duration_semantics = (
                    "NOT_PUBLICLY_SPECIFIED"
                )
            else:
                duration_semantics = (
                    "PLANNED_"
                    + plan.get(
                        "duration_relation",
                        "REPORTED",
                    )
                )

            delta_v_ft_s = (
                plan.get(
                    "planned_delta_v_ft_s"
                )
            )

            if (
                delta_v_ft_s
                is None
            ):
                delta_v_semantics = (
                    "NOT_PUBLICLY_SPECIFIED"
                )
            else:
                delta_v_semantics = (
                    plan[
                        "delta_v_semantics"
                    ]
                )

        rows.append(
            {
                "maneuver_id":
                    maneuver[
                        "maneuver_id"
                    ],

                "name":
                    maneuver[
                        "name"
                    ],

                "leg":
                    maneuver[
                        "leg"
                    ],

                "sequence_index":
                    maneuver[
                        "sequence_index"
                    ],

                "planned":
                    str(
                        maneuver[
                            "planned"
                        ]
                    ).lower(),

                "status":
                    maneuver[
                        "status"
                    ],

                "executed":
                    str(
                        maneuver[
                            "executed"
                        ]
                    ).lower(),

                "timestamp_utc":
                    (
                        timestamp_utc
                        if timestamp_utc
                        is not None
                        else ""
                    ),

                "timestamp_precision":
                    timestamp_precision,

                "duration_seconds":
                    (
                        duration_seconds
                        if duration_seconds
                        is not None
                        else ""
                    ),

                "duration_semantics":
                    duration_semantics,

                "delta_v_ft_s":
                    (
                        delta_v_ft_s
                        if delta_v_ft_s
                        is not None
                        else ""
                    ),

                "delta_v_semantics":
                    delta_v_semantics,
            }
        )

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
        writer.writerows(
            rows
        )

    # --------------------------------------------------------
    # Figure and summary
    # --------------------------------------------------------

    build_figure(
        maneuvers,
        outbound_cancel_fraction,
        return_duration_seconds,
        return_scalar_delta_v_ft_s,
    )

    status_counts = Counter(
        maneuver[
            "status"
        ]
        for maneuver in maneuvers
    )

    summary = {
        "product_id":
            "phase2i1_maneuver_plan_execution_analysis",

        "mission":
            "Artemis II",

        "reference_dataset_id":
            reference[
                "dataset_id"
            ],

        "maneuver_count":
            len(maneuvers),

        "status_counts":
            dict(
                status_counts
            ),

        "outbound": {
            "planned_count":
                outbound_planned_count,

            "cancelled_count":
                outbound_cancelled_count,

            "executed_count":
                outbound_executed_count,

            "cancellation_fraction":
                outbound_cancel_fraction,

            "cancellation_percent":
                (
                    outbound_cancel_fraction
                    * 100.0
                ),
        },

        "return": {
            "planned_count":
                return_planned_count,

            "executed_count":
                return_executed_count,

            "combined_burn_duration_seconds":
                return_duration_seconds,

            "scalar_sum_reported_delta_v_ft_s":
                return_scalar_delta_v_ft_s,

            "scalar_sum_reported_delta_v_m_s":
                return_scalar_delta_v_m_s,

            "net_vector_delta_v_computed":
                False,
        },

        "all_executed_corrections": {
            "executed_count":
                status_counts[
                    "EXECUTED"
                ],

            "known_combined_burn_duration_seconds":
                known_executed_duration_seconds,

            "combined_delta_v_computed":
                False,

            "combined_delta_v_reason":
                (
                    "OTC3 public delta-v is unavailable "
                    "in the Phase 2I.1 source set."
                ),
        },

        "otc1": {
            "planned_timestamp_utc":
                otc1[
                    "plan"
                ][
                    "planned_timestamp_utc"
                ],

            "planned_duration_seconds":
                otc1[
                    "plan"
                ][
                    "planned_duration_seconds"
                ],

            "planned_duration_relation":
                otc1[
                    "plan"
                ][
                    "duration_relation"
                ],

            "planned_delta_v_ft_s":
                otc1[
                    "plan"
                ][
                    "planned_delta_v_ft_s"
                ],

            "status":
                "CANCELLED",

            "exact_cancellation_timestamp_known":
                False,
        },

        "otc2": {
            "status":
                "CANCELLED",

            "exact_cancellation_timestamp_known":
                False,

            "parallel_operational_activity":
                otc2[
                    "decision"
                ][
                    "parallel_operational_activity"
                ],
        },

        "rtc2_cross_phase_context": {
            "communications_loss_precision":
                loss[
                    "precision"
                ],

            "communications_recovery_precision":
                recovery[
                    "precision"
                ],

            "burn_executed_after_recovery":
                True,

            "communications_anomaly_implied_burn_failure":
                False,
        },

        "postflight_context":
            postflight,

        "propulsion_assignment_boundary":
            reference[
                "propulsion_assignment_boundary"
            ],

        "guardrails":
            reference[
                "guardrails"
            ],

        "outputs": {
            "maneuver_csv":
                str(
                    OUTPUT_CSV.relative_to(
                        ROOT
                    )
                ),

            "plan_execution_figure":
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
        "Phase 2I.1 Maneuver Plan / Execution Analysis"
    )

    print("=" * 58)

    print()
    print(
        "Maneuver records:"
    )

    print(
        f"  total: {len(maneuvers)}"
    )

    print(
        f"  executed: "
        f"{status_counts['EXECUTED']}"
    )

    print(
        f"  cancelled: "
        f"{status_counts['CANCELLED']}"
    )

    print()
    print(
        "Outbound:"
    )

    print(
        f"  planned: "
        f"{outbound_planned_count}"
    )

    print(
        f"  cancelled: "
        f"{outbound_cancelled_count}"
    )

    print(
        f"  executed: "
        f"{outbound_executed_count}"
    )

    print(
        "  cancellation fraction:"
    )

    print(
        f"    "
        f"{outbound_cancel_fraction:.6f}"
    )

    print(
        f"    "
        f"{outbound_cancel_fraction * 100.0:.3f}%"
    )

    print()
    print(
        "OTC1:"
    )

    print(
        "  planned UTC:"
    )

    print(
        "    "
        f"{otc1['plan']['planned_timestamp_utc']}"
    )

    print(
        "  planned duration:"
    )

    print(
        "    ~"
        f"{otc1['plan']['planned_duration_seconds']:.0f} s"
    )

    print(
        "  planned delta-v:"
    )

    print(
        "    "
        f"{otc1['plan']['planned_delta_v_ft_s']} ft/s"
    )

    print(
        "  status:"
    )

    print(
        "    CANCELLED"
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
        "  status:"
    )

    print(
        "    CANCELLED"
    )

    print(
        "  reason:"
    )

    print(
        "    TRAJECTORY_REMAINED_ON_TRACK"
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
        "  status:"
    )

    print(
        "    EXECUTED"
    )

    print(
        "  UTC:"
    )

    print(
        "    "
        f"{maneuvers_by_id['otc3']['execution']['timestamp_utc']}"
    )

    print(
        "  duration:"
    )

    print(
        "    "
        f"{maneuvers_by_id['otc3']['execution']['duration_seconds']} s"
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
        f"  planned: "
        f"{return_planned_count}"
    )

    print(
        f"  executed: "
        f"{return_executed_count}"
    )

    print(
        "  combined burn duration:"
    )

    print(
        f"    "
        f"{return_duration_seconds:.1f} s"
    )

    print(
        "  scalar delta-v magnitude sum:"
    )

    print(
        f"    "
        f"{return_scalar_delta_v_ft_s:.1f} ft/s"
    )

    print(
        f"    "
        f"{return_scalar_delta_v_m_s:.5f} m/s"
    )

    print(
        "  net vector delta-v:"
    )

    print(
        "    NOT COMPUTED"
    )

    print()
    print(
        "All executed correction burns:"
    )

    print(
        "  known combined firing time:"
    )

    print(
        f"    "
        f"{known_executed_duration_seconds:.1f} s"
    )

    print(
        "  combined delta-v:"
    )

    print(
        "    NOT COMPUTED"
    )

    print(
        "  reason:"
    )

    print(
        "    OTC3 DELTA-V NOT PUBLIC "
        "IN PHASE 2I.1 SOURCE SET"
    )

    print()
    print(
        "Postflight TLI context:"
    )

    print(
        "  TLI duration:"
    )

    print(
        "    350.0 s"
    )

    print(
        "  outbound corrections made unnecessary:"
    )

    print(
        "    2 of 3"
    )

    print(
        "  attribution:"
    )

    print(
        "    PRECISE TLI"
    )

    print()
    print(
        "RTC2 cross-phase communications context:"
    )

    print(
        "  preburn loss:"
    )

    print(
        "    APPROXIMATE"
    )

    print(
        "  recovery:"
    )

    print(
        "    SEQUENCE_ONLY"
    )

    print(
        "  RTC2 executed afterward:"
    )

    print(
        "    TRUE"
    )

    print(
        "  burn failure inferred:"
    )

    print(
        "    FALSE"
    )

    print()
    print(
        "Engine assignment boundary:"
    )

    print(
        "  OTC3: UNRESOLVED"
    )

    print(
        "  RTC1: UNRESOLVED"
    )

    print(
        "  RTC2: UNRESOLVED"
    )

    print(
        "  RTC3: UNRESOLVED"
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
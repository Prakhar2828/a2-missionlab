from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_phase2_integrated_operations.json"
)

FLIGHT_DYNAMICS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_trajectory_correlation.json"
)

COMMUNICATIONS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_operational_threads.json"
)

PROPULSION_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_esm_propulsion_architecture.json"
)

MANEUVERS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_operational_threads.json"
)

GNC_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_gnc_operational_threads.json"
)

OUTPUT_DIR = ROOT / "data" / "processed" / "phase2"

THREAD_CSV = OUTPUT_DIR / "phase2_integrated_operational_threads.csv"
DOMAIN_CSV = OUTPUT_DIR / "phase2_domain_closure.csv"
SUMMARY_PATH = OUTPUT_DIR / "phase2_integrated_operations_summary.json"

ASSET_DIR = ROOT / "docs" / "assets" / "phase2"

THREAD_FIGURE = (
    ASSET_DIR
    / "phase2k_integrated_operational_threads.svg"
)

DOMAIN_FIGURE = (
    ASSET_DIR
    / "phase2k_domain_closure.svg"
)

plt.rcParams["svg.hashsalt"] = "a2-missionlab"

SVG_METADATA = {
    "Date": None
}


def fail(message):
    raise SystemExit(
        f"VALIDATION FAILED: {message}"
    )


def load_json(path):
    if not path.exists():
        fail(
            f"missing file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def normalize_svg(path):
    text = path.read_text(
        encoding="utf-8"
    )

    cleaned = "\n".join(
        line.rstrip(" \t")
        for line in text.splitlines()
    )

    path.write_text(
        cleaned + "\n",
        encoding="utf-8",
    )


def get_thread(items, thread_id):
    for item in items:
        if item["thread_id"] == thread_id:
            return item

    fail(
        f"missing thread: {thread_id}"
    )


def get_step(thread, step_id):
    for item in thread["operational_sequence"]:
        if item["step_id"] == step_id:
            return item

    fail(
        f"missing step {step_id} "
        f"in {thread['thread_id']}"
    )


def get_anchor(reference, event_id):
    for item in reference["mission_clock_anchors"]:
        if item["event_id"] == event_id:
            return item

    fail(
        f"missing mission-clock anchor: {event_id}"
    )


def get_maneuver(items, maneuver_id):
    for item in items:
        if item["maneuver_id"] == maneuver_id:
            return item

    fail(
        f"missing maneuver correlation: {maneuver_id}"
    )


def build_thread_figure(reference):
    threads = reference[
        "phase2_integrated_operational_threads"
    ]

    rows = []

    for item in threads:
        rows.append(
            [
                item["thread_id"].replace(
                    "_",
                    " ",
                ).title(),
                item["classification"],
                "YES" if item["anomaly"] else "NO",
                ", ".join(
                    item["domains"]
                ),
            ]
        )

    fig, ax = plt.subplots(
        figsize=(18, 7)
    )

    ax.axis("off")

    ax.set_title(
        "Artemis II Phase 2 Integrated Operational Threads",
        fontsize=15,
        pad=18,
    )

    table = ax.table(
        cellText=rows,
        colLabels=[
            "Operational Thread",
            "Classification",
            "Anomaly",
            "Domains",
        ],
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        7.5
    )

    table.scale(
        1.0,
        1.9,
    )

    ax.text(
        0.5,
        0.04,
        (
            "Integrated public-evidence threads are not "
            "complete console logs, filter histories, "
            "guidance laws, targeting solutions, or "
            "thruster telemetry."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        THREAD_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(fig)

    normalize_svg(
        THREAD_FIGURE
    )


def build_domain_figure(reference):
    rows = []

    for domain, item in (
        reference[
            "phase2_domain_status"
        ].items()
    ):
        rows.append(
            [
                domain.replace(
                    "_",
                    " ",
                ).title(),
                item["status"],
                str(
                    len(
                        item[
                            "capabilities"
                        ]
                    )
                ),
            ]
        )

    fig, ax = plt.subplots(
        figsize=(14, 5.5)
    )

    ax.axis("off")

    ax.set_title(
        "Artemis II Phase 2 Domain Closure",
        fontsize=15,
        pad=18,
    )

    table = ax.table(
        cellText=rows,
        colLabels=[
            "Domain",
            "Status",
            "Integrated Capabilities",
        ],
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        9
    )

    table.scale(
        1.0,
        1.9,
    )

    ax.text(
        0.5,
        0.06,
        (
            "Phase 2 closes flight dynamics, communications, "
            "propulsion, maneuvers, and GNC only to the "
            "public-evidence scope defined by MissionLab."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        DOMAIN_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(fig)

    normalize_svg(
        DOMAIN_FIGURE
    )


def main():
    reference = load_json(
        REFERENCE_PATH
    )

    flight_dynamics = load_json(
        FLIGHT_DYNAMICS_PATH
    )

    communications = load_json(
        COMMUNICATIONS_PATH
    )

    propulsion = load_json(
        PROPULSION_PATH
    )

    maneuvers = load_json(
        MANEUVERS_PATH
    )

    gnc = load_json(
        GNC_PATH
    )

    expected_ids = {
        "reference":
            "phase2k_artemis_ii_phase2_integrated_operations",

        "flight_dynamics":
            "phase2i3_artemis_ii_maneuver_trajectory_correlation",

        "communications":
            "phase2h4_artemis_ii_communications_operational_threads",

        "propulsion":
            "phase2i2_artemis_ii_esm_propulsion_architecture",

        "maneuvers":
            "phase2i4_artemis_ii_maneuver_operational_threads",

        "gnc":
            "phase2j4_artemis_ii_gnc_operational_threads",
    }

    observed_ids = {
        "reference":
            reference.get(
                "dataset_id"
            ),

        "flight_dynamics":
            flight_dynamics.get(
                "dataset_id"
            ),

        "communications":
            communications.get(
                "dataset_id"
            ),

        "propulsion":
            propulsion.get(
                "dataset_id"
            ),

        "maneuvers":
            maneuvers.get(
                "dataset_id"
            ),

        "gnc":
            gnc.get(
                "dataset_id"
            ),
    }

    for key, expected in (
        expected_ids.items()
    ):
        if (
            observed_ids[key]
            != expected
        ):
            fail(
                f"{key} dataset ID mismatch"
            )

    if (
        reference["phase"]
        != "2K"
    ):
        fail(
            "Phase identifier mismatch"
        )

    if (
        reference["phase_name"]
        != "Phase 2 Integration & Closure"
    ):
        fail(
            "Phase name mismatch"
        )

    valid_statuses = {
        "IMPLEMENTATION_IN_PROGRESS",
        "COMPLETE",
    }

    if (
        reference[
            "phase2_status"
        ]
        not in valid_statuses
    ):
        fail(
            "invalid Phase 2 status"
        )

    expected_domains = [
        "flight_dynamics",
        "communications",
        "propulsion",
        "maneuvers",
        "gnc",
    ]

    if (
        list(
            reference[
                "phase2_domain_status"
            ]
        )
        != expected_domains
    ):
        fail(
            "Phase 2 domain order changed"
        )

    for domain in expected_domains:
        if (
            reference[
                "phase2_domain_status"
            ][domain]["status"]
            != "COMPLETE_TO_PHASE2_SCOPE"
        ):
            fail(
                f"{domain} not complete "
                "to Phase 2 scope"
            )

    #
    # Mission clock
    #

    flight_anchors = (
        flight_dynamics[
            "mission_anchors"
        ]
    )

    for event_id in [
        "launch",
        "lunar_soi_entry",
        "pericynthion",
        "lunar_soi_exit",
        "entry_interface",
        "splashdown",
    ]:
        integrated = get_anchor(
            reference,
            event_id,
        )

        source = flight_anchors[
            event_id
        ]

        if (
            integrated[
                "timestamp_utc"
            ]
            != source[
                "timestamp_utc"
            ]
        ):
            fail(
                f"mission-clock mismatch: {event_id}"
            )

    maneuver_map = {
        item["maneuver_id"]: item
        for item in (
            flight_dynamics[
                "maneuver_correlations"
            ]
        )
    }

    for maneuver_id in [
        "otc3",
        "rtc1",
        "rtc2",
        "rtc3",
    ]:
        integrated = get_anchor(
            reference,
            maneuver_id,
        )

        source = maneuver_map[
            maneuver_id
        ]

        if (
            integrated[
                "timestamp_utc"
            ]
            != source[
                "timestamp_utc"
            ]
        ):
            fail(
                f"maneuver anchor mismatch: {maneuver_id}"
            )

    #
    # Communications cross-check
    #

    lunar_comms = get_thread(
        communications[
            "threads"
        ],
        "lunar_occultation_blackout_and_reacquisition",
    )

    fd9_comms = get_thread(
        communications[
            "threads"
        ],
        "flight_day_9_return_link_loss_and_recovery",
    )

    if (
        lunar_comms[
            "classification"
        ]
        != "EXPECTED_OPERATIONAL_CONSTRAINT"
        or lunar_comms[
            "anomaly"
        ]
        is not False
    ):
        fail(
            "expected lunar blackout "
            "classification changed"
        )

    reported_earthrise = get_step(
        lunar_comms,
        "reported_earthrise",
    )

    if (
        get_anchor(
            reference,
            "reported_earthrise",
        )[
            "timestamp_utc"
        ]
        != reported_earthrise[
            "timestamp_utc"
        ]
    ):
        fail(
            "reported Earthrise mismatch"
        )

    if (
        fd9_comms[
            "classification"
        ]
        != "UNEXPECTED_COMMUNICATIONS_ANOMALY"
        or fd9_comms[
            "anomaly"
        ]
        is not True
        or fd9_comms[
            "complete_two_way_outage_established"
        ]
        is not False
        or fd9_comms[
            "causal_relationship"
        ]
        != "NOT_ESTABLISHED"
        or fd9_comms[
            "failed_subsystem_identified"
        ]
        is not False
    ):
        fail(
            "Flight Day 9 communications "
            "boundary changed"
        )

    fd9_loss = get_step(
        fd9_comms,
        "unexpected_return_link_loss",
    )

    integrated_fd9 = get_thread(
        reference[
            "phase2_integrated_operational_threads"
        ],
        "rtc2_communications_anomaly_recovery_and_mission_continuation",
    )

    if (
        integrated_fd9[
            "approximate_loss_anchor_utc"
        ]
        != fd9_loss[
            "approximate_anchor_utc"
        ]
        or integrated_fd9[
            "approximate_anchor_is_exact"
        ]
        is not False
        or integrated_fd9[
            "causal_relationship"
        ]
        != "NOT_ESTABLISHED"
        or integrated_fd9[
            "complete_two_way_outage_established"
        ]
        is not False
        or integrated_fd9[
            "root_cause_public"
        ]
        is not False
        or integrated_fd9[
            "failed_subsystem_public"
        ]
        is not False
        or integrated_fd9[
            "burn_failure"
        ]
        is not False
        or integrated_fd9[
            "propulsion_anomaly_inferred"
        ]
        is not False
    ):
        fail(
            "RTC2 anomaly integration failed"
        )

    #
    # Propulsion architecture
    #

    architecture = propulsion[
        "architecture"
    ]

    if (
        architecture[
            "engine_class_count"
        ]
        != 3
        or architecture[
            "total_engine_count"
        ]
        != 33
    ):
        fail(
            "propulsion architecture count mismatch"
        )

    propulsion_counts = {
        item[
            "engine_class_id"
        ]:
            item[
                "count"
            ]
        for item in architecture[
            "engine_classes"
        ]
    }

    expected_propulsion_counts = {
        "main_engine_oms_e": 1,
        "auxiliary_r4d11": 8,
        "reaction_control_system": 24,
    }

    if (
        propulsion_counts
        != expected_propulsion_counts
    ):
        fail(
            "propulsion engine-class count mismatch"
        )

    if (
        reference[
            "propulsion_boundary"
        ][
            "resolved_correction_burn_engine_assignments"
        ]
        != 0
    ):
        fail(
            "correction engine assignment "
            "incorrectly resolved"
        )

    if (
        reference[
            "propulsion_boundary"
        ][
            "unresolved_correction_burn_engine_assignments"
        ]
        != [
            "otc3",
            "rtc1",
            "rtc2",
            "rtc3",
        ]
    ):
        fail(
            "unresolved correction-burn set changed"
        )

    if (
        reference[
            "propulsion_boundary"
        ][
            "confirmed_major_burn_engine_assignment_generalized_to_corrections"
        ]
        is not False
    ):
        fail(
            "major-burn engine assignment "
            "incorrectly generalized"
        )

    #
    # Maneuver accounting
    #

    maneuver_summary = (
        maneuvers[
            "mission_summary"
        ]
    )

    quantitative = reference[
        "phase2_quantitative_summary"
    ]

    comparisons = {
        "planned_trajectory_correction_opportunities":
            maneuver_summary[
                "planned_correction_opportunities"
            ],

        "executed_trajectory_corrections":
            maneuver_summary[
                "executed_corrections"
            ],

        "cancelled_trajectory_corrections":
            maneuver_summary[
                "cancelled_corrections"
            ],

        "known_executed_correction_firing_time_seconds":
            maneuver_summary[
                "known_executed_correction_firing_time_seconds"
            ],

        "return_scalar_delta_v_magnitude_sum_ft_s":
            maneuver_summary[
                "return_scalar_delta_v_magnitude_sum_ft_s"
            ],

        "return_scalar_delta_v_magnitude_sum_m_s":
            maneuver_summary[
                "return_scalar_delta_v_magnitude_sum_m_s"
            ],
    }

    for key, expected in (
        comparisons.items()
    ):
        if (
            quantitative[key]
            != expected
        ):
            fail(
                f"maneuver summary mismatch: {key}"
            )

    if (
        quantitative[
            "net_vector_delta_v_computed"
        ]
        is not False
        or quantitative[
            "all_correction_scalar_delta_v_computed"
        ]
        is not False
    ):
        fail(
            "unsupported delta-v aggregate introduced"
        )

    maneuver_propulsion = (
        maneuvers[
            "propulsion_boundary"
        ]
    )

    if (
        maneuver_propulsion[
            "correction_burn_engine_assignments_resolved"
        ]
        != 0
        or maneuver_propulsion[
            "correction_burn_engine_assignments_unresolved"
        ]
        != 4
    ):
        fail(
            "Phase 2I propulsion boundary changed"
        )

    #
    # OEM boundary
    #

    if (
        len(
            flight_dynamics[
                "oem_creation_time_brackets"
            ]
        )
        != 4
    ):
        fail(
            "OEM maneuver bracket count changed"
        )

    available_comparisons = sum(
        1
        for item in (
            flight_dynamics[
                "oem_creation_time_brackets"
            ]
        )
        if item[
            "same_epoch_solution_difference"
        ][
            "available"
        ]
    )

    if (
        available_comparisons
        != 3
    ):
        fail(
            "OEM same-epoch comparison count changed"
        )

    oem_boundary = reference[
        "oem_boundary"
    ]

    if (
        oem_boundary[
            "maneuver_brackets_audited"
        ]
        != 4
        or oem_boundary[
            "same_epoch_solution_comparisons_available"
        ]
        != 3
        or oem_boundary[
            "solution_difference_is_navigation_error"
        ]
        is not False
        or oem_boundary[
            "solution_difference_is_measured_burn_delta_v"
        ]
        is not False
        or oem_boundary[
            "creation_time_proves_maneuver_assimilation"
        ]
        is not False
        or oem_boundary[
            "maneuver_assimilation_status"
        ]
        != "NOT_ESTABLISHED"
    ):
        fail(
            "OEM interpretation boundary failed"
        )

    #
    # GNC integration
    #

    if (
        gnc[
            "core_architecture"
        ][
            "onboard_navigation_sensor_count"
        ]
        != 6
    ):
        fail(
            "GNC navigation sensor count changed"
        )

    if (
        len(
            gnc[
                "operational_threads"
            ]
        )
        != 5
    ):
        fail(
            "GNC operational thread count changed"
        )

    gnc_state_boundary = (
        gnc[
            "state_product_boundary"
        ][
            "statement"
        ]
    )

    expected_state_boundary = (
        "ONBOARD_NAVIGATION_STATE != "
        "GROUND_ORBIT_DETERMINATION != "
        "AROW_PUBLIC_STATE_VECTOR"
    )

    if (
        gnc_state_boundary
        != expected_state_boundary
        or reference[
            "navigation_boundary"
        ][
            "state_product_boundary"
        ]
        != expected_state_boundary
    ):
        fail(
            "navigation state-product boundary changed"
        )

    if (
        reference[
            "navigation_boundary"
        ][
            "dsn_onboard_sensor"
        ]
        is not False
        or reference[
            "navigation_boundary"
        ][
            "complete_onboard_filter_state_history_public"
        ]
        is not False
        or reference[
            "navigation_boundary"
        ][
            "complete_ground_orbit_determination_solution_history_public"
        ]
        is not False
    ):
        fail(
            "navigation evidence boundary failed"
        )

    if (
        gnc[
            "phase2j_cross_phase_closure"
        ][
            "phase2j4"
        ][
            "status"
        ]
        != "COMPLETE"
    ):
        fail(
            "Phase 2J is not closed"
        )

    #
    # Integrated thread structure
    #

    expected_thread_ids = [
        "earth_departure_and_adaptive_outbound_trajectory_management",
        "proximity_operations_manual_control_and_navigation",
        "deep_space_navigation_and_lunar_communications_constraint",
        "return_trajectory_refinement",
        "rtc2_communications_anomaly_recovery_and_mission_continuation",
        "final_correction_to_entry_handoff",
    ]

    integrated_threads = (
        reference[
            "phase2_integrated_operational_threads"
        ]
    )

    observed_thread_ids = [
        item["thread_id"]
        for item in integrated_threads
    ]

    if (
        observed_thread_ids
        != expected_thread_ids
    ):
        fail(
            "Phase 2 integrated thread set changed"
        )

    anomaly_threads = [
        item
        for item in integrated_threads
        if item["anomaly"]
    ]

    if (
        len(
            anomaly_threads
        )
        != 1
        or anomaly_threads[
            0
        ][
            "thread_id"
        ]
        != (
            "rtc2_communications_anomaly_recovery_"
            "and_mission_continuation"
        )
    ):
        fail(
            "Phase 2 anomaly classification changed"
        )

    final_thread = get_thread(
        integrated_threads,
        "final_correction_to_entry_handoff",
    )

    if (
        final_thread[
            "rtc3_timestamp_utc"
        ]
        != "2026-04-10T18:53:00Z"
        or final_thread[
            "entry_interface_timestamp_utc"
        ]
        != "2026-04-10T23:53:00Z"
        or final_thread[
            "rtc3_to_entry_interval_seconds"
        ]
        != 18000.0
        or final_thread[
            "splashdown_timestamp_utc"
        ]
        != "2026-04-11T00:07:00Z"
    ):
        fail(
            "Phase 2 final entry handoff changed"
        )

    #
    # Closure criteria
    #

    criteria = reference[
        "phase2_closure_criteria"
    ]

    for key, value in (
        criteria.items()
    ):
        if (
            key
            == "unsupported_telemetry_fabricated"
        ):
            if value is not False:
                fail(
                    "unsupported telemetry fabrication flag failed"
                )
        elif value is not True:
            fail(
                f"closure criterion failed: {key}"
            )

    if (
        "DETAILED_AS_FLOWN_ENTRY_GUIDANCE"
        not in reference[
            "phase2_not_reconstructable"
        ]
    ):
        fail(
            "entry-guidance evidence boundary missing"
        )

    next_phases = (
        reference[
            "next_phase_handoffs"
        ]
    )

    for key in [
        "phase3_vehicle_systems",
        "phase4_entry_descent_splashdown_recovery",
        "phase5_space_weather_and_radiation",
        "phase6_lunar_science_and_observations",
        "phase7_mission_control_engineering_perspectives",
    ]:
        if (
            next_phases[
                key
            ][
                "status"
            ]
            != "READY"
        ):
            fail(
                f"next-phase handoff not ready: {key}"
            )

    if (
        next_phases[
            "phase4_entry_descent_splashdown_recovery"
        ][
            "entry_anchor_utc"
        ]
        != "2026-04-10T23:53:00Z"
    ):
        fail(
            "Phase 4 entry handoff anchor changed"
        )

    #
    # Write processed products
    #

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    thread_rows = []

    for item in integrated_threads:
        thread_rows.append(
            {
                "thread_id":
                    item[
                        "thread_id"
                    ],

                "classification":
                    item[
                        "classification"
                    ],

                "anomaly":
                    str(
                        item[
                            "anomaly"
                        ]
                    ).lower(),

                "domains":
                    "|".join(
                        item[
                            "domains"
                        ]
                    ),

                "sequence":
                    "|".join(
                        item[
                            "sequence"
                        ]
                    ),

                "sequence_step_count":
                    len(
                        item[
                            "sequence"
                        ]
                    ),

                "interpretation":
                    item[
                        "interpretation"
                    ],
            }
        )

    with THREAD_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "thread_id",
                "classification",
                "anomaly",
                "domains",
                "sequence",
                "sequence_step_count",
                "interpretation",
            ],
        )

        writer.writeheader()
        writer.writerows(
            thread_rows
        )

    domain_rows = []

    for domain, item in (
        reference[
            "phase2_domain_status"
        ].items()
    ):
        domain_rows.append(
            {
                "domain":
                    domain,

                "status":
                    item[
                        "status"
                    ],

                "capability_count":
                    len(
                        item[
                            "capabilities"
                        ]
                    ),

                "capabilities":
                    "|".join(
                        item[
                            "capabilities"
                        ]
                    ),
            }
        )

    with DOMAIN_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "domain",
                "status",
                "capability_count",
                "capabilities",
            ],
        )

        writer.writeheader()
        writer.writerows(
            domain_rows
        )

    build_thread_figure(
        reference
    )

    build_domain_figure(
        reference
    )

    summary = {
        "product_id":
            "phase2k_integrated_operations_analysis",

        "mission":
            reference[
                "mission"
            ],

        "phase":
            reference[
                "phase"
            ],

        "phase_status":
            reference[
                "phase2_status"
            ],

        "dependency_checks": {
            "flight_dynamics":
                "PASS",

            "communications":
                "PASS",

            "propulsion":
                "PASS",

            "maneuvers":
                "PASS",

            "gnc":
                "PASS",
        },

        "domain_status": {
            key:
                value[
                    "status"
                ]
            for key, value in (
                reference[
                    "phase2_domain_status"
                ].items()
            )
        },

        "mission_clock_anchor_count":
            len(
                reference[
                    "mission_clock_anchors"
                ]
            ),

        "integrated_operational_thread_count":
            len(
                integrated_threads
            ),

        "integrated_operational_thread_ids":
            observed_thread_ids,

        "anomaly_thread_count":
            len(
                anomaly_threads
            ),

        "planned_trajectory_correction_opportunities":
            quantitative[
                "planned_trajectory_correction_opportunities"
            ],

        "executed_trajectory_corrections":
            quantitative[
                "executed_trajectory_corrections"
            ],

        "cancelled_trajectory_corrections":
            quantitative[
                "cancelled_trajectory_corrections"
            ],

        "known_executed_correction_firing_time_seconds":
            quantitative[
                "known_executed_correction_firing_time_seconds"
            ],

        "return_scalar_delta_v_magnitude_sum_ft_s":
            quantitative[
                "return_scalar_delta_v_magnitude_sum_ft_s"
            ],

        "correction_burn_engine_assignments_resolved":
            quantitative[
                "correction_burn_engine_assignments_resolved"
            ],

        "correction_burn_engine_assignments_unresolved":
            quantitative[
                "correction_burn_engine_assignments_unresolved"
            ],

        "onboard_navigation_sensor_classes":
            quantitative[
                "onboard_navigation_sensor_classes"
            ],

        "oem_maneuver_creation_brackets_audited":
            quantitative[
                "oem_maneuver_creation_brackets_audited"
            ],

        "oem_same_epoch_solution_comparisons_available":
            quantitative[
                "oem_same_epoch_solution_comparisons_available"
            ],

        "reconstructable_count":
            len(
                reference[
                    "phase2_reconstructable"
                ]
            ),

        "not_reconstructable_count":
            len(
                reference[
                    "phase2_not_reconstructable"
                ]
            ),

        "next_phase_handoffs":
            reference[
                "next_phase_handoffs"
            ],

        "closure_criteria":
            criteria,

        "guardrails":
            reference[
                "guardrails"
            ],

        "generated_products": [
            "data/processed/phase2/phase2_integrated_operational_threads.csv",
            "data/processed/phase2/phase2_domain_closure.csv",
            "data/processed/phase2/phase2_integrated_operations_summary.json",
            "docs/assets/phase2/phase2k_integrated_operational_threads.svg",
            "docs/assets/phase2/phase2k_domain_closure.svg",
        ],
    }

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary,
            f,
            indent=2,
        )

        f.write("\n")

    print(
        "Phase 2K Artemis II Phase 2 Integration & Closure"
    )

    print(
        "=" * 72
    )

    print()
    print("Flight dynamics integration: PASS")
    print("Communications integration: PASS")
    print("Propulsion integration: PASS")
    print("Maneuver integration: PASS")
    print("GNC integration: PASS")
    print("Shared mission clock: PASS")
    print("Expected constraint vs anomaly boundary: PASS")
    print("Propulsion assignment boundary: PASS")
    print("ONBOARD != GROUND != AROW boundary: PASS")
    print("OEM non-inference boundary: PASS")
    print("RTC2 communications non-causation boundary: PASS")
    print("Final correction-to-entry handoff: PASS")
    print("Downstream phase handoffs: PASS")
    print()

    print(
        "Integrated mission-clock anchors:",
        len(
            reference[
                "mission_clock_anchors"
            ]
        ),
    )

    print(
        "Integrated operational threads:",
        len(
            integrated_threads
        ),
    )

    print(
        "Reconstructable Phase 2 items:",
        len(
            reference[
                "phase2_reconstructable"
            ]
        ),
    )

    print(
        "Not reconstructable Phase 2 items:",
        len(
            reference[
                "phase2_not_reconstructable"
            ]
        ),
    )

    print()
    print(
        "PHASE 2K ANALYSIS COMPLETE"
    )


if __name__ == "__main__":
    main()
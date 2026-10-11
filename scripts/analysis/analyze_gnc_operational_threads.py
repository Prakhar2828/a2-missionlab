from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = ROOT / "data" / "reference" / "artemis_ii_gnc_operational_threads.json"
GNC_PATH = ROOT / "data" / "reference" / "artemis_ii_gnc_architecture.json"
MANUAL_PATH = ROOT / "data" / "reference" / "artemis_ii_manual_piloting_control_modes.json"
NAV_PATH = ROOT / "data" / "reference" / "artemis_ii_navigation_state_estimation.json"
MANEUVER_PATH = ROOT / "data" / "reference" / "artemis_ii_maneuver_operational_threads.json"

THREAD_CSV = ROOT / "data" / "processed" / "gnc" / "gnc_operational_threads.csv"
CLOSURE_CSV = ROOT / "data" / "processed" / "gnc" / "phase2j_closure_matrix.csv"
SUMMARY_PATH = ROOT / "data" / "processed" / "gnc" / "gnc_operational_threads_summary.json"

THREAD_FIGURE = ROOT / "docs" / "assets" / "gnc" / "phase2j4_gnc_operational_threads.svg"
CLOSURE_FIGURE = ROOT / "docs" / "assets" / "gnc" / "phase2j4_phase2j_closure.svg"

plt.rcParams["svg.hashsalt"] = "a2-missionlab"
SVG_METADATA = {"Date": None}


def fail(message):
    raise SystemExit(f"VALIDATION FAILED: {message}")


def load_json(path):
    if not path.exists():
        fail(f"missing file: {path}")
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def normalize_svg(path):
    text = path.read_text(encoding="utf-8")
    path.write_text(
        "\n".join(line.rstrip(" \t") for line in text.splitlines()) + "\n",
        encoding="utf-8",
    )


def thread_map(items):
    return {item["thread_id"]: item for item in items}


def step_map(thread):
    return {item["step_id"]: item for item in thread["operational_sequence"]}


def build_thread_figure(threads):
    rows = []

    for thread in threads:
        rows.append(
            [
                thread["name"],
                thread["classification"],
                str(len(thread["operational_sequence"])),
                "YES" if thread["anomaly"] else "NO",
            ]
        )

    fig, ax = plt.subplots(figsize=(17, 6))
    ax.axis("off")

    ax.set_title(
        "Phase 2J.4 Artemis II GNC Operational Threads",
        fontsize=15,
        pad=18,
    )

    table = ax.table(
        cellText=rows,
        colLabels=[
            "Operational Thread",
            "Classification",
            "Steps",
            "Anomaly",
        ],
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.8)

    ax.text(
        0.5,
        0.08,
        (
            "Operational threads integrate public evidence. They are not console logs, "
            "complete guidance laws, onboard filter histories, or thruster histories."
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
    normalize_svg(THREAD_FIGURE)


def build_closure_figure(reference):
    rows = []

    for phase_id, item in reference["phase2j_cross_phase_closure"].items():
        rows.append(
            [
                phase_id.upper(),
                item["name"],
                item["status"],
            ]
        )

    fig, ax = plt.subplots(figsize=(15, 5.5))
    ax.axis("off")

    ax.set_title(
        "Phase 2J GNC Reconstruction Closure",
        fontsize=15,
        pad=18,
    )

    table = ax.table(
        cellText=rows,
        colLabels=[
            "Subphase",
            "Scope",
            "Status",
        ],
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.8)

    ax.text(
        0.5,
        0.08,
        (
            "Detailed as-flown entry guidance remains deferred to Phase 4. "
            "Flight-control decision/rationale reconstruction remains deferred to Phase 7."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        CLOSURE_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(fig)
    normalize_svg(CLOSURE_FIGURE)


def main():
    reference = load_json(REFERENCE_PATH)
    gnc = load_json(GNC_PATH)
    manual = load_json(MANUAL_PATH)
    navigation = load_json(NAV_PATH)
    maneuvers = load_json(MANEUVER_PATH)

    expected_ids = {
        "reference": "phase2j4_artemis_ii_gnc_operational_threads",
        "gnc": "phase2j1_artemis_ii_gnc_architecture",
        "manual": "phase2j2_artemis_ii_manual_piloting_control_modes",
        "navigation": "phase2j3_artemis_ii_navigation_state_estimation",
        "maneuvers": "phase2i4_artemis_ii_maneuver_operational_threads",
    }

    observed_ids = {
        "reference": reference.get("dataset_id"),
        "gnc": gnc.get("dataset_id"),
        "manual": manual.get("dataset_id"),
        "navigation": navigation.get("dataset_id"),
        "maneuvers": maneuvers.get("dataset_id"),
    }

    for key, expected in expected_ids.items():
        if observed_ids[key] != expected:
            fail(f"{key} dataset ID mismatch")

    domains = reference["gnc_domain_model"]

    if list(domains) != ["navigation", "guidance", "control"]:
        fail("GNC domain order changed")

    if domains["navigation"]["phase2j_status"] != "RECONSTRUCTED_TO_PUBLIC_EVIDENCE_LIMIT":
        fail("navigation closure status changed")

    if domains["guidance"]["complete_as_flown_algorithm_public"] is not False:
        fail("complete as-flown guidance algorithm incorrectly claimed public")

    if domains["control"]["complete_as_flown_control_law_public"] is not False:
        fail("complete as-flown control law incorrectly claimed public")

    expected_sensor_ids = [
        "star_tracker",
        "imu",
        "gps_receiver",
        "barometric_altimeter",
        "optical_navigation_camera",
        "sun_sensor",
    ]

    gnc_sensor_ids = [
        item["sensor_id"]
        for item in gnc["onboard_navigation_architecture"]["sensors"]
    ]

    if gnc_sensor_ids != expected_sensor_ids:
        fail("Phase 2J.1 navigation sensor architecture changed")

    core = reference["core_architecture"]

    if core["onboard_navigation_sensor_ids"] != expected_sensor_ids:
        fail("Phase 2J.4 sensor architecture changed")

    if core["onboard_navigation_sensor_count"] != 6:
        fail("Phase 2J.4 sensor count changed")

    gnc_external = gnc["external_navigation_support"]

    if (
        len(gnc_external) != 1
        or gnc_external[0]["support_id"] != "deep_space_network_tracking"
        or gnc_external[0]["onboard_sensor"] is not False
    ):
        fail("Phase 2J.1 DSN boundary changed")

    if (
        core["external_navigation_support"]["support_id"]
        != "deep_space_network_tracking"
        or core["external_navigation_support"]["onboard_sensor"] is not False
    ):
        fail("Phase 2J.4 DSN boundary changed")

    manual_architecture = manual["manual_control_architecture"]

    if (
        core["manual_control"]["rotational_hand_controller_domain"]
        != manual_architecture["rotational_hand_controller"]["command_domain"]
        or core["manual_control"]["translational_hand_controller_domain"]
        != manual_architecture["translational_hand_controller"]["command_domain"]
        or core["manual_control"]["hand_controller_is_direct_thruster_switch"] is not False
        or core["manual_control"]["command_path"]
        != manual_architecture["command_path"]
    ):
        fail("manual-control architecture integration failed")

    expected_effector_counts = {
        "main_engine_oms_e": 1,
        "auxiliary_r4d11": 8,
        "reaction_control_system": 24,
    }

    observed_effector_counts = {
        item["effector_id"]: item["count"]
        for item in core["control_effectors"]
    }

    if observed_effector_counts != expected_effector_counts:
        fail("control-effector architecture changed")

    if (
        core["correction_burn_engine_assignments_resolved"] != 0
        or core["correction_burn_engine_assignments_unresolved"] != 4
        or core["unresolved_correction_burns"]
        != ["otc3", "rtc1", "rtc2", "rtc3"]
    ):
        fail("correction-burn engine-assignment boundary changed")

    if (
        maneuvers["propulsion_boundary"]["correction_burn_engine_assignments_resolved"]
        != 0
        or maneuvers["propulsion_boundary"]["correction_burn_engine_assignments_unresolved"]
        != 4
    ):
        fail("Phase 2I.4 propulsion-assignment boundary changed")

    state_boundary = reference["state_product_boundary"]

    expected_state_products = [
        "ONBOARD_NAVIGATION_STATE",
        "GROUND_ORBIT_DETERMINATION",
        "AROW_PUBLIC_STATE_VECTOR",
    ]

    if state_boundary["products"] != expected_state_products:
        fail("Phase 2J.4 state-product taxonomy changed")

    nav_products = [
        item["product_id"]
        for item in navigation["navigation_state_product_taxonomy"]["products"]
    ]

    if nav_products != expected_state_products:
        fail("Phase 2J.3 state-product taxonomy changed")

    expected_statement = (
        "ONBOARD_NAVIGATION_STATE != "
        "GROUND_ORBIT_DETERMINATION != "
        "AROW_PUBLIC_STATE_VECTOR"
    )

    if (
        state_boundary["statement"] != expected_statement
        or navigation["critical_state_product_boundary"]["statement"]
        != expected_statement
        or state_boundary["arow_equals_onboard_filter_state_proven"] is not False
        or state_boundary["arow_equals_complete_ground_navigation_solution_proven"]
        is not False
    ):
        fail("state-product evidence boundary failed")

    threads = reference["operational_threads"]

    expected_thread_ids = [
        "proximity_operations_gnc",
        "flight_day_4_manual_piloting",
        "deep_space_navigation",
        "trajectory_correction_gnc",
        "final_correction_to_entry_handoff",
    ]

    observed_thread_ids = [
        item["thread_id"]
        for item in threads
    ]

    if observed_thread_ids != expected_thread_ids:
        fail("Phase 2J.4 operational thread set changed")

    for thread in threads:
        orders = [
            item["order"]
            for item in thread["operational_sequence"]
        ]

        if orders != list(range(1, len(orders) + 1)):
            fail(f"non-contiguous step order in {thread['thread_id']}")

    threads_by_id = thread_map(threads)

    proximity = threads_by_id["proximity_operations_gnc"]
    proximity_steps = step_map(proximity)
    manual_proximity = manual["proximity_operations"]["as_flown"]

    if (
        proximity["execution_status"] != "COMPLETED"
        or proximity["duration_minutes"] != 70.0
        or manual_proximity["execution_status"] != "COMPLETED"
        or manual_proximity["duration_minutes"] != 70.0
        or proximity_steps["onboard_navigation_sensor_use"]["onboard_navigation_sensors_used"]
        is not True
        or manual_proximity["onboard_navigation_sensors_used"] is not True
        or proximity_steps["reaction_control_thruster_use"]["reaction_control_thrusters_used"]
        is not True
        or manual_proximity["reaction_control_thrusters_used"] is not True
        or proximity_steps["automated_departure"]["status"]
        != "AS_FLOWN_CONFIRMED"
        or manual_proximity["automated_departure_confirmed"] is not True
    ):
        fail("proximity-operations GNC integration failed")

    fd4_thread = threads_by_id["flight_day_4_manual_piloting"]
    fd4 = manual["flight_day_4_manual_piloting"]

    if (
        fd4_thread["execution_status"] != "COMPLETED"
        or fd4_thread["derived_start_utc"] != fd4["derived_start_utc"]
        or fd4_thread["derived_start_met"] != fd4["derived_start_met"]
        or fd4_thread["duration_minutes"] != fd4["duration_minutes"]
        or fd4_thread["derived_end_utc"] != fd4["derived_end_utc"]
        or fd4_thread["derived_end_met"] != fd4["derived_end_met"]
    ):
        fail("Flight Day 4 GNC integration failed")

    deep_space = threads_by_id["deep_space_navigation"]
    deep_steps = step_map(deep_space)

    nav_as_flown = navigation[
        "artemis_ii_as_flown_navigation_evidence"
    ]

    if (
        deep_space["critical_boundary"] != expected_statement
        or deep_steps["optical_navigation_imagery"]["earth_images_captured"]
        is not True
        or deep_steps["optical_navigation_imagery"]["moon_images_captured"]
        is not True
        or nav_as_flown["optical_navigation_imagery"]["earth_images_captured"]
        is not True
        or nav_as_flown["optical_navigation_imagery"]["moon_images_captured"]
        is not True
        or deep_steps["deep_space_network_support"]["onboard_sensor"] is not False
        or deep_steps["arow_public_state_product"]["proven_equal_to_onboard_filter_state"]
        is not False
    ):
        fail("deep-space navigation integration failed")

    correction = threads_by_id["trajectory_correction_gnc"]
    correction_steps = step_map(correction)

    if (
        correction_steps["otc3_execution"]["duration_seconds"] != 17.5
        or correction_steps["rtc1_execution"]["reported_delta_v_ft_s"] != 1.6
        or correction_steps["rtc2_execution"]["reported_delta_v_ft_s"] != 5.3
        or correction_steps["rtc3_execution"]["reported_delta_v_ft_s"] != 4.2
    ):
        fail("trajectory-correction maneuver values changed")

    monitoring = navigation[
        "artemis_ii_as_flown_navigation_evidence"
    ]["trajectory_correction_navigation_monitoring"]

    confirmed_ids = [
        item["maneuver_id"]
        for item in monitoring["confirmed_as_flown_examples"]
    ]

    planned_ids = [
        item["maneuver_id"]
        for item in monitoring["planned_or_preburn_monitoring_context"]
    ]

    if confirmed_ids != ["rtc1", "rtc3"]:
        fail("as-flown correction monitoring evidence changed")

    if planned_ids != ["otc3", "rtc2"]:
        fail("planned correction monitoring context changed")

    oem = correction["public_oem_context"]

    if (
        oem["maneuver_brackets_audited"] != 4
        or oem["same_epoch_solution_comparisons_available"] != 3
        or oem["same_epoch_comparisons_are_navigation_error"] is not False
        or oem["same_epoch_comparisons_are_measured_burn_delta_v"] is not False
        or oem["creation_time_proves_maneuver_assimilation"] is not False
        or oem["maneuver_assimilation_status"] != "NOT_ESTABLISHED"
    ):
        fail("public OEM boundary failed")

    if (
        maneuvers["mission_summary"]["executed_corrections"] != 4
        or maneuvers["mission_summary"]["cancelled_corrections"] != 2
    ):
        fail("Phase 2I.4 maneuver accounting changed")

    final_thread = threads_by_id["final_correction_to_entry_handoff"]
    final_steps = step_map(final_thread)

    if (
        final_steps["rtc3"]["timestamp_utc"] != "2026-04-10T18:53:00Z"
        or final_steps["rtc3_to_entry_interval"]["interval_seconds"] != 18000.0
        or final_steps["entry_interface"]["timestamp_utc"]
        != "2026-04-10T23:53:00Z"
    ):
        fail("final correction-to-entry public clock handoff changed")

    if (
        final_thread["phase2j_boundary"][
            "final_correction_to_entry_clock_relationship_established"
        ]
        is not True
    ):
        fail("final correction-to-entry relationship not established")

    for key in [
        "complete_final_navigation_state_vector_public",
        "complete_entry_targeting_covariance_public",
        "complete_entry_targeting_algorithm_public",
        "complete_entry_guidance_command_history_public",
        "complete_bank_command_history_public",
        "complete_entry_control_command_history_public",
    ]:
        if final_thread["phase2j_boundary"][key] is not False:
            fail(f"unsupported entry detail introduced: {key}")

    closure = reference["phase2j_cross_phase_closure"]

    if list(closure) != ["phase2j1", "phase2j2", "phase2j3", "phase2j4"]:
        fail("Phase 2J closure matrix changed")

    if (
        closure["phase2j1"]["status"] != "COMPLETE"
        or closure["phase2j2"]["status"] != "COMPLETE"
        or closure["phase2j3"]["status"] != "COMPLETE"
        or closure["phase2j4"]["status"] != "COMPLETE"
    ):
        fail("Phase 2J subphase status mismatch")

    criteria = reference["closure_criteria"]

    for key, value in criteria.items():
        if key == "unsupported_telemetry_fabricated":
            if value is not False:
                fail("unsupported telemetry fabrication flag failed")
        elif value is not True:
            fail(f"closure criterion failed: {key}")

    if (
        "DETAILED_AS_FLOWN_ENTRY_GUIDANCE"
        not in reference["phase2j_not_reconstructable"]
    ):
        fail("entry-guidance non-reconstructable boundary missing")

    if (
        "DETAILED_AS_FLOWN_ENTRY_GUIDANCE_WHERE_PUBLIC_EVIDENCE_SUPPORTS_IT"
        not in reference["deferred_scope"]["phase4_entry_descent_splashdown_recovery"]
    ):
        fail("Phase 4 deferred entry-guidance scope missing")

    if (
        "DECISION_THREADS"
        not in reference["deferred_scope"]["phase7_mission_control_engineering_perspectives"]
    ):
        fail("Phase 7 deferred decision-thread scope missing")

    THREAD_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    THREAD_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    thread_rows = []

    for thread in threads:
        domains_seen = []

        for step in thread["operational_sequence"]:
            domain = step.get("gnc_domain")

            if domain and domain not in domains_seen:
                domains_seen.append(domain)

        thread_rows.append(
            {
                "thread_id": thread["thread_id"],
                "name": thread["name"],
                "classification": thread["classification"],
                "anomaly": str(thread["anomaly"]).lower(),
                "step_count": len(thread["operational_sequence"]),
                "gnc_domains": "|".join(domains_seen),
                "purpose": thread["purpose"],
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
                "name",
                "classification",
                "anomaly",
                "step_count",
                "gnc_domains",
                "purpose",
            ],
        )

        writer.writeheader()
        writer.writerows(thread_rows)

    closure_rows = []

    for phase_id, item in closure.items():
        closure_rows.append(
            {
                "phase_id": phase_id,
                "name": item["name"],
                "status": item["status"],
            }
        )

    with CLOSURE_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "phase_id",
                "name",
                "status",
            ],
        )

        writer.writeheader()
        writer.writerows(closure_rows)

    build_thread_figure(threads)
    build_closure_figure(reference)

    summary = {
        "product_id": "phase2j4_gnc_operational_threads_analysis",
        "mission": reference["mission"],
        "dependency_checks": {
            "phase2j1_gnc_architecture": "PASS",
            "phase2j2_manual_control": "PASS",
            "phase2j3_navigation_state_estimation": "PASS",
            "phase2i4_maneuver_operational_threads": "PASS",
        },
        "gnc_domains": {
            key: value["phase2j_status"]
            for key, value in domains.items()
        },
        "onboard_navigation_sensor_count": 6,
        "state_product_boundary": expected_statement,
        "operational_thread_count": len(threads),
        "operational_thread_ids": observed_thread_ids,
        "anomaly_thread_count": sum(
            1
            for item in threads
            if item["anomaly"]
        ),
        "correction_burn_engine_assignments_resolved": 0,
        "correction_burn_engine_assignments_unresolved": 4,
        "phase2j_subphase_status": {
            key: value["status"]
            for key, value in closure.items()
        },
        "closure_criteria": criteria,
        "reconstructable_count": len(
            reference["phase2j_reconstructable"]
        ),
        "not_reconstructable_count": len(
            reference["phase2j_not_reconstructable"]
        ),
        "deferred_scope": reference["deferred_scope"],
        "guardrails": reference["guardrails"],
        "generated_products": [
            "data/processed/gnc/gnc_operational_threads.csv",
            "data/processed/gnc/phase2j_closure_matrix.csv",
            "data/processed/gnc/gnc_operational_threads_summary.json",
            "docs/assets/gnc/phase2j4_gnc_operational_threads.svg",
            "docs/assets/gnc/phase2j4_phase2j_closure.svg",
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

    print("Phase 2J.4 GNC Operational Threads & Closure")
    print("=" * 72)
    print()
    print("Dependencies: PASS")
    print("GNC domains: PASS")
    print("Six-sensor navigation architecture: PASS")
    print("DSN ground-support boundary: PASS")
    print("ONBOARD != GROUND != AROW boundary: PASS")
    print("Manual-control architecture: PASS")
    print("Proximity-operations GNC thread: PASS")
    print("Flight Day 4 manual-piloting thread: PASS")
    print("Deep-space navigation thread: PASS")
    print("Trajectory-correction GNC thread: PASS")
    print("Final correction-to-entry handoff: PASS")
    print("Correction-engine assignment uncertainty: PASS")
    print("OEM non-inference boundary: PASS")
    print("Phase 4 entry-guidance deferral: PASS")
    print("Phase 7 mission-control deferral: PASS")
    print()
    print(f"Operational threads: {len(threads)}")
    print(
        "Reconstructable items: "
        f"{len(reference['phase2j_reconstructable'])}"
    )
    print(
        "Not reconstructable items: "
        f"{len(reference['phase2j_not_reconstructable'])}"
    )
    print()
    print("PHASE 2J.4 ANALYSIS COMPLETE")


if __name__ == "__main__":
    main()

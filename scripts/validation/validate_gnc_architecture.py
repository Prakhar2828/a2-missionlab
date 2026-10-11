from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_gnc_architecture.json"
)

PROPULSION_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_esm_propulsion_architecture.json"
)

COMPONENT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "gnc"
    / "gnc_architecture_components.csv"
)

BOUNDARY_CSV = (
    ROOT
    / "data"
    / "processed"
    / "gnc"
    / "gnc_evidence_boundaries.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "gnc"
    / "gnc_architecture_summary.json"
)

ARCHITECTURE_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "gnc"
    / "phase2j1_gnc_architecture.svg"
)

BOUNDARY_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "gnc"
    / "phase2j1_gnc_evidence_boundary.svg"
)

EXPECTED_DATASET_ID = (
    "phase2j1_artemis_ii_gnc_architecture"
)

EXPECTED_PRODUCT_ID = (
    "phase2j1_gnc_architecture_analysis"
)


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


def main():
    reference = load_json(
        REFERENCE_PATH
    )

    propulsion = load_json(
        PROPULSION_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    if (
        reference[
            "dataset_id"
        ]
        != EXPECTED_DATASET_ID
    ):
        fail(
            "reference dataset ID mismatch"
        )

    if (
        summary[
            "product_id"
        ]
        != EXPECTED_PRODUCT_ID
    ):
        fail(
            "summary product ID mismatch"
        )

    sources = (
        reference[
            "sources"
        ]
    )

    if len(
        sources
    ) != 7:
        fail(
            "expected seven curated NASA sources"
        )

    for source in sources:
        if (
            source[
                "organization"
            ]
            != "NASA"
        ):
            fail(
                "non-NASA Phase 2J.1 source introduced"
            )

        if (
            not source[
                "url"
            ].startswith(
                "https://www.nasa.gov/"
            )
        ):
            fail(
                "unexpected Phase 2J.1 source domain"
            )

        if "?" in source[
            "url"
        ]:
            fail(
                "tracking/query parameter present "
                "in canonical source URL"
            )

    domains = (
        reference[
            "gnc_domain_model"
        ]
    )

    if list(
        domains
    ) != [
        "navigation",
        "guidance",
        "control",
    ]:
        fail(
            "GNC domain order changed"
        )

    software = (
        reference[
            "gncp_flight_software"
        ]
    )

    required_true = [
        "receives_navigation_sensor_inputs",
        "receives_pilot_control_inputs",
        "accepts_ground_commands",
        "accepts_crew_commands",
        "manual_mode_supported",
        "automated_mode_supported",
        "commands_effectors",
    ]

    for key in required_true:
        if (
            software[
                key
            ]
            is not True
        ):
            fail(
                f"GNC&P software architecture failed: {key}"
            )

    if (
        software[
            "public_source_code_available_in_current_source_set"
        ]
        is not False
        or software[
            "complete_control_law_available_in_current_source_set"
        ]
        is not False
        or software[
            "complete_guidance_algorithm_available_in_current_source_set"
        ]
        is not False
    ):
        fail(
            "unsupported software disclosure introduced"
        )

    sensors = (
        reference[
            "onboard_navigation_architecture"
        ][
            "sensors"
        ]
    )

    expected_sensor_ids = [
        "star_tracker",
        "imu",
        "gps_receiver",
        "barometric_altimeter",
        "optical_navigation_camera",
        "sun_sensor",
    ]

    if [
        item[
            "sensor_id"
        ]
        for item in sensors
    ] != expected_sensor_ids:
        fail(
            "navigation sensor set changed"
        )

    if len(
        sensors
    ) != 6:
        fail(
            "expected six onboard navigation sensor classes"
        )

    for sensor in sensors:
        if (
            sensor[
                "raw_artemis_ii_measurements_available_in_current_source_set"
            ]
            is not False
        ):
            fail(
                f"{sensor['sensor_id']} raw history "
                "incorrectly marked available"
            )

    gps = next(
        item
        for item in sensors
        if item[
            "sensor_id"
        ] == "gps_receiver"
    )

    if (
        gps[
            "deep_space_primary_navigation"
        ]
        is not False
    ):
        fail(
            "GPS incorrectly promoted to "
            "deep-space primary navigation"
        )

    opnav = next(
        item
        for item in sensors
        if item[
            "sensor_id"
        ] == "optical_navigation_camera"
    )

    if (
        opnav[
            "emergency_return_role"
        ]
        is not True
        or opnav[
            "autonomous_lost_communications_role_reported"
        ]
        is not True
    ):
        fail(
            "OpNav emergency-return role changed"
        )

    sun = next(
        item
        for item in sensors
        if item[
            "sensor_id"
        ] == "sun_sensor"
    )

    if (
        sun[
            "primary_trajectory_navigation_sensor"
        ]
        is not False
    ):
        fail(
            "Sun sensor incorrectly promoted "
            "to primary trajectory navigation"
        )

    external = (
        reference[
            "external_navigation_support"
        ]
    )

    if (
        len(
            external
        )
        != 1
        or external[
            0
        ][
            "support_id"
        ]
        != "deep_space_network_tracking"
        or external[
            0
        ][
            "onboard_sensor"
        ]
        is not False
    ):
        fail(
            "DSN onboard/external boundary failed"
        )

    manual = (
        reference[
            "manual_control_architecture"
        ]
    )

    if (
        manual[
            "rotational_hand_controller"
        ][
            "command_domain"
        ]
        != "ATTITUDE"
    ):
        fail(
            "RHC command domain changed"
        )

    if (
        manual[
            "translational_hand_controller"
        ][
            "command_domain"
        ]
        != "TRANSLATION"
    ):
        fail(
            "THC command domain changed"
        )

    if (
        manual[
            "rotational_hand_controller"
        ][
            "direct_thruster_command_device"
        ]
        is not False
        or manual[
            "translational_hand_controller"
        ][
            "direct_thruster_command_device"
        ]
        is not False
    ):
        fail(
            "manual controllers incorrectly modeled "
            "as direct thruster switches"
        )

    if (
        manual[
            "exact_controller_input_time_history_available_in_current_source_set"
        ]
        is not False
        or manual[
            "exact_thruster_command_history_available_in_current_source_set"
        ]
        is not False
    ):
        fail(
            "unsupported manual-control history introduced"
        )

    engine_classes = {
        item[
            "engine_class_id"
        ]:
            item
        for item in propulsion[
            "architecture"
        ][
            "engine_classes"
        ]
    }

    expected_counts = {
        "main_engine_oms_e":
            1,

        "auxiliary_r4d11":
            8,

        "reaction_control_system":
            24,
    }

    effectors = {
        item[
            "effector_id"
        ]:
            item
        for item in reference[
            "control_effectors"
        ]
    }

    for effector_id, expected_count in (
        expected_counts.items()
    ):
        if (
            engine_classes[
                effector_id
            ][
                "count"
            ]
            != expected_count
            or effectors[
                effector_id
            ][
                "count"
            ]
            != expected_count
        ):
            fail(
                f"{effector_id} cross-phase count mismatch"
            )

    if (
        effectors[
            "main_engine_oms_e"
        ][
            "burn_specific_correction_assignment_implied"
        ]
        is not False
        or effectors[
            "auxiliary_r4d11"
        ][
            "burn_specific_correction_assignment_implied"
        ]
        is not False
    ):
        fail(
            "correction engine assignment incorrectly inferred"
        )

    anchors = (
        reference[
            "artemis_ii_operational_anchors"
        ]
    )

    if [
        item[
            "event_id"
        ]
        for item in anchors
    ] != [
        "proximity_operations_demonstration",
        "flight_day_4_manual_piloting",
        "flight_day_8_manual_piloting",
    ]:
        fail(
            "operational-anchor order changed"
        )

    proximity = anchors[
        0
    ]

    if (
        proximity[
            "execution_status"
        ]
        != "COMPLETED"
        or proximity[
            "duration_semantics"
        ]
        != "APPROXIMATELY"
        or proximity[
            "duration_minutes"
        ]
        != 70
        or proximity[
            "onboard_navigation_sensors_used"
        ]
        is not True
        or proximity[
            "reaction_control_thrusters_used"
        ]
        is not True
        or proximity[
            "automated_departure_burn_afterward"
        ]
        is not True
    ):
        fail(
            "proximity-operations evidence changed"
        )

    flight_day_4 = anchors[
        1
    ]

    if (
        flight_day_4[
            "execution_status"
        ]
        != "COMPLETED"
        or flight_day_4[
            "duration_minutes"
        ]
        != 41
        or flight_day_4[
            "tested_modes"
        ]
        != [
            "SIX_DEGREES_OF_FREEDOM",
            "THREE_DEGREES_OF_FREEDOM",
        ]
        or flight_day_4[
            "mode_names_define_complete_control_algorithm"
        ]
        is not False
    ):
        fail(
            "Flight Day 4 evidence changed"
        )

    flight_day_8 = anchors[
        2
    ]

    if (
        flight_day_8[
            "execution_status"
        ]
        != "FOREGONE"
        or flight_day_8[
            "performed"
        ]
        is not False
    ):
        fail(
            "Flight Day 8 foregone boundary failed"
        )

    related = (
        reference[
            "related_measurement_context"
        ]
    )

    if (
        len(
            related
        )
        != 1
        or related[
            0
        ][
            "system"
        ]
        != "DOCKING_CAMERA"
        or related[
            0
        ][
            "classified_as_primary_artemis_ii_onboard_navigation_sensor_here"
        ]
        is not False
    ):
        fail(
            "docking-camera evidence boundary changed"
        )

    boundaries = (
        reference[
            "current_public_source_set_boundaries"
        ]
    )

    expected_true = {
        "sensor_architecture_available",
        "sensor_roles_available",
        "gncp_flight_software_architecture_available",
        "manual_control_architecture_available",
        "as_flown_manual_control_event_sequence_available",
        "six_dof_three_dof_execution_available",
    }

    for key, value in (
        boundaries.items()
    ):
        if key in expected_true:
            if value is not True:
                fail(
                    f"expected available boundary failed: {key}"
                )
        else:
            if value is not False:
                fail(
                    f"unsupported evidence became available: {key}"
                )

    cross_phase = (
        reference[
            "cross_phase_boundaries"
        ]
    )

    required_false = [
        "arow_oem_state_vector_is_onboard_navigation_filter_state",
        "dsn_orbit_determination_is_onboard_sensor_measurement",
        "propulsion_architecture_is_exact_control_effector_history",
        "trajectory_correction_outcome_is_guidance_command_history",
        "correction_burn_engine_assignment_resolved_by_gnc_architecture",
    ]

    for key in required_false:
        if (
            cross_phase[
                key
            ]
            is not False
        ):
            fail(
                f"cross-phase non-inference failed: {key}"
            )

    if (
        cross_phase[
            "phase_2i_unresolved_correction_engine_assignments_preserved"
        ]
        is not True
    ):
        fail(
            "Phase 2I engine-assignment boundary lost"
        )

    if not COMPONENT_CSV.exists():
        fail(
            "architecture component CSV missing"
        )

    with COMPONENT_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        component_rows = list(
            csv.DictReader(f)
        )

    if len(
        component_rows
    ) != 13:
        fail(
            "architecture component CSV must contain 13 rows"
        )

    if not BOUNDARY_CSV.exists():
        fail(
            "evidence boundary CSV missing"
        )

    with BOUNDARY_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        boundary_rows = list(
            csv.DictReader(f)
        )

    if len(
        boundary_rows
    ) != len(
        boundaries
    ):
        fail(
            "evidence boundary CSV row count mismatch"
        )

    if (
        summary[
            "domain_count"
        ]
        != 3
        or summary[
            "onboard_navigation_sensor_count"
        ]
        != 6
        or summary[
            "external_navigation_support_count"
        ]
        != 1
        or summary[
            "manual_controller_count"
        ]
        != 2
        or summary[
            "control_effector_class_count"
        ]
        != 3
        or summary[
            "architecture_component_rows"
        ]
        != 13
        or summary[
            "operational_anchor_count"
        ]
        != 3
    ):
        fail(
            "summary architecture counts changed"
        )

    if (
        summary[
            "current_public_source_set_boundaries"
        ]
        != boundaries
        or summary[
            "cross_phase_boundaries"
        ]
        != cross_phase
        or summary[
            "guardrails"
        ]
        != reference[
            "guardrails"
        ]
    ):
        fail(
            "summary evidence boundaries mismatch"
        )

    for figure in [
        ARCHITECTURE_FIGURE,
        BOUNDARY_FIGURE,
    ]:
        if not figure.exists():
            fail(
                f"missing figure: {figure}"
            )

        svg = figure.read_text(
            encoding="utf-8"
        )

        if (
            "<svg" not in svg
            or len(
                svg
            ) < 1000
        ):
            fail(
                f"invalid SVG: {figure}"
            )

    print()
    print(
        "Phase 2J.1 GNC Architecture / Evidence Validation"
    )

    print("=" * 72)

    print()
    print(
        "GNC domain decomposition:"
    )

    print(
        "  navigation: PASS"
    )

    print(
        "  guidance: PASS"
    )

    print(
        "  control: PASS"
    )

    print()
    print(
        "GNC&P flight software:"
    )

    print(
        "  navigation-sensor inputs: PASS"
    )

    print(
        "  pilot-control inputs: PASS"
    )

    print(
        "  crew commands: PASS"
    )

    print(
        "  ground commands: PASS"
    )

    print(
        "  manual + automated modes: PASS"
    )

    print(
        "  effector commanding: PASS"
    )

    print()
    print(
        "Onboard navigation architecture:"
    )

    print(
        "  sensor classes: 6"
    )

    print(
        "  star tracker: PASS"
    )

    print(
        "  IMU: PASS"
    )

    print(
        "  GPS: PASS"
    )

    print(
        "  barometric altimeter: PASS"
    )

    print(
        "  optical navigation camera: PASS"
    )

    print(
        "  Sun sensor: PASS"
    )

    print()
    print(
        "External navigation support:"
    )

    print(
        "  DSN tracking: PASS"
    )

    print(
        "  onboard sensor: FALSE"
    )

    print()
    print(
        "Manual-control architecture:"
    )

    print(
        "  RHC -> attitude: PASS"
    )

    print(
        "  THC -> translation: PASS"
    )

    print(
        "  direct thruster switches: FALSE"
    )

    print(
        "  exact controller history public: FALSE"
    )

    print(
        "  exact thruster history public: FALSE"
    )

    print()
    print(
        "Control-effectors cross-check:"
    )

    print(
        "  OMS-E: 1"
    )

    print(
        "  auxiliary: 8"
    )

    print(
        "  RCS: 24"
    )

    print(
        "  correction engine assignment inferred: FALSE"
    )

    print()
    print(
        "Artemis II operational anchors:"
    )

    print(
        "  proximity operations:"
    )

    print(
        "    COMPLETED"
    )

    print(
        "    approximately 70 min"
    )

    print(
        "    onboard navigation sensors: USED"
    )

    print(
        "    RCS: USED"
    )

    print(
        "  Flight Day 4 manual piloting:"
    )

    print(
        "    COMPLETED"
    )

    print(
        "    41 min"
    )

    print(
        "    6-DOF / 3-DOF: PASS"
    )

    print(
        "  Flight Day 8 manual piloting:"
    )

    print(
        "    FOREGONE"
    )

    print()
    print(
        "Evidence boundaries:"
    )

    print(
        "  raw sensor histories: NOT AVAILABLE"
    )

    print(
        "  attitude time series: NOT AVAILABLE"
    )

    print(
        "  navigation-filter state history: NOT AVAILABLE"
    )

    print(
        "  navigation covariance: NOT AVAILABLE"
    )

    print(
        "  guidance-target history: NOT AVAILABLE"
    )

    print(
        "  complete control law: NOT AVAILABLE"
    )

    print(
        "  manual controller time history: NOT AVAILABLE"
    )

    print()
    print(
        "Cross-phase interpretation:"
    )

    print(
        "  AROW/OEM state = onboard filter state: FALSE"
    )

    print(
        "  DSN tracking = onboard sensor: FALSE"
    )

    print(
        "  propulsion architecture = exact effector history: FALSE"
    )

    print(
        "  maneuver outcome = guidance command history: FALSE"
    )

    print(
        "  Phase 2I unresolved assignments preserved: PASS"
    )

    print()
    print(
        "Products:"
    )

    print(
        "  architecture component CSV rows: 13"
    )

    print(
        f"  evidence boundary CSV rows: {len(boundaries)}"
    )

    print(
        "  summary: PASS"
    )

    print(
        "  architecture figure: PASS"
    )

    print(
        "  evidence-boundary figure: PASS"
    )

    print()
    print(
        "OK: Phase 2J.1 GNC domain decomposition, GNC&P "
        "flight-software architecture, onboard navigation "
        "sensor roles, external DSN boundary, manual-control "
        "interfaces, propulsion-effectors cross-check, Artemis II "
        "as-flown manual-control anchors, source-set availability "
        "boundaries, cross-phase non-inference guardrails, "
        "generated products, and evidence discipline independently "
        "validated."
    )


if __name__ == "__main__":
    main()
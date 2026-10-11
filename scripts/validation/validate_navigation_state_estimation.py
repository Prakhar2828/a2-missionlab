from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_navigation_state_estimation.json"
)

GNC_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_gnc_architecture.json"
)

MANUAL_CONTROL_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_manual_piloting_control_modes.json"
)

MANEUVER_CORRELATION_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_trajectory_correlation.json"
)

TAXONOMY_CSV = (
    ROOT
    / "data"
    / "processed"
    / "gnc"
    / "navigation_state_product_taxonomy.csv"
)

BOUNDARY_CSV = (
    ROOT
    / "data"
    / "processed"
    / "gnc"
    / "navigation_evidence_boundaries.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "gnc"
    / "navigation_state_estimation_summary.json"
)

ARCHITECTURE_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "gnc"
    / "phase2j3_navigation_architecture.svg"
)

BOUNDARY_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "gnc"
    / "phase2j3_state_product_boundaries.svg"
)

EXPECTED_DATASET_ID = (
    "phase2j3_artemis_ii_navigation_state_estimation"
)

EXPECTED_PRODUCT_ID = (
    "phase2j3_navigation_state_estimation_analysis"
)


def fail(message):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
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


def load_csv(path):
    if not path.exists():
        fail(
            f"missing file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        return list(
            csv.DictReader(
                f
            )
        )


def validate_svg(path):
    if not path.exists():
        fail(
            f"missing SVG: {path}"
        )

    if (
        path.stat().st_size
        < 1000
    ):
        fail(
            f"SVG unexpectedly small: {path}"
        )

    text = path.read_text(
        encoding="utf-8",
    )

    if (
        "<svg"
        not in text
    ):
        fail(
            f"invalid SVG content: {path}"
        )


def main():
    reference = load_json(
        REFERENCE_PATH
    )

    gnc = load_json(
        GNC_PATH
    )

    manual_control = load_json(
        MANUAL_CONTROL_PATH
    )

    maneuver_correlation = load_json(
        MANEUVER_CORRELATION_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    taxonomy_rows = load_csv(
        TAXONOMY_CSV
    )

    boundary_rows = load_csv(
        BOUNDARY_CSV
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

    if (
        gnc[
            "dataset_id"
        ]
        != "phase2j1_artemis_ii_gnc_architecture"
    ):
        fail(
            "Phase 2J.1 dependency mismatch"
        )

    if (
        manual_control[
            "dataset_id"
        ]
        != "phase2j2_artemis_ii_manual_piloting_control_modes"
    ):
        fail(
            "Phase 2J.2 dependency mismatch"
        )

    if (
        maneuver_correlation[
            "dataset_id"
        ]
        != "phase2i3_artemis_ii_maneuver_trajectory_correlation"
    ):
        fail(
            "Phase 2I.3 dependency mismatch"
        )

    serialized_reference = json.dumps(
        reference,
        ensure_ascii=False,
    )

    copy_artifacts = [
        "innovations,covariance",
        "thevehicle",
        "andis",
        "dataproduct",
        "maneuverdelta-v",
        "herefor",
    ]

    for artifact in copy_artifacts:
        if (
            artifact
            in serialized_reference
        ):
            fail(
                "reference contains copy/paste artifact: "
                f"{artifact}"
            )

    sources = (
        reference[
            "sources"
        ]
    )

    if (
        len(
            sources
        )
        != 9
    ):
        fail(
            "expected nine curated Phase 2J.3 sources"
        )

    for source in sources:
        if (
            source[
                "organization"
            ]
            != "NASA"
        ):
            fail(
                "non-NASA Phase 2J.3 source introduced"
            )

        url = (
            source[
                "url"
            ]
        )

        if not (
            url.startswith(
                "https://www.nasa.gov/"
            )
            or url.startswith(
                "https://pds.nasa.gov/"
            )
        ):
            fail(
                "unexpected Phase 2J.3 source domain"
            )

        if (
            "utm_"
            in url.lower()
        ):
            fail(
                "tracking parameter present in source URL"
            )

    expected_sensor_ids = [
        "star_tracker",
        "imu",
        "gps_receiver",
        "barometric_altimeter",
        "optical_navigation_camera",
        "sun_sensor",
    ]

    gnc_sensor_ids = [
        item[
            "sensor_id"
        ]
        for item in (
            gnc[
                "onboard_navigation_architecture"
            ][
                "sensors"
            ]
        )
    ]

    reference_sensor_ids = [
        item[
            "sensor_id"
        ]
        for item in (
            reference[
                "onboard_navigation_sensor_capability_context"
            ]
        )
    ]

    if (
        gnc_sensor_ids
        != expected_sensor_ids
    ):
        fail(
            "Phase 2J.1 sensor architecture changed"
        )

    if (
        reference_sensor_ids
        != expected_sensor_ids
    ):
        fail(
            "Phase 2J.3 sensor architecture changed"
        )

    if (
        gnc_sensor_ids
        != reference_sensor_ids
    ):
        fail(
            "Phase 2J.1 / Phase 2J.3 sensor mismatch"
        )

    gnc_external = (
        gnc[
            "external_navigation_support"
        ]
    )

    if (
        len(
            gnc_external
        )
        != 1
        or gnc_external[
            0
        ][
            "support_id"
        ]
        != "deep_space_network_tracking"
        or gnc_external[
            0
        ][
            "onboard_sensor"
        ]
        is not False
    ):
        fail(
            "Phase 2J.1 DSN boundary changed"
        )

    external = (
        reference[
            "external_navigation_support"
        ]
    )

    if (
        external[
            "support_id"
        ]
        != "deep_space_network_tracking"
        or external[
            "onboard_sensor"
        ]
        is not False
        or external[
            "equivalent_to_onboard_navigation_filter"
        ]
        is not False
    ):
        fail(
            "Phase 2J.3 DSN boundary failed"
        )

    taxonomy = (
        reference[
            "navigation_state_product_taxonomy"
        ]
    )

    if (
        taxonomy[
            "taxonomy_is_missionlab_normalization"
        ]
        is not True
    ):
        fail(
            "MissionLab taxonomy provenance failed"
        )

    products = (
        taxonomy[
            "products"
        ]
    )

    expected_product_ids = [
        "ONBOARD_NAVIGATION_STATE",
        "GROUND_ORBIT_DETERMINATION",
        "AROW_PUBLIC_STATE_VECTOR",
    ]

    product_ids = [
        item[
            "product_id"
        ]
        for item in products
    ]

    if (
        product_ids
        != expected_product_ids
    ):
        fail(
            "navigation state-product taxonomy changed"
        )

    product_map = {
        item[
            "product_id"
        ]:
            item
        for item in products
    }

    if (
        product_map[
            "GROUND_ORBIT_DETERMINATION"
        ][
            "exact_label_is_claimed_as_nasa_public_product_name"
        ]
        is not False
    ):
        fail(
            "MissionLab normalized ground-navigation category "
            "was promoted to a NASA product name"
        )

    if (
        product_map[
            "AROW_PUBLIC_STATE_VECTOR"
        ][
            "proven_equal_to_onboard_navigation_filter_state"
        ]
        is not False
    ):
        fail(
            "AROW was promoted to onboard filter state"
        )

    critical = (
        reference[
            "critical_state_product_boundary"
        ]
    )

    if (
        critical[
            "onboard_navigation_state_equals_ground_orbit_determination"
        ]
        is not False
        or critical[
            "onboard_navigation_state_equals_arow_public_state_vector"
        ]
        is not False
        or critical[
            "ground_orbit_determination_equals_arow_public_state_vector"
        ]
        is not False
    ):
        fail(
            "critical state-product separation failed"
        )

    expected_boundary_statement = (
        "ONBOARD_NAVIGATION_STATE != "
        "GROUND_ORBIT_DETERMINATION != "
        "AROW_PUBLIC_STATE_VECTOR"
    )

    if (
        critical[
            "statement"
        ]
        != expected_boundary_statement
    ):
        fail(
            "critical boundary statement changed"
        )

    arow = (
        reference[
            "arow_public_product_context"
        ]
    )

    for key in [
        "state_vectors_publicly_provided",
        "downloadable_ephemeris_publicly_provided",
        "arow_visualizes_data_associated_with_orion_and_mission_control",
    ]:
        if (
            arow[
                key
            ]
            is not True
        ):
            fail(
                f"AROW evidence failed: {key}"
            )

    for key in [
        "public_state_vector_proven_to_be_raw_sensor_data",
        "public_state_vector_proven_equal_to_onboard_navigation_filter_state",
        "public_state_vector_proven_equal_to_complete_ground_orbit_determination_solution",
        "public_state_vector_generation_algorithm_available_in_current_source_set",
    ]:
        if (
            arow[
                key
            ]
            is not False
        ):
            fail(
                f"unsupported AROW inference introduced: {key}"
            )

    as_flown = (
        reference[
            "artemis_ii_as_flown_navigation_evidence"
        ]
    )

    opnav = (
        as_flown[
            "optical_navigation_imagery"
        ]
    )

    if (
        opnav[
            "system"
        ]
        != "OPTICAL_NAVIGATION_CAMERA"
        or opnav[
            "execution_status"
        ]
        != "AS_FLOWN_CONFIRMED"
        or opnav[
            "earth_images_captured"
        ]
        is not True
        or opnav[
            "moon_images_captured"
        ]
        is not True
        or opnav[
            "flight_day_1_earth_image_publicly_identified_as_opnav"
        ]
        is not True
    ):
        fail(
            "as-flown OpNav evidence changed"
        )

    for key in [
        "image_capture_proves_specific_navigation_filter_update",
        "image_metadata_equals_navigation_state",
        "opnav_measurement_residual_history_public",
        "opnav_filter_innovation_history_public",
    ]:
        if (
            opnav[
                key
            ]
            is not False
        ):
            fail(
                f"unsupported OpNav estimator inference introduced: {key}"
            )

    proximity_j2 = (
        manual_control[
            "proximity_operations"
        ][
            "as_flown"
        ]
    )

    proximity_j3 = (
        as_flown[
            "proximity_operations_navigation"
        ]
    )

    if (
        proximity_j2[
            "onboard_navigation_sensors_used"
        ]
        is not True
        or proximity_j3[
            "onboard_navigation_sensors_used"
        ]
        is not True
    ):
        fail(
            "proximity navigation evidence mismatch"
        )

    for key in [
        "specific_sensor_set_publicly_identified",
        "individual_sensor_measurement_history_public",
        "relative_state_history_public",
        "navigation_filter_state_history_public",
    ]:
        if (
            proximity_j3[
                key
            ]
            is not False
        ):
            fail(
                f"unsupported proximity navigation detail introduced: {key}"
            )

    monitoring = (
        as_flown[
            "trajectory_correction_navigation_monitoring"
        ]
    )

    confirmed = (
        monitoring[
            "confirmed_as_flown_examples"
        ]
    )

    confirmed_ids = [
        item[
            "maneuver_id"
        ]
        for item in confirmed
    ]

    if (
        confirmed_ids
        != [
            "rtc1",
            "rtc3",
        ]
    ):
        fail(
            "confirmed as-flown monitoring examples changed"
        )

    for item in confirmed:
        if (
            item[
                "spacecraft_configuration_monitored"
            ]
            is not True
            or item[
                "navigation_data_monitored"
            ]
            is not True
        ):
            fail(
                "confirmed correction-burn monitoring evidence failed"
            )

    planned = (
        monitoring[
            "planned_or_preburn_monitoring_context"
        ]
    )

    planned_ids = [
        item[
            "maneuver_id"
        ]
        for item in planned
    ]

    if (
        planned_ids
        != [
            "otc3",
            "rtc2",
        ]
    ):
        fail(
            "planned/pre-burn monitoring context changed"
        )

    for item in planned:
        if (
            item[
                "promoted_to_complete_as_flown_display_history"
            ]
            is not False
        ):
            fail(
                "planned monitoring promoted to as-flown evidence"
            )

    if (
        monitoring[
            "as_flown_monitoring_confirmed_for_at_least_two_executed_correction_burns"
        ]
        is not True
        or monitoring[
            "all_executed_correction_burns_have_identical_public_monitoring_evidence"
        ]
        is not False
        or monitoring[
            "exact_displayed_variables_public"
        ]
        is not False
        or monitoring[
            "display_values_proven_equal_to_onboard_filter_state"
        ]
        is not False
        or monitoring[
            "display_time_history_public"
        ]
        is not False
    ):
        fail(
            "trajectory-correction display boundary failed"
        )

    oem_boundary = (
        reference[
            "public_oem_solution_evolution_boundary"
        ]
    )

    oem_brackets = (
        maneuver_correlation[
            "oem_creation_time_brackets"
        ]
    )

    if (
        len(
            oem_brackets
        )
        != 4
        or oem_boundary[
            "oem_maneuver_brackets_expected"
        ]
        != 4
    ):
        fail(
            "OEM maneuver bracket count changed"
        )

    if [
        item[
            "maneuver_id"
        ]
        for item in oem_brackets
    ] != [
        "otc3",
        "rtc1",
        "rtc2",
        "rtc3",
    ]:
        fail(
            "OEM maneuver order changed"
        )

    comparisons = [
        item[
            "same_epoch_solution_difference"
        ]
        for item in oem_brackets
        if item[
            "same_epoch_solution_difference"
        ][
            "available"
        ]
    ]

    if (
        len(
            comparisons
        )
        != 3
        or oem_boundary[
            "same_epoch_solution_comparisons_expected"
        ]
        != 3
    ):
        fail(
            "same-epoch OEM comparison count changed"
        )

    for comparison in comparisons:
        if (
            comparison[
                "navigation_error"
            ]
            is not False
            or comparison[
                "measured_burn_delta_v"
            ]
            is not False
        ):
            fail(
                "OEM comparison misinterpreted"
            )

    if (
        oem_boundary[
            "same_epoch_comparisons_are_navigation_error"
        ]
        is not False
        or oem_boundary[
            "same_epoch_comparisons_are_measured_burn_delta_v"
        ]
        is not False
        or oem_boundary[
            "oem_creation_time_proves_maneuver_assimilation"
        ]
        is not False
        or oem_boundary[
            "arow_state_vector_equals_onboard_navigation_filter_state"
        ]
        is not False
        or oem_boundary[
            "maneuver_assimilation_status_from_creation_time"
        ]
        != "NOT_ESTABLISHED"
    ):
        fail(
            "OEM interpretation boundary failed"
        )

    otc3 = (
        oem_brackets[
            0
        ]
    )

    if (
        otc3[
            "earliest_product_created_after_maneuver"
        ][
            "product"
        ]
        != "Artemis_II_OEM_2026_04_06_Pre-OTC3_to_EI.csv"
    ):
        fail(
            "OTC3 creation-time audit anchor changed"
        )

    if (
        oem_boundary[
            "important_example"
        ][
            "creation_time_proves_otc3_assimilation"
        ]
        is not False
    ):
        fail(
            "OTC3 creation-time inference boundary failed"
        )

    boundaries = (
        reference[
            "state_estimation_evidence_boundaries"
        ]
    )

    expected_true_keys = [
        "onboard_navigation_architecture_public",
        "onboard_sensor_roles_public",
        "dsn_ground_tracking_role_public",
        "arow_public_state_vectors_available",
        "arow_public_ephemeris_available",
        "artemis_ii_opnav_imagery_as_flown_confirmed",
        "proximity_ops_onboard_navigation_sensor_use_confirmed",
        "trajectory_correction_navigation_monitoring_as_flown_examples_confirmed",
    ]

    expected_false_keys = [
        "complete_onboard_navigation_state_history_public",
        "complete_ground_orbit_determination_solution_history_public",
        "raw_imu_time_history_public",
        "raw_star_tracker_time_history_public",
        "raw_gps_time_history_public",
        "raw_barometric_altimeter_time_history_public",
        "raw_sun_sensor_time_history_public",
        "complete_raw_opnav_measurement_time_history_public",
        "opnav_measurement_residual_history_public",
        "navigation_filter_innovation_history_public",
        "navigation_covariance_history_public",
        "filter_gain_history_public",
        "filter_bias_state_history_public",
        "sensor_selection_mode_history_public",
        "measurement_accept_reject_history_public",
        "complete_crew_navigation_display_history_public",
        "arow_equals_onboard_filter_state_proven",
        "arow_equals_complete_ground_navigation_solution_proven",
        "oem_difference_equals_navigation_error",
        "oem_difference_equals_measured_burn_delta_v",
        "oem_creation_time_proves_measurement_or_burn_assimilation",
    ]

    if (
        list(
            boundaries
        )
        != (
            expected_true_keys
            + expected_false_keys
        )
    ):
        fail(
            "state-estimation evidence boundary schema changed"
        )

    for key in expected_true_keys:
        if (
            boundaries[
                key
            ]
            is not True
        ):
            fail(
                f"expected evidence missing: {key}"
            )

    for key in expected_false_keys:
        if (
            boundaries[
                key
            ]
            is not False
        ):
            fail(
                f"unsupported evidence introduced: {key}"
            )

    if (
        len(
            taxonomy_rows
        )
        != 3
    ):
        fail(
            "taxonomy CSV row count mismatch"
        )

    if [
        row[
            "product_id"
        ]
        for row in taxonomy_rows
    ] != expected_product_ids:
        fail(
            "taxonomy CSV product order mismatch"
        )

    for row, product in zip(
        taxonomy_rows,
        products,
    ):
        if (
            row[
                "producer_context"
            ]
            != product[
                "producer_context"
            ]
            or row[
                "product_class"
            ]
            != product[
                "product_class"
            ]
            or row[
                "role"
            ]
            != product[
                "role"
            ]
        ):
            fail(
                "taxonomy CSV content mismatch"
            )

        if (
            row[
                "proven_equal_to_onboard_filter_state"
            ]
            != "false"
        ):
            fail(
                "taxonomy CSV onboard-filter boundary failed"
            )

    expected_history_flags = [
        "false",
        "false",
        "true",
    ]

    if [
        row[
            "complete_artemis_ii_history_public"
        ]
        for row in taxonomy_rows
    ] != expected_history_flags:
        fail(
            "taxonomy CSV public-history flags changed"
        )

    if (
        len(
            boundary_rows
        )
        != len(
            boundaries
        )
    ):
        fail(
            "boundary CSV row count mismatch"
        )

    expected_boundary_rows = [
        {
            "evidence_item":
                key,
            "established_in_current_public_source_set":
                str(
                    value
                ).lower(),
        }
        for key, value in boundaries.items()
    ]

    if (
        boundary_rows
        != expected_boundary_rows
    ):
        fail(
            "boundary CSV does not match reference dataset"
        )

    dependencies = (
        summary[
            "dependency_checks"
        ]
    )

    if (
        dependencies[
            "phase2j1_gnc_architecture"
        ]
        != "PASS"
        or dependencies[
            "phase2j2_manual_control_reconstruction"
        ]
        != "PASS"
        or dependencies[
            "phase2i3_oem_trajectory_correlation"
        ]
        != "PASS"
    ):
        fail(
            "summary dependency check failed"
        )

    if (
        summary[
            "onboard_navigation_sensor_count"
        ]
        != 6
        or summary[
            "onboard_navigation_sensor_ids"
        ]
        != expected_sensor_ids
    ):
        fail(
            "summary sensor architecture mismatch"
        )

    if (
        summary[
            "external_navigation_support"
        ][
            "support_id"
        ]
        != "deep_space_network_tracking"
        or summary[
            "external_navigation_support"
        ][
            "onboard_sensor"
        ]
        is not False
    ):
        fail(
            "summary DSN boundary mismatch"
        )

    if (
        summary[
            "navigation_state_product_ids"
        ]
        != expected_product_ids
    ):
        fail(
            "summary product taxonomy mismatch"
        )

    if (
        summary[
            "critical_state_product_boundary"
        ]
        != expected_boundary_statement
    ):
        fail(
            "summary critical boundary mismatch"
        )

    summary_as_flown = (
        summary[
            "artemis_ii_as_flown_navigation_evidence"
        ]
    )

    if (
        summary_as_flown[
            "opnav_earth_images_confirmed"
        ]
        is not True
        or summary_as_flown[
            "opnav_moon_images_confirmed"
        ]
        is not True
        or summary_as_flown[
            "proximity_onboard_navigation_sensor_use_confirmed"
        ]
        is not True
        or summary_as_flown[
            "trajectory_correction_as_flown_monitoring_examples"
        ]
        != [
            "rtc1",
            "rtc3",
        ]
        or summary_as_flown[
            "trajectory_correction_preburn_or_planned_monitoring_context"
        ]
        != [
            "otc3",
            "rtc2",
        ]
    ):
        fail(
            "summary as-flown navigation evidence mismatch"
        )

    summary_oem = (
        summary[
            "public_oem_audit"
        ]
    )

    if (
        summary_oem[
            "maneuver_brackets"
        ]
        != 4
        or summary_oem[
            "same_epoch_solution_comparisons"
        ]
        != 3
        or summary_oem[
            "comparisons_interpreted_as_navigation_error"
        ]
        is not False
        or summary_oem[
            "comparisons_interpreted_as_measured_burn_delta_v"
        ]
        is not False
        or summary_oem[
            "creation_time_proves_maneuver_assimilation"
        ]
        is not False
    ):
        fail(
            "summary OEM audit mismatch"
        )

    if (
        summary[
            "public_evidence_available_count"
        ]
        != len(
            expected_true_keys
        )
        or summary[
            "public_evidence_unavailable_count"
        ]
        != len(
            expected_false_keys
        )
    ):
        fail(
            "summary evidence counts mismatch"
        )

    if (
        summary[
            "reconstructable"
        ]
        != reference[
            "phase2j3_reconstructable"
        ]
    ):
        fail(
            "summary reconstructable set mismatch"
        )

    if (
        summary[
            "not_reconstructable"
        ]
        != reference[
            "phase2j3_not_reconstructable"
        ]
    ):
        fail(
            "summary non-reconstructable set mismatch"
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
            "summary guardrails mismatch"
        )

    expected_generated_products = [
        "data/processed/gnc/navigation_state_product_taxonomy.csv",
        "data/processed/gnc/navigation_evidence_boundaries.csv",
        "data/processed/gnc/navigation_state_estimation_summary.json",
        "docs/assets/gnc/phase2j3_navigation_architecture.svg",
        "docs/assets/gnc/phase2j3_state_product_boundaries.svg",
    ]

    if (
        summary[
            "generated_products"
        ]
        != expected_generated_products
    ):
        fail(
            "generated-product manifest mismatch"
        )

    validate_svg(
        ARCHITECTURE_FIGURE
    )

    validate_svg(
        BOUNDARY_FIGURE
    )

    print(
        "Phase 2J.3 Navigation / State-Estimation Validation"
    )

    print(
        "=" * 76
    )

    print()

    print(
        "Reference dataset: PASS"
    )

    print(
        "Phase 2J.1 dependency: PASS"
    )

    print(
        "Phase 2J.2 dependency: PASS"
    )

    print(
        "Phase 2I.3 dependency: PASS"
    )

    print(
        "Navigation sensor architecture: PASS"
    )

    print(
        "Deep Space Network boundary: PASS"
    )

    print(
        "Navigation-state product taxonomy: PASS"
    )

    print(
        "ONBOARD != GROUND != AROW boundary: PASS"
    )

    print(
        "AROW evidence boundary: PASS"
    )

    print(
        "Optical-navigation evidence: PASS"
    )

    print(
        "Proximity navigation evidence: PASS"
    )

    print(
        "Trajectory-correction monitoring boundary: PASS"
    )

    print(
        "OEM solution-evolution boundary: PASS"
    )

    print(
        "Generated taxonomy CSV: PASS"
    )

    print(
        "Generated evidence-boundary CSV: PASS"
    )

    print(
        "Generated summary JSON: PASS"
    )

    print(
        "Navigation architecture SVG: PASS"
    )

    print(
        "State-product boundary SVG: PASS"
    )

    print()

    print(
        "Evidence available:"
    )

    print(
        f"  {len(expected_true_keys)}"
    )

    print(
        "Evidence unavailable / not established:"
    )

    print(
        f"  {len(expected_false_keys)}"
    )

    print()

    print(
        "Critical permanent guardrail:"
    )

    print(
        "  AROW / OEM STATE VECTOR"
    )

    print(
        "  != PROVEN ORION ONBOARD FILTER STATE"
    )

    print()

    print(
        "PHASE 2J.3 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
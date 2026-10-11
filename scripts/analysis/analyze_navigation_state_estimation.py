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


plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def fail(message):
    raise SystemExit(
        message
    )


def load_json(path):
    if not path.exists():
        fail(
            f"Missing required file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def normalize_svg(path):
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


def build_architecture_figure(reference):
    ARCHITECTURE_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(17, 10)
    )

    ax.axis(
        "off"
    )

    ax.set_xlim(
        0,
        1,
    )

    ax.set_ylim(
        0,
        1,
    )

    ax.set_title(
        "Artemis II Navigation and State-Product Architecture",
        fontsize=15,
        pad=20,
    )

    onboard_text = (
        "ONBOARD NAVIGATION INPUTS\n\n"
        "Star Tracker\n"
        "IMU\n"
        "GPS Receiver\n"
        "Barometric Altimeter\n"
        "Optical Navigation Camera\n"
        "Sun Sensor"
    )

    onboard_state_text = (
        "ONBOARD NAVIGATION STATE\n\n"
        "Producer context:\n"
        "Orion vehicle-management computers\n\n"
        "Position / Velocity / Attitude\n"
        "knowledge computed onboard"
    )

    ground_text = (
        "EXTERNAL GROUND SUPPORT\n\n"
        "Deep Space Network\n"
        "communication-signal measurements\n\n"
        "Not an onboard sensor"
    )

    ground_state_text = (
        "GROUND ORBIT DETERMINATION\n\n"
        "MissionLab normalized category\n\n"
        "Ground navigation / spacecraft\n"
        "location determination context"
    )

    public_text = (
        "NASA PUBLIC MISSION DATA\n\n"
        "AROW tracking products\n"
        "Downloadable Artemis II\n"
        "trajectory / ephemeris data"
    )

    public_state_text = (
        "AROW PUBLIC STATE VECTOR\n\n"
        "Public Orion location and\n"
        "motion information\n\n"
        "Not proven equal to the\n"
        "onboard navigation-filter state"
    )

    columns = [
        (
            0.18,
            onboard_text,
            onboard_state_text,
        ),
        (
            0.50,
            ground_text,
            ground_state_text,
        ),
        (
            0.82,
            public_text,
            public_state_text,
        ),
    ]

    for x, top_text, bottom_text in columns:
        ax.text(
            x,
            0.72,
            top_text,
            ha="center",
            va="center",
            fontsize=9,
            bbox={
                "boxstyle":
                    "round,pad=0.7",
                "fill":
                    False,
            },
        )

        ax.text(
            x,
            0.33,
            bottom_text,
            ha="center",
            va="center",
            fontsize=9,
            bbox={
                "boxstyle":
                    "round,pad=0.7",
                "fill":
                    False,
            },
        )

        ax.annotate(
            "",
            xy=(
                x,
                0.47,
            ),
            xytext=(
                x,
                0.57,
            ),
            arrowprops={
                "arrowstyle":
                    "->",
            },
        )

    ax.text(
        0.34,
        0.33,
        "≠",
        ha="center",
        va="center",
        fontsize=22,
    )

    ax.text(
        0.66,
        0.33,
        "≠",
        ha="center",
        va="center",
        fontsize=22,
    )

    ax.text(
        0.5,
        0.09,
        (
            "Critical evidence boundary: "
            "ONBOARD_NAVIGATION_STATE ≠ "
            "GROUND_ORBIT_DETERMINATION ≠ "
            "AROW_PUBLIC_STATE_VECTOR"
        ),
        ha="center",
        fontsize=9,
    )

    ax.text(
        0.5,
        0.045,
        (
            "Public architecture and mission-data products do not expose "
            "the complete Artemis II onboard navigation-filter history."
        ),
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        ARCHITECTURE_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        ARCHITECTURE_FIGURE
    )


def build_boundary_figure(reference):
    BOUNDARY_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    boundaries = (
        reference[
            "state_estimation_evidence_boundaries"
        ]
    )

    rows = []

    for key, value in boundaries.items():
        rows.append(
            [
                key,
                (
                    "TRUE"
                    if value
                    else "FALSE"
                ),
            ]
        )

    fig, ax = plt.subplots(
        figsize=(17, 13)
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        "Phase 2J.3 Navigation and State-Estimation Evidence Boundary",
        fontsize=15,
        pad=18,
    )

    table = ax.table(
        cellText=rows,
        colLabels=[
            "Evidence Item",
            "Established in Current Public Source Set",
        ],
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        7.2
    )

    table.scale(
        1.0,
        1.45,
    )

    ax.text(
        0.5,
        0.018,
        (
            "FALSE means not established in the current curated "
            "MissionLab public source set. It does not mean that "
            "the underlying record never existed."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        BOUNDARY_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        BOUNDARY_FIGURE
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

    if (
        reference.get(
            "dataset_id"
        )
        != "phase2j3_artemis_ii_navigation_state_estimation"
    ):
        fail(
            "Unexpected Phase 2J.3 dataset ID."
        )

    if (
        gnc.get(
            "dataset_id"
        )
        != "phase2j1_artemis_ii_gnc_architecture"
    ):
        fail(
            "Unexpected Phase 2J.1 dependency."
        )

    if (
        manual_control.get(
            "dataset_id"
        )
        != "phase2j2_artemis_ii_manual_piloting_control_modes"
    ):
        fail(
            "Unexpected Phase 2J.2 dependency."
        )

    if (
        maneuver_correlation.get(
            "dataset_id"
        )
        != "phase2i3_artemis_ii_maneuver_trajectory_correlation"
    ):
        fail(
            "Unexpected Phase 2I.3 dependency."
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

    detected_copy_artifacts = [
        artifact
        for artifact in copy_artifacts
        if artifact in serialized_reference
    ]

    if detected_copy_artifacts:
        fail(
            "Phase 2J.3 reference text contains copy/paste "
            "spacing artifacts: "
            + ", ".join(
                detected_copy_artifacts
            )
        )

    sources = (
        reference[
            "sources"
        ]
    )

    if len(
        sources
    ) != 9:
        fail(
            "Expected nine curated Phase 2J.3 sources."
        )

    for source in sources:
        if (
            source[
                "organization"
            ]
            != "NASA"
        ):
            fail(
                "Non-NASA Phase 2J.3 source introduced."
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
                f"Unexpected Phase 2J.3 source domain: {url}"
            )

        if (
            "utm_"
            in url.lower()
        ):
            fail(
                "Tracking parameter found in canonical source URL."
            )

    expected_sensor_ids = [
        "star_tracker",
        "imu",
        "gps_receiver",
        "barometric_altimeter",
        "optical_navigation_camera",
        "sun_sensor",
    ]

    phase2j1_sensors = (
        gnc[
            "onboard_navigation_architecture"
        ][
            "sensors"
        ]
    )

    phase2j1_sensor_ids = [
        item[
            "sensor_id"
        ]
        for item in phase2j1_sensors
    ]

    if (
        phase2j1_sensor_ids
        != expected_sensor_ids
    ):
        fail(
            "Phase 2J.1 navigation sensor architecture changed."
        )

    phase2j3_sensors = (
        reference[
            "onboard_navigation_sensor_capability_context"
        ]
    )

    phase2j3_sensor_ids = [
        item[
            "sensor_id"
        ]
        for item in phase2j3_sensors
    ]

    if (
        phase2j3_sensor_ids
        != expected_sensor_ids
    ):
        fail(
            "Phase 2J.3 navigation sensor architecture changed."
        )

    if (
        phase2j3_sensor_ids
        != phase2j1_sensor_ids
    ):
        fail(
            "Phase 2J.3 sensor set does not match Phase 2J.1."
        )

    external_phase2j1 = (
        gnc[
            "external_navigation_support"
        ]
    )

    if (
        len(
            external_phase2j1
        )
        != 1
        or external_phase2j1[
            0
        ][
            "support_id"
        ]
        != "deep_space_network_tracking"
        or external_phase2j1[
            0
        ][
            "onboard_sensor"
        ]
        is not False
    ):
        fail(
            "Phase 2J.1 Deep Space Network boundary changed."
        )

    external_phase2j3 = (
        reference[
            "external_navigation_support"
        ]
    )

    if (
        external_phase2j3[
            "support_id"
        ]
        != "deep_space_network_tracking"
        or external_phase2j3[
            "onboard_sensor"
        ]
        is not False
        or external_phase2j3[
            "equivalent_to_onboard_navigation_filter"
        ]
        is not False
    ):
        fail(
            "Phase 2J.3 Deep Space Network boundary failed."
        )

    products = (
        reference[
            "navigation_state_product_taxonomy"
        ][
            "products"
        ]
    )

    expected_product_ids = [
        "ONBOARD_NAVIGATION_STATE",
        "GROUND_ORBIT_DETERMINATION",
        "AROW_PUBLIC_STATE_VECTOR",
    ]

    observed_product_ids = [
        item[
            "product_id"
        ]
        for item in products
    ]

    if (
        observed_product_ids
        != expected_product_ids
    ):
        fail(
            "Navigation-state product taxonomy changed."
        )

    if (
        reference[
            "navigation_state_product_taxonomy"
        ][
            "taxonomy_is_missionlab_normalization"
        ]
        is not True
    ):
        fail(
            "MissionLab taxonomy provenance boundary changed."
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
            "MissionLab ground-navigation taxonomy was "
            "incorrectly promoted to a NASA product name."
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
            "AROW was incorrectly equated with the onboard filter state."
        )

    critical_boundary = (
        reference[
            "critical_state_product_boundary"
        ]
    )

    if (
        critical_boundary[
            "onboard_navigation_state_equals_ground_orbit_determination"
        ]
        is not False
        or critical_boundary[
            "onboard_navigation_state_equals_arow_public_state_vector"
        ]
        is not False
        or critical_boundary[
            "ground_orbit_determination_equals_arow_public_state_vector"
        ]
        is not False
    ):
        fail(
            "Critical navigation state-product boundary failed."
        )

    if (
        critical_boundary[
            "statement"
        ]
        != (
            "ONBOARD_NAVIGATION_STATE != "
            "GROUND_ORBIT_DETERMINATION != "
            "AROW_PUBLIC_STATE_VECTOR"
        )
    ):
        fail(
            "Critical state-product boundary statement changed."
        )

    arow = (
        reference[
            "arow_public_product_context"
        ]
    )

    required_arow_true = [
        "state_vectors_publicly_provided",
        "downloadable_ephemeris_publicly_provided",
        "arow_visualizes_data_associated_with_orion_and_mission_control",
    ]

    for key in required_arow_true:
        if (
            arow[
                key
            ]
            is not True
        ):
            fail(
                f"AROW public-product evidence failed: {key}"
            )

    required_arow_false = [
        "public_state_vector_proven_to_be_raw_sensor_data",
        "public_state_vector_proven_equal_to_onboard_navigation_filter_state",
        "public_state_vector_proven_equal_to_complete_ground_orbit_determination_solution",
        "public_state_vector_generation_algorithm_available_in_current_source_set",
    ]

    for key in required_arow_false:
        if (
            arow[
                key
            ]
            is not False
        ):
            fail(
                f"Unsupported AROW interpretation introduced: {key}"
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
            "execution_status"
        ]
        != "AS_FLOWN_CONFIRMED"
        or opnav[
            "system"
        ]
        != "OPTICAL_NAVIGATION_CAMERA"
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
            "As-flown optical-navigation evidence changed."
        )

    if (
        opnav[
            "image_capture_proves_specific_navigation_filter_update"
        ]
        is not False
        or opnav[
            "image_metadata_equals_navigation_state"
        ]
        is not False
        or opnav[
            "opnav_measurement_residual_history_public"
        ]
        is not False
        or opnav[
            "opnav_filter_innovation_history_public"
        ]
        is not False
    ):
        fail(
            "Unsupported OpNav estimator inference introduced."
        )

    proximity_phase2j2 = (
        manual_control[
            "proximity_operations"
        ][
            "as_flown"
        ]
    )

    proximity_phase2j3 = (
        as_flown[
            "proximity_operations_navigation"
        ]
    )

    if (
        proximity_phase2j2[
            "onboard_navigation_sensors_used"
        ]
        is not True
        or proximity_phase2j3[
            "onboard_navigation_sensors_used"
        ]
        is not True
    ):
        fail(
            "As-flown proximity navigation evidence changed."
        )

    if (
        proximity_phase2j3[
            "specific_sensor_set_publicly_identified"
        ]
        is not False
        or proximity_phase2j3[
            "individual_sensor_measurement_history_public"
        ]
        is not False
        or proximity_phase2j3[
            "relative_state_history_public"
        ]
        is not False
        or proximity_phase2j3[
            "navigation_filter_state_history_public"
        ]
        is not False
    ):
        fail(
            "Unsupported proximity navigation detail introduced."
        )

    monitoring = (
        as_flown[
            "trajectory_correction_navigation_monitoring"
        ]
    )

    confirmed_examples = (
        monitoring[
            "confirmed_as_flown_examples"
        ]
    )

    confirmed_ids = [
        item[
            "maneuver_id"
        ]
        for item in confirmed_examples
    ]

    if (
        confirmed_ids
        != [
            "rtc1",
            "rtc3",
        ]
    ):
        fail(
            "As-flown trajectory-correction navigation "
            "monitoring examples changed."
        )

    for item in confirmed_examples:
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
                "Confirmed correction-burn monitoring evidence changed."
            )

    planned_monitoring = (
        monitoring[
            "planned_or_preburn_monitoring_context"
        ]
    )

    planned_ids = [
        item[
            "maneuver_id"
        ]
        for item in planned_monitoring
    ]

    if (
        planned_ids
        != [
            "otc3",
            "rtc2",
        ]
    ):
        fail(
            "Planned/pre-burn navigation-monitoring context changed."
        )

    for item in planned_monitoring:
        if (
            item[
                "promoted_to_complete_as_flown_display_history"
            ]
            is not False
        ):
            fail(
                "Planned monitoring evidence was incorrectly "
                "promoted to an as-flown display history."
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
            "Trajectory-correction navigation-display boundary failed."
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
        != oem_boundary[
            "oem_maneuver_brackets_expected"
        ]
        or len(
            oem_brackets
        )
        != 4
    ):
        fail(
            "OEM maneuver-bracket count changed."
        )

    expected_maneuver_ids = [
        "otc3",
        "rtc1",
        "rtc2",
        "rtc3",
    ]

    observed_maneuver_ids = [
        item[
            "maneuver_id"
        ]
        for item in oem_brackets
    ]

    if (
        observed_maneuver_ids
        != expected_maneuver_ids
    ):
        fail(
            "OEM maneuver-bracket ordering changed."
        )

    comparison_rows = [
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
            comparison_rows
        )
        != oem_boundary[
            "same_epoch_solution_comparisons_expected"
        ]
        or len(
            comparison_rows
        )
        != 3
    ):
        fail(
            "Same-epoch OEM comparison count changed."
        )

    for comparison in comparison_rows:
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
                "OEM solution difference was incorrectly "
                "promoted to navigation error or measured burn delta-v."
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
            "Public OEM interpretation boundary failed."
        )

    otc3_bracket = (
        oem_brackets[
            0
        ]
    )

    otc3_example = (
        oem_boundary[
            "important_example"
        ]
    )

    actual_otc3_post_product = (
        otc3_bracket[
            "earliest_product_created_after_maneuver"
        ][
            "product"
        ]
    )

    if (
        actual_otc3_post_product
        != otc3_example[
            "earliest_post_maneuver_created_product"
        ]
        or actual_otc3_post_product
        != "Artemis_II_OEM_2026_04_06_Pre-OTC3_to_EI.csv"
        or otc3_example[
            "creation_time_proves_otc3_assimilation"
        ]
        is not False
    ):
        fail(
            "OTC3 OEM creation-time guardrail changed."
        )

    boundaries = (
        reference[
            "state_estimation_evidence_boundaries"
        ]
    )

    required_true_boundaries = [
        "onboard_navigation_architecture_public",
        "onboard_sensor_roles_public",
        "dsn_ground_tracking_role_public",
        "arow_public_state_vectors_available",
        "arow_public_ephemeris_available",
        "artemis_ii_opnav_imagery_as_flown_confirmed",
        "proximity_ops_onboard_navigation_sensor_use_confirmed",
        "trajectory_correction_navigation_monitoring_as_flown_examples_confirmed",
    ]

    for key in required_true_boundaries:
        if (
            boundaries[
                key
            ]
            is not True
        ):
            fail(
                f"Expected public navigation evidence missing: {key}"
            )

    required_false_boundaries = [
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

    for key in required_false_boundaries:
        if (
            boundaries[
                key
            ]
            is not False
        ):
            fail(
                f"Unsupported navigation evidence introduced: {key}"
            )

    TAXONOMY_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    taxonomy_rows = []

    for product in products:
        taxonomy_rows.append(
            {
                "product_id":
                    product[
                        "product_id"
                    ],
                "producer_context":
                    product[
                        "producer_context"
                    ],
                "product_class":
                    product[
                        "product_class"
                    ],
                "role":
                    product[
                        "role"
                    ],
                "complete_artemis_ii_history_public":
                    str(
                        product.get(
                            "complete_artemis_ii_history_public_in_current_source_set",
                            product.get(
                                "complete_public_products_available",
                                False,
                            ),
                        )
                    ).lower(),
                "proven_equal_to_onboard_filter_state":
                    str(
                        product.get(
                            "proven_equal_to_onboard_navigation_filter_state",
                            False,
                        )
                    ).lower(),
            }
        )

    with TAXONOMY_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "product_id",
                "producer_context",
                "product_class",
                "role",
                "complete_artemis_ii_history_public",
                "proven_equal_to_onboard_filter_state",
            ],
        )

        writer.writeheader()
        writer.writerows(
            taxonomy_rows
        )

    boundary_rows = [
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

    with BOUNDARY_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "evidence_item",
                "established_in_current_public_source_set",
            ],
        )

        writer.writeheader()
        writer.writerows(
            boundary_rows
        )

    build_architecture_figure(
        reference
    )

    build_boundary_figure(
        reference
    )

    summary = {
        "product_id":
            "phase2j3_navigation_state_estimation_analysis",
        "mission":
            reference[
                "mission"
            ],
        "dependency_checks": {
            "phase2j1_gnc_architecture":
                "PASS",
            "phase2j2_manual_control_reconstruction":
                "PASS",
            "phase2i3_oem_trajectory_correlation":
                "PASS",
        },
        "onboard_navigation_sensor_count":
            len(
                phase2j3_sensors
            ),
        "onboard_navigation_sensor_ids":
            phase2j3_sensor_ids,
        "external_navigation_support": {
            "support_id":
                external_phase2j3[
                    "support_id"
                ],
            "onboard_sensor":
                external_phase2j3[
                    "onboard_sensor"
                ],
        },
        "navigation_state_product_ids":
            observed_product_ids,
        "critical_state_product_boundary":
            critical_boundary[
                "statement"
            ],
        "artemis_ii_as_flown_navigation_evidence": {
            "opnav_earth_images_confirmed":
                opnav[
                    "earth_images_captured"
                ],
            "opnav_moon_images_confirmed":
                opnav[
                    "moon_images_captured"
                ],
            "proximity_onboard_navigation_sensor_use_confirmed":
                proximity_phase2j3[
                    "onboard_navigation_sensors_used"
                ],
            "trajectory_correction_as_flown_monitoring_examples":
                confirmed_ids,
            "trajectory_correction_preburn_or_planned_monitoring_context":
                planned_ids,
        },
        "public_oem_audit": {
            "maneuver_brackets":
                len(
                    oem_brackets
                ),
            "same_epoch_solution_comparisons":
                len(
                    comparison_rows
                ),
            "comparisons_interpreted_as_navigation_error":
                False,
            "comparisons_interpreted_as_measured_burn_delta_v":
                False,
            "creation_time_proves_maneuver_assimilation":
                False,
        },
        "public_evidence_available_count":
            sum(
                1
                for value in boundaries.values()
                if value is True
            ),
        "public_evidence_unavailable_count":
            sum(
                1
                for value in boundaries.values()
                if value is False
            ),
        "reconstructable":
            reference[
                "phase2j3_reconstructable"
            ],
        "not_reconstructable":
            reference[
                "phase2j3_not_reconstructable"
            ],
        "guardrails":
            reference[
                "guardrails"
            ],
        "generated_products": [
            "data/processed/gnc/navigation_state_product_taxonomy.csv",
            "data/processed/gnc/navigation_evidence_boundaries.csv",
            "data/processed/gnc/navigation_state_estimation_summary.json",
            "docs/assets/gnc/phase2j3_navigation_architecture.svg",
            "docs/assets/gnc/phase2j3_state_product_boundaries.svg",
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

        f.write(
            "\n"
        )

    print(
        "Phase 2J.3 Navigation / State-Estimation Analysis"
    )

    print(
        "=" * 76
    )

    print()

    print(
        "Dependencies:"
    )

    print(
        "  Phase 2J.1 GNC architecture: PASS"
    )

    print(
        "  Phase 2J.2 manual-control reconstruction: PASS"
    )

    print(
        "  Phase 2I.3 OEM trajectory correlation: PASS"
    )

    print()

    print(
        "Onboard navigation sensor classes:"
    )

    for sensor_id in phase2j3_sensor_ids:
        print(
            f"  {sensor_id}"
        )

    print(
        "  count:"
    )

    print(
        f"    {len(phase2j3_sensor_ids)}"
    )

    print()

    print(
        "External navigation support:"
    )

    print(
        "  DEEP_SPACE_NETWORK_TRACKING"
    )

    print(
        "  onboard sensor:"
    )

    print(
        "    FALSE"
    )

    print()

    print(
        "Navigation-state product taxonomy:"
    )

    for product in products:
        print()

        print(
            f"  {product['product_id']}:"
        )

        print(
            "    producer context:"
        )

        print(
            f"      {product['producer_context']}"
        )

        print(
            "    role:"
        )

        print(
            f"      {product['role']}"
        )

    print()

    print(
        "Critical state-product boundary:"
    )

    print(
        "  ONBOARD_NAVIGATION_STATE"
    )

    print(
        "    != GROUND_ORBIT_DETERMINATION"
    )

    print(
        "    != AROW_PUBLIC_STATE_VECTOR"
    )

    print()

    print(
        "Artemis II as-flown navigation evidence:"
    )

    print()

    print(
        "  Optical navigation imagery:"
    )

    print(
        "    Earth imagery captured: TRUE"
    )

    print(
        "    Moon imagery captured: TRUE"
    )

    print(
        "    image capture proves estimator update: FALSE"
    )

    print()

    print(
        "  Proximity operations:"
    )

    print(
        "    onboard navigation sensors used: TRUE"
    )

    print(
        "    specific sensor set publicly identified: FALSE"
    )

    print(
        "    relative-state history public: FALSE"
    )

    print()

    print(
        "  Trajectory-correction navigation monitoring:"
    )

    print(
        "    confirmed as-flown examples:"
    )

    for maneuver_id in confirmed_ids:
        print(
            f"      {maneuver_id}"
        )

    print(
        "    planned/pre-burn context only:"
    )

    for maneuver_id in planned_ids:
        print(
            f"      {maneuver_id}"
        )

    print(
        "    exact displayed variables public: FALSE"
    )

    print(
        "    display equals onboard filter state: FALSE"
    )

    print()

    print(
        "AROW / OEM public trajectory products:"
    )

    print(
        f"  OEM maneuver brackets audited: {len(oem_brackets)}"
    )

    print(
        "  same-epoch solution comparisons available: "
        f"{len(comparison_rows)}"
    )

    print(
        "  comparisons explicitly not navigation error: "
        f"{len(comparison_rows)}"
    )

    print(
        "  comparisons explicitly not measured burn delta-v: "
        f"{len(comparison_rows)}"
    )

    print(
        "  OEM creation time proves maneuver assimilation:"
    )

    print(
        "    FALSE"
    )

    print(
        "  AROW state vector equals onboard navigation-filter state:"
    )

    print(
        "    NOT ESTABLISHED"
    )

    print()

    print(
        "State-estimation evidence boundaries:"
    )

    for key, value in boundaries.items():
        print(
            f"  {key}:"
        )

        print(
            "    "
            + (
                "TRUE"
                if value
                else "FALSE"
            )
        )

    print()

    print(
        "What Phase 2J.3 can reconstruct:"
    )

    for item in (
        reference[
            "phase2j3_reconstructable"
        ]
    ):
        print(
            f"  {item}"
        )

    print()

    print(
        "What Phase 2J.3 cannot reconstruct:"
    )

    for item in (
        reference[
            "phase2j3_not_reconstructable"
        ]
    ):
        print(
            f"  {item}"
        )

    print()

    print(
        "PHASE 2J.3 ANALYSIS COMPLETE"
    )


if __name__ == "__main__":
    main()
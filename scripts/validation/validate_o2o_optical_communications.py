from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_o2o_reference.json"
)

CATALOG_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_event_catalog.json"
)

METRICS_PATH = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "o2o_performance_metrics.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "o2o_optical_communications_summary.json"
)

ARCHITECTURE_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "communications"
    / "phase2h3_o2o_architecture.svg"
)

LINK_RATE_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "communications"
    / "phase2h3_o2o_link_rates.svg"
)

EXPECTED_DATASET_ID = (
    "phase2h3_artemis_ii_o2o_reference"
)

EXPECTED_PRODUCT_ID = (
    "phase2h3_o2o_optical_communications_analysis"
)

EXPECTED_METRIC_IDS = {
    "architecture_max_forward_rate",
    "architecture_max_return_rate",
    "flight_day_4_downlink_milestone",
    "mission_total_data_exchange",
    "mission_max_demonstrated_downlink",
    "main_ground_station_transfer",
    "derived_main_station_average_rate_lower_bound",
    "mount_stromlo_dual_stream_video_duration",
    "mount_stromlo_max_demonstrated_downlink",
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


def check_close(
    name,
    observed,
    expected,
    tolerance=1e-6,
):
    if abs(
        float(observed)
        - float(expected)
    ) > tolerance:
        fail(
            f"{name}: "
            f"{observed} != {expected}"
        )


def main() -> None:
    reference = load_json(
        REFERENCE_PATH
    )

    catalog = load_json(
        CATALOG_PATH
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

    role = (
        reference[
            "mission_role"
        ]
    )

    if (
        role[
            "classification"
        ]
        != "OPTICAL_COMMUNICATIONS_DEMONSTRATION"
    ):
        fail(
            "unexpected O2O mission role"
        )

    if (
        role[
            "primary_rf_replacement"
        ]
        is not False
    ):
        fail(
            "O2O cannot be marked as primary RF replacement"
        )

    if (
        role[
            "primary_mission_communications"
        ]
        != [
            "Near Space Network",
            "Deep Space Network",
        ]
    ):
        fail(
            "primary RF architecture changed"
        )

    architecture = (
        reference[
            "optical_architecture"
        ]
    )

    if (
        architecture[
            "optical_band"
        ]
        != "OPTICAL_C_BAND"
    ):
        fail(
            "optical band changed"
        )

    if (
        architecture[
            "nominal_wavelength_nm"
        ]
        != 1550
    ):
        fail(
            "expected 1550 nm wavelength"
        )

    if (
        architecture[
            "maximum_return_downlink_rate_mbps"
        ]
        != 260
    ):
        fail(
            "expected 260 Mbps return maximum"
        )

    if (
        architecture[
            "maximum_forward_uplink_rate_mbps"
        ]
        != 20
    ):
        fail(
            "expected 20 Mbps forward maximum"
        )

    components = {
        component["id"]:
            component
        for component in architecture[
            "terminal_components"
        ]
    }

    if set(
        components
    ) != {
        "optical_module",
        "modem",
        "controller",
    }:
        fail(
            "terminal component set changed"
        )

    optical_module = (
        components[
            "optical_module"
        ]
    )

    if (
        optical_module[
            "telescope_aperture_inches"
        ]
        != 4
    ):
        fail(
            "telescope aperture changed"
        )

    if (
        optical_module[
            "gimbal_count"
        ]
        != 2
    ):
        fail(
            "gimbal count changed"
        )

    ground = (
        reference[
            "ground_segment"
        ]
    )

    main_sites = (
        ground[
            "main_ground_sites"
        ]
    )

    additional_sites = (
        ground[
            "additional_demonstration_sites"
        ]
    )

    if len(main_sites) != 2:
        fail(
            "expected two main optical ground sites"
        )

    if len(additional_sites) != 1:
        fail(
            "expected one additional ground site"
        )

    if {
        site["site_id"]
        for site in main_sites
    } != {
        "white_sands_complex",
        "table_mountain_facility",
    }:
        fail(
            "main optical ground-site set changed"
        )

    if (
        additional_sites[0][
            "site_id"
        ]
        != "mount_stromlo_qogs"
    ):
        fail(
            "additional ground site changed"
        )

    operations = (
        reference[
            "operations_segment"
        ]
    )

    if {
        element["id"]
        for element in operations[
            "elements"
        ]
    } != {
        "mcc",
        "lstc",
        "lpac",
    }:
        fail(
            "operations segment changed"
        )

    catalog_by_id = {
        event["id"]:
            event
        for event in catalog[
            "events"
        ]
    }

    flight_day_3 = (
        catalog_by_id[
            "o2o_two_us_ground_station_links"
        ]
    )

    milestone = (
        catalog_by_id[
            "o2o_100_gb_downlink_milestone"
        ]
    )

    if (
        flight_day_3[
            "precision"
        ]
        != "DATE_LEVEL"
    ):
        fail(
            "Flight Day 3 event gained unsupported precision"
        )

    if (
        milestone[
            "precision"
        ]
        != "APPROXIMATE"
    ):
        fail(
            "100 GB event gained unsupported precision"
        )

    if (
        milestone.get(
            "anchor_is_not_exact"
        )
        is not True
    ):
        fail(
            "100 GB anchor lost non-exact guard"
        )

    if (
        milestone[
            "approximate_anchor_utc"
        ]
        != "2026-04-04T16:00:00Z"
    ):
        fail(
            "100 GB approximate anchor changed"
        )

    postflight = (
        reference[
            "postflight_results"
        ]
    )

    exchange = (
        postflight[
            "mission_total_data_exchange"
        ]
    )

    if (
        exchange[
            "value_gb"
        ]
        != 484
    ):
        fail(
            "mission data exchange changed"
        )

    if (
        exchange[
            "downlink_only"
        ]
        is not False
    ):
        fail(
            "484 GB incorrectly marked downlink-only"
        )

    if (
        exchange[
            "single_session"
        ]
        is not False
    ):
        fail(
            "484 GB incorrectly marked single-session"
        )

    downlink = (
        postflight[
            "downlink_performance"
        ]
    )

    if (
        downlink[
            "multiple_260_mbps_downlinks"
        ]
        is not True
    ):
        fail(
            "multiple 260 Mbps downlinks result missing"
        )

    if (
        downlink[
            "maximum_demonstrated_downlink_rate_mbps"
        ]
        != 260
    ):
        fail(
            "maximum demonstrated rate changed"
        )

    transfer = (
        postflight[
            "main_ground_station_transfer"
        ]
    )

    if (
        transfer[
            "reported_data_volume_gb"
        ]
        != 26
    ):
        fail(
            "26 GB transfer value changed"
        )

    if (
        transfer[
            "reported_duration_relation"
        ]
        != "LESS_THAN"
    ):
        fail(
            "26 GB duration bound changed"
        )

    if (
        transfer[
            "reported_duration_hours"
        ]
        != 1
    ):
        fail(
            "26 GB duration value changed"
        )

    if (
        transfer[
            "individual_site_assignment"
        ]
        is not None
    ):
        fail(
            "26 GB record gained unsupported station assignment"
        )

    expected_lower_bound_mbps = (
        26.0
        * 8.0
        * 1000.0
        / 3600.0
    )

    expected_ratio = (
        260.0
        / 20.0
    )

    expected_stromlo_seconds = (
        15.5
        * 3600.0
    )

    derived = (
        summary[
            "derived_metrics"
        ]
    )

    check_close(
        "max rate ratio",
        derived[
            "maximum_return_to_forward_rate_ratio"
        ],
        expected_ratio,
    )

    check_close(
        "26 GB duration upper bound",
        derived[
            "main_ground_station_26gb_transfer_duration_upper_bound_seconds"
        ],
        3600.0,
    )

    check_close(
        "26 GB average rate lower bound",
        derived[
            "main_ground_station_26gb_average_rate_lower_bound_mbps_decimal_gb"
        ],
        expected_lower_bound_mbps,
    )

    check_close(
        "Mount Stromlo video seconds lower bound",
        derived[
            "mount_stromlo_dual_stream_video_duration_lower_bound_seconds"
        ],
        expected_stromlo_seconds,
    )

    stromlo = (
        postflight[
            "mount_stromlo"
        ]
    )

    if (
        stromlo[
            "dual_stream_video_duration_relation"
        ]
        != "GREATER_THAN"
    ):
        fail(
            "Mount Stromlo duration lost lower-bound semantics"
        )

    if (
        stromlo[
            "dual_stream_video_duration_hours"
        ]
        != 15.5
    ):
        fail(
            "Mount Stromlo duration changed"
        )

    if (
        stromlo[
            "continuous_single_pass_claimed"
        ]
        is not False
    ):
        fail(
            "Mount Stromlo incorrectly treated as one continuous pass"
        )

    if (
        stromlo[
            "maximum_demonstrated_downlink_rate_mbps"
        ]
        != 260
    ):
        fail(
            "Mount Stromlo maximum rate changed"
        )

    content = (
        postflight[
            "content_and_direction"
        ]
    )

    for key in [
        "earthset_images_downlinked",
        "earthrise_images_downlinked",
        "forward_data_to_orion_demonstrated",
    ]:
        if (
            content[key]
            is not True
        ):
            fail(
                f"{key} changed"
            )

    if not METRICS_PATH.exists():
        fail(
            "performance metrics CSV missing"
        )

    with METRICS_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        metrics = list(
            csv.DictReader(f)
        )

    if len(metrics) != 9:
        fail(
            "performance metrics CSV must contain 9 rows"
        )

    metric_ids = {
        row[
            "metric_id"
        ]
        for row in metrics
    }

    if (
        metric_ids
        != EXPECTED_METRIC_IDS
    ):
        fail(
            "performance metric identity set changed"
        )

    metrics_by_id = {
        row[
            "metric_id"
        ]:
            row
        for row in metrics
    }

    if (
        metrics_by_id[
            "flight_day_4_downlink_milestone"
        ][
            "relation"
        ]
        != "GREATER_THAN"
    ):
        fail(
            "100 GB milestone lost threshold semantics"
        )

    if (
        metrics_by_id[
            "derived_main_station_average_rate_lower_bound"
        ][
            "relation"
        ]
        != "GREATER_THAN"
    ):
        fail(
            "derived transfer rate lost lower-bound semantics"
        )

    check_close(
        "CSV lower-bound rate",
        metrics_by_id[
            "derived_main_station_average_rate_lower_bound"
        ][
            "value"
        ],
        expected_lower_bound_mbps,
    )

    if (
        summary[
            "architecture"
        ][
            "maximum_return_downlink_rate_mbps"
        ]
        != 260.0
    ):
        fail(
            "summary return rate mismatch"
        )

    if (
        summary[
            "architecture"
        ][
            "maximum_forward_uplink_rate_mbps"
        ]
        != 20.0
    ):
        fail(
            "summary forward rate mismatch"
        )

    if (
        summary[
            "ground_segment"
        ][
            "main_site_count"
        ]
        != 2
    ):
        fail(
            "summary main ground-site count mismatch"
        )

    if (
        summary[
            "ground_segment"
        ][
            "additional_demonstration_site_count"
        ]
        != 1
    ):
        fail(
            "summary additional-site count mismatch"
        )

    if (
        summary[
            "live_mission_event_cross_checks"
        ][
            "flight_day_4_100gb_milestone"
        ][
            "anchor_is_exact"
        ]
        is not False
    ):
        fail(
            "summary 100 GB anchor exactness changed"
        )

    if (
        summary[
            "postflight_results"
        ][
            "mission_total_is_downlink_only"
        ]
        is not False
    ):
        fail(
            "summary mislabels 484 GB as downlink-only"
        )

    if (
        summary[
            "performance_metric_count"
        ]
        != 9
    ):
        fail(
            "summary metric count mismatch"
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
            "summary guardrails do not match reference"
        )

    for figure in [
        ARCHITECTURE_FIGURE,
        LINK_RATE_FIGURE,
    ]:
        if not figure.exists():
            fail(
                f"missing figure: {figure}"
            )

        text = figure.read_text(
            encoding="utf-8"
        )

        if (
            "<svg" not in text
            or len(text) < 1000
        ):
            fail(
                f"invalid SVG: {figure}"
            )

    print()
    print(
        "Phase 2H.3 O2O Optical Communications Validation"
    )

    print("=" * 63)

    print()
    print(
        "Mission role:"
    )

    print(
        "  optical demonstration: TRUE"
    )

    print(
        "  primary RF replacement: FALSE"
    )

    print()
    print(
        "Architecture:"
    )

    print(
        "  wavelength: 1550 nm"
    )

    print(
        "  max return/downlink: 260 Mbps"
    )

    print(
        "  max forward/uplink: 20 Mbps"
    )

    print(
        "  max return / max forward: 13.000x"
    )

    print(
        "  terminal components: 3"
    )

    print(
        "  telescope: 4 in"
    )

    print(
        "  gimbals: 2"
    )

    print()
    print(
        "Ground segment:"
    )

    print(
        "  main optical sites: 2"
    )

    print(
        "  additional demonstrated sites: 1"
    )

    print(
        "  White Sands: PASS"
    )

    print(
        "  Table Mountain / JPL: PASS"
    )

    print(
        "  Mount Stromlo QOGS: PASS"
    )

    print()
    print(
        "Mission-control operations:"
    )

    print(
        "  MCC: PASS"
    )

    print(
        "  LSTC: PASS"
    )

    print(
        "  LPAC: PASS"
    )

    print()
    print(
        "Live mission precision:"
    )

    print(
        "  Flight Day 3 links: DATE_LEVEL"
    )

    print(
        "  Flight Day 4 100 GB: APPROXIMATE"
    )

    print(
        "  100 GB anchor exact: FALSE"
    )

    print()
    print(
        "Postflight results:"
    )

    print(
        "  mission exchange: 484 GB"
    )

    print(
        "  exchange marked downlink-only: FALSE"
    )

    print(
        "  multiple 260 Mbps downlinks: TRUE"
    )

    print(
        "  26 GB transfer: <1 h"
    )

    print(
        "  derived average-rate lower bound:"
    )

    print(
        f"    >{expected_lower_bound_mbps:.3f} Mbps"
    )

    print(
        "  Mount Stromlo video:"
    )

    print(
        "    >15.5 h"
    )

    print(
        "  Mount Stromlo continuous-pass claim:"
    )

    print(
        "    FALSE"
    )

    print(
        "  Mount Stromlo 260 Mbps:"
    )

    print(
        "    TRUE"
    )

    print(
        "  Earthset imagery:"
    )

    print(
        "    TRUE"
    )

    print(
        "  Earthrise imagery:"
    )

    print(
        "    TRUE"
    )

    print(
        "  forward data to Orion:"
    )

    print(
        "    TRUE"
    )

    print()
    print(
        "Products:"
    )

    print(
        "  performance metrics rows: 9"
    )

    print(
        "  summary: PASS"
    )

    print(
        "  architecture figure: PASS"
    )

    print(
        "  link-rate figure: PASS"
    )

    print()
    print(
        "OK: Phase 2H.3 O2O mission role, optical architecture, "
        "ground segment, mission-control operations integration, "
        "live-event precision, postflight mission performance, "
        "derived transfer-rate lower bound, optical-versus-RF "
        "separation, generated products, and interpretation "
        "guardrails independently validated."
    )


if __name__ == "__main__":
    main()
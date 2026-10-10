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
    / "artemis_ii_o2o_reference.json"
)

COMMUNICATIONS_CATALOG_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_event_catalog.json"
)

OUTPUT_SUMMARY = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "o2o_optical_communications_summary.json"
)

OUTPUT_METRICS = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "o2o_performance_metrics.csv"
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


def metric(
    metric_id: str,
    name: str,
    value: float,
    unit: str,
    relation: str,
    evidence_layer: str,
    provenance: str,
    source_id: str,
    notes: str,
):
    return {
        "metric_id": metric_id,
        "name": name,
        "value": value,
        "unit": unit,
        "relation": relation,
        "evidence_layer": evidence_layer,
        "provenance": provenance,
        "source_id": source_id,
        "notes": notes,
    }


def build_architecture_figure(
    reference,
) -> None:
    ARCHITECTURE_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(15, 8)
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
            "round,pad=0.5",

        "fill":
            False,
    }

    orion_xy = (
        0.18,
        0.55,
    )

    wsc_xy = (
        0.53,
        0.76,
    )

    tmf_xy = (
        0.53,
        0.54,
    )

    qogs_xy = (
        0.53,
        0.32,
    )

    mcc_xy = (
        0.84,
        0.55,
    )

    ax.text(
        *orion_xy,
        (
            "ORION / O2O\n"
            "Optical module\n"
            "4-in telescope + 2 gimbals\n"
            "Modem\n"
            "Controller\n"
            "1550 nm optical C-band\n"
            "Return ≤ 260 Mbps\n"
            "Forward ≤ 20 Mbps"
        ),
        ha="center",
        va="center",
        bbox=box,
        fontsize=10,
    )

    ax.text(
        *wsc_xy,
        (
            "White Sands Complex\n"
            "New Mexico\n"
            "Main optical ground site"
        ),
        ha="center",
        va="center",
        bbox=box,
        fontsize=9,
    )

    ax.text(
        *tmf_xy,
        (
            "JPL / Table Mountain\n"
            "Southern California\n"
            "Main optical ground site"
        ),
        ha="center",
        va="center",
        bbox=box,
        fontsize=9,
    )

    ax.text(
        *qogs_xy,
        (
            "ANU QOGS\n"
            "Mount Stromlo, Canberra\n"
            "Additional demonstrated site"
        ),
        ha="center",
        va="center",
        bbox=box,
        fontsize=9,
    )

    ax.text(
        *mcc_xy,
        (
            "Johnson Space Center\n"
            "Mission Control Center\n"
            "LSTC\n"
            "LPAC"
        ),
        ha="center",
        va="center",
        bbox=box,
        fontsize=9,
    )

    for destination in [
        wsc_xy,
        tmf_xy,
        qogs_xy,
    ]:
        ax.annotate(
            "",
            xy=(
                destination[0] - 0.10,
                destination[1],
            ),
            xytext=(
                orion_xy[0] + 0.12,
                orion_xy[1],
            ),
            arrowprops={
                "arrowstyle":
                    "->",
            },
        )

    for origin in [
        wsc_xy,
        tmf_xy,
        qogs_xy,
    ]:
        ax.annotate(
            "",
            xy=(
                mcc_xy[0] - 0.09,
                mcc_xy[1],
            ),
            xytext=(
                origin[0] + 0.11,
                origin[1],
            ),
            arrowprops={
                "arrowstyle":
                    "->",
            },
        )

    ax.text(
        0.50,
        0.10,
        (
            "O2O was a parallel optical demonstration. "
            "Near Space Network and Deep Space Network "
            "remained Artemis II's primary RF communications."
        ),
        ha="center",
        va="center",
        fontsize=9,
        bbox=box,
    )

    ax.set_title(
        "Artemis II O2O Optical Communications Architecture",
        fontsize=14,
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


def build_link_rate_figure(
    max_forward_mbps,
    max_return_mbps,
    max_demonstrated_mbps,
    transfer_lower_bound_mbps,
) -> None:
    LINK_RATE_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    names = [
        "Architecture\nmax forward",
        "Architecture\nmax return",
        "Mission\nmax demonstrated",
        "26 GB / <1 h\naverage lower bound",
    ]

    values = [
        max_forward_mbps,
        max_return_mbps,
        max_demonstrated_mbps,
        transfer_lower_bound_mbps,
    ]

    fig, ax = plt.subplots(
        figsize=(11, 6.5)
    )

    bars = ax.bar(
        names,
        values,
    )

    labels = [
        f"{max_forward_mbps:.0f}",
        f"{max_return_mbps:.0f}",
        f"{max_demonstrated_mbps:.0f}",
        f">{transfer_lower_bound_mbps:.1f}",
    ]

    for bar, label in zip(
        bars,
        labels,
    ):
        ax.text(
            bar.get_x()
            + bar.get_width() / 2.0,
            bar.get_height() + 5,
            label,
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax.set_ylabel(
        "Megabits per second"
    )

    ax.set_title(
        "Artemis II O2O Reported and Derived Rate Context"
    )

    ax.grid(
        True,
        axis="y",
        alpha=0.25,
    )

    ax.text(
        0.01,
        -0.19,
        (
            "The 26 GB / <1 h value is a MissionLab lower bound "
            "on average transfer rate using decimal GB. "
            "It is not NASA-reported instantaneous throughput."
        ),
        transform=ax.transAxes,
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        LINK_RATE_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        LINK_RATE_FIGURE
    )


def main() -> None:
    reference = load_json(
        REFERENCE_PATH
    )

    catalog = load_json(
        COMMUNICATIONS_CATALOG_PATH
    )

    if (
        reference.get(
            "dataset_id"
        )
        != "phase2h3_artemis_ii_o2o_reference"
    ):
        fail(
            "Unexpected O2O reference dataset ID."
        )

    events_by_id = {
        event["id"]:
            event
        for event in catalog[
            "events"
        ]
    }

    required_events = [
        "o2o_two_us_ground_station_links",
        "o2o_100_gb_downlink_milestone",
    ]

    for event_id in required_events:
        if event_id not in events_by_id:
            fail(
                "Missing Phase 2H.1 event: "
                f"{event_id}"
            )

    architecture = (
        reference[
            "optical_architecture"
        ]
    )

    mission_role = (
        reference[
            "mission_role"
        ]
    )

    ground_segment = (
        reference[
            "ground_segment"
        ]
    )

    operations_segment = (
        reference[
            "operations_segment"
        ]
    )

    results = (
        reference[
            "postflight_results"
        ]
    )

    max_return_mbps = float(
        architecture[
            "maximum_return_downlink_rate_mbps"
        ]
    )

    max_forward_mbps = float(
        architecture[
            "maximum_forward_uplink_rate_mbps"
        ]
    )

    max_demonstrated_mbps = float(
        results[
            "downlink_performance"
        ][
            "maximum_demonstrated_downlink_rate_mbps"
        ]
    )

    if max_return_mbps != 260.0:
        fail(
            "Expected 260 Mbps maximum return rate."
        )

    if max_forward_mbps != 20.0:
        fail(
            "Expected 20 Mbps maximum forward rate."
        )

    if max_demonstrated_mbps != max_return_mbps:
        fail(
            "Demonstrated maximum does not match "
            "architecture maximum."
        )

    if (
        mission_role[
            "primary_rf_replacement"
        ]
        is not False
    ):
        fail(
            "O2O must not replace primary RF architecture."
        )

    terminal_components = {
        component["id"]
        for component in architecture[
            "terminal_components"
        ]
    }

    if terminal_components != {
        "optical_module",
        "modem",
        "controller",
    }:
        fail(
            "Unexpected O2O terminal component set."
        )

    optical_module = next(
        component
        for component in architecture[
            "terminal_components"
        ]
        if component[
            "id"
        ] == "optical_module"
    )

    if (
        optical_module[
            "telescope_aperture_inches"
        ]
        != 4
    ):
        fail(
            "Expected 4-inch O2O telescope."
        )

    if (
        optical_module[
            "gimbal_count"
        ]
        != 2
    ):
        fail(
            "Expected two optical-module gimbals."
        )

    main_sites = (
        ground_segment[
            "main_ground_sites"
        ]
    )

    additional_sites = (
        ground_segment[
            "additional_demonstration_sites"
        ]
    )

    if len(main_sites) != 2:
        fail(
            "Expected two main optical ground sites."
        )

    if len(additional_sites) != 1:
        fail(
            "Expected one additional demonstration site."
        )

    main_site_ids = {
        site["site_id"]
        for site in main_sites
    }

    if main_site_ids != {
        "white_sands_complex",
        "table_mountain_facility",
    }:
        fail(
            "Unexpected main ground-site set."
        )

    if (
        additional_sites[0][
            "site_id"
        ]
        != "mount_stromlo_qogs"
    ):
        fail(
            "Expected Mount Stromlo QOGS."
        )

    operations_ids = {
        element["id"]
        for element in operations_segment[
            "elements"
        ]
    }

    if operations_ids != {
        "mcc",
        "lstc",
        "lpac",
    }:
        fail(
            "Unexpected operations-segment element set."
        )

    flight_day_3 = (
        events_by_id[
            "o2o_two_us_ground_station_links"
        ]
    )

    milestone_100gb = (
        events_by_id[
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
            "Flight Day 3 O2O event must remain DATE_LEVEL."
        )

    if (
        milestone_100gb[
            "precision"
        ]
        != "APPROXIMATE"
    ):
        fail(
            "100 GB milestone must remain APPROXIMATE."
        )

    if (
        milestone_100gb.get(
            "anchor_is_not_exact"
        )
        is not True
    ):
        fail(
            "100 GB milestone approximate anchor lost guard."
        )

    reference_live_events = {
        event[
            "catalog_event_id"
        ]:
            event
        for event in reference[
            "live_mission_events"
        ]
    }

    if set(
        reference_live_events
    ) != set(
        required_events
    ):
        fail(
            "Reference live-event set does not match catalog."
        )

    if (
        reference_live_events[
            "o2o_100_gb_downlink_milestone"
        ][
            "approximate_anchor_utc"
        ]
        != milestone_100gb[
            "approximate_anchor_utc"
        ]
    ):
        fail(
            "100 GB milestone anchor mismatch."
        )

    total_exchange_gb = float(
        results[
            "mission_total_data_exchange"
        ][
            "value_gb"
        ]
    )

    if total_exchange_gb != 484.0:
        fail(
            "Expected 484 GB mission exchange."
        )

    if (
        results[
            "mission_total_data_exchange"
        ][
            "downlink_only"
        ]
        is not False
    ):
        fail(
            "484 GB must not be marked downlink-only."
        )

    transfer_gb = float(
        results[
            "main_ground_station_transfer"
        ][
            "reported_data_volume_gb"
        ]
    )

    duration_hours = float(
        results[
            "main_ground_station_transfer"
        ][
            "reported_duration_hours"
        ]
    )

    if (
        results[
            "main_ground_station_transfer"
        ][
            "reported_duration_relation"
        ]
        != "LESS_THAN"
    ):
        fail(
            "26 GB transfer duration must remain an upper bound."
        )

    duration_upper_bound_seconds = (
        duration_hours
        * 3600.0
    )

    transfer_megabits_decimal = (
        transfer_gb
        * 8.0
        * 1000.0
    )

    minimum_average_rate_mbps = (
        transfer_megabits_decimal
        / duration_upper_bound_seconds
    )

    max_rate_ratio = (
        max_return_mbps
        / max_forward_mbps
    )

    stromlo = (
        results[
            "mount_stromlo"
        ]
    )

    stromlo_hours = float(
        stromlo[
            "dual_stream_video_duration_hours"
        ]
    )

    stromlo_seconds_lower_bound = (
        stromlo_hours
        * 3600.0
    )

    if (
        stromlo[
            "dual_stream_video_duration_relation"
        ]
        != "GREATER_THAN"
    ):
        fail(
            "Mount Stromlo duration must remain a lower bound."
        )

    if (
        stromlo[
            "continuous_single_pass_claimed"
        ]
        is not False
    ):
        fail(
            "Mount Stromlo result must not imply one continuous pass."
        )

    if float(
        stromlo[
            "maximum_demonstrated_downlink_rate_mbps"
        ]
    ) != 260.0:
        fail(
            "Mount Stromlo 260 Mbps result missing."
        )

    metrics = [
        metric(
            "architecture_max_forward_rate",
            "Architecture maximum forward rate",
            max_forward_mbps,
            "Mbps",
            "REPORTED_VALUE",
            "PREMISSION_ARCHITECTURE",
            "NASA_NTRS_REPORTED",
            "ntrs_o2o_interface_20230007379",
            "Maximum forward/uplink architecture rate.",
        ),

        metric(
            "architecture_max_return_rate",
            "Architecture maximum return rate",
            max_return_mbps,
            "Mbps",
            "REPORTED_VALUE",
            "PREMISSION_ARCHITECTURE",
            "NASA_NTRS_REPORTED",
            "ntrs_o2o_interface_20230007379",
            "Maximum return/downlink architecture rate.",
        ),

        metric(
            "flight_day_4_downlink_milestone",
            "Flight Day 4 downlink milestone threshold",
            100.0,
            "GB",
            "GREATER_THAN",
            "LIVE_MISSION_REPORTED",
            "NASA_REPORTED",
            "nasa_flight_day_4_o2o",
            "NASA reported O2O had surpassed this threshold.",
        ),

        metric(
            "mission_total_data_exchange",
            "Mission total data exchanged",
            total_exchange_gb,
            "GB",
            "REPORTED_VALUE",
            "POSTFLIGHT_REPORTED",
            "NASA_REPORTED",
            "nasa_o2o_postflight",
            "Exchanged between Orion and Earth; not downlink-only.",
        ),

        metric(
            "mission_max_demonstrated_downlink",
            "Maximum demonstrated downlink rate",
            max_demonstrated_mbps,
            "Mbps",
            "REPORTED_VALUE",
            "POSTFLIGHT_REPORTED",
            "NASA_REPORTED",
            "nasa_o2o_postflight",
            "NASA reported multiple downlinks at this rate.",
        ),

        metric(
            "main_ground_station_transfer",
            "Reported main-ground-station transfer",
            transfer_gb,
            "GB",
            "REPORTED_VALUE",
            "POSTFLIGHT_REPORTED",
            "NASA_REPORTED",
            "nasa_o2o_postflight",
            "NASA reported 26 GB in under one hour.",
        ),

        metric(
            "derived_main_station_average_rate_lower_bound",
            "Derived average rate lower bound for 26 GB transfer",
            minimum_average_rate_mbps,
            "Mbps",
            "GREATER_THAN",
            "MISSIONLAB_DERIVED",
            "MISSIONLAB_DERIVED",
            "nasa_o2o_postflight",
            (
                "Uses decimal GB and the one-hour upper bound. "
                "Actual average rate must be greater if the "
                "reported transfer duration was under one hour."
            ),
        ),

        metric(
            "mount_stromlo_dual_stream_video_duration",
            "Mount Stromlo dual-stream video duration",
            stromlo_hours,
            "hours",
            "GREATER_THAN",
            "POSTFLIGHT_REPORTED",
            "NASA_REPORTED",
            "nasa_o2o_postflight",
            "Mission aggregate; not one continuous pass.",
        ),

        metric(
            "mount_stromlo_max_demonstrated_downlink",
            "Mount Stromlo maximum demonstrated downlink",
            260.0,
            "Mbps",
            "REPORTED_VALUE",
            "POSTFLIGHT_REPORTED",
            "NASA_REPORTED",
            "nasa_o2o_postflight",
            "Highest possible O2O downlink rate was demonstrated.",
        ),
    ]

    OUTPUT_METRICS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_METRICS.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "metric_id",
                "name",
                "value",
                "unit",
                "relation",
                "evidence_layer",
                "provenance",
                "source_id",
                "notes",
            ],
        )

        writer.writeheader()
        writer.writerows(
            metrics
        )

    build_architecture_figure(
        reference
    )

    build_link_rate_figure(
        max_forward_mbps,
        max_return_mbps,
        max_demonstrated_mbps,
        minimum_average_rate_mbps,
    )

    evidence_counts = Counter(
        source[
            "evidence_layer"
        ]
        for source in reference[
            "sources"
        ]
    )

    summary = {
        "product_id":
            "phase2h3_o2o_optical_communications_analysis",

        "mission":
            "Artemis II",

        "reference_dataset_id":
            reference[
                "dataset_id"
            ],

        "system":
            reference[
                "system_name"
            ],

        "mission_role":
            reference[
                "mission_role"
            ],

        "architecture": {
            "optical_band":
                architecture[
                    "optical_band"
                ],

            "wavelength_nm":
                architecture[
                    "nominal_wavelength_nm"
                ],

            "maximum_return_downlink_rate_mbps":
                max_return_mbps,

            "maximum_forward_uplink_rate_mbps":
                max_forward_mbps,

            "maximum_return_to_forward_rate_ratio":
                max_rate_ratio,

            "telescope_aperture_inches":
                optical_module[
                    "telescope_aperture_inches"
                ],

            "gimbal_count":
                optical_module[
                    "gimbal_count"
                ],

            "terminal_component_count":
                len(
                    architecture[
                        "terminal_components"
                    ]
                ),
        },

        "ground_segment": {
            "main_site_count":
                len(main_sites),

            "additional_demonstration_site_count":
                len(additional_sites),

            "main_site_ids":
                sorted(
                    main_site_ids
                ),

            "additional_site_ids": [
                site[
                    "site_id"
                ]
                for site in (
                    additional_sites
                )
            ],
        },

        "operations_segment": {
            "location":
                operations_segment[
                    "location"
                ],

            "element_ids":
                sorted(
                    operations_ids
                ),
        },

        "live_mission_event_cross_checks": {
            "flight_day_3_ground_links": {
                "catalog_event_id":
                    flight_day_3[
                        "id"
                    ],

                "precision":
                    flight_day_3[
                        "precision"
                    ],

                "event_state":
                    flight_day_3[
                        "event_state"
                    ],
            },

            "flight_day_4_100gb_milestone": {
                "catalog_event_id":
                    milestone_100gb[
                        "id"
                    ],

                "precision":
                    milestone_100gb[
                        "precision"
                    ],

                "approximate_anchor_utc":
                    milestone_100gb[
                        "approximate_anchor_utc"
                    ],

                "anchor_is_exact":
                    False,
            },
        },

        "postflight_results": {
            "mission_total_data_exchange_gb":
                total_exchange_gb,

            "mission_total_is_downlink_only":
                False,

            "multiple_260_mbps_downlinks":
                results[
                    "downlink_performance"
                ][
                    "multiple_260_mbps_downlinks"
                ],

            "maximum_demonstrated_downlink_rate_mbps":
                max_demonstrated_mbps,

            "main_ground_station_transfer_gb":
                transfer_gb,

            "main_ground_station_transfer_duration_relation":
                "LESS_THAN",

            "main_ground_station_transfer_duration_hours":
                duration_hours,

            "mount_stromlo_dual_stream_video_duration_relation":
                "GREATER_THAN",

            "mount_stromlo_dual_stream_video_hours":
                stromlo_hours,

            "mount_stromlo_maximum_demonstrated_downlink_rate_mbps":
                float(
                    stromlo[
                        "maximum_demonstrated_downlink_rate_mbps"
                    ]
                ),

            "earthset_images_downlinked":
                results[
                    "content_and_direction"
                ][
                    "earthset_images_downlinked"
                ],

            "earthrise_images_downlinked":
                results[
                    "content_and_direction"
                ][
                    "earthrise_images_downlinked"
                ],

            "forward_data_to_orion_demonstrated":
                results[
                    "content_and_direction"
                ][
                    "forward_data_to_orion_demonstrated"
                ],
        },

        "derived_metrics": {
            "maximum_return_to_forward_rate_ratio":
                max_rate_ratio,

            "main_ground_station_26gb_transfer_duration_upper_bound_seconds":
                duration_upper_bound_seconds,

            "main_ground_station_26gb_average_rate_lower_bound_mbps_decimal_gb":
                minimum_average_rate_mbps,

            "mount_stromlo_dual_stream_video_duration_lower_bound_seconds":
                stromlo_seconds_lower_bound,
        },

        "source_evidence_layer_counts":
            dict(
                evidence_counts
            ),

        "performance_metric_count":
            len(metrics),

        "guardrails":
            reference[
                "guardrails"
            ],

        "outputs": {
            "performance_metrics_csv":
                str(
                    OUTPUT_METRICS.relative_to(
                        ROOT
                    )
                ),

            "architecture_figure":
                str(
                    ARCHITECTURE_FIGURE.relative_to(
                        ROOT
                    )
                ),

            "link_rate_figure":
                str(
                    LINK_RATE_FIGURE.relative_to(
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
        "Phase 2H.3 O2O Optical Communications Analysis"
    )

    print("=" * 59)

    print()
    print(
        "Architecture:"
    )

    print(
        f"  wavelength: "
        f"{architecture['nominal_wavelength_nm']} nm"
    )

    print(
        f"  max return/downlink: "
        f"{max_return_mbps:.0f} Mbps"
    )

    print(
        f"  max forward/uplink: "
        f"{max_forward_mbps:.0f} Mbps"
    )

    print(
        f"  max return / max forward ratio: "
        f"{max_rate_ratio:.3f}x"
    )

    print(
        f"  telescope aperture: "
        f"{optical_module['telescope_aperture_inches']} in"
    )

    print(
        f"  gimbals: "
        f"{optical_module['gimbal_count']}"
    )

    print()
    print(
        "Ground segment:"
    )

    print(
        f"  main sites: "
        f"{len(main_sites)}"
    )

    for site in main_sites:
        print(
            f"    {site['name']}"
        )

    print(
        f"  additional demonstrated sites: "
        f"{len(additional_sites)}"
    )

    for site in additional_sites:
        print(
            f"    {site['name']}"
        )

    print()
    print(
        "Mission-control operations segment:"
    )

    print(
        f"  {operations_segment['location']}"
    )

    for element in (
        operations_segment[
            "elements"
        ]
    ):
        print(
            f"    {element['short_name']}: "
            f"{element['name']}"
        )

    print()
    print(
        "Live mission evidence:"
    )

    print(
        "  Flight Day 3 ground links:"
    )

    print(
        f"    precision: "
        f"{flight_day_3['precision']}"
    )

    print(
        "  Flight Day 4 100 GB milestone:"
    )

    print(
        f"    precision: "
        f"{milestone_100gb['precision']}"
    )

    print(
        "    approximate anchor:"
    )

    print(
        "      ~"
        f"{milestone_100gb['approximate_anchor_utc']}"
    )

    print()
    print(
        "Postflight results:"
    )

    print(
        f"  mission data exchanged: "
        f"{total_exchange_gb:.0f} GB"
    )

    print(
        f"  maximum demonstrated downlink: "
        f"{max_demonstrated_mbps:.0f} Mbps"
    )

    print(
        f"  main-station transfer: "
        f"{transfer_gb:.0f} GB in <"
        f"{duration_hours:.0f} h"
    )

    print(
        f"  derived average-rate lower bound:"
    )

    print(
        f"    >{minimum_average_rate_mbps:.3f} Mbps"
    )

    print(
        "  Mount Stromlo dual-stream video:"
    )

    print(
        f"    >{stromlo_hours:.1f} h"
    )

    print(
        "  Mount Stromlo maximum demonstrated:"
    )

    print(
        "    "
        f"{stromlo['maximum_demonstrated_downlink_rate_mbps']} Mbps"
    )

    print(
        "  Earthset imagery downlinked:"
    )

    print(
        "    TRUE"
    )

    print(
        "  Earthrise imagery downlinked:"
    )

    print(
        "    TRUE"
    )

    print(
        "  forward link to Orion demonstrated:"
    )

    print(
        "    TRUE"
    )

    print()
    print(
        "Primary-communications boundary:"
    )

    print(
        "  O2O primary RF replacement:"
    )

    print(
        "    FALSE"
    )

    print(
        "  primary RF networks:"
    )

    for network in (
        mission_role[
            "primary_mission_communications"
        ]
    ):
        print(
            f"    {network}"
        )

    print()
    print(
        "Generated metrics:"
    )

    print(
        f"  rows: {len(metrics)}"
    )

    print()
    print(
        "Wrote:"
    )

    print(
        "  "
        f"{OUTPUT_METRICS.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{OUTPUT_SUMMARY.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{ARCHITECTURE_FIGURE.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{LINK_RATE_FIGURE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
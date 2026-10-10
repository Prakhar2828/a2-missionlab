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
    / "artemis_ii_gnc_architecture.json"
)

PROPULSION_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_esm_propulsion_architecture.json"
)

MANEUVER_THREADS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_operational_threads.json"
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
            f"Missing required file: {path}"
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


def build_architecture_figure(reference) -> None:
    ARCHITECTURE_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(16, 10)
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
        "Artemis II / Orion Guidance, Navigation, and Control Architecture",
        fontsize=15,
        pad=20,
    )

    domain_y = {
        "NAVIGATION":
            0.80,

        "GUIDANCE":
            0.54,

        "CONTROL":
            0.28,
    }

    navigation_text = (
        "NAVIGATION\n"
        "Where am I, how am I moving, and which way am I pointed?\n\n"
        "Onboard: Star Tracker | IMU | GPS | Barometric Altimeter | "
        "OpNav Camera | Sun Sensor\n"
        "External support: Deep Space Network tracking"
    )

    guidance_text = (
        "GUIDANCE\n"
        "Where should Orion go or point next?\n\n"
        "GNC&P flight software | Ground commands | Crew commands | "
        "Trajectory / attitude objectives\n"
        "Manual and automated modes"
    )

    control_text = (
        "CONTROL\n"
        "How does Orion follow the commanded motion or attitude?\n\n"
        "RHC / THC -> GNC flight software -> effector selection\n"
        "RCS: 24 | Auxiliary: 8 | Main engine: 1"
    )

    for label, text in [
        (
            "NAVIGATION",
            navigation_text,
        ),
        (
            "GUIDANCE",
            guidance_text,
        ),
        (
            "CONTROL",
            control_text,
        ),
    ]:
        ax.text(
            0.5,
            domain_y[
                label
            ],
            text,
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
            0.5,
            0.64,
        ),
        xytext=(
            0.5,
            0.70,
        ),
        arrowprops={
            "arrowstyle":
                "->",
        },
    )

    ax.annotate(
        "",
        xy=(
            0.5,
            0.38,
        ),
        xytext=(
            0.5,
            0.44,
        ),
        arrowprops={
            "arrowstyle":
                "->",
        },
    )

    ax.text(
        0.5,
        0.07,
        (
            "Architecture capability does not establish the as-flown "
            "sensor measurement, navigation-filter state, guidance-command, "
            "controller-input, or thruster-firing history."
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


def build_boundary_figure(reference) -> None:
    BOUNDARY_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    boundaries = (
        reference[
            "current_public_source_set_boundaries"
        ]
    )

    rows = [
        [
            key,
            (
                "AVAILABLE"
                if value
                else "NOT AVAILABLE"
            ),
        ]
        for key, value in boundaries.items()
    ]

    fig, ax = plt.subplots(
        figsize=(15, 11)
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        "Phase 2J.1 Public GNC Evidence Boundary",
        fontsize=15,
        pad=18,
    )

    table = ax.table(
        cellText=rows,
        colLabels=[
            "Evidence Item",
            "Current Public Source Set",
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
        1.55,
    )

    ax.text(
        0.5,
        0.025,
        (
            "NOT AVAILABLE means not established in the current curated "
            "MissionLab public source set. It is not a claim that no such "
            "record exists anywhere."
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

    propulsion = load_json(
        PROPULSION_PATH
    )

    maneuver_threads = load_json(
        MANEUVER_THREADS_PATH
    )

    if (
        reference.get(
            "dataset_id"
        )
        != "phase2j1_artemis_ii_gnc_architecture"
    ):
        fail(
            "Unexpected Phase 2J.1 dataset ID."
        )

    if (
        propulsion.get(
            "dataset_id"
        )
        != "phase2i2_artemis_ii_esm_propulsion_architecture"
    ):
        fail(
            "Unexpected Phase 2I.2 dataset ID."
        )

    if (
        maneuver_threads.get(
            "dataset_id"
        )
        != "phase2i4_artemis_ii_maneuver_operational_threads"
    ):
        fail(
            "Unexpected Phase 2I.4 dataset ID."
        )

    domains = (
        reference[
            "gnc_domain_model"
        ]
    )

    if set(
        domains
    ) != {
        "navigation",
        "guidance",
        "control",
    }:
        fail(
            "GNC domain decomposition changed."
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
            "Navigation sensor architecture changed."
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
            "Deep Space Network boundary changed."
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

    for engine_id, count in (
        expected_counts.items()
    ):
        if (
            engine_classes[
                engine_id
            ][
                "count"
            ]
            != count
        ):
            fail(
                f"{engine_id} count changed."
            )

    effectors = {
        item[
            "effector_id"
        ]:
            item
        for item in reference[
            "control_effectors"
        ]
    }

    for engine_id, count in (
        expected_counts.items()
    ):
        if (
            effectors[
                engine_id
            ][
                "count"
            ]
            != count
        ):
            fail(
                f"{engine_id} Phase 2J.1 count mismatch."
            )

    anchors = {
        item[
            "event_id"
        ]:
            item
        for item in reference[
            "artemis_ii_operational_anchors"
        ]
    }

    if (
        anchors[
            "proximity_operations_demonstration"
        ][
            "execution_status"
        ]
        != "COMPLETED"
        or anchors[
            "proximity_operations_demonstration"
        ][
            "duration_minutes"
        ]
        != 70
    ):
        fail(
            "Proximity-operations anchor changed."
        )

    if (
        anchors[
            "flight_day_4_manual_piloting"
        ][
            "execution_status"
        ]
        != "COMPLETED"
        or anchors[
            "flight_day_4_manual_piloting"
        ][
            "duration_minutes"
        ]
        != 41
    ):
        fail(
            "Flight Day 4 manual-control anchor changed."
        )

    if (
        anchors[
            "flight_day_8_manual_piloting"
        ][
            "execution_status"
        ]
        != "FOREGONE"
        or anchors[
            "flight_day_8_manual_piloting"
        ][
            "performed"
        ]
        is not False
    ):
        fail(
            "Flight Day 8 execution boundary changed."
        )

    COMPONENT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    component_rows = []

    component_rows.append(
        {
            "component_id":
                "gncp_flight_software",

            "category":
                "SOFTWARE",

            "gnc_domain":
                "GUIDANCE_NAVIGATION_CONTROL",

            "role":
                (
                    "RECEIVE_NAVIGATION_AND_PILOT_INPUTS_"
                    "AND_COMMAND_EFFECTORS"
                ),

            "count":
                "",

            "raw_as_flown_history_available":
                "false",
        }
    )

    for sensor in sensors:
        component_rows.append(
            {
                "component_id":
                    sensor[
                        "sensor_id"
                    ],

                "category":
                    "ONBOARD_NAVIGATION_SENSOR",

                "gnc_domain":
                    "NAVIGATION",

                "role":
                    sensor[
                        "role"
                    ],

                "count":
                    "",

                "raw_as_flown_history_available":
                    str(
                        sensor[
                            "raw_artemis_ii_measurements_available_in_current_source_set"
                        ]
                    ).lower(),
            }
        )

    component_rows.append(
        {
            "component_id":
                "deep_space_network_tracking",

            "category":
                "EXTERNAL_NAVIGATION_SUPPORT",

            "gnc_domain":
                "NAVIGATION",

            "role":
                external[
                    0
                ][
                    "role"
                ],

            "count":
                "",

            "raw_as_flown_history_available":
                str(
                    external[
                        0
                    ][
                        "raw_artemis_ii_tracking_observables_available_in_current_source_set"
                    ]
                ).lower(),
        }
    )

    for controller_id, controller in [
        (
            "rotational_hand_controller",
            reference[
                "manual_control_architecture"
            ][
                "rotational_hand_controller"
            ],
        ),
        (
            "translational_hand_controller",
            reference[
                "manual_control_architecture"
            ][
                "translational_hand_controller"
            ],
        ),
    ]:
        component_rows.append(
            {
                "component_id":
                    controller_id,

                "category":
                    "CREW_CONTROL_INPUT",

                "gnc_domain":
                    "CONTROL",

                "role":
                    controller[
                        "command_domain"
                    ],

                "count":
                    "",

                "raw_as_flown_history_available":
                    "false",
            }
        )

    for effector in (
        reference[
            "control_effectors"
        ]
    ):
        component_rows.append(
            {
                "component_id":
                    effector[
                        "effector_id"
                    ],

                "category":
                    "CONTROL_EFFECTOR",

                "gnc_domain":
                    "CONTROL",

                "role":
                    effector[
                        "control_role"
                    ],

                "count":
                    effector[
                        "count"
                    ],

                "raw_as_flown_history_available":
                    "false",
            }
        )

    component_fields = [
        "component_id",
        "category",
        "gnc_domain",
        "role",
        "count",
        "raw_as_flown_history_available",
    ]

    with COMPONENT_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=component_fields,
        )

        writer.writeheader()
        writer.writerows(
            component_rows
        )

    boundaries = (
        reference[
            "current_public_source_set_boundaries"
        ]
    )

    boundary_rows = [
        {
            "boundary_id":
                key,

            "available":
                str(
                    value
                ).lower(),
        }
        for key, value in boundaries.items()
    ]

    with BOUNDARY_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "boundary_id",
                "available",
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
            "phase2j1_gnc_architecture_analysis",

        "mission":
            "Artemis II",

        "reference_dataset_id":
            reference[
                "dataset_id"
            ],

        "domain_count":
            len(
                domains
            ),

        "onboard_navigation_sensor_count":
            len(
                sensors
            ),

        "external_navigation_support_count":
            len(
                external
            ),

        "manual_controller_count":
            2,

        "control_effector_class_count":
            len(
                reference[
                    "control_effectors"
                ]
            ),

        "architecture_component_rows":
            len(
                component_rows
            ),

        "evidence_boundary_rows":
            len(
                boundary_rows
            ),

        "operational_anchor_count":
            len(
                anchors
            ),

        "operational_anchors":
            reference[
                "artemis_ii_operational_anchors"
            ],

        "current_public_source_set_boundaries":
            boundaries,

        "cross_phase_boundaries":
            reference[
                "cross_phase_boundaries"
            ],

        "guardrails":
            reference[
                "guardrails"
            ],

        "outputs": {
            "component_csv":
                str(
                    COMPONENT_CSV.relative_to(
                        ROOT
                    )
                ),

            "boundary_csv":
                str(
                    BOUNDARY_CSV.relative_to(
                        ROOT
                    )
                ),

            "architecture_figure":
                str(
                    ARCHITECTURE_FIGURE.relative_to(
                        ROOT
                    )
                ),

            "boundary_figure":
                str(
                    BOUNDARY_FIGURE.relative_to(
                        ROOT
                    )
                ),
        },
    }

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with SUMMARY_PATH.open(
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
        "Phase 2J.1 GNC Architecture / Evidence Analysis"
    )

    print("=" * 68)

    print()
    print(
        "GNC domains:"
    )

    print(
        "  NAVIGATION"
    )

    print(
        "  GUIDANCE"
    )

    print(
        "  CONTROL"
    )

    print()
    print(
        "GNC&P flight software:"
    )

    print(
        "  navigation sensor inputs: TRUE"
    )

    print(
        "  pilot-control inputs: TRUE"
    )

    print(
        "  crew commands: TRUE"
    )

    print(
        "  ground commands: TRUE"
    )

    print(
        "  manual mode: TRUE"
    )

    print(
        "  automated mode: TRUE"
    )

    print(
        "  effector commanding: TRUE"
    )

    print()
    print(
        "Onboard navigation sensors:"
    )

    for sensor in sensors:
        print(
            f"  {sensor['sensor_id']}: "
            f"{sensor['measurement_domain']}"
        )

    print()
    print(
        "External navigation support:"
    )

    print(
        "  DEEP_SPACE_NETWORK_TRACKING"
    )

    print(
        "  onboard sensor: FALSE"
    )

    print()
    print(
        "Manual-control architecture:"
    )

    print(
        "  RHC -> ATTITUDE"
    )

    print(
        "  THC -> TRANSLATION"
    )

    print(
        "  GNC flight software performs effector selection"
    )

    print()
    print(
        "Control effectors:"
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
        "    ~70 min"
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
        "    6-DOF / 3-DOF"
    )

    print(
        "  Flight Day 8 manual piloting:"
    )

    print(
        "    FOREGONE"
    )

    print()
    print(
        "Current-source-set unavailable histories:"
    )

    for key, value in boundaries.items():
        if value is False:
            print(
                f"  {key}"
            )

    print()
    print(
        "Cross-phase boundaries:"
    )

    for key, value in (
        reference[
            "cross_phase_boundaries"
        ].items()
    ):
        print(
            f"  {key}: "
            + (
                "TRUE"
                if value
                else "FALSE"
            )
        )

    print()
    print(
        "Wrote:"
    )

    print(
        "  "
        f"{COMPONENT_CSV.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{BOUNDARY_CSV.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{SUMMARY_PATH.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{ARCHITECTURE_FIGURE.relative_to(ROOT)}"
    )

    print(
        "  "
        f"{BOUNDARY_FIGURE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
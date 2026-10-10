from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_entry_profile_heritage.json"
)

ENTRY_M50_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_trajectory_m50.csv"
)

DYNAMICS_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_dynamics.csv"
)

DYNAMICS_SUMMARY_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_dynamics_summary.json"
)

EVENT_CORRELATIONS_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_event_correlations.json"
)

OUTPUT_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "artemis_entry_profile_comparison.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
)

DURATION_FIGURE = (
    ASSET_DIR
    / "phase2f_entry_duration_comparison.svg"
)

ALTITUDE_FIGURE = (
    ASSET_DIR
    / "phase2f_skip_loft_altitude_comparison.svg"
)

REBOUND_FIGURE = (
    ASSET_DIR
    / "phase2f_artemis_ii_rebound_profile.svg"
)


FT_TO_KM = 0.0003048
MPH_TO_KM_S = 0.00044704

EXPECTED_ENTRY_RECORDS = 819


plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def normalize_svg(
    path: Path,
) -> None:
    text = path.read_text(
        encoding="utf-8",
    )

    cleaned = "\n".join(
        line.rstrip(
            " \t"
        )
        for line in text.splitlines()
    ) + "\n"

    path.write_text(
        cleaned,
        encoding="utf-8",
    )


def load_json(
    path: Path,
):
    if not path.exists():
        raise SystemExit(
            "Missing required file:\n"
            f"{path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(
            f
        )


def load_csv(
    path: Path,
):
    if not path.exists():
        raise SystemExit(
            "Missing required file:\n"
            f"{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return list(
            csv.DictReader(
                f
            )
        )


def add_bar_labels(
    ax,
    bars,
    decimals: int,
) -> None:
    for bar in bars:
        height = float(
            bar.get_height()
        )

        ax.annotate(
            f"{height:.{decimals}f}",
            (
                bar.get_x()
                + bar.get_width()
                / 2.0,
                height,
            ),
            xytext=(
                0,
                4,
            ),
            textcoords=(
                "offset points"
            ),
            ha="center",
            va="bottom",
        )


def make_duration_figure(
    artemis_i_duration_s: float,
    artemis_ii_duration_s: float,
) -> None:
    labels = [
        "Artemis I\nskip entry",
        "Artemis II\nlofted / no skip",
    ]

    values = [
        artemis_i_duration_s,
        artemis_ii_duration_s,
    ]

    fig, ax = plt.subplots(
        figsize=(
            7.5,
            5.0,
        )
    )

    bars = ax.bar(
        labels,
        values,
    )

    add_bar_labels(
        ax,
        bars,
        decimals=1,
    )

    ax.set_ylabel(
        "EI-to-terminal duration (s)"
    )

    ax.set_title(
        "Artemis Entry-Profile Duration Comparison"
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        DURATION_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(
        fig
    )

    normalize_svg(
        DURATION_FIGURE
    )


def make_altitude_figure(
    artemis_i_skip_apogee_km: float,
    artemis_ii_rebound_top_km: float,
) -> None:
    labels = [
        "Artemis I\nskip apogee",
        "Artemis II\nrebound top",
    ]

    values = [
        artemis_i_skip_apogee_km,
        artemis_ii_rebound_top_km,
    ]

    fig, ax = plt.subplots(
        figsize=(
            7.5,
            5.0,
        )
    )

    bars = ax.bar(
        labels,
        values,
    )

    add_bar_labels(
        ax,
        bars,
        decimals=3,
    )

    ax.set_ylabel(
        "Geodetic altitude (km)"
    )

    ax.set_title(
        "Artemis I Skip Apogee vs "
        "Artemis II Rebound Top"
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        ALTITUDE_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(
        fig
    )

    normalize_svg(
        ALTITUDE_FIGURE
    )


def make_rebound_figure(
    elapsed_s: np.ndarray,
    altitude_km: np.ndarray,
    rebound_start: dict,
    rebound_end: dict,
) -> None:
    plot_stop_s = max(
        320.0,
        float(
            rebound_end[
                "elapsed_seconds"
            ]
        )
        + 50.0,
    )

    mask = (
        elapsed_s
        <= plot_stop_s
    )

    fig, ax = plt.subplots(
        figsize=(
            9.0,
            5.5,
        )
    )

    ax.plot(
        elapsed_s[
            mask
        ],
        altitude_km[
            mask
        ],
    )

    start_time = float(
        rebound_start[
            "elapsed_seconds"
        ]
    )

    start_altitude = float(
        rebound_start[
            "altitude_km"
        ]
    )

    end_time = float(
        rebound_end[
            "elapsed_seconds"
        ]
    )

    end_altitude = float(
        rebound_end[
            "altitude_km"
        ]
    )

    ax.scatter(
        [
            start_time,
            end_time,
        ],
        [
            start_altitude,
            end_altitude,
        ],
        zorder=3,
    )

    ax.annotate(
        (
            "Descent → climb\n"
            f"EI+{start_time:.1f} s\n"
            f"{start_altitude:.3f} km"
        ),
        (
            start_time,
            start_altitude,
        ),
        xytext=(
            12,
            -38,
        ),
        textcoords=(
            "offset points"
        ),
    )

    ax.annotate(
        (
            "Climb → descent\n"
            f"EI+{end_time:.1f} s\n"
            f"{end_altitude:.3f} km"
        ),
        (
            end_time,
            end_altitude,
        ),
        xytext=(
            12,
            12,
        ),
        textcoords=(
            "offset points"
        ),
    )

    ax.set_xlabel(
        "Seconds after Entry Interface"
    )

    ax.set_ylabel(
        "WGS 84 altitude (km)"
    )

    ax.set_title(
        "Artemis II Derived Vertical Rebound / Loft"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        REBOUND_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(
        fig
    )

    normalize_svg(
        REBOUND_FIGURE
    )


def main() -> None:
    reference = load_json(
        REFERENCE_JSON
    )

    m50_rows = load_csv(
        ENTRY_M50_CSV
    )

    dynamics_rows = load_csv(
        DYNAMICS_CSV
    )

    dynamics_summary = load_json(
        DYNAMICS_SUMMARY_JSON
    )

    event_correlations = load_json(
        EVENT_CORRELATIONS_JSON
    )

    if len(
        m50_rows
    ) != EXPECTED_ENTRY_RECORDS:
        raise SystemExit(
            "Expected "
            f"{EXPECTED_ENTRY_RECORDS} "
            "high-rate entry records, found "
            f"{len(m50_rows)}"
        )

    if len(
        dynamics_rows
    ) != EXPECTED_ENTRY_RECORDS:
        raise SystemExit(
            "Expected "
            f"{EXPECTED_ENTRY_RECORDS} "
            "entry-dynamics records, found "
            f"{len(dynamics_rows)}"
        )

    evidence_by_id = {
        item[
            "id"
        ]: item
        for item in reference[
            "evidence_items"
        ]
    }

    artemis_i_ei = (
        evidence_by_id[
            "artemis_i_entry_interface_state"
        ][
            "key_values"
        ]
    )

    artemis_i_skip = (
        evidence_by_id[
            "artemis_i_skip_apogee"
        ][
            "key_values"
        ]
    )

    artemis_i_acceleration = (
        evidence_by_id[
            "artemis_i_sensed_acceleration_peaks"
        ][
            "key_values"
        ]
    )

    artemis_i_duration = (
        evidence_by_id[
            "artemis_i_ei_to_splashdown_duration"
        ][
            "key_values"
        ]
    )

    artemis_ii_classification = (
        evidence_by_id[
            "artemis_ii_no_skip_entry"
        ][
            "key_values"
        ][
            "entry_classification"
        ]
    )

    artemis_ii_public_label = (
        evidence_by_id[
            "artemis_ii_lofted_entry_label"
        ][
            "key_values"
        ][
            "public_profile_label"
        ]
    )

    artemis_ii_public_speed_mph = float(
        evidence_by_id[
            "artemis_ii_public_pre_ei_velocity"
        ][
            "key_values"
        ][
            "maximum_velocity_before_ei_mph"
        ]
    )

    rebound = dynamics_summary.get(
        "skip_rebound"
    )

    if rebound is None:
        raise SystemExit(
            "No Artemis II derived vertical "
            "rebound found."
        )

    rebound_start = rebound[
        "start"
    ]

    rebound_end = rebound[
        "end"
    ]

    entry_interface = (
        event_correlations[
            "entry_interface"
        ][
            "derived"
        ]
    )

    terminal_surface = (
        event_correlations[
            "splashdown"
        ][
            "derived_surface_crossing"
        ]
    )

    first_m50 = (
        m50_rows[0]
    )

    if (
        first_m50[
            "timestamp_utc"
        ]
        != entry_interface[
            "utc"
        ]
    ):
        raise SystemExit(
            "Artemis II high-rate first "
            "state does not match the "
            "derived Entry Interface epoch."
        )

    artemis_i_ei_inertial_speed_km_s = (
        float(
            artemis_i_ei[
                "inertial_velocity_magnitude_ft_s"
            ]
        )
        * FT_TO_KM
    )

    artemis_ii_ei_inertial_speed_km_s = float(
        first_m50[
            "inertial_speed_km_s"
        ]
    )

    artemis_ii_public_speed_km_s = (
        artemis_ii_public_speed_mph
        * MPH_TO_KM_S
    )

    artemis_i_duration_s = float(
        artemis_i_duration[
            "ei_to_splashdown_seconds"
        ]
    )

    artemis_ii_duration_s = float(
        terminal_surface[
            "ei_elapsed_seconds"
        ]
    )

    duration_difference_s = (
        artemis_i_duration_s
        - artemis_ii_duration_s
    )

    duration_reduction_percent = (
        100.0
        * duration_difference_s
        / artemis_i_duration_s
    )

    artemis_i_skip_apogee_km = float(
        artemis_i_skip[
            "actual_skip_apogee_km"
        ]
    )

    artemis_ii_rebound_top_km = float(
        rebound_end[
            "altitude_km"
        ]
    )

    upper_landmark_difference_km = (
        artemis_i_skip_apogee_km
        - artemis_ii_rebound_top_km
    )

    upper_landmark_lower_percent = (
        100.0
        * upper_landmark_difference_km
        / artemis_i_skip_apogee_km
    )

    inertial_speed_signed_difference_km_s = (
        artemis_ii_ei_inertial_speed_km_s
        - artemis_i_ei_inertial_speed_km_s
    )

    inertial_speed_absolute_difference_km_s = abs(
        inertial_speed_signed_difference_km_s
    )

    inertial_speed_relative_difference_percent = (
        100.0
        * inertial_speed_signed_difference_km_s
        / artemis_i_ei_inertial_speed_km_s
    )

    if (
        inertial_speed_signed_difference_km_s
        > 0.0
    ):
        inertial_speed_relationship = (
            "ARTEMIS_II_HIGHER"
        )

    elif (
        inertial_speed_signed_difference_km_s
        < 0.0
    ):
        inertial_speed_relationship = (
            "ARTEMIS_II_LOWER"
        )

    else:
        inertial_speed_relationship = (
            "EQUAL_WITHIN_NUMERIC_PRECISION"
        )

    public_speed_context_difference_m_s = (
        (
            artemis_ii_ei_inertial_speed_km_s
            - artemis_ii_public_speed_km_s
        )
        * 1000.0
    )

    elapsed_s = np.array(
        [
            float(
                row[
                    "ei_elapsed_seconds"
                ]
            )
            for row in dynamics_rows
        ],
        dtype=float,
    )

    altitude_km = np.array(
        [
            float(
                row[
                    "wgs84_altitude_km"
                ]
            )
            for row in dynamics_rows
        ],
        dtype=float,
    )

    result = {
        "product_id":
            "phase2f2_artemis_entry_profile_comparison",

        "reference_dataset":
            reference[
                "dataset_id"
            ],

        "provenance":
            (
                "MIXED_NASA_REPORTED_"
                "NASA_FLIGHT_DERIVED_"
                "MISSIONLAB_DERIVED"
            ),

        "comparison_scope":
            (
                "Landmark-level comparison of "
                "Artemis I skip-entry heritage "
                "with the Artemis II modified "
                "lofted/no-skip entry profile."
            ),

        "artemis_i": {
            "entry_classification":
                "SKIP_ENTRY",

            "entry_interface": {
                "geodetic_altitude_ft":
                    float(
                        artemis_i_ei[
                            "geodetic_altitude_ft"
                        ]
                    ),

                "inertial_velocity_magnitude_ft_s":
                    float(
                        artemis_i_ei[
                            "inertial_velocity_magnitude_ft_s"
                        ]
                    ),

                "inertial_velocity_magnitude_km_s":
                    artemis_i_ei_inertial_speed_km_s,

                "provenance":
                    "NASA_REPORTED",
            },

            "skip_apogee": {
                "altitude_kft":
                    float(
                        artemis_i_skip[
                            "actual_skip_apogee_kft"
                        ]
                    ),

                "altitude_km":
                    artemis_i_skip_apogee_km,

                "provenance":
                    "NASA_REPORTED",
            },

            "ei_to_splashdown": {
                "duration_seconds":
                    artemis_i_duration_s,

                "entry_interface_met":
                    artemis_i_duration[
                        "entry_interface_met"
                    ],

                "splashdown_met":
                    artemis_i_duration[
                        "splashdown_met"
                    ],

                "provenance":
                    "NASA_REPORTED",
            },
        },

        "artemis_ii": {
            "nasa_entry_classification":
                artemis_ii_classification,

            "nasa_public_profile_label":
                artemis_ii_public_label,

            "missionlab_profile_label":
                (
                    "DERIVED_VERTICAL_REBOUND_"
                    "OR_LOFT_NOT_SKIP_ENTRY"
                ),

            "entry_interface": {
                "utc":
                    entry_interface[
                        "utc"
                    ],

                "wgs84_altitude_km":
                    float(
                        entry_interface[
                            "wgs84_altitude_km"
                        ]
                    ),

                "earth_relative_speed_km_s":
                    float(
                        entry_interface[
                            "earth_relative_speed_km_s"
                        ]
                    ),

                "m50_inertial_speed_km_s":
                    artemis_ii_ei_inertial_speed_km_s,

                "m50_source_timestamp_utc":
                    first_m50[
                        "timestamp_utc"
                    ],

                "trajectory_provenance":
                    (
                        "NASA flight-derived "
                        "high-rate ephemeris"
                    ),
            },

            "derived_vertical_rebound": {
                "descent_to_climb":
                    rebound_start,

                "climb_to_descent":
                    rebound_end,

                "duration_seconds":
                    float(
                        rebound[
                            "duration_seconds"
                        ]
                    ),

                "altitude_recovery_km":
                    float(
                        rebound[
                            "altitude_recovery_km"
                        ]
                    ),

                "speed_loss_km_s":
                    float(
                        rebound[
                            "speed_loss_km_s"
                        ]
                    ),

                "classification":
                    (
                        "MISSIONLAB_DERIVED_"
                        "VERTICAL_REBOUND_OR_LOFT"
                    ),

                "explicit_nonclassification":
                    "NOT_A_SKIP_ENTRY",
            },

            "terminal_surface_crossing": {
                "utc":
                    terminal_surface[
                        "utc"
                    ],

                "ei_elapsed_seconds":
                    artemis_ii_duration_s,

                "classification":
                    (
                        "DERIVED_SPLASHDOWN_"
                        "CORRELATED_SURFACE_CROSSING"
                    ),
            },
        },

        "primary_comparisons": {
            "entry_duration": {
                "artemis_i_seconds":
                    artemis_i_duration_s,

                "artemis_ii_seconds":
                    artemis_ii_duration_s,

                "artemis_ii_shorter_by_seconds":
                    duration_difference_s,

                "artemis_ii_shorter_by_percent":
                    duration_reduction_percent,

                "semantics":
                    (
                        "Artemis I uses NASA-reported "
                        "Entry Interface and splashdown "
                        "MET epochs. Artemis II uses "
                        "MissionLab Entry Interface and "
                        "the derived WGS84 surface "
                        "crossing correlated with NASA's "
                        "splashdown minute."
                    ),
            },

            "upper_profile_landmark_altitude": {
                "artemis_i_skip_apogee_km":
                    artemis_i_skip_apogee_km,

                "artemis_ii_rebound_top_km":
                    artemis_ii_rebound_top_km,

                "artemis_ii_lower_by_km":
                    upper_landmark_difference_km,

                "artemis_ii_lower_by_percent_of_artemis_i_skip_apogee":
                    upper_landmark_lower_percent,

                "semantics":
                    (
                        "These are upper-profile "
                        "landmarks from differently "
                        "classified trajectories. "
                        "They are not asserted to be "
                        "identical guidance phases."
                    ),
            },

            "entry_interface_inertial_speed": {
                "artemis_i_km_s":
                    artemis_i_ei_inertial_speed_km_s,

                "artemis_ii_km_s":
                    artemis_ii_ei_inertial_speed_km_s,

                "artemis_ii_minus_artemis_i_km_s":
                    inertial_speed_signed_difference_km_s,

                "absolute_difference_km_s":
                    inertial_speed_absolute_difference_km_s,

                "absolute_difference_m_s":
                    (
                        inertial_speed_absolute_difference_km_s
                        * 1000.0
                    ),

                "artemis_ii_relative_difference_percent":
                    inertial_speed_relative_difference_percent,

                "relationship":
                    inertial_speed_relationship,

                "artemis_i_semantics":
                    (
                        "NASA-reported reconstructed "
                        "Entry Interface inertial "
                        "velocity magnitude"
                    ),

                "artemis_ii_semantics":
                    (
                        "NASA flight-derived high-rate "
                        "M50 source-state inertial "
                        "velocity magnitude at the "
                        "MissionLab Entry Interface epoch"
                    ),

                "comparison_basis":
                    (
                        "Velocity magnitude is used "
                        "rather than vector components. "
                        "A pure inertial-frame rotation "
                        "does not change vector magnitude."
                    ),
            },
        },

        "context_only": {
            "artemis_i_sensed_acceleration": {
                "first_peak_g":
                    float(
                        artemis_i_acceleration[
                            "first_peak_sensed_acceleration_g"
                        ]
                    ),

                "second_peak_g":
                    float(
                        artemis_i_acceleration[
                            "second_peak_sensed_acceleration_g"
                        ]
                    ),

                "comparison_status":
                    (
                        "NOT_DIRECTLY_COMPARABLE_TO_"
                        "PHASE2C_KINEMATIC_G0_EQUIVALENT"
                    ),
            },

            "artemis_ii_public_pre_ei_velocity": {
                "reported_mph":
                    artemis_ii_public_speed_mph,

                "converted_km_s":
                    artemis_ii_public_speed_km_s,

                "first_m50_minus_public_value_m_s":
                    public_speed_context_difference_m_s,

                "comparison_status":
                    "CONTEXT_ONLY",

                "reason":
                    (
                        "The public maximum-velocity "
                        "statement does not provide "
                        "the same technical state "
                        "definition as the high-rate "
                        "Entry Interface source state."
                    ),
            },
        },

        "figures": [
            str(
                DURATION_FIGURE.relative_to(
                    ROOT
                )
            ),
            str(
                ALTITUDE_FIGURE.relative_to(
                    ROOT
                )
            ),
            str(
                REBOUND_FIGURE.relative_to(
                    ROOT
                )
            ),
        ],

        "interpretation_guardrails":
            reference[
                "interpretation_guardrails"
            ],

        "interpretation_limits": [
            (
                "MissionLab does not currently "
                "ingest a full Artemis I "
                "postflight trajectory time series."
            ),
            (
                "This is therefore a landmark-level "
                "cross-mission comparison rather "
                "than a point-by-point trajectory "
                "residual analysis."
            ),
            (
                "The Artemis II altitude rebound "
                "is a derived geometric feature "
                "from vertical-velocity sign "
                "changes and is not labeled a "
                "skip entry."
            ),
            (
                "Artemis I skip-apogee altitude "
                "and Artemis II rebound-top "
                "altitude are useful upper-profile "
                "landmarks but are not identical "
                "guidance events."
            ),
            (
                "Artemis I sensed acceleration "
                "is not compared numerically with "
                "MissionLab Phase 2C kinematic "
                "deceleration divided by g0."
            ),
            (
                "No entry-profile comparison is "
                "converted into a prediction of "
                "Avcoat char loss, recession, "
                "damage, or crew load."
            ),
        ],
    }

    OUTPUT_JSON.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
        )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    make_duration_figure(
        artemis_i_duration_s,
        artemis_ii_duration_s,
    )

    make_altitude_figure(
        artemis_i_skip_apogee_km,
        artemis_ii_rebound_top_km,
    )

    make_rebound_figure(
        elapsed_s,
        altitude_km,
        rebound_start,
        rebound_end,
    )

    print()
    print(
        "Phase 2F.2 Artemis Entry-Profile "
        "Comparison"
    )

    print(
        "================================"
    )

    print()
    print(
        "PROFILE CLASSIFICATION"
    )

    print(
        "----------------------"
    )

    print(
        "Artemis I:"
    )

    print(
        "  SKIP ENTRY"
    )

    print(
        "Artemis II NASA classification:"
    )

    print(
        "  MODIFIED TRAJECTORY "
        "WITHOUT SKIP ENTRY"
    )

    print(
        "Artemis II NASA public label:"
    )

    print(
        "  LOFTED ENTRY SEQUENCE"
    )

    print(
        "MissionLab derived feature:"
    )

    print(
        "  VERTICAL REBOUND / LOFT"
    )

    print(
        "  NOT A SKIP ENTRY"
    )

    print()
    print(
        "EI-TO-TERMINAL DURATION"
    )

    print(
        "-----------------------"
    )

    print(
        f"Artemis I:  "
        f"{artemis_i_duration_s:.6f} s"
    )

    print(
        f"Artemis II: "
        f"{artemis_ii_duration_s:.6f} s"
    )

    print(
        f"Artemis II shorter by: "
        f"{duration_difference_s:.6f} s"
    )

    print(
        f"Reduction: "
        f"{duration_reduction_percent:.6f}%"
    )

    print()
    print(
        "UPPER-PROFILE LANDMARK"
    )

    print(
        "----------------------"
    )

    print(
        "Artemis I skip apogee:"
    )

    print(
        f"  {artemis_i_skip_apogee_km:.6f} km"
    )

    print(
        "Artemis II rebound top:"
    )

    print(
        f"  {artemis_ii_rebound_top_km:.6f} km"
    )

    print(
        "Difference:"
    )

    print(
        f"  {upper_landmark_difference_km:.6f} km"
    )

    print(
        "Artemis II landmark lower by:"
    )

    print(
        f"  {upper_landmark_lower_percent:.6f}%"
    )

    print()
    print(
        "ARTEMIS II REBOUND STRUCTURE"
    )

    print(
        "----------------------------"
    )

    print(
        "Descent-to-climb:"
    )

    print(
        f"  EI+"
        f"{float(rebound_start['elapsed_seconds']):.6f} s"
    )

    print(
        f"  altitude "
        f"{float(rebound_start['altitude_km']):.6f} km"
    )

    print(
        "Climb-to-descent:"
    )

    print(
        f"  EI+"
        f"{float(rebound_end['elapsed_seconds']):.6f} s"
    )

    print(
        f"  altitude "
        f"{float(rebound_end['altitude_km']):.6f} km"
    )

    print(
        f"Rebound duration: "
        f"{float(rebound['duration_seconds']):.6f} s"
    )

    print(
        f"Altitude recovery: "
        f"{float(rebound['altitude_recovery_km']):.6f} km"
    )

    print(
        f"Speed loss during rebound: "
        f"{float(rebound['speed_loss_km_s']):.6f} km/s"
    )

    print()
    print(
        "MATCHED EI INERTIAL-SPEED COMPARISON"
    )

    print(
        "------------------------------------"
    )

    print(
        "Artemis I NASA reconstructed EI:"
    )

    print(
        f"  {artemis_i_ei_inertial_speed_km_s:.9f} km/s"
    )

    print(
        "Artemis II NASA flight-derived "
        "M50 source state:"
    )

    print(
        f"  {artemis_ii_ei_inertial_speed_km_s:.9f} km/s"
    )

    print(
        "Artemis II - Artemis I:"
    )

    print(
        f"  "
        f"{inertial_speed_signed_difference_km_s:+.9f} km/s"
    )

    print(
        f"  "
        f"{inertial_speed_signed_difference_km_s * 1000.0:+.3f} m/s"
    )

    print(
        "Absolute difference:"
    )

    print(
        f"  "
        f"{inertial_speed_absolute_difference_km_s * 1000.0:.3f} m/s"
    )

    print(
        "Relative difference:"
    )

    print(
        f"  "
        f"{inertial_speed_relative_difference_percent:+.6f}%"
    )

    print(
        "Relationship:"
    )

    print(
        f"  {inertial_speed_relationship}"
    )

    print()
    print(
        "PUBLIC ARTEMIS II SPEED CONTEXT"
    )

    print(
        "-------------------------------"
    )

    print(
        f"NASA public value: "
        f"{artemis_ii_public_speed_mph:.0f} mph"
    )

    print(
        f"Converted: "
        f"{artemis_ii_public_speed_km_s:.9f} km/s"
    )

    print(
        "First M50 inertial state "
        "minus public value:"
    )

    print(
        f"  "
        f"{public_speed_context_difference_m_s:+.3f} m/s"
    )

    print(
        "Status: CONTEXT ONLY"
    )

    print()
    print(
        "ACCELERATION HERITAGE"
    )

    print(
        "---------------------"
    )

    print(
        "Artemis I sensed acceleration:"
    )

    print(
        f"  first peak  "
        f"{float(artemis_i_acceleration['first_peak_sensed_acceleration_g']):.2f} g"
    )

    print(
        f"  second peak "
        f"{float(artemis_i_acceleration['second_peak_sensed_acceleration_g']):.2f} g"
    )

    print(
        "Direct comparison with Phase 2C "
        "kinematic g0-equivalent:"
    )

    print(
        "  PROHIBITED"
    )

    print()
    print(
        "INTERPRETATION"
    )

    print(
        "--------------"
    )

    print(
        "Artemis I used a true skip-entry "
        "trajectory."
    )

    print(
        "Artemis II did not use the Artemis I "
        "skip entry."
    )

    print(
        "The Artemis II flight-derived "
        "trajectory contains a modest vertical "
        "rebound that is described as a loft, "
        "not a skip."
    )

    print(
        "The matched technical Entry Interface "
        "inertial-speed magnitudes differ by "
        "less than one tenth of one percent."
    )

    print(
        "This phase compares published and "
        "derived trajectory landmarks only."
    )

    print(
        "No TPS-damage or crew-load inference "
        "is made."
    )

    print()
    print(
        "Wrote:"
    )

    print(
        f"  {OUTPUT_JSON.relative_to(ROOT)}"
    )

    print(
        f"  {DURATION_FIGURE.relative_to(ROOT)}"
    )

    print(
        f"  {ALTITUDE_FIGURE.relative_to(ROOT)}"
    )

    print(
        f"  {REBOUND_FIGURE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
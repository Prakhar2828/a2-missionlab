from __future__ import annotations

import csv
import json
import math
from pathlib import Path


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

COMPARISON_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "artemis_entry_profile_comparison.json"
)

FIGURES = [
    (
        ROOT
        / "docs"
        / "assets"
        / "entry"
        / "phase2f_entry_duration_comparison.svg"
    ),
    (
        ROOT
        / "docs"
        / "assets"
        / "entry"
        / "phase2f_skip_loft_altitude_comparison.svg"
    ),
    (
        ROOT
        / "docs"
        / "assets"
        / "entry"
        / "phase2f_artemis_ii_rebound_profile.svg"
    ),
]


FT_TO_KM = 0.0003048


def fail(
    message: str,
) -> None:
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def load_json(
    path: Path,
):
    if not path.exists():
        fail(
            f"missing required file: {path}"
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
        fail(
            f"missing required file: {path}"
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


def close(
    actual: float,
    expected: float,
    tolerance: float,
    label: str,
) -> None:
    if not math.isclose(
        actual,
        expected,
        rel_tol=0.0,
        abs_tol=tolerance,
    ):
        fail(
            f"{label}: expected "
            f"{expected!r}, found "
            f"{actual!r}"
        )


def main() -> None:
    reference = load_json(
        REFERENCE_JSON
    )

    m50_rows = load_csv(
        ENTRY_M50_CSV
    )

    dynamics_summary = load_json(
        DYNAMICS_SUMMARY_JSON
    )

    events = load_json(
        EVENT_CORRELATIONS_JSON
    )

    comparison = load_json(
        COMPARISON_JSON
    )

    if (
        comparison.get(
            "product_id"
        )
        != "phase2f2_artemis_entry_profile_comparison"
    ):
        fail(
            "unexpected product_id"
        )

    if (
        comparison.get(
            "reference_dataset"
        )
        != reference.get(
            "dataset_id"
        )
    ):
        fail(
            "reference dataset mismatch"
        )

    if (
        comparison.get(
            "provenance"
        )
        != (
            "MIXED_NASA_REPORTED_"
            "NASA_FLIGHT_DERIVED_"
            "MISSIONLAB_DERIVED"
        )
    ):
        fail(
            "unexpected comparison provenance"
        )

    if len(
        m50_rows
    ) != 819:
        fail(
            "expected 819 M50 entry records"
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

    artemis_i_duration = (
        evidence_by_id[
            "artemis_i_ei_to_splashdown_duration"
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

    artemis_ii_reference_classification = (
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

    first_m50 = (
        m50_rows[0]
    )

    event_ei = (
        events[
            "entry_interface"
        ][
            "derived"
        ]
    )

    surface = (
        events[
            "splashdown"
        ][
            "derived_surface_crossing"
        ]
    )

    if (
        first_m50[
            "timestamp_utc"
        ]
        != event_ei[
            "utc"
        ]
    ):
        fail(
            "first M50 state does not "
            "match Entry Interface epoch"
        )

    rebound = dynamics_summary.get(
        "skip_rebound"
    )

    if rebound is None:
        fail(
            "missing Artemis II "
            "rebound summary"
        )

    expected_artemis_i_speed_km_s = (
        float(
            artemis_i_ei[
                "inertial_velocity_magnitude_ft_s"
            ]
        )
        * FT_TO_KM
    )

    expected_artemis_ii_speed_km_s = float(
        first_m50[
            "inertial_speed_km_s"
        ]
    )

    expected_signed_speed_difference = (
        expected_artemis_ii_speed_km_s
        - expected_artemis_i_speed_km_s
    )

    expected_absolute_speed_difference = abs(
        expected_signed_speed_difference
    )

    expected_relative_speed_difference_percent = (
        100.0
        * expected_signed_speed_difference
        / expected_artemis_i_speed_km_s
    )

    if (
        expected_signed_speed_difference
        > 0.0
    ):
        expected_speed_relationship = (
            "ARTEMIS_II_HIGHER"
        )

    elif (
        expected_signed_speed_difference
        < 0.0
    ):
        expected_speed_relationship = (
            "ARTEMIS_II_LOWER"
        )

    else:
        expected_speed_relationship = (
            "EQUAL_WITHIN_NUMERIC_PRECISION"
        )

    expected_artemis_i_duration = float(
        artemis_i_duration[
            "ei_to_splashdown_seconds"
        ]
    )

    expected_artemis_ii_duration = float(
        surface[
            "ei_elapsed_seconds"
        ]
    )

    expected_duration_difference = (
        expected_artemis_i_duration
        - expected_artemis_ii_duration
    )

    expected_duration_percent = (
        100.0
        * expected_duration_difference
        / expected_artemis_i_duration
    )

    expected_artemis_i_apogee = float(
        artemis_i_skip[
            "actual_skip_apogee_km"
        ]
    )

    expected_artemis_ii_top = float(
        rebound[
            "end"
        ][
            "altitude_km"
        ]
    )

    expected_altitude_difference = (
        expected_artemis_i_apogee
        - expected_artemis_ii_top
    )

    expected_altitude_percent = (
        100.0
        * expected_altitude_difference
        / expected_artemis_i_apogee
    )

    artemis_i = comparison.get(
        "artemis_i"
    )

    artemis_ii = comparison.get(
        "artemis_ii"
    )

    primary = comparison.get(
        "primary_comparisons"
    )

    context = comparison.get(
        "context_only"
    )

    if not isinstance(
        artemis_i,
        dict,
    ):
        fail(
            "missing Artemis I block"
        )

    if not isinstance(
        artemis_ii,
        dict,
    ):
        fail(
            "missing Artemis II block"
        )

    if not isinstance(
        primary,
        dict,
    ):
        fail(
            "missing primary comparisons"
        )

    if not isinstance(
        context,
        dict,
    ):
        fail(
            "missing context-only block"
        )

    if (
        artemis_i.get(
            "entry_classification"
        )
        != "SKIP_ENTRY"
    ):
        fail(
            "Artemis I classification changed"
        )

    if (
        artemis_ii.get(
            "nasa_entry_classification"
        )
        != artemis_ii_reference_classification
    ):
        fail(
            "Artemis II NASA classification "
            "does not match reference"
        )

    if (
        artemis_ii[
            "nasa_entry_classification"
        ]
        != "MODIFIED_TRAJECTORY_WITHOUT_SKIP_ENTRY"
    ):
        fail(
            "Artemis II must remain "
            "classified without skip entry"
        )

    if (
        artemis_ii.get(
            "nasa_public_profile_label"
        )
        != artemis_ii_public_label
    ):
        fail(
            "Artemis II public loft label changed"
        )

    if (
        artemis_ii.get(
            "missionlab_profile_label"
        )
        != (
            "DERIVED_VERTICAL_REBOUND_"
            "OR_LOFT_NOT_SKIP_ENTRY"
        )
    ):
        fail(
            "MissionLab Artemis II profile "
            "label changed"
        )

    rebound_block = (
        artemis_ii[
            "derived_vertical_rebound"
        ]
    )

    if (
        rebound_block.get(
            "explicit_nonclassification"
        )
        != "NOT_A_SKIP_ENTRY"
    ):
        fail(
            "Artemis II rebound lost "
            "no-skip guardrail"
        )

    close(
        float(
            rebound_block[
                "duration_seconds"
            ]
        ),
        float(
            rebound[
                "duration_seconds"
            ]
        ),
        1e-9,
        "rebound duration",
    )

    close(
        float(
            rebound_block[
                "altitude_recovery_km"
            ]
        ),
        float(
            rebound[
                "altitude_recovery_km"
            ]
        ),
        1e-9,
        "rebound altitude recovery",
    )

    close(
        float(
            rebound_block[
                "speed_loss_km_s"
            ]
        ),
        float(
            rebound[
                "speed_loss_km_s"
            ]
        ),
        1e-9,
        "rebound speed loss",
    )

    duration_comparison = (
        primary[
            "entry_duration"
        ]
    )

    close(
        float(
            duration_comparison[
                "artemis_i_seconds"
            ]
        ),
        expected_artemis_i_duration,
        1e-9,
        "Artemis I duration",
    )

    close(
        float(
            duration_comparison[
                "artemis_ii_seconds"
            ]
        ),
        expected_artemis_ii_duration,
        1e-9,
        "Artemis II duration",
    )

    close(
        float(
            duration_comparison[
                "artemis_ii_shorter_by_seconds"
            ]
        ),
        expected_duration_difference,
        1e-9,
        "duration difference",
    )

    close(
        float(
            duration_comparison[
                "artemis_ii_shorter_by_percent"
            ]
        ),
        expected_duration_percent,
        1e-9,
        "duration percent",
    )

    altitude_comparison = (
        primary[
            "upper_profile_landmark_altitude"
        ]
    )

    close(
        float(
            altitude_comparison[
                "artemis_i_skip_apogee_km"
            ]
        ),
        expected_artemis_i_apogee,
        1e-9,
        "Artemis I skip apogee",
    )

    close(
        float(
            altitude_comparison[
                "artemis_ii_rebound_top_km"
            ]
        ),
        expected_artemis_ii_top,
        1e-9,
        "Artemis II rebound top",
    )

    close(
        float(
            altitude_comparison[
                "artemis_ii_lower_by_km"
            ]
        ),
        expected_altitude_difference,
        1e-9,
        "upper-landmark altitude difference",
    )

    close(
        float(
            altitude_comparison[
                "artemis_ii_lower_by_percent_of_artemis_i_skip_apogee"
            ]
        ),
        expected_altitude_percent,
        1e-9,
        "upper-landmark percent difference",
    )

    speed_comparison = (
        primary[
            "entry_interface_inertial_speed"
        ]
    )

    close(
        float(
            speed_comparison[
                "artemis_i_km_s"
            ]
        ),
        expected_artemis_i_speed_km_s,
        1e-12,
        "Artemis I EI inertial speed",
    )

    close(
        float(
            speed_comparison[
                "artemis_ii_km_s"
            ]
        ),
        expected_artemis_ii_speed_km_s,
        1e-12,
        "Artemis II EI inertial speed",
    )

    close(
        float(
            speed_comparison[
                "artemis_ii_minus_artemis_i_km_s"
            ]
        ),
        expected_signed_speed_difference,
        1e-12,
        "signed EI inertial-speed difference",
    )

    close(
        float(
            speed_comparison[
                "absolute_difference_km_s"
            ]
        ),
        expected_absolute_speed_difference,
        1e-12,
        "absolute EI inertial-speed difference",
    )

    close(
        float(
            speed_comparison[
                "absolute_difference_m_s"
            ]
        ),
        (
            expected_absolute_speed_difference
            * 1000.0
        ),
        1e-9,
        "absolute EI inertial-speed difference m/s",
    )

    close(
        float(
            speed_comparison[
                "artemis_ii_relative_difference_percent"
            ]
        ),
        expected_relative_speed_difference_percent,
        1e-12,
        "EI inertial-speed relative difference",
    )

    if (
        speed_comparison.get(
            "relationship"
        )
        != expected_speed_relationship
    ):
        fail(
            "EI inertial-speed relationship "
            "classification incorrect"
        )

    if (
        expected_speed_relationship
        != "ARTEMIS_II_HIGHER"
    ):
        fail(
            "current reconstructed comparison "
            "no longer shows Artemis II slightly "
            "higher than Artemis I"
        )

    acceleration_context = (
        context[
            "artemis_i_sensed_acceleration"
        ]
    )

    close(
        float(
            acceleration_context[
                "first_peak_g"
            ]
        ),
        float(
            artemis_i_acceleration[
                "first_peak_sensed_acceleration_g"
            ]
        ),
        1e-12,
        "first sensed acceleration peak",
    )

    close(
        float(
            acceleration_context[
                "second_peak_g"
            ]
        ),
        float(
            artemis_i_acceleration[
                "second_peak_sensed_acceleration_g"
            ]
        ),
        1e-12,
        "second sensed acceleration peak",
    )

    if (
        acceleration_context.get(
            "comparison_status"
        )
        != (
            "NOT_DIRECTLY_COMPARABLE_TO_"
            "PHASE2C_KINEMATIC_G0_EQUIVALENT"
        )
    ):
        fail(
            "sensed-acceleration guardrail changed"
        )

    expected_guardrails = (
        reference[
            "interpretation_guardrails"
        ]
    )

    if (
        comparison.get(
            "interpretation_guardrails"
        )
        != expected_guardrails
    ):
        fail(
            "interpretation guardrails "
            "were not preserved exactly"
        )

    observed_figures = set(
        comparison.get(
            "figures",
            [],
        )
    )

    expected_figure_strings = {
        str(
            path.relative_to(
                ROOT
            )
        )
        for path in FIGURES
    }

    if (
        observed_figures
        != expected_figure_strings
    ):
        fail(
            "figure inventory mismatch"
        )

    for figure in FIGURES:
        if not figure.exists():
            fail(
                f"missing figure: {figure}"
            )

        text = figure.read_text(
            encoding="utf-8",
        )

        if "<svg" not in text:
            fail(
                f"invalid SVG: {figure}"
            )

        if len(
            text
        ) < 1000:
            fail(
                f"unexpectedly small SVG: {figure}"
            )

    print()
    print(
        "Phase 2F.2 Artemis Entry-Profile "
        "Comparison Validation"
    )

    print(
        "=========================================="
    )

    print()
    print(
        "Classification:"
    )

    print(
        "  Artemis I:  SKIP_ENTRY"
    )

    print(
        "  Artemis II: "
        "MODIFIED_TRAJECTORY_WITHOUT_SKIP_ENTRY"
    )

    print(
        "  Artemis II derived feature: "
        "VERTICAL REBOUND / LOFT"
    )

    print()
    print(
        "Duration comparison:"
    )

    print(
        f"  Artemis I:  "
        f"{expected_artemis_i_duration:.6f} s"
    )

    print(
        f"  Artemis II: "
        f"{expected_artemis_ii_duration:.6f} s"
    )

    print(
        f"  shorter by: "
        f"{expected_duration_difference:.6f} s"
    )

    print(
        f"  reduction:  "
        f"{expected_duration_percent:.6f}%"
    )

    print()
    print(
        "Upper-profile landmark:"
    )

    print(
        f"  Artemis I skip apogee: "
        f"{expected_artemis_i_apogee:.6f} km"
    )

    print(
        f"  Artemis II rebound top: "
        f"{expected_artemis_ii_top:.6f} km"
    )

    print(
        f"  lower by: "
        f"{expected_altitude_difference:.6f} km"
    )

    print(
        f"  lower by: "
        f"{expected_altitude_percent:.6f}%"
    )

    print()
    print(
        "Matched EI inertial speed:"
    )

    print(
        f"  Artemis I:  "
        f"{expected_artemis_i_speed_km_s:.9f} km/s"
    )

    print(
        f"  Artemis II: "
        f"{expected_artemis_ii_speed_km_s:.9f} km/s"
    )

    print(
        "  Artemis II - Artemis I:"
    )

    print(
        f"    "
        f"{expected_signed_speed_difference:+.9f} km/s"
    )

    print(
        f"    "
        f"{expected_signed_speed_difference * 1000.0:+.3f} m/s"
    )

    print(
        "  absolute difference:"
    )

    print(
        f"    "
        f"{expected_absolute_speed_difference * 1000.0:.3f} m/s"
    )

    print(
        "  relative difference:"
    )

    print(
        f"    "
        f"{expected_relative_speed_difference_percent:+.6f}%"
    )

    print(
        "  relationship:"
    )

    print(
        f"    {expected_speed_relationship}"
    )

    print()
    print(
        "Artemis II rebound:"
    )

    print(
        f"  duration: "
        f"{float(rebound['duration_seconds']):.6f} s"
    )

    print(
        f"  altitude recovery: "
        f"{float(rebound['altitude_recovery_km']):.6f} km"
    )

    print(
        f"  speed loss: "
        f"{float(rebound['speed_loss_km_s']):.6f} km/s"
    )

    print()
    print(
        "Guardrails:"
    )

    print(
        "  Artemis II skip-entry label: "
        "PROHIBITED"
    )

    print(
        "  Sensed-g vs Phase 2C "
        "kinematic-g0 comparison: PROHIBITED"
    )

    print(
        "  Trajectory-to-TPS-damage "
        "inference: PROHIBITED"
    )

    print(
        "  Point-by-point Artemis I / II "
        "trajectory claim: PROHIBITED"
    )

    print()
    print(
        "Figures checked: 3"
    )

    print()
    print(
        "OK: Artemis I / Artemis II "
        "entry-profile comparison, matched "
        "EI inertial-speed calculation, "
        "signed speed relationship, derived "
        "rebound structure, figures, and "
        "interpretation guardrails "
        "independently validated."
    )


if __name__ == "__main__":
    main()
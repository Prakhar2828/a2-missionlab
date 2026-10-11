from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

EVIDENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_descent_recovery_evidence.json"
)

TIMELINE_PATH = (
    ROOT
    / "data"
    / "processed"
    / "recovery"
    / "entry_to_recovery_operational_timeline.json"
)

PHASE2_CORRELATION_PATH = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_event_correlations.json"
)

RESULT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "recovery"
    / "splashdown_accuracy_recovery_closure.json"
)

METRICS_CSV = (
    ROOT
    / "data"
    / "processed"
    / "recovery"
    / "splashdown_accuracy_metrics.csv"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "recovery"
    / "phase4b_splashdown_accuracy_boundary.svg"
)


EXPECTED_DATASET_ID = (
    "phase4b_artemis_ii_"
    "splashdown_accuracy_recovery_closure"
)

EXPECTED_ROADMAP_KEYS = [
    "return_geometry_and_entry_timeline",
    "public_entry_events",
    "communications_blackout",
    "modeled_atmospheric_quantities_where_raw_telemetry_unavailable",
    "parachute_sequence",
    "splashdown_accuracy",
    "recovery_timeline",
    "explicit_public_data_model_output_separation",
    "phase4_overall",
]


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 4B VALIDATION FAILED: "
        f"{message}"
    )


def require(
    condition: bool,
    message: str,
):
    if not condition:
        fail(
            message
        )


def load_json(
    path: Path,
) -> dict:
    require(
        path.exists(),
        f"missing JSON file: {path}",
    )

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as f:
            return json.load(
                f
            )

    except json.JSONDecodeError as exc:
        fail(
            f"invalid JSON in {path}: {exc}"
        )

        raise


def load_csv(
    path: Path,
) -> list[dict]:
    require(
        path.exists(),
        f"missing CSV file: {path}",
    )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        return list(
            csv.DictReader(
                f
            )
        )


def bool_from_csv(
    value: str,
) -> bool:
    normalized = (
        value
        .strip()
        .lower()
    )

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    fail(
        f"invalid CSV boolean: {value!r}"
    )

    raise RuntimeError


def normalize_path(
    value: str,
) -> str:
    return value.replace(
        "\\",
        "/",
    )


def validate_identity(
    evidence: dict,
    timeline: dict,
    phase2: dict,
    result: dict,
):
    require(
        evidence.get(
            "dataset_id"
        )
        == (
            "phase4a1_artemis_ii_"
            "entry_descent_recovery_evidence"
        ),
        "Phase 4A.1 dependency mismatch",
    )

    require(
        timeline.get(
            "dataset_id"
        )
        == (
            "phase4a2_artemis_ii_"
            "entry_to_recovery_operational_timeline"
        ),
        "Phase 4A.2 dependency mismatch",
    )

    require(
        phase2.get(
            "trajectory_provenance"
        )
        == "NASA flight-derived ephemeris",
        "Phase 2 trajectory provenance mismatch",
    )

    require(
        result.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "Phase 4B dataset identity mismatch",
    )

    require(
        result.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        result.get(
            "phase"
        )
        == "4B",
        "phase identity mismatch",
    )

    require(
        result.get(
            "status"
        )
        == "PHASE4_PUBLIC_EVIDENCE_CLOSURE_COMPLETE",
        "Phase 4B status mismatch",
    )


def validate_dependencies(
    result: dict,
):
    dependencies = result[
        "dependencies"
    ]

    require(
        dependencies[
            "phase4a1"
        ]
        == (
            "phase4a1_artemis_ii_"
            "entry_descent_recovery_evidence"
        ),
        "Phase 4A.1 dependency registry mismatch",
    )

    require(
        dependencies[
            "phase4a2"
        ]
        == (
            "phase4a2_artemis_ii_"
            "entry_to_recovery_operational_timeline"
        ),
        "Phase 4A.2 dependency registry mismatch",
    )

    require(
        normalize_path(
            dependencies[
                "phase2_entry_correlations"
            ]
        )
        == (
            "data/processed/entry/"
            "entry_event_correlations.json"
        ),
        "Phase 2 correlation path mismatch",
    )


def validate_public_time_consistency(
    result: dict,
):
    assessment = result[
        "splashdown_accuracy_assessment"
    ]

    public = assessment[
        "public_report"
    ]

    consistency = assessment[
        "public_time_consistency"
    ]

    require(
        public[
            "reported_utc_minute"
        ]
        == "2026-04-11T00:07:00Z",
        "public splashdown minute mismatch",
    )

    require(
        public[
            "reported_location"
        ]
        == (
            "Pacific Ocean off the coast "
            "of San Diego"
        ),
        "public splashdown location mismatch",
    )

    require(
        consistency[
            "derived_surface_crossing_within_reported_public_minute"
        ]
        is True,
        "derived surface crossing not within public minute",
    )

    offset = consistency[
        "derived_offset_from_reported_minute_start_seconds"
    ]

    require(
        abs(
            offset
            - 8.823676
        )
        < 0.001,
        (
            "surface-crossing public-minute "
            f"offset mismatch: {offset}"
        ),
    )

    require(
        consistency[
            "classification"
        ]
        == "PUBLIC_MINUTE_CONSISTENT",
        "time-consistency classification mismatch",
    )

    require(
        consistency[
            "is_exact_event_time_error"
        ]
        is False,
        (
            "public-minute consistency diagnostic "
            "incorrectly classified as exact timing error"
        ),
    )


def validate_terminal_state(
    result: dict,
):
    state = result[
        "splashdown_accuracy_assessment"
    ][
        "phase2_derived_terminal_state"
    ]

    require(
        state[
            "classification"
        ]
        == (
            "DERIVED_SPLASHDOWN_"
            "CORRELATED_SURFACE_CROSSING"
        ),
        "terminal-state classification mismatch",
    )

    require(
        state[
            "utc"
        ]
        == "2026-04-11T00:07:08.823676Z",
        "derived surface-crossing UTC mismatch",
    )

    require(
        abs(
            state[
                "latitude_deg"
            ]
            - 32.340599
        )
        < 0.00001,
        "derived terminal latitude mismatch",
    )

    require(
        abs(
            state[
                "longitude_deg"
            ]
            - (-117.763095)
        )
        < 0.00001,
        "derived terminal longitude mismatch",
    )

    require(
        state[
            "provenance"
        ]
        == (
            "PHASE2_DERIVED_FROM_"
            "NASA_FLIGHT_DERIVED_EPHEMERIS"
        ),
        "terminal-state provenance mismatch",
    )


def validate_spatial_accuracy_boundary(
    result: dict,
):
    spatial = result[
        "splashdown_accuracy_assessment"
    ][
        "spatial_accuracy"
    ]

    require(
        spatial[
            "official_target_coordinate_available"
        ]
        is False,
        (
            "official target coordinate "
            "incorrectly marked available"
        ),
    )

    require(
        spatial[
            "official_actual_splashdown_coordinate_available"
        ]
        is False,
        (
            "official actual splashdown coordinate "
            "incorrectly marked available"
        ),
    )

    require(
        spatial[
            "official_target_to_actual_miss_distance_available"
        ]
        is False,
        (
            "official targeting miss distance "
            "incorrectly marked available"
        ),
    )

    require(
        spatial[
            "targeting_accuracy_quantifiable"
        ]
        is False,
        (
            "targeting accuracy incorrectly "
            "marked quantifiable"
        ),
    )

    require(
        spatial[
            "official_target_to_actual_miss_distance_km"
        ]
        is None,
        "fabricated target miss distance in km",
    )

    require(
        spatial[
            "official_target_to_actual_miss_distance_miles"
        ]
        is None,
        "fabricated target miss distance in miles",
    )

    require(
        spatial[
            "derived_terminal_coordinate_is_official_actual_coordinate"
        ]
        is False,
        (
            "derived terminal coordinate "
            "incorrectly promoted to official actual"
        ),
    )

    require(
        spatial[
            "derived_terminal_coordinate_is_official_target_coordinate"
        ]
        is False,
        (
            "derived terminal coordinate "
            "incorrectly promoted to official target"
        ),
    )

    require(
        spatial[
            "classification"
        ]
        == (
            "TARGETING_MISS_DISTANCE_"
            "NOT_PUBLICLY_QUANTIFIABLE"
        ),
        "spatial accuracy classification mismatch",
    )


def validate_drogue_diagnostic(
    result: dict,
):
    diagnostic = result[
        "splashdown_accuracy_assessment"
    ][
        "drogue_distance_diagnostic"
    ]

    require(
        abs(
            diagnostic[
                "reported_distance_to_splashdown_miles"
            ]
            - 0.8
        )
        < 1e-9,
        "reported drogue distance mismatch",
    )

    require(
        abs(
            diagnostic[
                "derived_surface_distance_to_terminal_miles_at_altitude_anchor"
            ]
            - 1.159
        )
        < 0.01,
        "derived drogue-to-terminal distance mismatch",
    )

    require(
        diagnostic[
            "is_targeting_miss_distance"
        ]
        is False,
        (
            "drogue-distance diagnostic "
            "incorrectly interpreted as targeting miss"
        ),
    )


def validate_recovery_closure(
    result: dict,
):
    recovery = result[
        "recovery_closure"
    ]

    crew = recovery[
        "crew_recovery"
    ]

    spacecraft = recovery[
        "spacecraft_recovery"
    ]

    separation = recovery[
        "separation"
    ]

    require(
        crew[
            "completion_event_id"
        ]
        == "A2_CREW_ABOARD_RECOVERY_SHIP",
        "crew recovery completion event mismatch",
    )

    require(
        crew[
            "completion_state"
        ]
        == "CREW_RECOVERY_AT_SHIP_COMPLETE",
        "crew recovery completion state mismatch",
    )

    require(
        crew[
            "splashdown_to_crew_aboard_ship_public_minutes"
        ]
        == 111.0,
        "crew recovery public-minute relationship mismatch",
    )

    require(
        crew[
            "exact_duration"
        ]
        is False,
        "crew recovery interval promoted to exact duration",
    )

    require(
        spacecraft[
            "completion_event_id"
        ]
        == "A2_ORION_SECURED_IN_WELL_DECK",
        "spacecraft recovery completion event mismatch",
    )

    require(
        spacecraft[
            "completion_state"
        ]
        == "SPACECRAFT_RECOVERY_AT_SHIP_COMPLETE",
        "spacecraft recovery completion state mismatch",
    )

    require(
        spacecraft[
            "splashdown_to_orion_secured_public_minutes"
        ]
        == 500.0,
        (
            "spacecraft recovery public-minute "
            "relationship mismatch"
        ),
    )

    require(
        spacecraft[
            "exact_duration"
        ]
        is False,
        (
            "spacecraft recovery interval "
            "promoted to exact duration"
        ),
    )

    require(
        separation[
            "crew_recovery_equals_spacecraft_recovery"
        ]
        is False,
        (
            "crew recovery incorrectly equated "
            "with spacecraft recovery"
        ),
    )

    require(
        separation[
            "spacecraft_recovery_equals_postflight_analysis_complete"
        ]
        is False,
        (
            "spacecraft recovery incorrectly "
            "equated with postflight analysis closure"
        ),
    )


def validate_roadmap(
    result: dict,
):
    roadmap = result[
        "roadmap_assessment"
    ]

    require(
        list(
            roadmap.keys()
        )
        == EXPECTED_ROADMAP_KEYS,
        "Phase 4 roadmap assessment key set mismatch",
    )

    require(
        roadmap[
            "return_geometry_and_entry_timeline"
        ][
            "status"
        ]
        == "COMPLETE",
        "return geometry / entry timeline incomplete",
    )

    require(
        roadmap[
            "public_entry_events"
        ][
            "status"
        ]
        == "COMPLETE",
        "public entry events incomplete",
    )

    require(
        roadmap[
            "communications_blackout"
        ][
            "status"
        ]
        == "COMPLETE",
        "communications blackout incomplete",
    )

    require(
        roadmap[
            "modeled_atmospheric_quantities_where_raw_telemetry_unavailable"
        ][
            "status"
        ]
        == "COMPLETE",
        "modeled atmospheric quantities incomplete",
    )

    require(
        roadmap[
            "parachute_sequence"
        ][
            "status"
        ]
        == "COMPLETE",
        "parachute sequence incomplete",
    )

    splash = roadmap[
        "splashdown_accuracy"
    ]

    require(
        splash[
            "status"
        ]
        == "COMPLETE_WITH_PUBLIC_EVIDENCE_BOUNDARY",
        "splashdown accuracy closure mismatch",
    )

    require(
        splash[
            "quantitative_public_minute_consistency"
        ]
        is True,
        (
            "public-minute consistency "
            "not marked complete"
        ),
    )

    require(
        splash[
            "official_target_miss_distance_quantifiable"
        ]
        is False,
        (
            "official target miss distance "
            "incorrectly marked quantifiable"
        ),
    )

    require(
        roadmap[
            "recovery_timeline"
        ][
            "status"
        ]
        == "COMPLETE",
        "recovery timeline incomplete",
    )

    require(
        roadmap[
            "explicit_public_data_model_output_separation"
        ][
            "status"
        ]
        == "COMPLETE",
        "public/model separation incomplete",
    )

    require(
        roadmap[
            "phase4_overall"
        ][
            "status"
        ]
        == (
            "COMPLETE_RELATIVE_TO_"
            "DEFENSIBLE_PUBLIC_EVIDENCE"
        ),
        "Phase 4 overall closure mismatch",
    )


def validate_boundaries(
    result: dict,
):
    boundaries = result[
        "evidence_boundaries"
    ]

    expected_keys = [
        (
            "derived_surface_crossing_equals_"
            "official_actual_splashdown_coordinate"
        ),
        (
            "derived_surface_crossing_equals_"
            "official_target_coordinate"
        ),
        (
            "public_minute_offset_equals_"
            "exact_timing_error"
        ),
        (
            "drogue_distance_difference_equals_"
            "targeting_error"
        ),
        (
            "regional_location_description_"
            "supports_precise_miss_distance"
        ),
        (
            "absence_of_public_coordinates_"
            "means_landing_was_inaccurate"
        ),
        (
            "crew_recovery_complete_equals_"
            "spacecraft_recovery_complete"
        ),
        (
            "spacecraft_recovery_complete_equals_"
            "postflight_analysis_complete"
        ),
    ]

    require(
        set(
            boundaries.keys()
        )
        == set(
            expected_keys
        ),
        "evidence-boundary registry mismatch",
    )

    for key in expected_keys:
        require(
            boundaries[
                key
            ]
            is False,
            (
                "evidence boundary expected "
                f"FALSE: {key}"
            ),
        )


def validate_csv(
    rows: list[dict],
):
    require(
        len(
            rows
        )
        == 5,
        (
            "expected 5 splashdown/recovery metrics, "
            f"found {len(rows)}"
        ),
    )

    expected_ids = [
        "splashdown_public_minute_offset",
        "drogue_reported_distance_to_splashdown",
        "drogue_derived_distance_to_terminal",
        "splashdown_to_crew_aboard_ship",
        "splashdown_to_orion_secured",
    ]

    require(
        [
            row[
                "metric_id"
            ]
            for row in rows
        ]
        == expected_ids,
        "metrics CSV row ordering mismatch",
    )

    for row in rows:
        require(
            bool_from_csv(
                row[
                    "exact_accuracy_metric"
                ]
            )
            is False,
            (
                f"{row['metric_id']} incorrectly "
                "classified as exact accuracy metric"
            ),
        )


def validate_outputs(
    result: dict,
):
    outputs = result[
        "outputs"
    ]

    require(
        normalize_path(
            outputs[
                "json"
            ]
        )
        == (
            "data/processed/recovery/"
            "splashdown_accuracy_recovery_closure.json"
        ),
        "Phase 4B JSON output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "csv"
            ]
        )
        == (
            "data/processed/recovery/"
            "splashdown_accuracy_metrics.csv"
        ),
        "Phase 4B CSV output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "figure"
            ]
        )
        == (
            "docs/assets/recovery/"
            "phase4b_splashdown_accuracy_boundary.svg"
        ),
        "Phase 4B figure output path mismatch",
    )


def validate_figure():
    require(
        FIGURE_PATH.exists(),
        f"missing Phase 4B figure: {FIGURE_PATH}",
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 4B figure is empty",
    )

    content = FIGURE_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    require(
        "<svg"
        in content,
        "Phase 4B figure is not valid SVG content",
    )


def main():
    print()
    print(
        "Phase 4B Artemis II Splashdown Accuracy "
        "and Recovery Closure Validation"
    )
    print(
        "=" * 72
    )

    evidence = load_json(
        EVIDENCE_PATH
    )

    timeline = load_json(
        TIMELINE_PATH
    )

    phase2 = load_json(
        PHASE2_CORRELATION_PATH
    )

    result = load_json(
        RESULT_PATH
    )

    rows = load_csv(
        METRICS_CSV
    )

    validate_identity(
        evidence,
        timeline,
        phase2,
        result,
    )

    print()
    print(
        "Analysis identity: PASS"
    )

    validate_dependencies(
        result
    )

    print(
        "Dependency registry: PASS"
    )

    validate_public_time_consistency(
        result
    )

    print()
    print(
        "Splashdown public-minute consistency: PASS"
    )
    print(
        "Derived surface crossing within "
        "reported minute: PASS"
    )
    print(
        "Exact timing-error prohibition: PASS"
    )

    validate_terminal_state(
        result
    )

    print()
    print(
        "Derived terminal state: PASS"
    )
    print(
        "Terminal-state provenance: PASS"
    )

    validate_spatial_accuracy_boundary(
        result
    )

    print()
    print(
        "Official target-coordinate boundary: PASS"
    )
    print(
        "Official actual-coordinate boundary: PASS"
    )
    print(
        "Target-to-actual miss-distance boundary: PASS"
    )
    print(
        "No fabricated landing-accuracy metric: PASS"
    )

    validate_drogue_diagnostic(
        result
    )

    print()
    print(
        "Drogue distance diagnostic: PASS"
    )
    print(
        "Drogue diagnostic / targeting-error "
        "boundary: PASS"
    )

    validate_recovery_closure(
        result
    )

    print()
    print(
        "Crew recovery closure: PASS"
    )
    print(
        "Spacecraft recovery closure: PASS"
    )
    print(
        "Crew / spacecraft recovery separation: PASS"
    )
    print(
        "Recovery / postflight-analysis separation: PASS"
    )

    validate_roadmap(
        result
    )

    print()
    print(
        "Return geometry / entry timeline: PASS"
    )
    print(
        "Public entry events: PASS"
    )
    print(
        "Communications blackout: PASS"
    )
    print(
        "Modeled atmospheric quantities: PASS"
    )
    print(
        "Parachute sequence: PASS"
    )
    print(
        "Splashdown accuracy boundary closure: PASS"
    )
    print(
        "Recovery timeline: PASS"
    )
    print(
        "Public / model separation: PASS"
    )
    print(
        "Phase 4 roadmap coverage: PASS"
    )

    validate_boundaries(
        result
    )

    print()
    print(
        "Phase 4 evidence-boundary policy: PASS"
    )

    validate_csv(
        rows
    )

    print(
        "Metrics CSV consistency: PASS"
    )

    validate_outputs(
        result
    )

    validate_figure()

    print(
        "Documentation figure: PASS"
    )

    print()
    print(
        "Validated splashdown assessment:"
    )
    print(
        "  public splashdown minute: "
        "2026-04-11T00:07:00Z"
    )
    print(
        "  derived surface crossing: "
        "2026-04-11T00:07:08.823676Z"
    )
    print(
        "  public-minute offset: 8.824 s"
    )
    print(
        "  exact timing error: NO"
    )

    print()
    print(
        "Validated spatial boundary:"
    )
    print(
        "  official numerical target coordinate: NO"
    )
    print(
        "  official numerical actual coordinate: NO"
    )
    print(
        "  target-to-actual miss distance: "
        "NOT PUBLICLY QUANTIFIABLE"
    )
    print(
        "  fabricated landing accuracy: NO"
    )

    print()
    print(
        "Validated recovery closure:"
    )
    print(
        "  crew aboard recovery ship: COMPLETE"
    )
    print(
        "  Orion secured in well deck: COMPLETE"
    )
    print(
        "  crew recovery == spacecraft recovery: NO"
    )
    print(
        "  spacecraft recovery == postflight analysis: NO"
    )

    print()
    print(
        "Phase 4 status:"
    )
    print(
        "  return geometry / entry timeline: COMPLETE"
    )
    print(
        "  public entry events: COMPLETE"
    )
    print(
        "  communications blackout: COMPLETE"
    )
    print(
        "  atmospheric modeling: COMPLETE"
    )
    print(
        "  parachute sequence: COMPLETE"
    )
    print(
        "  splashdown accuracy: "
        "COMPLETE WITH PUBLIC EVIDENCE BOUNDARY"
    )
    print(
        "  recovery timeline: COMPLETE"
    )
    print(
        "  public / model separation: COMPLETE"
    )

    print()
    print(
        "PHASE 4B VALIDATION PASSED"
    )
    print(
        "PHASE 4 ROADMAP COVERAGE PASSED"
    )


if __name__ == "__main__":
    main()
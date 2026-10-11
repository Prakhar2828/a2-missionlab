from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


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

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "recovery"
)

OUTPUT_JSON = (
    OUTPUT_DIR
    / "splashdown_accuracy_recovery_closure.json"
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "splashdown_accuracy_metrics.csv"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "recovery"
)

OUTPUT_FIGURE = (
    ASSET_DIR
    / "phase4b_splashdown_accuracy_boundary.svg"
)


KM_TO_MILES = 0.621371192237334


plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 4B ANALYSIS FAILED: "
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
        f"missing dependency: {path}",
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


def normalize_svg(
    path: Path,
):
    text = path.read_text(
        encoding="utf-8",
    )

    cleaned = "\n".join(
        line.rstrip(
            " \t"
        )
        for line
        in text.splitlines()
    )

    path.write_text(
        cleaned + "\n",
        encoding="utf-8",
    )


def event_index(
    evidence: dict,
) -> dict[str, dict]:
    result = {}

    for event in evidence[
        "events"
    ]:
        result[
            event[
                "event_id"
            ]
        ] = event

    return result


def timeline_index(
    timeline: dict,
) -> dict[str, dict]:
    result = {}

    for event in timeline[
        "timeline"
    ]:
        result[
            event[
                "event_id"
            ]
        ] = event

    return result


def get_phase2_surface_state(
    correlations: dict,
) -> dict:
    require(
        "splashdown"
        in correlations,
        "Phase 2 splashdown correlation missing",
    )

    splashdown = correlations[
        "splashdown"
    ]

    require(
        "derived_surface_crossing"
        in splashdown,
        (
            "Phase 2 derived surface "
            "crossing missing"
        ),
    )

    return splashdown[
        "derived_surface_crossing"
    ]


def get_drogue_diagnostic(
    correlations: dict,
) -> dict:
    require(
        "drogue_deploy"
        in correlations,
        "Phase 2 drogue correlation missing",
    )

    section = correlations[
        "drogue_deploy"
    ]

    require(
        "altitude_anchor"
        in section,
        "Phase 2 drogue altitude anchor missing",
    )

    state = section[
        "altitude_anchor"
    ]

    derived_distance_miles = (
        state[
            "surface_distance_to_terminal_km"
        ]
        * KM_TO_MILES
    )

    reported_distance_miles = (
        section[
            "reported"
        ][
            "reported_distance_to_splashdown_statute_miles"
        ]
    )

    return {
        "reported_distance_to_splashdown_miles": (
            reported_distance_miles
        ),
        "derived_surface_distance_to_terminal_miles_at_altitude_anchor": (
            derived_distance_miles
        ),
        "difference_miles": (
            derived_distance_miles
            - reported_distance_miles
        ),
        "distance_crossing_offset_from_altitude_anchor_seconds": (
            section.get(
                "distance_crossing_offset_from_altitude_anchor_seconds"
            )
        ),
        "interpretation": (
            section[
                "interpretation"
            ]
        ),
        "is_targeting_miss_distance": (
            False
        ),
    }


def determine_public_coordinate_availability(
    evidence: dict,
) -> dict:
    events = event_index(
        evidence
    )

    splash = events[
        "A2_SPLASHDOWN"
    ]

    require(
        splash[
            "exact_coordinates_public_in_curated_source"
        ]
        is False,
        (
            "evidence unexpectedly claims "
            "exact public splashdown coordinates"
        ),
    )

    return {
        "public_location_description": (
            splash[
                "reported_location"
            ]
        ),
        "official_target_coordinate_available": (
            False
        ),
        "official_actual_splashdown_coordinate_available": (
            False
        ),
        "official_target_to_actual_miss_distance_available": (
            False
        ),
        "reason": (
            "The curated NASA public record identifies "
            "the splashdown region as the Pacific Ocean "
            "off the coast of San Diego but does not "
            "provide both an official numerical target "
            "coordinate and an official numerical actual "
            "splashdown coordinate required to calculate "
            "a defensible targeting miss distance."
        ),
    }


def build_accuracy_assessment(
    evidence: dict,
    timeline: dict,
    correlations: dict,
) -> dict:
    events = event_index(
        evidence
    )

    timeline_events = timeline_index(
        timeline
    )

    splash_correlation = correlations[
        "splashdown"
    ]

    surface_state = (
        get_phase2_surface_state(
            correlations
        )
    )

    coordinate_availability = (
        determine_public_coordinate_availability(
            evidence
        )
    )

    drogue_diagnostic = (
        get_drogue_diagnostic(
            correlations
        )
    )

    require(
        splash_correlation[
            "within_reported_minute"
        ]
        is True,
        (
            "derived surface crossing does not "
            "fall within reported splashdown minute"
        ),
    )

    reported_minute_offset = (
        splash_correlation[
            "reported_minute_offset_seconds"
        ]
    )

    require(
        0.0
        <= reported_minute_offset
        < 60.0,
        (
            "surface-crossing offset lies "
            "outside public splashdown minute"
        ),
    )

    splash_timeline = timeline_events[
        "A2_SPLASHDOWN"
    ]

    require(
        splash_timeline[
            "public_utc_minute"
        ]
        == events[
            "A2_SPLASHDOWN"
        ][
            "reported_utc_minute"
        ],
        (
            "Phase 4 timeline splashdown "
            "minute mismatch"
        ),
    )

    return {
        "public_report": {
            "reported_utc_minute": (
                events[
                    "A2_SPLASHDOWN"
                ][
                    "reported_utc_minute"
                ]
            ),
            "reported_location": (
                events[
                    "A2_SPLASHDOWN"
                ][
                    "reported_location"
                ]
            ),
            "time_precision": (
                events[
                    "A2_SPLASHDOWN"
                ][
                    "time_precision"
                ]
            ),
        },
        "phase2_derived_terminal_state": {
            "classification": (
                splash_correlation[
                    "classification"
                ]
            ),
            "utc": (
                surface_state[
                    "utc"
                ]
            ),
            "latitude_deg": (
                surface_state[
                    "latitude_deg"
                ]
            ),
            "longitude_deg": (
                surface_state[
                    "longitude_deg"
                ]
            ),
            "wgs84_altitude_km": (
                surface_state[
                    "wgs84_altitude_km"
                ]
            ),
            "earth_relative_speed_km_s": (
                surface_state[
                    "earth_relative_speed_km_s"
                ]
            ),
            "surface_distance_to_terminal_km": (
                surface_state[
                    "surface_distance_to_terminal_km"
                ]
            ),
            "provenance": (
                "PHASE2_DERIVED_FROM_"
                "NASA_FLIGHT_DERIVED_EPHEMERIS"
            ),
        },
        "public_time_consistency": {
            "derived_surface_crossing_within_reported_public_minute": (
                splash_correlation[
                    "within_reported_minute"
                ]
            ),
            "derived_offset_from_reported_minute_start_seconds": (
                reported_minute_offset
            ),
            "classification": (
                "PUBLIC_MINUTE_CONSISTENT"
            ),
            "is_exact_event_time_error": (
                False
            ),
            "reason": (
                "NASA's public splashdown time is "
                "minute-resolution. The difference "
                "between the derived crossing and the "
                "start of that public minute is a "
                "consistency diagnostic, not a precise "
                "timing error."
            ),
        },
        "spatial_accuracy": {
            **coordinate_availability,
            "targeting_accuracy_quantifiable": (
                False
            ),
            "official_target_to_actual_miss_distance_km": (
                None
            ),
            "official_target_to_actual_miss_distance_miles": (
                None
            ),
            "derived_terminal_coordinate_is_official_actual_coordinate": (
                False
            ),
            "derived_terminal_coordinate_is_official_target_coordinate": (
                False
            ),
            "classification": (
                "TARGETING_MISS_DISTANCE_"
                "NOT_PUBLICLY_QUANTIFIABLE"
            ),
        },
        "drogue_distance_diagnostic": (
            drogue_diagnostic
        ),
    }


def build_recovery_closure(
    timeline: dict,
) -> dict:
    summary = timeline[
        "public_minute_duration_summary"
    ]

    events = timeline_index(
        timeline
    )

    require(
        events[
            "A2_CREW_ABOARD_RECOVERY_SHIP"
        ][
            "recovery_state"
        ]
        == "CREW_RECOVERY_AT_SHIP_COMPLETE",
        "crew recovery state is incomplete",
    )

    require(
        events[
            "A2_ORION_SECURED_IN_WELL_DECK"
        ][
            "recovery_state"
        ]
        == "SPACECRAFT_RECOVERY_AT_SHIP_COMPLETE",
        "spacecraft recovery state is incomplete",
    )

    return {
        "crew_recovery": {
            "completion_event_id": (
                "A2_CREW_ABOARD_RECOVERY_SHIP"
            ),
            "completion_state": (
                "CREW_RECOVERY_AT_SHIP_COMPLETE"
            ),
            "splashdown_to_crew_aboard_ship_public_minutes": (
                summary[
                    "splashdown_to_crew_aboard_ship_public_minutes"
                ]
            ),
            "exact_duration": (
                False
            ),
        },
        "spacecraft_recovery": {
            "completion_event_id": (
                "A2_ORION_SECURED_IN_WELL_DECK"
            ),
            "completion_state": (
                "SPACECRAFT_RECOVERY_AT_SHIP_COMPLETE"
            ),
            "splashdown_to_orion_secured_public_minutes": (
                summary[
                    "splashdown_to_orion_secured_public_minutes"
                ]
            ),
            "exact_duration": (
                False
            ),
        },
        "separation": {
            "crew_recovery_equals_spacecraft_recovery": (
                False
            ),
            "spacecraft_recovery_equals_postflight_analysis_complete": (
                False
            ),
        },
    }


def build_roadmap_assessment() -> dict:
    return {
        "return_geometry_and_entry_timeline": {
            "status": "COMPLETE",
            "primary_phases": [
                "Phase 2",
                "Phase 4A.2",
            ],
        },
        "public_entry_events": {
            "status": "COMPLETE",
            "primary_phase": "Phase 4A.1",
        },
        "communications_blackout": {
            "status": "COMPLETE",
            "primary_phases": [
                "Phase 4A.1",
                "Phase 4A.2",
            ],
        },
        "modeled_atmospheric_quantities_where_raw_telemetry_unavailable": {
            "status": "COMPLETE",
            "primary_phase": "Phase 2",
        },
        "parachute_sequence": {
            "status": "COMPLETE",
            "primary_phases": [
                "Phase 4A.1",
                "Phase 4A.2",
            ],
        },
        "splashdown_accuracy": {
            "status": (
                "COMPLETE_WITH_PUBLIC_"
                "EVIDENCE_BOUNDARY"
            ),
            "quantitative_public_minute_consistency": (
                True
            ),
            "official_target_miss_distance_quantifiable": (
                False
            ),
            "reason": (
                "The flight-derived terminal surface "
                "crossing can be checked against the "
                "NASA-reported splashdown minute. "
                "A true target-to-actual spatial miss "
                "distance cannot be computed without "
                "public numerical target and actual "
                "splashdown coordinates."
            ),
        },
        "recovery_timeline": {
            "status": "COMPLETE",
            "primary_phase": "Phase 4A.2",
        },
        "explicit_public_data_model_output_separation": {
            "status": "COMPLETE",
            "primary_phases": [
                "Phase 2",
                "Phase 4A.1",
                "Phase 4A.2",
                "Phase 4B",
            ],
        },
        "phase4_overall": {
            "status": (
                "COMPLETE_RELATIVE_TO_"
                "DEFENSIBLE_PUBLIC_EVIDENCE"
            ),
        },
    }


def write_metrics_csv(
    assessment: dict,
    recovery: dict,
):
    rows = [
        {
            "metric_id": (
                "splashdown_public_minute_offset"
            ),
            "value": (
                assessment[
                    "public_time_consistency"
                ][
                    "derived_offset_from_reported_minute_start_seconds"
                ]
            ),
            "unit": "seconds",
            "classification": (
                "CONSISTENCY_DIAGNOSTIC"
            ),
            "exact_accuracy_metric": False,
        },
        {
            "metric_id": (
                "drogue_reported_distance_to_splashdown"
            ),
            "value": (
                assessment[
                    "drogue_distance_diagnostic"
                ][
                    "reported_distance_to_splashdown_miles"
                ]
            ),
            "unit": "statute_miles",
            "classification": (
                "NASA_REPORTED_APPROXIMATE"
            ),
            "exact_accuracy_metric": False,
        },
        {
            "metric_id": (
                "drogue_derived_distance_to_terminal"
            ),
            "value": (
                assessment[
                    "drogue_distance_diagnostic"
                ][
                    "derived_surface_distance_to_terminal_miles_at_altitude_anchor"
                ]
            ),
            "unit": "statute_miles",
            "classification": (
                "MISSIONLAB_DERIVED"
            ),
            "exact_accuracy_metric": False,
        },
        {
            "metric_id": (
                "splashdown_to_crew_aboard_ship"
            ),
            "value": (
                recovery[
                    "crew_recovery"
                ][
                    "splashdown_to_crew_aboard_ship_public_minutes"
                ]
            ),
            "unit": "public_update_minutes",
            "classification": (
                "PUBLIC_MINUTE_DIFFERENCE"
            ),
            "exact_accuracy_metric": False,
        },
        {
            "metric_id": (
                "splashdown_to_orion_secured"
            ),
            "value": (
                recovery[
                    "spacecraft_recovery"
                ][
                    "splashdown_to_orion_secured_public_minutes"
                ]
            ),
            "unit": "public_update_minutes",
            "classification": (
                "PUBLIC_MINUTE_DIFFERENCE"
            ),
            "exact_accuracy_metric": False,
        },
    ]

    with OUTPUT_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "metric_id",
                "value",
                "unit",
                "classification",
                "exact_accuracy_metric",
            ],
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def build_boundary_figure(
    assessment: dict,
):
    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(
            12,
            7,
        )
    )

    ax.axis(
        "off"
    )

    ax.set_title(
        (
            "Artemis II Splashdown Accuracy — "
            "Public Evidence Boundary"
        ),
        fontsize=15,
        pad=20,
    )

    surface = assessment[
        "phase2_derived_terminal_state"
    ]

    consistency = assessment[
        "public_time_consistency"
    ]

    spatial = assessment[
        "spatial_accuracy"
    ]

    left_text = (
        "PUBLICLY / DERIVABLY SUPPORTED\n\n"
        "NASA splashdown minute\n"
        f"{assessment['public_report']['reported_utc_minute']}\n\n"
        "NASA location description\n"
        f"{assessment['public_report']['reported_location']}\n\n"
        "Phase 2 derived surface crossing\n"
        f"{surface['utc']}\n"
        f"Lat {surface['latitude_deg']:.6f} deg\n"
        f"Lon {surface['longitude_deg']:.6f} deg\n\n"
        "Derived crossing inside public minute\n"
        f"{consistency['derived_surface_crossing_within_reported_public_minute']}\n\n"
        "Offset from start of public minute\n"
        f"{consistency['derived_offset_from_reported_minute_start_seconds']:.3f} s\n"
        "(consistency diagnostic only)"
    )

    right_text = (
        "NOT PUBLICLY QUANTIFIABLE\n\n"
        "Official numerical target coordinate\n"
        "NOT AVAILABLE\n\n"
        "Official numerical actual splashdown coordinate\n"
        "NOT AVAILABLE\n\n"
        "Official target-to-actual miss distance\n"
        "NOT COMPUTABLE\n\n"
        "Derived terminal coordinate\n"
        "IS NOT claimed as official impact telemetry\n\n"
        "Classification\n"
        f"{spatial['classification']}"
    )

    ax.text(
        0.03,
        0.88,
        left_text,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={
            "boxstyle": "round",
            "alpha": 0.08,
        },
    )

    ax.text(
        0.54,
        0.88,
        right_text,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={
            "boxstyle": "round",
            "alpha": 0.08,
        },
    )

    ax.text(
        0.5,
        0.06,
        (
            "MissionLab quantifies public-event "
            "consistency where evidence allows. "
            "It does not manufacture a landing "
            "accuracy number when the required "
            "public target and actual coordinates "
            "are unavailable."
        ),
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
    )

    fig.tight_layout()

    fig.savefig(
        OUTPUT_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        OUTPUT_FIGURE
    )


def main():
    print()
    print(
        "Phase 4B Artemis II Splashdown Accuracy "
        "and Recovery Closure"
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

    correlations = load_json(
        PHASE2_CORRELATION_PATH
    )

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
        correlations.get(
            "trajectory_provenance"
        )
        == "NASA flight-derived ephemeris",
        "Phase 2 trajectory provenance mismatch",
    )

    print()
    print(
        "Dependencies:"
    )
    print(
        "  Phase 4A.1 public evidence: PASS"
    )
    print(
        "  Phase 4A.2 operational timeline: PASS"
    )
    print(
        "  Phase 2 entry correlations: PASS"
    )

    assessment = (
        build_accuracy_assessment(
            evidence,
            timeline,
            correlations,
        )
    )

    recovery = (
        build_recovery_closure(
            timeline
        )
    )

    roadmap = (
        build_roadmap_assessment()
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_metrics_csv(
        assessment,
        recovery,
    )

    build_boundary_figure(
        assessment
    )

    result = {
        "dataset_id": (
            "phase4b_artemis_ii_"
            "splashdown_accuracy_recovery_closure"
        ),
        "mission": "Artemis II",
        "phase": "4B",
        "status": (
            "PHASE4_PUBLIC_EVIDENCE_CLOSURE_COMPLETE"
        ),
        "dependencies": {
            "phase4a1": (
                evidence[
                    "dataset_id"
                ]
            ),
            "phase4a2": (
                timeline[
                    "dataset_id"
                ]
            ),
            "phase2_entry_correlations": (
                "data/processed/entry/"
                "entry_event_correlations.json"
            ),
        },
        "splashdown_accuracy_assessment": (
            assessment
        ),
        "recovery_closure": (
            recovery
        ),
        "roadmap_assessment": (
            roadmap
        ),
        "evidence_boundaries": {
            "derived_surface_crossing_equals_official_actual_splashdown_coordinate": (
                False
            ),
            "derived_surface_crossing_equals_official_target_coordinate": (
                False
            ),
            "public_minute_offset_equals_exact_timing_error": (
                False
            ),
            "drogue_distance_difference_equals_targeting_error": (
                False
            ),
            "regional_location_description_supports_precise_miss_distance": (
                False
            ),
            "absence_of_public_coordinates_means_landing_was_inaccurate": (
                False
            ),
            "crew_recovery_complete_equals_spacecraft_recovery_complete": (
                False
            ),
            "spacecraft_recovery_complete_equals_postflight_analysis_complete": (
                False
            ),
        },
        "outputs": {
            "json": str(
                OUTPUT_JSON.relative_to(
                    ROOT
                )
            ),
            "csv": str(
                OUTPUT_CSV.relative_to(
                    ROOT
                )
            ),
            "figure": str(
                OUTPUT_FIGURE.relative_to(
                    ROOT
                )
            ),
        },
    }

    with OUTPUT_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
        )

        f.write(
            "\n"
        )

    consistency = assessment[
        "public_time_consistency"
    ]

    spatial = assessment[
        "spatial_accuracy"
    ]

    drogue = assessment[
        "drogue_distance_diagnostic"
    ]

    surface = assessment[
        "phase2_derived_terminal_state"
    ]

    print()
    print(
        "Splashdown public-time consistency:"
    )
    print(
        "  derived surface crossing within "
        "NASA public splashdown minute: "
        f"{consistency['derived_surface_crossing_within_reported_public_minute']}"
    )
    print(
        "  derived crossing offset from "
        "public-minute start: "
        f"{consistency['derived_offset_from_reported_minute_start_seconds']:.3f} s"
    )
    print(
        "  exact timing-error interpretation: NO"
    )

    print()
    print(
        "Derived terminal surface state:"
    )
    print(
        f"  UTC: {surface['utc']}"
    )
    print(
        "  latitude: "
        f"{surface['latitude_deg']:.6f} deg"
    )
    print(
        "  longitude: "
        f"{surface['longitude_deg']:.6f} deg"
    )
    print(
        "  classification: "
        f"{surface['classification']}"
    )
    print(
        "  official actual splashdown coordinate: NO"
    )

    print()
    print(
        "Spatial targeting accuracy:"
    )
    print(
        "  official numerical target coordinate: "
        "NOT PUBLICLY AVAILABLE"
    )
    print(
        "  official numerical actual coordinate: "
        "NOT PUBLICLY AVAILABLE"
    )
    print(
        "  target-to-actual miss distance: "
        "NOT PUBLICLY QUANTIFIABLE"
    )
    print(
        "  targeting accuracy claimed: NO"
    )

    print()
    print(
        "Drogue-distance diagnostic:"
    )
    print(
        "  NASA reported approximate distance: "
        f"{drogue['reported_distance_to_splashdown_miles']:.3f} mi"
    )
    print(
        "  derived distance to terminal at "
        "drogue altitude anchor: "
        f"{drogue['derived_surface_distance_to_terminal_miles_at_altitude_anchor']:.3f} mi"
    )
    print(
        "  interpreted as targeting miss: NO"
    )

    print()
    print(
        "Recovery closure:"
    )
    print(
        "  crew aboard recovery ship: COMPLETE"
    )
    print(
        "  spacecraft secured in well deck: COMPLETE"
    )
    print(
        "  crew recovery == spacecraft recovery: NO"
    )
    print(
        "  spacecraft recovery == postflight analysis: NO"
    )

    print()
    print(
        "Phase 4 roadmap assessment:"
    )

    for key, item in roadmap.items():
        print(
            "  "
            + key
            + ": "
            + item[
                "status"
            ]
        )

    print()
    print(
        "Evidence boundary:"
    )
    print(
        "  derived terminal coordinate "
        "!= official actual coordinate"
    )
    print(
        "  derived terminal coordinate "
        "!= official target coordinate"
    )
    print(
        "  public-minute offset "
        "!= exact timing error"
    )
    print(
        "  drogue distance diagnostic "
        "!= targeting error"
    )
    print(
        "  regional location "
        "!= precise miss distance"
    )
    print(
        "  unavailable public coordinates "
        "!= evidence of inaccurate landing"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            OUTPUT_JSON.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            OUTPUT_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            OUTPUT_FIGURE.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 4B SPLASHDOWN ACCURACY "
        "AND RECOVERY CLOSURE COMPLETE"
    )


if __name__ == "__main__":
    main()
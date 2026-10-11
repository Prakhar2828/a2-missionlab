from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "radiation"
    / "artemis_ii_nairas_radiation_interface.json"
)

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_nairas_interface.json"
)

TRAJECTORY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "radiation"
    / "artemis_ii_nairas_trajectory_fields.csv"
)

SOURCE_TRAJECTORY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "trajectory"
    / "trajectory_with_mission_phases.csv"
)

SPACE_WEATHER_PATH = (
    ROOT
    / "data"
    / "processed"
    / "space_weather"
    / "artemis_ii_space_weather_context.json"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "radiation"
    / "phase5b_nairas_radiation_interface.svg"
)


EXPECTED_DATASET_ID = (
    "phase5b_artemis_ii_nairas_radiation_interface"
)

EXPECTED_ROW_COUNT = 3262

EXPECTED_FIELDS = [
    "date",
    "time",
    "geocentric_latitude_deg",
    "geocentric_longitude_deg",
    "altitude_km",
]

EXPECTED_START_DATE = "2026-04-02"
EXPECTED_START_TIME_PREFIX = "01:57:37"
EXPECTED_STOP_DATE = "2026-04-10"
EXPECTED_STOP_TIME_PREFIX = "23:53:16"

EXPECTED_MIN_ALTITUDE_KM = 143.951
EXPECTED_MAX_ALTITUDE_KM = 406773.436


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 5B VALIDATION FAILED: "
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


def normalize_path(
    value: str,
) -> str:
    return value.replace(
        "\\",
        "/",
    )


def validate_identity(
    summary: dict,
    reference: dict,
    space_weather: dict,
):
    require(
        summary.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "Phase 5B dataset identity mismatch",
    )

    require(
        summary.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        summary.get(
            "phase"
        )
        == "5B",
        "phase identifier mismatch",
    )

    require(
        summary.get(
            "status"
        )
        == "NAIRAS_TRAJECTORY_INTERFACE_PREPARED",
        "Phase 5B status mismatch",
    )

    require(
        reference
        == summary,
        (
            "processed and reference "
            "NAIRAS manifests differ"
        ),
    )

    require(
        space_weather.get(
            "dataset_id"
        )
        == (
            "phase5a_artemis_ii_"
            "space_weather_context"
        ),
        "Phase 5A dependency mismatch",
    )


def validate_source_trajectory(
    summary: dict,
    source_rows: list[dict],
):
    source = summary[
        "source_trajectory"
    ]

    require(
        normalize_path(
            source[
                "path"
            ]
        )
        == (
            "data/processed/trajectory/"
            "trajectory_with_mission_phases.csv"
        ),
        "source trajectory path mismatch",
    )

    require(
        source[
            "input_row_count"
        ]
        == EXPECTED_ROW_COUNT,
        "source trajectory row count mismatch",
    )

    require(
        len(
            source_rows
        )
        == EXPECTED_ROW_COUNT,
        "actual source trajectory row count mismatch",
    )

    require(
        source[
            "start_utc"
        ].startswith(
            "2026-04-02T01:57:37.084"
        ),
        "source trajectory start time mismatch",
    )

    require(
        source[
            "stop_utc"
        ].startswith(
            "2026-04-10T23:53:16.723"
        ),
        "source trajectory stop time mismatch",
    )

    require(
        source[
            "complete_launch_to_splashdown_coverage"
        ]
        is False,
        (
            "trajectory incorrectly claims "
            "launch-to-splashdown coverage"
        ),
    )

    require(
        source[
            "provenance"
        ]
        == (
            "NASA_FLIGHT_DERIVED_OEM_"
            "WITH_MISSIONLAB_DERIVED_GEOMETRY"
        ),
        "source trajectory provenance mismatch",
    )


def validate_nairas_model(
    summary: dict,
):
    model = summary[
        "nairas_model"
    ]

    require(
        model[
            "name"
        ]
        == "NAIRAS",
        "NAIRAS model name mismatch",
    )

    require(
        model[
            "version_family"
        ]
        == "3.0",
        "NAIRAS version mismatch",
    )

    require(
        model[
            "trajectory_run_supported"
        ]
        is True,
        "trajectory-run support mismatch",
    )

    require(
        model[
            "spacecraft_trajectory_supported"
        ]
        is True,
        "spacecraft trajectory support mismatch",
    )

    require(
        model[
            "required_trajectory_fields"
        ]
        == EXPECTED_FIELDS,
        "required NAIRAS field registry mismatch",
    )

    require(
        len(
            model[
                "available_dosimetric_quantities"
            ]
        )
        == 5,
        "expected 5 dosimetric quantities",
    )

    require(
        model[
            "user_selectable_aluminum_equivalent_shielding_depths"
        ]
        is True,
        "shielding-depth selection boundary mismatch",
    )


def validate_trajectory_interface(
    summary: dict,
    rows: list[dict],
):
    interface = summary[
        "trajectory_interface"
    ]

    require(
        interface[
            "output_row_count"
        ]
        == EXPECTED_ROW_COUNT,
        "output trajectory row count mismatch",
    )

    require(
        interface[
            "field_content_ready"
        ]
        is True,
        "trajectory fields not marked ready",
    )

    require(
        interface[
            "portal_specific_file_syntax_confirmed"
        ]
        is False,
        (
            "undocumented portal syntax "
            "incorrectly claimed"
        ),
    )

    require(
        len(
            rows
        )
        == EXPECTED_ROW_COUNT,
        (
            "actual NAIRAS trajectory "
            f"row count mismatch: {len(rows)}"
        ),
    )

    require(
        list(
            rows[
                0
            ].keys()
        )
        == EXPECTED_FIELDS,
        "NAIRAS trajectory CSV schema mismatch",
    )

    require(
        rows[
            0
        ][
            "date"
        ]
        == EXPECTED_START_DATE,
        "first NAIRAS trajectory date mismatch",
    )

    require(
        rows[
            0
        ][
            "time"
        ].startswith(
            EXPECTED_START_TIME_PREFIX
        ),
        "first NAIRAS trajectory time mismatch",
    )

    require(
        rows[
            -1
        ][
            "date"
        ]
        == EXPECTED_STOP_DATE,
        "final NAIRAS trajectory date mismatch",
    )

    require(
        rows[
            -1
        ][
            "time"
        ].startswith(
            EXPECTED_STOP_TIME_PREFIX
        ),
        "final NAIRAS trajectory time mismatch",
    )


def validate_coordinates(
    summary: dict,
    rows: list[dict],
):
    geometry = summary[
        "trajectory_interface"
    ][
        "coordinate_conversion"
    ]

    require(
        geometry[
            "input_frame"
        ]
        == "J2000",
        "input coordinate frame mismatch",
    )

    require(
        geometry[
            "output_frame"
        ]
        == "IAU_EARTH",
        "output coordinate frame mismatch",
    )

    min_altitude = min(
        float(
            row[
                "altitude_km"
            ]
        )
        for row
        in rows
    )

    max_altitude = max(
        float(
            row[
                "altitude_km"
            ]
        )
        for row
        in rows
    )

    require(
        abs(
            min_altitude
            - EXPECTED_MIN_ALTITUDE_KM
        )
        < 0.01,
        (
            "minimum altitude mismatch: "
            f"{min_altitude}"
        ),
    )

    require(
        abs(
            max_altitude
            - EXPECTED_MAX_ALTITUDE_KM
        )
        < 0.01,
        (
            "maximum altitude mismatch: "
            f"{max_altitude}"
        ),
    )

    require(
        abs(
            geometry[
                "minimum_altitude_km"
            ]
            - EXPECTED_MIN_ALTITUDE_KM
        )
        < 0.01,
        "manifest minimum altitude mismatch",
    )

    require(
        abs(
            geometry[
                "maximum_altitude_km"
            ]
            - EXPECTED_MAX_ALTITUDE_KM
        )
        < 0.01,
        "manifest maximum altitude mismatch",
    )

    for index, row in enumerate(
        rows,
        start=1,
    ):
        latitude = float(
            row[
                "geocentric_latitude_deg"
            ]
        )

        longitude = float(
            row[
                "geocentric_longitude_deg"
            ]
        )

        altitude = float(
            row[
                "altitude_km"
            ]
        )

        require(
            -90.0
            <= latitude
            <= 90.0,
            (
                "latitude outside valid range "
                f"at row {index}"
            ),
        )

        require(
            -180.0
            <= longitude
            <= 180.0,
            (
                "longitude outside valid range "
                f"at row {index}"
            ),
        )

        require(
            altitude
            > 0.0,
            (
                "non-positive altitude "
                f"at row {index}"
            ),
        )


def validate_shielding_boundary(
    summary: dict,
):
    shielding = summary[
        "shielding"
    ]

    require(
        shielding[
            "orion_specific_effective_aluminum_equivalent_depth_publicly_established_here"
        ]
        is False,
        (
            "Orion shielding depth "
            "incorrectly claimed"
        ),
    )

    require(
        shielding[
            "shielding_depths_g_cm2_used_by_missionlab"
        ]
        == [],
        (
            "MissionLab unexpectedly used "
            "a shielding-depth assumption"
        ),
    )

    require(
        shielding[
            "dose_calculation_performed"
        ]
        is False,
        (
            "dose calculation incorrectly "
            "claimed as performed"
        ),
    )


def validate_phase5a_relationship(
    summary: dict,
):
    relationship = summary[
        "phase5a_relationship"
    ]

    require(
        relationship[
            "space_weather_dataset_id"
        ]
        == (
            "phase5a_artemis_ii_"
            "space_weather_context"
        ),
        "Phase 5A dataset crosslink mismatch",
    )

    require(
        relationship[
            "omni_context_manually_used_as_nairas_driver"
        ]
        is False,
        (
            "OMNI context incorrectly "
            "treated as NAIRAS driver"
        ),
    )


def validate_radiation_chain(
    summary: dict,
):
    chain = summary[
        "radiation_response_chain"
    ]

    require(
        len(
            chain
        )
        == 4,
        "radiation-response chain length mismatch",
    )

    require(
        [
            item[
                "stage"
            ]
            for item
            in chain
        ]
        == [
            1,
            2,
            3,
            4,
        ],
        "radiation-response stage numbering mismatch",
    )

    require(
        [
            item[
                "name"
            ]
            for item
            in chain
        ]
        == [
            "external_radiation_environment",
            "transport_through_material",
            "absorbed_dose",
            (
                "radiation_protection_"
                "response_quantity"
            ),
        ],
        "radiation-response chain mismatch",
    )


def validate_run_boundary(
    summary: dict,
):
    run = summary[
        "nairas_run_status"
    ]

    require(
        run[
            "run_submitted_by_missionlab"
        ]
        is False,
        "NAIRAS run incorrectly claimed submitted",
    )

    require(
        run[
            "run_id"
        ]
        is None,
        "fabricated NAIRAS run ID found",
    )

    require(
        run[
            "run_output_ingested"
        ]
        is False,
        "NAIRAS output incorrectly claimed ingested",
    )

    require(
        run[
            "dose_values_reported"
        ]
        is False,
        "NAIRAS dose incorrectly reported",
    )

    require(
        run[
            "status"
        ]
        == "TRAJECTORY_PREPARED_NO_RUN_CLAIMED",
        "NAIRAS execution status mismatch",
    )


def validate_non_equivalences(
    summary: dict,
):
    items = summary[
        "critical_non_equivalences"
    ]

    require(
        len(
            items
        )
        == 8,
        (
            "expected 8 critical "
            f"non-equivalences, found {len(items)}"
        ),
    )

    for item in items:
        require(
            item[
                "equivalent"
            ]
            is False,
            (
                "critical non-equivalence "
                "incorrectly marked equivalent"
            ),
        )


def validate_roadmap(
    summary: dict,
):
    roadmap = summary[
        "roadmap_assessment"
    ]

    require(
        roadmap[
            "ingest_omni_cdaweb_quantities"
        ][
            "status"
        ]
        == "COMPLETE",
        "OMNI roadmap item incomplete",
    )

    require(
        roadmap[
            "correlate_space_weather_with_mission_clock"
        ][
            "status"
        ]
        == "COMPLETE",
        "mission-clock correlation incomplete",
    )

    require(
        roadmap[
            "prepare_artemis_ii_trajectory_for_nairas"
        ][
            "status"
        ]
        == "COMPLETE",
        "NAIRAS trajectory preparation incomplete",
    )

    require(
        roadmap[
            "ingest_export_nairas_runs_where_permitted"
        ][
            "status"
        ]
        == (
            "INTERFACE_PREPARED_"
            "NO_RUN_OUTPUT_CLAIMED"
        ),
        "NAIRAS run boundary roadmap mismatch",
    )

    require(
        roadmap[
            "make_shielding_assumptions_explicit"
        ][
            "status"
        ]
        == "COMPLETE",
        "shielding-assumption roadmap item incomplete",
    )

    require(
        roadmap[
            "make_shielding_assumptions_explicit"
        ][
            "assumption_used"
        ]
        == "NONE",
        "unexpected shielding assumption found",
    )

    require(
        roadmap[
            "external_environment_vs_astronaut_dose"
        ][
            "status"
        ]
        == "SEPARATED",
        (
            "external environment / dose "
            "boundary incomplete"
        ),
    )

    require(
        roadmap[
            "phase5_overall"
        ][
            "status"
        ]
        == (
            "COMPLETE_WITH_NAIRAS_"
            "EXECUTION_BOUNDARY"
        ),
        "Phase 5 overall status mismatch",
    )


def validate_evidence_boundaries(
    summary: dict,
):
    boundaries = summary[
        "evidence_boundaries"
    ]

    expected_false = [
        "trajectory_fields_equal_radiation_dose",
        "omni_context_equal_orion_local_radiation",
        "shielding_depth_inferred_without_source",
        "nairas_run_claimed_without_run_output",
        "model_output_equal_dosimeter_measurement",
        "external_environment_equal_absorbed_dose",
        "absorbed_dose_equal_effective_dose",
        "oem_coverage_extended_beyond_public_states",
    ]

    require(
        set(
            boundaries.keys()
        )
        == set(
            expected_false
        ),
        "evidence-boundary registry mismatch",
    )

    for key in expected_false:
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


def validate_outputs(
    summary: dict,
):
    outputs = summary[
        "outputs"
    ]

    require(
        normalize_path(
            outputs[
                "trajectory_fields_csv"
            ]
        )
        == (
            "data/processed/radiation/"
            "artemis_ii_nairas_trajectory_fields.csv"
        ),
        "trajectory output path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "processed_summary_json"
            ]
        )
        == (
            "data/processed/radiation/"
            "artemis_ii_nairas_radiation_interface.json"
        ),
        "processed summary path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "reference_manifest_json"
            ]
        )
        == (
            "data/reference/"
            "artemis_ii_nairas_interface.json"
        ),
        "reference manifest path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "figure"
            ]
        )
        == (
            "docs/assets/radiation/"
            "phase5b_nairas_radiation_interface.svg"
        ),
        "radiation figure path mismatch",
    )


def validate_figure():
    require(
        FIGURE_PATH.exists(),
        f"missing Phase 5B figure: {FIGURE_PATH}",
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 5B figure is empty",
    )

    content = FIGURE_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    require(
        "<svg"
        in content,
        "Phase 5B figure is not SVG",
    )


def main():
    print()
    print(
        "Phase 5B Artemis II Radiation Environment "
        "and NAIRAS Interface Validation"
    )
    print(
        "=" * 72
    )

    summary = load_json(
        SUMMARY_PATH
    )

    reference = load_json(
        REFERENCE_PATH
    )

    space_weather = load_json(
        SPACE_WEATHER_PATH
    )

    nairas_rows = load_csv(
        TRAJECTORY_PATH
    )

    source_rows = load_csv(
        SOURCE_TRAJECTORY_PATH
    )

    validate_identity(
        summary,
        reference,
        space_weather,
    )

    print()
    print(
        "Analysis identity: PASS"
    )
    print(
        "Processed / reference manifest consistency: PASS"
    )
    print(
        "Phase 5A dependency: PASS"
    )

    validate_source_trajectory(
        summary,
        source_rows,
    )

    print()
    print(
        "Flight-derived source trajectory: PASS"
    )
    print(
        "3,262 source states: PASS"
    )
    print(
        "Public OEM coverage boundary: PASS"
    )

    validate_nairas_model(
        summary
    )

    print()
    print(
        "NAIRAS model identity: PASS"
    )
    print(
        "Trajectory-run capability: PASS"
    )
    print(
        "Required trajectory fields: PASS"
    )
    print(
        "Dosimetric-output registry: PASS"
    )
    print(
        "User-selectable shielding input: PASS"
    )

    validate_trajectory_interface(
        summary,
        nairas_rows,
    )

    print()
    print(
        "3,262 NAIRAS trajectory points: PASS"
    )
    print(
        "NAIRAS field schema: PASS"
    )
    print(
        "Trajectory start / stop coverage: PASS"
    )
    print(
        "Portal-syntax non-claim: PASS"
    )

    validate_coordinates(
        summary,
        nairas_rows,
    )

    print()
    print(
        "J2000 -> IAU_EARTH transformation: PASS"
    )
    print(
        "Geocentric latitude range: PASS"
    )
    print(
        "Geocentric longitude range: PASS"
    )
    print(
        "Mean-radius altitude range: PASS"
    )

    validate_shielding_boundary(
        summary
    )

    print()
    print(
        "No unsupported Orion shielding depth: PASS"
    )
    print(
        "No shielding assumption used: PASS"
    )
    print(
        "No dose calculation performed: PASS"
    )

    validate_phase5a_relationship(
        summary
    )

    print()
    print(
        "Phase 5A OMNI crosslink: PASS"
    )
    print(
        "OMNI / NAIRAS-driver separation: PASS"
    )

    validate_radiation_chain(
        summary
    )

    print()
    print(
        "Radiation-response chain: PASS"
    )
    print(
        "External environment / absorbed-dose separation: PASS"
    )
    print(
        "Absorbed-dose / response-quantity separation: PASS"
    )

    validate_run_boundary(
        summary
    )

    print()
    print(
        "NAIRAS interface prepared: PASS"
    )
    print(
        "No fabricated NAIRAS run: PASS"
    )
    print(
        "No fabricated NAIRAS run ID: PASS"
    )
    print(
        "No fabricated NAIRAS dose: PASS"
    )

    validate_non_equivalences(
        summary
    )

    print()
    print(
        "8 critical non-equivalences: PASS"
    )

    validate_roadmap(
        summary
    )

    print()
    print(
        "OMNI / CDAWeb roadmap item: PASS"
    )
    print(
        "Mission-clock correlation roadmap item: PASS"
    )
    print(
        "NAIRAS trajectory preparation roadmap item: PASS"
    )
    print(
        "NAIRAS execution boundary roadmap item: PASS"
    )
    print(
        "Shielding-assumption roadmap item: PASS"
    )
    print(
        "External environment / astronaut-dose boundary: PASS"
    )
    print(
        "Phase 5 roadmap coverage: PASS"
    )

    validate_evidence_boundaries(
        summary
    )

    print()
    print(
        "Phase 5 evidence-boundary policy: PASS"
    )

    validate_outputs(
        summary
    )

    validate_figure()

    print(
        "Documentation figure: PASS"
    )

    print()
    print(
        "Validated trajectory preparation:"
    )
    print(
        "  source states: 3262"
    )
    print(
        "  NAIRAS trajectory points: 3262"
    )
    print(
        "  start: 2026-04-02T01:57:37.084Z"
    )
    print(
        "  stop: 2026-04-10T23:53:16.723Z"
    )
    print(
        "  min altitude: 143.951 km"
    )
    print(
        "  max altitude: 406,773.436 km"
    )

    print()
    print(
        "Validated NAIRAS execution boundary:"
    )
    print(
        "  trajectory interface prepared: YES"
    )
    print(
        "  shielding depth assumed: NO"
    )
    print(
        "  run submitted: NO"
    )
    print(
        "  run ID: NONE"
    )
    print(
        "  output ingested: NO"
    )
    print(
        "  dose reported: NO"
    )

    print()
    print(
        "Validated radiation boundaries:"
    )
    print(
        "  OMNI context != Orion-local radiation"
    )
    print(
        "  external environment != absorbed dose"
    )
    print(
        "  absorbed dose != dose equivalent"
    )
    print(
        "  dose equivalent != effective dose"
    )
    print(
        "  trajectory geometry != radiation dose"
    )
    print(
        "  assumed shielding != Orion shielding"
    )
    print(
        "  interface prepared != run executed"
    )
    print(
        "  model output != dosimeter measurement"
    )

    print()
    print(
        "Phase 5 status:"
    )
    print(
        "  OMNI / CDAWeb ingestion: COMPLETE"
    )
    print(
        "  mission-clock correlation: COMPLETE"
    )
    print(
        "  NAIRAS trajectory preparation: COMPLETE"
    )
    print(
        "  shielding assumptions: EXPLICIT / NONE USED"
    )
    print(
        "  external environment vs dose: SEPARATED"
    )
    print(
        "  NAIRAS execution: NOT CLAIMED"
    )
    print(
        "  overall: COMPLETE WITH NAIRAS EXECUTION BOUNDARY"
    )

    print()
    print(
        "PHASE 5B VALIDATION PASSED"
    )
    print(
        "PHASE 5 ROADMAP COVERAGE PASSED"
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MISSION_PATH = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "space_weather"
    / "artemis_ii_space_weather_context.json"
)

NORMALIZED_CSV_PATH = (
    ROOT
    / "data"
    / "processed"
    / "space_weather"
    / "omni_hro2_1min_artemis_ii.csv"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "space_weather"
    / "phase5a_space_weather_context.svg"
)


EXPECTED_DATASET_ID = (
    "phase5a_artemis_ii_space_weather_context"
)

EXPECTED_OMNI_DATASET = (
    "OMNI_HRO2_1MIN"
)

EXPECTED_PARAMETERS = [
    "Time",
    "F",
    "BX_GSE",
    "BY_GSM",
    "BZ_GSM",
    "flow_speed",
    "proton_density",
    "T",
    "Pressure",
    "E",
    "Beta",
    "Mach_num",
    "AE_INDEX",
    "SYM_H",
]

EXPECTED_ROWS = 13053

EXPECTED_EXTREMA = {
    "BZ_GSM": {
        "operation": "min",
        "value": -14.460,
        "utc": "2026-04-02T07:09:00Z",
        "met": "00:08:33:48",
    },
    "flow_speed": {
        "operation": "max",
        "value": 789.700,
        "utc": "2026-04-03T15:52:00Z",
        "met": "01:17:16:48",
    },
    "proton_density": {
        "operation": "max",
        "value": 35.880,
        "utc": "2026-04-10T07:16:00Z",
        "met": "08:08:40:48",
    },
    "Pressure": {
        "operation": "max",
        "value": 11.750,
        "utc": "2026-04-10T07:16:00Z",
        "met": "08:08:40:48",
    },
    "E": {
        "operation": "max",
        "value": 8.490,
        "utc": "2026-04-02T07:04:00Z",
        "met": "00:08:28:48",
    },
    "AE_INDEX": {
        "operation": "max",
        "value": 3266.000,
        "utc": "2026-04-03T16:47:00Z",
        "met": "01:18:11:48",
    },
    "SYM_H": {
        "operation": "min",
        "value": -104.000,
        "utc": "2026-04-02T08:41:00Z",
        "met": "00:10:05:48",
    },
}

EXPECTED_COMPLETENESS = {
    "BZ_GSM": 12438,
    "flow_speed": 7828,
    "proton_density": 7828,
    "Pressure": 7828,
    "E": 7745,
    "AE_INDEX": 13053,
    "SYM_H": 13053,
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 5A VALIDATION FAILED: "
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


def parse_utc(
    value: str,
) -> datetime:
    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
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
    mission: dict,
    result: dict,
):
    require(
        mission.get(
            "mission"
        )
        == "Artemis II",
        "mission config identity mismatch",
    )

    require(
        result.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "Phase 5A dataset identity mismatch",
    )

    require(
        result.get(
            "mission"
        )
        == "Artemis II",
        "Phase 5A mission mismatch",
    )

    require(
        result.get(
            "phase"
        )
        == "5A",
        "Phase 5A phase identifier mismatch",
    )

    require(
        result.get(
            "status"
        )
        == "MISSION_SPACE_WEATHER_CONTEXT_COMPLETE",
        "Phase 5A status mismatch",
    )


def validate_mission_window(
    result: dict,
):
    window = result[
        "mission_window"
    ]

    require(
        window[
            "launch_utc"
        ]
        == "2026-04-01T22:35:12Z",
        "launch UTC mismatch",
    )

    require(
        window[
            "splashdown_public_minute_utc"
        ]
        == "2026-04-11T00:07:00Z",
        "splashdown UTC mismatch",
    )

    require(
        window[
            "query_start_utc"
        ]
        == "2026-04-01T22:35:00Z",
        "OMNI query start mismatch",
    )

    require(
        window[
            "query_stop_utc_exclusive"
        ]
        == "2026-04-11T00:08:00Z",
        "OMNI query stop mismatch",
    )

    require(
        parse_utc(
            window[
                "launch_utc"
            ]
        )
        < parse_utc(
            window[
                "splashdown_public_minute_utc"
            ]
        ),
        "mission window ordering invalid",
    )


def validate_source(
    result: dict,
):
    source = result[
        "source"
    ]

    require(
        source[
            "publisher"
        ]
        == (
            "NASA GSFC Space Physics "
            "Data Facility"
        ),
        "NASA publisher mismatch",
    )

    require(
        source[
            "service"
        ]
        == "CDAWeb HAPI",
        "CDAWeb service mismatch",
    )

    require(
        source[
            "dataset_id"
        ]
        == EXPECTED_OMNI_DATASET,
        "OMNI dataset mismatch",
    )

    require(
        source[
            "requested_parameters"
        ]
        == EXPECTED_PARAMETERS,
        "requested parameter set mismatch",
    )

    require(
        source[
            "cadence"
        ]
        == "1 minute",
        "OMNI cadence mismatch",
    )

    require(
        (
            "cdaweb.gsfc.nasa.gov"
            in source[
                "request_url"
            ]
        ),
        "NASA CDAWeb request URL missing",
    )

    require(
        (
            "OMNI_HRO2_1MIN"
            in source[
                "request_url"
            ]
        ),
        "OMNI dataset absent from request URL",
    )


def validate_coverage(
    result: dict,
):
    coverage = result[
        "coverage"
    ]

    require(
        coverage[
            "rows"
        ]
        == EXPECTED_ROWS,
        (
            "downloaded row count mismatch: "
            f"{coverage['rows']}"
        ),
    )

    require(
        coverage[
            "expected_nominal_minute_rows"
        ]
        == EXPECTED_ROWS,
        (
            "nominal mission-minute count "
            "mismatch"
        ),
    )

    require(
        coverage[
            "first_utc"
        ]
        == "2026-04-01T22:35:00Z",
        "first OMNI timestamp mismatch",
    )

    require(
        coverage[
            "last_utc"
        ]
        == "2026-04-11T00:07:00Z",
        "last OMNI timestamp mismatch",
    )

    require(
        coverage[
            "continuous_coverage_assumed"
        ]
        is False,
        (
            "continuous coverage was "
            "incorrectly assumed"
        ),
    )


def validate_completeness(
    result: dict,
):
    completeness = result[
        "parameter_completeness"
    ]

    for (
        parameter,
        expected_valid,
    ) in EXPECTED_COMPLETENESS.items():
        require(
            parameter
            in completeness,
            (
                "missing completeness record: "
                f"{parameter}"
            ),
        )

        item = completeness[
            parameter
        ]

        require(
            item[
                "total_rows"
            ]
            == EXPECTED_ROWS,
            (
                f"{parameter} total row "
                "count mismatch"
            ),
        )

        require(
            item[
                "valid_rows"
            ]
            == expected_valid,
            (
                f"{parameter} valid row "
                f"count mismatch: "
                f"{item['valid_rows']}"
            ),
        )

        require(
            item[
                "missing_rows"
            ]
            == (
                EXPECTED_ROWS
                - expected_valid
            ),
            (
                f"{parameter} missing row "
                "count mismatch"
            ),
        )

        expected_fraction = (
            expected_valid
            / EXPECTED_ROWS
        )

        require(
            abs(
                item[
                    "valid_fraction"
                ]
                - expected_fraction
            )
            < 1e-12,
            (
                f"{parameter} valid fraction "
                "mismatch"
            ),
        )


def validate_extrema(
    result: dict,
):
    extrema = result[
        "mission_clock_extrema"
    ]

    for (
        parameter,
        expected,
    ) in EXPECTED_EXTREMA.items():
        require(
            parameter
            in extrema,
            (
                "missing extrema record: "
                f"{parameter}"
            ),
        )

        item = extrema[
            parameter
        ]

        require(
            item is not None,
            (
                "extrema unexpectedly missing: "
                f"{parameter}"
            ),
        )

        require(
            item[
                "operation"
            ]
            == expected[
                "operation"
            ],
            (
                f"{parameter} extrema "
                "operation mismatch"
            ),
        )

        require(
            abs(
                item[
                    "value"
                ]
                - expected[
                    "value"
                ]
            )
            < 0.0011,
            (
                f"{parameter} extrema value "
                f"mismatch: {item['value']}"
            ),
        )

        require(
            item[
                "utc"
            ]
            == expected[
                "utc"
            ],
            (
                f"{parameter} extrema "
                "UTC mismatch"
            ),
        )

        require(
            item[
                "met"
            ]
            == expected[
                "met"
            ],
            (
                f"{parameter} extrema "
                "MET mismatch"
            ),
        )

        require(
            item[
                "provenance"
            ]
            == (
                "MISSIONLAB_DERIVED_FROM_"
                "NASA_OMNI_HRO2_1MIN"
            ),
            (
                f"{parameter} extrema "
                "provenance mismatch"
            ),
        )


def validate_interpretation(
    result: dict,
):
    interpretation = result[
        "interpretation"
    ]

    expected_false = [
        "omni_values_are_orion_local_measurements",
        (
            "omni_values_are_spacecraft_"
            "radiation_measurements"
        ),
        "omni_values_are_astronaut_dose",
        "geomagnetic_indices_are_orion_dose",
        "extrema_are_spacecraft_anomalies",
    ]

    for key in expected_false:
        require(
            interpretation[
                key
            ]
            is False,
            (
                "interpretation boundary "
                f"expected FALSE: {key}"
            ),
        )


def validate_non_equivalences(
    result: dict,
):
    items = result[
        "critical_non_equivalences"
    ]

    require(
        len(
            items
        )
        == 5,
        (
            "expected 5 critical "
            f"non-equivalences, found {len(items)}"
        ),
    )

    expected_pairs = [
        (
            "OMNI_BOW_SHOCK_CONTEXT",
            "ORION_LOCAL_ENVIRONMENT",
        ),
        (
            "SOLAR_WIND_PARAMETERS",
            "IONIZING_RADIATION_DOSE",
        ),
        (
            "GEOMAGNETIC_ACTIVITY",
            "ASTRONAUT_EFFECTIVE_DOSE",
        ),
        (
            "MISSION_WINDOW_CORRELATION",
            "CAUSAL_SPACECRAFT_EFFECT",
        ),
        (
            "OMNI_DATA_GAP",
            "QUIET_SPACE_WEATHER",
        ),
    ]

    actual_pairs = [
        (
            item[
                "left"
            ],
            item[
                "right"
            ],
        )
        for item in items
    ]

    require(
        actual_pairs
        == expected_pairs,
        "critical non-equivalence set mismatch",
    )

    for item in items:
        require(
            item[
                "equivalent"
            ]
            is False,
            (
                "non-equivalence incorrectly "
                "marked equivalent"
            ),
        )


def validate_csv(
    rows: list[dict],
):
    require(
        len(
            rows
        )
        == EXPECTED_ROWS,
        (
            "normalized CSV row count "
            f"mismatch: {len(rows)}"
        ),
    )

    expected_columns = [
        "timestamp_utc",
        "met_seconds",
        "met",
        "F",
        "BX_GSE",
        "BY_GSM",
        "BZ_GSM",
        "flow_speed",
        "proton_density",
        "T",
        "Pressure",
        "E",
        "Beta",
        "Mach_num",
        "AE_INDEX",
        "SYM_H",
    ]

    require(
        list(
            rows[
                0
            ].keys()
        )
        == expected_columns,
        "normalized CSV schema mismatch",
    )

    require(
        rows[
            0
        ][
            "timestamp_utc"
        ]
        == "2026-04-01T22:35:00Z",
        "normalized CSV first timestamp mismatch",
    )

    require(
        rows[
            -1
        ][
            "timestamp_utc"
        ]
        == "2026-04-11T00:07:00Z",
        "normalized CSV final timestamp mismatch",
    )

    require(
        rows[
            0
        ][
            "met"
        ]
        == "-00:00:00:12",
        (
            "normalized CSV initial MET "
            "alignment mismatch"
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
                "raw_json"
            ]
        )
        == (
            "data/raw/space_weather/"
            "omni_hro2_1min_artemis_ii.json"
        ),
        "raw OMNI path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "normalized_csv"
            ]
        )
        == (
            "data/processed/space_weather/"
            "omni_hro2_1min_artemis_ii.csv"
        ),
        "normalized OMNI path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "summary_json"
            ]
        )
        == (
            "data/processed/space_weather/"
            "artemis_ii_space_weather_context.json"
        ),
        "summary JSON path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "figure"
            ]
        )
        == (
            "docs/assets/space_weather/"
            "phase5a_space_weather_context.svg"
        ),
        "space-weather figure path mismatch",
    )


def validate_figure():
    require(
        FIGURE_PATH.exists(),
        (
            "missing Phase 5A figure: "
            f"{FIGURE_PATH}"
        ),
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 5A figure is empty",
    )

    content = FIGURE_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    require(
        "<svg"
        in content,
        "Phase 5A figure is not SVG",
    )


def main():
    print()
    print(
        "Phase 5A Artemis II "
        "Mission Space-Weather Context Validation"
    )
    print(
        "=" * 72
    )

    mission = load_json(
        MISSION_PATH
    )

    result = load_json(
        SUMMARY_PATH
    )

    rows = load_csv(
        NORMALIZED_CSV_PATH
    )

    validate_identity(
        mission,
        result,
    )

    print()
    print(
        "Analysis identity: PASS"
    )

    validate_mission_window(
        result
    )

    print(
        "Mission-window alignment: PASS"
    )

    validate_source(
        result
    )

    print()
    print(
        "NASA SPDF / CDAWeb source: PASS"
    )
    print(
        "OMNI_HRO2_1MIN dataset: PASS"
    )
    print(
        "Requested parameter registry: PASS"
    )

    validate_coverage(
        result
    )

    print()
    print(
        "13,053 mission-window minute rows: PASS"
    )
    print(
        "Mission-window temporal coverage: PASS"
    )
    print(
        "No silent continuous-coverage assumption: PASS"
    )

    validate_completeness(
        result
    )

    print()
    print(
        "Bz GSM completeness: PASS"
    )
    print(
        "Solar-wind speed completeness: PASS"
    )
    print(
        "Proton-density completeness: PASS"
    )
    print(
        "Flow-pressure completeness: PASS"
    )
    print(
        "Electric-field completeness: PASS"
    )
    print(
        "AE-index completeness: PASS"
    )
    print(
        "SYM/H completeness: PASS"
    )

    validate_extrema(
        result
    )

    print()
    print(
        "Mission-clock Bz minimum: PASS"
    )
    print(
        "Mission-clock solar-wind-speed maximum: PASS"
    )
    print(
        "Mission-clock proton-density maximum: PASS"
    )
    print(
        "Mission-clock flow-pressure maximum: PASS"
    )
    print(
        "Mission-clock electric-field maximum: PASS"
    )
    print(
        "Mission-clock AE maximum: PASS"
    )
    print(
        "Mission-clock SYM/H minimum: PASS"
    )

    validate_interpretation(
        result
    )

    print()
    print(
        "Near-Earth / Orion-local boundary: PASS"
    )
    print(
        "Solar-wind / radiation-dose boundary: PASS"
    )
    print(
        "Geomagnetic-index / crew-dose boundary: PASS"
    )
    print(
        "Extrema / spacecraft-anomaly boundary: PASS"
    )

    validate_non_equivalences(
        result
    )

    print(
        "Critical non-equivalences: PASS"
    )

    validate_csv(
        rows
    )

    print()
    print(
        "Normalized CSV row count: PASS"
    )
    print(
        "Normalized CSV schema: PASS"
    )
    print(
        "UTC / MET correlation: PASS"
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
        "Validated data totals:"
    )
    print(
        "  mission-window rows: 13053"
    )
    print(
        "  BZ_GSM valid rows: 12438"
    )
    print(
        "  flow_speed valid rows: 7828"
    )
    print(
        "  proton_density valid rows: 7828"
    )
    print(
        "  Pressure valid rows: 7828"
    )
    print(
        "  E valid rows: 7745"
    )
    print(
        "  AE_INDEX valid rows: 13053"
    )
    print(
        "  SYM_H valid rows: 13053"
    )

    print()
    print(
        "Validated mission-window extrema:"
    )
    print(
        "  BZ_GSM min: -14.460 nT"
    )
    print(
        "  flow_speed max: 789.700 km/s"
    )
    print(
        "  proton_density max: 35.880 n/cc"
    )
    print(
        "  Pressure max: 11.750 nPa"
    )
    print(
        "  E max: 8.490 mV/m"
    )
    print(
        "  AE_INDEX max: 3266 nT"
    )
    print(
        "  SYM_H min: -104 nT"
    )

    print()
    print(
        "Critical evidence boundaries:"
    )
    print(
        "  OMNI bow-shock context "
        "!= Orion-local environment"
    )
    print(
        "  solar-wind parameters "
        "!= ionizing-radiation dose"
    )
    print(
        "  geomagnetic activity "
        "!= astronaut effective dose"
    )
    print(
        "  mission-window correlation "
        "!= causal spacecraft effect"
    )
    print(
        "  OMNI data gap "
        "!= quiet space weather"
    )

    print()
    print(
        "PHASE 5A VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
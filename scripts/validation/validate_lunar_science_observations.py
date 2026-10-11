from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_lunar_observation_reconstruction.json"
)

PROCESSED_PATH = (
    ROOT
    / "data"
    / "processed"
    / "lunar_science"
    / "artemis_ii_lunar_observation_reconstruction.json"
)

OBSERVATION_CSV = (
    ROOT
    / "data"
    / "processed"
    / "lunar_science"
    / "artemis_ii_lunar_observation_correlations.csv"
)

PHASE6A_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_lunar_science_archive_index.json"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "lunar_science"
    / "phase6b_lunar_observation_reconstruction.svg"
)


EXPECTED_DATASET_ID = (
    "phase6b_artemis_ii_"
    "lunar_observation_reconstruction"
)

EXPECTED_EARTH_FULL_START = (
    "2026-04-06T22:43:22.462Z"
)

EXPECTED_EARTH_FULL_STOP = (
    "2026-04-06T23:19:56.488Z"
)

EXPECTED_EARTH_FULL_DURATION_MIN = (
    36.5671
)

EXPECTED_ECLIPSE_TOTAL_START = (
    "2026-04-07T00:34:27.220Z"
)

EXPECTED_ECLIPSE_TOTAL_STOP = (
    "2026-04-07T01:28:53.125Z"
)

EXPECTED_ECLIPSE_DURATION_MIN = (
    54.43175
)

EXPECTED_OBSERVATION_IDS = [
    "A2_LUNAR_EARTHSET",
    "A2_LUNAR_EARTHRISE",
    "A2_LUNAR_TERMINATOR_VAVILOV",
    "A2_LUNAR_TERMINATOR_GENERAL",
    "A2_LUNAR_SOLAR_ECLIPSE",
    "A2_LUNAR_ECLIPSE_CORONA",
    "A2_LUNAR_IMPACT_FLASH_REPORT",
    "A2_LRO_ORIENTALE_CONTEXT",
]

EXPECTED_CSV_COLUMNS = [
    "observation_id",
    "observation_class",
    "evidence_state",
    "reported_utc",
    "reported_date",
    "time_precision",
    "target",
    "view_direction",
    "image_ids",
    "audio_records",
    "crew_remark_summary",
    "confirmed_observation",
]


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 6B VALIDATION FAILED: "
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


def observation_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "observation_id"
        ]: item
        for item
        in result[
            "observation_records"
        ]
    }


def product_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "product_id"
        ]: item
        for item
        in result[
            "selected_product_registry"
        ]
    }


def audio_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "record_id"
        ]: item
        for item
        in result[
            "audio_annotation_registry"
        ]
    }


def context_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "context_id"
        ]: item
        for item
        in result[
            "lro_context_registry"
        ]
    }


def validate_identity(
    reference: dict,
    processed: dict,
    phase6a: dict,
):
    require(
        reference
        == processed,
        (
            "reference and processed "
            "Phase 6B manifests differ"
        ),
    )

    require(
        reference.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "Phase 6B dataset identity mismatch",
    )

    require(
        reference.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        reference.get(
            "phase"
        )
        == "6B",
        "phase identity mismatch",
    )

    require(
        reference.get(
            "status"
        )
        == (
            "LUNAR_SCIENCE_OBSERVATION_"
            "RECONSTRUCTION_COMPLETE"
        ),
        "Phase 6B status mismatch",
    )

    require(
        reference[
            "dependencies"
        ][
            "phase6a_dataset_id"
        ]
        == phase6a[
            "dataset_id"
        ],
        "Phase 6A dependency mismatch",
    )

    require(
        phase6a[
            "dataset_id"
        ]
        == (
            "phase6a_artemis_ii_"
            "lunar_science_archive_index"
        ),
        "unexpected Phase 6A dataset",
    )


def validate_dependencies(
    result: dict,
):
    dependencies = result[
        "dependencies"
    ]

    require(
        normalize_path(
            dependencies[
                "flight_derived_trajectory"
            ]
        )
        == (
            "data/processed/trajectory/"
            "trajectory_with_mission_phases.csv"
        ),
        "flight-derived trajectory path mismatch",
    )

    require(
        dependencies[
            "spice_kernels"
        ]
        == [
            "naif0012.tls",
            "de440s.bsp",
            "pck00011.tpc",
        ],
        "SPICE kernel registry mismatch",
    )


def validate_product_registry(
    result: dict,
):
    products = result[
        "selected_product_registry"
    ]

    require(
        len(
            products
        )
        == 6,
        (
            "expected 6 selected products, "
            f"found {len(products)}"
        ),
    )

    ids = [
        item[
            "product_id"
        ]
        for item
        in products
    ]

    require(
        len(
            ids
        )
        == len(
            set(
                ids
            )
        ),
        "duplicate selected product IDs",
    )

    index = product_index(
        result
    )

    expected_products = {
        "art002e009288",
        "art002e021278",
        "art002e009282",
        "art002e009301",
        "015A9930.NEF",
        "019A0860.NEF",
    }

    require(
        set(
            index.keys()
        )
        == expected_products,
        "selected product registry mismatch",
    )

    require(
        index[
            "art002e009288"
        ][
            "capture_time_utc"
        ]
        == "2026-04-06T22:41:00Z",
        "Earthset product time mismatch",
    )

    require(
        index[
            "art002e021278"
        ][
            "capture_time_utc"
        ]
        == "2026-04-06T23:22:00Z",
        "Earthrise product time mismatch",
    )

    require(
        index[
            "art002e009282"
        ][
            "capture_time_utc"
        ]
        is None,
        (
            "Vavilov image unexpectedly "
            "has fabricated exact time"
        ),
    )

    require(
        index[
            "art002e009301"
        ][
            "capture_time_utc"
        ]
        is None,
        (
            "eclipse image unexpectedly "
            "has fabricated exact time"
        ),
    )


def validate_audio_annotations(
    result: dict,
):
    records = result[
        "audio_annotation_registry"
    ]

    require(
        len(
            records
        )
        == 7,
        (
            "expected 7 audio/annotation records, "
            f"found {len(records)}"
        ),
    )

    ids = [
        item[
            "record_id"
        ]
        for item
        in records
    ]

    require(
        len(
            ids
        )
        == len(
            set(
                ids
            )
        ),
        "duplicate audio/annotation IDs",
    )

    index = audio_index(
        result
    )

    require(
        "AUDIO_OBSERVING_EARTHSET"
        in index,
        "Earthset audio record missing",
    )

    require(
        "AUDIO_VAVILOV_COLOR_TERRAIN"
        in index,
        "Vavilov audio record missing",
    )

    require(
        "AUDIO_SEARCH_IMPACT_FLASH_DUST"
        in index,
        "impact-flash search audio missing",
    )

    require(
        "ANNOTATION_IMPACT_FLASHES"
        in index,
        "impact-flash annotation missing",
    )

    require(
        "ANNOTATION_CORONA_STREAMER"
        in index,
        "corona annotation missing",
    )

    impact = index[
        "ANNOTATION_IMPACT_FLASHES"
    ]

    require(
        impact[
            "reference_visualization_utc"
        ]
        == "2026-04-07T01:04:00Z",
        "impact annotation reference time mismatch",
    )

    require(
        impact[
            "reference_visualization_time_is_flash_time"
        ]
        is False,
        (
            "annotation reference time "
            "incorrectly treated as flash time"
        ),
    )

    require(
        impact[
            "postflight_confirmed_flash_count"
        ]
        == 5,
        "impact annotation flash count mismatch",
    )


def validate_earth_occultation(
    result: dict,
):
    earth = result[
        "geometry_reconstruction"
    ][
        "earth_occultation"
    ]

    require(
        earth[
            "reported_earthset_utc"
        ]
        == "2026-04-06T22:41:00Z",
        "reported Earthset time mismatch",
    )

    require(
        earth[
            "reported_earthrise_utc"
        ]
        == "2026-04-06T23:22:00Z",
        "reported Earthrise time mismatch",
    )

    require(
        earth[
            "reported_earthset_snapshot"
        ][
            "status"
        ]
        == "PARTIAL_LIMB_OVERLAP",
        (
            "Earthset geometry status "
            "is not partial limb overlap"
        ),
    )

    require(
        earth[
            "reported_earthrise_snapshot"
        ][
            "status"
        ]
        == "PARTIAL_LIMB_OVERLAP",
        (
            "Earthrise geometry status "
            "is not partial limb overlap"
        ),
    )

    full = earth[
        "full_occultation_intervals"
    ]

    require(
        len(
            full
        )
        == 1,
        (
            "expected one full Earth "
            f"occultation interval, found {len(full)}"
        ),
    )

    interval = full[
        0
    ]

    require(
        interval[
            "start_utc"
        ]
        == EXPECTED_EARTH_FULL_START,
        (
            "full Earth occultation "
            "start mismatch"
        ),
    )

    require(
        interval[
            "stop_utc"
        ]
        == EXPECTED_EARTH_FULL_STOP,
        (
            "full Earth occultation "
            "stop mismatch"
        ),
    )

    require(
        abs(
            interval[
                "duration_minutes"
            ]
            - EXPECTED_EARTH_FULL_DURATION_MIN
        )
        < 0.02,
        (
            "full Earth occultation "
            "duration mismatch"
        ),
    )

    require(
        interval[
            "provenance"
        ]
        == (
            "MISSIONLAB_DERIVED_FROM_"
            "NASA_FLIGHT_DERIVED_OEM_AND_SPICE"
        ),
        "Earth-occultation provenance mismatch",
    )

    require(
        earth[
            "reported_times_equal_derived_contact_times"
        ]
        is False,
        (
            "reported image times incorrectly "
            "equated to derived contact times"
        ),
    )


def validate_solar_eclipse(
    result: dict,
):
    eclipse = result[
        "geometry_reconstruction"
    ][
        "solar_eclipse"
    ]

    totality = eclipse[
        "totality_intervals"
    ]

    require(
        len(
            totality
        )
        == 1,
        (
            "expected one total solar-eclipse "
            f"interval, found {len(totality)}"
        ),
    )

    interval = totality[
        0
    ]

    require(
        interval[
            "start_utc"
        ]
        == EXPECTED_ECLIPSE_TOTAL_START,
        (
            "solar totality start mismatch"
        ),
    )

    require(
        interval[
            "stop_utc"
        ]
        == EXPECTED_ECLIPSE_TOTAL_STOP,
        (
            "solar totality stop mismatch"
        ),
    )

    require(
        abs(
            interval[
                "duration_minutes"
            ]
            - EXPECTED_ECLIPSE_DURATION_MIN
        )
        < 0.02,
        (
            "solar totality duration mismatch"
        ),
    )

    require(
        interval[
            "classification"
        ]
        == "TOTAL_SOLAR_ECLIPSE",
        "solar totality classification mismatch",
    )

    require(
        eclipse[
            "nasa_reported_duration"
        ][
            "description"
        ]
        == "nearly 54 minutes",
        "NASA eclipse-duration wording mismatch",
    )

    require(
        eclipse[
            "nasa_reported_duration"
        ][
            "exact"
        ]
        is False,
        (
            "NASA eclipse duration "
            "incorrectly treated as exact"
        ),
    )

    require(
        eclipse[
            "derived_totality_is_nasa_reported_duration"
        ]
        is False,
        (
            "derived totality incorrectly "
            "equated with NASA reported duration"
        ),
    )


def validate_pericynthion(
    result: dict,
):
    item = result[
        "geometry_reconstruction"
    ][
        "pericynthion"
    ]

    require(
        item[
            "utc"
        ].startswith(
            "2026-04-06T23:00:46.177"
        ),
        "pericynthion UTC mismatch",
    )

    require(
        item[
            "met"
        ]
        == "05:00:25:34",
        "pericynthion MET mismatch",
    )

    require(
        item[
            "provenance"
        ]
        == "MISSIONLAB_DERIVED_PREVIOUS_PHASE",
        "pericynthion provenance mismatch",
    )


def validate_observations(
    result: dict,
):
    records = result[
        "observation_records"
    ]

    require(
        len(
            records
        )
        == 8,
        (
            "expected 8 reconstructed observations, "
            f"found {len(records)}"
        ),
    )

    ids = [
        item[
            "observation_id"
        ]
        for item
        in records
    ]

    require(
        ids
        == EXPECTED_OBSERVATION_IDS,
        "observation registry mismatch",
    )

    index = observation_index(
        result
    )

    for item in records:
        require(
            item[
                "confirmed_observation"
            ]
            is True,
            (
                "reconstructed record not marked "
                f"confirmed: {item['observation_id']}"
            ),
        )

    require(
        index[
            "A2_LUNAR_EARTHSET"
        ][
            "geometry_status_at_reported_time"
        ]
        == "PARTIAL_LIMB_OVERLAP",
        "Earthset observation geometry mismatch",
    )

    require(
        index[
            "A2_LUNAR_EARTHRISE"
        ][
            "geometry_status_at_reported_time"
        ]
        == "PARTIAL_LIMB_OVERLAP",
        "Earthrise observation geometry mismatch",
    )

    require(
        index[
            "A2_LUNAR_TERMINATOR_VAVILOV"
        ][
            "exact_image_time_inferred"
        ]
        is False,
        (
            "Vavilov exact image time "
            "was incorrectly inferred"
        ),
    )

    eclipse = index[
        "A2_LUNAR_SOLAR_ECLIPSE"
    ]

    require(
        eclipse[
            "nasa_reported_duration"
        ]
        == "nearly 54 minutes",
        (
            "eclipse observation NASA-duration "
            "summary mismatch"
        ),
    )

    require(
        len(
            eclipse[
                "derived_totality_intervals"
            ]
        )
        == 1,
        (
            "eclipse observation missing "
            "derived totality interval"
        ),
    )


def validate_flash_reconciliation(
    result: dict,
):
    reconciliation = result[
        "impact_flash_reconciliation"
    ]

    require(
        reconciliation[
            "early_public_count"
        ]
        == 6,
        "early flash count mismatch",
    )

    require(
        reconciliation[
            "early_publication_date"
        ]
        == "2026-04-07",
        "early flash publication date mismatch",
    )

    require(
        reconciliation[
            "postflight_confirmed_count"
        ]
        == 5,
        "postflight flash count mismatch",
    )

    require(
        reconciliation[
            "postflight_publication_date"
        ]
        == "2026-10-07",
        "postflight flash publication date mismatch",
    )

    require(
        reconciliation[
            "missionlab_final_science_count"
        ]
        == 5,
        "MissionLab final flash count mismatch",
    )

    require(
        reconciliation[
            "status"
        ]
        == (
            "RESOLVED_BY_LATER_"
            "POSTFLIGHT_SCIENCE_REPORT"
        ),
        "impact-flash reconciliation status mismatch",
    )

    require(
        reconciliation[
            "early_report_erased"
        ]
        is False,
        (
            "early six-flash report "
            "was incorrectly erased"
        ),
    )

    observation = observation_index(
        result
    )[
        "A2_LUNAR_IMPACT_FLASH_REPORT"
    ]

    require(
        observation[
            "source_evolution"
        ][
            "early_reported_count"
        ]
        == 6,
        "observation early flash count mismatch",
    )

    require(
        observation[
            "source_evolution"
        ][
            "postflight_reported_count"
        ]
        == 5,
        "observation postflight flash count mismatch",
    )

    require(
        observation[
            "source_evolution"
        ][
            "missionlab_final_count"
        ]
        == 5,
        "observation final flash count mismatch",
    )

    require(
        observation[
            "reference_annotation_utc_is_flash_time"
        ]
        is False,
        (
            "annotation reference time incorrectly "
            "treated as individual flash time"
        ),
    )


def validate_eclipse_reconciliation(
    result: dict,
):
    reconciliation = result[
        "eclipse_interpretation_reconciliation"
    ]

    require(
        reconciliation[
            "early_public_status"
        ]
        == "HALO_UNDER_INVESTIGATION",
        "early eclipse interpretation mismatch",
    )

    require(
        reconciliation[
            "postflight_status"
        ]
        == (
            "CORONAL_STRUCTURE_AND_"
            "ZODIACAL_LIGHT_REPORTED"
        ),
        "postflight eclipse interpretation mismatch",
    )

    require(
        reconciliation[
            "status"
        ]
        == (
            "RESOLVED_BY_LATER_"
            "POSTFLIGHT_SCIENCE_REPORT"
        ),
        "eclipse reconciliation status mismatch",
    )

    require(
        reconciliation[
            "early_uncertainty_erased"
        ]
        is False,
        (
            "early eclipse uncertainty "
            "was incorrectly erased"
        ),
    )

    observation = observation_index(
        result
    )[
        "A2_LUNAR_ECLIPSE_CORONA"
    ]

    require(
        observation[
            "source_evolution"
        ][
            "early_status"
        ]
        == "HALO_UNDER_INVESTIGATION",
        (
            "corona observation early "
            "status mismatch"
        ),
    )

    require(
        observation[
            "source_evolution"
        ][
            "postflight_status"
        ]
        == (
            "CORONAL_STRUCTURE_AND_"
            "ZODIACAL_LIGHT_REPORTED"
        ),
        (
            "corona observation postflight "
            "status mismatch"
        ),
    )


def validate_lro_context(
    result: dict,
):
    contexts = result[
        "lro_context_registry"
    ]

    require(
        len(
            contexts
        )
        == 3,
        (
            "expected 3 LRO/target context "
            f"records, found {len(contexts)}"
        ),
    )

    index = context_index(
        result
    )

    require(
        set(
            index.keys()
        )
        == {
            "LRO_CONTEXT_ORIENTALE",
            "LRO_CONTEXT_HERTZSPRUNG",
            "TARGET_CONTEXT_VAVILOV",
        },
        "LRO/target context registry mismatch",
    )

    orientale = index[
        "LRO_CONTEXT_ORIENTALE"
    ]

    instruments = [
        item[
            "instrument"
        ]
        for item
        in orientale[
            "products"
        ]
    ]

    require(
        "LROC WAC"
        in instruments,
        "Orientale LROC WAC context missing",
    )

    require(
        "LOLA"
        in instruments,
        "Orientale LOLA context missing",
    )

    require(
        "Diviner"
        in instruments,
        "Orientale Diviner context missing",
    )

    hertzsprung = index[
        "LRO_CONTEXT_HERTZSPRUNG"
    ]

    require(
        hertzsprung[
            "products"
        ][
            0
        ][
            "product_id"
        ]
        == "M112421089RE",
        "Hertzsprung LROC NAC product mismatch",
    )

    vavilov = index[
        "TARGET_CONTEXT_VAVILOV"
    ]

    require(
        abs(
            vavilov[
                "center_latitude_deg"
            ]
            - (
                -0.87
            )
        )
        < 0.001,
        "Vavilov latitude mismatch",
    )

    require(
        abs(
            vavilov[
                "center_longitude_deg"
            ]
            - (
                -138.77
            )
        )
        < 0.001,
        "Vavilov longitude mismatch",
    )

    require(
        abs(
            vavilov[
                "diameter_km"
            ]
            - 98.22
        )
        < 0.001,
        "Vavilov diameter mismatch",
    )


def validate_csv(
    rows: list[dict],
):
    require(
        len(
            rows
        )
        == 8,
        (
            "observation CSV expected 8 rows, "
            f"found {len(rows)}"
        ),
    )

    require(
        list(
            rows[
                0
            ].keys()
        )
        == EXPECTED_CSV_COLUMNS,
        "observation CSV schema mismatch",
    )

    ids = [
        row[
            "observation_id"
        ]
        for row
        in rows
    ]

    require(
        ids
        == EXPECTED_OBSERVATION_IDS,
        "observation CSV record ordering mismatch",
    )

    for row in rows:
        require(
            row[
                "confirmed_observation"
            ].lower()
            == "true",
            (
                "observation CSV contains "
                "unconfirmed record"
            ),
        )


def validate_roadmap(
    result: dict,
):
    roadmap = result[
        "roadmap_assessment"
    ]

    require(
        roadmap[
            "index_pds_crew_imagery_metadata"
        ]
        == (
            "COMPLETE_AT_COLLECTION_AND_"
            "SELECTED_SCIENCE_PRODUCT_LEVEL"
        ),
        "crew-imagery roadmap status mismatch",
    )

    require(
        roadmap[
            "index_pds_orion_imagery_metadata"
        ]
        == (
            "COMPLETE_AT_COLLECTION_AND_"
            "SELECTED_SCIENCE_PRODUCT_LEVEL"
        ),
        "Orion-imagery roadmap status mismatch",
    )

    require(
        roadmap[
            "index_mission_audio_transcripts_annotations"
        ]
        == (
            "COMPLETE_AT_COLLECTION_AND_"
            "SELECTED_OBSERVATION_LEVEL"
        ),
        "audio/transcript roadmap status mismatch",
    )

    require(
        roadmap[
            "connect_time_view_image_remark_target"
        ]
        == (
            "COMPLETE_FOR_RECONSTRUCTED_"
            "SCIENCE_OBSERVATIONS"
        ),
        "observation-linkage roadmap status mismatch",
    )

    require(
        roadmap[
            "integrate_public_lro_context"
        ]
        == "COMPLETE_FOR_SELECTED_TARGETS",
        "LRO context roadmap status mismatch",
    )

    for key in [
        "reconstruct_impact_flash_observations",
        "reconstruct_terminator_observations",
        "reconstruct_eclipse_corona_observations",
        "reconstruct_earth_imagery_analysis",
    ]:
        require(
            roadmap[
                key
            ]
            == "COMPLETE",
            f"{key} is not complete",
        )

    require(
        roadmap[
            "phase6_overall"
        ]
        == (
            "COMPLETE_RELATIVE_TO_"
            "DEFENSIBLE_PUBLIC_POSTFLIGHT_EVIDENCE"
        ),
        "Phase 6 overall roadmap status mismatch",
    )


def validate_non_equivalences(
    result: dict,
):
    items = result[
        "critical_non_equivalences"
    ]

    expected_pairs = [
        (
            "REPORTED_IMAGE_TIME",
            "DERIVED_GEOMETRIC_CONTACT_TIME",
        ),
        (
            "IMAGE_CAPTURE_TIME",
            "CREW_REMARK_TIME",
        ),
        (
            "TARGETING_PLAN_OPPORTUNITY",
            "CONFIRMED_OBSERVATION",
        ),
        (
            "REFERENCE_ANNOTATION_TIME",
            "INDIVIDUAL_IMPACT_FLASH_TIME",
        ),
        (
            "EARLY_SIX_FLASH_REPORT",
            "POSTFLIGHT_FIVE_FLASH_RESULT",
        ),
        (
            "EARLY_HALO_UNCERTAINTY",
            "POSTFLIGHT_CORONAL_INTERPRETATION",
        ),
        (
            "LRO_CONTEXT_PRODUCT",
            "ARTEMIS_II_CREW_IMAGE",
        ),
        (
            "MISSIONLAB_GEOMETRY",
            "ONBOARD_ORION_TELEMETRY",
        ),
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

    actual_pairs = [
        (
            item[
                "left"
            ],
            item[
                "right"
            ],
        )
        for item
        in items
    ]

    require(
        actual_pairs
        == expected_pairs,
        "critical non-equivalence registry mismatch",
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


def validate_outputs(
    result: dict,
):
    outputs = result[
        "outputs"
    ]

    require(
        normalize_path(
            outputs[
                "reference_json"
            ]
        )
        == (
            "data/reference/"
            "artemis_ii_lunar_observation_reconstruction.json"
        ),
        "reference JSON path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "processed_json"
            ]
        )
        == (
            "data/processed/lunar_science/"
            "artemis_ii_lunar_observation_reconstruction.json"
        ),
        "processed JSON path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "observation_csv"
            ]
        )
        == (
            "data/processed/lunar_science/"
            "artemis_ii_lunar_observation_correlations.csv"
        ),
        "observation CSV path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "figure"
            ]
        )
        == (
            "docs/assets/lunar_science/"
            "phase6b_lunar_observation_reconstruction.svg"
        ),
        "figure output path mismatch",
    )


def validate_figure():
    require(
        FIGURE_PATH.exists(),
        f"missing Phase 6B figure: {FIGURE_PATH}",
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 6B figure is empty",
    )

    content = FIGURE_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    require(
        "<svg"
        in content,
        "Phase 6B figure is not SVG",
    )


def main():
    print()
    print(
        "Phase 6B Artemis II Lunar Observation "
        "Reconstruction Validation"
    )
    print(
        "=" * 72
    )

    reference = load_json(
        REFERENCE_PATH
    )

    processed = load_json(
        PROCESSED_PATH
    )

    phase6a = load_json(
        PHASE6A_PATH
    )

    observation_rows = load_csv(
        OBSERVATION_CSV
    )

    validate_identity(
        reference,
        processed,
        phase6a,
    )

    print()
    print(
        "Analysis identity: PASS"
    )
    print(
        "Reference / processed manifest consistency: PASS"
    )
    print(
        "Phase 6A dependency: PASS"
    )

    validate_dependencies(
        reference
    )

    print()
    print(
        "Flight-derived trajectory dependency: PASS"
    )
    print(
        "SPICE kernel registry: PASS"
    )

    validate_product_registry(
        reference
    )

    print()
    print(
        "6 selected image products: PASS"
    )
    print(
        "Earthset image/time linkage: PASS"
    )
    print(
        "Earthrise image/time linkage: PASS"
    )
    print(
        "Vavilov exact-time non-inference: PASS"
    )
    print(
        "Eclipse exact-time non-inference: PASS"
    )

    validate_audio_annotations(
        reference
    )

    print()
    print(
        "7 audio / annotation records: PASS"
    )
    print(
        "Earthset audio linkage: PASS"
    )
    print(
        "Vavilov audio linkage: PASS"
    )
    print(
        "Impact-flash audio linkage: PASS"
    )
    print(
        "Impact-flash annotation linkage: PASS"
    )
    print(
        "Corona annotation linkage: PASS"
    )
    print(
        "Annotation-time / flash-time boundary: PASS"
    )

    validate_earth_occultation(
        reference
    )

    print()
    print(
        "Earthset partial-limb geometry: PASS"
    )
    print(
        "Earthrise partial-limb geometry: PASS"
    )
    print(
        "Full Earth-occultation interval: PASS"
    )
    print(
        "Earth-occultation duration: PASS"
    )
    print(
        "Reported-time / contact-time separation: PASS"
    )

    validate_solar_eclipse(
        reference
    )

    print()
    print(
        "Total solar-eclipse interval: PASS"
    )
    print(
        "54.43-minute derived totality: PASS"
    )
    print(
        "NASA nearly-54-minute comparison: PASS"
    )
    print(
        "Derived-geometry / NASA-report separation: PASS"
    )

    validate_pericynthion(
        reference
    )

    print()
    print(
        "Pericynthion crosslink: PASS"
    )

    validate_observations(
        reference
    )

    print()
    print(
        "8 reconstructed observation records: PASS"
    )
    print(
        "Earth imagery reconstruction: PASS"
    )
    print(
        "Terminator reconstruction: PASS"
    )
    print(
        "Eclipse reconstruction: PASS"
    )
    print(
        "LRO-context observation linkage: PASS"
    )

    validate_flash_reconciliation(
        reference
    )

    print()
    print(
        "Early six-flash report preserved: PASS"
    )
    print(
        "Postflight five-flash result: PASS"
    )
    print(
        "Impact-flash source reconciliation: PASS"
    )
    print(
        "No fabricated individual flash times: PASS"
    )

    validate_eclipse_reconciliation(
        reference
    )

    print()
    print(
        "Early halo uncertainty preserved: PASS"
    )
    print(
        "Postflight coronal interpretation: PASS"
    )
    print(
        "Eclipse interpretation reconciliation: PASS"
    )

    validate_lro_context(
        reference
    )

    print()
    print(
        "3 LRO / target context records: PASS"
    )
    print(
        "Orientale LROC / LOLA / Diviner context: PASS"
    )
    print(
        "Hertzsprung LROC NAC context: PASS"
    )
    print(
        "Vavilov target coordinates: PASS"
    )

    validate_csv(
        observation_rows
    )

    print()
    print(
        "Observation correlation CSV: PASS"
    )
    print(
        "Observation CSV schema: PASS"
    )

    validate_roadmap(
        reference
    )

    print()
    print(
        "Crew imagery roadmap item: PASS"
    )
    print(
        "Orion imagery roadmap item: PASS"
    )
    print(
        "Audio / transcript / annotation roadmap item: PASS"
    )
    print(
        "Time / view / image / remark / target linkage: PASS"
    )
    print(
        "LRO context roadmap item: PASS"
    )
    print(
        "Impact-flash roadmap item: PASS"
    )
    print(
        "Terminator roadmap item: PASS"
    )
    print(
        "Eclipse / corona roadmap item: PASS"
    )
    print(
        "Earth-imagery roadmap item: PASS"
    )
    print(
        "Phase 6 roadmap coverage: PASS"
    )

    validate_non_equivalences(
        reference
    )

    print()
    print(
        "8 critical non-equivalences: PASS"
    )
    print(
        "Image-time / contact-time boundary: PASS"
    )
    print(
        "Image-time / remark-time boundary: PASS"
    )
    print(
        "Opportunity / observation boundary: PASS"
    )
    print(
        "Annotation-time / flash-time boundary: PASS"
    )
    print(
        "Six-flash / five-flash source-evolution boundary: PASS"
    )
    print(
        "Halo-uncertainty / postflight-interpretation boundary: PASS"
    )
    print(
        "LRO-context / Artemis-image boundary: PASS"
    )
    print(
        "Derived-geometry / onboard-telemetry boundary: PASS"
    )

    validate_outputs(
        reference
    )

    validate_figure()

    print()
    print(
        "Documentation figure: PASS"
    )

    print()
    print(
        "Validated Earth geometry:"
    )
    print(
        "  NASA Earthset: "
        "2026-04-06T22:41:00Z"
    )
    print(
        "  Earthset state: PARTIAL_LIMB_OVERLAP"
    )
    print(
        "  full occultation start: "
        "2026-04-06T22:43:22.462Z"
    )
    print(
        "  full occultation stop: "
        "2026-04-06T23:19:56.488Z"
    )
    print(
        "  full occultation duration: "
        "36.57 min"
    )
    print(
        "  NASA Earthrise: "
        "2026-04-06T23:22:00Z"
    )
    print(
        "  Earthrise state: PARTIAL_LIMB_OVERLAP"
    )

    print()
    print(
        "Validated eclipse geometry:"
    )
    print(
        "  totality start: "
        "2026-04-07T00:34:27.220Z"
    )
    print(
        "  totality stop: "
        "2026-04-07T01:28:53.125Z"
    )
    print(
        "  derived duration: 54.43 min"
    )
    print(
        "  NASA description: nearly 54 minutes"
    )
    print(
        "  derived geometry == telemetry: NO"
    )

    print()
    print(
        "Validated science reconciliation:"
    )
    print(
        "  Apr 7 impact-flash report: 6"
    )
    print(
        "  Oct 7 postflight result: 5"
    )
    print(
        "  MissionLab final science result: 5"
    )
    print(
        "  early report preserved: YES"
    )
    print(
        "  individual flash times fabricated: NO"
    )
    print(
        "  early eclipse halo status: "
        "UNDER INVESTIGATION"
    )
    print(
        "  postflight interpretation: "
        "CORONAL STRUCTURE + ZODIACAL LIGHT"
    )
    print(
        "  early uncertainty preserved: YES"
    )

    print()
    print(
        "Validated selected target context:"
    )
    print(
        "  Orientale: LROC / LOLA / Diviner"
    )
    print(
        "  Hertzsprung: LROC NAC M112421089RE"
    )
    print(
        "  Vavilov: -0.87 deg, "
        "-138.77 deg, 98.22 km"
    )

    print()
    print(
        "Phase 6 status:"
    )
    print(
        "  PDS imagery indexing: COMPLETE"
    )
    print(
        "  audio / transcript / annotation indexing: COMPLETE"
    )
    print(
        "  observation linkage: COMPLETE"
    )
    print(
        "  LRO context integration: COMPLETE"
    )
    print(
        "  impact-flash reconstruction: COMPLETE"
    )
    print(
        "  terminator reconstruction: COMPLETE"
    )
    print(
        "  eclipse / corona reconstruction: COMPLETE"
    )
    print(
        "  Earth imagery reconstruction: COMPLETE"
    )
    print(
        "  overall: COMPLETE RELATIVE TO "
        "DEFENSIBLE PUBLIC POSTFLIGHT EVIDENCE"
    )

    print()
    print(
        "PHASE 6B VALIDATION PASSED"
    )
    print(
        "PHASE 6 ROADMAP COVERAGE PASSED"
    )


if __name__ == "__main__":
    main()
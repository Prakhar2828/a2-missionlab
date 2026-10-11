from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_lunar_science_archive_index.json"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "lunar_science"
    / "artemis_ii_lunar_science_archive_summary.json"
)

COLLECTION_CSV = (
    ROOT
    / "data"
    / "processed"
    / "lunar_science"
    / "artemis_ii_lunar_science_collections.csv"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "lunar_science"
    / "phase6a_lunar_science_archive_index.svg"
)


EXPECTED_DATASET_ID = (
    "phase6a_artemis_ii_"
    "lunar_science_archive_index"
)

EXPECTED_BUNDLE_COUNTS = {
    "crew_camera": 4,
    "orion_camera": 3,
    "mission_audio": 5,
}

EXPECTED_BUNDLE_IDS = [
    "crew_camera",
    "orion_camera",
    "mission_audio",
]

EXPECTED_OBSERVATION_IDS = [
    "A2_LUNAR_EARTHSET",
    "A2_LUNAR_EARTHRISE",
    "A2_LUNAR_TERMINATOR_VAVILOV",
    "A2_LUNAR_SOLAR_ECLIPSE",
    "A2_LUNAR_IMPACT_FLASH_REPORT",
]

EXPECTED_COLLECTION_COLUMNS = [
    "bundle_id",
    "bundle_pds_identifier",
    "bundle_doi",
    "bundle_start_utc",
    "bundle_stop_utc",
    "collection_id",
    "collection_pds_identifier",
    "collection_type",
    "content_class",
    "collection_name",
]


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 6A VALIDATION FAILED: "
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


def source_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "source_id"
        ]: item
        for item
        in result[
            "source_registry"
        ]
    }


def bundle_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "bundle_id"
        ]: item
        for item
        in result[
            "pds_bundles"
        ]
    }


def observation_index(
    result: dict,
) -> dict[str, dict]:
    return {
        item[
            "observation_id"
        ]: item
        for item
        in result[
            "observation_evidence"
        ]
    }


def validate_identity(
    reference: dict,
    summary: dict,
):
    require(
        reference
        == summary,
        (
            "reference and processed "
            "archive manifests differ"
        ),
    )

    require(
        reference.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "Phase 6A dataset identity mismatch",
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
        == "6A",
        "phase identity mismatch",
    )

    require(
        reference.get(
            "status"
        )
        == (
            "PUBLIC_LUNAR_SCIENCE_"
            "ARCHIVE_INDEXED"
        ),
        "Phase 6A status mismatch",
    )


def validate_release_summary(
    result: dict,
):
    release = result[
        "release_summary"
    ]

    require(
        release[
            "release_date"
        ]
        == "2026-10-07",
        "lunar-science release date mismatch",
    )

    volume = release[
        "reported_total_data_volume_gb"
    ]

    require(
        volume[
            "operator"
        ]
        == ">",
        "archive-volume operator mismatch",
    )

    require(
        volume[
            "value"
        ]
        == 800,
        "archive-volume value mismatch",
    )

    require(
        volume[
            "exact"
        ]
        is False,
        (
            "archive-volume summary incorrectly "
            "treated as exact"
        ),
    )

    media = release[
        "reported_full_resolution_image_video_count"
    ]

    require(
        media[
            "operator"
        ]
        == ">",
        "media-count operator mismatch",
    )

    require(
        media[
            "value"
        ]
        == 11000,
        "media-count value mismatch",
    )

    require(
        media[
            "exact"
        ]
        is False,
        (
            "media-count summary incorrectly "
            "treated as exact"
        ),
    )

    require(
        release[
            "reported_science_audio_hours"
        ][
            "value"
        ]
        == 8.5,
        "science-audio duration mismatch",
    )

    require(
        release[
            "reported_science_audio_hours"
        ][
            "exact"
        ]
        is False,
        (
            "science-audio summary incorrectly "
            "treated as exact"
        ),
    )

    expected_includes = {
        "crew_handheld_imagery",
        "orion_spacecraft_imagery",
        "video",
        "crew_science_audio",
        "transcripts",
        "crew_annotations",
    }

    require(
        set(
            release[
                "includes"
            ]
        )
        == expected_includes,
        "archive-content registry mismatch",
    )


def validate_sources(
    result: dict,
):
    sources = result[
        "source_registry"
    ]

    require(
        len(
            sources
        )
        == 8,
        (
            "expected 8 source records, "
            f"found {len(sources)}"
        ),
    )

    ids = [
        item[
            "source_id"
        ]
        for item
        in sources
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
        "duplicate source IDs",
    )

    index = source_index(
        result
    )

    required_sources = [
        (
            "NASA_ARTEMIS_II_LUNAR_"
            "SCIENCE_DATA_RELEASE_2026_10_07"
        ),
        (
            "NASA_ARTEMIS_II_CREW_MOON_"
            "PHOTO_ANNOTATIONS_2026_10_07"
        ),
        (
            "NASA_ARTEMIS_II_OFFICIAL_"
            "MOON_FLYBY_PHOTOS_2026_04_07"
        ),
        (
            "NASA_ARTEMIS_II_LUNAR_"
            "TARGETING_PLAN"
        ),
        "PDS_ARTEMIS2_CREW_CAMERA_BUNDLE",
        "PDS_ARTEMIS2_ORION_CAMERA_BUNDLE",
        "PDS_ARTEMIS2_MISSION_AUDIO_BUNDLE",
        (
            "NASA_ARTEMIS_II_PRELIMINARY_"
            "LUNAR_SCIENCE_REPORT_PAGE"
        ),
    ]

    require(
        set(
            index.keys()
        )
        == set(
            required_sources
        ),
        "source registry identity mismatch",
    )

    for source_id in [
        "PDS_ARTEMIS2_CREW_CAMERA_BUNDLE",
        "PDS_ARTEMIS2_ORION_CAMERA_BUNDLE",
        "PDS_ARTEMIS2_MISSION_AUDIO_BUNDLE",
    ]:
        require(
            index[
                source_id
            ][
                "publisher"
            ]
            == (
                "NASA Planetary Data System"
            ),
            (
                "PDS source publisher mismatch: "
                f"{source_id}"
            ),
        )

        require(
            index[
                source_id
            ][
                "source_type"
            ]
            == "PDS_BUNDLE",
            (
                "PDS source type mismatch: "
                f"{source_id}"
            ),
        )


def validate_bundles(
    result: dict,
):
    bundles = result[
        "pds_bundles"
    ]

    require(
        len(
            bundles
        )
        == 3,
        (
            "expected 3 PDS bundles, "
            f"found {len(bundles)}"
        ),
    )

    ids = [
        bundle[
            "bundle_id"
        ]
        for bundle
        in bundles
    ]

    require(
        ids
        == EXPECTED_BUNDLE_IDS,
        "PDS bundle ordering or identity mismatch",
    )

    index = bundle_index(
        result
    )

    expected_metadata = {
        "crew_camera": {
            "doi": "10.17189/x52v-tb80",
            "identifier": (
                "urn:nasa:pds:"
                "artemis2_crew_camera::1.0"
            ),
            "start": (
                "2026-04-02T11:35:16.960Z"
            ),
            "stop": (
                "2026-04-09T04:28:31.990Z"
            ),
        },
        "orion_camera": {
            "doi": "10.17189/hzev-nq50",
            "identifier": (
                "urn:nasa:pds:"
                "artemis2_orion_camera::1.0"
            ),
            "start": (
                "2026-04-02T12:49:07.000Z"
            ),
            "stop": (
                "2026-04-10T08:13:18.000Z"
            ),
        },
        "mission_audio": {
            "doi": "10.17189/4a29-dz64",
            "identifier": (
                "urn:nasa:pds:"
                "artemis2_mission_audio::1.0"
            ),
            "start": (
                "2026-04-05T05:36:35.000Z"
            ),
            "stop": (
                "2026-04-07T11:59:59.000Z"
            ),
        },
    }

    for (
        bundle_id,
        expected,
    ) in expected_metadata.items():
        bundle = index[
            bundle_id
        ]

        require(
            bundle[
                "doi"
            ]
            == expected[
                "doi"
            ],
            (
                f"{bundle_id} DOI mismatch"
            ),
        )

        require(
            bundle[
                "pds_identifier"
            ]
            == expected[
                "identifier"
            ],
            (
                f"{bundle_id} PDS "
                "identifier mismatch"
            ),
        )

        require(
            bundle[
                "start_utc"
            ]
            == expected[
                "start"
            ],
            (
                f"{bundle_id} start time mismatch"
            ),
        )

        require(
            bundle[
                "stop_utc"
            ]
            == expected[
                "stop"
            ],
            (
                f"{bundle_id} stop time mismatch"
            ),
        )

        require(
            len(
                bundle[
                    "collections"
                ]
            )
            == EXPECTED_BUNDLE_COUNTS[
                bundle_id
            ],
            (
                f"{bundle_id} collection "
                "count mismatch"
            ),
        )

        require(
            set(
                bundle[
                    "targets"
                ]
            )
            == {
                "Earth",
                "Moon",
            },
            (
                f"{bundle_id} target "
                "registry mismatch"
            ),
        )


def validate_collection_summary(
    result: dict,
    rows: list[dict],
):
    summary = result[
        "collection_index_summary"
    ]

    require(
        summary[
            "bundle_count"
        ]
        == 3,
        "bundle summary count mismatch",
    )

    require(
        summary[
            "collection_count"
        ]
        == 12,
        "collection summary count mismatch",
    )

    require(
        summary[
            "bundle_ids"
        ]
        == EXPECTED_BUNDLE_IDS,
        "bundle summary ID mismatch",
    )

    require(
        summary[
            "individual_media_downloaded"
        ]
        is False,
        (
            "Phase 6A incorrectly claims "
            "media download"
        ),
    )

    require(
        len(
            rows
        )
        == 12,
        (
            "collection CSV expected 12 rows, "
            f"found {len(rows)}"
        ),
    )

    require(
        list(
            rows[
                0
            ].keys()
        )
        == EXPECTED_COLLECTION_COLUMNS,
        "collection CSV schema mismatch",
    )

    csv_ids = [
        row[
            "collection_id"
        ]
        for row
        in rows
    ]

    require(
        len(
            csv_ids
        )
        == len(
            set(
                csv_ids
            )
        ),
        "duplicate collection IDs in CSV",
    )

    actual_bundle_counts = {}

    for row in rows:
        bundle_id = row[
            "bundle_id"
        ]

        actual_bundle_counts[
            bundle_id
        ] = (
            actual_bundle_counts.get(
                bundle_id,
                0,
            )
            + 1
        )

    require(
        actual_bundle_counts
        == EXPECTED_BUNDLE_COUNTS,
        "collection CSV bundle counts mismatch",
    )


def validate_earth_imagery(
    observations: dict[str, dict],
):
    earthset = observations[
        "A2_LUNAR_EARTHSET"
    ]

    require(
        earthset[
            "observation_class"
        ]
        == "EARTH_IMAGERY",
        "Earthset observation class mismatch",
    )

    require(
        earthset[
            "reported_utc"
        ]
        == "2026-04-06T22:41:00Z",
        "Earthset time mismatch",
    )

    require(
        earthset[
            "reported_image_id"
        ]
        == "art002e009288",
        "Earthset image ID mismatch",
    )

    require(
        earthset[
            "evidence_state"
        ]
        == "NASA_REPORTED",
        "Earthset evidence state mismatch",
    )

    earthrise = observations[
        "A2_LUNAR_EARTHRISE"
    ]

    require(
        earthrise[
            "observation_class"
        ]
        == "EARTH_IMAGERY",
        "Earthrise observation class mismatch",
    )

    require(
        earthrise[
            "reported_utc"
        ]
        == "2026-04-06T23:22:00Z",
        "Earthrise time mismatch",
    )

    require(
        earthrise[
            "reported_image_id"
        ]
        == "art002e021278",
        "Earthrise image ID mismatch",
    )

    require(
        earthrise[
            "evidence_state"
        ]
        == "NASA_REPORTED",
        "Earthrise evidence state mismatch",
    )


def validate_terminator(
    observations: dict[str, dict],
):
    item = observations[
        "A2_LUNAR_TERMINATOR_VAVILOV"
    ]

    require(
        item[
            "observation_class"
        ]
        == "TERMINATOR_OBSERVATION",
        "terminator observation class mismatch",
    )

    require(
        item[
            "reported_utc"
        ]
        is None,
        (
            "terminator observation unexpectedly "
            "has fabricated exact UTC"
        ),
    )

    require(
        item[
            "reported_date"
        ]
        == "2026-04-06",
        "terminator observation date mismatch",
    )

    require(
        item[
            "time_precision"
        ]
        == "DATE_ONLY_IN_CURATED_SOURCE",
        "terminator timing boundary mismatch",
    )

    require(
        item[
            "reported_image_id"
        ]
        == "art002e009282",
        "terminator image ID mismatch",
    )

    require(
        (
            "Vavilov"
            in item[
                "target"
            ]
        ),
        "Vavilov target missing",
    )


def validate_eclipse(
    observations: dict[str, dict],
):
    item = observations[
        "A2_LUNAR_SOLAR_ECLIPSE"
    ]

    require(
        item[
            "observation_class"
        ]
        == "ECLIPSE_CORONA_OBSERVATION",
        "eclipse observation class mismatch",
    )

    require(
        item[
            "reported_utc"
        ]
        is None,
        (
            "eclipse unexpectedly has "
            "fabricated exact UTC"
        ),
    )

    require(
        item[
            "reported_totality_duration_minutes"
        ]
        == 54,
        "reported eclipse duration mismatch",
    )

    require(
        item[
            "duration_qualifier"
        ]
        == "NEARLY",
        "eclipse duration qualifier mismatch",
    )

    require(
        item[
            "reported_image_id"
        ]
        == "art002e009301",
        "eclipse image ID mismatch",
    )

    require(
        (
            "under investigation"
            in item[
                "interpretation_boundary"
            ]
        ),
        "eclipse interpretation boundary missing",
    )


def validate_impact_flash(
    observations: dict[str, dict],
):
    item = observations[
        "A2_LUNAR_IMPACT_FLASH_REPORT"
    ]

    require(
        item[
            "observation_class"
        ]
        == "IMPACT_FLASH_OBSERVATION",
        "impact-flash observation class mismatch",
    )

    require(
        item[
            "reported_utc"
        ]
        is None,
        (
            "impact-flash record unexpectedly "
            "has fabricated individual timing"
        ),
    )

    require(
        item[
            "evidence_state"
        ]
        == (
            "SOURCE_EVOLUTION_REQUIRES_"
            "RECONCILIATION"
        ),
        "impact-flash evidence state mismatch",
    )

    evidence = item[
        "count_evidence"
    ]

    require(
        len(
            evidence
        )
        == 2,
        "expected two flash-count source records",
    )

    require(
        evidence[
            0
        ][
            "reported_count"
        ]
        == 6,
        "early impact-flash count mismatch",
    )

    require(
        evidence[
            0
        ][
            "publication_date"
        ]
        == "2026-04-07",
        "early impact-flash report date mismatch",
    )

    require(
        evidence[
            0
        ][
            "status"
        ]
        == "EARLY_PUBLIC_REPORT",
        "early impact-flash status mismatch",
    )

    require(
        evidence[
            1
        ][
            "reported_count"
        ]
        == 5,
        "postflight impact-flash count mismatch",
    )

    require(
        evidence[
            1
        ][
            "publication_date"
        ]
        == "2026-10-07",
        "postflight impact-flash report date mismatch",
    )

    require(
        evidence[
            1
        ][
            "status"
        ]
        == "POSTFLIGHT_DATA_RELEASE_REPORT",
        "postflight impact-flash status mismatch",
    )

    require(
        item[
            "missionlab_selected_count"
        ]
        is None,
        (
            "MissionLab silently selected "
            "an impact-flash count"
        ),
    )


def validate_observations(
    result: dict,
):
    items = result[
        "observation_evidence"
    ]

    require(
        len(
            items
        )
        == 5,
        (
            "expected 5 observation records, "
            f"found {len(items)}"
        ),
    )

    ids = [
        item[
            "observation_id"
        ]
        for item
        in items
    ]

    require(
        ids
        == EXPECTED_OBSERVATION_IDS,
        "observation evidence registry mismatch",
    )

    observations = observation_index(
        result
    )

    validate_earth_imagery(
        observations
    )

    validate_terminator(
        observations
    )

    validate_eclipse(
        observations
    )

    validate_impact_flash(
        observations
    )


def validate_roadmap_mapping(
    result: dict,
):
    roadmap = result[
        "roadmap_mapping"
    ]

    require(
        roadmap[
            "index_pds_crew_imagery_metadata"
        ]
        == (
            "COLLECTION_LEVEL_COMPLETE_"
            "PRODUCT_LEVEL_PENDING"
        ),
        "crew imagery roadmap state mismatch",
    )

    require(
        roadmap[
            "index_pds_orion_imagery_metadata"
        ]
        == (
            "COLLECTION_LEVEL_COMPLETE_"
            "PRODUCT_LEVEL_PENDING"
        ),
        "Orion imagery roadmap state mismatch",
    )

    require(
        roadmap[
            "index_audio_transcripts_annotations"
        ]
        == (
            "COLLECTION_LEVEL_COMPLETE_"
            "PRODUCT_LEVEL_PENDING"
        ),
        "audio/transcript roadmap state mismatch",
    )

    require(
        roadmap[
            "connect_observation_time_view_image_remark_target"
        ]
        == (
            "PARTIAL_OBSERVATION_EVIDENCE_"
            "SEE_PHASE6B"
        ),
        "observation-correlation roadmap state mismatch",
    )

    for key in [
        "integrate_lro_context",
        "reconstruct_impact_flash",
        "reconstruct_terminator",
        "reconstruct_eclipse_corona",
        "reconstruct_earth_imagery",
    ]:
        require(
            roadmap[
                key
            ]
            == "PENDING_PHASE6B",
            (
                f"{key} incorrectly marked "
                "complete in Phase 6A"
            ),
        )


def validate_non_equivalences(
    result: dict,
):
    items = result[
        "critical_non_equivalences"
    ]

    expected_pairs = [
        (
            "NASA_RELEASE_SUMMARY_COUNT",
            "EXACT_PDS_PRODUCT_COUNT",
        ),
        (
            "PDS_COLLECTION_INDEX",
            "FULL_MEDIA_DOWNLOAD",
        ),
        (
            "IMAGE_CAPTURE_TIME",
            "CREW_REMARK_TIME",
        ),
        (
            "OBSERVATION_OPPORTUNITY",
            "CONFIRMED_OBSERVATION",
        ),
        (
            "EARLY_PUBLIC_FLASH_COUNT",
            "FINAL_RECONCILED_FLASH_COUNT",
        ),
        (
            "VISIBLE_ECLIPSE_HALO",
            "CONFIRMED_SOLAR_CORONA_ONLY",
        ),
    ]

    require(
        len(
            items
        )
        == 6,
        (
            "expected 6 critical "
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
            "artemis_ii_lunar_science_archive_index.json"
        ),
        "reference JSON path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "processed_summary_json"
            ]
        )
        == (
            "data/processed/lunar_science/"
            "artemis_ii_lunar_science_archive_summary.json"
        ),
        "processed summary path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "collection_csv"
            ]
        )
        == (
            "data/processed/lunar_science/"
            "artemis_ii_lunar_science_collections.csv"
        ),
        "collection CSV path mismatch",
    )

    require(
        normalize_path(
            outputs[
                "figure"
            ]
        )
        == (
            "docs/assets/lunar_science/"
            "phase6a_lunar_science_archive_index.svg"
        ),
        "figure path mismatch",
    )


def validate_figure():
    require(
        FIGURE_PATH.exists(),
        f"missing Phase 6A figure: {FIGURE_PATH}",
    )

    require(
        FIGURE_PATH.stat().st_size
        > 0,
        "Phase 6A figure is empty",
    )

    content = FIGURE_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    require(
        "<svg"
        in content,
        "Phase 6A figure is not SVG",
    )


def main():
    print()
    print(
        "Phase 6A Artemis II Lunar Science "
        "Archive and Evidence Index Validation"
    )
    print(
        "=" * 72
    )

    reference = load_json(
        REFERENCE_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    collection_rows = load_csv(
        COLLECTION_CSV
    )

    validate_identity(
        reference,
        summary,
    )

    print()
    print(
        "Analysis identity: PASS"
    )
    print(
        "Reference / processed manifest consistency: PASS"
    )

    validate_release_summary(
        reference
    )

    print()
    print(
        "October 7 public release summary: PASS"
    )
    print(
        "800+ GB non-exact boundary: PASS"
    )
    print(
        "11,000+ image/video non-exact boundary: PASS"
    )
    print(
        "8.5-hour science-audio summary: PASS"
    )

    validate_sources(
        reference
    )

    print()
    print(
        "8-source registry: PASS"
    )
    print(
        "NASA source identities: PASS"
    )
    print(
        "PDS source identities: PASS"
    )

    validate_bundles(
        reference
    )

    print()
    print(
        "3 PDS bundles: PASS"
    )
    print(
        "Crew-camera bundle metadata: PASS"
    )
    print(
        "Orion-camera bundle metadata: PASS"
    )
    print(
        "Mission-audio bundle metadata: PASS"
    )

    validate_collection_summary(
        reference,
        collection_rows,
    )

    print()
    print(
        "12 PDS collections: PASS"
    )
    print(
        "Crew-camera 4-collection set: PASS"
    )
    print(
        "Orion-camera 3-collection set: PASS"
    )
    print(
        "Mission-audio 5-collection set: PASS"
    )
    print(
        "Collection CSV schema: PASS"
    )
    print(
        "Collection ID uniqueness: PASS"
    )
    print(
        "No full-media-download claim: PASS"
    )

    validate_observations(
        reference
    )

    print()
    print(
        "5 observation evidence records: PASS"
    )
    print(
        "Earthset evidence: PASS"
    )
    print(
        "Earthrise evidence: PASS"
    )
    print(
        "Terminator / Vavilov evidence: PASS"
    )
    print(
        "Solar eclipse evidence: PASS"
    )
    print(
        "Impact-flash evidence: PASS"
    )

    observations = observation_index(
        reference
    )

    flash = observations[
        "A2_LUNAR_IMPACT_FLASH_REPORT"
    ]

    print()
    print(
        "Impact-flash source evolution:"
    )
    print(
        "  Apr 7 early public report: "
        f"{flash['count_evidence'][0]['reported_count']}"
    )
    print(
        "  Oct 7 postflight report: "
        f"{flash['count_evidence'][1]['reported_count']}"
    )
    print(
        "  MissionLab selected count: NONE"
    )
    print(
        "  silent reconciliation prohibition: PASS"
    )

    validate_roadmap_mapping(
        reference
    )

    print()
    print(
        "Collection-level crew imagery indexing: PASS"
    )
    print(
        "Collection-level Orion imagery indexing: PASS"
    )
    print(
        "Collection-level audio/transcript indexing: PASS"
    )
    print(
        "Phase 6B product-level handoff: PASS"
    )
    print(
        "LRO context correctly left to 6B: PASS"
    )
    print(
        "Observation reconstruction correctly left to 6B: PASS"
    )

    validate_non_equivalences(
        reference
    )

    print()
    print(
        "6 critical non-equivalences: PASS"
    )
    print(
        "Summary-count / product-count boundary: PASS"
    )
    print(
        "Archive-index / full-download boundary: PASS"
    )
    print(
        "Image-time / remark-time boundary: PASS"
    )
    print(
        "Opportunity / confirmed-observation boundary: PASS"
    )
    print(
        "Flash-count reconciliation boundary: PASS"
    )
    print(
        "Eclipse-halo / corona-only boundary: PASS"
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
        "Validated archive totals:"
    )
    print(
        "  source records: 8"
    )
    print(
        "  PDS bundles: 3"
    )
    print(
        "  PDS collections: 12"
    )
    print(
        "  crew-camera collections: 4"
    )
    print(
        "  Orion-camera collections: 3"
    )
    print(
        "  mission-audio collections: 5"
    )
    print(
        "  observation evidence records: 5"
    )

    print()
    print(
        "Validated public observations:"
    )
    print(
        "  Earthset: "
        "2026-04-06T22:41:00Z"
    )
    print(
        "  Earthrise: "
        "2026-04-06T23:22:00Z"
    )
    print(
        "  terminator / Vavilov: INDEXED"
    )
    print(
        "  eclipse: nearly 54 minutes"
    )
    print(
        "  impact flashes: SOURCE EVOLUTION PRESERVED"
    )

    print()
    print(
        "Phase 6A status:"
    )
    print(
        "  authoritative source registry: COMPLETE"
    )
    print(
        "  PDS bundle registry: COMPLETE"
    )
    print(
        "  PDS collection registry: COMPLETE"
    )
    print(
        "  initial observation evidence: COMPLETE"
    )
    print(
        "  product-level correlation: PENDING 6B"
    )
    print(
        "  LRO context: PENDING 6B"
    )
    print(
        "  observation reconstruction: PENDING 6B"
    )

    print()
    print(
        "PHASE 6A VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
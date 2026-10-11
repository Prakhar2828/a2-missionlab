from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "lunar_science"
)

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_lunar_science_archive_index.json"
)

COLLECTION_CSV = (
    OUTPUT_DIR
    / "artemis_ii_lunar_science_collections.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR
    / "artemis_ii_lunar_science_archive_summary.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "lunar_science"
)

FIGURE_PATH = (
    ASSET_DIR
    / "phase6a_lunar_science_archive_index.svg"
)


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
        "PHASE 6A ANALYSIS FAILED: "
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


def source_registry() -> list[dict]:
    return [
        {
            "source_id": (
                "NASA_ARTEMIS_II_LUNAR_"
                "SCIENCE_DATA_RELEASE_2026_10_07"
            ),
            "publisher": "NASA",
            "source_type": "NASA_RELEASE",
            "url": (
                "https://www.nasa.gov/blogs/missions/"
                "2026/10/07/nasa-releases-artemis-ii-"
                "lunar-science-data-images/"
            ),
            "role": (
                "Postflight release announcing the "
                "full public Artemis II lunar-science "
                "dataset and high-level archive totals."
            ),
        },
        {
            "source_id": (
                "NASA_ARTEMIS_II_CREW_MOON_"
                "PHOTO_ANNOTATIONS_2026_10_07"
            ),
            "publisher": "NASA",
            "source_type": "NASA_IMAGE_ARTICLE",
            "url": (
                "https://www.nasa.gov/image-article/"
                "artemis-ii-crew-moon-photo-annotations/"
            ),
            "role": (
                "Postflight public evidence for crew "
                "annotations and impact-flash observations."
            ),
        },
        {
            "source_id": (
                "NASA_ARTEMIS_II_OFFICIAL_"
                "MOON_FLYBY_PHOTOS_2026_04_07"
            ),
            "publisher": "NASA",
            "source_type": "NASA_RELEASE",
            "url": (
                "https://www.nasa.gov/news-release/"
                "nasas-artemis-ii-crew-beams-official-"
                "moon-flyby-photos-to-earth/"
            ),
            "role": (
                "Early public release of lunar-flyby "
                "imagery, Earthset/Earthrise, eclipse, "
                "terminator, and impact-flash reporting."
            ),
        },
        {
            "source_id": (
                "NASA_ARTEMIS_II_LUNAR_"
                "TARGETING_PLAN"
            ),
            "publisher": "NASA Science",
            "source_type": "NASA_SCIENCE_RESOURCE",
            "url": (
                "https://science.nasa.gov/resource/"
                "artemis-ii-lunar-targeting-plan/"
            ),
            "role": (
                "Public description of the crew lunar "
                "observation targeting plan and night-side "
                "science opportunities."
            ),
        },
        {
            "source_id": (
                "PDS_ARTEMIS2_CREW_CAMERA_BUNDLE"
            ),
            "publisher": (
                "NASA Planetary Data System"
            ),
            "source_type": "PDS_BUNDLE",
            "url": (
                "https://pds.nasa.gov/ds-view/pds/"
                "viewBundle.jsp?identifier="
                "urn:nasa:pds:artemis2_crew_camera"
                "&version=1.0"
            ),
            "role": (
                "Authoritative crew-camera bundle "
                "metadata and collection registry."
            ),
        },
        {
            "source_id": (
                "PDS_ARTEMIS2_ORION_CAMERA_BUNDLE"
            ),
            "publisher": (
                "NASA Planetary Data System"
            ),
            "source_type": "PDS_BUNDLE",
            "url": (
                "https://pds.nasa.gov/ds-view/pds/"
                "viewBundle.jsp?identifier="
                "urn:nasa:pds:artemis2_orion_camera"
                "&version=1.0"
            ),
            "role": (
                "Authoritative Orion-camera bundle "
                "metadata and collection registry."
            ),
        },
        {
            "source_id": (
                "PDS_ARTEMIS2_MISSION_AUDIO_BUNDLE"
            ),
            "publisher": (
                "NASA Planetary Data System"
            ),
            "source_type": "PDS_BUNDLE",
            "url": (
                "https://pds.nasa.gov/ds-view/pds/"
                "viewBundle.jsp?identifier="
                "urn:nasa:pds:artemis2_mission_audio"
                "&version=1.0"
            ),
            "role": (
                "Authoritative mission audio, transcript, "
                "voice-loop, and crew-annotation registry."
            ),
        },
        {
            "source_id": (
                "NASA_ARTEMIS_II_PRELIMINARY_"
                "LUNAR_SCIENCE_REPORT_PAGE"
            ),
            "publisher": "NASA Science",
            "source_type": "NASA_SCIENCE_REPORT_INDEX",
            "url": (
                "https://science.nasa.gov/feature/"
                "artemis-ii-preliminary-lunar-science-report/"
            ),
            "role": (
                "Public landing page for the preliminary "
                "science report, science operations report, "
                "data user guide, audio, and imagery."
            ),
        },
    ]


def bundle_registry() -> list[dict]:
    return [
        {
            "bundle_id": "crew_camera",
            "pds_identifier": (
                "urn:nasa:pds:"
                "artemis2_crew_camera::1.0"
            ),
            "name": (
                "Artemis 2 Crew Camera "
                "Product Bundle"
            ),
            "doi": "10.17189/x52v-tb80",
            "start_utc": (
                "2026-04-02T11:35:16.960Z"
            ),
            "stop_utc": (
                "2026-04-09T04:28:31.990Z"
            ),
            "targets": [
                "Earth",
                "Moon",
            ],
            "instruments": [
                "Nikon D5 camera",
                "Nikon Z9 camera",
            ],
            "collections": [
                {
                    "collection_id": (
                        "crew_camera_native_source"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_crew_camera:"
                        "data_source::1.0"
                    ),
                    "collection_type": "DATA",
                    "name": (
                        "Artemis 2 Crew Camera "
                        "Native Source Product Collection"
                    ),
                    "content_class": (
                        "native_source_imagery"
                    ),
                },
                {
                    "collection_id": (
                        "crew_camera_raw"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_crew_camera:"
                        "data_raw::1.0"
                    ),
                    "collection_type": "DATA",
                    "name": (
                        "Artemis 2 Crew Camera "
                        "Raw Product Collection"
                    ),
                    "content_class": (
                        "raw_imagery"
                    ),
                },
                {
                    "collection_id": (
                        "crew_camera_processed"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_crew_camera:"
                        "data_processed::1.0"
                    ),
                    "collection_type": "DATA",
                    "name": (
                        "Artemis 2 Crew Camera "
                        "Nikon Processed Product Collection"
                    ),
                    "content_class": (
                        "processed_imagery"
                    ),
                },
                {
                    "collection_id": (
                        "crew_camera_browse"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_crew_camera:"
                        "browse::1.0"
                    ),
                    "collection_type": "BROWSE",
                    "name": (
                        "Artemis 2 Crew Camera "
                        "Browse Product Collection"
                    ),
                    "content_class": (
                        "browse_imagery"
                    ),
                },
            ],
        },
        {
            "bundle_id": "orion_camera",
            "pds_identifier": (
                "urn:nasa:pds:"
                "artemis2_orion_camera::1.0"
            ),
            "name": (
                "Artemis 2 Orion Camera "
                "Product Bundle"
            ),
            "doi": "10.17189/hzev-nq50",
            "start_utc": (
                "2026-04-02T12:49:07.000Z"
            ),
            "stop_utc": (
                "2026-04-10T08:13:18.000Z"
            ),
            "targets": [
                "Earth",
                "Moon",
            ],
            "instruments": [
                (
                    "Orion Solar Array Wing "
                    "(SAW) cameras"
                ),
                (
                    "Orion Optical Navigation "
                    "(OpNav) camera"
                ),
                "Orion Cabin cameras",
                "Orion Docking Camera",
            ],
            "collections": [
                {
                    "collection_id": (
                        "orion_camera_raw_image"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_orion_camera:"
                        "data_raw_image::1.0"
                    ),
                    "collection_type": "DATA",
                    "name": (
                        "Artemis 2 Orion Cameras "
                        "Data Raw Image Product Collection"
                    ),
                    "content_class": (
                        "raw_imagery"
                    ),
                },
                {
                    "collection_id": (
                        "orion_camera_video"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_orion_camera:"
                        "data_video::1.0"
                    ),
                    "collection_type": "DATA",
                    "name": (
                        "Artemis 2 Orion Cameras "
                        "Data Raw Product Collection"
                    ),
                    "content_class": (
                        "video"
                    ),
                },
                {
                    "collection_id": (
                        "orion_camera_browse"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_orion_camera:"
                        "browse_source::1.0"
                    ),
                    "collection_type": "BROWSE",
                    "name": (
                        "Artemis 2 Orion Cameras "
                        "Browse Source Product Collection"
                    ),
                    "content_class": (
                        "browse_imagery"
                    ),
                },
            ],
        },
        {
            "bundle_id": "mission_audio",
            "pds_identifier": (
                "urn:nasa:pds:"
                "artemis2_mission_audio::1.0"
            ),
            "name": (
                "Artemis 2 Mission Audio "
                "Product Bundle"
            ),
            "doi": "10.17189/4a29-dz64",
            "start_utc": (
                "2026-04-05T05:36:35.000Z"
            ),
            "stop_utc": (
                "2026-04-07T11:59:59.000Z"
            ),
            "targets": [
                "Earth",
                "Moon",
            ],
            "instruments": [
                "Microsoft Surface Pro 5",
                "Artemis Voice Loop",
            ],
            "collections": [
                {
                    "collection_id": (
                        "mission_audio_pcd"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_mission_audio:"
                        "data_audio_pcd::1.0"
                    ),
                    "collection_type": "DATA",
                    "name": (
                        "Artemis 2 Mission "
                        "PCD Audio Product Collection"
                    ),
                    "content_class": "crew_audio",
                },
                {
                    "collection_id": (
                        "mission_transcripts_pcd"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_mission_audio:"
                        "data_transcripts_pcd::1.0"
                    ),
                    "collection_type": "DATA",
                    "name": (
                        "Artemis 2 Mission Audio "
                        "Portable Computing Device "
                        "Transcript Product Collection"
                    ),
                    "content_class": (
                        "crew_audio_transcripts"
                    ),
                },
                {
                    "collection_id": (
                        "mission_voice_loop_audio"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_mission_audio:"
                        "data_audio_loops::1.0"
                    ),
                    "collection_type": "DATA",
                    "name": (
                        "Artemis 2 Mission Voice "
                        "Loop Audio Product Collection"
                    ),
                    "content_class": (
                        "voice_loop_audio"
                    ),
                },
                {
                    "collection_id": (
                        "mission_voice_loop_transcripts"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_mission_audio:"
                        "data_transcripts_loops::1.0"
                    ),
                    "collection_type": "DATA",
                    "name": (
                        "Artemis 2 Mission Voice "
                        "Loop Transcript Product Collection"
                    ),
                    "content_class": (
                        "voice_loop_transcripts"
                    ),
                },
                {
                    "collection_id": (
                        "mission_annotations"
                    ),
                    "pds_identifier": (
                        "urn:nasa:pds:"
                        "artemis2_mission_audio:"
                        "annotations::1.0"
                    ),
                    "collection_type": "DOCUMENT",
                    "name": (
                        "Artemis 2 Mission Crew "
                        "Annotation Files Product Collection"
                    ),
                    "content_class": (
                        "crew_annotations"
                    ),
                },
            ],
        },
    ]


def observation_evidence() -> list[dict]:
    return [
        {
            "observation_id": (
                "A2_LUNAR_EARTHSET"
            ),
            "observation_class": (
                "EARTH_IMAGERY"
            ),
            "target": "Earth",
            "reported_utc": (
                "2026-04-06T22:41:00Z"
            ),
            "time_precision": (
                "MINUTE"
            ),
            "reported_image_id": (
                "art002e009288"
            ),
            "evidence_state": (
                "NASA_REPORTED"
            ),
            "description": (
                "Earthset behind the lunar limb "
                "during the far-side flyby."
            ),
            "source_ids": [
                (
                    "NASA_ARTEMIS_II_OFFICIAL_"
                    "MOON_FLYBY_PHOTOS_2026_04_07"
                ),
            ],
        },
        {
            "observation_id": (
                "A2_LUNAR_EARTHRISE"
            ),
            "observation_class": (
                "EARTH_IMAGERY"
            ),
            "target": "Earth",
            "reported_utc": (
                "2026-04-06T23:22:00Z"
            ),
            "time_precision": (
                "MINUTE"
            ),
            "reported_image_id": (
                "art002e021278"
            ),
            "evidence_state": (
                "NASA_REPORTED"
            ),
            "description": (
                "Earthrise photographed through "
                "an Orion spacecraft window."
            ),
            "source_ids": [
                (
                    "NASA_ARTEMIS_II_OFFICIAL_"
                    "MOON_FLYBY_PHOTOS_2026_04_07"
                ),
            ],
        },
        {
            "observation_id": (
                "A2_LUNAR_TERMINATOR_VAVILOV"
            ),
            "observation_class": (
                "TERMINATOR_OBSERVATION"
            ),
            "target": (
                "Vavilov Crater / "
                "Hertzsprung basin region"
            ),
            "reported_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "DATE_ONLY_IN_CURATED_SOURCE"
            ),
            "reported_image_id": (
                "art002e009282"
            ),
            "evidence_state": (
                "NASA_REPORTED"
            ),
            "description": (
                "Long shadows near the lunar "
                "terminator accentuated Vavilov "
                "Crater and surrounding terrain."
            ),
            "source_ids": [
                (
                    "NASA_ARTEMIS_II_OFFICIAL_"
                    "MOON_FLYBY_PHOTOS_2026_04_07"
                ),
            ],
        },
        {
            "observation_id": (
                "A2_LUNAR_SOLAR_ECLIPSE"
            ),
            "observation_class": (
                "ECLIPSE_CORONA_OBSERVATION"
            ),
            "target": (
                "Sun / lunar limb"
            ),
            "reported_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "NO_EXACT_START_STOP_IN_CURATED_SOURCE"
            ),
            "reported_image_id": (
                "art002e009301"
            ),
            "reported_totality_duration_minutes": (
                54
            ),
            "duration_qualifier": (
                "NEARLY"
            ),
            "evidence_state": (
                "NASA_REPORTED"
            ),
            "description": (
                "The Moon fully eclipsed the Sun "
                "from Orion's viewpoint for nearly "
                "54 minutes."
            ),
            "interpretation_boundary": (
                "NASA stated the visible halo "
                "was under investigation as corona, "
                "zodiacal light, or a combination."
            ),
            "source_ids": [
                (
                    "NASA_ARTEMIS_II_OFFICIAL_"
                    "MOON_FLYBY_PHOTOS_2026_04_07"
                ),
            ],
        },
        {
            "observation_id": (
                "A2_LUNAR_IMPACT_FLASH_REPORT"
            ),
            "observation_class": (
                "IMPACT_FLASH_OBSERVATION"
            ),
            "target": (
                "lunar night side"
            ),
            "reported_utc": None,
            "time_precision": (
                "NO_INDIVIDUAL_FLASH_TIMES_"
                "IN_CURATED_SOURCE"
            ),
            "evidence_state": (
                "SOURCE_EVOLUTION_REQUIRES_"
                "RECONCILIATION"
            ),
            "count_evidence": [
                {
                    "reported_count": 6,
                    "source_id": (
                        "NASA_ARTEMIS_II_OFFICIAL_"
                        "MOON_FLYBY_PHOTOS_2026_04_07"
                    ),
                    "publication_date": (
                        "2026-04-07"
                    ),
                    "status": (
                        "EARLY_PUBLIC_REPORT"
                    ),
                },
                {
                    "reported_count": 5,
                    "source_id": (
                        "NASA_ARTEMIS_II_CREW_MOON_"
                        "PHOTO_ANNOTATIONS_2026_10_07"
                    ),
                    "publication_date": (
                        "2026-10-07"
                    ),
                    "status": (
                        "POSTFLIGHT_DATA_RELEASE_REPORT"
                    ),
                },
            ],
            "missionlab_selected_count": None,
            "reason": (
                "MissionLab preserves the public "
                "source evolution rather than silently "
                "forcing the early six-flash report "
                "and later five-flash annotation report "
                "into a single unsupported value."
            ),
        },
    ]


def archive_release_summary() -> dict:
    return {
        "release_date": "2026-10-07",
        "reported_total_data_volume_gb": {
            "operator": ">",
            "value": 800,
            "exact": False,
        },
        "reported_full_resolution_image_video_count": {
            "operator": ">",
            "value": 11000,
            "exact": False,
        },
        "reported_science_audio_hours": {
            "value": 8.5,
            "exact": False,
        },
        "includes": [
            "crew_handheld_imagery",
            "orion_spacecraft_imagery",
            "video",
            "crew_science_audio",
            "transcripts",
            "crew_annotations",
        ],
        "boundary": (
            "NASA release totals are public summary "
            "figures and are not treated as exact "
            "PDS product counts."
        ),
    }


def flatten_collections(
    bundles: list[dict],
) -> list[dict]:
    rows = []

    for bundle in bundles:
        for collection in bundle[
            "collections"
        ]:
            rows.append(
                {
                    "bundle_id": (
                        bundle[
                            "bundle_id"
                        ]
                    ),
                    "bundle_pds_identifier": (
                        bundle[
                            "pds_identifier"
                        ]
                    ),
                    "bundle_doi": (
                        bundle[
                            "doi"
                        ]
                    ),
                    "bundle_start_utc": (
                        bundle[
                            "start_utc"
                        ]
                    ),
                    "bundle_stop_utc": (
                        bundle[
                            "stop_utc"
                        ]
                    ),
                    "collection_id": (
                        collection[
                            "collection_id"
                        ]
                    ),
                    "collection_pds_identifier": (
                        collection[
                            "pds_identifier"
                        ]
                    ),
                    "collection_type": (
                        collection[
                            "collection_type"
                        ]
                    ),
                    "content_class": (
                        collection[
                            "content_class"
                        ]
                    ),
                    "collection_name": (
                        collection[
                            "name"
                        ]
                    ),
                }
            )

    return rows


def write_collection_csv(
    rows: list[dict],
):
    fieldnames = [
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

    with COLLECTION_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def build_figure(
    bundles: list[dict],
):
    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    bundle_names = [
        "Crew camera",
        "Orion camera",
        "Mission audio",
    ]

    collection_counts = [
        len(
            bundle[
                "collections"
            ]
        )
        for bundle
        in bundles
    ]

    fig, ax = plt.subplots(
        figsize=(
            10,
            6,
        )
    )

    ax.bar(
        bundle_names,
        collection_counts,
    )

    ax.set_ylabel(
        "Indexed PDS collections"
    )

    ax.set_title(
        (
            "Artemis II Lunar Science "
            "Public Archive Index"
        )
    )

    ax.grid(
        True,
        axis="y",
        alpha=0.25,
    )

    ax.text(
        0.5,
        -0.18,
        (
            "Collection-level archive registry. "
            "NASA release totals of 800+ GB and "
            "11,000+ images/video are not treated "
            "as exact product counts."
        ),
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
    )

    fig.tight_layout()

    fig.savefig(
        FIGURE_PATH,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        FIGURE_PATH
    )


def main():
    print()
    print(
        "Phase 6A Artemis II Lunar Science "
        "Archive and Evidence Index"
    )
    print(
        "=" * 72
    )

    sources = source_registry()
    bundles = bundle_registry()
    observations = observation_evidence()
    release = archive_release_summary()

    collections = flatten_collections(
        bundles
    )

    require(
        len(
            sources
        )
        == 8,
        "expected 8 source records",
    )

    require(
        len(
            bundles
        )
        == 3,
        "expected 3 PDS bundles",
    )

    require(
        len(
            collections
        )
        == 12,
        (
            "expected 12 PDS collections, "
            f"found {len(collections)}"
        ),
    )

    require(
        len(
            observations
        )
        == 5,
        "expected 5 observation evidence records",
    )

    collection_ids = [
        row[
            "collection_id"
        ]
        for row
        in collections
    ]

    require(
        len(
            collection_ids
        )
        == len(
            set(
                collection_ids
            )
        ),
        "duplicate collection IDs",
    )

    observation_ids = [
        item[
            "observation_id"
        ]
        for item
        in observations
    ]

    require(
        len(
            observation_ids
        )
        == len(
            set(
                observation_ids
            )
        ),
        "duplicate observation IDs",
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REFERENCE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_collection_csv(
        collections
    )

    build_figure(
        bundles
    )

    result = {
        "dataset_id": (
            "phase6a_artemis_ii_"
            "lunar_science_archive_index"
        ),
        "mission": "Artemis II",
        "phase": "6A",
        "status": (
            "PUBLIC_LUNAR_SCIENCE_"
            "ARCHIVE_INDEXED"
        ),
        "release_summary": release,
        "source_registry": sources,
        "pds_bundles": bundles,
        "collection_index_summary": {
            "bundle_count": (
                len(
                    bundles
                )
            ),
            "collection_count": (
                len(
                    collections
                )
            ),
            "bundle_ids": [
                bundle[
                    "bundle_id"
                ]
                for bundle
                in bundles
            ],
            "content_classes": sorted(
                {
                    row[
                        "content_class"
                    ]
                    for row
                    in collections
                }
            ),
            "individual_media_downloaded": (
                False
            ),
            "reason": (
                "Phase 6A indexes authoritative "
                "PDS archive structure and metadata "
                "without downloading the 800+ GB "
                "science archive."
            ),
        },
        "observation_evidence": (
            observations
        ),
        "roadmap_mapping": {
            "index_pds_crew_imagery_metadata": (
                "COLLECTION_LEVEL_COMPLETE_"
                "PRODUCT_LEVEL_PENDING"
            ),
            "index_pds_orion_imagery_metadata": (
                "COLLECTION_LEVEL_COMPLETE_"
                "PRODUCT_LEVEL_PENDING"
            ),
            "index_audio_transcripts_annotations": (
                "COLLECTION_LEVEL_COMPLETE_"
                "PRODUCT_LEVEL_PENDING"
            ),
            "connect_observation_time_view_image_remark_target": (
                "PARTIAL_OBSERVATION_EVIDENCE_"
                "SEE_PHASE6B"
            ),
            "integrate_lro_context": (
                "PENDING_PHASE6B"
            ),
            "reconstruct_impact_flash": (
                "PENDING_PHASE6B"
            ),
            "reconstruct_terminator": (
                "PENDING_PHASE6B"
            ),
            "reconstruct_eclipse_corona": (
                "PENDING_PHASE6B"
            ),
            "reconstruct_earth_imagery": (
                "PENDING_PHASE6B"
            ),
        },
        "critical_non_equivalences": [
            {
                "left": (
                    "NASA_RELEASE_SUMMARY_COUNT"
                ),
                "right": (
                    "EXACT_PDS_PRODUCT_COUNT"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "PDS_COLLECTION_INDEX"
                ),
                "right": (
                    "FULL_MEDIA_DOWNLOAD"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "IMAGE_CAPTURE_TIME"
                ),
                "right": (
                    "CREW_REMARK_TIME"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "OBSERVATION_OPPORTUNITY"
                ),
                "right": (
                    "CONFIRMED_OBSERVATION"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "EARLY_PUBLIC_FLASH_COUNT"
                ),
                "right": (
                    "FINAL_RECONCILED_FLASH_COUNT"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "VISIBLE_ECLIPSE_HALO"
                ),
                "right": (
                    "CONFIRMED_SOLAR_CORONA_ONLY"
                ),
                "equivalent": False,
            },
        ],
        "outputs": {
            "reference_json": (
                "data/reference/"
                "artemis_ii_lunar_science_archive_index.json"
            ),
            "processed_summary_json": (
                "data/processed/lunar_science/"
                "artemis_ii_lunar_science_archive_summary.json"
            ),
            "collection_csv": (
                "data/processed/lunar_science/"
                "artemis_ii_lunar_science_collections.csv"
            ),
            "figure": (
                "docs/assets/lunar_science/"
                "phase6a_lunar_science_archive_index.svg"
            ),
        },
    }

    with REFERENCE_PATH.open(
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

    with SUMMARY_PATH.open(
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

    print()
    print(
        "NASA public release:"
    )
    print(
        "  reported archive volume: >800 GB"
    )
    print(
        "  reported images/video: >11,000"
    )
    print(
        "  reported science audio: 8.5 hours"
    )
    print(
        "  exact PDS product counts inferred: NO"
    )

    print()
    print(
        "PDS bundle registry:"
    )

    for bundle in bundles:
        print(
            "  "
            + bundle[
                "bundle_id"
            ]
            + ": "
            + str(
                len(
                    bundle[
                        "collections"
                    ]
                )
            )
            + " collections"
        )

    print()
    print(
        "Archive index totals:"
    )
    print(
        "  PDS bundles: "
        f"{len(bundles)}"
    )
    print(
        "  PDS collections: "
        f"{len(collections)}"
    )
    print(
        "  source records: "
        f"{len(sources)}"
    )
    print(
        "  observation evidence records: "
        f"{len(observations)}"
    )
    print(
        "  individual media downloaded: NO"
    )

    print()
    print(
        "Observation evidence:"
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
        "  solar eclipse: nearly 54 min"
    )
    print(
        "  impact flashes: "
        "PUBLIC SOURCE EVOLUTION PRESERVED"
    )

    print()
    print(
        "Impact-flash source evolution:"
    )
    print(
        "  Apr 7 early public report: 6"
    )
    print(
        "  Oct 7 postflight annotation report: 5"
    )
    print(
        "  silently reconciled by MissionLab: NO"
    )

    print()
    print(
        "Critical boundaries:"
    )
    print(
        "  NASA summary count "
        "!= exact PDS product count"
    )
    print(
        "  archive index "
        "!= full media download"
    )
    print(
        "  image time "
        "!= crew remark time"
    )
    print(
        "  observation opportunity "
        "!= confirmed observation"
    )
    print(
        "  early flash count "
        "!= final reconciled count"
    )
    print(
        "  visible eclipse halo "
        "!= confirmed corona-only signal"
    )

    print()
    print(
        "Phase 6 roadmap state:"
    )
    print(
        "  PDS collection-level archive index: COMPLETE"
    )
    print(
        "  product-level observation correlation: PENDING 6B"
    )
    print(
        "  LRO target context: PENDING 6B"
    )
    print(
        "  observation reconstruction: PENDING 6B"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            REFERENCE_PATH.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            SUMMARY_PATH.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            COLLECTION_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            FIGURE_PATH.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 6A LUNAR SCIENCE "
        "ARCHIVE INDEX COMPLETE"
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import spiceypy as spice


ROOT = Path(__file__).resolve().parents[2]

MISSION_PATH = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

TRAJECTORY_PATH = (
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

SPICE_DIR = (
    ROOT
    / "data"
    / "raw"
    / "spice"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "radiation"
)

OUTPUT_TRAJECTORY = (
    OUTPUT_DIR
    / "artemis_ii_nairas_trajectory_fields.csv"
)

OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / "artemis_ii_nairas_radiation_interface.json"
)

REFERENCE_OUTPUT = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_nairas_interface.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "radiation"
)

FIGURE_PATH = (
    ASSET_DIR
    / "phase5b_nairas_radiation_interface.svg"
)


NAIRAS_MODEL_NAME = "NAIRAS"
NAIRAS_MODEL_VERSION = "3.0"

NAIRAS_MODEL_URL = (
    "https://ccmc.gsfc.nasa.gov/models/NAIRAS~3.0/"
)

NAIRAS_ROR_URL = (
    "https://ccmc.gsfc.nasa.gov/ror/requests/"
    "IT/NAIRAS3/nairas_user_registration.php"
)

NAIRAS_REQUIRED_FIELDS = [
    "date",
    "time",
    "geocentric_latitude_deg",
    "geocentric_longitude_deg",
    "altitude_km",
]

NAIRAS_DOSIMETRIC_OUTPUTS = [
    "absorbed_dose_in_silicon",
    "absorbed_dose_in_tissue",
    "dose_equivalent",
    "ambient_dose_equivalent",
    "effective_dose",
]

NAIRAS_RADIATION_SOURCES = [
    "GCR",
    "SEP",
    "TRP_where_model_applicable",
]


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
        "PHASE 5B ANALYSIS FAILED: "
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


def load_csv(
    path: Path,
) -> list[dict]:
    require(
        path.exists(),
        f"missing trajectory: {path}",
    )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(
            csv.DictReader(
                f
            )
        )

    require(
        len(
            rows
        )
        > 0,
        "trajectory contains no rows",
    )

    return rows


def parse_utc(
    value: str,
) -> datetime:
    normalized = value.strip()

    if normalized.endswith(
        "Z"
    ):
        normalized = (
            normalized[
                :-1
            ]
            + "+00:00"
        )

    result = datetime.fromisoformat(
        normalized
    )

    if result.tzinfo is None:
        result = result.replace(
            tzinfo=timezone.utc,
        )

    return result.astimezone(
        timezone.utc
    )


def format_utc(
    value: datetime,
) -> str:
    return (
        value.isoformat(
            timespec="milliseconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def format_nairas_time(
    value: datetime,
) -> str:
    return (
        value.strftime(
            "%H:%M:%S.%f"
        )[
            :-3
        ]
    )


def normalize_longitude(
    degrees: float,
) -> float:
    normalized = (
        (
            degrees
            + 180.0
        )
        % 360.0
    ) - 180.0

    if normalized == -180.0:
        return 180.0

    return normalized


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


def load_spice():
    required = [
        SPICE_DIR
        / "naif0012.tls",
        SPICE_DIR
        / "pck00011.tpc",
    ]

    for path in required:
        require(
            path.exists(),
            f"missing SPICE kernel: {path}",
        )

        spice.furnsh(
            str(
                path
            )
        )


def trajectory_to_nairas(
    rows: list[dict],
    launch: datetime,
) -> tuple[
    list[dict],
    dict,
]:
    _, earth_radii = spice.bodvrd(
        "EARTH",
        "RADII",
        3,
    )

    earth_mean_radius_km = (
        sum(
            earth_radii
        )
        / 3.0
    )

    output = []

    previous_time = None

    for index, row in enumerate(
        rows,
        start=1,
    ):
        for required in [
            "timestamp_utc",
            "x_km",
            "y_km",
            "z_km",
        ]:
            require(
                required
                in row,
                (
                    "trajectory row missing "
                    f"{required}"
                ),
            )

        timestamp = parse_utc(
            row[
                "timestamp_utc"
            ]
        )

        if previous_time is not None:
            require(
                timestamp
                > previous_time,
                (
                    "trajectory timestamps "
                    f"not increasing at row {index}"
                ),
            )

        previous_time = timestamp

        inertial_position = [
            float(
                row[
                    "x_km"
                ]
            ),
            float(
                row[
                    "y_km"
                ]
            ),
            float(
                row[
                    "z_km"
                ]
            ),
        ]

        spice_time = (
            timestamp.strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )
            + " UTC"
        )

        et = spice.str2et(
            spice_time
        )

        rotation = spice.pxform(
            "J2000",
            "IAU_EARTH",
            et,
        )

        earth_fixed = spice.mxv(
            rotation,
            inertial_position,
        )

        (
            radius_km,
            longitude_rad,
            latitude_rad,
        ) = spice.reclat(
            earth_fixed
        )

        latitude_deg = math.degrees(
            latitude_rad
        )

        longitude_deg = (
            normalize_longitude(
                math.degrees(
                    longitude_rad
                )
            )
        )

        altitude_km = (
            radius_km
            - earth_mean_radius_km
        )

        met_seconds = (
            timestamp
            - launch
        ).total_seconds()

        require(
            math.isfinite(
                latitude_deg
            ),
            (
                "non-finite latitude "
                f"at row {index}"
            ),
        )

        require(
            math.isfinite(
                longitude_deg
            ),
            (
                "non-finite longitude "
                f"at row {index}"
            ),
        )

        require(
            math.isfinite(
                altitude_km
            ),
            (
                "non-finite altitude "
                f"at row {index}"
            ),
        )

        require(
            -90.0
            <= latitude_deg
            <= 90.0,
            (
                "latitude outside range "
                f"at row {index}"
            ),
        )

        require(
            -180.0
            <= longitude_deg
            <= 180.0,
            (
                "longitude outside range "
                f"at row {index}"
            ),
        )

        output.append(
            {
                "date": (
                    timestamp.strftime(
                        "%Y-%m-%d"
                    )
                ),
                "time": (
                    format_nairas_time(
                        timestamp
                    )
                ),
                "geocentric_latitude_deg": (
                    round(
                        latitude_deg,
                        8,
                    )
                ),
                "geocentric_longitude_deg": (
                    round(
                        longitude_deg,
                        8,
                    )
                ),
                "altitude_km": (
                    round(
                        altitude_km,
                        6,
                    )
                ),
                "source_timestamp_utc": (
                    format_utc(
                        timestamp
                    )
                ),
                "met_seconds": (
                    round(
                        met_seconds,
                        3,
                    )
                ),
                "geometric_mission_phase": (
                    row.get(
                        "geometric_mission_phase",
                        "",
                    )
                ),
            }
        )

    altitudes = [
        row[
            "altitude_km"
        ]
        for row
        in output
    ]

    latitudes = [
        row[
            "geocentric_latitude_deg"
        ]
        for row
        in output
    ]

    longitudes = [
        row[
            "geocentric_longitude_deg"
        ]
        for row
        in output
    ]

    metadata = {
        "earth_radii_km": [
            float(
                value
            )
            for value
            in earth_radii
        ],
        "earth_mean_radius_km": (
            earth_mean_radius_km
        ),
        "input_frame": (
            "J2000"
        ),
        "output_frame": (
            "IAU_EARTH"
        ),
        "latitude_definition": (
            "geocentric latitude from "
            "Earth-fixed Cartesian position"
        ),
        "longitude_definition": (
            "Earth-fixed geocentric longitude "
            "normalized to [-180, 180] degrees"
        ),
        "altitude_definition": (
            "Earth-center radius minus SPICE "
            "mean Earth radius"
        ),
        "minimum_altitude_km": (
            min(
                altitudes
            )
        ),
        "maximum_altitude_km": (
            max(
                altitudes
            )
        ),
        "minimum_latitude_deg": (
            min(
                latitudes
            )
        ),
        "maximum_latitude_deg": (
            max(
                latitudes
            )
        ),
        "minimum_longitude_deg": (
            min(
                longitudes
            )
        ),
        "maximum_longitude_deg": (
            max(
                longitudes
            )
        ),
    }

    return (
        output,
        metadata,
    )


def write_nairas_field_csv(
    rows: list[dict],
):
    fieldnames = [
        "date",
        "time",
        "geocentric_latitude_deg",
        "geocentric_longitude_deg",
        "altitude_km",
    ]

    with OUTPUT_TRAJECTORY.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    key: row[
                        key
                    ]
                    for key
                    in fieldnames
                }
            )


def build_figure(
    rows: list[dict],
):
    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    met_days = [
        row[
            "met_seconds"
        ]
        / 86400.0
        for row
        in rows
    ]

    altitude_thousands_km = [
        row[
            "altitude_km"
        ]
        / 1000.0
        for row
        in rows
    ]

    latitude = [
        row[
            "geocentric_latitude_deg"
        ]
        for row
        in rows
    ]

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(
            14,
            9,
        ),
        sharex=True,
    )

    axes[
        0
    ].plot(
        met_days,
        altitude_thousands_km,
    )

    axes[
        0
    ].set_ylabel(
        "Geocentric altitude (10³ km)"
    )

    axes[
        0
    ].grid(
        True,
        alpha=0.25,
    )

    axes[
        1
    ].plot(
        met_days,
        latitude,
    )

    axes[
        1
    ].set_ylabel(
        "Geocentric latitude (deg)"
    )

    axes[
        1
    ].set_xlabel(
        "Mission elapsed time (days)"
    )

    axes[
        1
    ].grid(
        True,
        alpha=0.25,
    )

    fig.suptitle(
        (
            "Artemis II NAIRAS "
            "Trajectory-Interface Preparation"
        )
    )

    fig.text(
        0.5,
        0.015,
        (
            "Geometry is transformed from the "
            "NASA flight-derived J2000 trajectory. "
            "No shielding depth, radiation flux, "
            "or crew dose is inferred by this step."
        ),
        ha="center",
        fontsize=8,
    )

    fig.tight_layout(
        rect=(
            0,
            0.04,
            1,
            0.96,
        )
    )

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


def build_interface_manifest(
    mission: dict,
    space_weather: dict,
    input_rows: list[dict],
    output_rows: list[dict],
    geometry_metadata: dict,
) -> dict:
    first = output_rows[
        0
    ]

    last = output_rows[
        -1
    ]

    phases = sorted(
        {
            row[
                "geometric_mission_phase"
            ]
            for row
            in output_rows
            if row[
                "geometric_mission_phase"
            ]
        }
    )

    return {
        "dataset_id": (
            "phase5b_artemis_ii_"
            "nairas_radiation_interface"
        ),
        "mission": (
            "Artemis II"
        ),
        "phase": (
            "5B"
        ),
        "status": (
            "NAIRAS_TRAJECTORY_INTERFACE_PREPARED"
        ),
        "source_trajectory": {
            "path": (
                "data/processed/trajectory/"
                "trajectory_with_mission_phases.csv"
            ),
            "provenance": (
                "NASA_FLIGHT_DERIVED_OEM_"
                "WITH_MISSIONLAB_DERIVED_GEOMETRY"
            ),
            "input_row_count": (
                len(
                    input_rows
                )
            ),
            "start_utc": (
                first[
                    "source_timestamp_utc"
                ]
            ),
            "stop_utc": (
                last[
                    "source_timestamp_utc"
                ]
            ),
            "mission_phases_present": (
                phases
            ),
            "complete_launch_to_splashdown_coverage": (
                False
            ),
            "coverage_boundary": (
                "The selected public primary OEM "
                "begins after launch and ends at "
                "Entry Interface. MissionLab does "
                "not invent trajectory states outside "
                "the flight-derived OEM coverage."
            ),
        },
        "nairas_model": {
            "name": (
                NAIRAS_MODEL_NAME
            ),
            "version_family": (
                NAIRAS_MODEL_VERSION
            ),
            "model_page": (
                NAIRAS_MODEL_URL
            ),
            "runs_on_request_page": (
                NAIRAS_ROR_URL
            ),
            "trajectory_run_supported": (
                True
            ),
            "spacecraft_trajectory_supported": (
                True
            ),
            "required_trajectory_fields": (
                NAIRAS_REQUIRED_FIELDS
            ),
            "radiation_sources_described_by_model": (
                NAIRAS_RADIATION_SOURCES
            ),
            "available_dosimetric_quantities": (
                NAIRAS_DOSIMETRIC_OUTPUTS
            ),
            "user_selectable_aluminum_equivalent_shielding_depths": (
                True
            ),
        },
        "trajectory_interface": {
            "output_path": (
                "data/processed/radiation/"
                "artemis_ii_nairas_trajectory_fields.csv"
            ),
            "output_row_count": (
                len(
                    output_rows
                )
            ),
            "field_content_ready": (
                True
            ),
            "portal_specific_file_syntax_confirmed": (
                False
            ),
            "reason": (
                "NASA publicly specifies the key "
                "trajectory fields. This product "
                "prepares those fields directly but "
                "does not claim an undocumented "
                "portal parser syntax."
            ),
            "coordinate_conversion": (
                geometry_metadata
            ),
        },
        "shielding": {
            "orion_specific_effective_aluminum_equivalent_depth_publicly_established_here": (
                False
            ),
            "shielding_depths_g_cm2_used_by_missionlab": [],
            "dose_calculation_performed": (
                False
            ),
            "reason": (
                "NAIRAS shielding depth is a model "
                "input. MissionLab does not assign "
                "an Orion crew-location shielding "
                "depth without defensible source "
                "evidence."
            ),
        },
        "phase5a_relationship": {
            "space_weather_dataset_id": (
                space_weather[
                    "dataset_id"
                ]
            ),
            "omni_context_manually_used_as_nairas_driver": (
                False
            ),
            "reason": (
                "Phase 5A OMNI data provide an "
                "independent mission-clock-aligned "
                "near-Earth context product. "
                "MissionLab does not override or "
                "replace NAIRAS internal radiation "
                "environment drivers."
            ),
        },
        "radiation_response_chain": [
            {
                "stage": 1,
                "name": (
                    "external_radiation_environment"
                ),
                "examples": [
                    "GCR",
                    "SEP",
                    "TRP_where_applicable",
                ],
            },
            {
                "stage": 2,
                "name": (
                    "transport_through_material"
                ),
                "requires": [
                    (
                        "trajectory"
                    ),
                    (
                        "material_or_aluminum_"
                        "equivalent_shielding"
                    ),
                ],
            },
            {
                "stage": 3,
                "name": (
                    "absorbed_dose"
                ),
                "examples": [
                    (
                        "absorbed_dose_"
                        "in_silicon"
                    ),
                    (
                        "absorbed_dose_"
                        "in_tissue"
                    ),
                ],
            },
            {
                "stage": 4,
                "name": (
                    "radiation_protection_"
                    "response_quantity"
                ),
                "examples": [
                    "dose_equivalent",
                    "ambient_dose_equivalent",
                    "effective_dose",
                ],
            },
        ],
        "nairas_run_status": {
            "run_submitted_by_missionlab": (
                False
            ),
            "run_id": (
                None
            ),
            "run_output_ingested": (
                False
            ),
            "dose_values_reported": (
                False
            ),
            "status": (
                "TRAJECTORY_PREPARED_"
                "NO_RUN_CLAIMED"
            ),
            "closure_rule": (
                "A future authenticated CCMC "
                "Runs-on-Request submission can "
                "use this trajectory field product. "
                "Until an actual NAIRAS output is "
                "obtained, MissionLab reports no "
                "NAIRAS-derived radiation dose."
            ),
        },
        "critical_non_equivalences": [
            {
                "left": (
                    "PHASE5A_OMNI_CONTEXT"
                ),
                "right": (
                    "ORION_LOCAL_RADIATION_FIELD"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "EXTERNAL_RADIATION_ENVIRONMENT"
                ),
                "right": (
                    "ABSORBED_DOSE"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "ABSORBED_DOSE"
                ),
                "right": (
                    "DOSE_EQUIVALENT"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "DOSE_EQUIVALENT"
                ),
                "right": (
                    "EFFECTIVE_DOSE"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "TRAJECTORY_GEOMETRY"
                ),
                "right": (
                    "RADIATION_DOSE"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "ASSUMED_SHIELDING_DEPTH"
                ),
                "right": (
                    "ORION_CREW_LOCATION_SHIELDING"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "NAIRAS_INTERFACE_PREPARED"
                ),
                "right": (
                    "NAIRAS_RUN_EXECUTED"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "NAIRAS_MODEL_OUTPUT"
                ),
                "right": (
                    "CREW_DOSIMETER_MEASUREMENT"
                ),
                "equivalent": (
                    False
                ),
            },
        ],
        "roadmap_assessment": {
            "ingest_omni_cdaweb_quantities": {
                "status": (
                    "COMPLETE"
                ),
                "phase": (
                    "5A"
                ),
            },
            "correlate_space_weather_with_mission_clock": {
                "status": (
                    "COMPLETE"
                ),
                "phase": (
                    "5A"
                ),
            },
            "prepare_artemis_ii_trajectory_for_nairas": {
                "status": (
                    "COMPLETE"
                ),
                "phase": (
                    "5B"
                ),
            },
            "ingest_export_nairas_runs_where_permitted": {
                "status": (
                    "INTERFACE_PREPARED_"
                    "NO_RUN_OUTPUT_CLAIMED"
                ),
                "phase": (
                    "5B"
                ),
            },
            "make_shielding_assumptions_explicit": {
                "status": (
                    "COMPLETE"
                ),
                "phase": (
                    "5B"
                ),
                "assumption_used": (
                    "NONE"
                ),
            },
            "external_environment_vs_astronaut_dose": {
                "status": (
                    "SEPARATED"
                ),
                "phase": (
                    "5B"
                ),
            },
            "phase5_overall": {
                "status": (
                    "COMPLETE_WITH_NAIRAS_"
                    "EXECUTION_BOUNDARY"
                ),
            },
        },
        "evidence_boundaries": {
            "trajectory_fields_equal_radiation_dose": (
                False
            ),
            "omni_context_equal_orion_local_radiation": (
                False
            ),
            "shielding_depth_inferred_without_source": (
                False
            ),
            "nairas_run_claimed_without_run_output": (
                False
            ),
            "model_output_equal_dosimeter_measurement": (
                False
            ),
            "external_environment_equal_absorbed_dose": (
                False
            ),
            "absorbed_dose_equal_effective_dose": (
                False
            ),
            "oem_coverage_extended_beyond_public_states": (
                False
            ),
        },
        "outputs": {
            "trajectory_fields_csv": (
                "data/processed/radiation/"
                "artemis_ii_nairas_trajectory_fields.csv"
            ),
            "processed_summary_json": (
                "data/processed/radiation/"
                "artemis_ii_nairas_radiation_interface.json"
            ),
            "reference_manifest_json": (
                "data/reference/"
                "artemis_ii_nairas_interface.json"
            ),
            "figure": (
                "docs/assets/radiation/"
                "phase5b_nairas_radiation_interface.svg"
            ),
        },
    }


def main():
    print()
    print(
        "Phase 5B Artemis II Radiation Environment "
        "and NAIRAS Interface"
    )
    print(
        "=" * 72
    )

    mission = load_json(
        MISSION_PATH
    )

    space_weather = load_json(
        SPACE_WEATHER_PATH
    )

    trajectory_rows = load_csv(
        TRAJECTORY_PATH
    )

    require(
        mission.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
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

    launch = parse_utc(
        mission[
            "launch_epoch_utc"
        ]
    )

    print()
    print(
        "Dependencies:"
    )
    print(
        "  Artemis II mission config: PASS"
    )
    print(
        "  Phase 5A space-weather context: PASS"
    )
    print(
        "  flight-derived mission trajectory: PASS"
    )

    load_spice()

    try:
        (
            nairas_rows,
            geometry_metadata,
        ) = trajectory_to_nairas(
            trajectory_rows,
            launch,
        )

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        ASSET_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        write_nairas_field_csv(
            nairas_rows
        )

        build_figure(
            nairas_rows
        )

        manifest = build_interface_manifest(
            mission,
            space_weather,
            trajectory_rows,
            nairas_rows,
            geometry_metadata,
        )

        with OUTPUT_SUMMARY.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                manifest,
                f,
                indent=2,
            )

            f.write(
                "\n"
            )

        with REFERENCE_OUTPUT.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                manifest,
                f,
                indent=2,
            )

            f.write(
                "\n"
            )

    finally:
        spice.kclear()

    first = nairas_rows[
        0
    ]

    last = nairas_rows[
        -1
    ]

    print()
    print(
        "NAIRAS trajectory field preparation:"
    )
    print(
        "  source states: "
        f"{len(trajectory_rows)}"
    )
    print(
        "  output trajectory points: "
        f"{len(nairas_rows)}"
    )
    print(
        "  required fields: "
        "date / time / geocentric lat / "
        "geocentric lon / altitude"
    )
    print(
        "  field content ready: YES"
    )
    print(
        "  undocumented portal syntax claimed: NO"
    )

    print()
    print(
        "Trajectory coverage:"
    )
    print(
        "  start: "
        + first[
            "source_timestamp_utc"
        ]
    )
    print(
        "  stop:  "
        + last[
            "source_timestamp_utc"
        ]
    )
    print(
        "  launch-to-splashdown coverage: NO"
    )
    print(
        "  public OEM coverage extended: NO"
    )

    print()
    print(
        "Coordinate transformation:"
    )
    print(
        "  J2000 -> IAU_EARTH: COMPLETE"
    )
    print(
        "  geocentric latitude: COMPLETE"
    )
    print(
        "  geocentric longitude: COMPLETE"
    )
    print(
        "  mean-radius altitude: COMPLETE"
    )
    print(
        "  altitude range: "
        f"{geometry_metadata['minimum_altitude_km']:,.3f}"
        " to "
        f"{geometry_metadata['maximum_altitude_km']:,.3f}"
        " km"
    )

    print()
    print(
        "NAIRAS radiation interface:"
    )
    print(
        "  trajectory RoR supported: YES"
    )
    print(
        "  spacecraft trajectory supported: YES"
    )
    print(
        "  dosimetric quantities available: 5"
    )
    print(
        "  user-selectable shielding: YES"
    )

    print()
    print(
        "Shielding boundary:"
    )
    print(
        "  Orion-specific effective shielding "
        "depth established here: NO"
    )
    print(
        "  shielding depth assumed by MissionLab: NO"
    )
    print(
        "  dose calculation performed: NO"
    )

    print()
    print(
        "NAIRAS execution boundary:"
    )
    print(
        "  trajectory interface prepared: YES"
    )
    print(
        "  NAIRAS run submitted: NO"
    )
    print(
        "  NAIRAS run ID: NONE"
    )
    print(
        "  NAIRAS outputs ingested: NO"
    )
    print(
        "  NAIRAS dose reported: NO"
    )

    print()
    print(
        "Radiation-response chain:"
    )
    print(
        "  external radiation environment"
    )
    print(
        "  -> material / shielding transport"
    )
    print(
        "  -> absorbed dose"
    )
    print(
        "  -> dose-equivalent / effective-dose "
        "response quantities"
    )

    print()
    print(
        "Critical boundaries:"
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
        "Phase 5 roadmap:"
    )
    print(
        "  OMNI/CDAWeb ingestion: COMPLETE"
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
        "  NAIRAS run results: NOT CLAIMED"
    )
    print(
        "  overall: "
        "COMPLETE WITH NAIRAS EXECUTION BOUNDARY"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            OUTPUT_TRAJECTORY.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            OUTPUT_SUMMARY.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            REFERENCE_OUTPUT.relative_to(
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
        "PHASE 5B NAIRAS RADIATION "
        "INTERFACE COMPLETE"
    )


if __name__ == "__main__":
    main()
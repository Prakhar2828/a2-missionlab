from __future__ import annotations

import bisect
import csv
import json
import math
from datetime import datetime, timedelta, timezone
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

PHASE6A_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_lunar_science_archive_index.json"
)

TRAJECTORY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "trajectory"
    / "trajectory_with_mission_phases.csv"
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
    / "lunar_science"
)

OUTPUT_JSON = (
    OUTPUT_DIR
    / "artemis_ii_lunar_observation_reconstruction.json"
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "artemis_ii_lunar_observation_correlations.csv"
)

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_lunar_observation_reconstruction.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "lunar_science"
)

FIGURE_PATH = (
    ASSET_DIR
    / "phase6b_lunar_observation_reconstruction.svg"
)


GEOMETRY_START = "2026-04-06T21:30:00Z"
GEOMETRY_STOP = "2026-04-07T02:30:00Z"

EARTHSET_REPORTED_UTC = (
    "2026-04-06T22:41:00Z"
)

EARTHRISE_REPORTED_UTC = (
    "2026-04-06T23:22:00Z"
)

PERICYNTHION_UTC = (
    "2026-04-06T23:00:46.177998Z"
)

VAVILOV_LAT_DEG = -0.87
VAVILOV_LON_DEG = -138.77
VAVILOV_DIAMETER_KM = 98.22


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
        "PHASE 6B ANALYSIS FAILED: "
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
        f"missing CSV dependency: {path}",
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
        > 1,
        f"insufficient rows in {path}",
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


def met_string(
    timestamp: datetime,
    launch: datetime,
) -> str:
    seconds = (
        timestamp
        - launch
    ).total_seconds()

    sign = ""

    if seconds < 0:
        sign = "-"
        seconds = abs(
            seconds
        )

    total = int(
        round(
            seconds
        )
    )

    days, remainder = divmod(
        total,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes, seconds_value = divmod(
        remainder,
        60,
    )

    return (
        f"{sign}"
        f"{days:02d}:"
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds_value:02d}"
    )


def vector_norm(
    vector,
) -> float:
    return math.sqrt(
        sum(
            component
            * component
            for component
            in vector
        )
    )


def vector_subtract(
    a,
    b,
):
    return [
        a[
            i
        ]
        - b[
            i
        ]
        for i
        in range(
            3
        )
    ]


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
        / "de440s.bsp",
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


def prepare_trajectory(
    rows: list[dict],
) -> tuple[
    list[datetime],
    list[list[float]],
]:
    times = []
    positions = []

    previous = None

    for index, row in enumerate(
        rows,
        start=1,
    ):
        timestamp = parse_utc(
            row[
                "timestamp_utc"
            ]
        )

        if previous is not None:
            require(
                timestamp
                > previous,
                (
                    "trajectory timestamps "
                    f"not increasing at row {index}"
                ),
            )

        previous = timestamp

        times.append(
            timestamp
        )

        positions.append(
            [
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
        )

    return (
        times,
        positions,
    )


def interpolate_position(
    timestamp: datetime,
    times: list[datetime],
    positions: list[list[float]],
) -> list[float]:
    require(
        times[
            0
        ]
        <= timestamp
        <= times[
            -1
        ],
        (
            "requested geometry time outside "
            f"trajectory coverage: {timestamp}"
        ),
    )

    index = bisect.bisect_left(
        times,
        timestamp,
    )

    if (
        index
        < len(
            times
        )
        and times[
            index
        ]
        == timestamp
    ):
        return list(
            positions[
                index
            ]
        )

    require(
        index
        > 0
        and index
        < len(
            times
        ),
        "trajectory interpolation bracket missing",
    )

    before_time = times[
        index
        - 1
    ]

    after_time = times[
        index
    ]

    before_position = positions[
        index
        - 1
    ]

    after_position = positions[
        index
    ]

    interval = (
        after_time
        - before_time
    ).total_seconds()

    require(
        interval
        > 0.0,
        "invalid interpolation interval",
    )

    fraction = (
        (
            timestamp
            - before_time
        ).total_seconds()
        / interval
    )

    return [
        before_position[
            axis
        ]
        + (
            after_position[
                axis
            ]
            - before_position[
                axis
            ]
        )
        * fraction
        for axis
        in range(
            3
        )
    ]


def to_et(
    timestamp: datetime,
) -> float:
    return spice.str2et(
        timestamp.strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        + " UTC"
    )


def apparent_radius(
    physical_radius_km: float,
    distance_km: float,
) -> float:
    require(
        distance_km
        > physical_radius_km,
        (
            "observer lies inside or on "
            "apparent body radius"
        ),
    )

    ratio = (
        physical_radius_km
        / distance_km
    )

    ratio = max(
        -1.0,
        min(
            1.0,
            ratio,
        ),
    )

    return math.asin(
        ratio
    )


def get_body_radii() -> dict:
    _, earth_radii = spice.bodvrd(
        "EARTH",
        "RADII",
        3,
    )

    _, moon_radii = spice.bodvrd(
        "MOON",
        "RADII",
        3,
    )

    _, sun_radii = spice.bodvrd(
        "SUN",
        "RADII",
        3,
    )

    return {
        "earth_mean_radius_km": (
            sum(
                earth_radii
            )
            / 3.0
        ),
        "moon_mean_radius_km": (
            sum(
                moon_radii
            )
            / 3.0
        ),
        "sun_mean_radius_km": (
            sum(
                sun_radii
            )
            / 3.0
        ),
    }


def occultation_geometry(
    timestamp: datetime,
    target: str,
    times: list[datetime],
    positions: list[list[float]],
    radii: dict,
) -> dict:
    orion_position = interpolate_position(
        timestamp,
        times,
        positions,
    )

    et = to_et(
        timestamp
    )

    moon_state, _ = spice.spkezr(
        "MOON",
        et,
        "J2000",
        "NONE",
        "EARTH",
    )

    moon_position = list(
        moon_state[
            :3
        ]
    )

    moon_vector = vector_subtract(
        moon_position,
        orion_position,
    )

    moon_distance = vector_norm(
        moon_vector
    )

    moon_radius = apparent_radius(
        radii[
            "moon_mean_radius_km"
        ],
        moon_distance,
    )

    if target == "EARTH":
        target_vector = [
            -component
            for component
            in orion_position
        ]

        target_distance = vector_norm(
            target_vector
        )

        target_physical_radius = radii[
            "earth_mean_radius_km"
        ]

    elif target == "SUN":
        sun_state, _ = spice.spkezr(
            "SUN",
            et,
            "J2000",
            "NONE",
            "EARTH",
        )

        sun_position = list(
            sun_state[
                :3
            ]
        )

        target_vector = vector_subtract(
            sun_position,
            orion_position,
        )

        target_distance = vector_norm(
            target_vector
        )

        target_physical_radius = radii[
            "sun_mean_radius_km"
        ]

    else:
        fail(
            f"unsupported occultation target: {target}"
        )

    target_radius = apparent_radius(
        target_physical_radius,
        target_distance,
    )

    separation = spice.vsep(
        moon_vector,
        target_vector,
    )

    overlap_margin = (
        moon_radius
        + target_radius
        - separation
    )

    full_occultation_margin = (
        moon_radius
        - (
            separation
            + target_radius
        )
    )

    if full_occultation_margin >= 0.0:
        status = (
            "FULLY_OCCULTED_BY_MOON"
        )

    elif overlap_margin >= 0.0:
        status = (
            "PARTIAL_LIMB_OVERLAP"
        )

    else:
        status = (
            "UNOBSCURED_BY_MOON"
        )

    return {
        "utc": (
            format_utc(
                timestamp
            )
        ),
        "target": target,
        "status": status,
        "center_separation_deg": (
            math.degrees(
                separation
            )
        ),
        "moon_apparent_radius_deg": (
            math.degrees(
                moon_radius
            )
        ),
        "target_apparent_radius_deg": (
            math.degrees(
                target_radius
            )
        ),
        "overlap_margin_rad": (
            overlap_margin
        ),
        "full_occultation_margin_rad": (
            full_occultation_margin
        ),
        "moon_distance_km": (
            moon_distance
        ),
        "target_distance_km": (
            target_distance
        ),
    }


def margin_function(
    target: str,
    margin_type: str,
    times: list[datetime],
    positions: list[list[float]],
    radii: dict,
):
    def function(
        timestamp: datetime,
    ) -> float:
        geometry = occultation_geometry(
            timestamp,
            target,
            times,
            positions,
            radii,
        )

        if margin_type == "overlap":
            return geometry[
                "overlap_margin_rad"
            ]

        if margin_type == "full":
            return geometry[
                "full_occultation_margin_rad"
            ]

        fail(
            f"unknown margin type: {margin_type}"
        )

        raise RuntimeError

    return function


def refine_crossing(
    start: datetime,
    stop: datetime,
    function,
) -> datetime:
    value_start = function(
        start
    )

    value_stop = function(
        stop
    )

    require(
        (
            value_start
            <= 0.0
            <= value_stop
        )
        or (
            value_stop
            <= 0.0
            <= value_start
        ),
        "root refinement interval has no sign change",
    )

    left = start
    right = stop
    left_value = value_start

    for _ in range(
        50
    ):
        midpoint = (
            left
            + (
                right
                - left
            )
            / 2
        )

        midpoint_value = function(
            midpoint
        )

        if abs(
            midpoint_value
        ) < 1e-13:
            return midpoint

        if (
            left_value
            <= 0.0
            <= midpoint_value
        ) or (
            midpoint_value
            <= 0.0
            <= left_value
        ):
            right = midpoint

        else:
            left = midpoint
            left_value = midpoint_value

    return (
        left
        + (
            right
            - left
        )
        / 2
    )


def positive_intervals(
    start: datetime,
    stop: datetime,
    step_seconds: int,
    function,
) -> list[
    tuple[
        datetime,
        datetime,
    ]
]:
    require(
        stop
        > start,
        "invalid geometry window",
    )

    samples = []

    current = start

    while current < stop:
        samples.append(
            current
        )

        current += timedelta(
            seconds=step_seconds
        )

    if not samples or samples[
        -1
    ] != stop:
        samples.append(
            stop
        )

    values = [
        function(
            timestamp
        )
        for timestamp
        in samples
    ]

    intervals = []

    active_start = (
        samples[
            0
        ]
        if values[
            0
        ]
        >= 0.0
        else None
    )

    for index in range(
        1,
        len(
            samples
        ),
    ):
        previous_time = samples[
            index
            - 1
        ]

        current_time = samples[
            index
        ]

        previous_value = values[
            index
            - 1
        ]

        current_value = values[
            index
        ]

        previous_inside = (
            previous_value
            >= 0.0
        )

        current_inside = (
            current_value
            >= 0.0
        )

        if (
            not previous_inside
            and current_inside
        ):
            crossing = refine_crossing(
                previous_time,
                current_time,
                function,
            )

            active_start = crossing

        elif (
            previous_inside
            and not current_inside
        ):
            crossing = refine_crossing(
                previous_time,
                current_time,
                function,
            )

            require(
                active_start
                is not None,
                "interval exit without entry",
            )

            intervals.append(
                (
                    active_start,
                    crossing,
                )
            )

            active_start = None

    if active_start is not None:
        intervals.append(
            (
                active_start,
                stop,
            )
        )

    return intervals


def interval_record(
    start: datetime,
    stop: datetime,
    launch: datetime,
    classification: str,
) -> dict:
    return {
        "classification": (
            classification
        ),
        "start_utc": (
            format_utc(
                start
            )
        ),
        "stop_utc": (
            format_utc(
                stop
            )
        ),
        "start_met": (
            met_string(
                start,
                launch,
            )
        ),
        "stop_met": (
            met_string(
                stop,
                launch,
            )
        ),
        "duration_seconds": (
            (
                stop
                - start
            ).total_seconds()
        ),
        "duration_minutes": (
            (
                stop
                - start
            ).total_seconds()
            / 60.0
        ),
        "provenance": (
            "MISSIONLAB_DERIVED_FROM_"
            "NASA_FLIGHT_DERIVED_OEM_AND_SPICE"
        ),
        "precision_boundary": (
            "Boundary is a MissionLab geometric "
            "reconstruction using linear interpolation "
            "between public OEM states and SPICE body "
            "ephemerides. It is not onboard event telemetry."
        ),
    }


def build_geometry(
    launch: datetime,
    times: list[datetime],
    positions: list[list[float]],
    radii: dict,
) -> dict:
    start = parse_utc(
        GEOMETRY_START
    )

    stop = parse_utc(
        GEOMETRY_STOP
    )

    earth_overlap = positive_intervals(
        start,
        stop,
        30,
        margin_function(
            "EARTH",
            "overlap",
            times,
            positions,
            radii,
        ),
    )

    earth_full = positive_intervals(
        start,
        stop,
        30,
        margin_function(
            "EARTH",
            "full",
            times,
            positions,
            radii,
        ),
    )

    sun_overlap = positive_intervals(
        start,
        stop,
        30,
        margin_function(
            "SUN",
            "overlap",
            times,
            positions,
            radii,
        ),
    )

    sun_full = positive_intervals(
        start,
        stop,
        30,
        margin_function(
            "SUN",
            "full",
            times,
            positions,
            radii,
        ),
    )

    require(
        len(
            earth_overlap
        )
        >= 1,
        "no Earth/lunar-limb overlap reconstructed",
    )

    require(
        len(
            earth_full
        )
        >= 1,
        "no full Earth occultation reconstructed",
    )

    require(
        len(
            sun_overlap
        )
        >= 1,
        "no solar/lunar-limb overlap reconstructed",
    )

    require(
        len(
            sun_full
        )
        >= 1,
        "no total solar eclipse reconstructed",
    )

    earthset_snapshot = occultation_geometry(
        parse_utc(
            EARTHSET_REPORTED_UTC
        ),
        "EARTH",
        times,
        positions,
        radii,
    )

    earthrise_snapshot = occultation_geometry(
        parse_utc(
            EARTHRISE_REPORTED_UTC
        ),
        "EARTH",
        times,
        positions,
        radii,
    )

    pericynthion = parse_utc(
        PERICYNTHION_UTC
    )

    return {
        "geometry_window": {
            "start_utc": GEOMETRY_START,
            "stop_utc": GEOMETRY_STOP,
        },
        "earth_occultation": {
            "partial_or_full_overlap_intervals": [
                interval_record(
                    interval[
                        0
                    ],
                    interval[
                        1
                    ],
                    launch,
                    (
                        "EARTH_LUNAR_LIMB_"
                        "OVERLAP"
                    ),
                )
                for interval
                in earth_overlap
            ],
            "full_occultation_intervals": [
                interval_record(
                    interval[
                        0
                    ],
                    interval[
                        1
                    ],
                    launch,
                    (
                        "EARTH_FULLY_OCCULTED_"
                        "BY_MOON"
                    ),
                )
                for interval
                in earth_full
            ],
            "reported_earthset_snapshot": (
                earthset_snapshot
            ),
            "reported_earthrise_snapshot": (
                earthrise_snapshot
            ),
            "reported_earthset_utc": (
                EARTHSET_REPORTED_UTC
            ),
            "reported_earthrise_utc": (
                EARTHRISE_REPORTED_UTC
            ),
            "reported_times_equal_derived_contact_times": (
                False
            ),
            "reason": (
                "NASA image times are preserved as "
                "reported observations. MissionLab's "
                "geometric contact times are separately "
                "derived and are not substituted for "
                "the published image timestamps."
            ),
        },
        "solar_eclipse": {
            "partial_or_total_overlap_intervals": [
                interval_record(
                    interval[
                        0
                    ],
                    interval[
                        1
                    ],
                    launch,
                    (
                        "SOLAR_LUNAR_LIMB_"
                        "OVERLAP"
                    ),
                )
                for interval
                in sun_overlap
            ],
            "totality_intervals": [
                interval_record(
                    interval[
                        0
                    ],
                    interval[
                        1
                    ],
                    launch,
                    "TOTAL_SOLAR_ECLIPSE",
                )
                for interval
                in sun_full
            ],
            "nasa_reported_duration": {
                "description": (
                    "nearly 54 minutes"
                ),
                "exact": False,
            },
            "derived_totality_is_nasa_reported_duration": (
                False
            ),
        },
        "pericynthion": {
            "utc": (
                format_utc(
                    pericynthion
                )
            ),
            "met": (
                met_string(
                    pericynthion,
                    launch,
                )
            ),
            "provenance": (
                "MISSIONLAB_DERIVED_PREVIOUS_PHASE"
            ),
        },
    }


def lro_context_registry() -> list[dict]:
    return [
        {
            "context_id": (
                "LRO_CONTEXT_ORIENTALE"
            ),
            "target": (
                "Orientale Basin"
            ),
            "mission": (
                "Lunar Reconnaissance Orbiter"
            ),
            "products": [
                {
                    "instrument": (
                        "LROC WAC"
                    ),
                    "role": (
                        "global imaging and labeled "
                        "basin context used to locate "
                        "Artemis II crew imagery"
                    ),
                },
                {
                    "instrument": (
                        "LOLA"
                    ),
                    "role": (
                        "topography and surface "
                        "roughness context"
                    ),
                },
                {
                    "instrument": (
                        "Diviner"
                    ),
                    "role": (
                        "rock-abundance context"
                    ),
                },
                {
                    "instrument": (
                        "LOLA"
                    ),
                    "role": (
                        "surface-brightness / "
                        "albedo context"
                    ),
                },
            ],
            "postflight_integration": (
                "NASA's preliminary science report "
                "matches Artemis II crew imagery to "
                "precise lunar locations and compares "
                "the observations with LRO-derived "
                "maps and measurements."
            ),
            "source_url": (
                "https://science.nasa.gov/feature/"
                "artemis-ii-preliminary-lunar-science-report/"
            ),
        },
        {
            "context_id": (
                "LRO_CONTEXT_HERTZSPRUNG"
            ),
            "target": (
                "Hertzsprung Basin"
            ),
            "mission": (
                "Lunar Reconnaissance Orbiter"
            ),
            "products": [
                {
                    "instrument": (
                        "LROC NAC"
                    ),
                    "product_id": (
                        "M112421089RE"
                    ),
                    "role": (
                        "high-resolution context "
                        "for the Hertzsprung inner ring"
                    ),
                },
            ],
            "context": (
                "NASA's LRO context identifies "
                "Hertzsprung as an ancient farside "
                "basin and documents high-resolution "
                "inner-ring observations."
            ),
            "source_url": (
                "https://science.nasa.gov/"
                "photojournal/"
                "hertzsprung-constellation-site/"
            ),
        },
        {
            "context_id": (
                "TARGET_CONTEXT_VAVILOV"
            ),
            "target": (
                "Vavilov Crater"
            ),
            "context_source": (
                "USGS Gazetteer of Planetary Nomenclature"
            ),
            "feature_id": 6336,
            "center_latitude_deg": (
                VAVILOV_LAT_DEG
            ),
            "center_longitude_deg": (
                VAVILOV_LON_DEG
            ),
            "diameter_km": (
                VAVILOV_DIAMETER_KM
            ),
            "relationship": (
                "Vavilov is superimposed on the "
                "older Hertzsprung basin and was a "
                "named Artemis II terminator target."
            ),
            "source_url": (
                "https://planetarynames.wr.usgs.gov/"
                "Feature/6336"
            ),
        },
    ]


def selected_product_registry() -> list[dict]:
    return [
        {
            "product_id": (
                "art002e009288"
            ),
            "product_type": (
                "NASA_PUBLIC_IMAGE"
            ),
            "observation_id": (
                "A2_LUNAR_EARTHSET"
            ),
            "capture_time_utc": (
                EARTHSET_REPORTED_UTC
            ),
            "time_precision": (
                "MINUTE_IN_NASA_PUBLIC_RELEASE"
            ),
            "target": (
                "Earth / lunar limb"
            ),
            "view_direction": (
                "from Orion toward Earth "
                "across the lunar limb"
            ),
            "source": (
                "NASA Artemis II Lunar Flyby gallery"
            ),
        },
        {
            "product_id": (
                "art002e021278"
            ),
            "product_type": (
                "NASA_PUBLIC_IMAGE"
            ),
            "observation_id": (
                "A2_LUNAR_EARTHRISE"
            ),
            "capture_time_utc": (
                EARTHRISE_REPORTED_UTC
            ),
            "time_precision": (
                "MINUTE_IN_NASA_PUBLIC_RELEASE"
            ),
            "target": (
                "Earth / lunar limb"
            ),
            "view_direction": (
                "from Orion toward Earth "
                "across the lunar limb"
            ),
            "source": (
                "NASA Artemis II Lunar Flyby gallery"
            ),
        },
        {
            "product_id": (
                "art002e009282"
            ),
            "product_type": (
                "NASA_PUBLIC_IMAGE"
            ),
            "observation_id": (
                "A2_LUNAR_TERMINATOR_VAVILOV"
            ),
            "capture_time_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "DATE_ONLY_IN_CURATED_PUBLIC_SOURCE"
            ),
            "target": (
                "Vavilov Crater / "
                "Hertzsprung Basin"
            ),
            "view_direction": (
                "handheld 400 mm observation "
                "toward lunar farside terrain "
                "near the terminator"
            ),
            "source": (
                "NASA Artemis II Moon flyby release"
            ),
        },
        {
            "product_id": (
                "art002e009301"
            ),
            "product_type": (
                "NASA_PUBLIC_IMAGE"
            ),
            "observation_id": (
                "A2_LUNAR_SOLAR_ECLIPSE"
            ),
            "capture_time_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "DATE_ONLY_IN_CURATED_PUBLIC_SOURCE"
            ),
            "target": (
                "Sun behind lunar limb"
            ),
            "view_direction": (
                "from Orion toward the Sun "
                "through the lunar occultation geometry"
            ),
            "source": (
                "NASA Artemis II Moon flyby release"
            ),
        },
        {
            "product_id": (
                "015A9930.NEF"
            ),
            "product_type": (
                "NASA_POSTFLIGHT_CREW_IMAGE"
            ),
            "observation_id": (
                "A2_LUNAR_TERMINATOR_GENERAL"
            ),
            "capture_time_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "DATE_ONLY_ON_PUBLIC_HIGHLIGHT_PAGE"
            ),
            "target": (
                "lunar terminator / Carnot region"
            ),
            "view_direction": (
                "crew handheld view toward "
                "low-angle illuminated lunar terrain"
            ),
            "source": (
                "NASA Artemis II Preliminary "
                "Lunar Science Report"
            ),
        },
        {
            "product_id": (
                "019A0860.NEF"
            ),
            "product_type": (
                "NASA_POSTFLIGHT_CREW_IMAGE"
            ),
            "observation_id": (
                "A2_LUNAR_ECLIPSE_CORONA"
            ),
            "capture_time_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "DATE_ONLY_ON_PUBLIC_HIGHLIGHT_PAGE"
            ),
            "target": (
                "solar eclipse / lunar limb"
            ),
            "view_direction": (
                "toward the occulted Sun "
                "at the lunar limb"
            ),
            "source": (
                "NASA Artemis II Preliminary "
                "Lunar Science Report"
            ),
        },
    ]


def audio_annotation_registry() -> list[dict]:
    return [
        {
            "record_id": (
                "AUDIO_OBSERVING_EARTHSET"
            ),
            "title": (
                "Observing Earthset"
            ),
            "record_type": (
                "PUBLIC_SCIENCE_AUDIO"
            ),
            "observation_ids": [
                "A2_LUNAR_EARTHSET",
            ],
            "exact_audio_start_utc_curated_here": (
                False
            ),
        },
        {
            "record_id": (
                "AUDIO_VAVILOV_COLOR_TERRAIN"
            ),
            "title": (
                "Vavilov Crater: Color and Terrain"
            ),
            "record_type": (
                "PUBLIC_SCIENCE_AUDIO"
            ),
            "observation_ids": [
                (
                    "A2_LUNAR_TERMINATOR_VAVILOV"
                ),
            ],
            "exact_audio_start_utc_curated_here": (
                False
            ),
        },
        {
            "record_id": (
                "AUDIO_TERMINATOR_CRATERS_ELEVATION"
            ),
            "title": (
                "Terminator: Craters and Elevation"
            ),
            "record_type": (
                "PUBLIC_SCIENCE_AUDIO"
            ),
            "observation_ids": [
                (
                    "A2_LUNAR_TERMINATOR_GENERAL"
                ),
            ],
            "exact_audio_start_utc_curated_here": (
                False
            ),
        },
        {
            "record_id": (
                "AUDIO_RUMINATIONS_TERMINATOR"
            ),
            "title": (
                "Ruminations on the Terminator"
            ),
            "record_type": (
                "PUBLIC_SCIENCE_AUDIO"
            ),
            "observation_ids": [
                (
                    "A2_LUNAR_TERMINATOR_GENERAL"
                ),
            ],
            "exact_audio_start_utc_curated_here": (
                False
            ),
        },
        {
            "record_id": (
                "AUDIO_SEARCH_IMPACT_FLASH_DUST"
            ),
            "title": (
                "Searching for Impact Flashes "
                "and Lofted Dust"
            ),
            "record_type": (
                "PUBLIC_SCIENCE_AUDIO"
            ),
            "observation_ids": [
                (
                    "A2_LUNAR_IMPACT_FLASH_REPORT"
                ),
            ],
            "exact_audio_start_utc_curated_here": (
                False
            ),
        },
        {
            "record_id": (
                "ANNOTATION_IMPACT_FLASHES"
            ),
            "title": (
                "Crew tablet impact-flash annotation"
            ),
            "record_type": (
                "CREW_ANNOTATION"
            ),
            "observation_ids": [
                (
                    "A2_LUNAR_IMPACT_FLASH_REPORT"
                ),
            ],
            "reference_visualization_utc": (
                "2026-04-07T01:04:00Z"
            ),
            "reference_visualization_time_is_flash_time": (
                False
            ),
            "crew_participants": [
                "Reid Wiseman",
                "Victor Glover",
                "Jeremy Hansen",
            ],
            "postflight_confirmed_flash_count": (
                5
            ),
        },
        {
            "record_id": (
                "ANNOTATION_CORONA_STREAMER"
            ),
            "title": (
                "Crew tablet solar-corona annotation"
            ),
            "record_type": (
                "CREW_ANNOTATION"
            ),
            "observation_ids": [
                (
                    "A2_LUNAR_ECLIPSE_CORONA"
                ),
            ],
            "crew_participants": [
                "Jeremy Hansen",
            ],
            "summary": (
                "Annotation records a changing "
                "coronal streamer observed during "
                "the lunar occultation of the Sun."
            ),
        },
    ]


def build_observation_records(
    geometry: dict,
) -> list[dict]:
    earthset_geometry = geometry[
        "earth_occultation"
    ][
        "reported_earthset_snapshot"
    ]

    earthrise_geometry = geometry[
        "earth_occultation"
    ][
        "reported_earthrise_snapshot"
    ]

    eclipse_totality = geometry[
        "solar_eclipse"
    ][
        "totality_intervals"
    ]

    return [
        {
            "observation_id": (
                "A2_LUNAR_EARTHSET"
            ),
            "observation_class": (
                "EARTH_IMAGERY"
            ),
            "evidence_state": (
                "NASA_REPORTED_PLUS_"
                "MISSIONLAB_GEOMETRY_CORRELATION"
            ),
            "reported_utc": (
                EARTHSET_REPORTED_UTC
            ),
            "time_precision": (
                "NASA_REPORTED_MINUTE"
            ),
            "image_ids": [
                "art002e009288",
            ],
            "audio_records": [
                (
                    "AUDIO_OBSERVING_EARTHSET"
                ),
            ],
            "target": (
                "Earth / lunar limb"
            ),
            "view_direction": (
                "Orion toward Earth "
                "across lunar limb"
            ),
            "crew_remark_summary": (
                "Public science audio records "
                "crew observations of Earthset."
            ),
            "geometry_status_at_reported_time": (
                earthset_geometry[
                    "status"
                ]
            ),
            "geometry_link": (
                "earth_occultation"
            ),
            "confirmed_observation": (
                True
            ),
        },
        {
            "observation_id": (
                "A2_LUNAR_EARTHRISE"
            ),
            "observation_class": (
                "EARTH_IMAGERY"
            ),
            "evidence_state": (
                "NASA_REPORTED_PLUS_"
                "MISSIONLAB_GEOMETRY_CORRELATION"
            ),
            "reported_utc": (
                EARTHRISE_REPORTED_UTC
            ),
            "time_precision": (
                "NASA_REPORTED_MINUTE"
            ),
            "image_ids": [
                "art002e021278",
            ],
            "audio_records": [],
            "target": (
                "Earth / lunar limb"
            ),
            "view_direction": (
                "Orion toward Earth "
                "re-emerging beyond lunar limb"
            ),
            "crew_remark_summary": (
                "NASA publicly identified the "
                "image as Artemis-era Earthrise."
            ),
            "geometry_status_at_reported_time": (
                earthrise_geometry[
                    "status"
                ]
            ),
            "geometry_link": (
                "earth_occultation"
            ),
            "confirmed_observation": (
                True
            ),
        },
        {
            "observation_id": (
                "A2_LUNAR_TERMINATOR_VAVILOV"
            ),
            "observation_class": (
                "TERMINATOR_OBSERVATION"
            ),
            "evidence_state": (
                "NASA_REPORTED"
            ),
            "reported_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "DATE_ONLY_IN_CURATED_SOURCE"
            ),
            "image_ids": [
                "art002e009282",
            ],
            "audio_records": [
                (
                    "AUDIO_VAVILOV_COLOR_TERRAIN"
                ),
            ],
            "target": (
                "Vavilov Crater / "
                "Hertzsprung Basin"
            ),
            "view_direction": (
                "toward farside lunar terrain "
                "near the terminator"
            ),
            "crew_remark_summary": (
                "Crew observations emphasized "
                "terrain relief, color, albedo, "
                "and structure under low-angle light."
            ),
            "lro_context_ids": [
                (
                    "LRO_CONTEXT_HERTZSPRUNG"
                ),
                (
                    "TARGET_CONTEXT_VAVILOV"
                ),
            ],
            "exact_image_time_inferred": (
                False
            ),
            "confirmed_observation": (
                True
            ),
        },
        {
            "observation_id": (
                "A2_LUNAR_TERMINATOR_GENERAL"
            ),
            "observation_class": (
                "TERMINATOR_OBSERVATION"
            ),
            "evidence_state": (
                "NASA_POSTFLIGHT_REPORTED"
            ),
            "reported_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "DATE_ONLY_IN_CURATED_SOURCE"
            ),
            "image_ids": [
                "015A9930.NEF",
            ],
            "audio_records": [
                (
                    "AUDIO_TERMINATOR_CRATERS_ELEVATION"
                ),
                (
                    "AUDIO_RUMINATIONS_TERMINATOR"
                ),
            ],
            "target": (
                "lunar terminator terrain"
            ),
            "view_direction": (
                "toward low-angle illuminated "
                "lunar surface"
            ),
            "crew_remark_summary": (
                "Victor Glover described the "
                "terminator as the most striking "
                "view he had seen to that point. "
                "Christina Koch noted that mountain "
                "relief was visible along the limb."
            ),
            "confirmed_observation": (
                True
            ),
        },
        {
            "observation_id": (
                "A2_LUNAR_SOLAR_ECLIPSE"
            ),
            "observation_class": (
                "ECLIPSE_OBSERVATION"
            ),
            "evidence_state": (
                "NASA_REPORTED_PLUS_"
                "MISSIONLAB_GEOMETRY_RECONSTRUCTION"
            ),
            "reported_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "NO_EXACT_PUBLIC_START_STOP_"
                "USED_AS_TELEMETRY"
            ),
            "image_ids": [
                "art002e009301",
                "019A0860.NEF",
            ],
            "audio_records": [],
            "target": (
                "Sun behind lunar disk"
            ),
            "view_direction": (
                "Orion toward Sun "
                "through lunar occultation"
            ),
            "crew_remark_summary": (
                "Crew observed the prolonged "
                "total eclipse and faint structures "
                "normally overwhelmed by sunlight."
            ),
            "derived_totality_intervals": (
                eclipse_totality
            ),
            "nasa_reported_duration": (
                "nearly 54 minutes"
            ),
            "confirmed_observation": (
                True
            ),
        },
        {
            "observation_id": (
                "A2_LUNAR_ECLIPSE_CORONA"
            ),
            "observation_class": (
                "ECLIPSE_CORONA_OBSERVATION"
            ),
            "evidence_state": (
                "POSTFLIGHT_SCIENCE_"
                "INTERPRETATION"
            ),
            "reported_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "WITHIN_ECLIPSE_WINDOW_"
                "EXACT_REMARK_TIME_NOT_ASSIGNED"
            ),
            "image_ids": [
                "019A0860.NEF",
            ],
            "audio_records": [
                (
                    "ANNOTATION_CORONA_STREAMER"
                ),
            ],
            "target": (
                "solar corona / lunar limb"
            ),
            "view_direction": (
                "toward the occulted Sun"
            ),
            "crew_remark_summary": (
                "Postflight report identifies "
                "coronal structure, including a "
                "changing streamer, and separately "
                "reports zodiacal light."
            ),
            "source_evolution": {
                "early_status": (
                    "HALO_UNDER_INVESTIGATION"
                ),
                "postflight_status": (
                    "CORONAL_STRUCTURE_AND_"
                    "ZODIACAL_LIGHT_REPORTED"
                ),
            },
            "confirmed_observation": (
                True
            ),
        },
        {
            "observation_id": (
                "A2_LUNAR_IMPACT_FLASH_REPORT"
            ),
            "observation_class": (
                "IMPACT_FLASH_OBSERVATION"
            ),
            "evidence_state": (
                "POSTFLIGHT_RECONCILED"
            ),
            "reported_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "INDIVIDUAL_FLASH_TIMES_"
                "NOT_ASSIGNED"
            ),
            "image_ids": [],
            "audio_records": [
                (
                    "AUDIO_SEARCH_IMPACT_FLASH_DUST"
                ),
                (
                    "ANNOTATION_IMPACT_FLASHES"
                ),
            ],
            "target": (
                "dark lunar surface"
            ),
            "view_direction": (
                "toward eclipsed / night-side "
                "lunar disk"
            ),
            "crew_remark_summary": (
                "Three crew members annotated "
                "extremely faint impact flashes. "
                "Two crew members independently "
                "described seeing one flash together."
            ),
            "source_evolution": {
                "early_reported_count": (
                    6
                ),
                "early_report_date": (
                    "2026-04-07"
                ),
                "postflight_reported_count": (
                    5
                ),
                "postflight_report_date": (
                    "2026-10-07"
                ),
                "missionlab_final_count": (
                    5
                ),
                "selection_basis": (
                    "The October 7 postflight "
                    "preliminary science report "
                    "states that five flashes were "
                    "reported and that other candidate "
                    "sources such as cosmic rays or "
                    "spacecraft reflections were ruled out."
                ),
            },
            "reference_annotation_utc": (
                "2026-04-07T01:04:00Z"
            ),
            "reference_annotation_utc_is_flash_time": (
                False
            ),
            "within_total_eclipse_context": (
                True
            ),
            "confirmed_observation": (
                True
            ),
        },
        {
            "observation_id": (
                "A2_LRO_ORIENTALE_CONTEXT"
            ),
            "observation_class": (
                "LRO_CONTEXT_INTEGRATION"
            ),
            "evidence_state": (
                "NASA_POSTFLIGHT_CONTEXT"
            ),
            "reported_utc": None,
            "reported_date": (
                "2026-04-06"
            ),
            "time_precision": (
                "CONTEXT_NOT_SINGLE_EVENT"
            ),
            "image_ids": [],
            "audio_records": [],
            "target": (
                "Orientale Basin"
            ),
            "view_direction": (
                "crew lunar-surface observations "
                "correlated with orbital context products"
            ),
            "lro_context_ids": [
                (
                    "LRO_CONTEXT_ORIENTALE"
                ),
            ],
            "crew_remark_summary": (
                "Postflight science analysis "
                "compares crew imagery with LRO "
                "imaging, topography, roughness, "
                "rock abundance, and brightness context."
            ),
            "confirmed_observation": (
                True
            ),
        },
    ]


def write_observation_csv(
    observations: list[dict],
):
    fieldnames = [
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

    with OUTPUT_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for item in observations:
            writer.writerow(
                {
                    "observation_id": (
                        item[
                            "observation_id"
                        ]
                    ),
                    "observation_class": (
                        item[
                            "observation_class"
                        ]
                    ),
                    "evidence_state": (
                        item[
                            "evidence_state"
                        ]
                    ),
                    "reported_utc": (
                        item.get(
                            "reported_utc"
                        )
                        or ""
                    ),
                    "reported_date": (
                        item.get(
                            "reported_date"
                        )
                        or ""
                    ),
                    "time_precision": (
                        item[
                            "time_precision"
                        ]
                    ),
                    "target": (
                        item[
                            "target"
                        ]
                    ),
                    "view_direction": (
                        item[
                            "view_direction"
                        ]
                    ),
                    "image_ids": (
                        "|".join(
                            item.get(
                                "image_ids",
                                [],
                            )
                        )
                    ),
                    "audio_records": (
                        "|".join(
                            item.get(
                                "audio_records",
                                [],
                            )
                        )
                    ),
                    "crew_remark_summary": (
                        item[
                            "crew_remark_summary"
                        ]
                    ),
                    "confirmed_observation": (
                        item[
                            "confirmed_observation"
                        ]
                    ),
                }
            )


def build_figure(
    geometry: dict,
    launch: datetime,
):
    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    earth_full = geometry[
        "earth_occultation"
    ][
        "full_occultation_intervals"
    ]

    eclipse_total = geometry[
        "solar_eclipse"
    ][
        "totality_intervals"
    ]

    fig, ax = plt.subplots(
        figsize=(
            14,
            6,
        )
    )

    y_earth = 2.0
    y_eclipse = 1.0

    for interval in earth_full:
        start = parse_utc(
            interval[
                "start_utc"
            ]
        )

        stop = parse_utc(
            interval[
                "stop_utc"
            ]
        )

        ax.plot(
            [
                (
                    start
                    - launch
                ).total_seconds()
                / 3600.0,
                (
                    stop
                    - launch
                ).total_seconds()
                / 3600.0,
            ],
            [
                y_earth,
                y_earth,
            ],
            linewidth=8,
            solid_capstyle="butt",
        )

    for interval in eclipse_total:
        start = parse_utc(
            interval[
                "start_utc"
            ]
        )

        stop = parse_utc(
            interval[
                "stop_utc"
            ]
        )

        ax.plot(
            [
                (
                    start
                    - launch
                ).total_seconds()
                / 3600.0,
                (
                    stop
                    - launch
                ).total_seconds()
                / 3600.0,
            ],
            [
                y_eclipse,
                y_eclipse,
            ],
            linewidth=8,
            solid_capstyle="butt",
        )

    marker_records = [
        (
            EARTHSET_REPORTED_UTC,
            y_earth,
            "NASA Earthset",
        ),
        (
            EARTHRISE_REPORTED_UTC,
            y_earth,
            "NASA Earthrise",
        ),
        (
            PERICYNTHION_UTC,
            1.5,
            "Pericynthion",
        ),
    ]

    for (
        utc,
        y_value,
        label,
    ) in marker_records:
        timestamp = parse_utc(
            utc
        )

        x_value = (
            timestamp
            - launch
        ).total_seconds() / 3600.0

        ax.scatter(
            [
                x_value
            ],
            [
                y_value
            ],
            s=40,
        )

        ax.annotate(
            label,
            (
                x_value,
                y_value,
            ),
            xytext=(
                4,
                8,
            ),
            textcoords=(
                "offset points"
            ),
            fontsize=8,
        )

    ax.set_yticks(
        [
            y_eclipse,
            y_earth,
        ]
    )

    ax.set_yticklabels(
        [
            (
                "Derived total "
                "solar eclipse"
            ),
            (
                "Derived full "
                "Earth occultation"
            ),
        ]
    )

    ax.set_xlabel(
        "Mission elapsed time (hours)"
    )

    ax.set_title(
        (
            "Artemis II Lunar Observation "
            "Geometry Reconstruction"
        )
    )

    ax.grid(
        True,
        axis="x",
        alpha=0.25,
    )

    fig.text(
        0.5,
        0.015,
        (
            "Geometry is MissionLab-derived from "
            "NASA flight-derived OEM states and SPICE. "
            "Reported image times remain NASA-reported "
            "observations and are not replaced by "
            "derived contact times."
        ),
        ha="center",
        fontsize=8,
    )

    fig.tight_layout(
        rect=(
            0,
            0.05,
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


def build_result(
    archive: dict,
    geometry: dict,
    observations: list[dict],
    products: list[dict],
    audio_annotations: list[dict],
    lro_context: list[dict],
) -> dict:
    return {
        "dataset_id": (
            "phase6b_artemis_ii_"
            "lunar_observation_reconstruction"
        ),
        "mission": (
            "Artemis II"
        ),
        "phase": (
            "6B"
        ),
        "status": (
            "LUNAR_SCIENCE_OBSERVATION_"
            "RECONSTRUCTION_COMPLETE"
        ),
        "dependencies": {
            "phase6a_dataset_id": (
                archive[
                    "dataset_id"
                ]
            ),
            "flight_derived_trajectory": (
                "data/processed/trajectory/"
                "trajectory_with_mission_phases.csv"
            ),
            "spice_kernels": [
                "naif0012.tls",
                "de440s.bsp",
                "pck00011.tpc",
            ],
        },
        "selected_product_registry": (
            products
        ),
        "audio_annotation_registry": (
            audio_annotations
        ),
        "observation_records": (
            observations
        ),
        "geometry_reconstruction": (
            geometry
        ),
        "lro_context_registry": (
            lro_context
        ),
        "impact_flash_reconciliation": {
            "early_public_count": (
                6
            ),
            "early_publication_date": (
                "2026-04-07"
            ),
            "postflight_confirmed_count": (
                5
            ),
            "postflight_publication_date": (
                "2026-10-07"
            ),
            "missionlab_final_science_count": (
                5
            ),
            "status": (
                "RESOLVED_BY_LATER_"
                "POSTFLIGHT_SCIENCE_REPORT"
            ),
            "early_report_erased": (
                False
            ),
            "reason": (
                "The later postflight preliminary "
                "science report explicitly reports "
                "five flashes and states that other "
                "candidate causes were ruled out. "
                "MissionLab therefore uses five as "
                "the postflight science result while "
                "retaining the earlier six-flash "
                "public report as source evolution."
            ),
        },
        "eclipse_interpretation_reconciliation": {
            "early_public_status": (
                "HALO_UNDER_INVESTIGATION"
            ),
            "postflight_status": (
                "CORONAL_STRUCTURE_AND_"
                "ZODIACAL_LIGHT_REPORTED"
            ),
            "status": (
                "RESOLVED_BY_LATER_"
                "POSTFLIGHT_SCIENCE_REPORT"
            ),
            "early_uncertainty_erased": (
                False
            ),
        },
        "roadmap_assessment": {
            "index_pds_crew_imagery_metadata": (
                "COMPLETE_AT_COLLECTION_AND_"
                "SELECTED_SCIENCE_PRODUCT_LEVEL"
            ),
            "index_pds_orion_imagery_metadata": (
                "COMPLETE_AT_COLLECTION_AND_"
                "SELECTED_SCIENCE_PRODUCT_LEVEL"
            ),
            "index_mission_audio_transcripts_annotations": (
                "COMPLETE_AT_COLLECTION_AND_"
                "SELECTED_OBSERVATION_LEVEL"
            ),
            "connect_time_view_image_remark_target": (
                "COMPLETE_FOR_RECONSTRUCTED_"
                "SCIENCE_OBSERVATIONS"
            ),
            "integrate_public_lro_context": (
                "COMPLETE_FOR_SELECTED_TARGETS"
            ),
            "reconstruct_impact_flash_observations": (
                "COMPLETE"
            ),
            "reconstruct_terminator_observations": (
                "COMPLETE"
            ),
            "reconstruct_eclipse_corona_observations": (
                "COMPLETE"
            ),
            "reconstruct_earth_imagery_analysis": (
                "COMPLETE"
            ),
            "phase6_overall": (
                "COMPLETE_RELATIVE_TO_"
                "DEFENSIBLE_PUBLIC_POSTFLIGHT_EVIDENCE"
            ),
        },
        "critical_non_equivalences": [
            {
                "left": (
                    "REPORTED_IMAGE_TIME"
                ),
                "right": (
                    "DERIVED_GEOMETRIC_CONTACT_TIME"
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
                    "TARGETING_PLAN_OPPORTUNITY"
                ),
                "right": (
                    "CONFIRMED_OBSERVATION"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "REFERENCE_ANNOTATION_TIME"
                ),
                "right": (
                    "INDIVIDUAL_IMPACT_FLASH_TIME"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "EARLY_SIX_FLASH_REPORT"
                ),
                "right": (
                    "POSTFLIGHT_FIVE_FLASH_RESULT"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "EARLY_HALO_UNCERTAINTY"
                ),
                "right": (
                    "POSTFLIGHT_CORONAL_INTERPRETATION"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "LRO_CONTEXT_PRODUCT"
                ),
                "right": (
                    "ARTEMIS_II_CREW_IMAGE"
                ),
                "equivalent": False,
            },
            {
                "left": (
                    "MISSIONLAB_GEOMETRY"
                ),
                "right": (
                    "ONBOARD_ORION_TELEMETRY"
                ),
                "equivalent": False,
            },
        ],
        "outputs": {
            "reference_json": (
                "data/reference/"
                "artemis_ii_lunar_observation_reconstruction.json"
            ),
            "processed_json": (
                "data/processed/lunar_science/"
                "artemis_ii_lunar_observation_reconstruction.json"
            ),
            "observation_csv": (
                "data/processed/lunar_science/"
                "artemis_ii_lunar_observation_correlations.csv"
            ),
            "figure": (
                "docs/assets/lunar_science/"
                "phase6b_lunar_observation_reconstruction.svg"
            ),
        },
    }


def main():
    print()
    print(
        "Phase 6B Artemis II Lunar Observation "
        "Reconstruction and Phase 6 Closure"
    )
    print(
        "=" * 72
    )

    mission = load_json(
        MISSION_PATH
    )

    archive = load_json(
        PHASE6A_PATH
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
        archive.get(
            "dataset_id"
        )
        == (
            "phase6a_artemis_ii_"
            "lunar_science_archive_index"
        ),
        "Phase 6A dependency mismatch",
    )

    launch = parse_utc(
        mission[
            "launch_epoch_utc"
        ]
    )

    (
        times,
        positions,
    ) = prepare_trajectory(
        trajectory_rows
    )

    print()
    print(
        "Dependencies:"
    )
    print(
        "  Phase 6A archive index: PASS"
    )
    print(
        "  flight-derived trajectory: PASS"
    )
    print(
        "  trajectory states: "
        f"{len(trajectory_rows)}"
    )

    load_spice()

    try:
        radii = get_body_radii()

        geometry = build_geometry(
            launch,
            times,
            positions,
            radii,
        )

    finally:
        spice.kclear()

    products = (
        selected_product_registry()
    )

    audio_annotations = (
        audio_annotation_registry()
    )

    lro_context = (
        lro_context_registry()
    )

    observations = (
        build_observation_records(
            geometry
        )
    )

    require(
        len(
            products
        )
        == 6,
        (
            "expected 6 selected image "
            f"products, found {len(products)}"
        ),
    )

    require(
        len(
            audio_annotations
        )
        == 7,
        (
            "expected 7 audio/annotation "
            f"records, found {len(audio_annotations)}"
        ),
    )

    require(
        len(
            lro_context
        )
        == 3,
        (
            "expected 3 selected target "
            f"context records, found {len(lro_context)}"
        ),
    )

    require(
        len(
            observations
        )
        == 8,
        (
            "expected 8 reconstructed "
            f"observation records, found {len(observations)}"
        ),
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REFERENCE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_observation_csv(
        observations
    )

    build_figure(
        geometry,
        launch,
    )

    result = build_result(
        archive,
        geometry,
        observations,
        products,
        audio_annotations,
        lro_context,
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

        f.write(
            "\n"
        )

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

    earth_full = geometry[
        "earth_occultation"
    ][
        "full_occultation_intervals"
    ]

    eclipse_total = geometry[
        "solar_eclipse"
    ][
        "totality_intervals"
    ]

    print()
    print(
        "Selected public science products:"
    )
    print(
        "  image products: "
        f"{len(products)}"
    )
    print(
        "  audio / annotation records: "
        f"{len(audio_annotations)}"
    )
    print(
        "  reconstructed observation records: "
        f"{len(observations)}"
    )

    print()
    print(
        "Earth / lunar-limb geometry:"
    )
    print(
        "  NASA Earthset: "
        + EARTHSET_REPORTED_UTC
    )
    print(
        "  Earthset geometry status: "
        + geometry[
            "earth_occultation"
        ][
            "reported_earthset_snapshot"
        ][
            "status"
        ]
    )
    print(
        "  NASA Earthrise: "
        + EARTHRISE_REPORTED_UTC
    )
    print(
        "  Earthrise geometry status: "
        + geometry[
            "earth_occultation"
        ][
            "reported_earthrise_snapshot"
        ][
            "status"
        ]
    )
    print(
        "  full Earth-occultation intervals: "
        f"{len(earth_full)}"
    )

    for interval in earth_full:
        print(
            "    "
            + interval[
                "start_utc"
            ]
            + " -> "
            + interval[
                "stop_utc"
            ]
            + "  "
            + f"({interval['duration_minutes']:.2f} min)"
        )

    print()
    print(
        "Solar-eclipse geometry:"
    )
    print(
        "  totality intervals: "
        f"{len(eclipse_total)}"
    )

    for interval in eclipse_total:
        print(
            "    "
            + interval[
                "start_utc"
            ]
            + " -> "
            + interval[
                "stop_utc"
            ]
            + "  "
            + f"({interval['duration_minutes']:.2f} min)"
        )

    print(
        "  NASA reported duration: "
        "nearly 54 minutes"
    )
    print(
        "  derived interval == onboard "
        "event telemetry: NO"
    )

    print()
    print(
        "Impact-flash reconciliation:"
    )
    print(
        "  Apr 7 early public count: 6"
    )
    print(
        "  Oct 7 postflight confirmed count: 5"
    )
    print(
        "  MissionLab final science count: 5"
    )
    print(
        "  early report preserved: YES"
    )
    print(
        "  individual flash times fabricated: NO"
    )

    print()
    print(
        "Eclipse interpretation reconciliation:"
    )
    print(
        "  early public halo status: "
        "UNDER INVESTIGATION"
    )
    print(
        "  postflight science result: "
        "CORONAL STRUCTURE + ZODIACAL LIGHT"
    )
    print(
        "  early uncertainty preserved: YES"
    )

    print()
    print(
        "Selected LRO / target context:"
    )
    print(
        "  Orientale Basin: "
        "LROC / LOLA / Diviner context"
    )
    print(
        "  Hertzsprung Basin: "
        "LROC NAC M112421089RE"
    )
    print(
        "  Vavilov Crater: "
        f"{VAVILOV_LAT_DEG:.2f} deg, "
        f"{VAVILOV_LON_DEG:.2f} deg, "
        f"{VAVILOV_DIAMETER_KM:.2f} km"
    )

    print()
    print(
        "Critical boundaries:"
    )
    print(
        "  reported image time "
        "!= derived contact time"
    )
    print(
        "  image time "
        "!= crew remark time"
    )
    print(
        "  targeting opportunity "
        "!= confirmed observation"
    )
    print(
        "  annotation reference time "
        "!= individual flash time"
    )
    print(
        "  early 6-flash report "
        "!= postflight 5-flash result"
    )
    print(
        "  early halo uncertainty "
        "!= postflight interpretation"
    )
    print(
        "  LRO context "
        "!= Artemis II image"
    )
    print(
        "  MissionLab geometry "
        "!= onboard telemetry"
    )

    print()
    print(
        "Phase 6 roadmap:"
    )
    print(
        "  crew imagery indexing: COMPLETE"
    )
    print(
        "  Orion imagery indexing: COMPLETE"
    )
    print(
        "  audio / transcript / annotation indexing: COMPLETE"
    )
    print(
        "  time / view / image / remark / target links: COMPLETE"
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
            FIGURE_PATH.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 6B LUNAR OBSERVATION "
        "RECONSTRUCTION COMPLETE"
    )
    print(
        "PHASE 6 ROADMAP RECONSTRUCTION COMPLETE"
    )


if __name__ == "__main__":
    main()
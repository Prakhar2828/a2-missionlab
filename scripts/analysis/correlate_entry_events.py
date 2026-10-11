from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]

GEOMETRY_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_geometry.csv"
)

REFERENCE_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_events.json"
)

OUTPUT_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_event_correlations.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
)

FT_TO_KM = 0.0003048
FT_S_TO_KM_S = 0.0003048

KM_TO_MILES = (
    0.621371192237334
)

KM_S_TO_FT_S = (
    3280.83989501312
)

KM_S_TO_MPH = (
    2236.9362920544
)

EARTH_MEAN_RADIUS_KM = (
    6371.0088
)


plt.rcParams["svg.hashsalt"] = (
    "a2-missionlab"
)

SVG_METADATA = {
    "Date": None,
}


def normalize_svg(
    path: Path,
):
    text = path.read_text(
        encoding="utf-8"
    )

    cleaned = "\n".join(
        line.rstrip(" \t")
        for line in text.splitlines()
    ) + "\n"

    path.write_text(
        cleaned,
        encoding="utf-8",
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


def format_utc(
    value: datetime,
) -> str:
    return (
        value.isoformat(
            timespec="microseconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def interpolate_crossing(
    t0,
    y0,
    t1,
    y1,
    target,
):
    if y1 == y0:
        return float(
            t0
        )

    fraction = (
        target - y0
    ) / (
        y1 - y0
    )

    return float(
        t0
        + fraction
        * (
            t1 - t0
        )
    )


def first_descending_crossing(
    time_s,
    values,
    target,
    start_time_s=0.0,
):
    for i in range(
        1,
        len(values),
    ):
        if (
            time_s[i]
            < start_time_s
        ):
            continue

        if (
            values[i - 1] >= target
            and values[i] <= target
        ):
            return interpolate_crossing(
                time_s[i - 1],
                values[i - 1],
                time_s[i],
                values[i],
                target,
            )

    return None


def interp(
    time_s,
    values,
    target_time,
):
    return float(
        np.interp(
            target_time,
            time_s,
            values,
        )
    )


def haversine_km(
    lat1_deg,
    lon1_deg,
    lat2_deg,
    lon2_deg,
):
    lat1 = math.radians(
        lat1_deg
    )

    lat2 = math.radians(
        lat2_deg
    )

    dlat = (
        lat2 - lat1
    )

    dlon = math.radians(
        lon2_deg - lon1_deg
    )

    a = (
        math.sin(
            dlat / 2.0
        ) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(
            dlon / 2.0
        ) ** 2
    )

    return (
        2.0
        * EARTH_MEAN_RADIUS_KM
        * math.asin(
            math.sqrt(a)
        )
    )


def within_reported_minute(
    event_time,
    reported_minute,
):
    minute_start = parse_utc(
        reported_minute
    )

    offset_s = (
        event_time
        - minute_start
    ).total_seconds()

    return (
        float(offset_s),
        bool(
            0.0 <= offset_s < 60.0
        ),
    )


def event_state(
    start,
    elapsed_s,
    time_s,
    altitude,
    speed,
    latitude,
    longitude,
    distance_to_terminal,
):
    timestamp = (
        start
        + timedelta(
            seconds=float(
                elapsed_s
            )
        )
    )

    return {
        "utc":
            format_utc(
                timestamp
            ),

        "ei_elapsed_seconds":
            float(
                elapsed_s
            ),

        "wgs84_altitude_km":
            interp(
                time_s,
                altitude,
                elapsed_s,
            ),

        "earth_relative_speed_km_s":
            interp(
                time_s,
                speed,
                elapsed_s,
            ),

        "latitude_deg":
            interp(
                time_s,
                latitude,
                elapsed_s,
            ),

        "longitude_deg":
            interp(
                time_s,
                longitude,
                elapsed_s,
            ),

        "surface_distance_to_terminal_km":
            interp(
                time_s,
                distance_to_terminal,
                elapsed_s,
            ),
    }


def main():
    if not GEOMETRY_CSV.exists():
        raise SystemExit(
            f"Missing geometry file:\n"
            f"{GEOMETRY_CSV}"
        )

    if not REFERENCE_JSON.exists():
        raise SystemExit(
            f"Missing NASA event "
            f"reference:\n"
            f"{REFERENCE_JSON}"
        )

    with GEOMETRY_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        rows = list(
            csv.DictReader(f)
        )

    with REFERENCE_JSON.open(
        "r",
        encoding="utf-8",
    ) as f:
        reference = json.load(f)

    if len(rows) != 819:
        raise SystemExit(
            f"Expected 819 states, "
            f"found {len(rows)}"
        )

    event_reference = {
        item["event_id"]: item
        for item in reference[
            "events"
        ]
    }

    timestamps = [
        parse_utc(
            row[
                "timestamp_utc"
            ]
        )
        for row in rows
    ]

    start = timestamps[0]

    time_s = np.array(
        [
            (
                timestamp
                - start
            ).total_seconds()
            for timestamp
            in timestamps
        ],
        dtype=float,
    )

    altitude = np.array(
        [
            float(
                row[
                    "wgs84_altitude_km"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    speed = np.array(
        [
            float(
                row[
                    "earth_relative_speed_km_s"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    latitude = np.array(
        [
            float(
                row[
                    "geodetic_latitude_deg"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    longitude = np.array(
        [
            float(
                row[
                    "geodetic_longitude_deg"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    # --------------------------------------------------------
    # Derived splashdown-correlated surface crossing
    # --------------------------------------------------------

    surface_t = (
        first_descending_crossing(
            time_s,
            altitude,
            0.0,
        )
    )

    if surface_t is None:
        raise SystemExit(
            "No WGS84 zero-altitude "
            "crossing found."
        )

    surface_lat = interp(
        time_s,
        latitude,
        surface_t,
    )

    surface_lon = interp(
        time_s,
        longitude,
        surface_t,
    )

    distance_to_terminal = np.array(
        [
            haversine_km(
                lat,
                lon,
                surface_lat,
                surface_lon,
            )
            for lat, lon in zip(
                latitude,
                longitude,
            )
        ],
        dtype=float,
    )

    surface_state = event_state(
        start,
        surface_t,
        time_s,
        altitude,
        speed,
        latitude,
        longitude,
        distance_to_terminal,
    )

    # --------------------------------------------------------
    # Entry Interface
    # --------------------------------------------------------

    ei_ref = event_reference[
        "entry_interface"
    ]

    ei_altitude_km = (
        ei_ref[
            "reported_altitude_ft"
        ]
        * FT_TO_KM
    )

    ei_state = event_state(
        start,
        0.0,
        time_s,
        altitude,
        speed,
        latitude,
        longitude,
        distance_to_terminal,
    )

    ei_time = parse_utc(
        ei_state[
            "utc"
        ]
    )

    (
        ei_minute_offset,
        ei_minute_match,
    ) = within_reported_minute(
        ei_time,
        ei_ref[
            "reported_utc_minute"
        ],
    )

    ei_distance_miles = (
        ei_state[
            "surface_distance_to_terminal_km"
        ]
        * KM_TO_MILES
    )

    # --------------------------------------------------------
    # Drogue event anchor and associated conditions
    # --------------------------------------------------------

    drogue_ref = event_reference[
        "drogue_deploy"
    ]

    drogue_altitude_km = (
        drogue_ref[
            "reported_altitude_ft"
        ]
        * FT_TO_KM
    )

    drogue_anchor_t = (
        first_descending_crossing(
            time_s,
            altitude,
            drogue_altitude_km,
            start_time_s=500.0,
        )
    )

    if drogue_anchor_t is None:
        raise SystemExit(
            "Could not reconstruct "
            "drogue altitude crossing."
        )

    drogue_state = event_state(
        start,
        drogue_anchor_t,
        time_s,
        altitude,
        speed,
        latitude,
        longitude,
        distance_to_terminal,
    )

    (
        drogue_minute_offset,
        drogue_minute_match,
    ) = within_reported_minute(
        parse_utc(
            drogue_state[
                "utc"
            ]
        ),
        drogue_ref[
            "reported_utc_minute"
        ],
    )

    drogue_speed_target = (
        drogue_ref[
            "reported_speed_ft_s"
        ]
        * FT_S_TO_KM_S
    )

    drogue_speed_t = (
        first_descending_crossing(
            time_s,
            speed,
            drogue_speed_target,
            start_time_s=500.0,
        )
    )

    if drogue_speed_t is None:
        raise SystemExit(
            "Could not reconstruct "
            "479-ft/s crossing."
        )

    drogue_speed_state = event_state(
        start,
        drogue_speed_t,
        time_s,
        altitude,
        speed,
        latitude,
        longitude,
        distance_to_terminal,
    )

    drogue_distance_target_km = (
        drogue_ref[
            "reported_distance_to_splashdown_statute_miles"
        ]
        / KM_TO_MILES
    )

    drogue_distance_t = (
        first_descending_crossing(
            time_s,
            distance_to_terminal,
            drogue_distance_target_km,
            start_time_s=500.0,
        )
    )

    drogue_distance_state = None

    if drogue_distance_t is not None:
        drogue_distance_state = (
            event_state(
                start,
                drogue_distance_t,
                time_s,
                altitude,
                speed,
                latitude,
                longitude,
                distance_to_terminal,
            )
        )

    # --------------------------------------------------------
    # Main parachute event
    # --------------------------------------------------------

    main_ref = event_reference[
        "main_deploy"
    ]

    main_altitude_km = (
        main_ref[
            "reported_altitude_ft"
        ]
        * FT_TO_KM
    )

    main_anchor_t = (
        first_descending_crossing(
            time_s,
            altitude,
            main_altitude_km,
            start_time_s=600.0,
        )
    )

    if main_anchor_t is None:
        raise SystemExit(
            "Could not reconstruct "
            "main altitude crossing."
        )

    main_state = event_state(
        start,
        main_anchor_t,
        time_s,
        altitude,
        speed,
        latitude,
        longitude,
        distance_to_terminal,
    )

    (
        main_minute_offset,
        main_minute_match,
    ) = within_reported_minute(
        parse_utc(
            main_state[
                "utc"
            ]
        ),
        main_ref[
            "reported_utc_minute"
        ],
    )

    main_speed_target = (
        main_ref[
            "reported_speed_upper_ft_s"
        ]
        * FT_S_TO_KM_S
    )

    main_speed_t = (
        first_descending_crossing(
            time_s,
            speed,
            main_speed_target,
            start_time_s=main_anchor_t,
        )
    )

    if main_speed_t is None:
        raise SystemExit(
            "Could not reconstruct "
            "200-ft/s crossing."
        )

    main_speed_state = event_state(
        start,
        main_speed_t,
        time_s,
        altitude,
        speed,
        latitude,
        longitude,
        distance_to_terminal,
    )

    # --------------------------------------------------------
    # Splashdown public-minute correlation
    # --------------------------------------------------------

    splash_ref = event_reference[
        "splashdown"
    ]

    (
        splash_minute_offset,
        splash_minute_match,
    ) = within_reported_minute(
        parse_utc(
            surface_state[
                "utc"
            ]
        ),
        splash_ref[
            "reported_utc_minute"
        ],
    )

    # --------------------------------------------------------
    # Structured output
    # --------------------------------------------------------

    result = {
        "trajectory_provenance":
            "NASA flight-derived ephemeris",

        "reference_provenance":
            "NASA_REPORTED",

        "time_resolution_rule":
            (
                "NASA public event timestamps "
                "are treated as minute-resolution "
                "reports, not exact second-level "
                "telemetry epochs."
            ),

        "entry_interface": {
            "reported":
                ei_ref,

            "derived":
                ei_state,

            "reported_minute_offset_seconds":
                ei_minute_offset,

            "within_reported_minute":
                ei_minute_match,

            "altitude_difference_m":
                (
                    (
                        ei_state[
                            "wgs84_altitude_km"
                        ]
                        - ei_altitude_km
                    )
                    * 1000.0
                ),

            "derived_distance_to_terminal_miles":
                ei_distance_miles,

            "reported_approximate_distance_miles":
                ei_ref[
                    "reported_distance_to_splashdown_statute_miles"
                ],

            "distance_difference_miles":
                (
                    ei_distance_miles
                    - ei_ref[
                        "reported_distance_to_splashdown_statute_miles"
                    ]
                ),

            "distance_percent_difference":
                (
                    100.0
                    * (
                        ei_distance_miles
                        - ei_ref[
                            "reported_distance_to_splashdown_statute_miles"
                        ]
                    )
                    / ei_ref[
                        "reported_distance_to_splashdown_statute_miles"
                    ]
                ),
        },

        "drogue_deploy": {
            "reported":
                drogue_ref,

            "altitude_anchor":
                drogue_state,

            "reported_minute_offset_seconds":
                drogue_minute_offset,

            "within_reported_minute":
                drogue_minute_match,

            "speed_at_altitude_anchor_ft_s":
                (
                    drogue_state[
                        "earth_relative_speed_km_s"
                    ]
                    * KM_S_TO_FT_S
                ),

            "reported_speed_crossing":
                drogue_speed_state,

            "speed_crossing_offset_from_altitude_anchor_seconds":
                (
                    drogue_speed_t
                    - drogue_anchor_t
                ),

            "reported_distance_crossing":
                drogue_distance_state,

            "distance_crossing_offset_from_altitude_anchor_seconds":
                (
                    None
                    if drogue_distance_t is None
                    else (
                        drogue_distance_t
                        - drogue_anchor_t
                    )
                ),

            "interpretation":
                (
                    "Altitude and 479-ft/s "
                    "conditions align within "
                    "about one second. The "
                    "reported 0.8-mile value "
                    "does not correspond to the "
                    "same derived trajectory epoch "
                    "and is retained as an "
                    "approximate public-report "
                    "condition rather than a hard "
                    "deployment-state constraint."
                ),
        },

        "main_deploy": {
            "reported":
                main_ref,

            "altitude_anchor":
                main_state,

            "reported_minute_offset_seconds":
                main_minute_offset,

            "within_reported_minute":
                main_minute_match,

            "speed_at_altitude_anchor_ft_s":
                (
                    main_state[
                        "earth_relative_speed_km_s"
                    ]
                    * KM_S_TO_FT_S
                ),

            "first_200_ft_s_crossing_after_anchor":
                main_speed_state,

            "speed_response_offset_seconds":
                (
                    main_speed_t
                    - main_anchor_t
                ),

            "interpretation":
                (
                    "The trajectory reaches "
                    "200 ft/s 2.6 seconds after "
                    "the 5,400-ft anchor, "
                    "consistent with NASA's "
                    "wording that main deployment "
                    "was reducing velocity to "
                    "less than 200 ft/s."
                ),
        },

        "splashdown": {
            "reported":
                splash_ref,

            "derived_surface_crossing":
                surface_state,

            "reported_minute_offset_seconds":
                splash_minute_offset,

            "within_reported_minute":
                splash_minute_match,

            "derived_surface_speed_m_s":
                (
                    surface_state[
                        "earth_relative_speed_km_s"
                    ]
                    * 1000.0
                ),

            "derived_surface_speed_mph":
                (
                    surface_state[
                        "earth_relative_speed_km_s"
                    ]
                    * KM_S_TO_MPH
                ),

            "classification":
                (
                    "DERIVED_SPLASHDOWN_"
                    "CORRELATED_SURFACE_CROSSING"
                ),

            "interpretation":
                (
                    "The derived WGS84 "
                    "surface crossing is "
                    "correlated with NASA's "
                    "actual splashdown minute. "
                    "It is not claimed as an "
                    "official NASA sub-second "
                    "splashdown timestamp."
                ),
        },
    }

    OUTPUT_JSON.parent.mkdir(
        parents=True,
        exist_ok=True,
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

    # --------------------------------------------------------
    # Deterministic altitude/event figure
    # --------------------------------------------------------

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    altitude_figure = (
        ASSET_DIR
        / "phase2d_entry_events_altitude.svg"
    )

    fig, ax = plt.subplots()

    ax.plot(
        time_s,
        altitude,
    )

    event_points = [
        (
            0.0,
            altitude[0],
            "EI",
        ),
        (
            drogue_anchor_t,
            drogue_state[
                "wgs84_altitude_km"
            ],
            "Drogues",
        ),
        (
            main_anchor_t,
            main_state[
                "wgs84_altitude_km"
            ],
            "Mains",
        ),
        (
            surface_t,
            0.0,
            "Splashdown correlation",
        ),
    ]

    for x, y, label in event_points:
        ax.scatter(
            [x],
            [y],
        )

        ax.annotate(
            label,
            (x, y),
        )

    ax.set_xlabel(
        "Seconds after Entry Interface"
    )

    ax.set_ylabel(
        "WGS 84 altitude (km)"
    )

    ax.set_title(
        "Artemis II Entry Events"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        altitude_figure,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(fig)

    normalize_svg(
        altitude_figure
    )

    # --------------------------------------------------------
    # Deterministic ground-track figure
    # --------------------------------------------------------

    ground_figure = (
        ASSET_DIR
        / "phase2d_terminal_ground_track.svg"
    )

    terminal_mask = (
        time_s >= 500.0
    )

    fig, ax = plt.subplots()

    ax.plot(
        longitude[
            terminal_mask
        ],
        latitude[
            terminal_mask
        ],
    )

    for state, label in [
        (
            drogue_state,
            "Drogues",
        ),
        (
            main_state,
            "Mains",
        ),
        (
            surface_state,
            "Splashdown correlation",
        ),
    ]:
        ax.scatter(
            [
                state[
                    "longitude_deg"
                ]
            ],
            [
                state[
                    "latitude_deg"
                ]
            ],
        )

        ax.annotate(
            label,
            (
                state[
                    "longitude_deg"
                ],
                state[
                    "latitude_deg"
                ],
            ),
        )

    ax.set_xlabel(
        "Geodetic longitude (deg)"
    )

    ax.set_ylabel(
        "Geodetic latitude (deg)"
    )

    ax.set_title(
        "Artemis II Terminal Ground Track"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        ground_figure,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(fig)

    normalize_svg(
        ground_figure
    )

    # --------------------------------------------------------
    # Console result
    # --------------------------------------------------------

    print()
    print(
        "Artemis II Entry Event Correlation"
    )

    print(
        "----------------------------------"
    )

    print()
    print(
        "Entry Interface:"
    )

    print(
        f"  UTC: "
        f"{ei_state['utc']}"
    )

    print(
        f"  within NASA minute: "
        f"{ei_minute_match}"
    )

    print(
        f"  altitude difference: "
        f"{result['entry_interface']['altitude_difference_m']:+.3f} m"
    )

    print(
        "  distance to terminal: "
        f"{ei_distance_miles:.3f} mi"
    )

    print(
        "  NASA approximate distance: "
        f"{ei_ref['reported_distance_to_splashdown_statute_miles']:.0f} mi"
    )

    print(
        "  distance percent difference: "
        f"{result['entry_interface']['distance_percent_difference']:+.4f}%"
    )

    print()
    print(
        "Drogues:"
    )

    print(
        f"  altitude-anchor UTC: "
        f"{drogue_state['utc']}"
    )

    print(
        f"  within NASA minute: "
        f"{drogue_minute_match}"
    )

    print(
        "  speed at 23,400 ft: "
        f"{result['drogue_deploy']['speed_at_altitude_anchor_ft_s']:.3f} ft/s"
    )

    print(
        "  479-ft/s crossing offset: "
        f"{result['drogue_deploy']['speed_crossing_offset_from_altitude_anchor_seconds']:+.6f} s"
    )

    print(
        "  0.8-mi crossing offset: "
        f"{result['drogue_deploy']['distance_crossing_offset_from_altitude_anchor_seconds']:+.6f} s"
    )

    print()
    print(
        "Mains:"
    )

    print(
        f"  altitude-anchor UTC: "
        f"{main_state['utc']}"
    )

    print(
        f"  within NASA minute: "
        f"{main_minute_match}"
    )

    print(
        "  speed at 5,400 ft: "
        f"{result['main_deploy']['speed_at_altitude_anchor_ft_s']:.3f} ft/s"
    )

    print(
        "  first 200-ft/s crossing "
        "after anchor: "
        f"+{result['main_deploy']['speed_response_offset_seconds']:.6f} s"
    )

    print()
    print(
        "Splashdown correlation:"
    )

    print(
        f"  derived surface UTC: "
        f"{surface_state['utc']}"
    )

    print(
        f"  within NASA minute: "
        f"{splash_minute_match}"
    )

    print(
        f"  latitude: "
        f"{surface_lat:.6f} deg"
    )

    print(
        f"  longitude: "
        f"{surface_lon:.6f} deg"
    )

    print(
        f"  speed: "
        f"{result['splashdown']['derived_surface_speed_m_s']:.3f} m/s"
    )

    print(
        f"  speed: "
        f"{result['splashdown']['derived_surface_speed_mph']:.3f} mph"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "NASA blog events have "
        "minute-level public timing."
    )

    print(
        "Derived sub-second epochs "
        "are trajectory correlations, "
        "not official NASA event times."
    )

    print()
    print(
        f"Wrote: "
        f"{OUTPUT_JSON.relative_to(ROOT)}"
    )

    print(
        "Wrote documentation SVGs "
        f"under {ASSET_DIR.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
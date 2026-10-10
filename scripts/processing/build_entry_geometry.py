from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import spiceypy as spice


ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_trajectory_j2000.csv"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_geometry.csv"
)

OUTPUT_METADATA = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_geometry_metadata.json"
)

EARTH_PCK = (
    ROOT
    / "data"
    / "raw"
    / "spice"
    / "earth_1962_260806_2126_combined.bpc"
)

WGS84_A_KM = 6378.137
WGS84_INV_F = 298.257223563
WGS84_F = 1.0 / WGS84_INV_F

ENTRY_INTERFACE_FT = 400000.0
ENTRY_INTERFACE_KM = (
    ENTRY_INTERFACE_FT
    * 0.3048
    / 1000.0
)


def find_tls() -> Path:
    matches = list(
        (
            ROOT
            / "data"
            / "raw"
        ).rglob(
            "naif0012.tls"
        )
    )

    if not matches:
        raise SystemExit(
            "Could not find naif0012.tls"
        )

    return matches[0]


def utc_to_et(
    timestamp: str,
) -> float:
    return spice.str2et(
        timestamp
        .replace("T", " ")
        .replace("Z", " UTC")
    )


def wrap_longitude(
    value_deg: float,
) -> float:
    return (
        (
            value_deg
            + 180.0
        )
        % 360.0
        - 180.0
    )


def main():
    if not INPUT_CSV.exists():
        raise SystemExit(
            "Missing transformed entry "
            f"trajectory:\n{INPUT_CSV}"
        )

    if not EARTH_PCK.exists():
        raise SystemExit(
            "Missing Earth orientation "
            f"kernel:\n{EARTH_PCK}"
        )

    tls = find_tls()

    spice.furnsh(
        str(tls)
    )

    spice.furnsh(
        str(EARTH_PCK)
    )

    try:
        with INPUT_CSV.open(
            "r",
            encoding="utf-8",
        ) as f:
            reader = csv.DictReader(
                f
            )

            input_fields = (
                reader.fieldnames
                or []
            )

            rows = list(
                reader
            )

        if not rows:
            raise SystemExit(
                "No transformed entry "
                "trajectory records found."
            )

        output_rows = []

        max_radius_rotation_error = 0.0

        for row in rows:
            timestamp = (
                row[
                    "timestamp_utc"
                ]
            )

            et = utc_to_et(
                timestamp
            )

            state_j2000 = np.array(
                [
                    float(
                        row[
                            "x_j2000_km"
                        ]
                    ),
                    float(
                        row[
                            "y_j2000_km"
                        ]
                    ),
                    float(
                        row[
                            "z_j2000_km"
                        ]
                    ),
                    float(
                        row[
                            "vx_j2000_km_s"
                        ]
                    ),
                    float(
                        row[
                            "vy_j2000_km_s"
                        ]
                    ),
                    float(
                        row[
                            "vz_j2000_km_s"
                        ]
                    ),
                ],
                dtype=float,
            )

            transform = np.asarray(
                spice.sxform(
                    "J2000",
                    "ITRF93",
                    et,
                ),
                dtype=float,
            )

            state_itrf93 = (
                transform
                @ state_j2000
            )

            position = (
                state_itrf93[:3]
            )

            velocity = (
                state_itrf93[3:]
            )

            (
                longitude_rad,
                latitude_rad,
                altitude_km,
            ) = spice.recgeo(
                position,
                WGS84_A_KM,
                WGS84_F,
            )

            longitude_deg = (
                wrap_longitude(
                    math.degrees(
                        longitude_rad
                    )
                )
            )

            latitude_deg = (
                math.degrees(
                    latitude_rad
                )
            )

            # Local geodetic ENU basis.
            east_hat = np.array(
                [
                    -math.sin(
                        longitude_rad
                    ),
                    math.cos(
                        longitude_rad
                    ),
                    0.0,
                ]
            )

            north_hat = np.array(
                [
                    -math.sin(
                        latitude_rad
                    )
                    * math.cos(
                        longitude_rad
                    ),

                    -math.sin(
                        latitude_rad
                    )
                    * math.sin(
                        longitude_rad
                    ),

                    math.cos(
                        latitude_rad
                    ),
                ]
            )

            up_hat = np.array(
                [
                    math.cos(
                        latitude_rad
                    )
                    * math.cos(
                        longitude_rad
                    ),

                    math.cos(
                        latitude_rad
                    )
                    * math.sin(
                        longitude_rad
                    ),

                    math.sin(
                        latitude_rad
                    ),
                ]
            )

            east_velocity = float(
                np.dot(
                    velocity,
                    east_hat,
                )
            )

            north_velocity = float(
                np.dot(
                    velocity,
                    north_hat,
                )
            )

            vertical_velocity = float(
                np.dot(
                    velocity,
                    up_hat,
                )
            )

            horizontal_speed = (
                math.hypot(
                    east_velocity,
                    north_velocity,
                )
            )

            earth_relative_speed = float(
                np.linalg.norm(
                    velocity
                )
            )

            flight_path_angle = (
                math.degrees(
                    math.atan2(
                        vertical_velocity,
                        horizontal_speed,
                    )
                )
            )

            heading_deg = (
                math.degrees(
                    math.atan2(
                        east_velocity,
                        north_velocity,
                    )
                )
                % 360.0
            )

            radius_j2000 = float(
                np.linalg.norm(
                    state_j2000[:3]
                )
            )

            radius_itrf93 = float(
                np.linalg.norm(
                    position
                )
            )

            max_radius_rotation_error = max(
                max_radius_rotation_error,
                abs(
                    radius_j2000
                    - radius_itrf93
                ),
            )

            output = dict(
                row
            )

            output.update(
                {
                    "x_itrf93_km":
                        position[0],

                    "y_itrf93_km":
                        position[1],

                    "z_itrf93_km":
                        position[2],

                    "vx_itrf93_km_s":
                        velocity[0],

                    "vy_itrf93_km_s":
                        velocity[1],

                    "vz_itrf93_km_s":
                        velocity[2],

                    "geodetic_latitude_deg":
                        latitude_deg,

                    "geodetic_longitude_deg":
                        longitude_deg,

                    "wgs84_altitude_km":
                        altitude_km,

                    "earth_relative_speed_km_s":
                        earth_relative_speed,

                    "east_velocity_km_s":
                        east_velocity,

                    "north_velocity_km_s":
                        north_velocity,

                    "vertical_velocity_km_s":
                        vertical_velocity,

                    "horizontal_speed_km_s":
                        horizontal_speed,

                    "flight_path_angle_deg":
                        flight_path_angle,

                    "heading_deg":
                        heading_deg,

                    "altitude_minus_ei_km":
                        (
                            altitude_km
                            - ENTRY_INTERFACE_KM
                        ),
                }
            )

            output_rows.append(
                output
            )

        appended_fields = [
            "x_itrf93_km",
            "y_itrf93_km",
            "z_itrf93_km",
            "vx_itrf93_km_s",
            "vy_itrf93_km_s",
            "vz_itrf93_km_s",
            "geodetic_latitude_deg",
            "geodetic_longitude_deg",
            "wgs84_altitude_km",
            "earth_relative_speed_km_s",
            "east_velocity_km_s",
            "north_velocity_km_s",
            "vertical_velocity_km_s",
            "horizontal_speed_km_s",
            "flight_path_angle_deg",
            "heading_deg",
            "altitude_minus_ei_km",
        ]

        with OUTPUT_CSV.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=(
                    input_fields
                    + appended_fields
                ),
            )

            writer.writeheader()

            writer.writerows(
                output_rows
            )

        nearest_ei = min(
            output_rows,
            key=lambda row: abs(
                float(
                    row[
                        "altitude_minus_ei_km"
                    ]
                )
            ),
        )

        altitudes = [
            float(
                row[
                    "wgs84_altitude_km"
                ]
            )
            for row in output_rows
        ]

        metadata = {
            "frames": {
                "input":
                    "J2000",

                "earth_fixed":
                    "ITRF93",
            },

            "earth_orientation_kernel": {
                "filename":
                    EARTH_PCK.name,

                "sha256":
                    (
                        "CC87AD1A495CF598800BA403763D350"
                        "F087AC0B97DA9FEC603278A3864C6A53E"
                    ),
            },

            "geodetic_model": {
                "name":
                    "WGS 84",

                "semi_major_axis_km":
                    WGS84_A_KM,

                "inverse_flattening":
                    WGS84_INV_F,
            },

            "entry_interface_reference": {
                "source_value_ft":
                    ENTRY_INTERFACE_FT,

                "converted_km":
                    ENTRY_INTERFACE_KM,

                "nearest_state_utc":
                    nearest_ei[
                        "timestamp_utc"
                    ],

                "nearest_state_altitude_km":
                    float(
                        nearest_ei[
                            "wgs84_altitude_km"
                        ]
                    ),

                "altitude_difference_km":
                    float(
                        nearest_ei[
                            "altitude_minus_ei_km"
                        ]
                    ),
            },

            "records": {
                "count":
                    len(
                        output_rows
                    ),

                "start_utc":
                    output_rows[0][
                        "timestamp_utc"
                    ],

                "stop_utc":
                    output_rows[-1][
                        "timestamp_utc"
                    ],

                "maximum_altitude_km":
                    max(
                        altitudes
                    ),

                "minimum_altitude_km":
                    min(
                        altitudes
                    ),
            },

            "diagnostics": {
                "max_position_norm_rotation_error_km":
                    max_radius_rotation_error,
            },

            "interpretation_limits": [
                (
                    "WGS84 altitude is derived "
                    "from the transformed public "
                    "trajectory."
                ),
                (
                    "Heading becomes poorly "
                    "conditioned when horizontal "
                    "speed approaches zero."
                ),
                (
                    "The final near-zero altitude "
                    "state is not labeled "
                    "splashdown until independently "
                    "validated against mission "
                    "reporting."
                ),
            ],
        }

        with OUTPUT_METADATA.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                metadata,
                f,
                indent=2,
            )

        first = (
            output_rows[0]
        )

        last = (
            output_rows[-1]
        )

        print()
        print(
            "Artemis II Entry Geometry"
        )

        print(
            "-------------------------"
        )

        print(
            f"Records: "
            f"{len(output_rows)}"
        )

        print()
        print(
            "First state:"
        )

        print(
            f"  UTC: "
            f"{first['timestamp_utc']}"
        )

        print(
            "  Latitude: "
            f"{float(first['geodetic_latitude_deg']):.6f} deg"
        )

        print(
            "  Longitude: "
            f"{float(first['geodetic_longitude_deg']):.6f} deg"
        )

        print(
            "  Altitude: "
            f"{float(first['wgs84_altitude_km']):.6f} km"
        )

        print(
            "  Earth-relative speed: "
            f"{float(first['earth_relative_speed_km_s']):.6f} km/s"
        )

        print(
            "  Flight-path angle: "
            f"{float(first['flight_path_angle_deg']):.6f} deg"
        )

        print(
            "  Heading: "
            f"{float(first['heading_deg']):.6f} deg"
        )

        print()
        print(
            "Entry Interface check:"
        )

        print(
            "  Reference altitude: "
            f"{ENTRY_INTERFACE_KM:.6f} km"
        )

        print(
            "  Nearest state: "
            f"{nearest_ei['timestamp_utc']}"
        )

        print(
            "  Derived altitude: "
            f"{float(nearest_ei['wgs84_altitude_km']):.6f} km"
        )

        print(
            "  Difference: "
            f"{float(nearest_ei['altitude_minus_ei_km']):+.6f} km"
        )

        print()
        print(
            "Last state:"
        )

        print(
            f"  UTC: "
            f"{last['timestamp_utc']}"
        )

        print(
            "  Latitude: "
            f"{float(last['geodetic_latitude_deg']):.6f} deg"
        )

        print(
            "  Longitude: "
            f"{float(last['geodetic_longitude_deg']):.6f} deg"
        )

        print(
            "  Altitude: "
            f"{float(last['wgs84_altitude_km']):.6f} km"
        )

        print(
            "  Earth-relative speed: "
            f"{float(last['earth_relative_speed_km_s']):.6f} km/s"
        )

        print()
        print(
            "Maximum position-norm "
            "rotation error:"
        )

        print(
            f"  "
            f"{max_radius_rotation_error:.12e} km"
        )

        print()
        print(
            f"Wrote: "
            f"{OUTPUT_CSV.relative_to(ROOT)}"
        )

        print(
            f"Wrote: "
            f"{OUTPUT_METADATA.relative_to(ROOT)}"
        )

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()
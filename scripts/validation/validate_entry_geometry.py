from __future__ import annotations

import csv
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
    / "entry_geometry.csv"
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

EI_KM = (
    400000.0
    * 0.3048
    / 1000.0
)


def fail(
    message: str,
):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
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
        fail(
            "naif0012.tls not found"
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


def angular_difference_deg(
    a: float,
    b: float,
) -> float:
    return abs(
        (
            a
            - b
            + 180.0
        )
        % 360.0
        - 180.0
    )


def main():
    if not INPUT_CSV.exists():
        fail(
            "entry_geometry.csv "
            "does not exist"
        )

    if not EARTH_PCK.exists():
        fail(
            "Earth orientation "
            "kernel does not exist"
        )

    with INPUT_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        rows = list(
            csv.DictReader(
                f
            )
        )

    if len(
        rows
    ) != 819:
        fail(
            f"expected 819 rows, "
            f"found {len(rows)}"
        )

    spice.furnsh(
        str(
            find_tls()
        )
    )

    spice.furnsh(
        str(
            EARTH_PCK
        )
    )

    try:
        max_position_error = 0.0
        max_velocity_error = 0.0
        max_altitude_error = 0.0
        max_latitude_error = 0.0
        max_longitude_error = 0.0
        max_speed_error = 0.0
        max_velocity_decomposition_error = 0.0

        for index, row in enumerate(
            rows,
            start=1,
        ):
            et = utc_to_et(
                row[
                    "timestamp_utc"
                ]
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
                ]
            )

            transform = np.asarray(
                spice.sxform(
                    "J2000",
                    "ITRF93",
                    et,
                )
            )

            expected_state = (
                transform
                @ state_j2000
            )

            stored_state = np.array(
                [
                    float(
                        row[
                            "x_itrf93_km"
                        ]
                    ),
                    float(
                        row[
                            "y_itrf93_km"
                        ]
                    ),
                    float(
                        row[
                            "z_itrf93_km"
                        ]
                    ),
                    float(
                        row[
                            "vx_itrf93_km_s"
                        ]
                    ),
                    float(
                        row[
                            "vy_itrf93_km_s"
                        ]
                    ),
                    float(
                        row[
                            "vz_itrf93_km_s"
                        ]
                    ),
                ]
            )

            position_error = (
                np.linalg.norm(
                    expected_state[:3]
                    - stored_state[:3]
                )
            )

            velocity_error = (
                np.linalg.norm(
                    expected_state[3:]
                    - stored_state[3:]
                )
            )

            max_position_error = max(
                max_position_error,
                position_error,
            )

            max_velocity_error = max(
                max_velocity_error,
                velocity_error,
            )

            (
                lon_rad,
                lat_rad,
                altitude,
            ) = spice.recgeo(
                stored_state[:3],
                WGS84_A_KM,
                WGS84_F,
            )

            expected_lon = (
                (
                    math.degrees(
                        lon_rad
                    )
                    + 180.0
                )
                % 360.0
                - 180.0
            )

            expected_lat = (
                math.degrees(
                    lat_rad
                )
            )

            stored_lon = float(
                row[
                    "geodetic_longitude_deg"
                ]
            )

            stored_lat = float(
                row[
                    "geodetic_latitude_deg"
                ]
            )

            stored_altitude = float(
                row[
                    "wgs84_altitude_km"
                ]
            )

            max_altitude_error = max(
                max_altitude_error,
                abs(
                    altitude
                    - stored_altitude
                ),
            )

            max_latitude_error = max(
                max_latitude_error,
                abs(
                    expected_lat
                    - stored_lat
                ),
            )

            max_longitude_error = max(
                max_longitude_error,
                angular_difference_deg(
                    expected_lon,
                    stored_lon,
                ),
            )

            speed = float(
                np.linalg.norm(
                    stored_state[3:]
                )
            )

            stored_speed = float(
                row[
                    "earth_relative_speed_km_s"
                ]
            )

            max_speed_error = max(
                max_speed_error,
                abs(
                    speed
                    - stored_speed
                ),
            )

            east = float(
                row[
                    "east_velocity_km_s"
                ]
            )

            north = float(
                row[
                    "north_velocity_km_s"
                ]
            )

            up = float(
                row[
                    "vertical_velocity_km_s"
                ]
            )

            decomposed_speed = (
                math.sqrt(
                    east**2
                    + north**2
                    + up**2
                )
            )

            max_velocity_decomposition_error = max(
                max_velocity_decomposition_error,
                abs(
                    decomposed_speed
                    - stored_speed
                ),
            )

        first = rows[0]
        last = rows[-1]

        first_altitude = float(
            first[
                "wgs84_altitude_km"
            ]
        )

        ei_difference = (
            first_altitude
            - EI_KM
        )

        if abs(
            ei_difference
        ) > 0.001:
            fail(
                "first state differs "
                "from 400,000-ft EI by "
                "more than 1 meter"
            )

        if abs(
            float(
                last[
                    "wgs84_altitude_km"
                ]
            )
        ) > 0.001:
            fail(
                "terminal state is not "
                "within 1 meter of the "
                "WGS84 ellipsoid"
            )

        if (
            max_position_error
            > 1e-10
        ):
            fail(
                "ITRF93 position "
                "reconstruction failed"
            )

        if (
            max_velocity_error
            > 1e-12
        ):
            fail(
                "ITRF93 velocity "
                "reconstruction failed"
            )

        if (
            max_altitude_error
            > 1e-10
        ):
            fail(
                "geodetic altitude "
                "reconstruction failed"
            )

        if (
            max_velocity_decomposition_error
            > 1e-12
        ):
            fail(
                "ENU velocity "
                "decomposition failed"
            )

        print()
        print(
            "Artemis II Entry "
            "Geometry Validation"
        )

        print(
            "--------------------------------"
        )

        print(
            f"Records checked: "
            f"{len(rows)}"
        )

        print()
        print(
            "Frame reconstruction:"
        )

        print(
            "  Max position error: "
            f"{max_position_error:.12e} km"
        )

        print(
            "  Max velocity error: "
            f"{max_velocity_error:.12e} km/s"
        )

        print()
        print(
            "Geodetic reconstruction:"
        )

        print(
            "  Max altitude error: "
            f"{max_altitude_error:.12e} km"
        )

        print(
            "  Max latitude error: "
            f"{max_latitude_error:.12e} deg"
        )

        print(
            "  Max longitude error: "
            f"{max_longitude_error:.12e} deg"
        )

        print()
        print(
            "Velocity reconstruction:"
        )

        print(
            "  Max speed error: "
            f"{max_speed_error:.12e} km/s"
        )

        print(
            "  Max ENU magnitude error: "
            f"{max_velocity_decomposition_error:.12e} km/s"
        )

        print()
        print(
            "Entry Interface:"
        )

        print(
            f"  Reference: "
            f"{EI_KM:.6f} km"
        )

        print(
            f"  First state: "
            f"{first_altitude:.6f} km"
        )

        print(
            "  Difference: "
            f"{ei_difference:+.9f} km"
        )

        print(
            "  Difference: "
            f"{ei_difference * 1000.0:+.3f} m"
        )

        print()
        print(
            "Terminal state:"
        )

        print(
            "  UTC: "
            f"{last['timestamp_utc']}"
        )

        print(
            "  Altitude: "
            f"{float(last['wgs84_altitude_km']):.6f} km"
        )

        print(
            "  Earth-relative speed: "
            f"{float(last['earth_relative_speed_km_s']):.6f} km/s"
        )

        print(
            "  Latitude: "
            f"{float(last['geodetic_latitude_deg']):.6f} deg"
        )

        print(
            "  Longitude: "
            f"{float(last['geodetic_longitude_deg']):.6f} deg"
        )

        print()
        print(
            "OK: Earth-fixed frame, "
            "WGS84 geodetic geometry, "
            "Earth-relative velocity, and "
            "Entry Interface reconstruction "
            "validated."
        )

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()
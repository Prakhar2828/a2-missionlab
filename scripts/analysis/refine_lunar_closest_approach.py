from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

import spiceypy as spice


INPUT_PATH = Path(
    "data/processed/trajectory/trajectory_with_lunar_geometry.csv"
)

OUTPUT_PATH = Path(
    "data/processed/trajectory/lunar_closest_approach.json"
)

SPICE_DIR = Path("data/raw/spice")


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def magnitude(vector):
    return math.sqrt(sum(x * x for x in vector))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def hermite_state(row0, row1, candidate_time):
    t0 = parse_utc(row0["timestamp_utc"])
    t1 = parse_utc(row1["timestamp_utc"])

    dt = (t1 - t0).total_seconds()

    u = (
        candidate_time - t0
    ).total_seconds() / dt

    p0 = [
        float(row0["x_km"]),
        float(row0["y_km"]),
        float(row0["z_km"]),
    ]

    p1 = [
        float(row1["x_km"]),
        float(row1["y_km"]),
        float(row1["z_km"]),
    ]

    v0 = [
        float(row0["vx_km_s"]),
        float(row0["vy_km_s"]),
        float(row0["vz_km_s"]),
    ]

    v1 = [
        float(row1["vx_km_s"]),
        float(row1["vy_km_s"]),
        float(row1["vz_km_s"]),
    ]

    h00 = 2 * u**3 - 3 * u**2 + 1
    h10 = u**3 - 2 * u**2 + u
    h01 = -2 * u**3 + 3 * u**2
    h11 = u**3 - u**2

    position = [
        h00 * p0[i]
        + h10 * dt * v0[i]
        + h01 * p1[i]
        + h11 * dt * v1[i]
        for i in range(3)
    ]

    dh00 = 6 * u**2 - 6 * u
    dh10 = 3 * u**2 - 4 * u + 1
    dh01 = -6 * u**2 + 6 * u
    dh11 = 3 * u**2 - 2 * u

    velocity = [
        (
            dh00 * p0[i]
            + dh10 * dt * v0[i]
            + dh01 * p1[i]
            + dh11 * dt * v1[i]
        )
        / dt
        for i in range(3)
    ]

    return position, velocity


def moon_state_at(candidate_time):
    time_string = (
        candidate_time.strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        + " UTC"
    )

    et = spice.str2et(time_string)

    state, _ = spice.spkezr(
        "MOON",
        et,
        "J2000",
        "NONE",
        "EARTH",
    )

    return list(state[:3]), list(state[3:])


def geometry(row0, row1, candidate_time):
    orion_position, orion_velocity = (
        hermite_state(
            row0,
            row1,
            candidate_time,
        )
    )

    moon_position, moon_velocity = (
        moon_state_at(candidate_time)
    )

    relative_position = [
        orion_position[i] - moon_position[i]
        for i in range(3)
    ]

    relative_velocity = [
        orion_velocity[i] - moon_velocity[i]
        for i in range(3)
    ]

    distance = magnitude(relative_position)
    speed = magnitude(relative_velocity)

    radial_velocity = (
        dot(
            relative_position,
            relative_velocity,
        )
        / distance
    )

    return {
        "distance_km": distance,
        "relative_speed_km_s": speed,
        "radial_velocity_km_s":
            radial_velocity,
    }


def minimize_segment(row0, row1):
    start = parse_utc(row0["timestamp_utc"])
    stop = parse_utc(row1["timestamp_utc"])

    total_seconds = (
        stop - start
    ).total_seconds()

    phi = (1 + math.sqrt(5)) / 2

    left = 0.0
    right = total_seconds

    for _ in range(80):
        c = right - (right - left) / phi
        d = left + (right - left) / phi

        time_c = start + timedelta(seconds=c)
        time_d = start + timedelta(seconds=d)

        distance_c = geometry(
            row0,
            row1,
            time_c,
        )["distance_km"]

        distance_d = geometry(
            row0,
            row1,
            time_d,
        )["distance_km"]

        if distance_c < distance_d:
            right = d
        else:
            left = c

    best_seconds = (left + right) / 2

    best_time = start + timedelta(
        seconds=best_seconds
    )

    return best_time, geometry(
        row0,
        row1,
        best_time,
    )


def main():
    spice.furnsh(
        str(SPICE_DIR / "naif0012.tls")
    )

    spice.furnsh(
        str(SPICE_DIR / "de440s.bsp")
    )

    spice.furnsh(
        str(SPICE_DIR / "pck00011.tpc")
    )

    _, moon_radii = spice.bodvrd(
        "MOON",
        "RADII",
        3,
    )

    moon_mean_radius = (
        sum(moon_radii) / 3
    )

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        rows = list(csv.DictReader(f))

    coarse_index = min(
        range(len(rows)),
        key=lambda i:
            float(
                rows[i][
                    "orion_moon_distance_km"
                ]
            ),
    )

    candidates = []

    if coarse_index > 0:
        candidates.append(
            minimize_segment(
                rows[coarse_index - 1],
                rows[coarse_index],
            )
        )

    if coarse_index < len(rows) - 1:
        candidates.append(
            minimize_segment(
                rows[coarse_index],
                rows[coarse_index + 1],
            )
        )

    best_time, best_geometry = min(
        candidates,
        key=lambda item:
            item[1]["distance_km"],
    )

    altitude = (
        best_geometry["distance_km"]
        - moon_mean_radius
    )

    result = {
        "timestamp_utc":
            best_time.isoformat(),
        "moon_center_distance_km":
            best_geometry["distance_km"],
        "lunar_altitude_mean_radius_km":
            altitude,
        "moon_relative_speed_km_s":
            best_geometry[
                "relative_speed_km_s"
            ],
        "moon_radial_velocity_km_s":
            best_geometry[
                "radial_velocity_km_s"
            ],
        "method":
            "Cubic Hermite interpolation of "
            "NASA Artemis II OEM state vectors "
            "with DE440 Moon state and "
            "golden-section distance minimization.",
        "provenance":
            "DERIVED",
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
        )

    print()
    print("Refined Artemis II Pericynthion")
    print("--------------------------------")

    print(
        "UTC: "
        f"{best_time.isoformat()}"
    )

    print(
        "Moon-center distance: "
        f"{best_geometry['distance_km']:,.3f} km"
    )

    print(
        "Mean-radius lunar altitude: "
        f"{altitude:,.3f} km"
    )

    print(
        "Moon-relative speed: "
        f"{best_geometry['relative_speed_km_s']:.6f} km/s"
    )

    print(
        "Moon radial velocity: "
        f"{best_geometry['radial_velocity_km_s']:.9f} km/s"
    )

    print()
    print(
        f"Wrote: {OUTPUT_PATH}"
    )

    spice.kclear()


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import math
from pathlib import Path

import spiceypy as spice


INPUT_PATH = Path(
    "data/processed/trajectory/primary_trajectory.csv"
)

OUTPUT_PATH = Path(
    "data/processed/trajectory/"
    "trajectory_with_lunar_geometry.csv"
)

SPICE_DIR = Path("data/raw/spice")


def magnitude(vector: list[float]) -> float:
    return math.sqrt(sum(component**2 for component in vector))


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def main() -> None:
    spice.furnsh(str(SPICE_DIR / "naif0012.tls"))
    spice.furnsh(str(SPICE_DIR / "de440s.bsp"))
    spice.furnsh(str(SPICE_DIR / "pck00011.tpc"))

    _, moon_radii = spice.bodvrd(
        "MOON",
        "RADII",
        3,
    )

    moon_mean_radius_km = sum(moon_radii) / 3.0

    print(
        f"Moon mean radius from SPICE: "
        f"{moon_mean_radius_km:.3f} km"
    )

    output_rows = []

    with INPUT_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            timestamp = row["timestamp_utc"]

            spice_time = timestamp.replace("T", " ") + " UTC"
            et = spice.str2et(spice_time)

            moon_state, _ = spice.spkezr(
                "MOON",
                et,
                "J2000",
                "NONE",
                "EARTH",
            )

            moon_position = list(moon_state[:3])
            moon_velocity = list(moon_state[3:])

            orion_position = [
                float(row["x_km"]),
                float(row["y_km"]),
                float(row["z_km"]),
            ]

            orion_velocity = [
                float(row["vx_km_s"]),
                float(row["vy_km_s"]),
                float(row["vz_km_s"]),
            ]

            moon_relative_position = [
                orion_position[i] - moon_position[i]
                for i in range(3)
            ]

            moon_relative_velocity = [
                orion_velocity[i] - moon_velocity[i]
                for i in range(3)
            ]

            moon_distance_km = magnitude(
                moon_relative_position
            )

            moon_relative_speed_km_s = magnitude(
                moon_relative_velocity
            )

            moon_radial_velocity_km_s = (
                dot(
                    moon_relative_position,
                    moon_relative_velocity,
                )
                / moon_distance_km
            )

            lunar_altitude_km = (
                moon_distance_km
                - moon_mean_radius_km
            )

            output_rows.append(
                {
                    **row,

                    "moon_x_eme2000_km":
                        round(moon_position[0], 6),
                    "moon_y_eme2000_km":
                        round(moon_position[1], 6),
                    "moon_z_eme2000_km":
                        round(moon_position[2], 6),

                    "moon_vx_eme2000_km_s":
                        round(moon_velocity[0], 9),
                    "moon_vy_eme2000_km_s":
                        round(moon_velocity[1], 9),
                    "moon_vz_eme2000_km_s":
                        round(moon_velocity[2], 9),

                    "orion_moon_distance_km":
                        round(moon_distance_km, 6),

                    "lunar_altitude_mean_radius_km":
                        round(lunar_altitude_km, 6),

                    "moon_relative_speed_km_s":
                        round(
                            moon_relative_speed_km_s,
                            9,
                        ),

                    "moon_radial_velocity_km_s":
                        round(
                            moon_radial_velocity_km_s,
                            9,
                        ),
                }
            )

    if not output_rows:
        raise SystemExit("No trajectory rows found.")

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(output_rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(output_rows)

    closest = min(
        output_rows,
        key=lambda row:
            row["orion_moon_distance_km"],
    )

    print()
    print("Closest sampled lunar approach")
    print("------------------------------")

    print(
        f"UTC: {closest['timestamp_utc']}"
    )

    print(
        f"MET: {closest['met']}"
    )

    print(
        "Moon-center distance: "
        f"{closest['orion_moon_distance_km']:,.3f} km"
    )

    print(
        "Mean-radius lunar altitude: "
        f"{closest['lunar_altitude_mean_radius_km']:,.3f} km"
    )

    print(
        "Moon-relative speed: "
        f"{closest['moon_relative_speed_km_s']:.6f} km/s"
    )

    print(
        "Moon radial velocity: "
        f"{closest['moon_radial_velocity_km_s']:.6f} km/s"
    )

    print()
    print(f"Wrote: {OUTPUT_PATH}")

    spice.kclear()


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import spiceypy as spice


ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_trajectory_m50.csv"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_trajectory_j2000.csv"
)

OUTPUT_METADATA = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_frame_transform_metadata.json"
)

SOURCE_FRAME = "B1950"
TARGET_FRAME = "J2000"


def utc_to_et(timestamp: str) -> float:
    spice_time = (
        timestamp
        .replace("T", " ")
        .replace("Z", " UTC")
    )

    return spice.str2et(
        spice_time
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


def matrix_to_list(
    matrix: np.ndarray,
):
    return [
        [
            float(value)
            for value in row
        ]
        for row in matrix
    ]


def main():
    if not INPUT_CSV.exists():
        raise SystemExit(
            "Missing Phase 2A input:\n"
            f"{INPUT_CSV}"
        )

    tls_path = find_tls()

    spice.furnsh(
        str(tls_path)
    )

    try:
        with INPUT_CSV.open(
            "r",
            encoding="utf-8",
        ) as f:
            reader = csv.DictReader(
                f
            )

            input_fieldnames = (
                reader.fieldnames
                or []
            )

            rows = list(
                reader
            )

        if not rows:
            raise SystemExit(
                "No M50 entry states found."
            )

        output_rows = []

        max_radius_difference = 0.0
        max_speed_difference = 0.0

        first_transform = None
        last_transform = None

        for row in rows:
            timestamp = (
                row[
                    "timestamp_utc"
                ]
            )

            et = utc_to_et(
                timestamp
            )

            transform = np.asarray(
                spice.sxform(
                    SOURCE_FRAME,
                    TARGET_FRAME,
                    et,
                ),
                dtype=float,
            )

            if first_transform is None:
                first_transform = (
                    transform.copy()
                )

            last_transform = (
                transform.copy()
            )

            m50_state = np.array(
                [
                    float(
                        row[
                            "x_m50_km"
                        ]
                    ),
                    float(
                        row[
                            "y_m50_km"
                        ]
                    ),
                    float(
                        row[
                            "z_m50_km"
                        ]
                    ),
                    float(
                        row[
                            "vx_m50_km_s"
                        ]
                    ),
                    float(
                        row[
                            "vy_m50_km_s"
                        ]
                    ),
                    float(
                        row[
                            "vz_m50_km_s"
                        ]
                    ),
                ],
                dtype=float,
            )

            j2000_state = (
                transform
                @ m50_state
            )

            m50_radius = (
                np.linalg.norm(
                    m50_state[:3]
                )
            )

            j2000_radius = (
                np.linalg.norm(
                    j2000_state[:3]
                )
            )

            m50_speed = (
                np.linalg.norm(
                    m50_state[3:]
                )
            )

            j2000_speed = (
                np.linalg.norm(
                    j2000_state[3:]
                )
            )

            max_radius_difference = max(
                max_radius_difference,
                abs(
                    m50_radius
                    - j2000_radius
                ),
            )

            max_speed_difference = max(
                max_speed_difference,
                abs(
                    m50_speed
                    - j2000_speed
                ),
            )

            output = dict(
                row
            )

            output.update(
                {
                    "x_j2000_km":
                        j2000_state[0],

                    "y_j2000_km":
                        j2000_state[1],

                    "z_j2000_km":
                        j2000_state[2],

                    "vx_j2000_km_s":
                        j2000_state[3],

                    "vy_j2000_km_s":
                        j2000_state[4],

                    "vz_j2000_km_s":
                        j2000_state[5],

                    "earth_center_distance_j2000_km":
                        j2000_radius,

                    "inertial_speed_j2000_km_s":
                        j2000_speed,
                }
            )

            output_rows.append(
                output
            )

        appended_fields = [
            "x_j2000_km",
            "y_j2000_km",
            "z_j2000_km",
            "vx_j2000_km_s",
            "vy_j2000_km_s",
            "vz_j2000_km_s",
            "earth_center_distance_j2000_km",
            "inertial_speed_j2000_km_s",
        ]

        output_fieldnames = (
            input_fieldnames
            + appended_fields
        )

        OUTPUT_CSV.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with OUTPUT_CSV.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=output_fieldnames,
            )

            writer.writeheader()

            writer.writerows(
                output_rows
            )

        assert (
            first_transform
            is not None
        )

        assert (
            last_transform
            is not None
        )

        rotation = (
            first_transform[
                :3,
                :3,
            ]
        )

        determinant = (
            np.linalg.det(
                rotation
            )
        )

        orthogonality_error = (
            np.linalg.norm(
                rotation.T
                @ rotation
                - np.eye(
                    3
                )
            )
        )

        transform_time_variation = (
            np.max(
                np.abs(
                    last_transform
                    - first_transform
                )
            )
        )

        metadata = {
            "source_frame_label":
                "M50",

            "analysis_mapping": {
                "spice_source_frame":
                    SOURCE_FRAME,

                "spice_target_frame":
                    TARGET_FRAME,

                "status":
                    (
                        "A2 MissionLab "
                        "analysis mapping"
                    ),

                "interpretation":
                    (
                        "The NASA source label "
                        "M50 is represented using "
                        "SPICE B1950 for conversion "
                        "to J2000. This mapping is "
                        "supported by legacy-frame "
                        "definitions and by Phase 1 "
                        "to Phase 2 trajectory "
                        "continuity testing."
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
            },

            "transform_diagnostics": {
                "rotation_matrix":
                    matrix_to_list(
                        rotation
                    ),

                "rotation_determinant":
                    float(
                        determinant
                    ),

                "orthogonality_error":
                    float(
                        orthogonality_error
                    ),

                "max_transform_time_variation":
                    float(
                        transform_time_variation
                    ),

                "max_radius_difference_km":
                    float(
                        max_radius_difference
                    ),

                "max_speed_difference_km_s":
                    float(
                        max_speed_difference
                    ),
            },

            "interpretation_limits": [
                (
                    "The source file itself "
                    "does not explicitly identify "
                    "M50 as the SPICE B1950 frame."
                ),
                (
                    "J2000 is used as the analysis "
                    "representation compatible "
                    "with the Phase 1 EME2000 "
                    "working frame."
                ),
                (
                    "This transformation does not "
                    "by itself establish geodetic "
                    "altitude or Earth-fixed "
                    "coordinates."
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

        print()
        print(
            "Artemis II Entry Frame Transform"
        )

        print(
            "--------------------------------"
        )

        print(
            f"Records: "
            f"{len(output_rows)}"
        )

        print(
            "Mapping: "
            "M50 -> SPICE B1950 -> J2000"
        )

        print()
        print(
            "Rotation determinant: "
            f"{determinant:.15f}"
        )

        print(
            "Orthogonality error: "
            f"{orthogonality_error:.12e}"
        )

        print(
            "Maximum transform "
            "time variation: "
            f"{transform_time_variation:.12e}"
        )

        print()
        print(
            "Maximum radius "
            "preservation error: "
            f"{max_radius_difference:.12e} km"
        )

        print(
            "Maximum speed "
            "preservation error: "
            f"{max_speed_difference:.12e} km/s"
        )

        print()
        print(
            "First J2000 state:"
        )

        first = (
            output_rows[0]
        )

        print(
            "  r = "
            f"({float(first['x_j2000_km']):.6f}, "
            f"{float(first['y_j2000_km']):.6f}, "
            f"{float(first['z_j2000_km']):.6f}) km"
        )

        print(
            "  v = "
            f"({float(first['vx_j2000_km_s']):.9f}, "
            f"{float(first['vy_j2000_km_s']):.9f}, "
            f"{float(first['vz_j2000_km_s']):.9f}) km/s"
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
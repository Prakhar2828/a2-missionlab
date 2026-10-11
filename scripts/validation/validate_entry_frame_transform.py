from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import spiceypy as spice


ROOT = Path(__file__).resolve().parents[2]

M50_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_trajectory_m50.csv"
)

J2000_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_trajectory_j2000.csv"
)

METADATA_PATH = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_frame_transform_metadata.json"
)

PHASE1_OEM = (
    ROOT
    / "data"
    / "processed"
    / "trajectory"
    / "Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.csv"
)

MU_EARTH = (
    398600.435507
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
    spice_time = (
        timestamp
        .replace("T", " ")
        .replace("Z", " UTC")
    )

    return spice.str2et(
        spice_time
    )


def acceleration(
    state: np.ndarray,
) -> np.ndarray:
    r = state[:3]

    radius = np.linalg.norm(
        r
    )

    result = np.zeros(
        6
    )

    result[:3] = (
        state[3:]
    )

    result[3:] = (
        -MU_EARTH
        * r
        / radius**3
    )

    return result


def rk4_step(
    state: np.ndarray,
    dt: float,
) -> np.ndarray:
    k1 = acceleration(
        state
    )

    k2 = acceleration(
        state
        + 0.5
        * dt
        * k1
    )

    k3 = acceleration(
        state
        + 0.5
        * dt
        * k2
    )

    k4 = acceleration(
        state
        + dt
        * k3
    )

    return (
        state
        + dt
        * (
            k1
            + 2.0 * k2
            + 2.0 * k3
            + k4
        )
        / 6.0
    )


def propagate_two_body(
    state: np.ndarray,
    duration: float,
    max_step: float = 0.05,
) -> np.ndarray:
    propagated = (
        state.copy()
    )

    remaining = (
        duration
    )

    while remaining > 0.0:
        step = min(
            max_step,
            remaining,
        )

        propagated = rk4_step(
            propagated,
            step,
        )

        remaining -= (
            step
        )

    return propagated


def find_column(
    headers,
    candidates,
):
    for candidate in candidates:
        if candidate in headers:
            return candidate

    return None


def load_phase1_final():
    with PHASE1_OEM.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(
            f
        )

        headers = (
            reader.fieldnames
            or []
        )

        rows = list(
            reader
        )

    if not rows:
        fail(
            "Phase 1 OEM is empty"
        )

    timestamp_column = (
        find_column(
            headers,
            [
                "timestamp_utc",
                "timestamp",
                "utc",
            ],
        )
    )

    x = find_column(
        headers,
        [
            "x_km",
            "x_eme2000_km",
        ],
    )

    y = find_column(
        headers,
        [
            "y_km",
            "y_eme2000_km",
        ],
    )

    z = find_column(
        headers,
        [
            "z_km",
            "z_eme2000_km",
        ],
    )

    vx = find_column(
        headers,
        [
            "vx_km_s",
            "vx_eme2000_km_s",
        ],
    )

    vy = find_column(
        headers,
        [
            "vy_km_s",
            "vy_eme2000_km_s",
        ],
    )

    vz = find_column(
        headers,
        [
            "vz_km_s",
            "vz_eme2000_km_s",
        ],
    )

    columns = [
        timestamp_column,
        x,
        y,
        z,
        vx,
        vy,
        vz,
    ]

    if any(
        value is None
        for value in columns
    ):
        fail(
            "could not identify Phase 1 "
            "OEM state columns"
        )

    last = rows[-1]

    state = np.array(
        [
            float(
                last[x]
            ),
            float(
                last[y]
            ),
            float(
                last[z]
            ),
            float(
                last[vx]
            ),
            float(
                last[vy]
            ),
            float(
                last[vz]
            ),
        ],
        dtype=float,
    )

    return (
        last[
            timestamp_column
        ],
        state,
    )


def main():
    for path in [
        M50_CSV,
        J2000_CSV,
        METADATA_PATH,
        PHASE1_OEM,
    ]:
        if not path.exists():
            fail(
                f"missing required file: "
                f"{path}"
            )

    with M50_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        m50_rows = list(
            csv.DictReader(
                f
            )
        )

    with J2000_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        j2000_rows = list(
            csv.DictReader(
                f
            )
        )

    with METADATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        metadata = json.load(
            f
        )

    if len(
        m50_rows
    ) != 819:
        fail(
            "M50 record count "
            "is not 819"
        )

    if len(
        j2000_rows
    ) != 819:
        fail(
            "J2000 record count "
            "is not 819"
        )

    if (
        metadata[
            "analysis_mapping"
        ][
            "spice_source_frame"
        ]
        != "B1950"
    ):
        fail(
            "metadata source frame "
            "is not B1950"
        )

    if (
        metadata[
            "analysis_mapping"
        ][
            "spice_target_frame"
        ]
        != "J2000"
    ):
        fail(
            "metadata target frame "
            "is not J2000"
        )

    tls_path = (
        find_tls()
    )

    spice.furnsh(
        str(
            tls_path
        )
    )

    try:
        max_position_transform_error = (
            0.0
        )

        max_velocity_transform_error = (
            0.0
        )

        max_radius_difference = (
            0.0
        )

        max_speed_difference = (
            0.0
        )

        first_transform = None
        last_transform = None

        for index, (
            m50_row,
            j2000_row,
        ) in enumerate(
            zip(
                m50_rows,
                j2000_rows,
            ),
            start=1,
        ):
            if (
                m50_row[
                    "timestamp_utc"
                ]
                != j2000_row[
                    "timestamp_utc"
                ]
            ):
                fail(
                    f"timestamp mismatch "
                    f"at record {index}"
                )

            timestamp = (
                m50_row[
                    "timestamp_utc"
                ]
            )

            et = utc_to_et(
                timestamp
            )

            transform = np.asarray(
                spice.sxform(
                    "B1950",
                    "J2000",
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

            source_state = np.array(
                [
                    float(
                        m50_row[
                            "x_m50_km"
                        ]
                    ),
                    float(
                        m50_row[
                            "y_m50_km"
                        ]
                    ),
                    float(
                        m50_row[
                            "z_m50_km"
                        ]
                    ),
                    float(
                        m50_row[
                            "vx_m50_km_s"
                        ]
                    ),
                    float(
                        m50_row[
                            "vy_m50_km_s"
                        ]
                    ),
                    float(
                        m50_row[
                            "vz_m50_km_s"
                        ]
                    ),
                ],
                dtype=float,
            )

            expected = (
                transform
                @ source_state
            )

            stored = np.array(
                [
                    float(
                        j2000_row[
                            "x_j2000_km"
                        ]
                    ),
                    float(
                        j2000_row[
                            "y_j2000_km"
                        ]
                    ),
                    float(
                        j2000_row[
                            "z_j2000_km"
                        ]
                    ),
                    float(
                        j2000_row[
                            "vx_j2000_km_s"
                        ]
                    ),
                    float(
                        j2000_row[
                            "vy_j2000_km_s"
                        ]
                    ),
                    float(
                        j2000_row[
                            "vz_j2000_km_s"
                        ]
                    ),
                ],
                dtype=float,
            )

            position_error = (
                np.linalg.norm(
                    expected[:3]
                    - stored[:3]
                )
            )

            velocity_error = (
                np.linalg.norm(
                    expected[3:]
                    - stored[3:]
                )
            )

            max_position_transform_error = max(
                max_position_transform_error,
                position_error,
            )

            max_velocity_transform_error = max(
                max_velocity_transform_error,
                velocity_error,
            )

            source_radius = (
                np.linalg.norm(
                    source_state[:3]
                )
            )

            target_radius = (
                np.linalg.norm(
                    stored[:3]
                )
            )

            source_speed = (
                np.linalg.norm(
                    source_state[3:]
                )
            )

            target_speed = (
                np.linalg.norm(
                    stored[3:]
                )
            )

            max_radius_difference = max(
                max_radius_difference,
                abs(
                    source_radius
                    - target_radius
                ),
            )

            max_speed_difference = max(
                max_speed_difference,
                abs(
                    source_speed
                    - target_speed
                ),
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

        time_variation = (
            np.max(
                np.abs(
                    last_transform
                    - first_transform
                )
            )
        )

        if abs(
            determinant - 1.0
        ) > 1e-12:
            fail(
                "rotation determinant "
                "is not approximately 1"
            )

        if (
            orthogonality_error
            > 1e-12
        ):
            fail(
                "rotation matrix is "
                "not sufficiently orthogonal"
            )

        if (
            max_position_transform_error
            > 1e-10
        ):
            fail(
                "stored transformed "
                "position does not match "
                "independent SPICE transform"
            )

        if (
            max_velocity_transform_error
            > 1e-12
        ):
            fail(
                "stored transformed "
                "velocity does not match "
                "independent SPICE transform"
            )

        if (
            max_radius_difference
            > 1e-9
        ):
            fail(
                "radius was not preserved"
            )

        if (
            max_speed_difference
            > 1e-12
        ):
            fail(
                "speed was not preserved"
            )

        # -----------------------------------------------------
        # Empirical Phase 1 -> Phase 2 handoff check
        # -----------------------------------------------------

        (
            phase1_time,
            phase1_state,
        ) = load_phase1_final()

        first_m50 = (
            m50_rows[0]
        )

        first_j2000 = (
            j2000_rows[0]
        )

        entry_time = (
            first_m50[
                "timestamp_utc"
            ]
        )

        gap = (
            utc_to_et(
                entry_time
            )
            - utc_to_et(
                phase1_time
            )
        )

        propagated_phase1 = (
            propagate_two_body(
                phase1_state,
                gap,
            )
        )

        raw_m50_state = np.array(
            [
                float(
                    first_m50[
                        "x_m50_km"
                    ]
                ),
                float(
                    first_m50[
                        "y_m50_km"
                    ]
                ),
                float(
                    first_m50[
                        "z_m50_km"
                    ]
                ),
                float(
                    first_m50[
                        "vx_m50_km_s"
                    ]
                ),
                float(
                    first_m50[
                        "vy_m50_km_s"
                    ]
                ),
                float(
                    first_m50[
                        "vz_m50_km_s"
                    ]
                ),
            ],
            dtype=float,
        )

        transformed_state = np.array(
            [
                float(
                    first_j2000[
                        "x_j2000_km"
                    ]
                ),
                float(
                    first_j2000[
                        "y_j2000_km"
                    ]
                ),
                float(
                    first_j2000[
                        "z_j2000_km"
                    ]
                ),
                float(
                    first_j2000[
                        "vx_j2000_km_s"
                    ]
                ),
                float(
                    first_j2000[
                        "vy_j2000_km_s"
                    ]
                ),
                float(
                    first_j2000[
                        "vz_j2000_km_s"
                    ]
                ),
            ],
            dtype=float,
        )

        raw_position_difference = (
            np.linalg.norm(
                raw_m50_state[:3]
                - propagated_phase1[:3]
            )
        )

        raw_velocity_difference = (
            np.linalg.norm(
                raw_m50_state[3:]
                - propagated_phase1[3:]
            )
        )

        transformed_position_difference = (
            np.linalg.norm(
                transformed_state[:3]
                - propagated_phase1[:3]
            )
        )

        transformed_velocity_difference = (
            np.linalg.norm(
                transformed_state[3:]
                - propagated_phase1[3:]
            )
        )

        position_improvement = (
            raw_position_difference
            / transformed_position_difference
        )

        velocity_improvement = (
            raw_velocity_difference
            / transformed_velocity_difference
        )

        if (
            position_improvement
            < 10.0
        ):
            fail(
                "B1950->J2000 does not "
                "materially improve "
                "position continuity"
            )

        if (
            velocity_improvement
            < 10.0
        ):
            fail(
                "B1950->J2000 does not "
                "materially improve "
                "velocity continuity"
            )

        print()
        print(
            "Artemis II Entry Frame "
            "Transform Validation"
        )

        print(
            "--------------------------------"
        )

        print(
            f"Records checked: "
            f"{len(j2000_rows)}"
        )

        print()
        print(
            "SPICE mapping:"
        )

        print(
            "  M50 source label"
        )

        print(
            "  -> B1950 analysis proxy"
        )

        print(
            "  -> J2000"
        )

        print()
        print(
            "Rotation determinant:"
        )

        print(
            f"  {determinant:.15f}"
        )

        print(
            "Orthogonality error:"
        )

        print(
            f"  "
            f"{orthogonality_error:.12e}"
        )

        print(
            "Transform time variation:"
        )

        print(
            f"  "
            f"{time_variation:.12e}"
        )

        print()
        print(
            "Maximum stored transform errors:"
        )

        print(
            "  Position: "
            f"{max_position_transform_error:.12e} km"
        )

        print(
            "  Velocity: "
            f"{max_velocity_transform_error:.12e} km/s"
        )

        print()
        print(
            "Magnitude preservation:"
        )

        print(
            "  Radius: "
            f"{max_radius_difference:.12e} km"
        )

        print(
            "  Speed:  "
            f"{max_speed_difference:.12e} km/s"
        )

        print()
        print(
            "Phase 1 -> Phase 2 handoff"
        )

        print(
            "--------------------------"
        )

        print(
            f"Gap: "
            f"{gap:.6f} s"
        )

        print()
        print(
            "Untransformed M50-as-J2000:"
        )

        print(
            "  Position difference: "
            f"{raw_position_difference:.6f} km"
        )

        print(
            "  Velocity difference: "
            f"{raw_velocity_difference * 1000.0:.6f} m/s"
        )

        print()
        print(
            "B1950 -> J2000:"
        )

        print(
            "  Position difference: "
            f"{transformed_position_difference:.6f} km"
        )

        print(
            "  Velocity difference: "
            f"{transformed_velocity_difference * 1000.0:.6f} m/s"
        )

        print()
        print(
            "Improvement:"
        )

        print(
            "  Position: "
            f"{position_improvement:.3f}x"
        )

        print(
            "  Velocity: "
            f"{velocity_improvement:.3f}x"
        )

        print()
        print(
            "NOTE: handoff differences are "
            "not navigation errors."
        )

        print(
            "The comparison uses a short "
            "two-body propagation model."
        )

        print()
        print(
            "OK: entry frame transformation "
            "and empirical handoff continuity "
            "validated."
        )

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()
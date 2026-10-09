from __future__ import annotations

import csv
import math
from datetime import datetime, timezone
from pathlib import Path


RTN_PATH = Path(
    "data/processed/trajectory/oem_rtn_residuals.csv"
)

COMPARISON_PATH = Path(
    "data/processed/trajectory/oem_comparison_detail.csv"
)

POSITION_TOLERANCE_KM = 1e-6
VELOCITY_TOLERANCE_M_S = 1e-6


def normalize_timestamp(value: str) -> str:
    dt = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return (
        dt.astimezone(timezone.utc)
        .isoformat()
    )


def main():
    scalar_lookup = {}

    with COMPARISON_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            key = (
                row["product"],
                normalize_timestamp(
                    row[
                        "comparison_timestamp_utc"
                    ]
                ),
            )

            scalar_lookup[key] = {
                "position_km":
                    float(
                        row[
                            "position_difference_km"
                        ]
                    ),

                "velocity_m_s":
                    float(
                        row[
                            "velocity_difference_m_s"
                        ]
                    ),
            }

    row_count = 0

    max_position_component_error = 0.0
    max_velocity_component_error = 0.0

    max_position_scalar_error = 0.0
    max_velocity_scalar_error = 0.0

    missing_scalar_rows = 0

    with RTN_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            row_count += 1

            dr_r = float(
                row["delta_r_radial_km"]
            )

            dr_t = float(
                row["delta_r_along_track_km"]
            )

            dr_n = float(
                row["delta_r_cross_track_km"]
            )

            stored_dr_norm = float(
                row["delta_r_norm_km"]
            )

            dv_r = float(
                row["delta_v_radial_m_s"]
            )

            dv_t = float(
                row["delta_v_along_track_m_s"]
            )

            dv_n = float(
                row["delta_v_cross_track_m_s"]
            )

            stored_dv_norm = float(
                row["delta_v_norm_m_s"]
            )

            calculated_dr_norm = math.sqrt(
                dr_r**2
                + dr_t**2
                + dr_n**2
            )

            calculated_dv_norm = math.sqrt(
                dv_r**2
                + dv_t**2
                + dv_n**2
            )

            position_component_error = abs(
                calculated_dr_norm
                - stored_dr_norm
            )

            velocity_component_error = abs(
                calculated_dv_norm
                - stored_dv_norm
            )

            max_position_component_error = max(
                max_position_component_error,
                position_component_error,
            )

            max_velocity_component_error = max(
                max_velocity_component_error,
                velocity_component_error,
            )

            key = (
                row["product"],
                normalize_timestamp(
                    row["timestamp_utc"]
                ),
            )

            scalar = scalar_lookup.get(
                key
            )

            if scalar is None:
                missing_scalar_rows += 1
                continue

            position_scalar_error = abs(
                stored_dr_norm
                - scalar["position_km"]
            )

            velocity_scalar_error = abs(
                stored_dv_norm
                - scalar["velocity_m_s"]
            )

            max_position_scalar_error = max(
                max_position_scalar_error,
                position_scalar_error,
            )

            max_velocity_scalar_error = max(
                max_velocity_scalar_error,
                velocity_scalar_error,
            )

    print()
    print("RTN Residual Validation")
    print("-----------------------")

    print(
        f"Rows checked: "
        f"{row_count}"
    )

    print(
        "Missing scalar comparison rows: "
        f"{missing_scalar_rows}"
    )

    print()
    print(
        "Maximum RTN component -> "
        "stored position norm error:"
    )

    print(
        f"  {max_position_component_error:.12e} km"
    )

    print(
        "Maximum RTN component -> "
        "stored velocity norm error:"
    )

    print(
        f"  {max_velocity_component_error:.12e} m/s"
    )

    print()
    print(
        "Maximum RTN position norm -> "
        "Phase 1E scalar error:"
    )

    print(
        f"  {max_position_scalar_error:.12e} km"
    )

    print(
        "Maximum RTN velocity norm -> "
        "Phase 1E scalar error:"
    )

    print(
        f"  {max_velocity_scalar_error:.12e} m/s"
    )

    errors = []

    if missing_scalar_rows:
        errors.append(
            "Some RTN rows could not be matched "
            "to Phase 1E scalar comparisons."
        )

    if (
        max_position_component_error
        > POSITION_TOLERANCE_KM
    ):
        errors.append(
            "RTN position components do not "
            "preserve vector magnitude."
        )

    if (
        max_velocity_component_error
        > VELOCITY_TOLERANCE_M_S
    ):
        errors.append(
            "RTN velocity components do not "
            "preserve vector magnitude."
        )

    if (
        max_position_scalar_error
        > POSITION_TOLERANCE_KM
    ):
        errors.append(
            "RTN position norms do not match "
            "Phase 1E scalar comparisons."
        )

    if (
        max_velocity_scalar_error
        > VELOCITY_TOLERANCE_M_S
    ):
        errors.append(
            "RTN velocity norms do not match "
            "Phase 1E scalar comparisons."
        )

    if errors:
        print()
        print("VALIDATION FAILED")

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    print()
    print(
        "OK: RTN decomposition preserves "
        "position and velocity residual magnitudes."
    )


if __name__ == "__main__":
    main()
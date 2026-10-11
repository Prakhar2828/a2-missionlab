from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pymsis
from pymsis.utils import get_f107_ap


ROOT = Path(__file__).resolve().parents[2]

GEOMETRY_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_geometry.csv"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_msis_drivers.csv"
)

OUTPUT_METADATA = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_msis_environment.json"
)

SOURCE_FILENAME = "SW-All.csv"

SOURCE_URL = (
    "https://celestrak.org/"
    "SpaceData/SW-All.csv"
)

EXPECTED_SOURCE_SHA256 = (
    "50130BC78F48B02FEC4424DA59098A06"
    "5D5DE06562DB73BBCC3631BCCBFFBAEE"
)

EXPECTED_PYMSIS_VERSION = "0.12.0"

MODEL_VERSION = 2.0

GEOMAGNETIC_ACTIVITY = -1


def sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as f:
        while True:
            chunk = f.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return (
        digest.hexdigest()
        .upper()
    )


def find_space_weather_source() -> Path:
    package_dir = Path(
        pymsis.__file__
    ).resolve().parent

    matches = list(
        package_dir.rglob(
            SOURCE_FILENAME
        )
    )

    if not matches:
        raise SystemExit(
            "Could not find SW-All.csv "
            "inside the pymsis package tree. "
            "Run get_f107_ap once first."
        )

    if len(matches) > 1:
        raise SystemExit(
            "Multiple SW-All.csv files found:\n"
            + "\n".join(
                str(path)
                for path in matches
            )
        )

    return matches[0]


def main():
    if (
        pymsis.__version__
        != EXPECTED_PYMSIS_VERSION
    ):
        raise SystemExit(
            "Unexpected pymsis version.\n"
            f"Expected: {EXPECTED_PYMSIS_VERSION}\n"
            f"Observed: {pymsis.__version__}"
        )

    if not GEOMETRY_CSV.exists():
        raise SystemExit(
            f"Missing geometry file:\n"
            f"{GEOMETRY_CSV}"
        )

    with GEOMETRY_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        geometry_rows = list(
            csv.DictReader(f)
        )

    if len(
        geometry_rows
    ) != 819:
        raise SystemExit(
            f"Expected 819 trajectory states, "
            f"found {len(geometry_rows)}"
        )

    dates = np.array(
        [
            np.datetime64(
                row[
                    "timestamp_utc"
                ].replace(
                    "Z",
                    ""
                )
            )
            for row
            in geometry_rows
        ]
    )

    # This uses pymsis only to reconstruct
    # the exact historical driver vectors.
    # The resulting snapshot is committed so
    # normal future analysis does not depend
    # on a mutable external SW-All.csv file.
    f107, f107a, aps = get_f107_ap(
        dates
    )

    source_path = (
        find_space_weather_source()
    )

    source_hash = sha256(
        source_path
    )

    if (
        source_hash
        != EXPECTED_SOURCE_SHA256
    ):
        raise SystemExit(
            "SW-All.csv differs from the "
            "source used during Phase 2E.1 "
            "inspection.\n"
            f"Expected: "
            f"{EXPECTED_SOURCE_SHA256}\n"
            f"Observed: "
            f"{source_hash}\n\n"
            "Do not silently regenerate the "
            "reference-driver snapshot from "
            "a different source revision."
        )

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "timestamp_utc",
        "f107",
        "f107a",
        "ap_daily",
        "ap_current_3h",
        "ap_3h_prior",
        "ap_6h_prior",
        "ap_9h_prior",
        "ap_12_to_33h_average",
        "ap_36_to_57h_average",
    ]

    with OUTPUT_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )

        writer.writeheader()

        for i, row in enumerate(
            geometry_rows
        ):
            writer.writerow(
                {
                    "timestamp_utc":
                        row[
                            "timestamp_utc"
                        ],

                    "f107":
                        float(
                            f107[i]
                        ),

                    "f107a":
                        float(
                            f107a[i]
                        ),

                    "ap_daily":
                        float(
                            aps[i, 0]
                        ),

                    "ap_current_3h":
                        float(
                            aps[i, 1]
                        ),

                    "ap_3h_prior":
                        float(
                            aps[i, 2]
                        ),

                    "ap_6h_prior":
                        float(
                            aps[i, 3]
                        ),

                    "ap_9h_prior":
                        float(
                            aps[i, 4]
                        ),

                    "ap_12_to_33h_average":
                        float(
                            aps[i, 5]
                        ),

                    "ap_36_to_57h_average":
                        float(
                            aps[i, 6]
                        ),
                }
            )

    driver_snapshot_hash = sha256(
        OUTPUT_CSV
    )

    metadata = {
        "mission":
            "Artemis II",

        "purpose":
            (
                "Pinned historical space-weather "
                "drivers for Phase 2E atmospheric "
                "reconstruction."
            ),

        "provenance":
            "MODEL_INPUT",

        "atmosphere_model": {
            "name":
                "NRLMSIS",

            "version":
                MODEL_VERSION,

            "implementation":
                "pymsis",

            "pymsis_version":
                pymsis.__version__,

            "geomagnetic_activity":
                GEOMAGNETIC_ACTIVITY,

            "geomagnetic_interpretation":
                (
                    "Storm-time mode using "
                    "the full seven-element "
                    "Ap history vector."
                ),
        },

        "space_weather_source": {
            "provider":
                "CelesTrak",

            "url":
                SOURCE_URL,

            "filename":
                SOURCE_FILENAME,

            "local_source_size_bytes":
                source_path.stat().st_size,

            "sha256":
                source_hash,
        },

        "driver_snapshot": {
            "filename":
                OUTPUT_CSV.name,

            "sha256":
                driver_snapshot_hash,

            "records":
                len(
                    geometry_rows
                ),

            "start_utc":
                geometry_rows[0][
                    "timestamp_utc"
                ],

            "stop_utc":
                geometry_rows[-1][
                    "timestamp_utc"
                ],

            "ap_vector_order": [
                "daily_ap",
                "current_3h_ap",
                "3h_prior_ap",
                "6h_prior_ap",
                "9h_prior_ap",
                "12_to_33h_average_ap",
                "36_to_57h_average_ap",
            ],
        },

        "observed_driver_range": {
            "distinct_f107":
                sorted(
                    float(value)
                    for value in np.unique(
                        f107
                    )
                ),

            "distinct_f107a":
                sorted(
                    float(value)
                    for value in np.unique(
                        f107a
                    )
                ),

            "distinct_current_3h_ap":
                sorted(
                    float(value)
                    for value in np.unique(
                        aps[:, 1]
                    )
                ),
        },

        "utc_boundary_control": {
            "boundary":
                (
                    "2026-04-10T23:59:59.866000Z "
                    "to "
                    "2026-04-11T00:00:00.866000Z"
                ),

            "observed_altitude_change_m":
                -164.736,

            "observed_density_change_percent":
                2.142846275,

            "driver_only_density_effect_percent":
                0.0,

            "fixed_driver_geometry_time_change_percent":
                2.142846275,

            "interpretation":
                (
                    "The modeled density change "
                    "across midnight is attributable "
                    "to trajectory descent through "
                    "the atmospheric density gradient. "
                    "The F10.7/F10.7a/Ap driver swap "
                    "produced no measurable density "
                    "effect at these approximately "
                    "47-km states."
                ),
        },

        "interpretation_limits": [
            (
                "These values are empirical-model "
                "forcing inputs, not spacecraft "
                "measurements."
            ),
            (
                "The committed driver snapshot is "
                "used for reproducibility rather "
                "than silently consuming future "
                "updates to SW-All.csv."
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
        "Artemis II MSIS Driver Capture"
    )

    print(
        "--------------------------------"
    )

    print(
        f"pymsis: "
        f"{pymsis.__version__}"
    )

    print(
        "NRLMSIS version: "
        f"{MODEL_VERSION}"
    )

    print(
        f"Records: "
        f"{len(geometry_rows)}"
    )

    print()
    print(
        "Source:"
    )

    print(
        f"  {source_path}"
    )

    print(
        f"  Size: "
        f"{source_path.stat().st_size} bytes"
    )

    print(
        f"  SHA256: "
        f"{source_hash}"
    )

    print()
    print(
        "Driver snapshot:"
    )

    print(
        f"  "
        f"{OUTPUT_CSV.relative_to(ROOT)}"
    )

    print(
        f"  SHA256: "
        f"{driver_snapshot_hash}"
    )

    print()
    print(
        "Distinct F10.7:"
    )

    for value in np.unique(
        f107
    ):
        print(
            f"  {float(value):.3f}"
        )

    print(
        "Distinct F10.7a:"
    )

    for value in np.unique(
        f107a
    ):
        print(
            f"  {float(value):.3f}"
        )

    print(
        "Distinct current 3-hour Ap:"
    )

    for value in np.unique(
        aps[:, 1]
    ):
        print(
            f"  {float(value):.3f}"
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


if __name__ == "__main__":
    main()
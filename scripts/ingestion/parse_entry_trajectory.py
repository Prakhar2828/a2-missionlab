from __future__ import annotations

import csv
import io
import json
import math
import re
import statistics
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SOURCE_ARCHIVE = (
    ROOT
    / "data"
    / "raw"
    / "arow"
    / "all-artemis-ii-oem-files.zip"
)

NESTED_ARCHIVE_NAME = (
    "2026.04.10 - Post-RTC3 to EI.zip"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "entry"
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "entry_trajectory_m50.csv"
)

OUTPUT_METADATA = (
    OUTPUT_DIR
    / "entry_trajectory_metadata.json"
)

FT_TO_KM = 0.0003048

NUMBER_RE = re.compile(
    r"[+-]?"
    r"(?:\d+(?:\.\d*)?|\.\d+)"
    r"(?:[Ee][+-]?\d+)?"
)


def seconds_of_year_to_utc(
    year: int,
    seconds: float,
) -> datetime:
    return (
        datetime(
            year,
            1,
            1,
            tzinfo=timezone.utc,
        )
        + timedelta(
            seconds=seconds
        )
    )


def format_utc(
    dt: datetime,
) -> str:
    return (
        dt.isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


def extract_numbers(
    line: str,
) -> list[float]:
    return [
        float(value)
        for value
        in NUMBER_RE.findall(
            line
        )
    ]


def load_source():
    if not SOURCE_ARCHIVE.exists():
        raise SystemExit(
            "Missing NASA AROW archive:\n"
            f"{SOURCE_ARCHIVE}"
        )

    with zipfile.ZipFile(
        SOURCE_ARCHIVE,
        "r",
    ) as outer:
        if (
            NESTED_ARCHIVE_NAME
            not in outer.namelist()
        ):
            raise SystemExit(
                "Missing nested entry archive:\n"
                f"{NESTED_ARCHIVE_NAME}"
            )

        nested_bytes = outer.read(
            NESTED_ARCHIVE_NAME
        )

    with zipfile.ZipFile(
        io.BytesIO(
            nested_bytes
        ),
        "r",
    ) as nested:
        files = [
            info
            for info in nested.infolist()
            if not info.is_dir()
        ]

        if len(files) != 1:
            raise SystemExit(
                "Expected exactly one file "
                "inside the entry archive, "
                f"found {len(files)}."
            )

        source_info = files[0]

        raw = nested.read(
            source_info.filename
        )

    try:
        text = raw.decode(
            "utf-8"
        )
    except UnicodeDecodeError:
        text = raw.decode(
            "latin-1"
        )

    return (
        source_info.filename,
        text.splitlines(),
    )


def main():
    (
        source_filename,
        lines,
    ) = load_source()

    if len(lines) < 3:
        raise SystemExit(
            "Entry trajectory file "
            "contains too few lines."
        )

    format_header = (
        lines[0].split()
    )

    units_header = (
        lines[1].split()
    )

    if len(format_header) != 2:
        raise SystemExit(
            "Unexpected PROP_MAN header."
        )

    if len(units_header) != 8:
        raise SystemExit(
            "Unexpected entry metadata "
            "header structure."
        )

    format_identifier = (
        format_header[0]
    )

    format_version = (
        format_header[1]
    )

    year = int(
        units_header[0]
    )

    epoch_seconds = float(
        units_header[1]
    )

    start_offset_seconds = float(
        units_header[2]
    )

    header_duration_seconds = float(
        units_header[3]
    )

    frame = units_header[4]
    position_units = units_header[5]
    velocity_units = units_header[6]
    time_units = units_header[7]

    records = []

    for line_number, line in enumerate(
        lines[2:],
        start=3,
    ):
        values = extract_numbers(
            line
        )

        if len(values) != 8:
            raise SystemExit(
                f"Line {line_number}: "
                f"expected 8 numeric fields, "
                f"found {len(values)}."
            )

        if not all(
            math.isfinite(value)
            for value in values
        ):
            raise SystemExit(
                f"Line {line_number}: "
                "non-finite value."
            )

        (
            time_seconds,
            x_ft,
            y_ft,
            z_ft,
            vx_ft_s,
            vy_ft_s,
            vz_ft_s,
            auxiliary_scalar,
        ) = values

        timestamp = (
            seconds_of_year_to_utc(
                year,
                time_seconds,
            )
        )

        x_km = (
            x_ft
            * FT_TO_KM
        )

        y_km = (
            y_ft
            * FT_TO_KM
        )

        z_km = (
            z_ft
            * FT_TO_KM
        )

        vx_km_s = (
            vx_ft_s
            * FT_TO_KM
        )

        vy_km_s = (
            vy_ft_s
            * FT_TO_KM
        )

        vz_km_s = (
            vz_ft_s
            * FT_TO_KM
        )

        earth_center_distance_km = (
            math.sqrt(
                x_km**2
                + y_km**2
                + z_km**2
            )
        )

        inertial_speed_km_s = (
            math.sqrt(
                vx_km_s**2
                + vy_km_s**2
                + vz_km_s**2
            )
        )

        records.append(
            {
                "source_line":
                    line_number,

                "timestamp_utc":
                    format_utc(
                        timestamp
                    ),

                "time_seconds_of_year":
                    time_seconds,

                "seconds_from_reference_epoch":
                    (
                        time_seconds
                        - epoch_seconds
                    ),

                "x_m50_ft":
                    x_ft,

                "y_m50_ft":
                    y_ft,

                "z_m50_ft":
                    z_ft,

                "vx_m50_ft_s":
                    vx_ft_s,

                "vy_m50_ft_s":
                    vy_ft_s,

                "vz_m50_ft_s":
                    vz_ft_s,

                "auxiliary_scalar_raw":
                    auxiliary_scalar,

                "x_m50_km":
                    x_km,

                "y_m50_km":
                    y_km,

                "z_m50_km":
                    z_km,

                "vx_m50_km_s":
                    vx_km_s,

                "vy_m50_km_s":
                    vy_km_s,

                "vz_m50_km_s":
                    vz_km_s,

                "earth_center_distance_km":
                    earth_center_distance_km,

                "inertial_speed_km_s":
                    inertial_speed_km_s,
            }
        )

    if not records:
        raise SystemExit(
            "No trajectory records parsed."
        )

    first_time = records[0][
        "time_seconds_of_year"
    ]

    last_time = records[-1][
        "time_seconds_of_year"
    ]

    steps = [
        current[
            "time_seconds_of_year"
        ]
        - previous[
            "time_seconds_of_year"
        ]
        for previous, current
        in zip(
            records[:-1],
            records[1:],
        )
    ]

    expected_first_time = (
        epoch_seconds
        + start_offset_seconds
    )

    actual_duration = (
        last_time
        - first_time
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = list(
        records[0].keys()
    )

    with OUTPUT_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            records
        )

    metadata = {
        "source": {
            "outer_archive":
                str(
                    SOURCE_ARCHIVE.relative_to(
                        ROOT
                    )
                ),

            "nested_archive":
                NESTED_ARCHIVE_NAME,

            "source_file":
                source_filename,
        },

        "format": {
            "identifier":
                format_identifier,

            "version":
                format_version,

            "frame":
                frame,

            "position_units":
                position_units,

            "velocity_units":
                velocity_units,

            "time_units":
                time_units,
        },

        "time": {
            "year":
                year,

            "reference_epoch_seconds_of_year":
                epoch_seconds,

            "reference_epoch_utc":
                format_utc(
                    seconds_of_year_to_utc(
                        year,
                        epoch_seconds,
                    )
                ),

            "start_offset_seconds":
                start_offset_seconds,

            "expected_first_time_seconds_of_year":
                expected_first_time,

            "header_duration_seconds":
                header_duration_seconds,

            "actual_duration_seconds":
                actual_duration,

            "start_utc":
                records[0][
                    "timestamp_utc"
                ],

            "stop_utc":
                records[-1][
                    "timestamp_utc"
                ],
        },

        "records": {
            "count":
                len(records),

            "cadence_min_seconds":
                min(steps),

            "cadence_max_seconds":
                max(steps),

            "cadence_median_seconds":
                statistics.median(
                    steps
                ),
        },

        "auxiliary_scalar": {
            "status":
                "UNRESOLVED",

            "interpretation":
                (
                    "The eighth numeric field "
                    "is preserved exactly as "
                    "provided by the source. "
                    "No physical meaning or "
                    "units are assigned yet."
                ),

            "first":
                records[0][
                    "auxiliary_scalar_raw"
                ],

            "last":
                records[-1][
                    "auxiliary_scalar_raw"
                ],

            "minimum":
                min(
                    record[
                        "auxiliary_scalar_raw"
                    ]
                    for record
                    in records
                ),

            "maximum":
                max(
                    record[
                        "auxiliary_scalar_raw"
                    ]
                    for record
                    in records
                ),
        },

        "interpretation_limits": [
            (
                "M50 source-state coordinates "
                "have not yet been transformed "
                "to EME2000/J2000."
            ),
            (
                "Earth-center distance is not "
                "geodetic altitude."
            ),
            (
                "The archive filename is not "
                "assumed to define exact state "
                "coverage semantics."
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
        "Artemis II High-Rate Entry "
        "Trajectory Parser"
    )
    print(
        "--------------------------------"
    )

    print(
        f"Source: {source_filename}"
    )

    print(
        f"Format: "
        f"{format_identifier} "
        f"{format_version}"
    )

    print(
        f"Frame: {frame}"
    )

    print(
        f"Units: "
        f"{position_units} "
        f"{velocity_units} "
        f"{time_units}"
    )

    print()
    print(
        f"Records: {len(records)}"
    )

    print(
        f"Start:   "
        f"{records[0]['timestamp_utc']}"
    )

    print(
        f"Stop:    "
        f"{records[-1]['timestamp_utc']}"
    )

    print(
        f"Duration: "
        f"{actual_duration:.3f} s"
    )

    print()
    print(
        "First Earth-center distance: "
        f"{records[0]['earth_center_distance_km']:.3f} km"
    )

    print(
        "First inertial speed:        "
        f"{records[0]['inertial_speed_km_s']:.6f} km/s"
    )

    print(
        "Last Earth-center distance:  "
        f"{records[-1]['earth_center_distance_km']:.3f} km"
    )

    print(
        "Last inertial speed:         "
        f"{records[-1]['inertial_speed_km_s']:.6f} km/s"
    )

    print()
    print(
        "Auxiliary scalar: "
        "UNRESOLVED"
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
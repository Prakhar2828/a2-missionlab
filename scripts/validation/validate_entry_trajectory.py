from __future__ import annotations

import csv
import io
import json
import math
import re
import zipfile
from datetime import datetime
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

ENTRY_DIR = (
    ROOT
    / "data"
    / "processed"
    / "entry"
)

CSV_PATH = (
    ENTRY_DIR
    / "entry_trajectory_m50.csv"
)

METADATA_PATH = (
    ENTRY_DIR
    / "entry_trajectory_metadata.json"
)

FT_TO_KM = 0.0003048

NUMBER_RE = re.compile(
    r"[+-]?"
    r"(?:\d+(?:\.\d*)?|\.\d+)"
    r"(?:[Ee][+-]?\d+)?"
)

NUMERIC_COLUMNS = [
    "source_line",
    "time_seconds_of_year",
    "seconds_from_reference_epoch",
    "x_m50_ft",
    "y_m50_ft",
    "z_m50_ft",
    "vx_m50_ft_s",
    "vy_m50_ft_s",
    "vz_m50_ft_s",
    "auxiliary_scalar_raw",
    "x_m50_km",
    "y_m50_km",
    "z_m50_km",
    "vx_m50_km_s",
    "vy_m50_km_s",
    "vz_m50_km_s",
    "earth_center_distance_km",
    "inertial_speed_km_s",
]


def fail(
    message: str,
):
    raise SystemExit(
        f"VALIDATION FAILED: {message}"
    )


def load_raw_records():
    if not SOURCE_ARCHIVE.exists():
        fail(
            "NASA AROW source archive "
            f"does not exist: {SOURCE_ARCHIVE}"
        )

    with zipfile.ZipFile(
        SOURCE_ARCHIVE,
        "r",
    ) as outer:
        if (
            NESTED_ARCHIVE_NAME
            not in outer.namelist()
        ):
            fail(
                "nested entry archive "
                "is missing"
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
            fail(
                "expected exactly one "
                "entry trajectory file "
                "inside nested archive"
            )

        raw = nested.read(
            files[0].filename
        )

    try:
        text = raw.decode(
            "utf-8"
        )
    except UnicodeDecodeError:
        text = raw.decode(
            "latin-1"
        )

    lines = text.splitlines()

    if len(lines) < 3:
        fail(
            "source trajectory file "
            "contains too few lines"
        )

    header1 = (
        lines[0].split()
    )

    header2 = (
        lines[1].split()
    )

    raw_records = []

    for line_number, line in enumerate(
        lines[2:],
        start=3,
    ):
        values = [
            float(value)
            for value
            in NUMBER_RE.findall(
                line
            )
        ]

        if len(values) != 8:
            fail(
                f"raw line {line_number} "
                f"contains {len(values)} "
                "numeric fields instead "
                "of 8"
            )

        if not all(
            math.isfinite(value)
            for value in values
        ):
            fail(
                f"raw line {line_number} "
                "contains a non-finite "
                "numeric value"
            )

        raw_records.append(
            values
        )

    return (
        header1,
        header2,
        raw_records,
    )


def parse_timestamp(
    value: str,
) -> datetime:
    try:
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError as exc:
        fail(
            f"invalid UTC timestamp: "
            f"{value}"
        )

        raise exc


def validate_numeric_row(
    row,
    record_number,
):
    for column in NUMERIC_COLUMNS:
        if column not in row:
            fail(
                f"missing numeric column "
                f"{column}"
            )

        try:
            value = float(
                row[column]
            )
        except ValueError:
            fail(
                f"record {record_number}: "
                f"{column} is not numeric"
            )

        if not math.isfinite(
            value
        ):
            fail(
                f"record {record_number}: "
                f"{column} is not finite"
            )


def main():
    if not CSV_PATH.exists():
        fail(
            f"missing processed CSV: "
            f"{CSV_PATH}"
        )

    if not METADATA_PATH.exists():
        fail(
            f"missing metadata JSON: "
            f"{METADATA_PATH}"
        )

    with METADATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        metadata = json.load(
            f
        )

    with CSV_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        processed = list(
            csv.DictReader(
                f
            )
        )

    (
        raw_header1,
        raw_header2,
        raw_records,
    ) = load_raw_records()

    # ---------------------------------------------------------
    # Header validation
    # ---------------------------------------------------------

    if raw_header1 != [
        "PROP_MAN",
        "11.0",
    ]:
        fail(
            "unexpected PROP_MAN header"
        )

    if len(
        raw_header2
    ) != 8:
        fail(
            "unexpected source metadata "
            "header length"
        )

    if raw_header2[4:] != [
        "M50",
        "FT",
        "FPS",
        "SEC",
    ]:
        fail(
            "unexpected frame/unit header"
        )

    if (
        metadata["format"][
            "identifier"
        ]
        != "PROP_MAN"
    ):
        fail(
            "metadata format identifier "
            "does not match source"
        )

    if (
        metadata["format"][
            "version"
        ]
        != "11.0"
    ):
        fail(
            "metadata format version "
            "does not match source"
        )

    if (
        metadata["format"][
            "frame"
        ]
        != "M50"
    ):
        fail(
            "metadata frame is not M50"
        )

    if (
        metadata["format"][
            "position_units"
        ]
        != "FT"
    ):
        fail(
            "metadata position units "
            "are not FT"
        )

    if (
        metadata["format"][
            "velocity_units"
        ]
        != "FPS"
    ):
        fail(
            "metadata velocity units "
            "are not FPS"
        )

    if (
        metadata["format"][
            "time_units"
        ]
        != "SEC"
    ):
        fail(
            "metadata time units "
            "are not SEC"
        )

    # ---------------------------------------------------------
    # Record count validation
    # ---------------------------------------------------------

    if len(
        raw_records
    ) != len(
        processed
    ):
        fail(
            "raw/processed record "
            "count mismatch"
        )

    if len(
        processed
    ) != 819:
        fail(
            f"expected 819 records, "
            f"found {len(processed)}"
        )

    if (
        metadata["records"][
            "count"
        ]
        != 819
    ):
        fail(
            "metadata record count "
            "does not equal 819"
        )

    # ---------------------------------------------------------
    # Record-level validation
    # ---------------------------------------------------------

    times = []

    max_position_conversion_error = (
        0.0
    )

    max_velocity_conversion_error = (
        0.0
    )

    max_radius_reconstruction_error = (
        0.0
    )

    max_speed_reconstruction_error = (
        0.0
    )

    for record_number, (
        raw,
        row,
    ) in enumerate(
        zip(
            raw_records,
            processed,
        ),
        start=1,
    ):
        validate_numeric_row(
            row,
            record_number,
        )

        if (
            "timestamp_utc"
            not in row
        ):
            fail(
                "processed CSV is missing "
                "timestamp_utc"
            )

        parse_timestamp(
            row[
                "timestamp_utc"
            ]
        )

        source_line = int(
            float(
                row[
                    "source_line"
                ]
            )
        )

        expected_source_line = (
            record_number + 2
        )

        if (
            source_line
            != expected_source_line
        ):
            fail(
                f"record {record_number}: "
                "source-line provenance "
                "does not match"
            )

        raw_time = (
            raw[0]
        )

        processed_time = float(
            row[
                "time_seconds_of_year"
            ]
        )

        if abs(
            raw_time
            - processed_time
        ) > 1e-9:
            fail(
                f"record {record_number}: "
                "time mismatch"
            )

        times.append(
            processed_time
        )

        # -----------------------------------------------------
        # Preserve raw state exactly
        # -----------------------------------------------------

        raw_columns = [
            "x_m50_ft",
            "y_m50_ft",
            "z_m50_ft",
            "vx_m50_ft_s",
            "vy_m50_ft_s",
            "vz_m50_ft_s",
            "auxiliary_scalar_raw",
        ]

        for raw_value, column in zip(
            raw[1:],
            raw_columns,
        ):
            processed_value = float(
                row[
                    column
                ]
            )

            if abs(
                raw_value
                - processed_value
            ) > 1e-9:
                fail(
                    f"record {record_number}: "
                    f"raw field {column} "
                    "was not preserved"
                )

        # -----------------------------------------------------
        # Position unit conversion
        # -----------------------------------------------------

        raw_positions = (
            raw[1:4]
        )

        processed_positions = [
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
        ]

        for (
            raw_value,
            processed_value,
        ) in zip(
            raw_positions,
            processed_positions,
        ):
            expected = (
                raw_value
                * FT_TO_KM
            )

            error = abs(
                expected
                - processed_value
            )

            max_position_conversion_error = max(
                max_position_conversion_error,
                error,
            )

        # -----------------------------------------------------
        # Velocity unit conversion
        # -----------------------------------------------------

        raw_velocities = (
            raw[4:7]
        )

        processed_velocities = [
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
        ]

        for (
            raw_value,
            processed_value,
        ) in zip(
            raw_velocities,
            processed_velocities,
        ):
            expected = (
                raw_value
                * FT_TO_KM
            )

            error = abs(
                expected
                - processed_value
            )

            max_velocity_conversion_error = max(
                max_velocity_conversion_error,
                error,
            )

        # -----------------------------------------------------
        # Radius reconstruction
        # -----------------------------------------------------

        reconstructed_radius = (
            math.sqrt(
                sum(
                    value**2
                    for value
                    in processed_positions
                )
            )
        )

        stored_radius = float(
            row[
                "earth_center_distance_km"
            ]
        )

        radius_error = abs(
            reconstructed_radius
            - stored_radius
        )

        max_radius_reconstruction_error = max(
            max_radius_reconstruction_error,
            radius_error,
        )

        # -----------------------------------------------------
        # Speed reconstruction
        # -----------------------------------------------------

        reconstructed_speed = (
            math.sqrt(
                sum(
                    value**2
                    for value
                    in processed_velocities
                )
            )
        )

        stored_speed = float(
            row[
                "inertial_speed_km_s"
            ]
        )

        speed_error = abs(
            reconstructed_speed
            - stored_speed
        )

        max_speed_reconstruction_error = max(
            max_speed_reconstruction_error,
            speed_error,
        )

    # ---------------------------------------------------------
    # Time monotonicity and cadence
    # ---------------------------------------------------------

    for previous, current in zip(
        times[:-1],
        times[1:],
    ):
        if current <= previous:
            fail(
                "times are not strictly "
                "increasing"
            )

    steps = [
        current - previous
        for previous, current in zip(
            times[:-1],
            times[1:],
        )
    ]

    if len(
        steps
    ) != 818:
        fail(
            f"expected 818 time steps, "
            f"found {len(steps)}"
        )

    for index, step in enumerate(
        steps[:-1],
        start=1,
    ):
        if abs(
            step - 1.0
        ) > 1e-9:
            fail(
                f"non-terminal cadence "
                f"at interval {index} "
                f"is {step} s"
            )

    if abs(
        steps[-1]
        - 0.975
    ) > 1e-9:
        fail(
            "terminal cadence "
            f"is {steps[-1]} s, "
            "expected 0.975 s"
        )

    # ---------------------------------------------------------
    # Header timing relationships
    # ---------------------------------------------------------

    year = int(
        raw_header2[0]
    )

    epoch_seconds = float(
        raw_header2[1]
    )

    start_offset = float(
        raw_header2[2]
    )

    header_duration = float(
        raw_header2[3]
    )

    expected_first = (
        epoch_seconds
        + start_offset
    )

    if abs(
        times[0]
        - expected_first
    ) > 1e-9:
        fail(
            "first state does not equal "
            "epoch + start offset"
        )

    actual_duration = (
        times[-1]
        - times[0]
    )

    if abs(
        actual_duration
        - header_duration
    ) > 1e-9:
        fail(
            "record span does not match "
            "header duration"
        )

    if (
        metadata["time"][
            "year"
        ]
        != year
    ):
        fail(
            "metadata year mismatch"
        )

    if abs(
        metadata["time"][
            "reference_epoch_seconds_of_year"
        ]
        - epoch_seconds
    ) > 1e-9:
        fail(
            "metadata reference epoch "
            "mismatch"
        )

    if abs(
        metadata["time"][
            "start_offset_seconds"
        ]
        - start_offset
    ) > 1e-9:
        fail(
            "metadata start offset "
            "mismatch"
        )

    if abs(
        metadata["time"][
            "header_duration_seconds"
        ]
        - header_duration
    ) > 1e-9:
        fail(
            "metadata header duration "
            "mismatch"
        )

    # ---------------------------------------------------------
    # Auxiliary-field behavior
    # ---------------------------------------------------------

    auxiliary_values = [
        float(
            row[
                "auxiliary_scalar_raw"
            ]
        )
        for row in processed
    ]

    if (
        metadata[
            "auxiliary_scalar"
        ][
            "status"
        ]
        != "UNRESOLVED"
    ):
        fail(
            "auxiliary scalar should "
            "remain unresolved"
        )

    if abs(
        auxiliary_values[0]
        - 22855.0
    ) > 1e-9:
        fail(
            "unexpected first "
            "auxiliary scalar"
        )

    if abs(
        auxiliary_values[-1]
        - 20476.3
    ) > 1e-9:
        fail(
            "unexpected final "
            "auxiliary scalar"
        )

    # ---------------------------------------------------------
    # Final physical summaries
    # ---------------------------------------------------------

    radii = [
        float(
            row[
                "earth_center_distance_km"
            ]
        )
        for row in processed
    ]

    speeds = [
        float(
            row[
                "inertial_speed_km_s"
            ]
        )
        for row in processed
    ]

    print()
    print(
        "Artemis II Entry "
        "Trajectory Validation"
    )
    print(
        "--------------------------------"
    )

    print(
        f"Records checked: "
        f"{len(processed)}"
    )

    print()
    print(
        f"Start: "
        f"{processed[0]['timestamp_utc']}"
    )

    print(
        f"Stop:  "
        f"{processed[-1]['timestamp_utc']}"
    )

    print(
        f"Duration: "
        f"{actual_duration:.3f} s"
    )

    print()
    print(
        "Cadence:"
    )

    print(
        "  Regular intervals: "
        "1.000 s"
    )

    print(
        f"  Terminal interval: "
        f"{steps[-1]:.3f} s"
    )

    print()
    print(
        "Earth-center distance:"
    )

    print(
        f"  First: "
        f"{radii[0]:.3f} km"
    )

    print(
        f"  Last:  "
        f"{radii[-1]:.3f} km"
    )

    print()
    print(
        "Inertial speed:"
    )

    print(
        f"  First: "
        f"{speeds[0]:.6f} km/s"
    )

    print(
        f"  Last:  "
        f"{speeds[-1]:.6f} km/s"
    )

    print()
    print(
        "Auxiliary scalar "
        "(meaning unresolved):"
    )

    print(
        f"  First: "
        f"{auxiliary_values[0]:.3f}"
    )

    print(
        f"  Last:  "
        f"{auxiliary_values[-1]:.3f}"
    )

    print()
    print(
        "Maximum raw-to-km "
        "position conversion error:"
    )

    print(
        f"  "
        f"{max_position_conversion_error:.12e} km"
    )

    print(
        "Maximum raw-to-km/s "
        "velocity conversion error:"
    )

    print(
        f"  "
        f"{max_velocity_conversion_error:.12e} km/s"
    )

    print()
    print(
        "Maximum radius reconstruction "
        "error:"
    )

    print(
        f"  "
        f"{max_radius_reconstruction_error:.12e} km"
    )

    print(
        "Maximum speed reconstruction "
        "error:"
    )

    print(
        f"  "
        f"{max_speed_reconstruction_error:.12e} km/s"
    )

    print()
    print(
        "OK: high-rate entry trajectory "
        "structure, timing, units, raw-state "
        "preservation, and numeric conversion "
        "validated."
    )


if __name__ == "__main__":
    main()
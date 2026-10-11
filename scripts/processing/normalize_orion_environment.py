from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = (
    ROOT
    / "data"
    / "raw"
    / "pds"
    / "artemis2"
    / "orion_environment"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "eclss"
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "orion_environment_normalized.csv"
)

OUTPUT_METADATA = (
    OUTPUT_DIR
    / "orion_environment_metadata.json"
)

MISSION_CONFIG = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

LOGGER_FILES = {
    "1104": (
        "art002_086-162546_111-205046_"
        "hobo1104_raw_v01.csv"
    ),
    "1105": (
        "art002_086-162926_111-203826_"
        "hobo1105_raw_v01.csv"
    ),
}

UTC = timezone.utc

CDT = timezone(
    timedelta(
        hours=-5
    )
)

SPLASHDOWN_UTC = datetime(
    2026,
    4,
    11,
    0,
    7,
    0,
    tzinfo=UTC,
)


def load_mission_config() -> dict:
    if not MISSION_CONFIG.exists():
        raise SystemExit(
            "\nERROR: Missing mission "
            "configuration:\n"
            f"{MISSION_CONFIG}"
        )

    with MISSION_CONFIG.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def parse_iso_utc(
    value: str,
) -> datetime:
    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    ).astimezone(
        UTC
    )


def iso_z(
    value: datetime,
) -> str:
    return (
        value.astimezone(
            UTC
        )
        .isoformat(
            timespec="seconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def normalize_header(
    value: str,
) -> str:
    value = (
        value.strip()
        .lower()
    )

    value = value.replace(
        "°",
        "deg",
    )

    value = value.replace(
        "%",
        "pct",
    )

    value = re.sub(
        r"[^a-z0-9#]+",
        "_",
        value,
    )

    return value.strip(
        "_"
    )


def identify_columns(
    headers: list[str],
) -> dict[str, int]:
    normalized = [
        normalize_header(
            header
        )
        for header in headers
    ]

    columns: dict[str, int] = {}

    for index, header in enumerate(
        normalized
    ):
        if (
            "date" in header
            and "time" in header
        ):
            columns[
                "datetime"
            ] = index

        elif (
            "dew" in header
            and (
                "point" in header
                or "pt" in header
            )
        ):
            columns[
                "dew_point"
            ] = index

        elif (
            "temperature" in header
            or header.startswith(
                "temp"
            )
        ):
            columns[
                "temperature"
            ] = index

        elif (
            header == "rh"
            or header.startswith(
                "rh_"
            )
            or "relative_humidity" in header
        ):
            columns[
                "relative_humidity"
            ] = index

        elif (
            header == "#"
            or header.startswith(
                "sample"
            )
            or header == "number"
        ):
            columns[
                "sample"
            ] = index

    required = {
        "sample",
        "datetime",
        "temperature",
        "relative_humidity",
        "dew_point",
    }

    missing = (
        required
        - set(
            columns
        )
    )

    if missing:
        raise SystemExit(
            "\nERROR: Unable to identify "
            "all NASA PDS HOBO columns.\n\n"
            f"Original headers:\n"
            f"{headers}\n\n"
            f"Normalized headers:\n"
            f"{normalized}\n\n"
            f"Missing fields:\n"
            f"{sorted(missing)}"
        )

    return columns


def clean_datetime_text(
    value: str,
) -> str:
    value = value.strip()

    value = re.sub(
        r"\s+CDT$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\s+GMT-05:00$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\s+UTC-05:00$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    return value.strip()


def parse_source_datetime(
    value: str,
) -> datetime:
    cleaned = (
        clean_datetime_text(
            value
        )
    )

    formats = [
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%y %I:%M:%S %p",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(
                cleaned,
                fmt,
            )

            return parsed.replace(
                tzinfo=CDT
            )

        except ValueError:
            continue

    raise ValueError(
        "Unsupported NASA PDS "
        "environment timestamp: "
        f"{value!r}"
    )


def parse_float(
    value: str,
    field_name: str,
    row_number: int,
) -> float:
    cleaned = (
        value.strip()
    )

    try:
        return float(
            cleaned
        )

    except ValueError as exc:
        raise ValueError(
            f"Invalid {field_name} "
            f"at row {row_number}: "
            f"{value!r}"
        ) from exc


def parse_sample(
    value: str,
    row_number: int,
) -> int:
    cleaned = (
        value.strip()
    )

    try:
        return int(
            float(
                cleaned
            )
        )

    except ValueError as exc:
        raise ValueError(
            "Invalid sample number "
            f"at row {row_number}: "
            f"{value!r}"
        ) from exc


def format_met(
    seconds: float,
) -> str:
    sign = (
        "-"
        if seconds < 0
        else ""
    )

    total_seconds = int(
        round(
            abs(
                seconds
            )
        )
    )

    days, remainder = divmod(
        total_seconds,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    return (
        f"{sign}"
        f"{days:02d}:"
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


def classify_mission_period(
    timestamp_utc: datetime,
    launch_utc: datetime,
) -> str:
    if (
        timestamp_utc
        < launch_utc
    ):
        return "PRELAUNCH"

    if (
        timestamp_utc
        <= SPLASHDOWN_UTC
    ):
        return "IN_FLIGHT"

    return "POSTFLIGHT"


def numeric_summary(
    rows: list[dict],
    field: str,
) -> dict:
    values = [
        float(
            row[
                field
            ]
        )
        for row in rows
    ]

    return {
        "minimum": min(
            values
        ),
        "maximum": max(
            values
        ),
        "mean": (
            sum(
                values
            )
            / len(
                values
            )
        ),
    }


def parse_logger(
    logger_serial: str,
    filename: str,
    launch_utc: datetime,
) -> tuple[
    list[dict],
    dict,
]:
    path = (
        RAW_DIR
        / filename
    )

    if not path.exists():
        raise SystemExit(
            "\nERROR: Missing NASA PDS "
            "environment CSV:\n"
            f"{path}\n\n"
            "Run:\n"
            ".\\.venv\\Scripts\\python.exe "
            "scripts\\ingestion\\"
            "download_orion_environment_data.py"
        )

    parsed_rows: list[dict] = []

    irregular_intervals = []

    sample_discontinuities = []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        reader = csv.reader(
            f
        )

        try:
            headers = next(
                reader
            )

        except StopIteration:
            raise SystemExit(
                "\nERROR: NASA PDS "
                f"CSV is empty:\n{path}"
            )

        columns = identify_columns(
            headers
        )

        previous_sample = None
        previous_timestamp = None

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            if not row:
                continue

            if all(
                not cell.strip()
                for cell in row
            ):
                continue

            sample_number = (
                parse_sample(
                    row[
                        columns[
                            "sample"
                        ]
                    ],
                    row_number,
                )
            )

            source_datetime = (
                parse_source_datetime(
                    row[
                        columns[
                            "datetime"
                        ]
                    ]
                )
            )

            timestamp_utc = (
                source_datetime
                .astimezone(
                    UTC
                )
            )

            temperature_c = (
                parse_float(
                    row[
                        columns[
                            "temperature"
                        ]
                    ],
                    "temperature",
                    row_number,
                )
            )

            relative_humidity_pct = (
                parse_float(
                    row[
                        columns[
                            "relative_humidity"
                        ]
                    ],
                    "relative humidity",
                    row_number,
                )
            )

            dew_point_c = (
                parse_float(
                    row[
                        columns[
                            "dew_point"
                        ]
                    ],
                    "dew point",
                    row_number,
                )
            )

            if (
                previous_sample
                is not None
            ):
                if (
                    sample_number
                    != previous_sample + 1
                ):
                    sample_discontinuities.append(
                        {
                            "previous_sample": (
                                previous_sample
                            ),
                            "current_sample": (
                                sample_number
                            ),
                        }
                    )

            if (
                previous_timestamp
                is not None
            ):
                interval_seconds = (
                    timestamp_utc
                    - previous_timestamp
                ).total_seconds()

                if (
                    interval_seconds
                    <= 0
                ):
                    raise SystemExit(
                        "\nERROR: Non-monotonic "
                        "NASA PDS timestamps "
                        f"for logger SN "
                        f"{logger_serial}."
                    )

                if (
                    interval_seconds
                    != 60.0
                ):
                    irregular_intervals.append(
                        {
                            "previous_sample": (
                                previous_sample
                            ),
                            "current_sample": (
                                sample_number
                            ),
                            "interval_seconds": (
                                interval_seconds
                            ),
                        }
                    )

            met_seconds = (
                timestamp_utc
                - launch_utc
            ).total_seconds()

            parsed_rows.append(
                {
                    "logger_serial": (
                        logger_serial
                    ),
                    "sample_number": (
                        sample_number
                    ),
                    "source_datetime_cdt": (
                        source_datetime.strftime(
                            "%Y-%m-%dT"
                            "%H:%M:%S-05:00"
                        )
                    ),
                    "timestamp_utc": (
                        iso_z(
                            timestamp_utc
                        )
                    ),
                    "mission_elapsed_seconds": (
                        f"{met_seconds:.0f}"
                    ),
                    "mission_elapsed": (
                        format_met(
                            met_seconds
                        )
                    ),
                    "mission_period": (
                        classify_mission_period(
                            timestamp_utc,
                            launch_utc,
                        )
                    ),
                    "temperature_c": (
                        f"{temperature_c:.6f}"
                    ),
                    "relative_humidity_pct": (
                        f"{relative_humidity_pct:.6f}"
                    ),
                    "dew_point_c": (
                        f"{dew_point_c:.6f}"
                    ),
                    "provenance": (
                        "NASA_PDS_FLIGHT_SENSOR_DATA"
                    ),
                    "source_file": (
                        filename
                    ),
                }
            )

            previous_sample = (
                sample_number
            )

            previous_timestamp = (
                timestamp_utc
            )

    if not parsed_rows:
        raise SystemExit(
            "\nERROR: No records parsed "
            f"for logger SN "
            f"{logger_serial}."
        )

    logger_summary = {
        "logger_serial": (
            logger_serial
        ),
        "source_file": (
            filename
        ),
        "records": len(
            parsed_rows
        ),
        "start_utc": (
            parsed_rows[0][
                "timestamp_utc"
            ]
        ),
        "stop_utc": (
            parsed_rows[-1][
                "timestamp_utc"
            ]
        ),
        "sample_start": (
            parsed_rows[0][
                "sample_number"
            ]
        ),
        "sample_stop": (
            parsed_rows[-1][
                "sample_number"
            ]
        ),
        "sample_discontinuities": (
            sample_discontinuities
        ),
        "irregular_intervals": (
            irregular_intervals
        ),
        "temperature_c": (
            numeric_summary(
                parsed_rows,
                "temperature_c",
            )
        ),
        "relative_humidity_pct": (
            numeric_summary(
                parsed_rows,
                "relative_humidity_pct",
            )
        ),
        "dew_point_c": (
            numeric_summary(
                parsed_rows,
                "dew_point_c",
            )
        ),
    }

    return (
        parsed_rows,
        logger_summary,
    )


def main():
    print()
    print(
        "Phase 3A.1 Artemis II "
        "Orion Environment Normalization"
    )
    print(
        "=" * 72
    )

    mission = (
        load_mission_config()
    )

    launch_epoch_utc = (
        mission[
            "launch_epoch_utc"
        ]
    )

    launch_utc = (
        parse_iso_utc(
            launch_epoch_utc
        )
    )

    print()
    print(
        "Mission clock:"
    )
    print(
        "  Launch UTC:"
    )
    print(
        f"    {iso_z(launch_utc)}"
    )

    print()
    print(
        "NASA PDS source:"
    )
    print(
        "  Artemis II Mission Bundle"
    )
    print(
        "  Orion Environment Data"
    )
    print(
        "  HOBO MX1101 loggers"
    )
    print(
        "  SN 1104 / SN 1105"
    )

    print()
    print(
        "Measurement fields:"
    )
    print(
        "  temperature"
    )
    print(
        "  relative humidity"
    )
    print(
        "  dew point"
    )

    print()
    print(
        "Timing model:"
    )
    print(
        "  source timezone: "
        "CDT / UTC-05:00"
    )
    print(
        "  normalized timezone: UTC"
    )
    print(
        "  nominal cadence: 60 s"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined_rows: list[dict] = []

    logger_summaries = {}

    for (
        logger_serial,
        filename,
    ) in LOGGER_FILES.items():
        print()
        print(
            f"Parsing logger "
            f"SN {logger_serial}..."
        )

        (
            rows,
            summary,
        ) = parse_logger(
            logger_serial,
            filename,
            launch_utc,
        )

        combined_rows.extend(
            rows
        )

        logger_summaries[
            logger_serial
        ] = summary

        print(
            f"  Records: "
            f"{summary['records']}"
        )

        print(
            f"  Start UTC: "
            f"{summary['start_utc']}"
        )

        print(
            f"  Stop UTC:  "
            f"{summary['stop_utc']}"
        )

        print(
            "  Sample discontinuities: "
            f"{len(summary['sample_discontinuities'])}"
        )

        print(
            "  Non-60-second intervals: "
            f"{len(summary['irregular_intervals'])}"
        )

    combined_rows.sort(
        key=lambda row: (
            row[
                "timestamp_utc"
            ],
            row[
                "logger_serial"
            ],
        )
    )

    fieldnames = [
        "logger_serial",
        "sample_number",
        "source_datetime_cdt",
        "timestamp_utc",
        "mission_elapsed_seconds",
        "mission_elapsed",
        "mission_period",
        "temperature_c",
        "relative_humidity_pct",
        "dew_point_c",
        "provenance",
        "source_file",
    ]

    with OUTPUT_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            combined_rows
        )

    period_counts = {}

    for row in combined_rows:
        period = (
            row[
                "mission_period"
            ]
        )

        period_counts[
            period
        ] = (
            period_counts.get(
                period,
                0,
            )
            + 1
        )

    metadata = {
        "dataset_id": (
            "phase3a1_artemis_ii_"
            "orion_environment_normalized"
        ),
        "mission": (
            "Artemis II"
        ),
        "phase": (
            "3A.1"
        ),
        "status": (
            "NORMALIZED"
        ),
        "source": {
            "agency": (
                "NASA Planetary Data System"
            ),
            "bundle": (
                "Artemis II Mission Bundle"
            ),
            "collection": (
                "Orion Environment Data"
            ),
            "instrument": (
                "Onset HOBO MX1101"
            ),
            "logger_serials": [
                "1104",
                "1105",
            ],
            "nominal_cadence_seconds": (
                60
            ),
            "measurement_fields": [
                "temperature_c",
                "relative_humidity_pct",
                "dew_point_c",
            ],
        },
        "mission_clock": {
            "launch_epoch_utc": (
                iso_z(
                    launch_utc
                )
            ),
            "splashdown_utc": (
                iso_z(
                    SPLASHDOWN_UTC
                )
            ),
        },
        "records": {
            "combined": len(
                combined_rows
            ),
            "mission_period_counts": (
                period_counts
            ),
            "loggers": (
                logger_summaries
            ),
        },
        "evidence_boundary": {
            "measurements_are_public_flight_sensor_data": (
                True
            ),
            "measurements_characterize_orion_storage_locker_environment": (
                True
            ),
            "measurements_are_complete_orion_cabin_environment": (
                False
            ),
            "measurements_are_complete_orion_eclss_telemetry": (
                False
            ),
            "temperature_rh_and_dew_point_are_direct_pds_measurements": (
                True
            ),
            "mission_elapsed_time_is_missionlab_derived": (
                True
            ),
            "mission_period_classification_is_missionlab_derived": (
                True
            ),
        },
        "outputs": {
            "normalized_csv": str(
                OUTPUT_CSV.relative_to(
                    ROOT
                )
            ),
            "metadata_json": str(
                OUTPUT_METADATA.relative_to(
                    ROOT
                )
            ),
        },
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

        f.write(
            "\n"
        )

    print()
    print(
        "=" * 72
    )
    print(
        "NORMALIZATION SUMMARY"
    )
    print(
        "=" * 72
    )

    print()
    print(
        f"Combined records: "
        f"{len(combined_rows)}"
    )

    for (
        period,
        count,
    ) in sorted(
        period_counts.items()
    ):
        print(
            f"{period}: "
            f"{count}"
        )

    print()
    print(
        "Evidence boundary:"
    )
    print(
        "  HOBO data = NASA PDS "
        "storage-locker environmental "
        "sensor measurements"
    )
    print(
        "  HOBO data != complete "
        "Orion cabin environment"
    )
    print(
        "  HOBO data != complete "
        "Orion ECLSS telemetry"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            OUTPUT_CSV.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            OUTPUT_METADATA.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 3A.1 NORMALIZATION COMPLETE"
    )


if __name__ == "__main__":
    main()
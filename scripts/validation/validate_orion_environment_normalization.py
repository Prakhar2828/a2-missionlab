from __future__ import annotations

import csv
import json
import math
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

PROCESSED_DIR = (
    ROOT
    / "data"
    / "processed"
    / "eclss"
)

CSV_PATH = (
    PROCESSED_DIR
    / "orion_environment_normalized.csv"
)

METADATA_PATH = (
    PROCESSED_DIR
    / "orion_environment_metadata.json"
)

MISSION_CONFIG = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

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

EXPECTED = {
    "1104": {
        "filename": (
            "art002_086-162546_111-205046_"
            "hobo1104_raw_v01.csv"
        ),
        "records": 37706,
        "start_utc": (
            "2026-03-26T16:25:46Z"
        ),
        "stop_utc": (
            "2026-04-21T20:50:46Z"
        ),
    },
    "1105": {
        "filename": (
            "art002_086-162926_111-203826_"
            "hobo1105_raw_v01.csv"
        ),
        "records": 37690,
        "start_utc": (
            "2026-03-26T16:29:26Z"
        ),
        "stop_utc": (
            "2026-04-21T20:38:26Z"
        ),
    },
}

EXPECTED_TOTAL = 75396

EXPECTED_PERIOD_COUNTS = {
    "PRELAUNCH": 18016,
    "IN_FLIGHT": 26104,
    "POSTFLIGHT": 31276,
}

EXPECTED_COLUMNS = [
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


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 3A.1 VALIDATION FAILED: "
        f"{message}"
    )


def parse_utc(
    value: str,
) -> datetime:
    try:
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        ).astimezone(
            UTC
        )

    except ValueError:
        fail(
            "invalid UTC timestamp: "
            f"{value}"
        )

        raise


def parse_cdt(
    value: str,
) -> datetime:
    try:
        value = value.replace(
            "-05:00",
            "",
        )

        parsed = datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%S",
        )

        return parsed.replace(
            tzinfo=CDT
        )

    except ValueError:
        fail(
            "invalid normalized CDT "
            f"timestamp: {value}"
        )

        raise


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


def classify_period(
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


def load_json(
    path: Path,
) -> dict:
    if not path.exists():
        fail(
            f"missing JSON file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(
            f
        )


def raw_record_count(
    path: Path,
) -> int:
    if not path.exists():
        fail(
            "missing raw NASA PDS "
            f"CSV: {path}"
        )

    count = 0

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        reader = csv.reader(
            f
        )

        try:
            next(
                reader
            )

        except StopIteration:
            fail(
                f"raw CSV is empty: {path}"
            )

        for row in reader:
            if not row:
                continue

            if all(
                not cell.strip()
                for cell in row
            ):
                continue

            count += 1

    return count


def require_finite(
    value: str,
    field: str,
    record_number: int,
) -> float:
    try:
        parsed = float(
            value
        )

    except ValueError:
        fail(
            f"record {record_number}: "
            f"{field} is not numeric"
        )

    if not math.isfinite(
        parsed
    ):
        fail(
            f"record {record_number}: "
            f"{field} is not finite"
        )

    return parsed


def mean(
    values: list[float],
) -> float:
    return (
        sum(
            values
        )
        / len(
            values
        )
    )


def validate_summary(
    metadata_summary: dict,
    values: list[float],
    label: str,
):
    expected_min = min(
        values
    )

    expected_max = max(
        values
    )

    expected_mean = mean(
        values
    )

    observed_min = float(
        metadata_summary[
            "minimum"
        ]
    )

    observed_max = float(
        metadata_summary[
            "maximum"
        ]
    )

    observed_mean = float(
        metadata_summary[
            "mean"
        ]
    )

    if abs(
        observed_min
        - expected_min
    ) > 1e-9:
        fail(
            f"{label} metadata minimum "
            "does not match CSV"
        )

    if abs(
        observed_max
        - expected_max
    ) > 1e-9:
        fail(
            f"{label} metadata maximum "
            "does not match CSV"
        )

    if abs(
        observed_mean
        - expected_mean
    ) > 1e-9:
        fail(
            f"{label} metadata mean "
            "does not match CSV"
        )


def main():
    print()
    print(
        "Phase 3A.1 Artemis II "
        "Orion Environment "
        "Normalization Validation"
    )
    print(
        "=" * 72
    )

    if not CSV_PATH.exists():
        fail(
            "normalized CSV is missing"
        )

    metadata = load_json(
        METADATA_PATH
    )

    mission = load_json(
        MISSION_CONFIG
    )

    launch_utc = parse_utc(
        mission[
            "launch_epoch_utc"
        ]
    )

    #
    # Metadata identity
    #

    if (
        metadata.get(
            "dataset_id"
        )
        != (
            "phase3a1_artemis_ii_"
            "orion_environment_normalized"
        )
    ):
        fail(
            "dataset ID mismatch"
        )

    if (
        metadata.get(
            "mission"
        )
        != "Artemis II"
    ):
        fail(
            "mission identity mismatch"
        )

    if (
        metadata.get(
            "phase"
        )
        != "3A.1"
    ):
        fail(
            "phase identity mismatch"
        )

    if (
        metadata.get(
            "status"
        )
        != "NORMALIZED"
    ):
        fail(
            "dataset status is not "
            "NORMALIZED"
        )

    print()
    print(
        "Metadata identity: PASS"
    )

    #
    # Raw source preservation
    #

    for (
        logger_serial,
        config,
    ) in EXPECTED.items():
        path = (
            RAW_DIR
            / config[
                "filename"
            ]
        )

        observed = (
            raw_record_count(
                path
            )
        )

        if (
            observed
            != config[
                "records"
            ]
        ):
            fail(
                f"raw SN {logger_serial} "
                "record count mismatch: "
                f"{observed}"
            )

    print(
        "Raw NASA PDS source counts: PASS"
    )

    #
    # Read normalized CSV
    #

    with CSV_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        reader = csv.DictReader(
            f
        )

        if (
            reader.fieldnames
            != EXPECTED_COLUMNS
        ):
            fail(
                "normalized CSV columns "
                "do not match expected schema"
            )

        rows = list(
            reader
        )

    if (
        len(
            rows
        )
        != EXPECTED_TOTAL
    ):
        fail(
            "combined normalized record "
            f"count is {len(rows)}, "
            f"expected {EXPECTED_TOTAL}"
        )

    print(
        "Normalized CSV schema: PASS"
    )
    print(
        "Combined record count: PASS"
    )

    #
    # Per-logger validation
    #

    logger_rows = {
        "1104": [],
        "1105": [],
    }

    period_counts = {
        "PRELAUNCH": 0,
        "IN_FLIGHT": 0,
        "POSTFLIGHT": 0,
    }

    previous_combined_key = None

    for record_number, row in enumerate(
        rows,
        start=1,
    ):
        logger_serial = (
            row[
                "logger_serial"
            ]
        )

        if (
            logger_serial
            not in logger_rows
        ):
            fail(
                f"record {record_number}: "
                "unexpected logger serial "
                f"{logger_serial}"
            )

        logger_rows[
            logger_serial
        ].append(
            row
        )

        try:
            sample_number = int(
                row[
                    "sample_number"
                ]
            )

        except ValueError:
            fail(
                f"record {record_number}: "
                "sample_number is not "
                "an integer"
            )

        timestamp_utc = parse_utc(
            row[
                "timestamp_utc"
            ]
        )

        source_cdt = parse_cdt(
            row[
                "source_datetime_cdt"
            ]
        )

        converted_source_utc = (
            source_cdt.astimezone(
                UTC
            )
        )

        if (
            converted_source_utc
            != timestamp_utc
        ):
            fail(
                f"record {record_number}: "
                "CDT to UTC conversion "
                "mismatch"
            )

        met_seconds = (
            timestamp_utc
            - launch_utc
        ).total_seconds()

        observed_met_seconds = (
            require_finite(
                row[
                    "mission_elapsed_seconds"
                ],
                "mission_elapsed_seconds",
                record_number,
            )
        )

        if abs(
            observed_met_seconds
            - met_seconds
        ) > 1e-9:
            fail(
                f"record {record_number}: "
                "mission elapsed seconds "
                "mismatch"
            )

        expected_met = format_met(
            met_seconds
        )

        if (
            row[
                "mission_elapsed"
            ]
            != expected_met
        ):
            fail(
                f"record {record_number}: "
                "formatted MET mismatch"
            )

        expected_period = (
            classify_period(
                timestamp_utc,
                launch_utc,
            )
        )

        if (
            row[
                "mission_period"
            ]
            != expected_period
        ):
            fail(
                f"record {record_number}: "
                "mission-period "
                "classification mismatch"
            )

        period_counts[
            expected_period
        ] += 1

        temperature = (
            require_finite(
                row[
                    "temperature_c"
                ],
                "temperature_c",
                record_number,
            )
        )

        relative_humidity = (
            require_finite(
                row[
                    "relative_humidity_pct"
                ],
                "relative_humidity_pct",
                record_number,
            )
        )

        dew_point = (
            require_finite(
                row[
                    "dew_point_c"
                ],
                "dew_point_c",
                record_number,
            )
        )

        if not (
            0.0
            <= relative_humidity
            <= 100.0
        ):
            fail(
                f"record {record_number}: "
                "relative humidity outside "
                "0-100 percent"
            )

        if (
            temperature
            < -100.0
            or temperature
            > 100.0
        ):
            fail(
                f"record {record_number}: "
                "temperature outside "
                "sanity bounds"
            )

        if (
            dew_point
            < -100.0
            or dew_point
            > 100.0
        ):
            fail(
                f"record {record_number}: "
                "dew point outside "
                "sanity bounds"
            )

        if (
            row[
                "provenance"
            ]
            != (
                "NASA_PDS_"
                "FLIGHT_SENSOR_DATA"
            )
        ):
            fail(
                f"record {record_number}: "
                "provenance mismatch"
            )

        if (
            row[
                "source_file"
            ]
            != EXPECTED[
                logger_serial
            ][
                "filename"
            ]
        ):
            fail(
                f"record {record_number}: "
                "source-file provenance "
                "mismatch"
            )

        combined_key = (
            timestamp_utc,
            logger_serial,
        )

        if (
            previous_combined_key
            is not None
            and combined_key
            < previous_combined_key
        ):
            fail(
                "combined normalized CSV "
                "is not sorted by "
                "timestamp/logger"
            )

        previous_combined_key = (
            combined_key
        )

        if sample_number < 0:
            fail(
                f"record {record_number}: "
                "negative sample number"
            )

    print(
        "Record-level numeric fields: PASS"
    )
    print(
        "CDT to UTC conversion: PASS"
    )
    print(
        "Mission elapsed time: PASS"
    )
    print(
        "Mission-period classification: PASS"
    )
    print(
        "Provenance preservation: PASS"
    )
    print(
        "Combined temporal ordering: PASS"
    )

    #
    # Per-logger cadence and bounds
    #

    for (
        logger_serial,
        config,
    ) in EXPECTED.items():
        current_rows = (
            logger_rows[
                logger_serial
            ]
        )

        if (
            len(
                current_rows
            )
            != config[
                "records"
            ]
        ):
            fail(
                f"SN {logger_serial} "
                "normalized record count "
                "mismatch"
            )

        if (
            current_rows[0][
                "timestamp_utc"
            ]
            != config[
                "start_utc"
            ]
        ):
            fail(
                f"SN {logger_serial} "
                "start UTC mismatch"
            )

        if (
            current_rows[-1][
                "timestamp_utc"
            ]
            != config[
                "stop_utc"
            ]
        ):
            fail(
                f"SN {logger_serial} "
                "stop UTC mismatch"
            )

        previous_sample = None
        previous_time = None

        temperatures = []
        humidities = []
        dew_points = []

        for row in current_rows:
            sample_number = int(
                row[
                    "sample_number"
                ]
            )

            timestamp = parse_utc(
                row[
                    "timestamp_utc"
                ]
            )

            if (
                previous_sample
                is not None
            ):
                if (
                    sample_number
                    != previous_sample + 1
                ):
                    fail(
                        f"SN {logger_serial} "
                        "sample numbering "
                        "is discontinuous"
                    )

            if (
                previous_time
                is not None
            ):
                interval = (
                    timestamp
                    - previous_time
                ).total_seconds()

                if (
                    interval
                    != 60.0
                ):
                    fail(
                        f"SN {logger_serial} "
                        "contains a non-60-s "
                        f"interval: {interval}"
                    )

            previous_sample = (
                sample_number
            )

            previous_time = (
                timestamp
            )

            temperatures.append(
                float(
                    row[
                        "temperature_c"
                    ]
                )
            )

            humidities.append(
                float(
                    row[
                        "relative_humidity_pct"
                    ]
                )
            )

            dew_points.append(
                float(
                    row[
                        "dew_point_c"
                    ]
                )
            )

        metadata_logger = (
            metadata[
                "records"
            ][
                "loggers"
            ][
                logger_serial
            ]
        )

        if (
            metadata_logger[
                "records"
            ]
            != config[
                "records"
            ]
        ):
            fail(
                f"SN {logger_serial} "
                "metadata record count "
                "mismatch"
            )

        if (
            metadata_logger[
                "start_utc"
            ]
            != config[
                "start_utc"
            ]
        ):
            fail(
                f"SN {logger_serial} "
                "metadata start mismatch"
            )

        if (
            metadata_logger[
                "stop_utc"
            ]
            != config[
                "stop_utc"
            ]
        ):
            fail(
                f"SN {logger_serial} "
                "metadata stop mismatch"
            )

        if (
            metadata_logger[
                "sample_discontinuities"
            ]
            != []
        ):
            fail(
                f"SN {logger_serial} "
                "metadata reports sample "
                "discontinuities"
            )

        if (
            metadata_logger[
                "irregular_intervals"
            ]
            != []
        ):
            fail(
                f"SN {logger_serial} "
                "metadata reports cadence "
                "irregularities"
            )

        validate_summary(
            metadata_logger[
                "temperature_c"
            ],
            temperatures,
            (
                f"SN {logger_serial} "
                "temperature"
            ),
        )

        validate_summary(
            metadata_logger[
                "relative_humidity_pct"
            ],
            humidities,
            (
                f"SN {logger_serial} "
                "relative humidity"
            ),
        )

        validate_summary(
            metadata_logger[
                "dew_point_c"
            ],
            dew_points,
            (
                f"SN {logger_serial} "
                "dew point"
            ),
        )

    print()
    print(
        "SN 1104 record count: PASS"
    )
    print(
        "SN 1104 start/stop UTC: PASS"
    )
    print(
        "SN 1104 60-second cadence: PASS"
    )
    print(
        "SN 1104 sample continuity: PASS"
    )

    print()
    print(
        "SN 1105 record count: PASS"
    )
    print(
        "SN 1105 start/stop UTC: PASS"
    )
    print(
        "SN 1105 60-second cadence: PASS"
    )
    print(
        "SN 1105 sample continuity: PASS"
    )

    #
    # Mission-period totals
    #

    if (
        period_counts
        != EXPECTED_PERIOD_COUNTS
    ):
        fail(
            "mission-period counts "
            f"mismatch: {period_counts}"
        )

    metadata_period_counts = (
        metadata[
            "records"
        ][
            "mission_period_counts"
        ]
    )

    if (
        metadata_period_counts
        != EXPECTED_PERIOD_COUNTS
    ):
        fail(
            "metadata mission-period "
            "counts mismatch"
        )

    print()
    print(
        "Mission-period totals:"
    )
    print(
        "  PRELAUNCH:  "
        f"{period_counts['PRELAUNCH']}"
    )
    print(
        "  IN_FLIGHT:  "
        f"{period_counts['IN_FLIGHT']}"
    )
    print(
        "  POSTFLIGHT: "
        f"{period_counts['POSTFLIGHT']}"
    )
    print(
        "  TOTAL:      "
        f"{len(rows)}"
    )

    #
    # Source metadata
    #

    source = (
        metadata[
            "source"
        ]
    )

    if (
        source[
            "agency"
        ]
        != (
            "NASA Planetary Data System"
        )
    ):
        fail(
            "source agency mismatch"
        )

    if (
        source[
            "instrument"
        ]
        != "Onset HOBO MX1101"
    ):
        fail(
            "instrument identity mismatch"
        )

    if (
        source[
            "nominal_cadence_seconds"
        ]
        != 60
    ):
        fail(
            "metadata cadence mismatch"
        )

    if (
        set(
            source[
                "logger_serials"
            ]
        )
        != {
            "1104",
            "1105",
        }
    ):
        fail(
            "metadata logger set mismatch"
        )

    print()
    print(
        "NASA PDS source metadata: PASS"
    )

    #
    # Mission clock metadata
    #

    if (
        metadata[
            "mission_clock"
        ][
            "launch_epoch_utc"
        ]
        != mission[
            "launch_epoch_utc"
        ]
    ):
        fail(
            "metadata launch epoch "
            "does not match mission config"
        )

    if (
        metadata[
            "mission_clock"
        ][
            "splashdown_utc"
        ]
        != "2026-04-11T00:07:00Z"
    ):
        fail(
            "metadata splashdown epoch "
            "mismatch"
        )

    print(
        "Mission-clock metadata: PASS"
    )

    #
    # Evidence boundaries
    #

    boundary = (
        metadata[
            "evidence_boundary"
        ]
    )

    required_true = [
        (
            "measurements_are_public_"
            "flight_sensor_data"
        ),
        (
            "measurements_characterize_"
            "orion_storage_locker_environment"
        ),
        (
            "temperature_rh_and_dew_point_"
            "are_direct_pds_measurements"
        ),
        (
            "mission_elapsed_time_is_"
            "missionlab_derived"
        ),
        (
            "mission_period_classification_"
            "is_missionlab_derived"
        ),
    ]

    required_false = [
        (
            "measurements_are_complete_"
            "orion_cabin_environment"
        ),
        (
            "measurements_are_complete_"
            "orion_eclss_telemetry"
        ),
    ]

    for key in required_true:
        if (
            boundary.get(
                key
            )
            is not True
        ):
            fail(
                "required TRUE evidence "
                f"boundary failed: {key}"
            )

    for key in required_false:
        if (
            boundary.get(
                key
            )
            is not False
        ):
            fail(
                "required FALSE evidence "
                f"boundary failed: {key}"
            )

    print()
    print(
        "Evidence boundaries:"
    )
    print(
        "  Public flight sensor data: PASS"
    )
    print(
        "  Storage-locker environment: PASS"
    )
    print(
        "  Complete cabin environment: FALSE"
    )
    print(
        "  Complete ECLSS telemetry: FALSE"
    )
    print(
        "  MET is MissionLab-derived: PASS"
    )
    print(
        "  Mission-period labels "
        "are MissionLab-derived: PASS"
    )

    print()
    print(
        "Products:"
    )
    print(
        "  normalized CSV: PASS"
    )
    print(
        "  metadata JSON: PASS"
    )

    print()
    print(
        "PHASE 3A.1 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
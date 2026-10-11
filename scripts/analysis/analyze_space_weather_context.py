from __future__ import annotations

import csv
import json
import math
import statistics
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

MISSION_CONFIG_PATH = ROOT / "data" / "config" / "mission.json"

PHASE4_EVIDENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_descent_recovery_evidence.json"
)

RAW_DIR = ROOT / "data" / "raw" / "space_weather"
PROCESSED_DIR = ROOT / "data" / "processed" / "space_weather"
ASSET_DIR = ROOT / "docs" / "assets" / "space_weather"

RAW_JSON_PATH = (
    RAW_DIR
    / "omni_hro2_1min_artemis_ii.json"
)

NORMALIZED_CSV_PATH = (
    PROCESSED_DIR
    / "omni_hro2_1min_artemis_ii.csv"
)

SUMMARY_JSON_PATH = (
    PROCESSED_DIR
    / "artemis_ii_space_weather_context.json"
)

FIGURE_PATH = (
    ASSET_DIR
    / "phase5a_space_weather_context.svg"
)

HAPI_BASE = (
    "https://cdaweb.gsfc.nasa.gov/hapi/data"
)

DATASET_ID = "OMNI_HRO2_1MIN"

PARAMETERS = [
    "Time",
    "F",
    "BX_GSE",
    "BY_GSM",
    "BZ_GSM",
    "flow_speed",
    "proton_density",
    "T",
    "Pressure",
    "E",
    "Beta",
    "Mach_num",
    "AE_INDEX",
    "SYM_H",
]

PARAMETER_UNITS = {
    "F": "nT",
    "BX_GSE": "nT",
    "BY_GSM": "nT",
    "BZ_GSM": "nT",
    "flow_speed": "km/s",
    "proton_density": "n/cc",
    "T": "K",
    "Pressure": "nPa",
    "E": "mV/m",
    "Beta": None,
    "Mach_num": None,
    "AE_INDEX": "nT",
    "SYM_H": "nT",
}

EXTREMA_RULES = {
    "F": "max",
    "BZ_GSM": "min",
    "flow_speed": "max",
    "proton_density": "max",
    "Pressure": "max",
    "E": "max",
    "AE_INDEX": "max",
    "SYM_H": "min",
}

plt.rcParams[
    "svg.hashsalt"
] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 5A ANALYSIS FAILED: "
        f"{message}"
    )


def require(
    condition: bool,
    message: str,
):
    if not condition:
        fail(
            message
        )


def load_json(
    path: Path,
) -> dict:
    require(
        path.exists(),
        f"missing dependency: {path}",
    )

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as f:
            return json.load(
                f
            )

    except json.JSONDecodeError as exc:
        fail(
            f"invalid JSON in {path}: {exc}"
        )

        raise


def parse_utc(
    value: str,
) -> datetime:
    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def format_utc(
    value: datetime,
) -> str:
    return (
        value.isoformat(
            timespec="seconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def met_string(
    seconds: float,
) -> str:
    sign = ""

    if seconds < 0:
        sign = "-"
        seconds = abs(
            seconds
        )

    total_seconds = int(
        round(
            seconds
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

    minutes, seconds_value = divmod(
        remainder,
        60,
    )

    return (
        f"{sign}"
        f"{days:02d}:"
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds_value:02d}"
    )


def floor_to_minute(
    value: datetime,
) -> datetime:
    return value.replace(
        second=0,
        microsecond=0,
    )


def ceil_to_next_minute(
    value: datetime,
) -> datetime:
    floored = floor_to_minute(
        value
    )

    if value == floored:
        return (
            value
            + timedelta(
                minutes=1
            )
        )

    return (
        floored
        + timedelta(
            minutes=1
        )
    )


def normalize_svg(
    path: Path,
):
    text = path.read_text(
        encoding="utf-8",
    )

    cleaned = "\n".join(
        line.rstrip(
            " \t"
        )
        for line
        in text.splitlines()
    )

    path.write_text(
        cleaned + "\n",
        encoding="utf-8",
    )


def get_splashdown_utc(
    evidence: dict,
) -> datetime:
    for event in evidence[
        "events"
    ]:
        if (
            event[
                "event_id"
            ]
            == "A2_SPLASHDOWN"
        ):
            return parse_utc(
                event[
                    "reported_utc_minute"
                ]
            )

    fail(
        "Phase 4 splashdown event missing"
    )

    raise RuntimeError


def build_hapi_url(
    start: datetime,
    stop: datetime,
) -> str:
    query = urllib.parse.urlencode(
        {
            "id": DATASET_ID,
            "parameters": ",".join(
                PARAMETERS
            ),
            "time.min": format_utc(
                start
            ),
            "time.max": format_utc(
                stop
            ),
            "format": "json",
        }
    )

    return (
        HAPI_BASE
        + "?"
        + query
    )


def download_hapi(
    url: str,
) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "A2-MissionLab/"
                "Phase5A"
            ),
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=120,
        ) as response:
            raw = response.read()

    except Exception as exc:
        fail(
            "NASA CDAWeb HAPI request failed: "
            f"{exc}"
        )

        raise

    try:
        payload = json.loads(
            raw.decode(
                "utf-8"
            )
        )

    except Exception as exc:
        fail(
            "NASA CDAWeb response was not "
            f"valid JSON: {exc}"
        )

        raise

    require(
        "data"
        in payload,
        "HAPI response missing data",
    )

    require(
        "parameters"
        in payload,
        (
            "HAPI response missing "
            "parameter metadata"
        ),
    )

    return payload


def build_parameter_metadata(
    payload: dict,
) -> dict[str, dict]:
    metadata = {}

    for parameter in payload[
        "parameters"
    ]:
        metadata[
            parameter[
                "name"
            ]
        ] = parameter

    returned = [
        parameter[
            "name"
        ]
        for parameter
        in payload[
            "parameters"
        ]
    ]

    require(
        returned == PARAMETERS,
        (
            "HAPI parameter order mismatch.\n"
            f"Expected: {PARAMETERS}\n"
            f"Returned: {returned}"
        ),
    )

    return metadata


def is_fill_value(
    value,
    metadata: dict,
) -> bool:
    fill = metadata.get(
        "fill"
    )

    if fill is None:
        return False

    return (
        str(
            value
        ).strip()
        == str(
            fill
        ).strip()
    )


def normalize_numeric(
    value,
    metadata: dict,
):
    if value is None:
        return None

    if is_fill_value(
        value,
        metadata,
    ):
        return None

    try:
        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    if not math.isfinite(
        number
    ):
        return None

    return number


def normalize_rows(
    payload: dict,
    launch: datetime,
) -> list[dict]:
    metadata = (
        build_parameter_metadata(
            payload
        )
    )

    rows = []

    for record in payload[
        "data"
    ]:
        require(
            len(
                record
            )
            == len(
                PARAMETERS
            ),
            (
                "HAPI record width mismatch: "
                f"{len(record)}"
            ),
        )

        raw = dict(
            zip(
                PARAMETERS,
                record,
            )
        )

        timestamp = parse_utc(
            raw[
                "Time"
            ]
        )

        met_seconds = (
            timestamp
            - launch
        ).total_seconds()

        row = {
            "timestamp_utc": (
                format_utc(
                    timestamp
                )
            ),
            "met_seconds": (
                met_seconds
            ),
            "met": (
                met_string(
                    met_seconds
                )
            ),
        }

        for parameter in PARAMETERS[
            1:
        ]:
            row[
                parameter
            ] = normalize_numeric(
                raw[
                    parameter
                ],
                metadata[
                    parameter
                ],
            )

        rows.append(
            row
        )

    require(
        len(
            rows
        )
        > 0,
        "NASA OMNI response contained no data",
    )

    return rows


def numeric_values(
    rows: list[dict],
    key: str,
) -> list[float]:
    return [
        row[
            key
        ]
        for row
        in rows
        if row[
            key
        ]
        is not None
    ]


def completeness(
    rows: list[dict],
    key: str,
) -> dict:
    valid = numeric_values(
        rows,
        key,
    )

    total = len(
        rows
    )

    count = len(
        valid
    )

    return {
        "total_rows": (
            total
        ),
        "valid_rows": (
            count
        ),
        "missing_rows": (
            total
            - count
        ),
        "valid_fraction": (
            count
            / total
            if total
            else 0.0
        ),
    }


def summary_stats(
    rows: list[dict],
    key: str,
) -> dict:
    values = numeric_values(
        rows,
        key,
    )

    if not values:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
        }

    return {
        "count": (
            len(
                values
            )
        ),
        "min": (
            min(
                values
            )
        ),
        "max": (
            max(
                values
            )
        ),
        "mean": (
            statistics.fmean(
                values
            )
        ),
        "median": (
            statistics.median(
                values
            )
        ),
    }


def extrema_record(
    rows: list[dict],
    key: str,
    mode: str,
) -> dict | None:
    candidates = [
        row
        for row
        in rows
        if row[
            key
        ]
        is not None
    ]

    if not candidates:
        return None

    if mode == "min":
        row = min(
            candidates,
            key=lambda item: item[
                key
            ],
        )

    elif mode == "max":
        row = max(
            candidates,
            key=lambda item: item[
                key
            ],
        )

    else:
        fail(
            f"unknown extrema mode: {mode}"
        )

    return {
        "parameter": (
            key
        ),
        "operation": (
            mode
        ),
        "value": (
            row[
                key
            ]
        ),
        "unit": (
            PARAMETER_UNITS.get(
                key
            )
        ),
        "utc": (
            row[
                "timestamp_utc"
            ]
        ),
        "met_seconds": (
            row[
                "met_seconds"
            ]
        ),
        "met": (
            row[
                "met"
            ]
        ),
        "provenance": (
            "MISSIONLAB_DERIVED_FROM_"
            "NASA_OMNI_HRO2_1MIN"
        ),
    }


def write_normalized_csv(
    rows: list[dict],
):
    fieldnames = [
        "timestamp_utc",
        "met_seconds",
        "met",
        *PARAMETERS[
            1:
        ],
    ]

    with NORMALIZED_CSV_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    key: (
                        ""
                        if row.get(
                            key
                        )
                        is None
                        else row.get(
                            key
                        )
                    )
                    for key
                    in fieldnames
                }
            )


def build_figure(
    rows: list[dict],
):
    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamps = [
        parse_utc(
            row[
                "timestamp_utc"
            ]
        )
        for row
        in rows
    ]

    series = [
        (
            "BZ_GSM",
            "Bz GSM (nT)",
        ),
        (
            "flow_speed",
            "Solar-wind speed (km/s)",
        ),
        (
            "Pressure",
            "Flow pressure (nPa)",
        ),
        (
            "SYM_H",
            "SYM/H (nT)",
        ),
    ]

    fig, axes = plt.subplots(
        len(
            series
        ),
        1,
        figsize=(
            14,
            10,
        ),
        sharex=True,
    )

    for ax, (
        key,
        label,
    ) in zip(
        axes,
        series,
    ):
        values = [
            (
                math.nan
                if row[
                    key
                ]
                is None
                else row[
                    key
                ]
            )
            for row
            in rows
        ]

        ax.plot(
            timestamps,
            values,
            linewidth=0.8,
        )

        ax.set_ylabel(
            label
        )

        ax.grid(
            True,
            alpha=0.25,
        )

    axes[
        -1
    ].set_xlabel(
        "UTC"
    )

    fig.suptitle(
        (
            "Artemis II Mission-Window "
            "Near-Earth Space-Weather Context\n"
            "NASA OMNI_HRO2_1MIN"
        )
    )

    fig.text(
        0.5,
        0.01,
        (
            "OMNI values are near-Earth solar-wind / "
            "geomagnetic context time-shifted to the "
            "Earth bow-shock nose. They are not "
            "Orion-local radiation measurements "
            "and are not crew dose."
        ),
        ha="center",
        fontsize=8,
    )

    fig.tight_layout(
        rect=(
            0,
            0.04,
            1,
            0.96,
        )
    )

    fig.savefig(
        FIGURE_PATH,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    normalize_svg(
        FIGURE_PATH
    )


def main():
    print()
    print(
        "Phase 5A Artemis II "
        "Mission Space-Weather Context"
    )
    print(
        "=" * 72
    )

    mission = load_json(
        MISSION_CONFIG_PATH
    )

    phase4 = load_json(
        PHASE4_EVIDENCE_PATH
    )

    require(
        mission.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    launch = parse_utc(
        mission[
            "launch_epoch_utc"
        ]
    )

    splashdown = (
        get_splashdown_utc(
            phase4
        )
    )

    query_start = floor_to_minute(
        launch
    )

    query_stop = ceil_to_next_minute(
        splashdown
    )

    print()
    print(
        "Mission window:"
    )
    print(
        "  launch: "
        + format_utc(
            launch
        )
    )
    print(
        "  splashdown public minute: "
        + format_utc(
            splashdown
        )
    )
    print(
        "  OMNI query start: "
        + format_utc(
            query_start
        )
    )
    print(
        "  OMNI query stop: "
        + format_utc(
            query_stop
        )
    )

    url = build_hapi_url(
        query_start,
        query_stop,
    )

    print()
    print(
        "NASA source:"
    )
    print(
        "  CDAWeb HAPI"
    )
    print(
        "  dataset: "
        + DATASET_ID
    )
    print(
        "  cadence: 1 minute"
    )
    print(
        "  bow-shock time-shifted: YES"
    )

    print()
    print(
        "Downloading NASA OMNI data..."
    )

    payload = download_hapi(
        url
    )

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RAW_JSON_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            payload,
            f,
            indent=2,
        )

        f.write(
            "\n"
        )

    rows = normalize_rows(
        payload,
        launch,
    )

    write_normalized_csv(
        rows
    )

    build_figure(
        rows
    )

    first_time = parse_utc(
        rows[
            0
        ][
            "timestamp_utc"
        ]
    )

    last_time = parse_utc(
        rows[
            -1
        ][
            "timestamp_utc"
        ]
    )

    expected_rows = int(
        (
            query_stop
            - query_start
        ).total_seconds()
        / 60.0
    )

    statistics_summary = {
        key: summary_stats(
            rows,
            key,
        )
        for key
        in PARAMETERS[
            1:
        ]
    }

    completeness_summary = {
        key: completeness(
            rows,
            key,
        )
        for key
        in PARAMETERS[
            1:
        ]
    }

    extrema = {
        key: extrema_record(
            rows,
            key,
            mode,
        )
        for key, mode
        in EXTREMA_RULES.items()
    }

    result = {
        "dataset_id": (
            "phase5a_artemis_ii_"
            "space_weather_context"
        ),
        "mission": (
            "Artemis II"
        ),
        "phase": (
            "5A"
        ),
        "status": (
            "MISSION_SPACE_WEATHER_CONTEXT_COMPLETE"
        ),
        "mission_window": {
            "launch_utc": (
                format_utc(
                    launch
                )
            ),
            "splashdown_public_minute_utc": (
                format_utc(
                    splashdown
                )
            ),
            "query_start_utc": (
                format_utc(
                    query_start
                )
            ),
            "query_stop_utc_exclusive": (
                format_utc(
                    query_stop
                )
            ),
        },
        "source": {
            "publisher": (
                "NASA GSFC Space Physics "
                "Data Facility"
            ),
            "service": (
                "CDAWeb HAPI"
            ),
            "dataset_id": (
                DATASET_ID
            ),
            "dataset_description": (
                "OMNI Combined, Definitive "
                "1-minute IMF and Definitive "
                "Plasma Data Time-Shifted to "
                "the Nose of the Earth's Bow "
                "Shock, plus Magnetic Indices"
            ),
            "hapi_endpoint": (
                HAPI_BASE
            ),
            "request_url": (
                url
            ),
            "requested_parameters": (
                PARAMETERS
            ),
            "cadence": (
                "1 minute"
            ),
        },
        "coverage": {
            "rows": (
                len(
                    rows
                )
            ),
            "expected_nominal_minute_rows": (
                expected_rows
            ),
            "first_utc": (
                format_utc(
                    first_time
                )
            ),
            "last_utc": (
                format_utc(
                    last_time
                )
            ),
            "continuous_coverage_assumed": (
                False
            ),
            "reason": (
                "OMNI documentation explicitly "
                "states that continuous coverage "
                "is not guaranteed. Parameter-level "
                "completeness is therefore reported "
                "rather than silently filling gaps."
            ),
        },
        "parameter_completeness": (
            completeness_summary
        ),
        "parameter_statistics": (
            statistics_summary
        ),
        "mission_clock_extrema": (
            extrema
        ),
        "interpretation": {
            "what_this_dataset_represents": (
                "Near-Earth interplanetary magnetic "
                "field, solar-wind plasma, and "
                "geomagnetic-index context during "
                "the Artemis II mission window."
            ),
            "omni_values_are_orion_local_measurements": (
                False
            ),
            "omni_values_are_spacecraft_radiation_measurements": (
                False
            ),
            "omni_values_are_astronaut_dose": (
                False
            ),
            "geomagnetic_indices_are_orion_dose": (
                False
            ),
            "extrema_are_spacecraft_anomalies": (
                False
            ),
        },
        "critical_non_equivalences": [
            {
                "left": (
                    "OMNI_BOW_SHOCK_CONTEXT"
                ),
                "right": (
                    "ORION_LOCAL_ENVIRONMENT"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "SOLAR_WIND_PARAMETERS"
                ),
                "right": (
                    "IONIZING_RADIATION_DOSE"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "GEOMAGNETIC_ACTIVITY"
                ),
                "right": (
                    "ASTRONAUT_EFFECTIVE_DOSE"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "MISSION_WINDOW_CORRELATION"
                ),
                "right": (
                    "CAUSAL_SPACECRAFT_EFFECT"
                ),
                "equivalent": (
                    False
                ),
            },
            {
                "left": (
                    "OMNI_DATA_GAP"
                ),
                "right": (
                    "QUIET_SPACE_WEATHER"
                ),
                "equivalent": (
                    False
                ),
            },
        ],
        "outputs": {
            "raw_json": str(
                RAW_JSON_PATH.relative_to(
                    ROOT
                )
            ),
            "normalized_csv": str(
                NORMALIZED_CSV_PATH.relative_to(
                    ROOT
                )
            ),
            "summary_json": str(
                SUMMARY_JSON_PATH.relative_to(
                    ROOT
                )
            ),
            "figure": str(
                FIGURE_PATH.relative_to(
                    ROOT
                )
            ),
        },
    }

    with SUMMARY_JSON_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
        )

        f.write(
            "\n"
        )

    print()
    print(
        "Coverage:"
    )
    print(
        "  downloaded rows: "
        f"{len(rows)}"
    )
    print(
        "  nominal minute slots: "
        f"{expected_rows}"
    )
    print(
        "  continuous coverage assumed: NO"
    )

    print()
    print(
        "Parameter completeness:"
    )

    for key in [
        "BZ_GSM",
        "flow_speed",
        "proton_density",
        "Pressure",
        "E",
        "AE_INDEX",
        "SYM_H",
    ]:
        item = completeness_summary[
            key
        ]

        print(
            "  "
            + key
            + ": "
            + f"{item['valid_rows']}/"
            + f"{item['total_rows']} "
            + (
                f"({100.0 * item['valid_fraction']:.1f}%)"
            )
        )

    print()
    print(
        "Mission-clock extrema:"
    )

    for key in [
        "BZ_GSM",
        "flow_speed",
        "proton_density",
        "Pressure",
        "E",
        "AE_INDEX",
        "SYM_H",
    ]:
        item = extrema[
            key
        ]

        if item is None:
            print(
                "  "
                + key
                + ": unavailable"
            )

            continue

        unit = (
            ""
            if item[
                "unit"
            ]
            is None
            else (
                " "
                + item[
                    "unit"
                ]
            )
        )

        print(
            "  "
            + key
            + " "
            + item[
                "operation"
            ]
            + ": "
            + f"{item['value']:.3f}"
            + unit
            + " at "
            + item[
                "utc"
            ]
            + " / MET "
            + item[
                "met"
            ]
        )

    print()
    print(
        "Evidence boundary:"
    )
    print(
        "  OMNI bow-shock context "
        "!= Orion-local environment"
    )
    print(
        "  solar-wind parameters "
        "!= ionizing-radiation dose"
    )
    print(
        "  geomagnetic activity "
        "!= astronaut effective dose"
    )
    print(
        "  temporal correlation "
        "!= causal spacecraft effect"
    )
    print(
        "  missing OMNI data "
        "!= quiet conditions"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + str(
            RAW_JSON_PATH.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            NORMALIZED_CSV_PATH.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            SUMMARY_JSON_PATH.relative_to(
                ROOT
            )
        )
    )
    print(
        "  "
        + str(
            FIGURE_PATH.relative_to(
                ROOT
            )
        )
    )

    print()
    print(
        "PHASE 5A MISSION SPACE-WEATHER "
        "CONTEXT COMPLETE"
    )


if __name__ == "__main__":
    main()
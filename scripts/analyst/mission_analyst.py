from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

MISSION_PATH = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

REFERENCE_DIR = (
    ROOT
    / "data"
    / "reference"
)

PHASE7A_PATH = (
    REFERENCE_DIR
    / "artemis_ii_mission_control_perspectives.json"
)

PHASE7B_PATH = (
    REFERENCE_DIR
    / "artemis_ii_decision_threads.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "analyst"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "artemis_ii_mission_analyst_index.json"
)

REFERENCE_PATH = (
    REFERENCE_DIR
    / "artemis_ii_mission_analyst_index.json"
)


EXPECTED_PHASE7A_DATASET = (
    "phase7a_artemis_ii_"
    "mission_control_perspectives"
)

EXPECTED_PHASE7B_DATASET = (
    "phase7b_artemis_ii_"
    "mission_control_decision_threads"
)

INDEX_DATASET_ID = (
    "phase8a_artemis_ii_"
    "mission_analyst_index"
)

WORD_PATTERN = re.compile(
    r"[A-Za-z0-9_./:+-]+"
)


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 8A ANALYST FAILED: "
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
) -> Any:
    require(
        path.exists(),
        f"missing JSON file: {path}",
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


def write_json(
    path: Path,
    value: Any,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            value,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write(
            "\n"
        )


def relpath(
    path: Path,
) -> str:
    return str(
        path.relative_to(
            ROOT
        )
    ).replace(
        "\\",
        "/",
    )


def parse_utc(
    value: str,
) -> datetime:
    normalized = value.strip()

    if normalized.endswith(
        "Z"
    ):
        normalized = (
            normalized[:-1]
            + "+00:00"
        )

    try:
        result = datetime.fromisoformat(
            normalized
        )

    except ValueError as exc:
        fail(
            f"invalid UTC timestamp: {value}"
        )
        raise exc

    if result.tzinfo is None:
        result = result.replace(
            tzinfo=timezone.utc
        )

    return result.astimezone(
        timezone.utc
    )


def format_utc(
    value: datetime,
) -> str:
    value = value.astimezone(
        timezone.utc
    )

    if value.microsecond:
        text = value.isoformat(
            timespec="milliseconds"
        )
    else:
        text = value.isoformat(
            timespec="seconds"
        )

    return text.replace(
        "+00:00",
        "Z",
    )


def format_seconds(
    seconds: float,
) -> str:
    sign = ""

    if seconds < 0:
        sign = "-"
        seconds = abs(
            seconds
        )

    days = int(
        seconds
        // 86400
    )
    seconds -= (
        days
        * 86400
    )

    hours = int(
        seconds
        // 3600
    )
    seconds -= (
        hours
        * 3600
    )

    minutes = int(
        seconds
        // 60
    )
    seconds -= (
        minutes
        * 60
    )

    if abs(
        seconds
        - round(
            seconds
        )
    ) < 1e-9:
        second_text = (
            f"{int(round(seconds)):02d}"
        )
    else:
        second_text = (
            f"{seconds:06.3f}"
        )

    return (
        f"{sign}"
        f"{days:02d}:"
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{second_text}"
    )


def parse_met(
    value: str,
) -> float:
    text = value.strip()
    sign = 1.0

    if text.startswith(
        "-"
    ):
        sign = -1.0
        text = text[1:]

    parts = text.split(
        ":"
    )

    require(
        len(
            parts
        )
        == 4,
        (
            "MET must use "
            "DD:HH:MM:SS[.sss]"
        ),
    )

    try:
        days = int(
            parts[0]
        )
        hours = int(
            parts[1]
        )
        minutes = int(
            parts[2]
        )
        seconds = float(
            parts[3]
        )

    except ValueError as exc:
        fail(
            f"invalid MET value: {value}"
        )
        raise exc

    require(
        days
        >= 0,
        "MET days must be non-negative",
    )

    require(
        0
        <= hours
        < 24,
        "MET hours must be 0-23",
    )

    require(
        0
        <= minutes
        < 60,
        "MET minutes must be 0-59",
    )

    require(
        0.0
        <= seconds
        < 60.0,
        "MET seconds must be 0-59.999...",
    )

    total = (
        days
        * 86400
        + hours
        * 3600
        + minutes
        * 60
        + seconds
    )

    return (
        sign
        * total
    )


def utc_to_met(
    utc_value: str,
    launch: datetime,
) -> dict:
    timestamp = parse_utc(
        utc_value
    )

    seconds = (
        timestamp
        - launch
    ).total_seconds()

    return {
        "tool": "utc_to_met",
        "input_utc": format_utc(
            timestamp
        ),
        "launch_epoch_utc": format_utc(
            launch
        ),
        "elapsed_seconds": seconds,
        "met": format_seconds(
            seconds
        ),
        "deterministic": True,
    }


def met_to_utc(
    met_value: str,
    launch: datetime,
) -> dict:
    seconds = parse_met(
        met_value
    )

    timestamp = (
        launch
        + timedelta(
            seconds=seconds
        )
    )

    return {
        "tool": "met_to_utc",
        "input_met": met_value,
        "launch_epoch_utc": format_utc(
            launch
        ),
        "elapsed_seconds": seconds,
        "utc": format_utc(
            timestamp
        ),
        "deterministic": True,
    }


def elapsed_time(
    start_value: str,
    stop_value: str,
) -> dict:
    start = parse_utc(
        start_value
    )
    stop = parse_utc(
        stop_value
    )

    seconds = (
        stop
        - start
    ).total_seconds()

    return {
        "tool": "elapsed_time",
        "start_utc": format_utc(
            start
        ),
        "stop_utc": format_utc(
            stop
        ),
        "elapsed_seconds": seconds,
        "elapsed_minutes": (
            seconds
            / 60.0
        ),
        "elapsed_hours": (
            seconds
            / 3600.0
        ),
        "formatted": format_seconds(
            seconds
        ),
        "deterministic": True,
    }


def citation(
    dataset_id: str | None,
    path: str,
    locator: str,
    evidence_class: str | None = None,
    url: str | None = None,
) -> dict:
    result = {
        "dataset_id": dataset_id,
        "path": path,
        "locator": locator,
        "evidence_class": evidence_class,
        "citation_text": (
            f"{path} :: {locator}"
        ),
    }

    if url:
        result[
            "url"
        ] = url

    return result


def iter_dicts(
    value: Any,
):
    if isinstance(
        value,
        dict,
    ):
        yield value

        for child in value.values():
            yield from iter_dicts(
                child
            )

    elif isinstance(
        value,
        list,
    ):
        for child in value:
            yield from iter_dicts(
                child
            )


def reference_json_files() -> list[Path]:
    return sorted(
        path
        for path
        in REFERENCE_DIR.glob(
            "*.json"
        )
        if path
        != REFERENCE_PATH
    )


def build_dataset_registry() -> list[dict]:
    records = []

    for path in reference_json_files():
        value = load_json(
            path
        )

        if not isinstance(
            value,
            dict,
        ):
            continue

        dataset_id = value.get(
            "dataset_id"
        )

        if not dataset_id:
            continue

        records.append(
            {
                "dataset_id": dataset_id,
                "mission": value.get(
                    "mission"
                ),
                "phase": value.get(
                    "phase"
                ),
                "status": value.get(
                    "status"
                ),
                "title": (
                    value.get(
                        "title"
                    )
                    or value.get(
                        "purpose"
                    )
                    or dataset_id
                ),
                "path": relpath(
                    path
                ),
                "top_level_keys": sorted(
                    value.keys()
                ),
                "citation": citation(
                    dataset_id,
                    relpath(
                        path
                    ),
                    "$",
                    (
                        value.get(
                            "provenance"
                        )
                        or value.get(
                            "evidence_class"
                        )
                    ),
                ),
            }
        )

    ids = [
        item[
            "dataset_id"
        ]
        for item
        in records
    ]

    require(
        len(
            ids
        )
        == len(
            set(
                ids
            )
        ),
        (
            "duplicate dataset_id values "
            "found in data/reference"
        ),
    )

    return records


def merge_source(
    registry: dict[str, dict],
    source: dict,
    dataset_id: str | None,
    path: str,
):
    source_id = source.get(
        "source_id"
    )

    if not source_id:
        return

    if not any(
        key
        in source
        for key
        in [
            "url",
            "title",
            "publisher",
            "source_type",
            "source_organization",
        ]
    ):
        return

    occurrence = {
        "dataset_id": dataset_id,
        "path": path,
    }

    existing = registry.get(
        source_id
    )

    if existing is None:
        registry[
            source_id
        ] = {
            "source_id": source_id,
            "publisher": (
                source.get(
                    "publisher"
                )
                or source.get(
                    "source_organization"
                )
            ),
            "title": source.get(
                "title"
            ),
            "publication_date": (
                source.get(
                    "publication_date"
                )
                or source.get(
                    "source_date"
                )
            ),
            "url": source.get(
                "url"
            ),
            "source_type": source.get(
                "source_type"
            ),
            "role": (
                source.get(
                    "role"
                )
                or source.get(
                    "claim"
                )
            ),
            "occurrences": [
                occurrence
            ],
        }

    else:
        if occurrence not in existing[
            "occurrences"
        ]:
            existing[
                "occurrences"
            ].append(
                occurrence
            )

        for key, aliases in {
            "publisher": [
                "publisher",
                "source_organization",
            ],
            "title": [
                "title",
            ],
            "publication_date": [
                "publication_date",
                "source_date",
            ],
            "url": [
                "url",
            ],
            "source_type": [
                "source_type",
            ],
            "role": [
                "role",
                "claim",
            ],
        }.items():
            if existing.get(
                key
            ):
                continue

            for alias in aliases:
                candidate = source.get(
                    alias
                )

                if candidate:
                    existing[
                        key
                    ] = candidate
                    break


def build_source_registry() -> list[dict]:
    registry: dict[str, dict] = {}

    for path in reference_json_files():
        value = load_json(
            path
        )

        if not isinstance(
            value,
            dict,
        ):
            continue

        dataset_id = value.get(
            "dataset_id"
        )

        relative = relpath(
            path
        )

        for item in iter_dicts(
            value
        ):
            merge_source(
                registry,
                item,
                dataset_id,
                relative,
            )

    records = sorted(
        registry.values(),
        key=lambda item: item[
            "source_id"
        ],
    )

    for item in records:
        occurrence = item[
            "occurrences"
        ][0]

        item[
            "citation"
        ] = citation(
            occurrence.get(
                "dataset_id"
            ),
            occurrence[
                "path"
            ],
            (
                "source_id="
                + item[
                    "source_id"
                ]
            ),
            "SOURCE_METADATA",
            item.get(
                "url"
            ),
        )

    return records


def build_event_registry(
    phase7a: dict,
) -> list[dict]:
    records = []

    dataset_id = phase7a[
        "dataset_id"
    ]

    path = relpath(
        PHASE7A_PATH
    )

    for event in phase7a[
        "shared_timeline"
    ]:
        event_id = event[
            "event_id"
        ]

        records.append(
            {
                "event_id": event_id,
                "order": event[
                    "order"
                ],
                "name": event[
                    "name"
                ],
                "timestamp_utc": event.get(
                    "timestamp_utc"
                ),
                "date_utc": event.get(
                    "date_utc"
                ),
                "met": event.get(
                    "met"
                ),
                "time_precision": event[
                    "time_precision"
                ],
                "evidence_class": event[
                    "evidence_class"
                ],
                "classification": event[
                    "classification"
                ],
                "summary": event[
                    "summary"
                ],
                "source_dependency": event[
                    "source_dependency"
                ],
                "primary_lenses": event[
                    "primary_lenses"
                ],
                "priorities": event[
                    "priorities"
                ],
                "citation": citation(
                    dataset_id,
                    path,
                    (
                        "shared_timeline"
                        f"[event_id={event_id}]"
                    ),
                    event[
                        "evidence_class"
                    ],
                ),
            }
        )

    require(
        len(
            records
        )
        == 24,
        (
            "expected 24 Phase 7A events, "
            f"found {len(records)}"
        ),
    )

    return records


def build_thread_registry(
    phase7b: dict,
) -> list[dict]:
    records = []

    dataset_id = phase7b[
        "dataset_id"
    ]

    path = relpath(
        PHASE7B_PATH
    )

    for thread in phase7b[
        "decision_threads"
    ]:
        thread_id = thread[
            "thread_id"
        ]

        records.append(
            {
                "thread_id": thread_id,
                "title": thread[
                    "title"
                ],
                "classification": thread[
                    "classification"
                ],
                "anomaly": thread[
                    "anomaly"
                ],
                "primary_lenses": thread[
                    "primary_lenses"
                ],
                "anchor_event_ids": thread[
                    "anchor_event_ids"
                ],
                "stages": thread[
                    "stages"
                ],
                "guardrails": thread[
                    "guardrails"
                ],
                "maturity": phase7b[
                    "decision_maturity"
                ][
                    thread_id
                ],
                "citation": citation(
                    dataset_id,
                    path,
                    (
                        "decision_threads"
                        f"[thread_id={thread_id}]"
                    ),
                    "MISSION_CONTROL_DECISION_SYNTHESIS",
                ),
            }
        )

    require(
        len(
            records
        )
        == 10,
        (
            "expected 10 Phase 7B decision "
            f"threads, found {len(records)}"
        ),
    )

    return records


def build_postflight_registry(
    phase7b: dict,
) -> list[dict]:
    records = []

    dataset_id = phase7b[
        "dataset_id"
    ]

    path = relpath(
        PHASE7B_PATH
    )

    for item in phase7b[
        "postflight_engineering_timeline"
    ]:
        record_id = item[
            "record_id"
        ]

        result = dict(
            item
        )

        result[
            "citation"
        ] = citation(
            dataset_id,
            path,
            (
                "postflight_engineering_timeline"
                f"[record_id={record_id}]"
            ),
            "NASA_POSTFLIGHT_REPORTED",
        )

        records.append(
            result
        )

    require(
        len(
            records
        )
        == 6,
        (
            "expected 6 postflight records, "
            f"found {len(records)}"
        ),
    )

    return records


def record_search_text(
    value: Any,
) -> str:
    if isinstance(
        value,
        dict,
    ):
        parts = []

        for key, child in value.items():
            if key in {
                "citation",
                "priorities",
                "top_level_keys",
                "occurrences",
            }:
                continue

            parts.append(
                record_search_text(
                    child
                )
            )

        return " ".join(
            parts
        )

    if isinstance(
        value,
        list,
    ):
        return " ".join(
            record_search_text(
                child
            )
            for child
            in value
        )

    if value is None:
        return ""

    return str(
        value
    )


def tokenize(
    value: str,
) -> list[str]:
    return [
        token.lower()
        for token
        in WORD_PATTERN.findall(
            value
        )
        if token.strip()
    ]


def make_unified_records(
    datasets: list[dict],
    sources: list[dict],
    events: list[dict],
    threads: list[dict],
    postflight: list[dict],
) -> list[dict]:
    records = []

    for item in events:
        records.append(
            {
                "record_type": "event",
                "record_id": item[
                    "event_id"
                ],
                "title": item[
                    "name"
                ],
                "summary": item[
                    "summary"
                ],
                "citation": item[
                    "citation"
                ],
                "payload": item,
            }
        )

    for item in threads:
        stage_text = " ".join(
            stage[
                "summary"
            ]
            for stage
            in item[
                "stages"
            ].values()
        )

        records.append(
            {
                "record_type": (
                    "decision_thread"
                ),
                "record_id": item[
                    "thread_id"
                ],
                "title": item[
                    "title"
                ],
                "summary": stage_text,
                "citation": item[
                    "citation"
                ],
                "payload": item,
            }
        )

    for item in postflight:
        records.append(
            {
                "record_type": (
                    "postflight_record"
                ),
                "record_id": item[
                    "record_id"
                ],
                "title": item[
                    "category"
                ],
                "summary": item[
                    "summary"
                ],
                "citation": item[
                    "citation"
                ],
                "payload": item,
            }
        )

    for item in sources:
        records.append(
            {
                "record_type": "source",
                "record_id": item[
                    "source_id"
                ],
                "title": (
                    item.get(
                        "title"
                    )
                    or item[
                        "source_id"
                    ]
                ),
                "summary": (
                    item.get(
                        "role"
                    )
                    or ""
                ),
                "citation": item[
                    "citation"
                ],
                "payload": item,
            }
        )

    for item in datasets:
        records.append(
            {
                "record_type": "dataset",
                "record_id": item[
                    "dataset_id"
                ],
                "title": item[
                    "title"
                ],
                "summary": (
                    (
                        "phase="
                        + str(
                            item.get(
                                "phase"
                            )
                        )
                    )
                    + " "
                    + (
                        "status="
                        + str(
                            item.get(
                                "status"
                            )
                        )
                    )
                ),
                "citation": item[
                    "citation"
                ],
                "payload": item,
            }
        )

    for record in records:
        search_text = (
            record[
                "record_id"
            ]
            + " "
            + record[
                "title"
            ]
            + " "
            + record[
                "summary"
            ]
            + " "
            + record_search_text(
                record[
                    "payload"
                ]
            )
        )

        record[
            "search_tokens"
        ] = sorted(
            set(
                tokenize(
                    search_text
                )
            )
        )

    return records


def tool_registry() -> list[dict]:
    return [
        {
            "tool_id": "search",
            "deterministic": True,
            "network_required": False,
            "description": (
                "Search the unified analyst index "
                "across events, decision threads, "
                "postflight records, sources, and datasets."
            ),
        },
        {
            "tool_id": "event_lookup",
            "deterministic": True,
            "network_required": False,
            "description": (
                "Retrieve one exact shared-timeline "
                "event by event_id."
            ),
        },
        {
            "tool_id": "decision_thread_lookup",
            "deterministic": True,
            "network_required": False,
            "description": (
                "Retrieve one exact Phase 7 "
                "decision thread by thread_id."
            ),
        },
        {
            "tool_id": "source_lookup",
            "deterministic": True,
            "network_required": False,
            "description": (
                "Retrieve normalized public source "
                "metadata and its local provenance."
            ),
        },
        {
            "tool_id": "dataset_lookup",
            "deterministic": True,
            "network_required": False,
            "description": (
                "Retrieve one indexed reference "
                "dataset by dataset_id."
            ),
        },
        {
            "tool_id": "utc_to_met",
            "deterministic": True,
            "network_required": False,
            "description": (
                "Convert UTC to Artemis II Mission "
                "Elapsed Time using mission.json."
            ),
        },
        {
            "tool_id": "met_to_utc",
            "deterministic": True,
            "network_required": False,
            "description": (
                "Convert Mission Elapsed Time "
                "DD:HH:MM:SS[.sss] to UTC."
            ),
        },
        {
            "tool_id": "elapsed_time",
            "deterministic": True,
            "network_required": False,
            "description": (
                "Calculate deterministic elapsed "
                "time between two UTC timestamps."
            ),
        },
    ]


def build_index() -> dict:
    mission = load_json(
        MISSION_PATH
    )

    phase7a = load_json(
        PHASE7A_PATH
    )

    phase7b = load_json(
        PHASE7B_PATH
    )

    require(
        mission.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        phase7a.get(
            "dataset_id"
        )
        == EXPECTED_PHASE7A_DATASET,
        "Phase 7A dependency mismatch",
    )

    require(
        phase7b.get(
            "dataset_id"
        )
        == EXPECTED_PHASE7B_DATASET,
        "Phase 7B dependency mismatch",
    )

    datasets = build_dataset_registry()
    sources = build_source_registry()
    events = build_event_registry(
        phase7a
    )
    threads = build_thread_registry(
        phase7b
    )
    postflight = build_postflight_registry(
        phase7b
    )

    unified = make_unified_records(
        datasets,
        sources,
        events,
        threads,
        postflight,
    )

    tools = tool_registry()

    result = {
        "dataset_id": INDEX_DATASET_ID,
        "mission": "Artemis II",
        "phase": "8A",
        "status": (
            "STRUCTURED_RETRIEVAL_AND_"
            "DETERMINISTIC_TOOLS_COMPLETE"
        ),
        "purpose": (
            "Provide an evidence-grounded, "
            "zero-cost structured retrieval and "
            "deterministic calculation layer over "
            "validated Artemis II MissionLab artifacts."
        ),
        "mission_clock": {
            "launch_epoch_utc": (
                mission[
                    "launch_epoch_utc"
                ]
            ),
            "source": (
                relpath(
                    MISSION_PATH
                )
            ),
        },
        "dependency_registry": [
            {
                "dataset_id": (
                    phase7a[
                        "dataset_id"
                    ]
                ),
                "path": relpath(
                    PHASE7A_PATH
                ),
                "role": (
                    "shared mission events and "
                    "discipline priorities"
                ),
            },
            {
                "dataset_id": (
                    phase7b[
                        "dataset_id"
                    ]
                ),
                "path": relpath(
                    PHASE7B_PATH
                ),
                "role": (
                    "decision threads and "
                    "postflight engineering timeline"
                ),
            },
        ],
        "dataset_registry": datasets,
        "source_registry": sources,
        "event_registry": events,
        "decision_thread_registry": threads,
        "postflight_registry": postflight,
        "unified_records": unified,
        "tool_registry": tools,
        "retrieval_policy": {
            "structured_local_artifacts_first": True,
            "exact_id_lookup_supported": True,
            "keyword_search_supported": True,
            "record_type_filter_supported": True,
            "citations_returned_with_records": True,
            "source_urls_preserved_when_available": True,
            "missing_fact_may_be_invented": False,
            "missionlab_derived_may_be_labeled_nasa_reported": False,
            "unknown_timing_may_be_given_exact_utc": False,
        },
        "calculation_policy": {
            "utc_met_conversion_uses_mission_json": True,
            "elapsed_time_is_deterministic": True,
            "network_required": False,
            "paid_model_required": False,
            "llm_required": False,
        },
        "phase8_roadmap_assessment": {
            "structured_retrieval_over_events_data_sources": (
                "COMPLETE_PHASE8A"
            ),
            "deterministic_calculations_exposed_as_tools": (
                "COMPLETE_PHASE8A"
            ),
            "citation_first_answers": (
                "PENDING_PHASE8B"
            ),
            "optional_local_browser_llm": (
                "PENDING_PHASE8B"
            ),
            "no_paid_model_dependency": (
                "SATISFIED_PHASE8A"
            ),
        },
        "outputs": {
            "reference_json": (
                "data/reference/"
                "artemis_ii_mission_analyst_index.json"
            ),
            "processed_json": (
                "data/processed/analyst/"
                "artemis_ii_mission_analyst_index.json"
            ),
        },
    }

    return result


def load_index() -> dict:
    if not REFERENCE_PATH.exists():
        fail(
            "analyst index not built; run "
            "'build-index' first"
        )

    value = load_json(
        REFERENCE_PATH
    )

    require(
        value.get(
            "dataset_id"
        )
        == INDEX_DATASET_ID,
        "analyst index identity mismatch",
    )

    return value


def exact_lookup(
    index: dict,
    registry_key: str,
    id_key: str,
    record_id: str,
) -> dict:
    for item in index[
        registry_key
    ]:
        if item.get(
            id_key
        ) == record_id:
            return item

    fail(
        f"{id_key} not found: {record_id}"
    )
    raise RuntimeError


def search_index(
    index: dict,
    query: str,
    record_type: str | None,
    limit: int,
) -> list[dict]:
    tokens = tokenize(
        query
    )

    require(
        len(
            tokens
        )
        > 0,
        "search query produced no tokens",
    )

    require(
        limit
        >= 1,
        "search limit must be >= 1",
    )

    allowed_types = {
        "event",
        "decision_thread",
        "postflight_record",
        "source",
        "dataset",
    }

    if record_type is not None:
        require(
            record_type
            in allowed_types,
            (
                "record type must be one of: "
                + ", ".join(
                    sorted(
                        allowed_types
                    )
                )
            ),
        )

    results = []

    query_lower = query.lower()

    for record in index[
        "unified_records"
    ]:
        if (
            record_type
            is not None
            and record[
                "record_type"
            ]
            != record_type
        ):
            continue

        record_tokens = set(
            record[
                "search_tokens"
            ]
        )

        matched = [
            token
            for token
            in tokens
            if token
            in record_tokens
        ]

        if not matched:
            continue

        score = (
            len(
                matched
            )
            * 10
        )

        record_id_lower = record[
            "record_id"
        ].lower()

        title_lower = record[
            "title"
        ].lower()

        if query_lower == record_id_lower:
            score += 100

        if query_lower in record_id_lower:
            score += 25

        if query_lower in title_lower:
            score += 20

        score += sum(
            3
            for token
            in matched
            if token
            in title_lower
        )

        results.append(
            {
                "score": score,
                "record_type": (
                    record[
                        "record_type"
                    ]
                ),
                "record_id": (
                    record[
                        "record_id"
                    ]
                ),
                "title": (
                    record[
                        "title"
                    ]
                ),
                "summary": (
                    record[
                        "summary"
                    ]
                ),
                "matched_tokens": (
                    matched
                ),
                "citation": (
                    record[
                        "citation"
                    ]
                ),
            }
        )

    results.sort(
        key=lambda item: (
            -item[
                "score"
            ],
            item[
                "record_type"
            ],
            item[
                "record_id"
            ],
        )
    )

    return results[
        :limit
    ]


def print_json(
    value: Any,
):
    print(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
        )
    )


def run_build_index():
    result = build_index()

    write_json(
        REFERENCE_PATH,
        result,
    )

    write_json(
        OUTPUT_PATH,
        result,
    )

    launch = parse_utc(
        result[
            "mission_clock"
        ][
            "launch_epoch_utc"
        ]
    )

    otc3 = utc_to_met(
        "2026-04-06T03:03:00Z",
        launch,
    )

    earthset_to_earthrise = elapsed_time(
        "2026-04-06T22:41:00Z",
        "2026-04-06T23:22:00Z",
    )

    smoke_search = search_index(
        result,
        "return link RTC2",
        None,
        5,
    )

    require(
        len(
            smoke_search
        )
        >= 1,
        "smoke search returned no results",
    )

    require(
        any(
            item[
                "record_id"
            ]
            == "RETURN_LINK_ANOMALY_RTC2"
            for item
            in smoke_search
        ),
        (
            "smoke search did not retrieve "
            "RETURN_LINK_ANOMALY_RTC2"
        ),
    )

    print()
    print(
        "Phase 8A Artemis II Evidence-Grounded "
        "Mission Analyst"
    )
    print(
        "=" * 72
    )

    print()
    print(
        "Dependencies:"
    )
    print(
        "  Phase 7A shared mission timeline: PASS"
    )
    print(
        "  Phase 7B decision threads: PASS"
    )
    print(
        "  mission clock configuration: PASS"
    )

    print()
    print(
        "Structured retrieval index:"
    )
    print(
        "  reference datasets: "
        f"{len(result['dataset_registry'])}"
    )
    print(
        "  normalized public sources: "
        f"{len(result['source_registry'])}"
    )
    print(
        "  shared mission events: "
        f"{len(result['event_registry'])}"
    )
    print(
        "  decision threads: "
        f"{len(result['decision_thread_registry'])}"
    )
    print(
        "  postflight records: "
        f"{len(result['postflight_registry'])}"
    )
    print(
        "  unified searchable records: "
        f"{len(result['unified_records'])}"
    )

    print()
    print(
        "Deterministic analyst tools:"
    )

    for tool in result[
        "tool_registry"
    ]:
        print(
            "  "
            + tool[
                "tool_id"
            ]
            + ": READY"
        )

    print()
    print(
        "Citation policy:"
    )
    print(
        "  local artifact citation returned "
        "with every indexed record: YES"
    )
    print(
        "  source URL preserved when available: YES"
    )
    print(
        "  unsupported fact invention permitted: NO"
    )
    print(
        "  MissionLab-derived may be relabeled "
        "NASA-reported: NO"
    )
    print(
        "  unknown timing may receive exact UTC: NO"
    )

    print()
    print(
        "Calculation smoke tests:"
    )
    print(
        "  OTC3 UTC -> MET: "
        + otc3[
            "met"
        ]
    )
    print(
        "  Earthset -> Earthrise elapsed: "
        + earthset_to_earthrise[
            "formatted"
        ]
    )

    print()
    print(
        "Retrieval smoke test:"
    )

    for item in smoke_search[
        :3
    ]:
        print(
            "  "
            + item[
                "record_type"
            ]
            + "  "
            + item[
                "record_id"
            ]
            + "  score="
            + str(
                item[
                    "score"
                ]
            )
        )
        print(
            "    citation: "
            + item[
                "citation"
            ][
                "citation_text"
            ]
        )

    print()
    print(
        "Phase 8 roadmap state:"
    )
    print(
        "  structured retrieval over "
        "events/data/sources: COMPLETE 8A"
    )
    print(
        "  deterministic calculations as tools: COMPLETE 8A"
    )
    print(
        "  citation-first answer composer: PENDING 8B"
    )
    print(
        "  optional local/browser LLM: PENDING 8B"
    )
    print(
        "  paid model dependency: NONE"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + relpath(
            REFERENCE_PATH
        )
    )
    print(
        "  "
        + relpath(
            OUTPUT_PATH
        )
    )

    print()
    print(
        "PHASE 8A STRUCTURED RETRIEVAL "
        "AND DETERMINISTIC TOOLS COMPLETE"
    )


def run_stats():
    index = load_index()

    print_json(
        {
            "dataset_id": (
                index[
                    "dataset_id"
                ]
            ),
            "datasets": len(
                index[
                    "dataset_registry"
                ]
            ),
            "sources": len(
                index[
                    "source_registry"
                ]
            ),
            "events": len(
                index[
                    "event_registry"
                ]
            ),
            "decision_threads": len(
                index[
                    "decision_thread_registry"
                ]
            ),
            "postflight_records": len(
                index[
                    "postflight_registry"
                ]
            ),
            "unified_records": len(
                index[
                    "unified_records"
                ]
            ),
            "tools": len(
                index[
                    "tool_registry"
                ]
            ),
        }
    )


def run_tool(
    args: argparse.Namespace,
):
    index = load_index()

    launch = parse_utc(
        index[
            "mission_clock"
        ][
            "launch_epoch_utc"
        ]
    )

    if args.tool_name == "utc-to-met":
        print_json(
            utc_to_met(
                args.value,
                launch,
            )
        )

    elif args.tool_name == "met-to-utc":
        print_json(
            met_to_utc(
                args.value,
                launch,
            )
        )

    elif args.tool_name == "elapsed":
        print_json(
            elapsed_time(
                args.value,
                args.stop,
            )
        )

    else:
        fail(
            f"unknown calculation tool: {args.tool_name}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Artemis II evidence-grounded "
            "MissionLab analyst"
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "build-index",
        help=(
            "Build the Phase 8A structured "
            "retrieval index."
        ),
    )

    subparsers.add_parser(
        "stats",
        help="Show analyst index counts.",
    )

    event_parser = subparsers.add_parser(
        "event",
        help="Retrieve an exact event by event_id.",
    )
    event_parser.add_argument(
        "event_id",
    )

    thread_parser = subparsers.add_parser(
        "thread",
        help=(
            "Retrieve an exact decision thread "
            "by thread_id."
        ),
    )
    thread_parser.add_argument(
        "thread_id",
    )

    source_parser = subparsers.add_parser(
        "source",
        help="Retrieve an exact source by source_id.",
    )
    source_parser.add_argument(
        "source_id",
    )

    dataset_parser = subparsers.add_parser(
        "dataset",
        help=(
            "Retrieve an exact reference dataset "
            "by dataset_id."
        ),
    )
    dataset_parser.add_argument(
        "dataset_id",
    )

    search_parser = subparsers.add_parser(
        "search",
        help=(
            "Search events, threads, postflight "
            "records, sources, and datasets."
        ),
    )
    search_parser.add_argument(
        "query",
    )
    search_parser.add_argument(
        "--type",
        dest="record_type",
        default=None,
        choices=[
            "event",
            "decision_thread",
            "postflight_record",
            "source",
            "dataset",
        ],
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    tool_parser = subparsers.add_parser(
        "tool",
        help=(
            "Run a deterministic mission-time "
            "calculation tool."
        ),
    )
    tool_parser.add_argument(
        "tool_name",
        choices=[
            "utc-to-met",
            "met-to-utc",
            "elapsed",
        ],
    )
    tool_parser.add_argument(
        "value",
        help=(
            "UTC for utc-to-met/elapsed start, "
            "or MET for met-to-utc."
        ),
    )
    tool_parser.add_argument(
        "stop",
        nargs="?",
        help=(
            "Stop UTC for elapsed."
        ),
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "build-index":
        run_build_index()
        return

    if args.command == "stats":
        run_stats()
        return

    index = load_index()

    if args.command == "event":
        print_json(
            exact_lookup(
                index,
                "event_registry",
                "event_id",
                args.event_id,
            )
        )

    elif args.command == "thread":
        print_json(
            exact_lookup(
                index,
                "decision_thread_registry",
                "thread_id",
                args.thread_id,
            )
        )

    elif args.command == "source":
        print_json(
            exact_lookup(
                index,
                "source_registry",
                "source_id",
                args.source_id,
            )
        )

    elif args.command == "dataset":
        print_json(
            exact_lookup(
                index,
                "dataset_registry",
                "dataset_id",
                args.dataset_id,
            )
        )

    elif args.command == "search":
        print_json(
            search_index(
                index,
                args.query,
                args.record_type,
                args.limit,
            )
        )

    elif args.command == "tool":
        if (
            args.tool_name
            == "elapsed"
            and not args.stop
        ):
            fail(
                "elapsed requires START_UTC STOP_UTC"
            )

        run_tool(
            args
        )

    else:
        parser.error(
            "unsupported command"
        )


if __name__ == "__main__":
    main()
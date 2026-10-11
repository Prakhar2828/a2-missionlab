from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_mission_analyst_index.json"
)

PROCESSED_PATH = (
    ROOT
    / "data"
    / "processed"
    / "analyst"
    / "artemis_ii_mission_analyst_index.json"
)

ANALYST_PATH = (
    ROOT
    / "scripts"
    / "analyst"
    / "mission_analyst.py"
)

MISSION_PATH = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)


EXPECTED_DATASET_ID = (
    "phase8a_artemis_ii_"
    "mission_analyst_index"
)

EXPECTED_COUNTS = {
    "datasets": 25,
    "sources": 81,
    "events": 24,
    "decision_threads": 10,
    "postflight_records": 6,
    "unified_records": 146,
    "tools": 8,
}

EXPECTED_TOOLS = [
    "search",
    "event_lookup",
    "decision_thread_lookup",
    "source_lookup",
    "dataset_lookup",
    "utc_to_met",
    "met_to_utc",
    "elapsed_time",
]

EXPECTED_RECORD_TYPES = {
    "event",
    "decision_thread",
    "postflight_record",
    "source",
    "dataset",
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 8A VALIDATION FAILED: "
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
):
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


def load_analyst_module():
    require(
        ANALYST_PATH.exists(),
        f"missing analyst module: {ANALYST_PATH}",
    )

    spec = importlib.util.spec_from_file_location(
        "mission_analyst",
        ANALYST_PATH,
    )

    require(
        spec is not None,
        "could not create analyst module spec",
    )

    require(
        spec.loader is not None,
        "analyst module spec has no loader",
    )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def index_by(
    records: list[dict],
    key: str,
) -> dict[str, dict]:
    return {
        item[
            key
        ]: item
        for item
        in records
    }


def validate_identity(
    reference: dict,
    processed: dict,
):
    require(
        reference
        == processed,
        (
            "reference and processed "
            "analyst indices differ"
        ),
    )

    require(
        reference.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "Phase 8A dataset identity mismatch",
    )

    require(
        reference.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        reference.get(
            "phase"
        )
        == "8A",
        "phase identity mismatch",
    )

    require(
        reference.get(
            "status"
        )
        == (
            "STRUCTURED_RETRIEVAL_AND_"
            "DETERMINISTIC_TOOLS_COMPLETE"
        ),
        "Phase 8A status mismatch",
    )


def validate_mission_clock(
    reference: dict,
    mission: dict,
):
    require(
        mission.get(
            "mission"
        )
        == "Artemis II",
        "mission config identity mismatch",
    )

    require(
        reference[
            "mission_clock"
        ][
            "launch_epoch_utc"
        ]
        == "2026-04-01T22:35:12Z",
        "analyst mission-clock launch mismatch",
    )

    require(
        reference[
            "mission_clock"
        ][
            "launch_epoch_utc"
        ]
        == mission[
            "launch_epoch_utc"
        ],
        (
            "analyst launch epoch does not match "
            "mission.json"
        ),
    )

    require(
        reference[
            "mission_clock"
        ][
            "source"
        ]
        == "data/config/mission.json",
        "mission-clock source path mismatch",
    )


def validate_dependencies(
    reference: dict,
):
    dependencies = reference[
        "dependency_registry"
    ]

    require(
        len(
            dependencies
        )
        == 2,
        (
            "expected 2 direct Phase 8A dependencies, "
            f"found {len(dependencies)}"
        ),
    )

    ids = [
        item[
            "dataset_id"
        ]
        for item
        in dependencies
    ]

    require(
        ids
        == [
            (
                "phase7a_artemis_ii_"
                "mission_control_perspectives"
            ),
            (
                "phase7b_artemis_ii_"
                "mission_control_decision_threads"
            ),
        ],
        "Phase 8A dependency registry mismatch",
    )

    require(
        dependencies[
            0
        ][
            "path"
        ]
        == (
            "data/reference/"
            "artemis_ii_mission_control_perspectives.json"
        ),
        "Phase 7A dependency path mismatch",
    )

    require(
        dependencies[
            1
        ][
            "path"
        ]
        == (
            "data/reference/"
            "artemis_ii_decision_threads.json"
        ),
        "Phase 7B dependency path mismatch",
    )


def validate_dataset_registry(
    reference: dict,
):
    records = reference[
        "dataset_registry"
    ]

    require(
        len(
            records
        )
        == EXPECTED_COUNTS[
            "datasets"
        ],
        (
            "expected "
            f"{EXPECTED_COUNTS['datasets']} datasets, "
            f"found {len(records)}"
        ),
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
        "duplicate dataset IDs",
    )

    require(
        EXPECTED_DATASET_ID
        not in ids,
        (
            "Phase 8A analyst index incorrectly "
            "indexed itself as an input dataset"
        ),
    )

    required_ids = {
        (
            "phase2k_artemis_ii_"
            "phase2_integrated_operations"
        ),
        (
            "phase3b1_artemis_ii_"
            "waste_management_evidence"
        ),
        (
            "phase4a1_artemis_ii_"
            "entry_descent_recovery_evidence"
        ),
        (
            "phase5b_artemis_ii_"
            "nairas_radiation_interface"
        ),
        (
            "phase6b_artemis_ii_"
            "lunar_observation_reconstruction"
        ),
        (
            "phase7a_artemis_ii_"
            "mission_control_perspectives"
        ),
        (
            "phase7b_artemis_ii_"
            "mission_control_decision_threads"
        ),
    }

    require(
        required_ids.issubset(
            set(
                ids
            )
        ),
        (
            "dataset registry missing one or more "
            "major validated phase products"
        ),
    )

    for item in records:
        require(
            item[
                "path"
            ].startswith(
                "data/reference/"
            ),
            (
                "dataset outside reference registry: "
                f"{item['dataset_id']}"
            ),
        )

        require(
            item[
                "citation"
            ][
                "path"
            ]
            == item[
                "path"
            ],
            (
                "dataset citation path mismatch: "
                f"{item['dataset_id']}"
            ),
        )

        require(
            item[
                "citation"
            ][
                "locator"
            ]
            == "$",
            (
                "dataset root citation locator mismatch: "
                f"{item['dataset_id']}"
            ),
        )


def validate_source_registry(
    reference: dict,
):
    records = reference[
        "source_registry"
    ]

    require(
        len(
            records
        )
        == EXPECTED_COUNTS[
            "sources"
        ],
        (
            "expected "
            f"{EXPECTED_COUNTS['sources']} normalized sources, "
            f"found {len(records)}"
        ),
    )

    ids = [
        item[
            "source_id"
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
        "duplicate normalized source IDs",
    )

    index = index_by(
        records,
        "source_id",
    )

    required_sources = {
        (
            "NASA_INITIAL_POSTFLIGHT_"
            "ASSESSMENT_2026_04_20"
        ),
        (
            "NASA_ARTEMIS_II_PRELIMINARY_"
            "LUNAR_SCIENCE_2026_10_07"
        ),
        (
            "NASA_JSC_MISSION_CONTROL_CENTER"
        ),
    }

    require(
        required_sources.issubset(
            set(
                ids
            )
        ),
        (
            "normalized source registry missing "
            "required public sources"
        ),
    )

    for source_id in required_sources:
        require(
            len(
                index[
                    source_id
                ][
                    "occurrences"
                ]
            )
            >= 1,
            (
                "source has no local occurrence: "
                f"{source_id}"
            ),
        )

    url_sources = [
        item
        for item
        in records
        if item.get(
            "url"
        )
    ]

    require(
        len(
            url_sources
        )
        > 0,
        "no source URLs preserved",
    )

    for item in url_sources:
        require(
            item[
                "citation"
            ].get(
                "url"
            )
            == item[
                "url"
            ],
            (
                "source URL not preserved in citation: "
                f"{item['source_id']}"
            ),
        )


def validate_event_registry(
    reference: dict,
):
    records = reference[
        "event_registry"
    ]

    require(
        len(
            records
        )
        == EXPECTED_COUNTS[
            "events"
        ],
        (
            "expected 24 events, "
            f"found {len(records)}"
        ),
    )

    ids = [
        item[
            "event_id"
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
        "duplicate analyst event IDs",
    )

    require(
        [
            item[
                "order"
            ]
            for item
            in records
        ]
        == list(
            range(
                1,
                25,
            )
        ),
        "analyst event ordering mismatch",
    )

    index = index_by(
        records,
        "event_id",
    )

    require(
        index[
            "A2_LAUNCH"
        ][
            "timestamp_utc"
        ]
        == "2026-04-01T22:35:12Z",
        "launch event timestamp mismatch",
    )

    require(
        index[
            "A2_OTC3"
        ][
            "timestamp_utc"
        ]
        == "2026-04-06T03:03:00Z",
        "OTC3 event timestamp mismatch",
    )

    require(
        index[
            "A2_PERICYNTHION"
        ][
            "evidence_class"
        ]
        == "MISSIONLAB_DERIVED_GEOMETRY",
        (
            "pericynthion evidence class "
            "incorrectly relabeled"
        ),
    )

    require(
        index[
            "A2_ENTRY_BLACKOUT"
        ][
            "timestamp_utc"
        ]
        is None,
        (
            "entry blackout was assigned "
            "fabricated exact UTC"
        ),
    )

    require(
        index[
            "A2_RETURN_LINK_LOSS"
        ][
            "time_precision"
        ]
        == "APPROXIMATE_PUBLIC_ANCHOR",
        (
            "return-link timing precision "
            "boundary was lost"
        ),
    )

    require(
        index[
            "A2_SPLASHDOWN"
        ][
            "timestamp_utc"
        ]
        == "2026-04-11T00:07:00Z",
        "splashdown event timestamp mismatch",
    )

    for item in records:
        require(
            item[
                "citation"
            ][
                "locator"
            ]
            == (
                "shared_timeline"
                f"[event_id={item['event_id']}]"
            ),
            (
                "event citation locator mismatch: "
                f"{item['event_id']}"
            ),
        )


def validate_thread_registry(
    reference: dict,
):
    records = reference[
        "decision_thread_registry"
    ]

    require(
        len(
            records
        )
        == EXPECTED_COUNTS[
            "decision_threads"
        ],
        (
            "expected 10 decision threads, "
            f"found {len(records)}"
        ),
    )

    ids = [
        item[
            "thread_id"
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
        "duplicate analyst decision-thread IDs",
    )

    index = index_by(
        records,
        "thread_id",
    )

    require(
        "RETURN_LINK_ANOMALY_RTC2"
        in index,
        "RTC2 decision thread missing",
    )

    require(
        index[
            "RETURN_LINK_ANOMALY_RTC2"
        ][
            "anomaly"
        ]
        is True,
        "RTC2 thread anomaly state mismatch",
    )

    require(
        "TEMPORAL_SEQUENCE != CAUSATION"
        in index[
            "RETURN_LINK_ANOMALY_RTC2"
        ][
            "guardrails"
        ],
        "RTC2 causation guardrail missing",
    )

    require(
        index[
            "LUNAR_COMMUNICATIONS_CONSTRAINT"
        ][
            "anomaly"
        ]
        is False,
        (
            "expected lunar communications constraint "
            "incorrectly marked anomaly"
        ),
    )

    require(
        index[
            "ENTRY_BLACKOUT_REACQUISITION"
        ][
            "anomaly"
        ]
        is False,
        (
            "planned entry blackout "
            "incorrectly marked anomaly"
        ),
    )

    require(
        index[
            "TPS_RISK_MITIGATION_CLOSURE"
        ][
            "maturity"
        ][
            "publicly_established_stages"
        ]
        == 7,
        "TPS thread maturity mismatch",
    )

    for item in records:
        require(
            item[
                "citation"
            ][
                "locator"
            ]
            == (
                "decision_threads"
                f"[thread_id={item['thread_id']}]"
            ),
            (
                "thread citation locator mismatch: "
                f"{item['thread_id']}"
            ),
        )


def validate_postflight_registry(
    reference: dict,
):
    records = reference[
        "postflight_registry"
    ]

    require(
        len(
            records
        )
        == EXPECTED_COUNTS[
            "postflight_records"
        ],
        (
            "expected 6 postflight records, "
            f"found {len(records)}"
        ),
    )

    index = index_by(
        records,
        "record_id",
    )

    require(
        index[
            "POSTFLIGHT_URINE_VENT_INVESTIGATION"
        ][
            "open_issue"
        ]
        is True,
        (
            "urine vent investigation "
            "incorrectly marked closed"
        ),
    )

    require(
        index[
            "POSTFLIGHT_MISSION_FAULT_MANAGEMENT_ANALYSIS"
        ][
            "open_issue"
        ]
        is True,
        (
            "Mission/Fault Management analysis "
            "incorrectly marked closed"
        ),
    )

    require(
        index[
            "POSTFLIGHT_LUNAR_SCIENCE_RELEASE"
        ][
            "date"
        ]
        == "2026-10-07",
        "postflight lunar-science date mismatch",
    )


def validate_unified_records(
    reference: dict,
):
    records = reference[
        "unified_records"
    ]

    require(
        len(
            records
        )
        == EXPECTED_COUNTS[
            "unified_records"
        ],
        (
            "expected 146 unified records, "
            f"found {len(records)}"
        ),
    )

    expected_total = (
        len(
            reference[
                "event_registry"
            ]
        )
        + len(
            reference[
                "decision_thread_registry"
            ]
        )
        + len(
            reference[
                "postflight_registry"
            ]
        )
        + len(
            reference[
                "source_registry"
            ]
        )
        + len(
            reference[
                "dataset_registry"
            ]
        )
    )

    require(
        len(
            records
        )
        == expected_total,
        (
            "unified-record count does not equal "
            "sum of component registries"
        ),
    )

    record_types = {
        item[
            "record_type"
        ]
        for item
        in records
    }

    require(
        record_types
        == EXPECTED_RECORD_TYPES,
        "unified record-type registry mismatch",
    )

    for item in records:
        require(
            bool(
                item[
                    "record_id"
                ]
            ),
            "unified record missing record_id",
        )

        require(
            bool(
                item[
                    "title"
                ]
            ),
            (
                "unified record missing title: "
                f"{item['record_id']}"
            ),
        )

        require(
            isinstance(
                item[
                    "search_tokens"
                ],
                list,
            ),
            (
                "search_tokens not a list: "
                f"{item['record_id']}"
            ),
        )

        require(
            item[
                "search_tokens"
            ]
            == sorted(
                set(
                    item[
                        "search_tokens"
                    ]
                )
            ),
            (
                "search_tokens not normalized/sorted: "
                f"{item['record_id']}"
            ),
        )

        citation_value = item[
            "citation"
        ]

        require(
            bool(
                citation_value[
                    "path"
                ]
            ),
            (
                "unified record citation missing path: "
                f"{item['record_id']}"
            ),
        )

        require(
            bool(
                citation_value[
                    "locator"
                ]
            ),
            (
                "unified record citation missing locator: "
                f"{item['record_id']}"
            ),
        )

        require(
            citation_value[
                "citation_text"
            ]
            == (
                citation_value[
                    "path"
                ]
                + " :: "
                + citation_value[
                    "locator"
                ]
            ),
            (
                "citation text mismatch: "
                f"{item['record_id']}"
            ),
        )


def validate_tool_registry(
    reference: dict,
):
    tools = reference[
        "tool_registry"
    ]

    require(
        len(
            tools
        )
        == EXPECTED_COUNTS[
            "tools"
        ],
        (
            "expected 8 analyst tools, "
            f"found {len(tools)}"
        ),
    )

    ids = [
        item[
            "tool_id"
        ]
        for item
        in tools
    ]

    require(
        ids
        == EXPECTED_TOOLS,
        "analyst tool registry mismatch",
    )

    for item in tools:
        require(
            item[
                "deterministic"
            ]
            is True,
            (
                "tool not deterministic: "
                f"{item['tool_id']}"
            ),
        )

        require(
            item[
                "network_required"
            ]
            is False,
            (
                "tool unexpectedly requires network: "
                f"{item['tool_id']}"
            ),
        )


def validate_retrieval_policy(
    reference: dict,
):
    policy = reference[
        "retrieval_policy"
    ]

    expected_true = [
        "structured_local_artifacts_first",
        "exact_id_lookup_supported",
        "keyword_search_supported",
        "record_type_filter_supported",
        "citations_returned_with_records",
        "source_urls_preserved_when_available",
    ]

    expected_false = [
        "missing_fact_may_be_invented",
        (
            "missionlab_derived_may_be_"
            "labeled_nasa_reported"
        ),
        (
            "unknown_timing_may_be_"
            "given_exact_utc"
        ),
    ]

    for key in expected_true:
        require(
            policy[
                key
            ]
            is True,
            (
                "retrieval policy expected TRUE: "
                f"{key}"
            ),
        )

    for key in expected_false:
        require(
            policy[
                key
            ]
            is False,
            (
                "retrieval policy expected FALSE: "
                f"{key}"
            ),
        )


def validate_calculation_policy(
    reference: dict,
):
    policy = reference[
        "calculation_policy"
    ]

    require(
        policy[
            "utc_met_conversion_uses_mission_json"
        ]
        is True,
        "UTC/MET conversion source policy mismatch",
    )

    require(
        policy[
            "elapsed_time_is_deterministic"
        ]
        is True,
        "elapsed-time determinism policy mismatch",
    )

    require(
        policy[
            "network_required"
        ]
        is False,
        (
            "Phase 8A calculation layer "
            "unexpectedly requires network access"
        ),
    )

    require(
        policy[
            "paid_model_required"
        ]
        is False,
        (
            "Phase 8A incorrectly requires "
            "a paid model"
        ),
    )

    require(
        policy[
            "llm_required"
        ]
        is False,
        (
            "Phase 8A incorrectly requires "
            "an LLM"
        ),
    )


def validate_roadmap_state(
    reference: dict,
):
    roadmap = reference[
        "phase8_roadmap_assessment"
    ]

    require(
        roadmap[
            "structured_retrieval_over_events_data_sources"
        ]
        == "COMPLETE_PHASE8A",
        "structured retrieval roadmap item incomplete",
    )

    require(
        roadmap[
            "deterministic_calculations_exposed_as_tools"
        ]
        == "COMPLETE_PHASE8A",
        (
            "deterministic tools roadmap "
            "item incomplete"
        ),
    )

    require(
        roadmap[
            "citation_first_answers"
        ]
        == "PENDING_PHASE8B",
        (
            "citation-first answers incorrectly "
            "marked complete in 8A"
        ),
    )

    require(
        roadmap[
            "optional_local_browser_llm"
        ]
        == "PENDING_PHASE8B",
        (
            "optional local/browser LLM incorrectly "
            "marked complete in 8A"
        ),
    )

    require(
        roadmap[
            "no_paid_model_dependency"
        ]
        == "SATISFIED_PHASE8A",
        (
            "no-paid-model dependency "
            "roadmap state mismatch"
        ),
    )


def validate_outputs(
    reference: dict,
):
    outputs = reference[
        "outputs"
    ]

    require(
        outputs[
            "reference_json"
        ]
        == (
            "data/reference/"
            "artemis_ii_mission_analyst_index.json"
        ),
        "reference output path mismatch",
    )

    require(
        outputs[
            "processed_json"
        ]
        == (
            "data/processed/analyst/"
            "artemis_ii_mission_analyst_index.json"
        ),
        "processed output path mismatch",
    )


def validate_exact_lookup_functions(
    analyst,
    reference: dict,
):
    event = analyst.exact_lookup(
        reference,
        "event_registry",
        "event_id",
        "A2_RTC2",
    )

    require(
        event[
            "timestamp_utc"
        ]
        == "2026-04-10T02:53:00Z",
        "event_lookup RTC2 timestamp mismatch",
    )

    require(
        event[
            "citation"
        ][
            "locator"
        ]
        == (
            "shared_timeline"
            "[event_id=A2_RTC2]"
        ),
        "event_lookup citation mismatch",
    )

    thread = analyst.exact_lookup(
        reference,
        "decision_thread_registry",
        "thread_id",
        "RETURN_LINK_ANOMALY_RTC2",
    )

    require(
        thread[
            "anomaly"
        ]
        is True,
        "decision_thread_lookup RTC2 state mismatch",
    )

    dataset = analyst.exact_lookup(
        reference,
        "dataset_registry",
        "dataset_id",
        (
            "phase7b_artemis_ii_"
            "mission_control_decision_threads"
        ),
    )

    require(
        dataset[
            "path"
        ]
        == (
            "data/reference/"
            "artemis_ii_decision_threads.json"
        ),
        "dataset_lookup Phase 7B path mismatch",
    )

    source = analyst.exact_lookup(
        reference,
        "source_registry",
        "source_id",
        (
            "NASA_INITIAL_POSTFLIGHT_"
            "ASSESSMENT_2026_04_20"
        ),
    )

    require(
        source.get(
            "url"
        )
        == (
            "https://www.nasa.gov/missions/"
            "nasa-on-track-for-future-missions-"
            "with-initial-artemis-ii-assessments/"
        ),
        "source_lookup NASA postflight URL mismatch",
    )


def validate_search_function(
    analyst,
    reference: dict,
):
    results = analyst.search_index(
        reference,
        "return link RTC2",
        None,
        10,
    )

    ids = [
        item[
            "record_id"
        ]
        for item
        in results
    ]

    require(
        "RETURN_LINK_ANOMALY_RTC2"
        in ids,
        (
            "general search did not retrieve "
            "RETURN_LINK_ANOMALY_RTC2"
        ),
    )

    require(
        "A2_RTC2"
        in ids,
        (
            "general search did not retrieve "
            "A2_RTC2"
        ),
    )

    for item in results:
        require(
            bool(
                item[
                    "citation"
                ][
                    "citation_text"
                ]
            ),
            (
                "search result missing citation: "
                f"{item['record_id']}"
            ),
        )

    event_results = analyst.search_index(
        reference,
        "entry interface",
        "event",
        10,
    )

    require(
        len(
            event_results
        )
        >= 1,
        "event-filtered search returned no results",
    )

    require(
        all(
            item[
                "record_type"
            ]
            == "event"
            for item
            in event_results
        ),
        (
            "record-type filter leaked "
            "non-event results"
        ),
    )

    require(
        any(
            item[
                "record_id"
            ]
            == "A2_ENTRY_INTERFACE"
            for item
            in event_results
        ),
        (
            "event-filtered search did not retrieve "
            "A2_ENTRY_INTERFACE"
        ),
    )


def validate_time_tools(
    analyst,
    reference: dict,
):
    launch = analyst.parse_utc(
        reference[
            "mission_clock"
        ][
            "launch_epoch_utc"
        ]
    )

    otc3 = analyst.utc_to_met(
        "2026-04-06T03:03:00Z",
        launch,
    )

    require(
        otc3[
            "met"
        ]
        == "04:04:27:48",
        (
            "UTC -> MET calculation mismatch "
            "for OTC3"
        ),
    )

    require(
        otc3[
            "elapsed_seconds"
        ]
        == 361668.0,
        (
            "OTC3 elapsed-seconds "
            "calculation mismatch"
        ),
    )

    otc3_reverse = analyst.met_to_utc(
        "04:04:27:48",
        launch,
    )

    require(
        otc3_reverse[
            "utc"
        ]
        == "2026-04-06T03:03:00Z",
        (
            "MET -> UTC round-trip mismatch "
            "for OTC3"
        ),
    )

    earthset_to_earthrise = (
        analyst.elapsed_time(
            "2026-04-06T22:41:00Z",
            "2026-04-06T23:22:00Z",
        )
    )

    require(
        earthset_to_earthrise[
            "elapsed_seconds"
        ]
        == 2460.0,
        (
            "Earthset -> Earthrise "
            "elapsed seconds mismatch"
        ),
    )

    require(
        earthset_to_earthrise[
            "elapsed_minutes"
        ]
        == 41.0,
        (
            "Earthset -> Earthrise "
            "elapsed minutes mismatch"
        ),
    )

    require(
        earthset_to_earthrise[
            "formatted"
        ]
        == "00:00:41:00",
        (
            "Earthset -> Earthrise "
            "formatted duration mismatch"
        ),
    )

    pericynthion = analyst.utc_to_met(
        "2026-04-06T23:00:46.177998Z",
        launch,
    )

    require(
        pericynthion[
            "met"
        ]
        == "05:00:25:34.178",
        "pericynthion MET calculation mismatch",
    )

    require(
        otc3[
            "deterministic"
        ]
        is True,
        "UTC/MET tool not marked deterministic",
    )

    require(
        earthset_to_earthrise[
            "deterministic"
        ]
        is True,
        "elapsed-time tool not marked deterministic",
    )


def validate_zero_cost_runtime():
    content = ANALYST_PATH.read_text(
        encoding="utf-8",
    ).lower()

    prohibited_import_markers = [
        "import openai",
        "from openai",
        "import anthropic",
        "from anthropic",
        "import google.generativeai",
        "from google.generativeai",
    ]

    for marker in prohibited_import_markers:
        require(
            marker
            not in content,
            (
                "Phase 8A analyst has unexpected "
                f"paid-model dependency marker: {marker}"
            ),
        )


def main():
    print()
    print(
        "Phase 8A Artemis II Evidence-Grounded "
        "Mission Analyst Validation"
    )
    print(
        "=" * 72
    )

    reference = load_json(
        REFERENCE_PATH
    )

    processed = load_json(
        PROCESSED_PATH
    )

    mission = load_json(
        MISSION_PATH
    )

    analyst = load_analyst_module()

    validate_identity(
        reference,
        processed,
    )

    print()
    print(
        "Analysis identity: PASS"
    )
    print(
        "Reference / processed index consistency: PASS"
    )

    validate_mission_clock(
        reference,
        mission,
    )

    print()
    print(
        "Mission clock configuration: PASS"
    )
    print(
        "Launch epoch preservation: PASS"
    )

    validate_dependencies(
        reference
    )

    print()
    print(
        "Phase 7A dependency: PASS"
    )
    print(
        "Phase 7B dependency: PASS"
    )

    validate_dataset_registry(
        reference
    )

    print()
    print(
        "25 reference datasets: PASS"
    )
    print(
        "Dataset-ID uniqueness: PASS"
    )
    print(
        "Major Phase 2-7 products indexed: PASS"
    )
    print(
        "Analyst self-index exclusion: PASS"
    )
    print(
        "Dataset citations: PASS"
    )

    validate_source_registry(
        reference
    )

    print()
    print(
        "81 normalized public sources: PASS"
    )
    print(
        "Source-ID uniqueness: PASS"
    )
    print(
        "Public source occurrence tracking: PASS"
    )
    print(
        "Source URL preservation: PASS"
    )

    validate_event_registry(
        reference
    )

    print()
    print(
        "24 shared mission events: PASS"
    )
    print(
        "Event-ID uniqueness: PASS"
    )
    print(
        "Mission-event ordering: PASS"
    )
    print(
        "Reported timing preservation: PASS"
    )
    print(
        "Derived geometry labeling preservation: PASS"
    )
    print(
        "Unknown-time non-inference: PASS"
    )
    print(
        "Approximate-time precision preservation: PASS"
    )
    print(
        "Event citations: PASS"
    )

    validate_thread_registry(
        reference
    )

    print()
    print(
        "10 decision threads: PASS"
    )
    print(
        "Decision-thread ID uniqueness: PASS"
    )
    print(
        "RTC2 anomaly boundary preservation: PASS"
    )
    print(
        "Lunar communications constraint boundary: PASS"
    )
    print(
        "Entry blackout constraint boundary: PASS"
    )
    print(
        "TPS decision maturity preservation: PASS"
    )
    print(
        "Decision-thread citations: PASS"
    )

    validate_postflight_registry(
        reference
    )

    print()
    print(
        "6 postflight records: PASS"
    )
    print(
        "Urine vent investigation remains open: PASS"
    )
    print(
        "Mission/Fault Management analysis remains open: PASS"
    )
    print(
        "October lunar-science record: PASS"
    )

    validate_unified_records(
        reference
    )

    print()
    print(
        "146 unified searchable records: PASS"
    )
    print(
        "Unified record-count arithmetic: PASS"
    )
    print(
        "5 analyst record types: PASS"
    )
    print(
        "Normalized search-token registry: PASS"
    )
    print(
        "Citation payload on every unified record: PASS"
    )

    validate_tool_registry(
        reference
    )

    print()
    print(
        "8 deterministic analyst tools: PASS"
    )
    print(
        "Search tool registry: PASS"
    )
    print(
        "Exact lookup tool registry: PASS"
    )
    print(
        "Mission-time calculation tool registry: PASS"
    )
    print(
        "No network-required analyst tools: PASS"
    )

    validate_retrieval_policy(
        reference
    )

    print()
    print(
        "Structured-local-artifact-first policy: PASS"
    )
    print(
        "Exact-ID retrieval policy: PASS"
    )
    print(
        "Keyword retrieval policy: PASS"
    )
    print(
        "Record-type filtering policy: PASS"
    )
    print(
        "Citation-return policy: PASS"
    )
    print(
        "Unsupported-fact invention prohibition: PASS"
    )
    print(
        "MissionLab/NASA provenance separation: PASS"
    )
    print(
        "Unknown-time exact-UTC prohibition: PASS"
    )

    validate_calculation_policy(
        reference
    )

    print()
    print(
        "Mission-clock deterministic calculation policy: PASS"
    )
    print(
        "Elapsed-time deterministic policy: PASS"
    )
    print(
        "No calculation network dependency: PASS"
    )
    print(
        "No paid-model dependency: PASS"
    )
    print(
        "No LLM dependency: PASS"
    )

    validate_exact_lookup_functions(
        analyst,
        reference,
    )

    print()
    print(
        "event_lookup execution: PASS"
    )
    print(
        "decision_thread_lookup execution: PASS"
    )
    print(
        "dataset_lookup execution: PASS"
    )
    print(
        "source_lookup execution: PASS"
    )

    validate_search_function(
        analyst,
        reference,
    )

    print()
    print(
        "Unified keyword search execution: PASS"
    )
    print(
        "Return-link / RTC2 retrieval: PASS"
    )
    print(
        "Record-type filtered search: PASS"
    )
    print(
        "Search-result citation return: PASS"
    )

    validate_time_tools(
        analyst,
        reference,
    )

    print()
    print(
        "UTC -> MET execution: PASS"
    )
    print(
        "MET -> UTC execution: PASS"
    )
    print(
        "UTC/MET round-trip: PASS"
    )
    print(
        "Elapsed-time execution: PASS"
    )
    print(
        "OTC3 MET = 04:04:27:48: PASS"
    )
    print(
        "Earthset -> Earthrise = 41 minutes: PASS"
    )
    print(
        "Pericynthion MET calculation: PASS"
    )

    validate_zero_cost_runtime()

    print()
    print(
        "No OpenAI SDK dependency: PASS"
    )
    print(
        "No Anthropic SDK dependency: PASS"
    )
    print(
        "No Gemini SDK dependency: PASS"
    )

    validate_roadmap_state(
        reference
    )

    print()
    print(
        "Structured retrieval roadmap item: PASS"
    )
    print(
        "Deterministic-tools roadmap item: PASS"
    )
    print(
        "Citation-first answers correctly left to 8B: PASS"
    )
    print(
        "Optional local/browser LLM correctly left to 8B: PASS"
    )
    print(
        "No-paid-model roadmap requirement: PASS"
    )

    validate_outputs(
        reference
    )

    print()
    print(
        "Output registry: PASS"
    )

    print()
    print(
        "Validated Phase 8A totals:"
    )
    print(
        "  reference datasets: 25"
    )
    print(
        "  normalized public sources: 81"
    )
    print(
        "  shared mission events: 24"
    )
    print(
        "  decision threads: 10"
    )
    print(
        "  postflight records: 6"
    )
    print(
        "  unified searchable records: 146"
    )
    print(
        "  deterministic analyst tools: 8"
    )

    print()
    print(
        "Validated deterministic calculations:"
    )
    print(
        "  OTC3 UTC -> MET: 04:04:27:48"
    )
    print(
        "  MET 04:04:27:48 -> "
        "2026-04-06T03:03:00Z"
    )
    print(
        "  Earthset -> Earthrise: 00:00:41:00"
    )
    print(
        "  pericynthion MET: 05:00:25:34.178"
    )

    print()
    print(
        "Phase 8 status:"
    )
    print(
        "  structured retrieval: COMPLETE 8A"
    )
    print(
        "  deterministic tools: COMPLETE 8A"
    )
    print(
        "  citation-bearing retrieval: COMPLETE 8A"
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
        "PHASE 8A VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
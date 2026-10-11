from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INTERFACE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_mission_analyst_interface.json"
)

PROCESSED_INTERFACE_PATH = (
    ROOT
    / "data"
    / "processed"
    / "analyst"
    / "artemis_ii_mission_analyst_interface.json"
)

SMOKE_PATH = (
    ROOT
    / "data"
    / "processed"
    / "analyst"
    / "phase8b_smoke_answers.json"
)

INDEX_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_mission_analyst_index.json"
)

PHASE7A_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_mission_control_perspectives.json"
)

PHASE7B_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_decision_threads.json"
)

ANSWER_MODULE_PATH = (
    ROOT
    / "scripts"
    / "analyst"
    / "answer_mission_question.py"
)


EXPECTED_INTERFACE_DATASET = (
    "phase8b_artemis_ii_"
    "mission_analyst_interface"
)

EXPECTED_INDEX_DATASET = (
    "phase8a_artemis_ii_"
    "mission_analyst_index"
)

EXPECTED_PHASE7A_DATASET = (
    "phase7a_artemis_ii_"
    "mission_control_perspectives"
)

EXPECTED_PHASE7B_DATASET = (
    "phase7b_artemis_ii_"
    "mission_control_decision_threads"
)

EXPECTED_ROUTES = [
    "EVENT_TIME",
    "EVENT",
    "DECISION_THREAD",
    "DECISION_THREAD_CAUSATION",
    "DISCIPLINE",
    "DETERMINISTIC_ELAPSED_TIME",
    "KNOWN_UNKNOWN",
    "SEARCH_SYNTHESIS",
]

EXPECTED_NON_EQUIVALENCES = [
    (
        "LLM_PRESENTATION"
        " != EVIDENCE_AUTHORITY"
    ),
    (
        "RETRIEVAL_MATCH"
        " != FACT_NOT_SUPPORTED_BY_RECORD"
    ),
    (
        "MISSIONLAB_DERIVED"
        " != NASA_REPORTED"
    ),
    (
        "TEMPORAL_SEQUENCE"
        " != CAUSATION"
    ),
    (
        "HYPOTHESIS"
        " != CONFIRMED_ROOT_CAUSE"
    ),
    (
        "UNKNOWN_PUBLIC_FACT"
        " != PERMISSION_TO_INVENT"
    ),
    (
        "DISCIPLINE_RELEVANCE"
        " != DECISION_AUTHORITY"
    ),
    (
        "OPTIONAL_LLM_HANDOFF"
        " != REQUIRED_MODEL_DEPENDENCY"
    ),
]


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 8B VALIDATION FAILED: "
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


def load_answer_module():
    require(
        ANSWER_MODULE_PATH.exists(),
        (
            "missing Phase 8B answer module: "
            f"{ANSWER_MODULE_PATH}"
        ),
    )

    spec = importlib.util.spec_from_file_location(
        "phase8b_answer_mission_question",
        ANSWER_MODULE_PATH,
    )

    require(
        spec is not None,
        "could not create Phase 8B module spec",
    )

    require(
        spec.loader is not None,
        "Phase 8B module has no loader",
    )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def validate_identity(
    reference: dict,
    processed: dict,
):
    require(
        reference
        == processed,
        (
            "reference and processed "
            "Phase 8B interface manifests differ"
        ),
    )

    require(
        reference.get(
            "dataset_id"
        )
        == EXPECTED_INTERFACE_DATASET,
        "Phase 8B dataset identity mismatch",
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
        == "8B",
        "phase identity mismatch",
    )

    require(
        reference.get(
            "status"
        )
        == (
            "CITATION_FIRST_"
            "MISSION_ANALYST_COMPLETE"
        ),
        "Phase 8B status mismatch",
    )


def validate_dependencies(
    reference: dict,
):
    dependencies = reference[
        "dependencies"
    ]

    require(
        len(
            dependencies
        )
        == 3,
        (
            "expected 3 Phase 8B dependencies, "
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
            EXPECTED_INDEX_DATASET,
            EXPECTED_PHASE7A_DATASET,
            EXPECTED_PHASE7B_DATASET,
        ],
        "Phase 8B dependency registry mismatch",
    )

    require(
        dependencies[
            0
        ][
            "path"
        ]
        == (
            "data/reference/"
            "artemis_ii_mission_analyst_index.json"
        ),
        "Phase 8A dependency path mismatch",
    )

    require(
        dependencies[
            1
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
            2
        ][
            "path"
        ]
        == (
            "data/reference/"
            "artemis_ii_decision_threads.json"
        ),
        "Phase 7B dependency path mismatch",
    )


def validate_router(
    reference: dict,
):
    router = reference[
        "question_router"
    ]

    require(
        router[
            "routes"
        ]
        == EXPECTED_ROUTES,
        "question-router registry mismatch",
    )

    require(
        router[
            "deterministic"
        ]
        is True,
        "question router not deterministic",
    )

    require(
        router[
            "llm_used_for_routing"
        ]
        is False,
        "question router incorrectly uses an LLM",
    )


def validate_answer_contract(
    reference: dict,
):
    contract = reference[
        "answer_contract"
    ]

    expected_true = [
        "citation_first",
        "claim_level_citations_required",
        "known_unknown_state_supported",
        "provenance_labels_required",
        "deterministic_tools_may_be_used",
    ]

    expected_false = [
        "unsupported_fact_invention_allowed",
        "llm_required",
        "paid_model_required",
    ]

    for key in expected_true:
        require(
            contract[
                key
            ]
            is True,
            (
                "answer contract expected TRUE: "
                f"{key}"
            ),
        )

    for key in expected_false:
        require(
            contract[
                key
            ]
            is False,
            (
                "answer contract expected FALSE: "
                f"{key}"
            ),
        )


def validate_llm_adapters(
    reference: dict,
):
    adapters = reference[
        "optional_llm_adapters"
    ]

    require(
        len(
            adapters
        )
        == 2,
        (
            "expected 2 optional LLM adapters, "
            f"found {len(adapters)}"
        ),
    )

    require(
        [
            item[
                "target"
            ]
            for item
            in adapters
        ]
        == [
            "local",
            "browser",
        ],
        "LLM adapter targets mismatch",
    )

    require(
        [
            item[
                "adapter_id"
            ]
            for item
            in adapters
        ]
        == [
            "LOCAL_LLM_PROMPT_HANDOFF",
            "BROWSER_LLM_PROMPT_HANDOFF",
        ],
        "LLM adapter IDs mismatch",
    )

    for item in adapters:
        require(
            item[
                "optional"
            ]
            is True,
            (
                "LLM adapter not optional: "
                f"{item['adapter_id']}"
            ),
        )

        require(
            item[
                "execution_embedded"
            ]
            is False,
            (
                "LLM execution incorrectly embedded: "
                f"{item['adapter_id']}"
            ),
        )

        require(
            item[
                "api_key_required"
            ]
            is False,
            (
                "LLM adapter incorrectly requires API key: "
                f"{item['adapter_id']}"
            ),
        )

        require(
            item[
                "paid_model_required"
            ]
            is False,
            (
                "LLM adapter incorrectly requires "
                f"paid model: {item['adapter_id']}"
            ),
        )


def validate_authority_model(
    reference: dict,
):
    model = reference[
        "authority_model"
    ]

    expected_true = [
        "deterministic_retrieval_is_authoritative",
        "deterministic_calculations_are_authoritative",
        "llm_may_rewrite_locked_claims",
    ]

    expected_false = [
        "llm_may_add_new_facts",
        "llm_may_override_evidence_boundaries",
        "llm_may_change_provenance",
        "llm_may_invent_citations",
    ]

    for key in expected_true:
        require(
            model[
                key
            ]
            is True,
            (
                "authority model expected TRUE: "
                f"{key}"
            ),
        )

    for key in expected_false:
        require(
            model[
                key
            ]
            is False,
            (
                "authority model expected FALSE: "
                f"{key}"
            ),
        )


def validate_known_unknown_policy(
    reference: dict,
):
    policy = reference[
        "known_unknown_policy"
    ]

    require(
        policy[
            "unknowns_are_answerable"
        ]
        is True,
        "unknown-state answering disabled",
    )

    require(
        policy[
            "unknown_answer_must_state_boundary"
        ]
        is True,
        "unknown answers do not require boundary statement",
    )

    require(
        policy[
            "hypothesis_may_be_promoted_to_fact"
        ]
        is False,
        "hypothesis promotion incorrectly allowed",
    )

    require(
        policy[
            "open_investigation_may_be_forced_closed"
        ]
        is False,
        "open investigation closure incorrectly allowed",
    )

    require(
        policy[
            "missing_exact_time_may_be_invented"
        ]
        is False,
        "missing exact time invention incorrectly allowed",
    )


def validate_non_equivalences(
    reference: dict,
):
    values = reference[
        "critical_non_equivalences"
    ]

    require(
        values
        == EXPECTED_NON_EQUIVALENCES,
        (
            "Phase 8B critical non-equivalence "
            "registry mismatch"
        ),
    )


def validate_roadmap(
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
        "structured retrieval roadmap state mismatch",
    )

    require(
        roadmap[
            "deterministic_calculations_exposed_as_tools"
        ]
        == "COMPLETE_PHASE8A",
        "deterministic tools roadmap state mismatch",
    )

    require(
        roadmap[
            "citation_first_answers"
        ]
        == "COMPLETE_PHASE8B",
        "citation-first answer roadmap item incomplete",
    )

    require(
        roadmap[
            "optional_local_browser_llm"
        ]
        == (
            "COMPLETE_AS_OPTIONAL_"
            "HANDOFF_PHASE8B"
        ),
        "optional LLM roadmap item incomplete",
    )

    require(
        roadmap[
            "no_paid_model_dependency"
        ]
        == "COMPLETE",
        "no-paid-model roadmap item incomplete",
    )

    require(
        roadmap[
            "phase8_overall"
        ]
        == (
            "COMPLETE_RELATIVE_TO_"
            "VALIDATED_MISSIONLAB_EVIDENCE"
        ),
        "Phase 8 overall status mismatch",
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
            "artemis_ii_mission_analyst_interface.json"
        ),
        "reference output path mismatch",
    )

    require(
        outputs[
            "processed_json"
        ]
        == (
            "data/processed/analyst/"
            "artemis_ii_mission_analyst_interface.json"
        ),
        "processed interface output path mismatch",
    )

    require(
        outputs[
            "smoke_answers_json"
        ]
        == (
            "data/processed/analyst/"
            "phase8b_smoke_answers.json"
        ),
        "smoke-answer output path mismatch",
    )


def validate_answer_object(
    answer_module,
    answer: dict,
):
    answer_module.validate_answer_contract(
        answer
    )

    require(
        answer[
            "citation_first"
        ]
        is True,
        "answer not marked citation-first",
    )

    require(
        answer[
            "unsupported_fact_invention"
        ]
        is False,
        "answer permits unsupported facts",
    )

    require(
        answer[
            "llm_required"
        ]
        is False,
        "answer incorrectly requires LLM",
    )

    require(
        answer[
            "paid_model_required"
        ]
        is False,
        "answer incorrectly requires paid model",
    )

    require(
        len(
            answer[
                "claims"
            ]
        )
        >= 1,
        "answer has no claims",
    )

    require(
        len(
            answer[
                "citations"
            ]
        )
        >= 1,
        "answer has no citations",
    )

    citation_ids = {
        citation[
            "citation_id"
        ]
        for citation
        in answer[
            "citations"
        ]
    }

    for claim in answer[
        "claims"
    ]:
        require(
            bool(
                claim[
                    "provenance"
                ]
            ),
            "claim missing provenance",
        )

        require(
            len(
                claim[
                    "citation_ids"
                ]
            )
            >= 1,
            "claim missing citation IDs",
        )

        for citation_id in claim[
            "citation_ids"
        ]:
            require(
                citation_id
                in citation_ids,
                (
                    "claim references unknown citation "
                    f"{citation_id}"
                ),
            )

            require(
                f"[{citation_id}]"
                in answer[
                    "answer_text"
                ],
                (
                    "answer text missing citation token "
                    f"{citation_id}"
                ),
            )


def validate_runtime_answers(
    answer_module,
    index: dict,
    phase7a: dict,
):
    rtc2 = answer_module.answer_question(
        "When was RTC2?",
        index,
        phase7a,
    )

    validate_answer_object(
        answer_module,
        rtc2,
    )

    require(
        rtc2[
            "route"
        ]
        == "EVENT_TIME",
        "RTC2 route mismatch",
    )

    require(
        rtc2[
            "answer_status"
        ]
        == "SUPPORTED",
        "RTC2 answer status mismatch",
    )

    require(
        "2026-04-10T02:53:00Z"
        in rtc2[
            "answer_text"
        ],
        "RTC2 answer missing expected UTC",
    )

    require(
        any(
            citation[
                "locator"
            ]
            == (
                "shared_timeline"
                "[event_id=A2_RTC2]"
            )
            for citation
            in rtc2[
                "citations"
            ]
        ),
        "RTC2 answer missing event citation",
    )

    causation = answer_module.answer_question(
        "Did the return link loss cause RTC2?",
        index,
        phase7a,
    )

    validate_answer_object(
        answer_module,
        causation,
    )

    require(
        causation[
            "route"
        ]
        == "DECISION_THREAD_CAUSATION",
        "RTC2 causation route mismatch",
    )

    require(
        causation[
            "answer_status"
        ]
        == (
            "SUPPORTED_WITH_CAUSATION_BOUNDARY"
        ),
        "RTC2 causation status mismatch",
    )

    require(
        "does not establish"
        in causation[
            "answer_text"
        ],
        "RTC2 causation answer missing evidence boundary",
    )

    require(
        "TEMPORAL_SEQUENCE != CAUSATION"
        in causation[
            "answer_text"
        ],
        "RTC2 causation guardrail missing",
    )

    vent = answer_module.answer_question(
        (
            "What was the root cause of the "
            "urine vent-line issue?"
        ),
        index,
        phase7a,
    )

    validate_answer_object(
        answer_module,
        vent,
    )

    require(
        vent[
            "route"
        ]
        == "KNOWN_UNKNOWN",
        "vent-line root cause route mismatch",
    )

    require(
        vent[
            "answer_status"
        ]
        == (
            "UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE"
        ),
        (
            "vent-line root cause incorrectly "
            "treated as known"
        ),
    )

    require(
        "not established"
        in vent[
            "answer_text"
        ],
        "vent-line answer missing unknown-state statement",
    )

    require(
        "POSSIBLE_ICE != CONFIRMED_ICE"
        in vent[
            "answer_text"
        ],
        "vent-line answer missing ice guardrail",
    )

    elapsed = answer_module.answer_question(
        (
            "How long was it between Earthset "
            "and Earthrise?"
        ),
        index,
        phase7a,
    )

    validate_answer_object(
        answer_module,
        elapsed,
    )

    require(
        elapsed[
            "route"
        ]
        == "DETERMINISTIC_ELAPSED_TIME",
        "Earthset/Earthrise route mismatch",
    )

    require(
        len(
            elapsed[
                "deterministic_tools"
            ]
        )
        == 1,
        (
            "Earthset/Earthrise answer expected "
            "one deterministic tool result"
        ),
    )

    tool_result = elapsed[
        "deterministic_tools"
    ][0]

    require(
        tool_result[
            "tool"
        ]
        == "elapsed_time",
        "elapsed-time tool identity mismatch",
    )

    require(
        tool_result[
            "elapsed_minutes"
        ]
        == 41.0,
        "Earthset/Earthrise elapsed time mismatch",
    )

    require(
        tool_result[
            "deterministic"
        ]
        is True,
        "elapsed-time result not deterministic",
    )

    require(
        (
            "not the same thing as the duration "
            "of full Earth occultation"
        )
        in elapsed[
            "answer_text"
        ],
        (
            "Earthset/Earthrise answer missing "
            "occultation boundary"
        ),
    )

    science = answer_module.answer_question(
        (
            "What does the SCIENCE perspective "
            "focus on?"
        ),
        index,
        phase7a,
    )

    validate_answer_object(
        answer_module,
        science,
    )

    require(
        science[
            "route"
        ]
        == "DISCIPLINE",
        "SCIENCE discipline route mismatch",
    )

    require(
        "SCIENCE"
        in science[
            "answer_text"
        ],
        "SCIENCE answer missing discipline name",
    )

    require(
        "lunar targeting"
        in science[
            "answer_text"
        ].lower(),
        "SCIENCE answer missing lunar targeting",
    )

    tps = answer_module.answer_question(
        (
            "What happened with the Artemis II "
            "heat shield?"
        ),
        index,
        phase7a,
    )

    validate_answer_object(
        answer_module,
        tps,
    )

    require(
        tps[
            "route"
        ]
        == "DECISION_THREAD",
        "TPS route mismatch",
    )

    require(
        (
            "Artemis I heat-shield finding "
            "to Artemis II mitigation"
        )
        in tps[
            "answer_text"
        ],
        "TPS answer missing decision-thread classification",
    )

    entry = answer_module.answer_question(
        "What happened at Entry Interface?",
        index,
        phase7a,
    )

    validate_answer_object(
        answer_module,
        entry,
    )

    require(
        entry[
            "route"
        ]
        == "EVENT",
        "Entry Interface event route mismatch",
    )

    require(
        "A2_ENTRY_INTERFACE"
        not in entry[
            "answer_text"
        ],
        (
            "Entry Interface answer should be "
            "human-readable rather than raw ID only"
        ),
    )

    unknown_search = answer_module.answer_question(
        (
            "What color was the commander's "
            "private checklist cover?"
        ),
        index,
        phase7a,
    )

    validate_answer_object(
        answer_module,
        unknown_search,
    )

    require(
        unknown_search[
            "route"
        ]
        == "SEARCH_SYNTHESIS",
        "unsupported-query route mismatch",
    )

    require(
        unknown_search[
            "answer_status"
        ]
        in {
            "INSUFFICIENT_INDEXED_EVIDENCE",
            "SUPPORTED",
        },
        "unsupported-query answer status invalid",
    )

    if (
        unknown_search[
            "answer_status"
        ]
        == "INSUFFICIENT_INDEXED_EVIDENCE"
    ):
        require(
            (
                "No indexed MissionLab evidence"
                in unknown_search[
                    "answer_text"
                ]
            ),
            (
                "insufficient-evidence response "
                "missing explicit boundary"
            ),
        )


def validate_smoke_file(
    answer_module,
    smoke: dict,
):
    answers = smoke[
        "answers"
    ]

    require(
        len(
            answers
        )
        == 6,
        (
            "expected 6 Phase 8B smoke answers, "
            f"found {len(answers)}"
        ),
    )

    expected_routes = [
        "EVENT_TIME",
        "DECISION_THREAD_CAUSATION",
        "KNOWN_UNKNOWN",
        "DETERMINISTIC_ELAPSED_TIME",
        "DISCIPLINE",
        "DECISION_THREAD",
    ]

    require(
        [
            answer[
                "route"
            ]
            for answer
            in answers
        ]
        == expected_routes,
        "smoke-answer route sequence mismatch",
    )

    for answer in answers:
        validate_answer_object(
            answer_module,
            answer,
        )

    require(
        answers[
            0
        ][
            "answer_status"
        ]
        == "SUPPORTED",
        "RTC2 smoke answer status mismatch",
    )

    require(
        answers[
            1
        ][
            "answer_status"
        ]
        == (
            "SUPPORTED_WITH_CAUSATION_BOUNDARY"
        ),
        "causation smoke answer status mismatch",
    )

    require(
        answers[
            2
        ][
            "answer_status"
        ]
        == (
            "UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE"
        ),
        "known/unknown smoke answer status mismatch",
    )

    local_handoff = smoke[
        "local_llm_handoff"
    ]

    browser_handoff = smoke[
        "browser_llm_handoff"
    ]

    require(
        local_handoff[
            "target"
        ]
        == "local",
        "local handoff target mismatch",
    )

    require(
        browser_handoff[
            "target"
        ]
        == "browser",
        "browser handoff target mismatch",
    )

    for handoff in [
        local_handoff,
        browser_handoff,
    ]:
        require(
            handoff[
                "optional"
            ]
            is True,
            "LLM handoff not optional",
        )

        require(
            handoff[
                "execution_performed"
            ]
            is False,
            "LLM execution incorrectly performed",
        )

        require(
            handoff[
                "network_call_performed"
            ]
            is False,
            "LLM handoff incorrectly performed network call",
        )

        require(
            handoff[
                "paid_model_required"
            ]
            is False,
            "LLM handoff incorrectly requires paid model",
        )

        require(
            handoff[
                "api_key_required"
            ]
            is False,
            "LLM handoff incorrectly requires API key",
        )

        require(
            handoff[
                "authoritative_layer"
            ]
            == (
                "DETERMINISTIC_"
                "MISSIONLAB_EVIDENCE"
            ),
            "LLM handoff authority model mismatch",
        )

        require(
            len(
                handoff[
                    "locked_claims"
                ]
            )
            >= 1,
            "LLM handoff has no locked claims",
        )

        require(
            len(
                handoff[
                    "citations"
                ]
            )
            >= 1,
            "LLM handoff has no citations",
        )

        require(
            (
                "Use ONLY the locked claims "
                "and citations"
            )
            in handoff[
                "prompt"
            ],
            "LLM handoff prompt missing locked-claim rule",
        )

        require(
            (
                "Do not add facts"
            )
            in handoff[
                "prompt"
            ],
            "LLM handoff prompt missing no-new-facts rule",
        )


def validate_direct_handoff_execution(
    answer_module,
    index: dict,
    phase7a: dict,
):
    answer = answer_module.answer_question(
        (
            "What happened with the Artemis II "
            "heat shield?"
        ),
        index,
        phase7a,
    )

    local = answer_module.build_llm_handoff(
        answer,
        "local",
    )

    browser = answer_module.build_llm_handoff(
        answer,
        "browser",
    )

    for handoff in [
        local,
        browser,
    ]:
        require(
            handoff[
                "execution_performed"
            ]
            is False,
            "optional LLM handoff executed model",
        )

        require(
            handoff[
                "network_call_performed"
            ]
            is False,
            "optional LLM handoff used network",
        )

        require(
            handoff[
                "paid_model_required"
            ]
            is False,
            "optional LLM handoff requires paid model",
        )

        require(
            (
                "Every factual sentence requires "
                "supplied citations."
            )
            in handoff[
                "rules"
            ],
            (
                "optional LLM handoff missing "
                "citation rule"
            ),
        )

        require(
            (
                "Do not convert temporal order "
                "into causation."
            )
            in handoff[
                "rules"
            ],
            (
                "optional LLM handoff missing "
                "causation guardrail"
            ),
        )


def validate_zero_cost_runtime():
    text = ANSWER_MODULE_PATH.read_text(
        encoding="utf-8",
    ).lower()

    prohibited = [
        "import openai",
        "from openai",
        "import anthropic",
        "from anthropic",
        "import google.generativeai",
        "from google.generativeai",
        "requests.post(",
        "httpx.post(",
    ]

    for marker in prohibited:
        require(
            marker
            not in text,
            (
                "Phase 8B contains unexpected "
                f"model/network dependency marker: {marker}"
            ),
        )


def main():
    print()
    print(
        "Phase 8B Artemis II Citation-First "
        "Mission Analyst Validation"
    )
    print(
        "=" * 72
    )

    reference = load_json(
        INTERFACE_PATH
    )

    processed = load_json(
        PROCESSED_INTERFACE_PATH
    )

    smoke = load_json(
        SMOKE_PATH
    )

    index = load_json(
        INDEX_PATH
    )

    phase7a = load_json(
        PHASE7A_PATH
    )

    phase7b = load_json(
        PHASE7B_PATH
    )

    answer_module = load_answer_module()

    validate_identity(
        reference,
        processed,
    )

    print()
    print(
        "Analysis identity: PASS"
    )
    print(
        "Reference / processed interface consistency: PASS"
    )

    require(
        index[
            "dataset_id"
        ]
        == EXPECTED_INDEX_DATASET,
        "Phase 8A index identity mismatch",
    )

    require(
        phase7a[
            "dataset_id"
        ]
        == EXPECTED_PHASE7A_DATASET,
        "Phase 7A identity mismatch",
    )

    require(
        phase7b[
            "dataset_id"
        ]
        == EXPECTED_PHASE7B_DATASET,
        "Phase 7B identity mismatch",
    )

    validate_dependencies(
        reference
    )

    print()
    print(
        "Phase 8A dependency: PASS"
    )
    print(
        "Phase 7A dependency: PASS"
    )
    print(
        "Phase 7B dependency: PASS"
    )

    validate_router(
        reference
    )

    print()
    print(
        "8-route deterministic question router: PASS"
    )
    print(
        "EVENT_TIME route: PASS"
    )
    print(
        "EVENT route: PASS"
    )
    print(
        "DECISION_THREAD route: PASS"
    )
    print(
        "DECISION_THREAD_CAUSATION route: PASS"
    )
    print(
        "DISCIPLINE route: PASS"
    )
    print(
        "DETERMINISTIC_ELAPSED_TIME route: PASS"
    )
    print(
        "KNOWN_UNKNOWN route: PASS"
    )
    print(
        "SEARCH_SYNTHESIS route: PASS"
    )
    print(
        "LLM-free routing: PASS"
    )

    validate_answer_contract(
        reference
    )

    print()
    print(
        "Citation-first answer contract: PASS"
    )
    print(
        "Claim-level citation requirement: PASS"
    )
    print(
        "Provenance-label requirement: PASS"
    )
    print(
        "Known/unknown answer support: PASS"
    )
    print(
        "Unsupported-fact invention prohibition: PASS"
    )
    print(
        "No LLM requirement: PASS"
    )
    print(
        "No paid-model requirement: PASS"
    )

    validate_authority_model(
        reference
    )

    print()
    print(
        "Deterministic retrieval authority: PASS"
    )
    print(
        "Deterministic calculation authority: PASS"
    )
    print(
        "LLM new-fact prohibition: PASS"
    )
    print(
        "LLM provenance-change prohibition: PASS"
    )
    print(
        "LLM citation-invention prohibition: PASS"
    )
    print(
        "LLM evidence-boundary override prohibition: PASS"
    )

    validate_known_unknown_policy(
        reference
    )

    print()
    print(
        "Known/unknown policy: PASS"
    )
    print(
        "Unknown boundary requirement: PASS"
    )
    print(
        "Hypothesis / fact separation: PASS"
    )
    print(
        "Open-investigation preservation: PASS"
    )
    print(
        "Missing-time non-inference: PASS"
    )

    validate_llm_adapters(
        reference
    )

    print()
    print(
        "2 optional LLM handoff adapters: PASS"
    )
    print(
        "Local LLM handoff adapter: PASS"
    )
    print(
        "Browser LLM handoff adapter: PASS"
    )
    print(
        "Embedded model execution disabled: PASS"
    )
    print(
        "API-key requirement: NONE"
    )
    print(
        "Paid-model requirement: NONE"
    )

    validate_smoke_file(
        answer_module,
        smoke,
    )

    print()
    print(
        "6 persisted smoke answers: PASS"
    )
    print(
        "Smoke-answer citation integrity: PASS"
    )
    print(
        "RTC2 event-time smoke answer: PASS"
    )
    print(
        "RTC2 causation-boundary smoke answer: PASS"
    )
    print(
        "Vent-line known/unknown smoke answer: PASS"
    )
    print(
        "Earthset/Earthrise calculation smoke answer: PASS"
    )
    print(
        "SCIENCE discipline smoke answer: PASS"
    )
    print(
        "TPS decision-thread smoke answer: PASS"
    )
    print(
        "Persisted local LLM handoff: PASS"
    )
    print(
        "Persisted browser LLM handoff: PASS"
    )

    validate_runtime_answers(
        answer_module,
        index,
        phase7a,
    )

    print()
    print(
        "Runtime EVENT_TIME answer execution: PASS"
    )
    print(
        "Runtime causation answer execution: PASS"
    )
    print(
        "Runtime KNOWN_UNKNOWN answer execution: PASS"
    )
    print(
        "Runtime deterministic elapsed-time answer: PASS"
    )
    print(
        "Runtime discipline answer execution: PASS"
    )
    print(
        "Runtime decision-thread answer execution: PASS"
    )
    print(
        "Runtime event answer execution: PASS"
    )
    print(
        "Runtime search-synthesis fallback: PASS"
    )

    print()
    print(
        "Validated mission facts / boundaries:"
    )
    print(
        "  RTC2 UTC = 2026-04-10T02:53:00Z"
    )
    print(
        "  return-link loss -> RTC2 causation claimed: NO"
    )
    print(
        "  temporal sequence != causation: PRESERVED"
    )
    print(
        "  urine vent-line root cause: UNKNOWN"
    )
    print(
        "  possible ice != confirmed ice: PRESERVED"
    )
    print(
        "  Earthset -> Earthrise reported-image interval: 41 min"
    )
    print(
        "  reported-image interval != full-occultation duration"
    )

    validate_direct_handoff_execution(
        answer_module,
        index,
        phase7a,
    )

    print()
    print(
        "Live local LLM handoff construction: PASS"
    )
    print(
        "Live browser LLM handoff construction: PASS"
    )
    print(
        "Locked-claim handoff: PASS"
    )
    print(
        "Citation-preserving handoff: PASS"
    )
    print(
        "No handoff model execution: PASS"
    )
    print(
        "No handoff network call: PASS"
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
    print(
        "No embedded HTTP model call: PASS"
    )

    validate_non_equivalences(
        reference
    )

    print()
    print(
        "8 critical non-equivalences: PASS"
    )
    print(
        "LLM presentation / evidence authority boundary: PASS"
    )
    print(
        "Retrieval match / unsupported fact boundary: PASS"
    )
    print(
        "MissionLab-derived / NASA-reported boundary: PASS"
    )
    print(
        "Temporal-sequence / causation boundary: PASS"
    )
    print(
        "Hypothesis / root-cause boundary: PASS"
    )
    print(
        "Unknown-public-fact / invention boundary: PASS"
    )
    print(
        "Discipline-relevance / authority boundary: PASS"
    )
    print(
        "Optional-handoff / required-model boundary: PASS"
    )

    validate_roadmap(
        reference
    )

    print()
    print(
        "Structured retrieval roadmap coverage: PASS"
    )
    print(
        "Deterministic tools roadmap coverage: PASS"
    )
    print(
        "Citation-first answers roadmap coverage: PASS"
    )
    print(
        "Optional local/browser LLM roadmap coverage: PASS"
    )
    print(
        "No-paid-model roadmap coverage: PASS"
    )
    print(
        "Phase 8 roadmap coverage: PASS"
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
        "Validated Phase 8 architecture:"
    )
    print(
        "  deterministic retrieval: AUTHORITATIVE"
    )
    print(
        "  deterministic calculations: AUTHORITATIVE"
    )
    print(
        "  citation-first answer composer: COMPLETE"
    )
    print(
        "  known/unknown handling: COMPLETE"
    )
    print(
        "  causation guardrails: COMPLETE"
    )
    print(
        "  discipline-aware answers: COMPLETE"
    )
    print(
        "  optional local LLM handoff: COMPLETE"
    )
    print(
        "  optional browser LLM handoff: COMPLETE"
    )
    print(
        "  embedded LLM execution: NONE"
    )
    print(
        "  paid model dependency: NONE"
    )

    print()
    print(
        "Phase 8 status:"
    )
    print(
        "  structured retrieval: COMPLETE"
    )
    print(
        "  deterministic calculations: COMPLETE"
    )
    print(
        "  citation-first answers: COMPLETE"
    )
    print(
        "  optional local/browser LLM: COMPLETE"
    )
    print(
        "  no paid model dependency: COMPLETE"
    )
    print(
        "  overall: COMPLETE RELATIVE TO "
        "VALIDATED MISSIONLAB EVIDENCE"
    )

    print()
    print(
        "PHASE 8B VALIDATION PASSED"
    )
    print(
        "PHASE 8 ROADMAP COVERAGE PASSED"
    )


if __name__ == "__main__":
    main()
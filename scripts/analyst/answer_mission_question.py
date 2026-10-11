from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

ANALYST_PATH = (
    ROOT
    / "scripts"
    / "analyst"
    / "mission_analyst.py"
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

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_mission_analyst_interface.json"
)

PROCESSED_DIR = (
    ROOT
    / "data"
    / "processed"
    / "analyst"
)

PROCESSED_PATH = (
    PROCESSED_DIR
    / "artemis_ii_mission_analyst_interface.json"
)

SMOKE_PATH = (
    PROCESSED_DIR
    / "phase8b_smoke_answers.json"
)


INTERFACE_DATASET_ID = (
    "phase8b_artemis_ii_"
    "mission_analyst_interface"
)

EXPECTED_INDEX_DATASET_ID = (
    "phase8a_artemis_ii_"
    "mission_analyst_index"
)

EXPECTED_PHASE7A_DATASET_ID = (
    "phase7a_artemis_ii_"
    "mission_control_perspectives"
)

EXPECTED_PHASE7B_DATASET_ID = (
    "phase7b_artemis_ii_"
    "mission_control_decision_threads"
)


EVENT_ALIASES = {
    "launch": "A2_LAUNCH",
    "otc3": "A2_OTC3",
    "pericynthion": "A2_PERICYNTHION",
    "earthset": "A2_EARTHSET",
    "earthrise": "A2_EARTHRISE",
    "rtc1": "A2_RTC1",
    "rtc2": "A2_RTC2",
    "rtc3": "A2_RTC3",
    "return link loss": (
        "A2_RETURN_LINK_LOSS"
    ),
    "return-link loss": (
        "A2_RETURN_LINK_LOSS"
    ),
    "entry interface": (
        "A2_ENTRY_INTERFACE"
    ),
    "entry blackout": (
        "A2_ENTRY_BLACKOUT"
    ),
    "plasma blackout": (
        "A2_ENTRY_BLACKOUT"
    ),
    "reacquisition": (
        "A2_ENTRY_REACQUISITION"
    ),
    "drogue": (
        "A2_DROGUE_DEPLOYMENT"
    ),
    "main parachute": (
        "A2_MAIN_DEPLOYMENT"
    ),
    "splashdown": (
        "A2_SPLASHDOWN"
    ),
}


THREAD_ALIASES = {
    "outbound correction": (
        "OUTBOUND_TRAJECTORY_ADAPTATION"
    ),
    "toilet fault": (
        "FD1_UWMS_FAULT_RECOVERY"
    ),
    "uwms fault": (
        "FD1_UWMS_FAULT_RECOVERY"
    ),
    "wastewater vent": (
        "FD4_WASTEWATER_VENT_RESPONSE"
    ),
    "vent line": (
        "FD4_WASTEWATER_VENT_RESPONSE"
    ),
    "vent-line": (
        "FD4_WASTEWATER_VENT_RESPONSE"
    ),
    "lunar communications": (
        "LUNAR_COMMUNICATIONS_CONSTRAINT"
    ),
    "lunar blackout": (
        "LUNAR_COMMUNICATIONS_CONSTRAINT"
    ),
    "lunar science": (
        "LUNAR_SCIENCE_EXECUTION"
    ),
    "impact flash": (
        "LUNAR_SCIENCE_EXECUTION"
    ),
    "impact flashes": (
        "LUNAR_SCIENCE_EXECUTION"
    ),
    "return link": (
        "RETURN_LINK_ANOMALY_RTC2"
    ),
    "return-link": (
        "RETURN_LINK_ANOMALY_RTC2"
    ),
    "heat shield": (
        "TPS_RISK_MITIGATION_CLOSURE"
    ),
    "heat-shield": (
        "TPS_RISK_MITIGATION_CLOSURE"
    ),
    "tps": (
        "TPS_RISK_MITIGATION_CLOSURE"
    ),
    "final correction": (
        "FINAL_CORRECTION_ENTRY_HANDOFF"
    ),
    "entry blackout": (
        "ENTRY_BLACKOUT_REACQUISITION"
    ),
    "plasma blackout": (
        "ENTRY_BLACKOUT_REACQUISITION"
    ),
    "descent": (
        "DESCENT_SPLASHDOWN_RECOVERY"
    ),
    "recovery": (
        "DESCENT_SPLASHDOWN_RECOVERY"
    ),
}


DISCIPLINE_ALIASES = {
    "flight director": "FLIGHT",
    "flight dynamics": "FDO",
    "flight activities": "FAO",
    "science officer": "SCIENCE",
    "engineering support": (
        "ENGINEERING_SUPPORT"
    ),
    "flight": "FLIGHT",
    "fdo": "FDO",
    "fao": "FAO",
    "eecom": "EECOM",
    "communications perspective": "COMM",
    "comm": "COMM",
    "science": "SCIENCE",
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 8B ANALYST FAILED: "
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


def relative_path(
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


def load_base_module():
    require(
        ANALYST_PATH.exists(),
        (
            "missing Phase 8A analyst: "
            f"{ANALYST_PATH}"
        ),
    )

    spec = importlib.util.spec_from_file_location(
        "phase8a_mission_analyst",
        ANALYST_PATH,
    )

    require(
        spec is not None,
        (
            "could not create "
            "Phase 8A module spec"
        ),
    )

    require(
        spec.loader is not None,
        (
            "Phase 8A module "
            "has no loader"
        ),
    )

    module = (
        importlib.util.module_from_spec(
            spec
        )
    )

    spec.loader.exec_module(
        module
    )

    return module


BASE = load_base_module()


def normalize_question(
    question: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        question.strip().lower(),
    )


def citation_key(
    value: dict,
) -> tuple:
    return (
        value.get(
            "dataset_id"
        ),
        value.get(
            "path"
        ),
        value.get(
            "locator"
        ),
        value.get(
            "url"
        ),
    )


def make_claim(
    statement: str,
    provenance: str,
    citations: list[dict],
    confidence: str = "SUPPORTED",
) -> dict:
    require(
        len(
            citations
        )
        >= 1,
        (
            "citation-first claim requires "
            "at least one citation"
        ),
    )

    return {
        "statement": statement,
        "provenance": provenance,
        "confidence": confidence,
        "citations": citations,
    }


def build_citation_registry(
    claims: list[dict],
) -> tuple[
    list[dict],
    list[dict],
]:
    citation_map: dict[
        tuple,
        str,
    ] = {}

    registry = []

    rendered_claims = []

    for claim in claims:
        ids = []

        for citation_value in claim[
            "citations"
        ]:
            key = citation_key(
                citation_value
            )

            if key not in citation_map:
                citation_id = (
                    f"C{len(registry) + 1}"
                )

                citation_map[
                    key
                ] = citation_id

                entry = dict(
                    citation_value
                )

                entry[
                    "citation_id"
                ] = citation_id

                registry.append(
                    entry
                )

            ids.append(
                citation_map[
                    key
                ]
            )

        rendered = dict(
            claim
        )

        rendered.pop(
            "citations",
            None,
        )

        rendered[
            "citation_ids"
        ] = ids

        rendered_claims.append(
            rendered
        )

    return (
        rendered_claims,
        registry,
    )


def render_answer_text(
    claims: list[dict],
) -> str:
    lines = []

    for claim in claims:
        suffix = " ".join(
            f"[{citation_id}]"
            for citation_id
            in claim[
                "citation_ids"
            ]
        )

        lines.append(
            claim[
                "statement"
            ]
            + " "
            + suffix
        )

    return "\n".join(
        lines
    )


def finalize_answer(
    question: str,
    route: str,
    claims: list[dict],
    evidence_bundle: list[dict],
    answer_status: str = "SUPPORTED",
    deterministic_tools: (
        list[dict]
        | None
    ) = None,
) -> dict:
    require(
        len(
            claims
        )
        >= 1,
        "answer requires at least one claim",
    )

    (
        rendered_claims,
        citations,
    ) = build_citation_registry(
        claims
    )

    return {
        "question": question,
        "route": route,
        "answer_status": (
            answer_status
        ),
        "answer_text": (
            render_answer_text(
                rendered_claims
            )
        ),
        "claims": (
            rendered_claims
        ),
        "citations": citations,
        "evidence_bundle": (
            evidence_bundle
        ),
        "deterministic_tools": (
            deterministic_tools
            or []
        ),
        "citation_first": True,
        "unsupported_fact_invention": (
            False
        ),
        "llm_required": False,
        "paid_model_required": False,
    }


def event_index(
    index: dict,
) -> dict[str, dict]:
    return {
        item[
            "event_id"
        ]: item
        for item
        in index[
            "event_registry"
        ]
    }


def thread_index(
    index: dict,
) -> dict[str, dict]:
    return {
        item[
            "thread_id"
        ]: item
        for item
        in index[
            "decision_thread_registry"
        ]
    }


def postflight_index(
    index: dict,
) -> dict[str, dict]:
    return {
        item[
            "record_id"
        ]: item
        for item
        in index[
            "postflight_registry"
        ]
    }


def discipline_index(
    phase7a: dict,
) -> dict[str, dict]:
    return {
        item[
            "discipline_id"
        ]: item
        for item
        in phase7a[
            "discipline_registry"
        ]
    }


def longest_alias(
    question: str,
    aliases: dict[
        str,
        str,
    ],
) -> str | None:
    matches = [
        (
            len(
                alias
            ),
            value,
        )
        for alias, value
        in aliases.items()
        if alias
        in question
    ]

    if not matches:
        return None

    matches.sort(
        reverse=True
    )

    return matches[
        0
    ][1]


def looks_like_time_question(
    question: str,
) -> bool:
    return any(
        marker
        in question
        for marker
        in [
            "when was",
            "what time",
            "timestamp",
            "what was the time",
            "mission elapsed time",
            "met for",
        ]
    )


def looks_like_elapsed_question(
    question: str,
) -> bool:
    return any(
        marker
        in question
        for marker
        in [
            "how long",
            "elapsed",
            "time between",
            "difference between",
        ]
    )


def looks_like_causation_question(
    question: str,
) -> bool:
    return any(
        marker
        in question
        for marker
        in [
            "cause",
            "caused",
            "because of",
            "due to",
            "result of",
        ]
    )


def looks_like_root_cause_question(
    question: str,
) -> bool:
    return (
        "root cause"
        in question
        or "what caused"
        in question
        or "why did"
        in question
    )


def looks_like_discipline_question(
    question: str,
) -> bool:
    return any(
        marker
        in question
        for marker
        in [
            "perspective",
            "focus",
            "responsible",
            "care about",
            "prioritize",
            "discipline",
            "console",
            "role",
        ]
    )


def classify_question(
    question: str,
) -> dict:
    q = normalize_question(
        question
    )

    if (
        looks_like_elapsed_question(
            q
        )
        and "earthset"
        in q
        and "earthrise"
        in q
    ):
        return {
            "route": (
                "DETERMINISTIC_"
                "ELAPSED_TIME"
            ),
            "subtype": (
                "EARTHSET_TO_"
                "EARTHRISE"
            ),
        }

    if (
        looks_like_root_cause_question(
            q
        )
        and any(
            term
            in q
            for term
            in [
                "vent",
                "wastewater",
                "urine",
            ]
        )
    ):
        return {
            "route": "KNOWN_UNKNOWN",
            "subtype": (
                "URINE_VENT_"
                "ROOT_CAUSE"
            ),
        }

    if (
        (
            "mission and fault"
            in q
            or "fault management"
            in q
        )
        and any(
            term
            in q
            for term
            in [
                "final",
                "result",
                "conclusion",
                "resolved",
            ]
        )
    ):
        return {
            "route": "KNOWN_UNKNOWN",
            "subtype": (
                "MISSION_FAULT_"
                "MANAGEMENT_FINAL"
            ),
        }

    if (
        looks_like_causation_question(
            q
        )
        and (
            "return link"
            in q
            or "return-link"
            in q
        )
        and "rtc2"
        in q
    ):
        return {
            "route": (
                "DECISION_THREAD_"
                "CAUSATION"
            ),
            "thread_id": (
                "RETURN_LINK_"
                "ANOMALY_RTC2"
            ),
        }

    discipline_id = (
        longest_alias(
            q,
            DISCIPLINE_ALIASES,
        )
    )

    if (
        discipline_id
        and looks_like_discipline_question(
            q
        )
    ):
        return {
            "route": "DISCIPLINE",
            "discipline_id": (
                discipline_id
            ),
        }

    event_id = longest_alias(
        q,
        EVENT_ALIASES,
    )

    if (
        event_id
        and looks_like_time_question(
            q
        )
    ):
        return {
            "route": "EVENT_TIME",
            "event_id": event_id,
        }

    thread_id = longest_alias(
        q,
        THREAD_ALIASES,
    )

    if thread_id:
        return {
            "route": (
                "DECISION_THREAD"
            ),
            "thread_id": (
                thread_id
            ),
        }

    if event_id:
        return {
            "route": "EVENT",
            "event_id": event_id,
        }

    return {
        "route": "SEARCH_SYNTHESIS",
    }


def answer_event(
    question: str,
    event: dict,
    route: str,
    include_met: bool = True,
) -> dict:
    citation_value = event[
        "citation"
    ]

    claims = []

    timestamp = event.get(
        "timestamp_utc"
    )

    if timestamp:
        if route == "EVENT_TIME":
            statement = (
                f"{event['name']} is recorded "
                f"at {timestamp}."
            )

        else:
            statement = (
                f"{event['name']} occurred "
                f"at {timestamp}. "
                f"{event['summary']}"
            )

        claims.append(
            make_claim(
                statement,
                event[
                    "evidence_class"
                ],
                [
                    citation_value
                ],
            )
        )

    else:
        claims.append(
            make_claim(
                (
                    "No exact public UTC is "
                    f"assigned to {event['name']}; "
                    "its timing is preserved as "
                    f"{event['time_precision']}."
                ),
                event[
                    "evidence_class"
                ],
                [
                    citation_value
                ],
            )
        )

    if (
        include_met
        and event.get(
            "met"
        )
    ):
        claims.append(
            make_claim(
                (
                    "Its MissionLab "
                    "mission-clock position is "
                    f"MET {event['met']}."
                ),
                (
                    "MISSIONLAB_"
                    "DETERMINISTIC_"
                    "MISSION_CLOCK"
                ),
                [
                    citation_value
                ],
            )
        )

    if (
        not timestamp
        or route
        == "EVENT_TIME"
    ):
        claims.append(
            make_claim(
                event[
                    "summary"
                ],
                event[
                    "evidence_class"
                ],
                [
                    citation_value
                ],
            )
        )

    return finalize_answer(
        question,
        route,
        claims,
        [
            event
        ],
    )


def answer_decision_thread(
    question: str,
    thread: dict,
) -> dict:
    citation_value = thread[
        "citation"
    ]

    stages = thread[
        "stages"
    ]

    claims = [
        make_claim(
            (
                f"{thread['title']} is "
                "classified as "
                f"{thread['classification']}."
            ),
            (
                "MISSIONLAB_"
                "DECISION_THREAD_"
                "CLASSIFICATION"
            ),
            [
                citation_value
            ],
        ),
        make_claim(
            (
                "Detection: "
                + stages[
                    "detection"
                ][
                    "summary"
                ]
            ),
            stages[
                "detection"
            ][
                "evidence_class"
            ],
            [
                citation_value
            ],
        ),
        make_claim(
            (
                "Action: "
                + stages[
                    "action"
                ][
                    "summary"
                ]
            ),
            stages[
                "action"
            ][
                "evidence_class"
            ],
            [
                citation_value
            ],
        ),
        make_claim(
            (
                "Outcome: "
                + stages[
                    "outcome"
                ][
                    "summary"
                ]
            ),
            stages[
                "outcome"
            ][
                "evidence_class"
            ],
            [
                citation_value
            ],
        ),
    ]

    return finalize_answer(
        question,
        "DECISION_THREAD",
        claims,
        [
            thread
        ],
    )


def answer_rtc2_causation(
    question: str,
    thread: dict,
) -> dict:
    citation_value = thread[
        "citation"
    ]

    require(
        (
            "TEMPORAL_SEQUENCE != CAUSATION"
            in thread[
                "guardrails"
            ]
        ),
        (
            "RTC2 causation guardrail "
            "missing from evidence"
        ),
    )

    claims = [
        make_claim(
            (
                "The curated public evidence "
                "does not establish that the "
                "unexpected return-link loss "
                "caused RTC2 or changed its "
                "targeting."
            ),
            (
                "PUBLIC_EVIDENCE_"
                "BOUNDARY"
            ),
            [
                citation_value
            ],
        ),
        make_claim(
            (
                "The supported public sequence "
                "is return-link interruption, "
                "communications recovery, "
                "resumed burn preparation, "
                "then RTC2 execution."
            ),
            "NASA_REPORTED",
            [
                citation_value
            ],
        ),
        make_claim(
            (
                "MissionLab explicitly "
                "preserves "
                "TEMPORAL_SEQUENCE != CAUSATION."
            ),
            (
                "MISSIONLAB_"
                "GUARDRAIL"
            ),
            [
                citation_value
            ],
        ),
    ]

    return finalize_answer(
        question,
        (
            "DECISION_THREAD_"
            "CAUSATION"
        ),
        claims,
        [
            thread
        ],
        answer_status=(
            "SUPPORTED_WITH_"
            "CAUSATION_BOUNDARY"
        ),
    )


def answer_urine_vent_unknown(
    question: str,
    index: dict,
) -> dict:
    thread = thread_index(
        index
    )[
        "FD4_WASTEWATER_"
        "VENT_RESPONSE"
    ]

    record = postflight_index(
        index
    )[
        "POSTFLIGHT_URINE_"
        "VENT_INVESTIGATION"
    ]

    claims = [
        make_claim(
            (
                "A confirmed urine vent-line "
                "root cause is not established "
                "in the curated public evidence."
            ),
            (
                "PUBLIC_EVIDENCE_"
                "BOUNDARY"
            ),
            [
                thread[
                    "citation"
                ],
                record[
                    "citation"
                ],
            ],
            confidence="KNOWN_UNKNOWN",
        ),
        make_claim(
            (
                "Possible ice was investigated, "
                "but MissionLab preserves "
                "POSSIBLE_ICE != CONFIRMED_ICE."
            ),
            (
                "NASA_REPORTED_PLUS_"
                "GUARDRAIL"
            ),
            [
                thread[
                    "citation"
                ]
            ],
        ),
        make_claim(
            (
                "NASA's April 20 postflight "
                "state still described hardware "
                "assessment and data gathering "
                "in support of root-cause "
                "identification and future "
                "corrective action."
            ),
            (
                "NASA_POSTFLIGHT_"
                "REPORTED"
            ),
            [
                record[
                    "citation"
                ]
            ],
        ),
    ]

    return finalize_answer(
        question,
        "KNOWN_UNKNOWN",
        claims,
        [
            thread,
            record,
        ],
        answer_status=(
            "UNKNOWN_IN_CURATED_"
            "PUBLIC_EVIDENCE"
        ),
    )


def answer_mission_fault_unknown(
    question: str,
    index: dict,
) -> dict:
    record = postflight_index(
        index
    )[
        "POSTFLIGHT_MISSION_"
        "FAULT_MANAGEMENT_ANALYSIS"
    ]

    claims = [
        make_claim(
            (
                "The curated public evidence "
                "does not contain a final Mission "
                "and Fault Management postflight "
                "result."
            ),
            (
                "PUBLIC_EVIDENCE_"
                "BOUNDARY"
            ),
            [
                record[
                    "citation"
                ]
            ],
            confidence="KNOWN_UNKNOWN",
        ),
        make_claim(
            (
                "The latest curated state reports "
                "the postflight analysis as ongoing."
            ),
            (
                "NASA_POSTFLIGHT_"
                "REPORTED"
            ),
            [
                record[
                    "citation"
                ]
            ],
        ),
    ]

    return finalize_answer(
        question,
        "KNOWN_UNKNOWN",
        claims,
        [
            record
        ],
        answer_status=(
            "UNKNOWN_IN_CURATED_"
            "PUBLIC_EVIDENCE"
        ),
    )


def discipline_citation(
    phase7a: dict,
    discipline_id: str,
) -> dict:
    return BASE.citation(
        phase7a[
            "dataset_id"
        ],
        relative_path(
            PHASE7A_PATH
        ),
        (
            "discipline_registry"
            f"[discipline_id={discipline_id}]"
        ),
        (
            "MISSION_CONTROL_"
            "ROLE_CONTEXT"
        ),
    )


def answer_discipline(
    question: str,
    discipline_id: str,
    index: dict,
    phase7a: dict,
) -> dict:
    disciplines = discipline_index(
        phase7a
    )

    require(
        discipline_id
        in disciplines,
        (
            "unknown discipline: "
            f"{discipline_id}"
        ),
    )

    discipline = disciplines[
        discipline_id
    ]

    citation_value = (
        discipline_citation(
            phase7a,
            discipline_id,
        )
    )

    relevant_events = sorted(
        (
            event
            for event
            in index[
                "event_registry"
            ]
            if event[
                "priorities"
            ][
                discipline_id
            ]
            == 3
        ),
        key=lambda event: event[
            "order"
        ],
    )

    claims = [
        make_claim(
            (
                f"{discipline_id} is represented "
                f"as {discipline['display_name']} "
                "with role type "
                f"{discipline['role_type']}."
            ),
            (
                "NASA_ROLE_CONTEXT_"
                "PLUS_MISSIONLAB_LENS"
            ),
            [
                citation_value
            ],
        ),
        make_claim(
            (
                "Its MissionLab focus includes "
                + ", ".join(
                    discipline[
                        "missionlab_focus"
                    ]
                )
                + "."
            ),
            (
                "MISSIONLAB_"
                "DISCIPLINE_MODEL"
            ),
            [
                citation_value
            ],
        ),
    ]

    if relevant_events:
        claims.append(
            make_claim(
                (
                    "Examples of PRIMARY-priority "
                    "mission events for this lens "
                    "include "
                    + ", ".join(
                        event[
                            "name"
                        ]
                        for event
                        in relevant_events[
                            :5
                        ]
                    )
                    + "."
                ),
                (
                    "MISSIONLAB_"
                    "PRIORITY_SYNTHESIS"
                ),
                [
                    citation_value,
                    *[
                        event[
                            "citation"
                        ]
                        for event
                        in relevant_events[
                            :5
                        ]
                    ],
                ],
            )
        )

    evidence_bundle = [
        {
            "discipline": (
                discipline
            ),
            "citation": (
                citation_value
            ),
        },
        *relevant_events[
            :5
        ],
    ]

    return finalize_answer(
        question,
        "DISCIPLINE",
        claims,
        evidence_bundle,
    )


def answer_earthset_earthrise_elapsed(
    question: str,
    index: dict,
) -> dict:
    events = event_index(
        index
    )

    earthset = events[
        "A2_EARTHSET"
    ]

    earthrise = events[
        "A2_EARTHRISE"
    ]

    require(
        earthset.get(
            "timestamp_utc"
        )
        is not None,
        "Earthset timestamp unavailable",
    )

    require(
        earthrise.get(
            "timestamp_utc"
        )
        is not None,
        "Earthrise timestamp unavailable",
    )

    calculation = (
        BASE.elapsed_time(
            earthset[
                "timestamp_utc"
            ],
            earthrise[
                "timestamp_utc"
            ],
        )
    )

    claims = [
        make_claim(
            (
                "The NASA-reported Earthset "
                "and Earthrise image times are "
                f"{earthset['timestamp_utc']} "
                "and "
                f"{earthrise['timestamp_utc']}."
            ),
            "NASA_REPORTED",
            [
                earthset[
                    "citation"
                ],
                earthrise[
                    "citation"
                ],
            ],
        ),
        make_claim(
            (
                "The deterministic elapsed time "
                "between those reported image "
                "times is "
                f"{calculation['elapsed_minutes']:.0f} "
                "minutes "
                f"({calculation['formatted']})."
            ),
            (
                "MISSIONLAB_"
                "DETERMINISTIC_CALCULATION"
            ),
            [
                earthset[
                    "citation"
                ],
                earthrise[
                    "citation"
                ],
            ],
        ),
        make_claim(
            (
                "This image-time difference is "
                "not the same thing as the "
                "duration of full Earth occultation."
            ),
            (
                "MISSIONLAB_"
                "EVIDENCE_BOUNDARY"
            ),
            [
                earthset[
                    "citation"
                ],
                earthrise[
                    "citation"
                ],
            ],
        ),
    ]

    return finalize_answer(
        question,
        (
            "DETERMINISTIC_"
            "ELAPSED_TIME"
        ),
        claims,
        [
            earthset,
            earthrise,
        ],
        deterministic_tools=[
            calculation
        ],
    )


def answer_search_synthesis(
    question: str,
    index: dict,
) -> dict:
    results = BASE.search_index(
        index,
        question,
        None,
        5,
    )

    if not results:
        claims = [
            make_claim(
                (
                    "No indexed MissionLab "
                    "evidence matched this question "
                    "strongly enough to support "
                    "a factual answer."
                ),
                (
                    "RETRIEVAL_BOUNDARY"
                ),
                [
                    BASE.citation(
                        index[
                            "dataset_id"
                        ],
                        relative_path(
                            INDEX_PATH
                        ),
                        "$",
                        (
                            "PHASE8A_INDEX"
                        ),
                    )
                ],
                confidence=(
                    "INSUFFICIENT_EVIDENCE"
                ),
            )
        ]

        return finalize_answer(
            question,
            "SEARCH_SYNTHESIS",
            claims,
            [],
            answer_status=(
                "INSUFFICIENT_"
                "INDEXED_EVIDENCE"
            ),
        )

    claims = []

    evidence_bundle = []

    for result in results[
        :3
    ]:
        claims.append(
            make_claim(
                (
                    f"{result['title']}: "
                    f"{result['summary']}"
                ),
                (
                    result[
                        "citation"
                    ].get(
                        "evidence_class"
                    )
                    or "INDEXED_EVIDENCE"
                ),
                [
                    result[
                        "citation"
                    ]
                ],
            )
        )

        evidence_bundle.append(
            result
        )

    return finalize_answer(
        question,
        "SEARCH_SYNTHESIS",
        claims,
        evidence_bundle,
    )


def answer_question(
    question: str,
    index: dict,
    phase7a: dict,
) -> dict:
    require(
        bool(
            question.strip()
        ),
        "question must not be empty",
    )

    routing = classify_question(
        question
    )

    route = routing[
        "route"
    ]

    if route == (
        "DETERMINISTIC_"
        "ELAPSED_TIME"
    ):
        return (
            answer_earthset_earthrise_elapsed(
                question,
                index,
            )
        )

    if route == "KNOWN_UNKNOWN":
        if routing[
            "subtype"
        ] == (
            "URINE_VENT_"
            "ROOT_CAUSE"
        ):
            return (
                answer_urine_vent_unknown(
                    question,
                    index,
                )
            )

        if routing[
            "subtype"
        ] == (
            "MISSION_FAULT_"
            "MANAGEMENT_FINAL"
        ):
            return (
                answer_mission_fault_unknown(
                    question,
                    index,
                )
            )

    if route == (
        "DECISION_THREAD_"
        "CAUSATION"
    ):
        return (
            answer_rtc2_causation(
                question,
                thread_index(
                    index
                )[
                    routing[
                        "thread_id"
                    ]
                ],
            )
        )

    if route == "DISCIPLINE":
        return answer_discipline(
            question,
            routing[
                "discipline_id"
            ],
            index,
            phase7a,
        )

    if route in {
        "EVENT",
        "EVENT_TIME",
    }:
        return answer_event(
            question,
            event_index(
                index
            )[
                routing[
                    "event_id"
                ]
            ],
            route=route,
        )

    if route == "DECISION_THREAD":
        return answer_decision_thread(
            question,
            thread_index(
                index
            )[
                routing[
                    "thread_id"
                ]
            ],
        )

    return answer_search_synthesis(
        question,
        index,
    )


def validate_answer_contract(
    answer: dict,
):
    require(
        answer[
            "citation_first"
        ]
        is True,
        "answer is not citation-first",
    )

    require(
        answer[
            "unsupported_fact_invention"
        ]
        is False,
        (
            "answer permits unsupported "
            "fact invention"
        ),
    )

    require(
        answer[
            "llm_required"
        ]
        is False,
        (
            "answer incorrectly "
            "requires an LLM"
        ),
    )

    require(
        answer[
            "paid_model_required"
        ]
        is False,
        (
            "answer incorrectly requires "
            "a paid model"
        ),
    )

    citation_ids = {
        item[
            "citation_id"
        ]
        for item
        in answer[
            "citations"
        ]
    }

    require(
        len(
            citation_ids
        )
        == len(
            answer[
                "citations"
            ]
        ),
        (
            "duplicate answer "
            "citation IDs"
        ),
    )

    for claim in answer[
        "claims"
    ]:
        require(
            len(
                claim[
                    "citation_ids"
                ]
            )
            >= 1,
            (
                "claim missing citation IDs: "
                f"{claim['statement']}"
            ),
        )

        for citation_id in claim[
            "citation_ids"
        ]:
            require(
                citation_id
                in citation_ids,
                (
                    "claim references unknown "
                    f"citation: {citation_id}"
                ),
            )

            require(
                f"[{citation_id}]"
                in answer[
                    "answer_text"
                ],
                (
                    "answer text missing "
                    "citation token: "
                    f"{citation_id}"
                ),
            )


def build_llm_handoff(
    answer: dict,
    target: str,
) -> dict:
    require(
        target
        in {
            "local",
            "browser",
        },
        (
            "LLM handoff target "
            "must be local or browser"
        ),
    )

    validate_answer_contract(
        answer
    )

    locked_claims = [
        {
            "statement": (
                claim[
                    "statement"
                ]
            ),
            "provenance": (
                claim[
                    "provenance"
                ]
            ),
            "confidence": (
                claim[
                    "confidence"
                ]
            ),
            "citation_ids": (
                claim[
                    "citation_ids"
                ]
            ),
        }
        for claim
        in answer[
            "claims"
        ]
    ]

    prompt_lines = [
        (
            "You are formatting an "
            "Artemis II MissionLab answer."
        ),
        (
            "Use ONLY the locked claims "
            "and citations provided below."
        ),
        (
            "Do not add facts, timestamps, "
            "causes, root causes, controller "
            "actions, or mission interpretations."
        ),
        (
            "Do not convert MissionLab-derived "
            "information into NASA-reported fact."
        ),
        (
            "Preserve every "
            "evidence limitation."
        ),
        (
            "Every factual sentence must "
            "include one or more supplied "
            "citation IDs."
        ),
        "",
        "QUESTION:",
        answer[
            "question"
        ],
        "",
        "LOCKED CLAIMS:",
    ]

    for claim in locked_claims:
        prompt_lines.append(
            "- "
            + claim[
                "statement"
            ]
            + " "
            + " ".join(
                f"[{citation_id}]"
                for citation_id
                in claim[
                    "citation_ids"
                ]
            )
        )

    prompt_lines.extend(
        [
            "",
            "CITATIONS:",
        ]
    )

    for value in answer[
        "citations"
    ]:
        prompt_lines.append(
            (
                f"[{value['citation_id']}] "
                f"{value['citation_text']}"
            )
        )

    prompt_lines.extend(
        [
            "",
            (
                "Return a concise answer "
                "using only the material above."
            ),
        ]
    )

    return {
        "target": target,
        "optional": True,
        "execution_performed": False,
        "network_call_performed": False,
        "paid_model_required": False,
        "api_key_required": False,
        "authoritative_layer": (
            "DETERMINISTIC_"
            "MISSIONLAB_EVIDENCE"
        ),
        "question": answer[
            "question"
        ],
        "locked_claims": (
            locked_claims
        ),
        "citations": answer[
            "citations"
        ],
        "deterministic_answer": (
            answer[
                "answer_text"
            ]
        ),
        "prompt": "\n".join(
            prompt_lines
        ),
        "rules": [
            (
                "Use only supplied "
                "locked claims."
            ),
            (
                "Do not invent "
                "missing facts."
            ),
            (
                "Do not infer private "
                "console dialogue."
            ),
            (
                "Do not infer undisclosed "
                "decision authority."
            ),
            (
                "Do not convert temporal "
                "order into causation."
            ),
            (
                "Do not promote hypotheses "
                "to root causes."
            ),
            (
                "Preserve MissionLab-derived "
                "vs NASA-reported provenance."
            ),
            (
                "Every factual sentence "
                "requires supplied citations."
            ),
        ],
    }


def build_interface_manifest(
    index: dict,
    phase7a: dict,
    phase7b: dict,
    smoke_answers: list[dict],
) -> dict:
    return {
        "dataset_id": (
            INTERFACE_DATASET_ID
        ),
        "mission": "Artemis II",
        "phase": "8B",
        "status": (
            "CITATION_FIRST_"
            "MISSION_ANALYST_COMPLETE"
        ),
        "purpose": (
            "Compose evidence-grounded "
            "Artemis II answers from the "
            "Phase 8A retrieval layer, with "
            "claim-level citations and optional "
            "local/browser LLM presentation handoff."
        ),
        "dependencies": [
            {
                "dataset_id": (
                    index[
                        "dataset_id"
                    ]
                ),
                "path": (
                    relative_path(
                        INDEX_PATH
                    )
                ),
                "role": (
                    "structured retrieval "
                    "and deterministic tools"
                ),
            },
            {
                "dataset_id": (
                    phase7a[
                        "dataset_id"
                    ]
                ),
                "path": (
                    relative_path(
                        PHASE7A_PATH
                    )
                ),
                "role": (
                    "discipline registry and "
                    "shared event priorities"
                ),
            },
            {
                "dataset_id": (
                    phase7b[
                        "dataset_id"
                    ]
                ),
                "path": (
                    relative_path(
                        PHASE7B_PATH
                    )
                ),
                "role": (
                    "decision threads and "
                    "known/unknown boundaries"
                ),
            },
        ],
        "question_router": {
            "routes": [
                "EVENT_TIME",
                "EVENT",
                "DECISION_THREAD",
                (
                    "DECISION_THREAD_"
                    "CAUSATION"
                ),
                "DISCIPLINE",
                (
                    "DETERMINISTIC_"
                    "ELAPSED_TIME"
                ),
                "KNOWN_UNKNOWN",
                "SEARCH_SYNTHESIS",
            ],
            "deterministic": True,
            "llm_used_for_routing": (
                False
            ),
        },
        "answer_contract": {
            "citation_first": True,
            (
                "claim_level_"
                "citations_required"
            ): True,
            (
                "unsupported_fact_"
                "invention_allowed"
            ): False,
            (
                "known_unknown_"
                "state_supported"
            ): True,
            (
                "provenance_labels_"
                "required"
            ): True,
            (
                "deterministic_tools_"
                "may_be_used"
            ): True,
            "llm_required": False,
            (
                "paid_model_required"
            ): False,
        },
        "optional_llm_adapters": [
            {
                "adapter_id": (
                    "LOCAL_LLM_"
                    "PROMPT_HANDOFF"
                ),
                "target": "local",
                "optional": True,
                (
                    "execution_"
                    "embedded"
                ): False,
                (
                    "api_key_"
                    "required"
                ): False,
                (
                    "paid_model_"
                    "required"
                ): False,
                "description": (
                    "Export a locked evidence "
                    "bundle and formatting prompt "
                    "for an optional local model."
                ),
            },
            {
                "adapter_id": (
                    "BROWSER_LLM_"
                    "PROMPT_HANDOFF"
                ),
                "target": "browser",
                "optional": True,
                (
                    "execution_"
                    "embedded"
                ): False,
                (
                    "api_key_"
                    "required"
                ): False,
                (
                    "paid_model_"
                    "required"
                ): False,
                "description": (
                    "Export the same locked "
                    "evidence bundle for optional "
                    "browser-side model presentation."
                ),
            },
        ],
        "authority_model": {
            (
                "deterministic_retrieval_"
                "is_authoritative"
            ): True,
            (
                "deterministic_calculations_"
                "are_authoritative"
            ): True,
            (
                "llm_may_rewrite_"
                "locked_claims"
            ): True,
            (
                "llm_may_add_new_facts"
            ): False,
            (
                "llm_may_override_"
                "evidence_boundaries"
            ): False,
            (
                "llm_may_change_"
                "provenance"
            ): False,
            (
                "llm_may_invent_"
                "citations"
            ): False,
        },
        "known_unknown_policy": {
            (
                "unknowns_are_"
                "answerable"
            ): True,
            (
                "unknown_answer_must_"
                "state_boundary"
            ): True,
            (
                "hypothesis_may_be_"
                "promoted_to_fact"
            ): False,
            (
                "open_investigation_"
                "may_be_forced_closed"
            ): False,
            (
                "missing_exact_time_"
                "may_be_invented"
            ): False,
        },
        "sample_answer_count": (
            len(
                smoke_answers
            )
        ),
        "sample_answers": [
            {
                "question": (
                    answer[
                        "question"
                    ]
                ),
                "route": (
                    answer[
                        "route"
                    ]
                ),
                "answer_status": (
                    answer[
                        "answer_status"
                    ]
                ),
                "claim_count": (
                    len(
                        answer[
                            "claims"
                        ]
                    )
                ),
                "citation_count": (
                    len(
                        answer[
                            "citations"
                        ]
                    )
                ),
            }
            for answer
            in smoke_answers
        ],
        "phase8_roadmap_assessment": {
            (
                "structured_retrieval_"
                "over_events_data_sources"
            ): (
                "COMPLETE_PHASE8A"
            ),
            (
                "deterministic_calculations_"
                "exposed_as_tools"
            ): (
                "COMPLETE_PHASE8A"
            ),
            (
                "citation_first_answers"
            ): (
                "COMPLETE_PHASE8B"
            ),
            (
                "optional_local_"
                "browser_llm"
            ): (
                "COMPLETE_AS_OPTIONAL_"
                "HANDOFF_PHASE8B"
            ),
            (
                "no_paid_model_"
                "dependency"
            ): "COMPLETE",
            "phase8_overall": (
                "COMPLETE_RELATIVE_TO_"
                "VALIDATED_MISSIONLAB_"
                "EVIDENCE"
            ),
        },
        "critical_non_equivalences": [
            (
                "LLM_PRESENTATION "
                "!= EVIDENCE_AUTHORITY"
            ),
            (
                "RETRIEVAL_MATCH "
                "!= FACT_NOT_SUPPORTED_BY_RECORD"
            ),
            (
                "MISSIONLAB_DERIVED "
                "!= NASA_REPORTED"
            ),
            (
                "TEMPORAL_SEQUENCE "
                "!= CAUSATION"
            ),
            (
                "HYPOTHESIS "
                "!= CONFIRMED_ROOT_CAUSE"
            ),
            (
                "UNKNOWN_PUBLIC_FACT "
                "!= PERMISSION_TO_INVENT"
            ),
            (
                "DISCIPLINE_RELEVANCE "
                "!= DECISION_AUTHORITY"
            ),
            (
                "OPTIONAL_LLM_HANDOFF "
                "!= REQUIRED_MODEL_DEPENDENCY"
            ),
        ],
        "outputs": {
            "reference_json": (
                "data/reference/"
                "artemis_ii_mission_"
                "analyst_interface.json"
            ),
            "processed_json": (
                "data/processed/analyst/"
                "artemis_ii_mission_"
                "analyst_interface.json"
            ),
            "smoke_answers_json": (
                "data/processed/analyst/"
                "phase8b_smoke_answers.json"
            ),
        },
    }


def load_runtime() -> tuple[
    dict,
    dict,
    dict,
]:
    index = load_json(
        INDEX_PATH
    )

    phase7a = load_json(
        PHASE7A_PATH
    )

    phase7b = load_json(
        PHASE7B_PATH
    )

    require(
        index.get(
            "dataset_id"
        )
        == EXPECTED_INDEX_DATASET_ID,
        (
            "Phase 8A analyst "
            "index mismatch"
        ),
    )

    require(
        phase7a.get(
            "dataset_id"
        )
        == EXPECTED_PHASE7A_DATASET_ID,
        (
            "Phase 7A dependency "
            "mismatch"
        ),
    )

    require(
        phase7b.get(
            "dataset_id"
        )
        == EXPECTED_PHASE7B_DATASET_ID,
        (
            "Phase 7B dependency "
            "mismatch"
        ),
    )

    return (
        index,
        phase7a,
        phase7b,
    )


def run_build_interface():
    (
        index,
        phase7a,
        phase7b,
    ) = load_runtime()

    smoke_questions = [
        "When was RTC2?",
        (
            "Did the return link loss "
            "cause RTC2?"
        ),
        (
            "What was the root cause "
            "of the urine vent-line issue?"
        ),
        (
            "How long was it between "
            "Earthset and Earthrise?"
        ),
        (
            "What does the SCIENCE "
            "perspective focus on?"
        ),
        (
            "What happened with the "
            "Artemis II heat shield?"
        ),
    ]

    smoke_answers = []

    for question in smoke_questions:
        answer = answer_question(
            question,
            index,
            phase7a,
        )

        validate_answer_contract(
            answer
        )

        smoke_answers.append(
            answer
        )

    require(
        smoke_answers[
            0
        ][
            "route"
        ]
        == "EVENT_TIME",
        (
            "RTC2 smoke test "
            "routing mismatch"
        ),
    )

    require(
        "2026-04-10T02:53:00Z"
        in smoke_answers[
            0
        ][
            "answer_text"
        ],
        (
            "RTC2 smoke answer "
            "missing UTC"
        ),
    )

    require(
        smoke_answers[
            1
        ][
            "route"
        ]
        == (
            "DECISION_THREAD_"
            "CAUSATION"
        ),
        (
            "RTC2 causation "
            "routing mismatch"
        ),
    )

    require(
        "does not establish"
        in smoke_answers[
            1
        ][
            "answer_text"
        ],
        (
            "RTC2 causation "
            "boundary missing"
        ),
    )

    require(
        smoke_answers[
            2
        ][
            "answer_status"
        ]
        == (
            "UNKNOWN_IN_CURATED_"
            "PUBLIC_EVIDENCE"
        ),
        (
            "urine vent root cause "
            "was not preserved "
            "as unknown"
        ),
    )

    require(
        any(
            tool[
                "tool"
            ]
            == "elapsed_time"
            and tool[
                "elapsed_minutes"
            ]
            == 41.0
            for tool
            in smoke_answers[
                3
            ][
                "deterministic_tools"
            ]
        ),
        (
            "Earthset/Earthrise "
            "calculation mismatch"
        ),
    )

    require(
        smoke_answers[
            4
        ][
            "route"
        ]
        == "DISCIPLINE",
        (
            "SCIENCE discipline "
            "routing mismatch"
        ),
    )

    require(
        smoke_answers[
            5
        ][
            "route"
        ]
        == "DECISION_THREAD",
        (
            "TPS decision-thread "
            "routing mismatch"
        ),
    )

    local_handoff = (
        build_llm_handoff(
            smoke_answers[
                5
            ],
            "local",
        )
    )

    browser_handoff = (
        build_llm_handoff(
            smoke_answers[
                5
            ],
            "browser",
        )
    )

    for handoff in [
        local_handoff,
        browser_handoff,
    ]:
        require(
            handoff[
                "execution_performed"
            ]
            is False,
            (
                "optional LLM execution "
                "should remain disabled"
            ),
        )

        require(
            handoff[
                "paid_model_required"
            ]
            is False,
            (
                "optional LLM handoff "
                "must not require "
                "a paid model"
            ),
        )

    manifest = (
        build_interface_manifest(
            index,
            phase7a,
            phase7b,
            smoke_answers,
        )
    )

    write_json(
        REFERENCE_PATH,
        manifest,
    )

    write_json(
        PROCESSED_PATH,
        manifest,
    )

    write_json(
        SMOKE_PATH,
        {
            "answers": (
                smoke_answers
            ),
            "local_llm_handoff": (
                local_handoff
            ),
            "browser_llm_handoff": (
                browser_handoff
            ),
        },
    )

    print()
    print(
        "Phase 8B Artemis II "
        "Citation-First Mission Analyst"
    )
    print(
        "=" * 72
    )

    print()
    print(
        "Dependencies:"
    )
    print(
        "  Phase 8A structured retrieval: PASS"
    )
    print(
        "  Phase 7A discipline registry: PASS"
    )
    print(
        "  Phase 7B decision boundaries: PASS"
    )

    print()
    print(
        "Question router:"
    )

    for route in [
        "EVENT_TIME",
        "EVENT",
        "DECISION_THREAD",
        (
            "DECISION_THREAD_"
            "CAUSATION"
        ),
        "DISCIPLINE",
        (
            "DETERMINISTIC_"
            "ELAPSED_TIME"
        ),
        "KNOWN_UNKNOWN",
        "SEARCH_SYNTHESIS",
    ]:
        print(
            f"  {route}: READY"
        )

    print()
    print(
        "Citation-first answer contract:"
    )
    print(
        "  claim-level citations required: YES"
    )
    print(
        "  provenance labels required: YES"
    )
    print(
        "  known/unknown answers supported: YES"
    )
    print(
        "  unsupported fact invention allowed: NO"
    )
    print(
        "  LLM required: NO"
    )
    print(
        "  paid model required: NO"
    )

    print()
    print(
        "Smoke answers:"
    )

    for answer in smoke_answers:
        print(
            "  "
            + answer[
                "route"
            ]
            + "  "
            + answer[
                "question"
            ]
        )

        print(
            "    status: "
            + answer[
                "answer_status"
            ]
        )

        print(
            "    claims: "
            + str(
                len(
                    answer[
                        "claims"
                    ]
                )
            )
        )

        print(
            "    citations: "
            + str(
                len(
                    answer[
                        "citations"
                    ]
                )
            )
        )

    print()
    print(
        "Deterministic calculation answer:"
    )
    print(
        "  Earthset -> Earthrise: 41 minutes"
    )

    print()
    print(
        "Known/unknown enforcement:"
    )
    print(
        "  urine vent-line final root cause: "
        "UNKNOWN IN CURATED PUBLIC EVIDENCE"
    )
    print(
        "  hypothesis promoted to root cause: NO"
    )

    print()
    print(
        "Causation enforcement:"
    )
    print(
        "  return-link loss -> RTC2 "
        "causation claimed: NO"
    )
    print(
        "  temporal sequence != causation: "
        "PRESERVED"
    )

    print()
    print(
        "Optional LLM handoff:"
    )
    print(
        "  local evidence-bundle handoff: READY"
    )
    print(
        "  browser evidence-bundle handoff: READY"
    )
    print(
        "  embedded model execution: NO"
    )
    print(
        "  API key required: NO"
    )
    print(
        "  paid model dependency: NONE"
    )
    print(
        "  deterministic evidence remains "
        "authoritative: YES"
    )

    print()
    print(
        "Phase 8 roadmap:"
    )
    print(
        "  structured retrieval over "
        "events/data/sources: COMPLETE"
    )
    print(
        "  deterministic calculations "
        "as tools: COMPLETE"
    )
    print(
        "  citation-first answers: COMPLETE"
    )
    print(
        "  optional local/browser LLM: "
        "COMPLETE AS OPTIONAL HANDOFF"
    )
    print(
        "  paid model dependency: NONE"
    )
    print(
        "  overall: COMPLETE RELATIVE TO "
        "VALIDATED MISSIONLAB EVIDENCE"
    )

    print()
    print(
        "Wrote:"
    )
    print(
        "  "
        + relative_path(
            REFERENCE_PATH
        )
    )
    print(
        "  "
        + relative_path(
            PROCESSED_PATH
        )
    )
    print(
        "  "
        + relative_path(
            SMOKE_PATH
        )
    )

    print()
    print(
        "PHASE 8B CITATION-FIRST "
        "MISSION ANALYST COMPLETE"
    )
    print(
        "PHASE 8 ROADMAP "
        "RECONSTRUCTION COMPLETE"
    )


def run_ask(
    question: str,
    output_format: str,
):
    (
        index,
        phase7a,
        _,
    ) = load_runtime()

    answer = answer_question(
        question,
        index,
        phase7a,
    )

    validate_answer_contract(
        answer
    )

    if output_format == "json":
        print(
            json.dumps(
                answer,
                indent=2,
                ensure_ascii=False,
            )
        )

        return

    print()
    print(
        answer[
            "answer_text"
        ]
    )

    print()
    print(
        "Citations:"
    )

    for value in answer[
        "citations"
    ]:
        print(
            (
                f"[{value['citation_id']}] "
                f"{value['citation_text']}"
            )
        )

        if value.get(
            "url"
        ):
            print(
                "    "
                + value[
                    "url"
                ]
            )


def run_handoff(
    question: str,
    target: str,
):
    (
        index,
        phase7a,
        _,
    ) = load_runtime()

    answer = answer_question(
        question,
        index,
        phase7a,
    )

    handoff = build_llm_handoff(
        answer,
        target,
    )

    print(
        json.dumps(
            handoff,
            indent=2,
            ensure_ascii=False,
        )
    )


def run_examples():
    examples = [
        "When was RTC2?",
        (
            "Did the return link loss "
            "cause RTC2?"
        ),
        (
            "What was the root cause "
            "of the urine vent-line issue?"
        ),
        (
            "How long was it between "
            "Earthset and Earthrise?"
        ),
        (
            "What does the SCIENCE "
            "perspective focus on?"
        ),
        (
            "What happened with the "
            "Artemis II heat shield?"
        ),
        (
            "What happened at "
            "Entry Interface?"
        ),
        (
            "What does MissionLab know "
            "about the lunar "
            "communications blackout?"
        ),
    ]

    for item in examples:
        print(
            item
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Artemis II citation-first "
            "MissionLab answer composer"
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "build-interface",
        help=(
            "Build and smoke-test the "
            "Phase 8B citation-first "
            "analyst interface."
        ),
    )

    ask_parser = subparsers.add_parser(
        "ask",
        help=(
            "Answer a mission question "
            "using the deterministic "
            "evidence layer."
        ),
    )

    ask_parser.add_argument(
        "question"
    )

    ask_parser.add_argument(
        "--format",
        choices=[
            "text",
            "json",
        ],
        default="text",
    )

    handoff_parser = (
        subparsers.add_parser(
            "handoff",
            help=(
                "Export a locked evidence "
                "bundle for optional local "
                "or browser LLM formatting."
            ),
        )
    )

    handoff_parser.add_argument(
        "question"
    )

    handoff_parser.add_argument(
        "--target",
        choices=[
            "local",
            "browser",
        ],
        required=True,
    )

    subparsers.add_parser(
        "examples",
        help=(
            "Show example supported "
            "questions."
        ),
    )

    return parser


def main():
    parser = build_parser()

    args = parser.parse_args()

    if args.command == "build-interface":
        run_build_interface()

    elif args.command == "ask":
        run_ask(
            args.question,
            args.format,
        )

    elif args.command == "handoff":
        run_handoff(
            args.question,
            args.target,
        )

    elif args.command == "examples":
        run_examples()

    else:
        parser.error(
            "unsupported command"
        )


if __name__ == "__main__":
    main()
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_waste_management_evidence.json"
)


EXPECTED_DATASET_ID = (
    "phase3b1_artemis_ii_"
    "waste_management_evidence"
)

EXPECTED_EVENT_IDS = {
    "A2_UWMS_FD1_FAULT_LIGHT",
    "A2_UWMS_FD1_RESTORED",
    "A2_UWMS_FD4_WASTEWATER_VENT_EARLY_END",
    "A2_UWMS_FD4_VENT_HEATER_RESPONSE",
    "A2_UWMS_FD4_SOLAR_POINTING",
    "A2_UWMS_FD4_BACKUP_COLLECTION_POSTURE",
    "A2_UWMS_POSTFLIGHT_URINE_VENT_INVESTIGATION",
}

EXPECTED_THREADS = {
    "flight_day_1_toilet_fault_and_recovery",
    "flight_day_4_urine_wastewater_vent_line_issue",
}

EXPECTED_SOURCE_IDS = {
    "NASA_A2_APOGEE_RAISE_UPDATE_2026_04_01",
    "NASA_A2_TOILET_RECOVERY_UPDATE_2026_04_02",
    "NASA_A2_FLIGHT_DAY_4_UPDATE_2026_04_04",
    "NASA_A2_INITIAL_POSTFLIGHT_ASSESSMENT_2026_04_20",
    "NASA_ORION_CREW_SYSTEMS_UWMS",
    "NASA_A2_REFERENCE_GUIDE_UWMS",
    "NASA_NTRS_ORION_UWMS_ARTEMIS_II",
}

REQUIRED_NON_EQUIVALENCES = {
    "BLINKING_FAULT_LIGHT != IDENTIFIED_FAILED_COMPONENT",
    "TOILET_FAULT_INDICATION != COMPLETE_UWMS_FAILURE",
    "TOILET_RETURNED_TO_NORMAL != ROOT_CAUSE_PUBLICLY_KNOWN",
    "VENT_ENDED_EARLY != CONFIRMED_COMPLETE_BLOCKAGE",
    "POSSIBLE_ICE != CONFIRMED_ICE",
    "VENT_HEATER_USE != PROOF_OF_ICE",
    "SUN_POINTING != ROOT_CAUSE_CONFIRMATION",
    "BACKUP_COLLECTION_AVAILABLE != TOILET_INOPERATIVE",
    "TANK_NOT_FULL != NOMINAL_VENT_LINE",
    "TOILET_OPERATIONAL != NOMINAL_URINE_VENT_PATH",
    "POSTFLIGHT_INVESTIGATION != FINAL_ROOT_CAUSE",
    "WASTEWATER_VENT_ISSUE != FECAL_COLLECTION_FAILURE",
}

REQUIRED_NOT_RECONSTRUCTABLE = {
    "Exact Flight Day 1 fault timestamp",
    "Internal UWMS fault code",
    "Exact failed component for the Flight Day 1 fault indication",
    "Flight Day 1 root cause",
    "Exact wastewater vent start time",
    "Exact wastewater vent stop time",
    "Vent-line pressure telemetry",
    "Vent-line temperature telemetry",
    "Vent flow-rate telemetry",
    "Confirmed presence of ice",
    "Complete internal ECLSS telemetry",
}


def fail(
    message: str,
):
    raise SystemExit(
        "PHASE 3B.1 VALIDATION FAILED: "
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


def load_reference() -> dict:
    if not REFERENCE_PATH.exists():
        fail(
            "missing reference product: "
            f"{REFERENCE_PATH}"
        )

    try:
        with REFERENCE_PATH.open(
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(
                f
            )

    except json.JSONDecodeError as exc:
        fail(
            "reference JSON is invalid: "
            f"{exc}"
        )

        raise


def parse_date(
    value: str,
    label: str,
) -> date:
    try:
        return date.fromisoformat(
            value
        )

    except ValueError:
        fail(
            f"{label} is not a valid "
            f"ISO date: {value}"
        )

        raise


def index_by_id(
    rows: list[dict],
    field: str,
    label: str,
) -> dict[str, dict]:
    result = {}

    for row in rows:
        if field not in row:
            fail(
                f"{label} is missing "
                f"{field}"
            )

        value = row[
            field
        ]

        if value in result:
            fail(
                f"duplicate {label} "
                f"{field}: {value}"
            )

        result[
            value
        ] = row

    return result


def require_source_resolution(
    events: list[dict],
    source_ids: set[str],
):
    for event in events:
        event_id = (
            event[
                "event_id"
            ]
        )

        event_sources = (
            event.get(
                "source_ids"
            )
        )

        require(
            isinstance(
                event_sources,
                list,
            )
            and len(
                event_sources
            )
            >= 1,
            (
                f"{event_id} must contain "
                "at least one source ID"
            ),
        )

        for source_id in event_sources:
            require(
                source_id
                in source_ids,
                (
                    f"{event_id} references "
                    "unknown source ID "
                    f"{source_id}"
                ),
            )


def validate_identity(
    data: dict,
):
    require(
        data.get(
            "dataset_id"
        )
        == EXPECTED_DATASET_ID,
        "dataset ID mismatch",
    )

    require(
        data.get(
            "mission"
        )
        == "Artemis II",
        "mission identity mismatch",
    )

    require(
        data.get(
            "phase"
        )
        == "3B.1",
        "phase identity mismatch",
    )

    require(
        data.get(
            "status"
        )
        == (
            "REFERENCE_EVIDENCE_"
            "ASSEMBLED"
        ),
        "reference status mismatch",
    )

    require(
        data.get(
            "title"
        )
        == (
            "Artemis II Waste "
            "Management Public "
            "Evidence Reconstruction"
        ),
        "reference title mismatch",
    )


def validate_scope(
    data: dict,
):
    scope = (
        data.get(
            "scope"
        )
    )

    require(
        isinstance(
            scope,
            dict,
        ),
        "missing scope object",
    )

    require(
        scope.get(
            "system"
        )
        == (
            "Orion Universal "
            "Waste Management System"
        ),
        "scope system mismatch",
    )

    require(
        scope.get(
            "abbreviation"
        )
        == "UWMS",
        "UWMS abbreviation mismatch",
    )

    threads = set(
        scope.get(
            "threads",
            [],
        )
    )

    require(
        threads
        == EXPECTED_THREADS,
        (
            "scope thread set mismatch: "
            f"{sorted(threads)}"
        ),
    )


def validate_system_architecture(
    data: dict,
):
    architecture = (
        data.get(
            "system_architecture"
        )
    )

    require(
        isinstance(
            architecture,
            dict,
        ),
        "missing system architecture",
    )

    require(
        architecture.get(
            "system_name"
        )
        == (
            "Universal Waste "
            "Management System"
        ),
        "system architecture name mismatch",
    )

    require(
        architecture.get(
            "spacecraft"
        )
        == "Orion",
        "spacecraft mismatch",
    )

    require(
        architecture.get(
            "evidence_class"
        )
        == (
            "NASA_REPORTED_"
            "SYSTEM_ARCHITECTURE"
        ),
        "system architecture evidence "
        "class mismatch",
    )

    functions = (
        architecture.get(
            "functions"
        )
    )

    require(
        isinstance(
            functions,
            dict,
        ),
        "missing UWMS functions",
    )

    required_functions = {
        "urine_collection",
        "fecal_collection",
        "contingency_collection",
    }

    require(
        set(
            functions
        )
        == required_functions,
        "UWMS function set mismatch",
    )

    contingency = (
        functions[
            "contingency_collection"
        ]
    )

    require(
        contingency.get(
            "available"
        )
        is True,
        "contingency collection "
        "availability mismatch",
    )


def validate_sources(
    data: dict,
) -> dict[str, dict]:
    sources = (
        data.get(
            "sources"
        )
    )

    require(
        isinstance(
            sources,
            list,
        ),
        "sources must be a list",
    )

    source_index = (
        index_by_id(
            sources,
            "source_id",
            "source",
        )
    )

    require(
        set(
            source_index
        )
        == EXPECTED_SOURCE_IDS,
        (
            "source ID set mismatch: "
            f"{sorted(source_index)}"
        ),
    )

    for (
        source_id,
        source,
    ) in source_index.items():
        require(
            source.get(
                "agency"
            )
            == "NASA",
            (
                f"{source_id} agency "
                "is not NASA"
            ),
        )

        title = (
            source.get(
                "title"
            )
        )

        require(
            isinstance(
                title,
                str,
            )
            and title.strip(),
            (
                f"{source_id} has "
                "no source title"
            ),
        )

        url = (
            source.get(
                "url"
            )
        )

        require(
            isinstance(
                url,
                str,
            )
            and url.startswith(
                "https://"
            ),
            (
                f"{source_id} does not "
                "have an HTTPS URL"
            ),
        )

        parsed = urlparse(
            url
        )

        hostname = (
            parsed.hostname
            or ""
        ).lower()

        require(
            (
                hostname
                == "nasa.gov"
                or hostname.endswith(
                    ".nasa.gov"
                )
            ),
            (
                f"{source_id} URL is "
                "not on a nasa.gov host: "
                f"{hostname}"
            ),
        )

        publication_date = (
            source.get(
                "publication_date"
            )
        )

        if (
            publication_date
            is not None
            and publication_date
            != "2026"
        ):
            parse_date(
                publication_date,
                (
                    f"{source_id} "
                    "publication date"
                ),
            )

        require(
            isinstance(
                source.get(
                    "source_type"
                ),
                str,
            )
            and source[
                "source_type"
            ].strip(),
            (
                f"{source_id} missing "
                "source type"
            ),
        )

    return source_index


def validate_events(
    data: dict,
    source_index: dict[str, dict],
) -> dict[str, dict]:
    events = (
        data.get(
            "events"
        )
    )

    require(
        isinstance(
            events,
            list,
        ),
        "events must be a list",
    )

    event_index = (
        index_by_id(
            events,
            "event_id",
            "event",
        )
    )

    require(
        set(
            event_index
        )
        == EXPECTED_EVENT_IDS,
        (
            "event ID set mismatch: "
            f"{sorted(event_index)}"
        ),
    )

    require(
        len(
            events
        )
        == 7,
        "expected exactly 7 events",
    )

    source_ids = set(
        source_index
    )

    require_source_resolution(
        events,
        source_ids,
    )

    for event in events:
        event_id = (
            event[
                "event_id"
            ]
        )

        require(
            event.get(
                "thread"
            )
            in EXPECTED_THREADS,
            (
                f"{event_id} references "
                "an invalid operational "
                "thread"
            ),
        )

        require(
            event.get(
                "provenance"
            )
            == "NASA_REPORTED",
            (
                f"{event_id} provenance "
                "is not NASA_REPORTED"
            ),
        )

        require(
            event.get(
                "timestamp_utc"
            )
            is None,
            (
                f"{event_id} fabricates "
                "an exact UTC timestamp"
            ),
        )

        require(
            event.get(
                "time_precision"
            )
            in {
                "RELATIVE_EVENT_ORDER_ONLY",
                "ARTICLE_DATE",
            },
            (
                f"{event_id} contains "
                "unsupported time precision"
            ),
        )

        event_date = (
            event.get(
                "date_utc"
            )
        )

        require(
            isinstance(
                event_date,
                str,
            ),
            (
                f"{event_id} missing "
                "event date"
            ),
        )

        parse_date(
            event_date,
            f"{event_id} date",
        )

        limits = (
            event.get(
                "missionlab_interpretation_limits"
            )
        )

        require(
            isinstance(
                limits,
                list,
            )
            and len(
                limits
            )
            >= 1,
            (
                f"{event_id} missing "
                "interpretation limits"
            ),
        )

    return event_index


def validate_fd1_thread(
    events: dict[str, dict],
):
    fault = (
        events[
            "A2_UWMS_FD1_FAULT_LIGHT"
        ]
    )

    restored = (
        events[
            "A2_UWMS_FD1_RESTORED"
        ]
    )

    require(
        fault[
            "thread"
        ]
        == (
            "flight_day_1_toilet_"
            "fault_and_recovery"
        ),
        "FD1 fault thread mismatch",
    )

    require(
        fault[
            "date_utc"
        ]
        == "2026-04-01",
        "FD1 fault date mismatch",
    )

    require(
        fault[
            "event_type"
        ]
        == "UWMS_FAULT_INDICATION",
        "FD1 fault event type mismatch",
    )

    reported = (
        fault[
            "nasa_reported"
        ]
    )

    require(
        reported.get(
            "root_cause"
        )
        is None,
        "FD1 fault root cause "
        "must remain unresolved",
    )

    require(
        reported.get(
            "root_cause_status"
        )
        == (
            "NOT_PUBLICLY_ESTABLISHED_"
            "IN_CURATED_SOURCE_SET"
        ),
        "FD1 root-cause status mismatch",
    )

    require(
        reported.get(
            "toilet_operational_status_at_initial_report"
        )
        == (
            "FAULT_INDICATION_"
            "UNDER_TROUBLESHOOTING"
        ),
        "FD1 initial operational "
        "status mismatch",
    )

    require(
        restored[
            "date_utc"
        ]
        == "2026-04-02",
        "FD1 restoration update "
        "date mismatch",
    )

    require(
        restored[
            "event_type"
        ]
        == (
            "UWMS_RETURN_TO_"
            "NORMAL_OPERATION"
        ),
        "FD1 restoration event "
        "type mismatch",
    )

    restored_report = (
        restored[
            "nasa_reported"
        ]
    )

    require(
        restored_report.get(
            "crew_ground_coordination"
        )
        is True,
        "FD1 restoration must preserve "
        "crew-ground coordination",
    )

    require(
        restored_report.get(
            "operational_status"
        )
        == (
            "NORMAL_OPERATIONS_"
            "RESTORED"
        ),
        "FD1 restoration status mismatch",
    )

    require(
        restored_report.get(
            "root_cause"
        )
        is None,
        "FD1 restoration must not "
        "invent root cause",
    )


def validate_fd4_thread(
    events: dict[str, dict],
):
    vent = (
        events[
            "A2_UWMS_FD4_"
            "WASTEWATER_VENT_EARLY_END"
        ]
    )

    heater = (
        events[
            "A2_UWMS_FD4_"
            "VENT_HEATER_RESPONSE"
        ]
    )

    solar = (
        events[
            "A2_UWMS_FD4_"
            "SOLAR_POINTING"
        ]
    )

    backup = (
        events[
            "A2_UWMS_FD4_"
            "BACKUP_COLLECTION_POSTURE"
        ]
    )

    postflight = (
        events[
            "A2_UWMS_POSTFLIGHT_"
            "URINE_VENT_INVESTIGATION"
        ]
    )

    expected_thread = (
        "flight_day_4_urine_"
        "wastewater_vent_line_issue"
    )

    for event in [
        vent,
        heater,
        solar,
        backup,
        postflight,
    ]:
        require(
            event[
                "thread"
            ]
            == expected_thread,
            (
                f"{event['event_id']} "
                "FD4 thread mismatch"
            ),
        )

    require(
        vent[
            "date_utc"
        ]
        == "2026-04-04",
        "FD4 vent date mismatch",
    )

    vent_report = (
        vent[
            "nasa_reported"
        ]
    )

    require(
        vent_report.get(
            "tank_full"
        )
        is False,
        "FD4 tank must remain "
        "explicitly NOT full",
    )

    require(
        vent_report.get(
            "toilet_operational"
        )
        is True,
        "FD4 toilet must remain "
        "explicitly operational",
    )

    require(
        vent_report.get(
            "root_cause"
        )
        is None,
        "FD4 vent root cause "
        "must remain unresolved",
    )

    require(
        vent_report.get(
            "root_cause_status"
        )
        == "UNDER_INVESTIGATION",
        "FD4 vent investigation "
        "status mismatch",
    )

    heater_report = (
        heater[
            "nasa_reported"
        ]
    )

    require(
        heater_report.get(
            "confirmed_ice_blockage"
        )
        is False,
        "vent-heater response must not "
        "claim confirmed ice",
    )

    require(
        heater_report.get(
            "other_causes_under_review"
        )
        is True,
        "FD4 evidence must preserve "
        "other causes under review",
    )

    solar_report = (
        solar[
            "nasa_reported"
        ]
    )

    require(
        isinstance(
            solar_report.get(
                "action"
            ),
            str,
        )
        and "Sun"
        in solar_report[
            "action"
        ],
        "Sun-pointing action missing",
    )

    require(
        isinstance(
            solar_report.get(
                "trajectory_impact"
            ),
            str,
        )
        and "did not impact"
        in solar_report[
            "trajectory_impact"
        ],
        "trajectory-impact boundary "
        "missing from Sun-pointing event",
    )

    backup_report = (
        backup[
            "nasa_reported"
        ]
    )

    require(
        backup_report.get(
            "toilet_operational"
        )
        is True,
        "backup posture incorrectly "
        "marks toilet inoperative",
    )

    require(
        backup_report.get(
            "tank_full"
        )
        is False,
        "backup posture incorrectly "
        "marks tank full",
    )

    postflight_report = (
        postflight[
            "nasa_reported"
        ]
    )

    require(
        postflight[
            "date_utc"
        ]
        == "2026-04-20",
        "postflight assessment "
        "date mismatch",
    )

    require(
        postflight_report.get(
            "investigation_status"
        )
        == "ONGOING",
        "postflight investigation "
        "status mismatch",
    )

    require(
        postflight_report.get(
            "hardware_assessment"
        )
        is True,
        "postflight hardware "
        "assessment missing",
    )

    require(
        postflight_report.get(
            "data_review"
        )
        is True,
        "postflight data review missing",
    )


def validate_operational_threads(
    data: dict,
):
    threads = (
        data.get(
            "operational_threads"
        )
    )

    require(
        isinstance(
            threads,
            dict,
        ),
        "missing operational threads",
    )

    require(
        set(
            threads
        )
        == EXPECTED_THREADS,
        "operational thread set mismatch",
    )

    fd1 = (
        threads[
            "flight_day_1_toilet_"
            "fault_and_recovery"
        ]
    )

    require(
        fd1.get(
            "public_outcome"
        )
        == "RESOLVED_IN_FLIGHT",
        "FD1 public outcome mismatch",
    )

    require(
        fd1.get(
            "root_cause_publicly_established"
        )
        is False,
        "FD1 thread incorrectly "
        "claims public root cause",
    )

    require(
        fd1.get(
            "sequence"
        )
        == [
            "Toilet-system checkout",
            "Blinking fault light reported by crew",
            "Mission Control assesses data",
            "Crew and ground troubleshoot",
            "Normal toilet operations restored",
        ],
        "FD1 operational sequence mismatch",
    )

    fd4 = (
        threads[
            "flight_day_4_urine_"
            "wastewater_vent_line_issue"
        ]
    )

    require(
        fd4.get(
            "public_outcome"
        )
        == (
            "MANAGED_IN_FLIGHT_WITH_"
            "POSTFLIGHT_INVESTIGATION"
        ),
        "FD4 public outcome mismatch",
    )

    require(
        fd4.get(
            "root_cause_publicly_established"
        )
        is False,
        "FD4 thread incorrectly "
        "claims public root cause",
    )

    sequence = (
        fd4.get(
            "sequence"
        )
    )

    require(
        isinstance(
            sequence,
            list,
        )
        and len(
            sequence
        )
        == 10,
        "FD4 operational sequence "
        "must contain 10 stages",
    )

    require(
        sequence[
            0
        ]
        == "Wastewater vented overboard",
        "FD4 sequence does not begin "
        "with overboard venting",
    )

    require(
        sequence[
            -1
        ]
        == (
            "Postflight hardware and "
            "data investigation continued"
        ),
        "FD4 sequence does not preserve "
        "postflight investigation",
    )


def validate_boundaries(
    data: dict,
):
    non_equivalences = set(
        data.get(
            "critical_non_equivalences",
            [],
        )
    )

    missing_non_equivalences = (
        REQUIRED_NON_EQUIVALENCES
        - non_equivalences
    )

    require(
        not missing_non_equivalences,
        (
            "missing critical "
            "non-equivalences: "
            f"{sorted(missing_non_equivalences)}"
        ),
    )

    not_reconstructable = set(
        data.get(
            "not_reconstructable_from_current_public_sources",
            [],
        )
    )

    missing_limits = (
        REQUIRED_NOT_RECONSTRUCTABLE
        - not_reconstructable
    )

    require(
        not missing_limits,
        (
            "missing public-evidence "
            "limits: "
            f"{sorted(missing_limits)}"
        ),
    )

    boundary = (
        data.get(
            "evidence_boundary"
        )
    )

    require(
        isinstance(
            boundary,
            dict,
        ),
        "missing evidence-boundary object",
    )

    required_true = [
        "flight_day_1_fault_was_nasa_reported",
        "flight_day_1_normal_operations_restored",
        "flight_day_4_vent_ended_early",
        "flight_day_4_toilet_was_operational",
        "flight_day_4_other_causes_were_under_review",
        "postflight_investigation_was_ongoing",
    ]

    required_false = [
        "flight_day_1_root_cause_publicly_established",
        "flight_day_4_tank_was_full",
        "flight_day_4_ice_was_confirmed",
        "public_record_supports_final_root_cause",
        "missionlab_may_infer_internal_fault_code",
        "missionlab_may_infer_confirmed_ice_blockage",
        "missionlab_may_infer_exact_unreported_event_times",
    ]

    for key in required_true:
        require(
            boundary.get(
                key
            )
            is True,
            (
                "evidence boundary "
                f"expected TRUE: {key}"
            ),
        )

    for key in required_false:
        require(
            boundary.get(
                key
            )
            is False,
            (
                "evidence boundary "
                f"expected FALSE: {key}"
            ),
        )


def validate_cross_thread_logic(
    events: dict[str, dict],
    data: dict,
):
    fd1_fault = (
        events[
            "A2_UWMS_FD1_FAULT_LIGHT"
        ]
    )

    fd1_restored = (
        events[
            "A2_UWMS_FD1_RESTORED"
        ]
    )

    fd4_vent = (
        events[
            "A2_UWMS_FD4_"
            "WASTEWATER_VENT_EARLY_END"
        ]
    )

    postflight = (
        events[
            "A2_UWMS_POSTFLIGHT_"
            "URINE_VENT_INVESTIGATION"
        ]
    )

    fd1_date = parse_date(
        fd1_fault[
            "date_utc"
        ],
        "FD1 fault date",
    )

    restored_date = parse_date(
        fd1_restored[
            "date_utc"
        ],
        "FD1 restoration date",
    )

    fd4_date = parse_date(
        fd4_vent[
            "date_utc"
        ],
        "FD4 vent date",
    )

    postflight_date = parse_date(
        postflight[
            "date_utc"
        ],
        "postflight investigation date",
    )

    require(
        fd1_date
        <= restored_date
        < fd4_date
        < postflight_date,
        "high-level waste-management "
        "chronology is inconsistent",
    )

    require(
        fd1_fault[
            "thread"
        ]
        != fd4_vent[
            "thread"
        ],
        "FD1 fault and FD4 vent issue "
        "must remain separate threads",
    )

    boundary = (
        data[
            "evidence_boundary"
        ]
    )

    require(
        boundary[
            "flight_day_1_root_cause_publicly_established"
        ]
        is False
        and boundary[
            "public_record_supports_final_root_cause"
        ]
        is False,
        "cross-thread root-cause "
        "uncertainty is inconsistent",
    )

    require(
        boundary[
            "flight_day_4_toilet_was_operational"
        ]
        is True
        and boundary[
            "flight_day_4_tank_was_full"
        ]
        is False,
        "FD4 operational-status "
        "relationship is inconsistent",
    )


def main():
    print()
    print(
        "Phase 3B.1 Artemis II "
        "Waste Management Public "
        "Evidence Validation"
    )
    print(
        "=" * 72
    )

    data = load_reference()

    validate_identity(
        data
    )

    print()
    print(
        "Reference identity: PASS"
    )

    validate_scope(
        data
    )

    print(
        "Phase 3B.1 scope: PASS"
    )

    validate_system_architecture(
        data
    )

    print(
        "UWMS architecture model: PASS"
    )

    source_index = (
        validate_sources(
            data
        )
    )

    print(
        "NASA source registry: PASS"
    )
    print(
        "NASA source URLs: PASS"
    )

    event_index = (
        validate_events(
            data,
            source_index,
        )
    )

    print(
        "Event registry: PASS"
    )
    print(
        "Event-source resolution: PASS"
    )
    print(
        "No fabricated exact UTCs: PASS"
    )

    validate_fd1_thread(
        event_index
    )

    print()
    print(
        "Flight Day 1 toilet "
        "fault evidence: PASS"
    )
    print(
        "Flight Day 1 restoration "
        "evidence: PASS"
    )
    print(
        "Flight Day 1 root-cause "
        "boundary: PASS"
    )

    validate_fd4_thread(
        event_index
    )

    print()
    print(
        "Flight Day 4 early vent "
        "termination evidence: PASS"
    )
    print(
        "Flight Day 4 tank-not-full "
        "status: PASS"
    )
    print(
        "Flight Day 4 toilet-operational "
        "status: PASS"
    )
    print(
        "Vent-heater response: PASS"
    )
    print(
        "Ice-confirmation boundary: PASS"
    )
    print(
        "Sun-pointing response: PASS"
    )
    print(
        "Backup collection posture: PASS"
    )
    print(
        "Postflight investigation "
        "status: PASS"
    )

    validate_operational_threads(
        data
    )

    print()
    print(
        "Operational thread "
        "reconstruction: PASS"
    )

    validate_boundaries(
        data
    )

    print(
        "Critical non-equivalences: PASS"
    )
    print(
        "Public evidence limits: PASS"
    )
    print(
        "Evidence-boundary policy: PASS"
    )

    validate_cross_thread_logic(
        event_index,
        data,
    )

    print(
        "Cross-thread chronology: PASS"
    )
    print(
        "FD1 / FD4 issue separation: PASS"
    )

    print()
    print(
        "Validated reference content:"
    )
    print(
        f"  sources: {len(source_index)}"
    )
    print(
        f"  events: {len(event_index)}"
    )
    print(
        "  operational threads: "
        f"{len(EXPECTED_THREADS)}"
    )

    print()
    print(
        "Key evidence boundaries:"
    )
    print(
        "  FD1 blinking fault light "
        "!= identified failed component"
    )
    print(
        "  FD1 normal operations restored "
        "!= publicly established root cause"
    )
    print(
        "  FD4 early vent termination "
        "!= confirmed blockage"
    )
    print(
        "  possible ice "
        "!= confirmed ice"
    )
    print(
        "  vent-heater use "
        "!= proof of ice"
    )
    print(
        "  tank was not full: PASS"
    )
    print(
        "  toilet remained operational: PASS"
    )
    print(
        "  postflight investigation "
        "!= final root cause"
    )
    print(
        "  exact unreported event UTCs "
        "remain unresolved"
    )

    print()
    print(
        "PHASE 3B.1 VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()
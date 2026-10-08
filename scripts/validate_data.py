#!/usr/bin/env python3
"""Lightweight Phase 0 validator with no third-party dependencies."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "seed" / "mission_events.json"
SOURCES_PATH = ROOT / "data" / "sources" / "source_catalog.json"

REQUIRED_EVENT_FIELDS = {
    "id", "timestamp_utc", "mission_phase", "domain", "title", "summary",
    "provenance_class", "source_agency", "source_title", "source_url",
    "mission_criticality", "affected_disciplines"
}
PROVENANCE = {"FLIGHT_DATA", "NASA_REPORTED", "DERIVED", "MODEL", "SYNTHETIC"}
CRITICALITY = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parse_iso8601(value: str) -> None:
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_events(events: list[dict]) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    for i, event in enumerate(events):
        label = f"event[{i}]"
        missing = REQUIRED_EVENT_FIELDS - event.keys()
        if missing:
            errors.append(f"{label}: missing {sorted(missing)}")
        if event.get("id") in ids:
            errors.append(f"{label}: duplicate id {event.get('id')}")
        ids.add(event.get("id"))
        try:
            parse_iso8601(event.get("timestamp_utc", ""))
        except Exception:
            errors.append(f"{label}: invalid timestamp_utc")
        if event.get("provenance_class") not in PROVENANCE:
            errors.append(f"{label}: invalid provenance_class")
        if event.get("mission_criticality") not in CRITICALITY:
            errors.append(f"{label}: invalid mission_criticality")
        if not is_url(event.get("source_url", "")):
            errors.append(f"{label}: invalid source_url")
        if not isinstance(event.get("affected_disciplines"), list):
            errors.append(f"{label}: affected_disciplines must be a list")
    return errors


def validate_sources(sources: list[dict]) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    for i, source in enumerate(sources):
        label = f"source[{i}]"
        for key in ("id", "domain", "title", "agency", "url", "data_type", "planned_use", "cost"):
            if key not in source:
                errors.append(f"{label}: missing {key}")
        if source.get("id") in ids:
            errors.append(f"{label}: duplicate id {source.get('id')}")
        ids.add(source.get("id"))
        if not is_url(source.get("url", "")):
            errors.append(f"{label}: invalid url")
    return errors


def main() -> int:
    events = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    errors = validate_events(events) + validate_sources(sources)
    if errors:
        print("Validation failed:\n")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"OK: {len(events)} mission events and {len(sources)} sources validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "data" / "reference"

INDEX = ROOT / "index.html"
STYLES = ROOT / "styles.css"
APP = ROOT / "app.js"
MISSION_DATA = ROOT / "js" / "mission-data.js"
MISSION_MAP = ROOT / "js" / "mission-map.js"
MISSION_ANALYST = ROOT / "js" / "mission-analyst.js"
ANALYST_AUDIT = ROOT / "scripts" / "validation" / "audit_mission_analyst.mjs"

PERSPECTIVES = REFERENCE / "artemis_ii_mission_control_perspectives.json"
DECISIONS = REFERENCE / "artemis_ii_decision_threads.json"
ANALYST_INDEX = REFERENCE / "artemis_ii_mission_analyst_index.json"
PUBLIC_EXPERIENCE = REFERENCE / "artemis_ii_public_experience.json"


def fail(message: str) -> None:
    raise SystemExit(f"PUBLIC EXPERIENCE V2.7 VALIDATION FAILED: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_text(path: Path) -> str:
    require(path.exists(), f"missing file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    require(bool(text.strip()), f"empty file: {path.relative_to(ROOT)}")
    return text


def load_json(path: Path) -> dict:
    require(path.exists(), f"missing file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def pass_line(label: str) -> None:
    print(f"{label}: PASS")


def main() -> None:
    print()
    print("A2 MissionLab Public Experience V2.7 Validation")
    print("=" * 72)
    print()

    index = load_text(INDEX)
    styles = load_text(STYLES)
    app = load_text(APP)
    mission_data = load_text(MISSION_DATA)
    mission_map = load_text(MISSION_MAP)
    mission_analyst = load_text(MISSION_ANALYST)
    analyst_audit = load_text(ANALYST_AUDIT)

    perspectives = load_json(PERSPECTIVES)
    decisions = load_json(DECISIONS)
    analyst_index = load_json(ANALYST_INDEX)
    public = load_json(PUBLIC_EXPERIENCE)

    require(public.get("dataset_id") == "public_experience_v2_artemis_ii", "dataset identity mismatch")
    require(public.get("mission") == "Artemis II", "mission identity mismatch")
    require(public.get("version") == "2.7.0", "V2.7 version mismatch")
    require(
        public.get("status") == "PUBLIC_EXPERIENCE_V2_7_STABLE_BRIEFING",
        "V2.7 status mismatch",
    )
    pass_line("Public Experience V2.7 dataset identity")

    require(len(perspectives.get("shared_timeline", [])) == 24, "expected 24 mission events")
    require(len(perspectives.get("discipline_registry", [])) == 7, "expected 7 discipline lenses")
    require(len(decisions.get("decision_threads", [])) == 10, "expected 10 decision threads")
    require(len(analyst_index.get("unified_records", [])) == 146, "expected 146 searchable records")
    pass_line("24-event mission timeline")
    pass_line("7 discipline lenses")
    pass_line("10 decision threads")
    pass_line("146 searchable MissionLab records")

    required_html = {
        "Mission-first hero": 'id="mission-map"',
        "Mission scrubber": 'id="mission-scrubber"',
        "Guided mission tour": 'id="tour"',
        "Mission explorer": 'id="explore"',
        "Mission Briefing": 'id="briefing"',
        "Mission Briefing query": 'id="analyst-question"',
        "Mission Briefing results": 'id="chat-log"',
        "Contextual briefing action": 'id="ask-event-button"',
        "Evidence section": 'id="evidence"',
        "Explain/engineering toggle": 'id="experience-mode"',
        "Accessible main landmark": 'id="main-content"',
    }
    for label, token in required_html.items():
        require(token in index, f"missing frontend feature: {label}")
        pass_line(label)

    require("Local MissionLab AI" not in index, "removed Local AI card is still visible")
    require("local-ai-button" not in index, "Local AI preload control is still visible")
    require("Llama 3.2" not in index, "Local model selector is still visible")
    require("general chatbot" in index, "Mission Briefing scope is not explained")
    pass_line("Unreliable Local AI feature removed from public UI")
    pass_line("Mission Briefing replacement scope")

    require("LocalMissionLLM" not in app, "app still imports LocalMissionLLM")
    require("state.localAI" not in app, "app still contains Local AI runtime state")
    require("ensureLocalAIReady" not in app, "app still contains Local AI startup path")
    require("state.analyst.answer(normalized)" in app, "Mission Briefing is not wired to MissionAnalyst")
    require("document.querySelector('#briefing')" in app, "event-to-briefing navigation missing")
    pass_line("Stable Mission Briefing application wiring")
    pass_line("No browser model/WebGPU dependency")

    require("EVENT_PROGRESS" in mission_map, "mission-map event progress layer missing")
    require(
        "A2_PERICYNTHION" in mission_map
        and "A2_ENTRY_INTERFACE" in mission_map
        and "A2_SPLASHDOWN" in mission_map,
        "mission map missing critical anchors",
    )
    require("const STATIC_LABELS = Object.freeze({});" in mission_map, "static map labels returned")
    require("renderLabel(event, target)" not in mission_map, "selected floating map label returned")
    require("EARTH LINE OF SIGHT BLOCKED BY LUNAR BODY" not in mission_map, "long occultation label still clutters map")
    require(".map-selected-label { display: none" in styles, "defensive map-label hiding missing")
    require("SCHEMATIC PATH" in index, "schematic-path evidence disclosure missing")
    pass_line("Decluttered landing mission map")
    pass_line("Mission-map evidence boundary")

    require("min-height: 390px;" in styles, "desktop mission map was not compacted")
    require("position: static;" in styles, "scale note can still overlap the map")
    pass_line("Compact first-fold mission presentation")

    for route in [
        "KNOWN_UNKNOWN",
        "DETERMINISTIC_ELAPSED_TIME",
        "COMMUNICATIONS_SYNTHESIS",
        "SYSTEM_SYNTHESIS",
        "COMPARISON",
        "CHRONOLOGY",
        "MISSION_CONTROL_CONTEXT",
        "MISSION_PHASE_SYNTHESIS",
        "MISSION_ISSUE_SYNTHESIS",
        "MISSION_OVERVIEW",
        "EVIDENCE_BOUNDARY",
    ]:
        require(route in mission_analyst, f"Mission Analyst missing route: {route}")
    pass_line("Mission Briefing evidence routes")

    require(
        "CASES = [" in analyst_audit
        and "MISSION ANALYST EVIDENCE AUDIT PASSED" in analyst_audit
        and "Contextual follow-up" in analyst_audit,
        "Mission Analyst regression audit missing",
    )
    pass_line("Mission Analyst regression audit")

    require(
        "images-assets.nasa.gov/image/art002e021219" in app
        and "images-assets.nasa.gov/image/art002e009280" in app
        and "IMAGE / EVIDENCE BOUNDARY" in app,
        "NASA mission imagery integration missing",
    )
    require(
        "LUNAR_PLAYER_STEPS" in app
        and "lunar-player-orion" in app
        and "DSN blackout begins" in app
        and "DSN reacquisition" in app,
        "interactive lunar encounter player missing",
    )
    pass_line("NASA Artemis II imagery integration")
    pass_line("Interactive lunar encounter player")

    require("data-answer-event" in app and "data-answer-thread" in app, "briefings are not linked back to mission views")
    require(".answer-context-actions" in styles, "briefing context actions styling missing")
    pass_line("Briefing-to-mission navigation")

    combined = "\\n".join([index, app, mission_data, mission_map, mission_analyst])
    for token in [
        "api.openai.com",
        "api.anthropic.com",
        "generativelanguage.googleapis.com",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
    ]:
        require(token not in combined, f"paid/API-backed model dependency found: {token}")
    pass_line("No paid API or backend dependency")

    require("@media (max-width: 900px)" in styles, "tablet breakpoint missing")
    require("@media (max-width: 650px)" in styles, "mobile breakpoint missing")
    require("@media (prefers-reduced-motion: reduce)" in styles, "reduced-motion support missing")
    pass_line("Responsive and reduced-motion support")

    inventory = public.get("validated_inventory", {})
    require(inventory.get("datasets") == 25, "validated dataset count mismatch")
    require(inventory.get("mission_events") == 24, "validated event count mismatch")
    require(inventory.get("decision_threads") == 10, "validated decision-thread count mismatch")
    require(inventory.get("searchable_records") == 146, "validated searchable-record count mismatch")
    pass_line("Validated publication inventory")

    print()
    print("PUBLIC EXPERIENCE V2.7 VALIDATION PASSED")


if __name__ == "__main__":
    main()

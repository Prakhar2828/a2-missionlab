# A2 MissionLab Analyst Guide

## Build the index

```powershell
.\.venv\Scripts\python.exe scripts\analyst\mission_analyst.py build-index
```

## Build the answer interface

```powershell
.\.venv\Scripts\python.exe scripts\analyst\answer_mission_question.py build-interface
```

## Show statistics

```powershell
.\.venv\Scripts\python.exe scripts\analyst\mission_analyst.py stats
```

## Event lookup

```powershell
.\.venv\Scripts\python.exe scripts\analyst\mission_analyst.py event A2_RTC2
```

## Decision-thread lookup

```powershell
.\.venv\Scripts\python.exe scripts\analyst\mission_analyst.py thread RETURN_LINK_ANOMALY_RTC2
```

## Search

```powershell
.\.venv\Scripts\python.exe scripts\analyst\mission_analyst.py search "return link RTC2"
```

## UTC to MET

```powershell
.\.venv\Scripts\python.exe scripts\analyst\mission_analyst.py tool utc-to-met 2026-04-10T02:53:00Z
```

## Ask a mission question

```powershell
.\.venv\Scripts\python.exe scripts\analyst\answer_mission_question.py ask "When was RTC2?"
```

## Supported routes

```text
EVENT_TIME
EVENT
DECISION_THREAD
DECISION_THREAD_CAUSATION
DISCIPLINE
DETERMINISTIC_ELAPSED_TIME
KNOWN_UNKNOWN
SEARCH_SYNTHESIS
```

## Known / unknown behavior

A valid response may be:

```text
UNKNOWN_IN_CURATED_PUBLIC_EVIDENCE
```

The analyst does not invent missing information.

## Optional local LLM handoff

```powershell
.\.venv\Scripts\python.exe scripts\analyst\answer_mission_question.py handoff "What happened with the Artemis II heat shield?" --target local
```

## Optional browser LLM handoff

```powershell
.\.venv\Scripts\python.exe scripts\analyst\answer_mission_question.py handoff "What happened with the Artemis II heat shield?" --target browser
```

Neither handoff executes a model.

## Authority hierarchy

```text
validated evidence
↓
deterministic retrieval
↓
deterministic calculations
↓
citation-first claims
↓
optional presentation model
```

# A2 MissionLab — Public Experience Release Compatibility Note

This filename is retained because historical release validators require it. The repository is no longer treated as a historical overlay package; the current source of truth is the integrated `a2-missionlab` repository on the local `phase-10-quality-recovery` branch.

## Current release profile

The qualified candidate includes:

- the dedicated Mission Explorer, Through Orion's Windows, GNC, Mission Control, PSI, Mission Library, and Technical Report routes;
- evidence-bounded trajectory correction, entry/recovery, space-weather, GNC, and PSI teaching models;
- the 25-moment provenance-labeled Artemis II Windows viewer;
- explicit NASA-reported / MissionLab-derived / modeled / inferred / unknown evidence boundaries;
- responsive and accessibility hardening across the full protected viewport matrix;
- performance, loading, offscreen-animation, and intentional-failure hardening;
- repository-owned social metadata/preview assets;
- Phase P fail-closed release-candidate orchestration;
- Phase Q separate adversarial executive reviews and final repository-state polish.

## Validation

The authoritative public structure check remains:

```powershell
python scripts\validate_public_experience.py
```

The final Phase Q static review/polish contract is:

```powershell
python scripts\validation\validate_phase_q_adversarial_review.py
```

The Windows release installer reruns the complete protected Phase P Edge + Chrome browser gate after applying the Phase Q mutation. No correct historical gate is replaced with a weaker shortcut.

## Evidence boundaries

- NASA reported fact ≠ MissionLab derived result
- modeled quantity ≠ telemetry
- public trajectory product ≠ Orion onboard navigation state
- sequence ≠ causation
- troubleshooting action ≠ confirmed root cause
- discipline relevance ≠ decision ownership
- mission image ≠ exact reconstructed instant unless metadata supports it
- unknown public fact ≠ permission to invent

## Manual/device boundary

The repository does not claim physical iPhone Safari, Android Chrome, tablet hardware, desktop Safari, or real screen-reader sessions unless those checks are separately run and recorded.

## Publishing

No implementation/release installer pushes, merges, deploys GitHub Pages, or changes remote production state. Publication remains an explicit user decision.

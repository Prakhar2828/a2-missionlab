# A2 MissionLab — final public figure audit

The final public layer preserves validated Phase 0–9 engineering artifacts and changes presentation, not the underlying evidence.

## Redesigned public-facing figures

- `navigation-state-products.svg` — separates onboard Orion, ground orbit determination, and public AROW/OEM products and makes the state-product evidence boundary visually explicit.
- `gnc-proximity-loop.svg` — teaches SENSE → ESTIMATE → GUIDE → CONTROL → FIRE → VERIFY in the Artemis II proximity-operations context.
- `esm-propulsion-architecture.svg` — shows one main engine, eight auxiliary engines, and 24 RCS thrusters while explicitly blocking burn-specific engine assignment inference.
- `trajectory-correction-plan-execution.svg` — presents OTC cancellations and RTC execution as a mission-operations story instead of sparse boxes.
- `entry-recovery-sequence.svg` — presents public entry/recovery event anchors without implying a telemetry replay.

## Final visual QA

Every redesigned SVG was rendered at publication scale for a final visual inspection. The pass specifically checked for clipped text, box overrun, label collisions, excessive whitespace, unreadable hierarchy, and evidence-label ambiguity. Final corrections included sensor-label sizing in the navigation figure, two-column spacing in the ESM propulsion figure, and splashdown-label clearance in the entry/recovery figure.

The final rendered set contains no intentionally retained white-background architecture diagram. Quantitative scientific plots that answer real engineering questions remain available in the Technical Report or Mission Library, including heating, atmosphere/Mach/dynamic pressure, ECLSS, communications geometry, and lunar-science reconstruction.

No validated repository artifact is deleted by this overlay.

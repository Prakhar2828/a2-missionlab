# GNC Interaction QA

Phase C removes frame-rate-dependent AUTO timing from the public GNC teaching model.

The experience remains a simplified educational model. It does not claim Orion flight software, proprietary controller gains, private navigation-filter state, or individual thruster firing history.

Production animation consumes real elapsed frame time through fixed 1/120-second physics substeps, with a two-second catch-up safety bound. The AUTO teaching model is expected to capture in 15 to 20 simulation seconds.

Visible progression: INITIAL ERROR, SENSE, ESTIMATE, GUIDE, CONTROL, FIRE, VERIFY, CONVERGENCE. CONVERGENCE is capture-driven rather than timer-driven.

Browser regression tests 60, 30, 15, 5, 2, and 1 FPS-equivalent cadence, requires no more than 0.5 second capture spread, checks deterministic disturbance recovery within 12 seconds, and exercises the real DOM/canvas path, MANUAL THC/RHC input, and disturbance behavior in Chrome and Edge.

The `?gnc-qa=1` clock is regression-only and calls the same `advanceSimulation` path used by production requestAnimationFrame.

Phase C does not alter Mission Explorer source or its dedicated Phase B regression artifacts. The exact Phase B parent commit is guarded before mutation and those files are verified unchanged before commit. Cross-route responsive browser QA is still rerun in Phase C.

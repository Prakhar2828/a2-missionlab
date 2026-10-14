# A2 MissionLab — PSI Interaction QA

## Product boundary

The PSI route is future lunar-landing engineering context. Artemis II did not land on the Moon. The public experience must never present the PSI model as Artemis II telemetry, a landing reconstruction, a flight-qualified analysis, CFD, DSMC, granular-flow prediction, or a certified hazard radius.

## Model contract

- Vehicle altitude changes ideal cone/surface footprint geometry.
- Plume cant changes the plume axis/direction and moves the footprint downrange.
- Plume spread changes angular divergence and footprint width/area.
- Thrust setting changes only the normalized source/loading proxy, not ideal geometry.
- Engine count scales only the aggregate source/loading proxy; plume-plume coupling is not modeled.
- Surface response class changes only the relative erosion-sensitivity proxy.
- Nearby hardware distance changes screening/exposure interpretation, not plume geometry.
- Outputs remain finite across the full control range.

## Browser regression

Run the exact model contract first, then the browser contract:

```powershell
node scripts/validation/validate_psi_model.js
python scripts/validation/validate_psi_regression.py --required
```

On Windows release QA, `--required` expects both Chrome and Edge. On portable CI, the validator uses any available Chromium-family browser unless stricter CI policy is added later.

## Responsive checks

At minimum inspect 320×568, 390×844, phone landscape, tablet portrait, 1280×800, and 1440×900. Confirm:

- no horizontal overflow;
- all controls remain reachable;
- canvas labels remain legible;
- cant and spread remain visually distinct;
- hardware remains visible when distance changes;
- no `NaN`, `undefined`, blank canvas, or clipped controls;
- reduced-motion preference stops continuous particle animation.

## Evidence sources

The route links directly to NASA public PSI material, including NASA Langley 2026 vacuum-chamber testing, the NASA PSI project overview, NASA Advanced Supercomputing PSI modeling context, and the 2026 NASA NTRS PSI testing presentation.

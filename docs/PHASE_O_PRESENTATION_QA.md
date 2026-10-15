# Phase O — README / Social Metadata / Demo Media QA

## Objective

Make the repository and every major public route present MissionLab deliberately when shared, reviewed on GitHub, or opened from a search/social preview, without changing the completed Phase N runtime, evidence, accessibility, responsive, performance, or failure-state contracts.

## Canonical deployment base

Phase O uses the GitHub Pages project-site base:

`https://prakhar2828.github.io/a2-missionlab/`

The repository has Pages enabled and the tracked Pages workflow deploys the repository root from `main`. Phase O does not push, deploy, or modify remote GitHub settings.

## Major routes

The Phase O metadata contract covers exactly eight public routes:

1. `index.html`
2. `mission.html`
3. `windows.html`
4. `gnc.html`
5. `mission-control.html`
6. `psi.html`
7. `library.html`
8. `technical-report.html`

Each route must expose exactly one deliberate:

- document title
- meta description
- canonical URL
- Open Graph site name, title, description, type, URL, image, image dimensions, and image alt text
- Twitter/X large-card title, description, and image
- SVG and ICO favicon link

## Social preview ownership

All routes use one repository-owned social preview image:

`docs/assets/social/a2-missionlab-social-preview.png`

Contract:

- format: PNG
- dimensions: 1200 × 630
- source artwork retained as `docs/assets/social/a2-missionlab-social-preview.svg`
- no third-party image host required for the link-unfurl asset
- wording describes MissionLab as a public-data engineering reconstruction, not an official NASA product

## README hiring-product contract

`README.md` must communicate, without overselling:

- what MissionLab is
- why it exists
- actual public mission data/evidence used
- mission experiences
- architecture
- technical challenges
- simulation methodology and fidelity boundaries
- evidence discipline
- selected results
- validation and browser boundaries
- demo media / live routes
- local run instructions
- zero-cost architecture
- limitations
- project status and documentation entry points

The README retains the historical publication-completion phrase required by the protected Phase 9 release validator while adding the later quality-recovery/Phase O context.

## Validation

Dedicated Phase O validation consists of:

- `scripts/validation/validate_phase_o_presentation.py`
  - exact metadata set and canonical mapping
  - social-image dimensions and ownership
  - README section/content contract
  - CI/public-validator integration
  - no third-party Open Graph image
- `scripts/validation/phase_o_presentation_regression.html`
  - browser-served metadata checks for all eight routes
- `scripts/validation/validate_phase_o_regression.py`
  - tokenized localhost completion handshake
  - Windows release mode requires Edge + Chrome
  - browser harness checks 96 metadata/presentation assertions per browser across eight routes (192 total assertions in Windows release mode)
  - package-build convenience mode may run one explicit Chromium-family binary and is not claimed as the Windows release gate

## Protected behavior

Phase O does not change:

- mission chronology or public evidence products
- mission models or simulation behavior
- Mission Explorer / Windows / GNC / Mission Control interactions
- PSI / trajectory / space-weather / entry models
- typography / route visual identity
- accessibility / responsive behavior
- Phase N performance, lazy-loading, animation ownership, or failure states

All protected regressions remain mandatory in the Windows installer before the Phase O engineering-log closure is appended.

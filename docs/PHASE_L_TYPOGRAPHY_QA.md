# Phase L — Typography + Visual Quality QA Contract

## Scope

Phase L replaces the unresolved `Inter` request with a deliberate zero-cost system-font architecture and normalizes the most compressed display typography without changing route identity, mission evidence, simulations, or protected interaction geometry.

## Product contract

- No remote font service, paid font, public-app font binary, or locally-installed-font assumption is required.
- The primary sans stack starts with `system-ui` and includes native platform fallbacks.
- Monospace technical text uses a deliberate system monospace stack.
- Mathematical equations retain a distinct serif voice.
- Major display headings preserve cinematic scale while avoiding fragile sub-0.86 line heights and extreme negative tracking.
- Mission, Windows, GNC, Mission Control, PSI, Library, Report, and the homepage retain their route-specific CSS and visual identity.
- Engineering readouts use tabular lining numerals where scanning stability matters.
- Long-form report/library prose keeps a readable rhythm and the Technical Report print serif contract remains intact.
- Phase L must not modify mission data, evidence wording, model behavior, canvas logic, interaction state, or protected F–K regressions.


## Font dependency boundary

The Phase L contract is about the **public application dependency graph**, not every file that may exist under a developer checkout. Local development environments such as `.venv` may contain third-party package font resources. Those files are not part of the public typography architecture unless a served HTML/CSS asset references them. Static validation therefore scans the public routes and top-level runtime CSS for font-binary references instead of asserting that no `.ttf`, `.otf`, `.woff`, or `.woff2` file can exist anywhere beneath the repository root.

## Release gates

1. `scripts/validation/validate_phase_l_typography.py`
2. `scripts/validation/validate_phase_l_regression.py --required`
3. Existing public/text/release validators
4. Protected Mission Explorer, Windows, GNC, Mission Control, PSI, Trajectory, Space Weather, Entry browser regressions
5. Global Chrome/Edge responsive QA

## Browser typography invariants

Across representative phone portrait, phone landscape, tablet, and desktop widths on all eight public routes:

- `typography.css` is the final stylesheet in cascade order.
- computed body font family does not request `Inter`.
- page body text remains at least 16 px.
- the primary H1 exists, stays inside the viewport, and retains a line-height/font-size ratio of at least 0.86.
- H1 absolute negative tracking does not exceed 5.5% of its computed font size.
- section display headings, when present, retain a line-height/font-size ratio of at least 0.92.
- no unintended horizontal overflow is introduced.

## Evidence and rollback

Typography is presentation only. Evidence taxonomy and quantitative claims are unchanged. The release installer must create a timestamped Phase L safety branch before mutation, use an exact changed-file allowlist, fail closed on any validation error, reset to the immutable Phase K documentation commit on failure, leave the worktree clean, commit locally only, and perform no push.

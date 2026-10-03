# Week 7 Phase 2–5 Stabilization Patch

This package is the corrected post-P0 Phase 2–5 baseline.

## Verified in this environment

- P0 authoritative machine gate: 100/100
- Phase 2–5 representative root-cause gate: 73/73

## Corrections made after the Windows local gate report

- Restored P0 Career Twin session-auth evidence and explicit credential inclusion.
- Restored functional Escape handling and keyboard focus trapping in the opportunity intelligence drawer.
- Restored the exact salary sanitizer required by P0 #81 in OpportunitiesClient.
- Removed the invalid server-component references to client state from Home page.
- Imported and applied GoalSchema correctly in the Home client.
- Bound expandedExperience to an actual resume experience accordion.
- Removed the unused API parseError helper and unused frontend imports.
- Corrected React effect/state patterns in Career Twin, Career Plan, Settings and ThemeToggle.
- Added Playwright and jsdom dev dependencies.
- Corrected the PowerShell local gate so native command failures cannot be reported as PASS.
- Removed the obsolete verifier SyntaxWarning source.

## Important verification boundary

The 73/73 Phase 2–5 gate is a representative root-cause gate. It is not evidence that all 900 individual P1–P4 audit records are independently VERIFIED. The Week 7 tracker must not be promoted to 1000/1000 until item-level evidence exists.

The Windows local gate must still pass typecheck, lint, tests and production build on the target machine after `npm install` resolves the updated dependency manifest.

## V4 test isolation corrections
- `frontend/lib/formatters.ts` now treats null/undefined/blank currency inputs as undisclosed instead of coercing null to `₹0`.
- `frontend/vitest.config.ts` excludes `e2e/**` so Vitest does not execute Playwright tests.
- `frontend/package.json` exposes a separate `test:e2e` command for the Playwright harness.
- Formatter unit coverage includes null, undefined, and blank currency inputs.


## V5 test correction
- Corrected the formatter contract test: `en-IN` must produce Indian grouping (`₹1,00,000`), while `en-US` is explicitly tested as `$100,000`.
- The implementation remains locale-aware; the prior V4 failure was a test expectation mismatch, not a reason to change the product formatter to `en-US`.

# Week 7 Audit Verification Workflow

## Status Lifecycle

OPEN
- Audit item exists and has not entered implementation.
- No resolution claim may be made.

IN PROGRESS
- Investigation or implementation has started.
- Item remains unresolved.

FIXED
- Implementation addressing the audit defect is complete.
- Targeted checks relevant to the defect pass.
- Fix commit/reference is recorded.
- Evidence is recorded.
- FIXED is not final acceptance.

VERIFIED
- Independent verification reproduces the acceptance condition.
- Required regression checks pass.
- Evidence is recorded.
- Verification timestamp is recorded.
- Verifier is recorded.

## Mandatory Transition

OPEN -> IN PROGRESS -> FIXED -> VERIFIED

Skipping states is prohibited.

## Reopening

If verification fails:
VERIFIED -> IN PROGRESS

If a later regression is discovered:
VERIFIED -> IN PROGRESS

## FIXED Requirements

FixCommit must identify the implementation commit or exact change.
Evidence must identify the verification command, test, screenshot, trace,
log, API response, or other reproducible proof.

## VERIFIED Requirements

FixCommit must be present.
Evidence must be present.
VerifiedAt must be present.
Verifier must be present.

Verification must be independent of the implementation claim.
A successful compilation/build alone does not verify a functional defect.
A representative test does not verify unrelated audit items.
An audit item is verified only against its own acceptance condition.

## Evidence Standard

Every VERIFIED item must provide:
1. Exact defect addressed.
2. Exact acceptance condition.
3. Verification method.
4. Verification result.
5. Reproducible evidence reference.

## Regression Rule

A fix is not considered stable if it introduces a regression in an
existing automated test, build, typecheck, security check, or relevant
user journey.

## Final Gate

Week 7 cannot be declared complete while:
- any P0/P1/P2/P3/P4 item remains OPEN;
- any item remains IN PROGRESS;
- any item remains FIXED but not VERIFIED;
- any VERIFIED item lacks required evidence;
- independent final verification has not passed.

# Week 7 — Phase 6 Product Implementation

Phase 6 is the connected product roadmap that sits on top of the P0–P4 remediation. This package adds a durable workspace layer, account authentication, product-wide persistence and the cross-workstream UI/API surfaces needed to connect the career operating system.

## Implemented product surfaces

| # | Workstream | Implementation in this package |
|---|---|---|
| 1 | Unified Application Shell | Shared `AppShell`, route-aware navigation, mobile drawer, keyboard handling, theme control, skip link and breadcrumb context. |
| 2 | Authentication & Authorization | Account creation, login, logout, signed session cookie, password hashing, session ownership checks and protected app routes. |
| 3 | Persistent Candidate Identity + Career Twin | Stable candidate UUID, persistent Career Twin hydration/update flow, career memory and timeline integration retained. |
| 4 | Client/Server State Architecture | SQLite-backed workspace store, centralized `apiClient`, persistence events and shared async workspace utilities. |
| 5 | Source Control Center | Provider catalog UI/API, persisted provider verification state and user-specific enable/disable preferences. |
| 6 | Canonical Job Identity & Provenance | Existing canonical job pipeline retained; saved-job records preserve source/job IDs, URLs, source records and capture metadata. |
| 7 | Professional Search & Filter Engine | Existing live search, role/location/salary/work-mode/skills filters, sorting, pagination and URL state retained. |
| 8 | Provider Orchestration | Existing concurrent provider fleet, cooldown/failure isolation and adaptive query expansion retained; user provider preferences are now passed into orchestration. |
| 9 | Opportunity Intelligence 2.0 | Existing Career Twin match, skill gaps, salary intelligence, confidence and explanation pipeline retained. |
| 10 | Real Dashboard | Dashboard consumes persisted workspace applications, saved/canonical opportunities, Career Twin skills and activity. |
| 11 | Companies Intelligence | Company view now derives persisted role presence, locations and observed matched skills. |
| 12 | Applications CRM | Persistent application records with status lifecycle and per-application packet creation. |
| 13 | Application Packets | Versioned packet records with resume/cover/evidence state and explicit human-submission requirement. |
| 14 | Adaptive Interview Engine | Persistent interview history, multiple modes, answer review, adaptive scoring feedback and progress history. |
| 15 | Adaptive Career Plan | Durable goals/tasks tied to Career Twin strengths and skill gaps. |
| 16 | Saved Jobs + Browser Clipper | Persistent saved jobs plus validated HTTP(S) browser-clip capture workflow. |
| 17 | Safe Application Assistant | Packet generation is supported while external submission remains explicitly user-controlled. |
| 18 | Market Intelligence | Search snapshots are persisted separately from saved jobs and exposed in a Market Intelligence surface. |
| 19 | Alerts & Automation | Persistent saved-search/automation definitions with hourly/daily/weekly frequency controls. |
| 20 | Networking CRM | Durable contacts, relationship status and notes. |
| 21 | Resume/Document Intelligence Hub | Existing resume parsing/ATS/rewrite pipeline retained; workspace now has a durable document/packet model for future document versions. |
| 22 | Agentic Intelligence Fabric 2.0 | Existing LangGraph orchestration, validation and Career Twin feedback loop retained; completed runs are now persisted as agent-run records. |
| 23 | API Contracts, Typing & Security | Pydantic request validation, centralized API client, CSRF/idempotency/request IDs and session ownership boundaries retained and extended. |
| 24 | Accessibility, Mobile, Performance & PWA | Existing accessibility/focus/mobile implementation retained; Web Vitals and PWA manifest remain enabled. |
| 25 | Automated Testing | Existing backend/frontend/unit/E2E infrastructure retained. This implementation pass intentionally did **not** execute the test suite. |
| 26 | CI/CD, Production, Observability & Portability | Existing CI/build/telemetry foundations retained; Phase 6 persistence is source-only and environment-configurable. |

## Persistence model

`backend/services/workspace_store.py` uses SQLite with per-candidate record isolation. Records are grouped by entity (`saved-jobs`, `applications`, `companies`, `interviews`, `career-plan`, `networking`, `alerts`, `packets`, `documents`, `market`, `agent-runs`, `settings`) and audited through an append-only activity event table.

## Authentication model

`backend/api/session.py` now supports:

- Sign-up
- Login
- Logout
- Account lookup
- Signed candidate session cookies
- Per-account candidate UUIDs
- Password hashing using Python `hashlib.scrypt`

## Important verification boundary

This package implements the Phase 6 product surfaces and wiring but does **not** claim that every Phase 6 acceptance condition has been independently tested in a production deployment. Test execution, E2E execution, accessibility scans, mobile runs, performance runs and deployment verification remain explicit final-gate activities.

## External integration layer added in the final Phase 6 pass

The final Phase 6 integration pass adds a dedicated external-integration boundary so third-party services never become hard dependencies of the CareerPilot core.

| Integration workstream | Delivered capability |
|---|---|
| Notion | OAuth, encrypted token storage, parent-page targeting, page creation and block append. |
| Google Workspace | OAuth, Gmail career-message import, Calendar/Drive synchronization and Contacts → Networking sync. |
| Microsoft 365 | OAuth with Microsoft Graph, Mail/Calendar/OneDrive synchronization and Contacts → Networking sync. |
| GitHub | OAuth and real profile/repository evidence synchronization. |
| GitLab | OAuth and real profile/project evidence synchronization. |
| Browser job clipper | Chromium Manifest V3 extension with revocable candidate-scoped clip tokens. |
| Official job APIs | USAJOBS and The Muse adapters using the existing canonical `JobSource` contract. |
| Learning | Unified learning-gap destination layer with official provider URLs and workspace progress tracking. |
| Networking | Google/Microsoft contacts flow into the existing Networking CRM. |
| Interviews + Career Inbox | Calendar events flow into Interviews; Gmail/Microsoft career mail is normalized into a single Career Inbox. |

All OAuth states are candidate-bound and short-lived. Access/refresh tokens are encrypted at rest. External failures are isolated and surfaced without blocking core CareerPilot search, Career Twin or workspace features.

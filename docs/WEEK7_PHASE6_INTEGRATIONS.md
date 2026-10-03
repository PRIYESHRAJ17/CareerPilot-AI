# CareerPilot AI — Week 7 Phase 6 Integrations

This extension adds the ten integration workstreams to the Week 7 product layer without making external accounts mandatory for the core application.

## 1. Notion

OAuth connection, encrypted token storage, page creation and block append APIs are implemented. CareerPilot stores the user's selected parent page locally in the browser and can create career notes under that page.

## 2. Google Workspace

OAuth connection covers Gmail read access, Calendar read access, Drive file access and Contacts read access. Synchronization maps events to Interviews, files to Documents, and contacts to Networking. Career Inbox imports career-relevant mail metadata only.

Google scopes are intentionally narrow for the current read/sync workflow. Production publishing still requires completing the provider's OAuth consent/review requirements where applicable.

## 3. Microsoft 365

Microsoft identity platform authorization code flow is implemented for Graph Mail, Calendar, Files and Contacts read access. Sync maps those objects into CareerPilot's interview/document/networking workspace.

## 4. GitHub + GitLab

OAuth connections and read-only technical evidence sync are implemented. CareerPilot stores profile/repository/project evidence as candidate-scoped workspace records so it can become supporting evidence for the Career Twin without fabricating resume claims.

## 5. Browser Job Clipper

A Manifest V3 Chromium extension is bundled in `browser-extension/`. It captures the active career page and sends the original URL plus visible metadata to the CareerPilot clipper endpoint. Tokens are revocable and stored hashed server-side.

## 6. Additional Official Job APIs

Two additional adapters are included:

- USAJOBS official Search API. Requires `USAJOBS_API_KEY` and `USAJOBS_USER_AGENT`.
- The Muse public Jobs API. Anonymous testing is supported; `THEMUSE_API_KEY` can be configured for registered API access and production rate limits.

They plug into the same canonical JobSource contract as Adzuna, Jooble and the verified ATS fleet.

## 7. Learning Hub

A unified learning layer maps Career Twin skills/gaps to official or established learning destinations: Microsoft Learn, AWS Skill Builder, GitHub Skills, Google Cloud Skills Boost, freeCodeCamp, Coursera and edX. The hub deliberately uses provider links instead of inventing undocumented private APIs.

Learning progress is persisted in the candidate workspace.

## 8. Networking CRM Integration

Google Contacts and Microsoft Graph Contacts synchronize into the existing Networking CRM. The same candidate-scoped record model is used, so imported contacts can carry notes and follow-ups without creating duplicate global users.

## 9. Interview / Meeting Integration

Google Calendar and Microsoft Calendar events synchronize into the existing Interviews workspace. The integration is intentionally read-first: CareerPilot can enrich interview preparation and history without silently modifying a user's calendar.

## 10. Career Inbox

Gmail and Microsoft mail metadata is normalized into a single Career Inbox. A deterministic classifier routes messages into interview, offer, rejection, application, recruiter and career categories. Full email bodies are not persisted by the inbox sync endpoint.

## Security and failure isolation

- OAuth state is bound to the authenticated candidate and expires after ten minutes.
- Access and refresh tokens are encrypted at rest using Fernet; production should set `CAREERPILOT_TOKEN_ENCRYPTION_KEY`.
- Each external integration fails independently. A disconnected provider does not block core CareerPilot search or workspace features.
- The browser clipper uses a separate revocable token instead of bypassing the user's CareerPilot session.
- External providers are never treated as live unless their own credentials/configuration and API response allow a successful call.

## Required server configuration

See `.env.example`. Each provider must have its own OAuth app registration and redirect URI configured before its Connect button becomes available.

Default redirect pattern:

`{CAREERPILOT_API_PUBLIC_URL}/integrations/oauth/{provider}/callback`

# TalentNexus — Codex Application Context

**Source:** MatriX TalentNexus Final Hackathon deck, version 6  
**Purpose:** Product and implementation context for generating the TalentNexus hackathon MVP with Codex.  
**Status:** A build brief derived from the deck. The sprint dates and impact numbers below are planned targets, not evidence of completed work or measured outcomes.

## 1. Product summary

TalentNexus is an AI-assisted talent intelligence and decision-support application. It brings together authorized, synthetic talent information from multiple people systems and presents an evidence-backed employee or team view for People Partners and managers. Its purpose is to reduce manual preparation for talent reviews and manager 1:1s while making data scope, sources, dates, and gaps visible.

The product is **advisory only**. It must not make, trigger, or recommend an automated employment action. A human remains responsible for interpreting information and making decisions.

## 2. Problem and intended outcomes

Talent information is distributed across five or more portals and exports, including CompanyDeavor, CompanyFulcrum, CompanyFusion, learning, rewards, the Promotion Portal, and the People Partner Portal. People Partners currently reconstruct employee histories manually; managers may enter conversations without a complete, authorized picture.

The deck sets these intended outcomes:

- Reduce People Partner preparation for one employee review from an estimated 45 minutes to under 5 minutes.
- Reduce manager preparation for a team-member 1:1 from an estimated 30 minutes to under 2 minutes.
- Show zero restricted fields to managers, verified by access tests.
- Link every insight to its supporting source and date.

Treat these as **hypotheses to measure**, not achieved results. The demo should time three representative tasks and show the observed values and method.

## 3. Users and permissions

### People Partner (PP)

- Can search and view employee context that the PP is authorized to access.
- Can review an employee 360 view, evidence-backed strengths and development opportunities, contradictions, caveats, and role-appropriate strategic consulting suggestions.
- Can access permitted programme and check-in information only where the data is authorized for this role.

### Manager

- Can view only employees on their own team and context explicitly approved for manager sharing.
- Can use scoped team-member Q&A and conversation guidance for a 1:1.
- Must never receive compensation/pay, talent tags, or private check-ins through the manager UI, API, retrieval layer, logs, prompts, or agent context.

### Authorization rules

- Enforce role and team scope on the server before retrieval and before data is passed to any model or agent. Do not rely on UI hiding alone.
- Use an explicit allowlist of manager-shareable fields. Deny by default when a field's classification or sharing status is unknown.
- Prevent cross-team employee lookup by managers. Return a generic access-denied/not-found response without revealing whether a restricted employee exists.
- Keep PP-only data out of manager agent context, tool results, citations, and generated summaries.
- Provide a safe, auditable way to inspect which fields and sources were included in a response, without logging sensitive field values.

## 4. MVP user journeys

### People Partner: employee review

1. Sign in to the local demo using a seeded PP role.
2. Search/select one of the 30 synthetic employee profiles.
3. Open the employee 360 view with profile summary, performance, career history, skills, allocation, permitted programme data, and relevant development context.
4. Review generated insights, strengths, opportunities, contradictions, suggestions, caveats, and source references.
5. Ask a scoped follow-up question. The answer must cite evidence and state when evidence is missing or conflicting.

### Manager: prepare a 1:1

1. Sign in using a seeded manager role.
2. See only the manager's own synthetic team.
3. Select a team member and view only manager-shareable context.
4. Review conversation guidance and open-ended prompts based on explicitly stated aspirations, needs, or commitments.
5. Ask a scoped team Q&A question. The assistant must abstain when the context is missing and must not infer undisclosed aspirations or expose restricted data.

### Shared experience

- Show data freshness/as-of dates and source provenance for all displayed facts and generated insights.
- Clearly distinguish source facts, calculated metrics, and AI-generated interpretation.
- Show missing or conflicting evidence as a caveat; never silently fill gaps with invented facts.
- Include an advisory-only notice near generated suggestions.

## 5. Agent responsibilities and orchestration

The deck proposes two cooperating agents on CompanyseAI.AgentMesh (spelling as shown in the deck). Implement the agent boundary behind an adapter so a local mock can power the MVP until AgentMesh access, model, and interfaces are confirmed.

### Talent Insights Agent

- Retrieve authorized performance, career, skills, allocation, and permitted programme data.
- Call deterministic, read-only metric functions for calculations; do not ask the LLM to do arithmetic that a tool can perform.
- Identify evidence-backed strengths, development opportunities, data gaps, and contradictions.
- Produce role-specific suggestions with caveats and citations.

### Talent Pulse Agent

- Retrieve authorized check-ins and approved shareable employee context for the active role.
- Extract only explicitly stated aspirations, development needs, and commitments.
- Suggest open-ended conversation prompts grounded in those statements.
- Abstain when relevant information is missing or cannot be shared with the current role.

### Request flow

1. Authenticate user and resolve role/team scope.
2. Apply server-side authorization and field allowlists.
3. Retrieve only authorized records and attach provenance/as-of metadata.
4. Invoke read-only metric tools where needed.
5. Run one or both agents with the minimum necessary context.
6. Validate output schema, citations, role permissions, and abstention conditions.
7. Return the answer with sources, dates, caveats, and advisory-only framing.

Use structured outputs and validate every agent response before rendering. A failed permission, citation, or schema check should suppress the affected content and return a safe explanation.

## 6. Data and evidence model

The deck specifies **30 synthetic employee profiles** and **16 datasets**, stored in JSON or SQLite for the demo. Use synthetic records only. Do not connect to live HR systems or use real employee data for this MVP.

Candidate source areas named in the deck include performance, career, skills, allocation, learning, rewards, promotion, People Partner portal/export data, and permitted programme/check-in context. The exact mapping of the 16 datasets to source portals is not confirmed; keep it in a configurable source registry and document the seeded mapping.

Each source fact should retain at minimum:

- `employee_id` and a stable record identifier
- `source_system` and `source_record_id`
- `field` or typed fact category
- value (with sensitivity classification)
- `as_of` date and, where available, source update date
- `share_policy` or role allowlist
- optional confidence/quality metadata for the source record

Each displayed or generated insight should retain:

- insight text and type (fact, metric, interpretation, suggestion, caveat)
- supporting source references and dates
- calculation/tool name when derived
- role visibility
- generated timestamp and model/agent identifier when applicable
- validation status

Never fabricate a source, date, metric, aspiration, or employee attribute. Treat empty, stale, ambiguous, or contradictory data explicitly.

## 7. Suggested implementation shape

The deck identifies AgentMesh plus an approved tool-calling LLM, read-only Python/native tools, JSON/SQLite, and React or an approved low-code interface. It does not confirm a specific model, deployment target, portal API, or AgentMesh interface.

For a self-contained local MVP, use these defaults unless the repository already establishes another stack:

- React UI for the PP and Manager experiences.
- A small Python API/service for authentication demo roles, authorization, retrieval, deterministic metrics, and agent orchestration.
- SQLite or JSON fixtures for the 30 synthetic profiles and 16 datasets.
- A provider/agent adapter with a deterministic mock implementation first; keep the future AgentMesh and approved LLM integration replaceable.
- Localhost execution and no external HR-system calls.

Keep storage access read-only from the application workflows. Any data seeding/reset command must be clearly separate from runtime APIs. Add schema validation at ingestion and response boundaries. Keep secrets/configuration out of source control.

## 8. Core screens

1. **Role-aware landing page:** current demo role and accessible team/profile list.
2. **Employee 360:** profile summary, sections by source/data domain, as-of dates, evidence-linked insights, contradictions, missing data, and caveats.
3. **Manager team view:** own-team list and manager-shareable profile summaries only.
4. **Scoped Q&A/conversation panel:** response, source/date citations, caveats, and abstention message.
5. **To-do/conversation guidance:** suggested open-ended prompts and commitments grounded in approved information.
6. **Demo measurement panel:** three timed tasks with manual and AI-assisted durations, observed result, and task notes. Label all sample values as illustrative until measured.

## 9. Safety, privacy, and reliability requirements

- No automatic hiring, promotion, compensation, performance-rating, termination, or other employment decisions/actions.
- Never surface pay, talent tags, or private check-ins to manager users or manager agents.
- No role escalation via request parameters, client-side state, prompt text, guessed employee IDs, or direct API calls.
- Do not treat model output as permission to access data. Authorization is deterministic and outside the model.
- Do not infer sensitive personal traits or unsupported conclusions. Keep generated language job-related, evidence-linked, and qualified.
- Abstain if evidence is absent, inaccessible, stale beyond configured rules, or materially contradictory.
- Avoid writing sensitive source content into logs, analytics, error messages, or test snapshots.
- Show citations and source dates for every factual insight; label uncited generative text as unavailable and do not display it as factual output.
- Use synthetic data for all demos and screenshots.

## 10. Acceptance criteria and test plan

### P0 hero cases (5)

The deck says the five P0 cases comprise four hero use cases plus missing-data abstention. Use this proposed breakdown as an implementation interpretation and allow the project owner to adjust it:

1. PP can retrieve an authorized employee review with source-linked insights.
2. PP can ask a follow-up question and receive a scoped, evidence-backed answer.
3. Manager can prepare for a 1:1 for a member of their own team using shareable context.
4. Manager can ask team-scoped Q&A and receive appropriate conversation prompts.
5. Either role gets a safe abstention when required context is missing; no fabricated details are returned.

### Mandatory access/privacy tests

- Manager cannot see pay, talent tags, or private check-ins in UI, API responses, model inputs, citations, logs, or exports.
- Manager cannot access an employee outside their team, including by changing IDs or calling APIs directly.
- PP-only fields never enter manager retrieval results or agent prompts.
- Unknown field classification fails closed.
- UI restrictions and server-side authorization agree.

### Other quality checks

- Every fact and insight has valid source references and an as-of date.
- Deterministic metric calculations match known fixture values.
- Conflicting or stale data produces a visible caveat.
- Invalid agent schema, missing citations, or permission validation failures suppress unsafe output.
- Role switching in the demo clears prior role-specific state and results.
- Run the deck's planned **18 test cases** (the deck does not enumerate them; create a documented suite covering the cases above and core UI, data, and failure paths).
- Run the full demo three consecutive times without a P0 failure before calling it ready.

### Measurement checks

Time three representative manual and AI-assisted tasks and record the method, task, and observed durations. Report whether the targets (<5 minutes for PP review preparation and <2 minutes for manager 1:1 preparation) were met; do not claim target attainment without observations.

## 11. Demo readiness and delivery

The deck's stated plan targets an integrated prototype by 28 November and MVP freeze on 30 November 2026. These are schedule targets from the source deck, not a claim that the milestones have been completed. Later jury rounds are described as subject to selection.

A jury-ready demo should include:

- 30/30 synthetic profiles linked to the fixture datasets.
- The two role-specific experiences and two agent responsibilities.
- Visible provenance, as-of dates, caveats, and authorization behavior.
- Five P0 cases and all access/privacy tests passing.
- Three consecutive successful demo runs.
- No automated HR actions.

## 12. Codex implementation instructions

When using this document to generate code:

1. Inspect the existing repository and follow its conventions before changing files.
2. If no app exists, create a small local MVP using the suggested implementation defaults in Section 7.
3. Build the data model, seeded synthetic fixtures, server-side access control, and tests before connecting agent output to the UI.
4. Implement mock agents and deterministic tools first. Keep AgentMesh/LLM integration behind interfaces because its access, model, and API details are not confirmed in the deck.
5. Ensure role filtering happens before retrieval and model invocation; add tests that inspect the actual model/agent input.
6. Keep outputs structured and cite only source records actually retrieved for the current user.
7. Include a README with setup, run, test, seeded demo accounts, data-safety boundaries, architecture, and the exact steps needed to replace the mock adapter with an approved AgentMesh integration.
8. Do not claim connection to CompanyDeavor, CompanyFulcrum, CompanyFusion, production HR data, or AgentMesh unless those interfaces and credentials are provided and verified.
9. Label all unmeasured impact figures and illustrative demo data accurately.

## 13. Open items from the deck

Confirm these before any real integration or production deployment:

- Approved LLM/model and AgentMesh interface, authentication, tool protocol, and deployment approach.
- Mapping and ownership of the 16 datasets and portal/export schemas.
- Field-level classifications and approved manager-shareable rules.
- HR rules and definitions for metrics, strengths, opportunities, and stale-data handling.
- Identity provider, manager-to-team mapping, audit requirements, retention, and data governance.
- Whether a supported low-code UI is required instead of React.
- The exact four hero cases, since the deck does not list them individually.

Until confirmed, keep the app local, synthetic-data-only, mock-backed, and advisory.

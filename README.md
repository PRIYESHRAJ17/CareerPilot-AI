# CareerPilot AI

CareerPilot AI is an intelligent career operating system designed to help candidates discover, evaluate, understand, and act on job opportunities.

Instead of functioning as a basic job-search interface, CareerPilot combines:

- Candidate intelligence
- Opportunity intelligence
- Resume intelligence
- ATS analysis
- Evidence-first resume rewriting
- Local LLM reasoning
- Agentic orchestration
- Shared workflow state
- Deterministic tools
- Validation and safety
- Personalized career recommendations

The project is being developed as an 8-week Agentic AI internship project, with the long-term goal of becoming a stateful and personalized career intelligence system.

---

## Project Status

### Week 1 — Foundation ✅ Complete

Established the core CareerPilot architecture and data foundations.

Implemented:

- Next.js frontend
- FastAPI backend
- Candidate profile schema
- Career goal representation
- Job-source abstraction
- Universal job-source connector interface
- Central job-source registry
- Environment configuration
- Initial candidate/job workflow
- Frontend/backend integration foundation

The architecture is designed to support additional job sources and intelligence services without rewriting the core system.

---

### Week 2 — Opportunity Intelligence ✅ Complete

CareerPilot was expanded into a multi-source job discovery and opportunity intelligence platform.

#### Job Sources

- Adzuna
- Jooble

#### Implemented

- Job aggregation
- Cross-source deduplication
- Canonical opportunity model
- Salary intelligence
- Candidate-specific hard filtering
- Job-description requirement extraction
- Deterministic candidate-to-job matching
- Semantic matching
- Hybrid matching
- Final match engine
- Ranked recommendations
- Explainable recommendations
- Skill-gap analysis
- Opportunity intelligence
- Source provenance
- Source-specific listing links
- Source-specific application links
- FastAPI job-search API
- Frontend opportunity intelligence experience
- Production frontend build

The connector architecture is extensible for future job sources.

---

### Week 3 — Resume & AI Intelligence ✅ Complete

Week 3 introduced candidate-side intelligence and a real local LLM reasoning pipeline.

The goal is to analyze the candidate's actual resume evidence against specific job requirements while preventing unsupported claims.

#### Resume Intelligence

Implemented:

- PDF resume parsing
- Text extraction
- Section detection
- Extraction artifact cleanup
- Template-noise filtering
- Canonical structured resume schema
- Resume normalization
- Experience extraction
- Education extraction
- Project extraction
- Certification extraction
- Achievement extraction
- Skills extraction
- Technical skills extraction
- Resume intelligence analysis

#### ATS Intelligence

Implemented:

- ATS-oriented resume analysis
- Job requirement comparison
- Keyword coverage analysis
- Skill coverage analysis
- Experience alignment
- Education alignment
- Resume section coverage
- ATS readiness scoring
- ATS risk identification
- Missing requirement identification

#### Job-Specific Resume Analysis

CareerPilot can identify:

- Strong matches
- Partial matches
- Missing requirements
- Evidence strength
- Keyword alignment
- Experience alignment
- Section relevance
- Priority gaps
- Recommended actions
- Overall job-specific fit

---

## Evidence-First Resume Rewriting

CareerPilot does not optimize a resume by simply generating impressive-sounding content.

The system improves wording while preserving the truth of the candidate's underlying evidence.

### Rewrite Pipeline

```text
Structured Resume
        ↓
Evidence Analysis
        ↓
Deterministic Rewrite Candidate
        ↓
LLM Reasoning
        ↓
Evidence Validation
        ↓
    ┌───┴────┐
    ↓        ↓
 ACCEPTED  REJECTED

 The validation layer rejects rewrites that introduce unsupported:

Technologies
Skills
Metrics
Achievements
Scale claims
Impact claims
Experience claims
Major semantic changes

Core principle:

CareerPilot may improve how candidate evidence is expressed, but must not manufacture candidate experience.

Local LLM Reasoning

Week 3 introduced real local LLM reasoning using:

Ollama
Qwen 3.5 9B

The LLM is integrated into the actual resume-analysis workflow.

RAW RESUME
    ↓
STRUCTURED RESUME
    ↓
DETERMINISTIC EVIDENCE
    ↓
JOB REQUIREMENTS
    ↓
EVIDENCE-BASED REWRITE
    ↓
QWEN 3.5 9B
    ↓
EVIDENCE VALIDATION
    ↓
ACCEPTED / REJECTED

The LLM does not replace deterministic evidence processing.

It operates inside an evidence-constrained reasoning and generation boundary.

Configuration
LLM_PROVIDER=ollama
LLM_MODEL=qwen3.5:9b
OLLAMA_URL=http://127.0.0.1:11434/api/generate

LLM_TIMEOUT=180
LLM_TEMPERATURE=0.2
LLM_NUM_PREDICT=220
LLM_MAX_CANDIDATES=3
Complete Resume Intelligence Pipeline
Resume PDF
    ↓
Resume Parser
    ↓
Resume Structurer
    ↓
Canonical Structured Resume
    ↓
┌───────────────────────┐
│                       │
↓                       ↓
Resume Intelligence   ATS Analysis
│                       │
└──────────┬────────────┘
           ↓
Job-Specific Analysis
           ↓
Evidence Extraction
           ↓
Evidence-First Rewrite
           ↓
Qwen 3.5 9B
           ↓
Evidence Validation
      ┌────┴────┐
      ↓         ↓
  ACCEPTED   REJECTED
      ↓
    FastAPI
      ↓
   Frontend
Complete Opportunity Intelligence Pipeline
Candidate Profile
       ↓
Search Request
       ↓
Job Aggregation
    ┌───┴────┐
    ↓        ↓
 Adzuna   Jooble
    └───┬────┘
        ↓
Cross-Source Deduplication
        ↓
Canonical Opportunity
        ↓
Salary Intelligence
        ↓
Hard Filtering
        ↓
Requirements Extraction
        ↓
Deterministic Matching
        ↓
Semantic Matching
        ↓
Final Match Engine
        ↓
Ranked Opportunities
        ↓
Opportunity Intelligence
Unified CareerPilot Architecture

By the end of Week 3, CareerPilot contained two major intelligence domains:

                     CAREERPILOT AI
                         │
              ┌──────────┴──────────┐
              ↓                     ↓
   Candidate Intelligence   Opportunity Intelligence
              │                     │
              ↓                     ↓
    Resume Intelligence      Job Intelligence
              │                     │
              └──────────┬──────────┘
                         ↓
                   Career Strategy
                         ↓
             Personalized Recommendations
                         ↓
                     Next Action

The broader pre-agentic architecture was:

User Goal
   ↓
Candidate Profile
   ↓
Candidate Intelligence
   ↓
Career Strategy
   ↓
Opportunity Intelligence
   ↓
Personalized Recommendations
   ↓
Next Action
LLM Safety Architecture

CareerPilot intentionally separates evidence from generation.

Verified Candidate Evidence
          ↓
Deterministic Processing
          ↓
LLM Generation
          ↓
Validation Layer
       ┌───┴────┐
       ↓        ↓
   ACCEPTED  REJECTED

Validation checks include:

Unsupported metrics
Unsupported technologies
Unsupported impact claims
Unsupported experience
Excessive semantic drift
Empty or invalid output
Other evidence violations

Failed local LLM generations are rejected rather than silently accepted.

Evaluation

Week 3 introduced an automated local LLM evaluation harness.

The evaluation covers:

Career reasoning
Evidence safety
Gap analysis
Actionability
Structured output
Evidence-constrained reasoning
Latest Evaluation

Model: Qwen 3.5 9B
Overall Score: 100/100

Test	Category	Score
CP-01	Job Fit Reasoning	100/100
CP-02	Evidence-Safe Rewrite	100/100
CP-03	Gap Analysis	100/100
CP-04	Action Plan	100/100
CP-05	Structured Output	100/100
CP-06	Evidence-Constrained Reasoning	100/100

Evaluation report:

reports/llm_eval_qwen3.5_9b_20260906_142020.json
Testing

Week 3 validation includes:

Deterministic backend regression tests
Automated LLM evaluation
Real local LLM execution
Production API testing
Frontend TypeScript validation
End-to-end resume analysis

Current backend regression result:

11 passed

Frontend TypeScript validation also passes successfully.

Week 4 — Agentic AI Orchestration ✅ Complete

Week 4 transformed CareerPilot from a collection of intelligence services into a coordinated agentic career intelligence system.

The central architectural principle is:

LLM = THINK / REASON
Python Deterministic Services = COMPUTE / VERIFY
LangGraph = ORCHESTRATE
Shared State = REMEMBER
Validation = TRUST

The goal of Week 4 was to introduce real agentic behavior without replacing reliable deterministic career intelligence with uncontrolled LLM generation.

Agentic Architecture

CareerPilot now uses a multi-agent architecture built around LangGraph.

                         USER GOAL
                            ↓
                     SUPERVISOR AGENT
                            ↓
              ┌─────────────┴─────────────┐
              ↓                           ↓
      CANDIDATE AGENT              RESUME AGENT
              │                           │
              ↓                           ↓
      Candidate Intelligence       Resume Intelligence
              │                           │
              └─────────────┬─────────────┘
                            ↓
                      STRATEGY AGENT
                            ↓
                       JOB AGENT
                            ↓
                 RECOMMENDATION AGENT
                            ↓
                   VALIDATION AGENT
                            ↓
                     FINAL RESPONSE

The workflow is not simply a sequence of LLM calls.

Agents share structured state, delegate tasks, use deterministic tools, and pass their outputs through validation.

Seven Specialist Agents

CareerPilot now contains seven defined agent roles:

1. Supervisor Agent

Responsible for deciding what should happen next in the workflow.

The Supervisor evaluates the current shared state and determines whether the system should:

Analyze the candidate
Analyze the resume
Analyze jobs
Generate career strategy
Generate recommendations
Validate the workflow
Recover from failure
Request user input
Finalize the response

The Supervisor decides the next action rather than directly performing every task.

2. Candidate Agent

Responsible for candidate intelligence.

It uses deterministic candidate intelligence services to derive:

Profile completeness
Normalized skills
Skill categories
Strengths
Missing information
Career direction
Target roles
Target industries
Readiness level
Readiness score
Candidate recommendations
3. Resume Agent

Responsible for resume-side intelligence.

It coordinates:

Resume parsing
Resume structuring
Resume intelligence
ATS analysis
Job-specific resume analysis
Evidence extraction
Evidence-first rewriting
LLM reasoning
Rewrite validation

Resume optimization is handled as a capability of the Resume Agent rather than as a separate unnecessary agent.

4. Job Agent

Responsible for opportunity and job intelligence.

It can coordinate:

Job search
Job aggregation
Requirements extraction
Job-description analysis
Candidate/job matching
Opportunity intelligence

Job-service imports are handled safely so optional heavy dependencies do not unnecessarily break unrelated workflows.

5. Career Strategy Agent

Responsible for transforming candidate intelligence into a structured career strategy.

It produces:

Career direction
Target roles
Target industries
Strategic actions
Skill-development priorities
Career strategy summary
6. Recommendation Agent

Responsible for synthesizing the outputs of the workflow into personalized recommendations.

It combines available intelligence from:

Candidate analysis
Resume analysis
Job intelligence
Career strategy

Example recommendation outputs include:

Target aligned opportunities
Strengthen production backend skills
Build stronger AI project evidence
Practice backend system design
Review and close key skill gaps
Strengthen resume positioning

The Recommendation Agent produces actionable rather than purely descriptive output.

7. Validation Agent

Responsible for trust and final workflow verification.

It validates:

Workflow structure
Recommendation structure
Required outputs
Final response consistency
Safety conditions

The validation layer prevents invalid agent outputs from being silently accepted.

Shared CareerPilot State

Week 4 introduced a shared workflow state used across the agentic graph.

The state can carry information such as:

User goal
Candidate profile
Candidate intelligence
Structured resume
Resume intelligence
ATS intelligence
Job intelligence
Career strategy
Recommendations
Next action
Supervisor decision
Agent trace
Tool trace
Validation result
Retry information
Workflow metadata
Workflow errors

This enables agents to operate as coordinated specialists rather than isolated functions.

Deterministic Tools Layer

Agents do not directly perform every computation themselves.

Week 4 introduced a deterministic tools layer that exposes reliable Python services to the agentic workflow.

Candidate Tools
Candidate intelligence analysis
Resume Tools
Resume parsing
Resume structuring
Resume intelligence
ATS analysis
Job-specific resume analysis
Evidence-first rewriting
LLM reasoning
Complete resume intelligence pipeline
Job Tools
Job search
Job requirements extraction
Job-description analysis
Complete job search pipeline
Strategy Tools
Candidate-to-strategy analysis
Career strategy generation
Validation Tools
Workflow validation
Recommendation validation
Evidence-oriented validation

The architecture keeps computation and verification deterministic while allowing agents to reason about which capabilities should be used.

Supervisor and Orchestration

The Supervisor is state-aware.

It does not blindly execute every agent.

The routing logic evaluates the current workflow state and selects the next required operation.

Conceptually:

Current State
     ↓
Supervisor
     ↓
What is missing?
     ↓
┌────┼────┬────┬────┬────┐
↓    ↓    ↓    ↓    ↓    ↓
Candidate
Resume
Job
Strategy
Recommendation
Validation
     ↓
Updated Shared State
     ↓
Supervisor Again

This creates a controlled agentic loop instead of a fixed chain.

LangGraph Workflow

CareerPilot uses LangGraph to coordinate the agentic workflow.

The graph contains:

Supervisor node
Candidate node
Resume node
Job node
Strategy node
Recommendation node
Validation node
Recovery node
Final node

The graph is compiled into a runnable workflow.

High-Level Workflow
START
  ↓
SUPERVISOR
  ↓
SPECIALIST AGENT
  ↓
SHARED STATE UPDATE
  ↓
SUPERVISOR
  ↓
NEXT SPECIALIST
  ↓
...
  ↓
VALIDATION
  ↓
FINAL

The workflow is state-driven rather than dependent on a hard-coded linear sequence.

Agent Delegation

Week 4 introduced explicit delegation tracing.

The Supervisor delegates tasks to specialist agents.

Example:

Supervisor → Candidate
Supervisor → Strategy
Supervisor → Recommendation
Supervisor → Validation

Each delegation can record:

Source agent
Target agent
Reason
Status
Workflow step

This makes the agentic workflow observable from the application UI.

The system can therefore show not only the final answer, but also which agents participated in producing it.

Workflow Tracing

CareerPilot records an agent trace and tool trace.

Agent Trace

Tracks:

Agent involved
Decision
Reason
Workflow state
Execution status
Tool Trace

Tracks:

Tool invoked
Agent invoking it
Tool status
Result information

The frontend uses this information to display the orchestration process.

Validation, Safety and Recovery

Week 4 introduced bounded workflow safety.

CareerPilot uses a safety policy with controlled limits including:

Maximum retries
Maximum workflow steps
Maximum workflow errors

The system evaluates whether a failed workflow can safely retry.

Conceptually:

Agent Failure
     ↓
Safety Evaluation
     ↓
Can Retry?
   ┌─┴─┐
   ↓   ↓
 YES   NO
   ↓    ↓
Recovery  Failed
   ↓
Resume Workflow

Retries are bounded so that an agentic failure cannot result in an uncontrolled execution loop.

Checkpointing

Week 4 introduced LangGraph checkpointing using an in-memory MemorySaver.

The workflow is associated with a thread identifier so the graph can maintain checkpointed execution state during a running application process.

The current implementation provides:

Thread-based workflow configuration
Checkpoint-backed graph execution
Workflow state continuity
Safer recovery behavior

Persistent external storage is intentionally deferred for future development.

Agentic API

Week 4 introduced a dedicated agentic API layer.

Agentic Health
GET /agentic/health

Used to verify that the agentic API layer is available.

Run CareerPilot
POST /agentic/run

Runs the agentic CareerPilot workflow.

The API accepts agentic workflow inputs and returns structured information including:

Workflow status
Current workflow agent
Agents used
Agent trace
Delegation trace
Tool trace
Validation result
Recommendations
Next action
Candidate intelligence
Retry information
Thread identifier
Workflow metadata

This provides a structured contract between the agentic backend and the frontend.

Agentic Frontend Command Center

Week 4 replaced the previous primary workflow experience with an agentic CareerPilot command center.

The interface allows the user to provide:

Career goal
Target role
Skills
Location

The dashboard then displays:

Workflow Trace

Shows the agents participating in the workflow.

Delegation Trace

Shows which agents delegated work to other agents.

Trust Layer

Displays:

Validation status
Retry count
Tool usage
Next Best Action

Shows the most useful immediate career action.

Candidate Intelligence

Displays candidate readiness information.

Personalized Recommendations

Displays structured recommendations generated from the combined workflow intelligence.

The frontend communicates directly with the Agentic API.

Agentic Workflow Example

A typical successful workflow can look like:

User
  ↓
Supervisor
  ↓
Candidate
  ↓
Candidate Intelligence
  ↓
Strategy
  ↓
Career Strategy
  ↓
Recommendation
  ↓
Personalized Recommendations
  ↓
Validation
  ↓
Validated Final Response

Delegation tracing records the orchestration between the agents.

The frontend can therefore show a real workflow such as:

Supervisor → Candidate
Supervisor → Strategy
Supervisor → Recommendation
Supervisor → Validation
Week 4 End-to-End Architecture

The architecture after Week 4 is:

                         USER
                          ↓
                      USER GOAL
                          ↓
                  CANDIDATE PROFILE
                          ↓
                   SUPERVISOR AGENT
                          ↓
        ┌─────────────────┼──────────────────┐
        ↓                 ↓                  ↓
 CANDIDATE AGENT    RESUME AGENT        JOB AGENT
        ↓                 ↓                  ↓
 Candidate           Resume/ATS       Opportunity
 Intelligence        Intelligence      Intelligence
        └─────────────────┼──────────────────┘
                          ↓
                   STRATEGY AGENT
                          ↓
                   CAREER STRATEGY
                          ↓
               RECOMMENDATION AGENT
                          ↓
             PERSONALIZED RECOMMENDATIONS
                          ↓
                  VALIDATION AGENT
                          ↓
                 VALIDATED RESPONSE
                          ↓
                    NEXT ACTION

The complete system now combines deterministic career intelligence with agentic orchestration.

Agentic Design Principles

CareerPilot follows several architectural principles:

LLM = Think / Reason

The LLM is used where reasoning and language generation are valuable.

Python Services = Compute / Verify

Deterministic services remain responsible for:

Structured processing
Scoring
Matching
Evidence extraction
Validation
Business rules
LangGraph = Orchestrate

LangGraph manages:

Workflow routing
Agent execution
State transitions
Recovery
Checkpointing
Shared State = Remember

All agents communicate through structured workflow state.

Validation = Trust

Generated outputs are validated before being accepted.

This separation helps keep the system reliable while still benefiting from agentic reasoning.

Week 4 Testing and Verification

Week 4 validation included:

Backend regression testing
LangGraph graph compilation
Agent-level tests
Deterministic tool tests
Agent delegation tests
Safety/recovery tests
Checkpoint tests
Agentic API tests
End-to-end workflow tests
Frontend TypeScript validation
Browser-level frontend verification

The primary regression suite passed:

11 passed

Agentic API verification successfully confirmed:

HTTP 200
Workflow: COMPLETED
Validation: VALID
Retry Count: 0
Recommendations: 2

The agentic workflow was also verified through the frontend with:

Completed workflow
Multiple participating agents
Delegation events
Validated result
Personalized recommendations
Candidate readiness
Tool usage
Zero retries in the successful run
Technology Stack
Frontend
Next.js
React
TypeScript
Backend
Python
FastAPI
Pydantic
PyPDF
Agentic AI
LangGraph
Shared workflow state
Supervisor orchestration
Specialist agents
Agent delegation
Deterministic tools
Workflow validation
Safety and recovery
Checkpointing
Job Intelligence
Adzuna
Jooble
Job aggregation
Deduplication
Salary intelligence
Hard filtering
Requirements extraction
Deterministic matching
Semantic matching
Opportunity ranking
Resume Intelligence
PDF parsing
Resume structuring
Resume normalization
Resume intelligence
ATS analysis
Job-specific resume analysis
Evidence extraction
Evidence-first rewriting
Rewrite validation
AI / LLM
Ollama
Qwen 3.5 9B
Evidence-constrained reasoning
LLM output validation
Hallucination protection
Testing & Evaluation
Pytest
Automated LLM evaluation
TypeScript type checking
End-to-end API verification
Agentic workflow verification
Project Structure
CareerPilot-AI/
│
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor_agent.py
│   │   ├── candidate_agent.py
│   │   ├── resume_agent.py
│   │   ├── job_agent.py
│   │   ├── strategy_agent.py
│   │   ├── recommendation_agent.py
│   │   └── validation_agent.py
│   │
│   ├── api/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── agentic.py
│   │
│   ├── connectors/
│   │   ├── adzuna.py
│   │   └── jooble.py
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── evaluator.py
│   │   ├── run_evaluation.py
│   │   └── test_cases.py
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   ├── routing.py
│   │   ├── workflow.py
│   │   ├── delegation.py
│   │   ├── checkpoints.py
│   │   └── safety.py
│   │
│   ├── schemas/
│   │   ├── candidate.py
│   │   ├── job.py
│   │   ├── resume.py
│   │   └── agentic.py
│   │
│   ├── services/
│   │   ├── ats_analyzer.py
│   │   ├── candidate_intelligence.py
│   │   ├── job_resume_analyzer.py
│   │   ├── llm_resume_reasoner.py
│   │   ├── resume_intelligence.py
│   │   ├── resume_parser.py
│   │   ├── resume_rewrite_engine.py
│   │   ├── resume_structurer.py
│   │   └── search_service.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── candidate_tools.py
│   │   ├── resume_tools.py
│   │   ├── job_tools.py
│   │   ├── strategy_tools.py
│   │   └── validation_tools.py
│   │
│   ├── career_strategy.py
│   └── test_*.py
│
├── frontend/
│   ├── app/
│   │   └── page.tsx
│   └── lib/
│       └── agentic.ts
│
├── reports/
│
├── sample-data/
│   └── sample_resume.pdf
│
├── .env.example
├── requirements.txt
└── README.md
API Endpoints
Job Search
POST /jobs/search

Searches available job sources and returns ranked opportunities with candidate intelligence and career strategy.

Resume Analysis
POST /resume/analyze

Parses and analyzes an uploaded PDF resume.

Job-Specific Resume Analysis
POST /resume/ats-analyze

Runs the complete resume-to-job intelligence pipeline:

PDF
 ↓
Parsing
 ↓
Structuring
 ↓
ATS Analysis
 ↓
Job-Specific Analysis
 ↓
Evidence-Based Rewrite
 ↓
LLM Reasoning
 ↓
Validation
 ↓
API Response
Agentic Health
GET /agentic/health

Checks the status of the Agentic CareerPilot API layer.

Agentic CareerPilot Run
POST /agentic/run

Executes the LangGraph-based CareerPilot agentic workflow.

The response includes structured workflow information such as:

Workflow status
Current agent
Agent trace
Delegation trace
Tool trace
Validation
Recommendations
Next action
Candidate intelligence
Retry count
Thread ID
Workflow metadata
Local Setup
Backend

From the project root:

.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
uvicorn backend.api.main:app --reload

Backend:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs
Frontend
cd frontend
npm run dev

Frontend:

http://localhost:3000
Local LLM Setup

CareerPilot uses Ollama for local LLM reasoning.

Required configuration:

LLM_PROVIDER=ollama
LLM_MODEL=qwen3.5:9b
OLLAMA_URL=http://127.0.0.1:11434/api/generate

The LLM is used as a reasoning and generation component inside the evidence-constrained CareerPilot pipeline.

Current Architecture Summary

CareerPilot has evolved through four major stages:

WEEK 1
Foundation
    ↓
WEEK 2
Opportunity Intelligence
    ↓
WEEK 3
Resume + AI Intelligence
    ↓
WEEK 4
Agentic AI Orchestration

The resulting system is:

                         CAREERPILOT AI
                              │
               ┌──────────────┴──────────────┐
               ↓                             ↓
      CANDIDATE INTELLIGENCE        OPPORTUNITY INTELLIGENCE
               │                             │
               ↓                             ↓
      RESUME / ATS INTELLIGENCE       JOB INTELLIGENCE
               │                             │
               └──────────────┬──────────────┘
                              ↓
                       CAREER STRATEGY
                              ↓
                       SUPERVISOR AGENT
                              ↓
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
        SPECIALIST       DETERMINISTIC     SHARED
          AGENTS            TOOLS           STATE
              └───────────────┼───────────────┘
                              ↓
                   PERSONALIZED RECOMMENDATIONS
                              ↓
                        VALIDATION LAYER
                              ↓
                         NEXT ACTION

CareerPilot is designed so that agentic reasoning extends the existing intelligence architecture rather than replacing it.

Future Direction

The current architecture provides the foundation for future CareerPilot capabilities such as:

Long-term career personalization
Persistent career memory
Career Twin / Career Simulator
Career Graph
Deeper opportunity intelligence
Long-term state persistence
More advanced agent delegation
Expanded validation and evaluation
Production deployment

These capabilities are intentionally built on top of the existing deterministic intelligence and agentic orchestration layers.

Project Goal

CareerPilot is designed to evolve from a career assistant into a personalized career intelligence system that continuously understands:

WHO YOU ARE
     ↓
WHAT YOU CAN DO
     ↓
WHERE YOU FIT
     ↓
WHAT YOU ARE MISSING
     ↓
WHAT YOU SHOULD DO NEXT

The long-term objective is to make career decisions more personalized, evidence-based, explainable, and actionable.

# CareerPilot AI

CareerPilot AI is an intelligent career operating system designed to help candidates discover, evaluate, understand, and act on job opportunities.

Instead of functioning as a basic job-search interface, CareerPilot combines:

- Candidate intelligence
- Opportunity intelligence
- Resume intelligence
- ATS analysis
- Evidence-first resume rewriting
- Local LLM reasoning

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
   ┌────┴────┐
   ↓         ↓
ACCEPTED   REJECTED

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

The LLM does not replace deterministic evidence processing. It operates inside an evidence-constrained reasoning and generation boundary.

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
       ┌───┴───┐
       ↓       ↓
   ACCEPTED  REJECTED
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

By the end of Week 3, CareerPilot contains two major intelligence domains:

                    CAREERPILOT AI
                         │
             ┌───────────┴───────────┐
             ↓                       ↓
 Candidate Intelligence      Opportunity Intelligence
             │                       │
             ↓                       ↓
   Resume Intelligence          Job Intelligence
             │                       │
             └───────────┬───────────┘
                         ↓
                  Career Strategy
                         ↓
              Personalized Recommendations
                         ↓
                    Next Action

The broader architecture is:

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
      ┌───┴───┐
      ↓       ↓
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
Project Structure
CareerPilot-AI/
│
├── backend/
│   ├── api/
│   │   ├── main.py
│   │   └── models.py
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
│   ├── schemas/
│   │   ├── candidate.py
│   │   ├── job.py
│   │   └── resume.py
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
│   ├── career_strategy.py
│   └── test_*.py
│
├── frontend/
│   ├── app/
│   └── lib/
│
├── reports/
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

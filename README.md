# CareerPilot AI

CareerPilot AI is an intelligent career operating system designed to help candidates discover, evaluate, understand, and act on job opportunities.

Instead of functioning as a basic job-search interface, CareerPilot combines:

- Live multi-source job discovery
- Cross-source deduplication
- Salary intelligence
- Candidate-specific hard filtering
- Deterministic candidate-to-job matching
- Semantic compatibility analysis
- Explainable recommendations
- Skill-gap analysis
- Source provenance
- Source-specific listing and application actions

The architecture is designed to scale from the current two live sources to a much larger multi-source ecosystem.

---

## Current Status

### Week 2 - Complete

CareerPilot currently includes:

- Next.js frontend
- FastAPI backend
- Adzuna job source
- Jooble job source
- Cross-source canonical opportunity model
- Salary Intelligence
- Candidate/job matching
- Semantic matching
- Opportunity Intelligence
- Source provenance
- Source-specific listing and application links
- Production frontend build

### Current Live Sources

1. Adzuna
2. Jooble

Additional sources will be added in later development phases.

The target architecture is intentionally extensible toward a much larger multi-source ecosystem.

---

# Architecture

```text
                     CareerPilot AI
                           |
                           v
                  Candidate Profile
                           |
                           v
                    Search Request
                           |
                           v
              +-------------------------+
              |    Job Aggregation      |
              +-------------------------+
                    |             |
                    v             v
                 Adzuna         Jooble
                    |             |
                    +------+------+
                           |
                           v
               Cross-Source Deduplication
                           |
                           v
                 Canonical Opportunity
                           |
                           v
                 Salary Intelligence
                           |
                           v
                    Hard Filtering
                           |
                           v
                Requirements Extraction
                           |
                           v
                Deterministic Matching
                           |
                           v
                 Semantic Matching
                           |
                           v
                 Final Match Engine
                           |
                           v
                 Ranked Opportunities
                           |
                           v
             Opportunity Intelligence UI
# CareerPilot AI - System Architecture

## Project Scope

CareerPilot AI is an Agentic AI based career development platform combining Track A core career assistance with Track B advanced agentic workflows.

## Week 1 Prototype

The Week 1 prototype focuses on job-search automation and AI-based job matching using an n8n workflow.

User
  |
  v
Job Search Input
  |
  v
n8n Workflow
  |
  +--> Input Validation
  |
  +--> Job Data
  |
  +--> Job Filtering
  |
  +--> AI Matching
  |
  v
Ranked Job Recommendations

## Planned Architecture

Frontend
React / Next.js
        |
        v
Backend API
FastAPI
        |
        v
Agent Orchestrator
LangGraph
        |
        +----------------+----------------+----------------+
        |                |                |                |
        v                v                v                v
    Job Agent      Resume Agent    Company Research    Interview Agent
        |                |                |                |
        +----------------+----------------+----------------+
                               |
                               v
                    Salary / Career Planning
                               |
                               v
                       PostgreSQL + Redis

Future services:
- Authentication
- Monitoring
- Notifications
- Application Tracking
- Security and privacy controls

## Development Roadmap

### Week 1
- Project setup
- Architecture design
- n8n prototype
- Job matching concept
- Sample job dataset

### Week 2
- Live job data integration
- Job filtering
- AI matching improvements
- Prototype deployment

### Weeks 3-4
- Resume parsing
- Company research
- Multiple career tools
- Agent workflow expansion

### Weeks 5-6
- Interview preparation
- Salary analysis
- Career path recommendations
- Application tracking

### Weeks 7-8
- Professional UI
- Authentication
- Security
- Monitoring
- Testing
- Production deployment

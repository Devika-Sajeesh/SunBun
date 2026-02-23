# SunBun Solar Assistant – Week 1 Submission

> **Agentic Hackathon**: Deterministic AI Agent using LangGraph workflows with controlled decision-making and state-based orchestration.

**Submission by**: Devika Sajeesh
**Date**: February 24, 2026 
**Repository**: [GitHub Link]

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Flow Coverage](#flow-coverage)
- [Deterministic Design](#deterministic-design)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Known Limitations](#known-limitations)
- [Week 2 Preview](#week-2-preview)
- [Demo Video](#demo-video)

---

## Overview

SunBun Solar Assistant is a deterministic state-graph backend built with LangGraph that handles both Sales and Service support flows for a fictional solar installation company.

### Key Features

- **100% Deterministic Routing** – All decision logic uses pure Python (no LLM for branching)
- **OTP-Based Authentication** – Simulated email/SMS verification with retry logic
- **Smart Service Support** – Analyzes site metrics, cloudiness data, and performance scores
- **Intelligent Sales Flow** – Generates proposals using formula-based calculations
- **Multi-Step Conversations** – Session-based state management across HTTP calls
- **Agent Handoff** – Routes to human agents when available
- **Complete Flow Coverage** – All 7 sections from spec implemented

---

## Screenshots

### Sales Flow (New Prospect)
![Sales Flow](sales_flow.png)

### Service Support Flow
![Support Flow](support_flow.png)

---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                  agentchat.vercel.app                    │
│                     (Frontend UI)                        │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP POST /chat
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Server                         │
│              (Session Management Layer)                  │
└─────────────────────┬───────────────────────────────────┘
                      │ process_message()
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  LangGraph State Graph                   │
│           (Deterministic Node Orchestration)             │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   DataService Layer                      │
│              (CSV Read/Write Operations)                 │
└─────────────────────────────────────────────────────────┘
```

### State Graph Visualization

![Graph Structure](graph.png)

**Graph Flow**:
1. **Entry** → User selects Sales/Service support
2. **Auth** → OTP verification (email or phone)
3. **Lookup** → Check if customer exists in database
4. **Router** → Branch to Sales or Service based on:
   - Support type selected
   - Customer found in DB or not
   - Has existing proposals or not
5. **Execution** → Run appropriate flow to completion

---

## Flow Coverage

All sections from the specification are fully implemented:

| Section | Flow Description | Status |
|---------|------------------|--------|
| **1. Entry** | Landing page routing (Sales/Service) | Complete |
| **2. Authentication** | OTP-based auth with email/phone, retry logic | Complete |
| **3. Customer Found** | Lookup → Branch to Sales/Service | Complete |
| **4. Service – Known** | Status check, issue analysis, cloudiness logic, NPS | Complete |
| **5. Service – Unknown** | System info collection, ticket creation | Complete |
| **6. Sales – Known** | Review existing proposals, generate new options | Complete |
| **7. Sales – Unknown** | New prospect flow, proposal generation | Complete |

### Branch Coverage Details

**Auth Flow**: 5 nodes
- Email/Phone selection
- OTP send & verify (with 3-attempt retry)
- Customer lookup (found/not found)
- Retry different identifier option
- Exit on auth failure

**Service Flow**: 7 nodes
- Site status check (reads `site_issues.csv`)
- Metrics analysis (cloudiness, performance, production)
- Happy path → NPS collection → Close
- Escalation path → Issue capture → Agent check → Ticket
- Unknown customer → System info → Issue capture → Ticket

**Sales Flow**: 8 nodes
- Existing proposals review → Select → Confirm
- New proposal generation (6-step info capture)
- Deterministic sizing formula
- Agent handoff (chat/call preference)
- CRM opportunity creation

---

## Deterministic Design

### Philosophy

**"Deterministic Where Possible, LLM Only for Language"**

All routing, branching, and business logic is implemented in pure Python. LLMs (if used at all) would only format natural language responses, never make decisions.

### Component Breakdown

| Component | Approach | Reasoning |
|-----------|----------|-----------|
| **OTP Verification** | Pure Python | Exact 6-digit match, retry counter, no ambiguity needed |
| **Customer Lookup** | Pandas CSV query | Deterministic email/phone string matching |
| **Branch Routing** | If/else on state fields | `support_type`, `is_in_db`, `has_proposals` are booleans |
| **Metrics Analysis** | Mathematical formulas | `avg_cloudiness > 60`, `performance < 75` = fixed thresholds |
| **Proposal Generation** | Formula-based | `system_kW = (bill / tariff × 12) / 1200 × growth_factor` |
| **Agent Availability** | CSV flag check | `is_online == True` in `agent_availability.csv` |
| **Message Formatting** | Python f-strings | Template strings with state variable interpolation |

### No LLM Usage

Week 1 submission uses **zero LLM calls** for decision-making. Every node returns a deterministic output given the same input state.

**Example – Service Status Check**:
```python
if site_status["issue_flag"] == True:
    return issue_message()
elif metrics["is_cloudy"]:
    return cloudy_weather_message()
elif metrics["avg_performance"] >= 75:
    return normal_performance_message()
else:
    return underperformance_message()
```

All branches are reachable and testable.

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- pip

### Installation Steps

```bash
# 1. Clone repository
git clone [your-repo-url]
cd sunbun-agent

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify data files
ls data/
# Should show 13 CSV files
```

### Dependencies

```
langgraph>=0.2.0
langchain>=0.2.0
langchain-openai>=0.1.0
fastapi>=0.111.0
uvicorn>=0.30.0
pandas>=2.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

---

## Running the Application

### Step 1: Start the FastAPI Server

```bash
# Development mode (auto-reload on code changes)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python -m api.main

# You should see:
# 🌞 SunBun Solar Assistant API Starting...
# ✅ Graph initialized successfully
# 📡 Server ready at http://localhost:8000
```

### Step 2: Connect agentchat.vercel.app

1. Open [agentchat.vercel.app](https://agentchat.vercel.app/)
2. Configure endpoint:
   - **URL**: `http://localhost:8000/chat`
   - **Method**: POST
3. Start chatting!

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Main chat endpoint (agentchat compatible) |
| `POST` | `/message` | Alternative chat endpoint |
| `POST` | `/reset` | Reset a session to initial state |
| `GET` | `/session/{id}` | Inspect session state (debugging) |
| `GET` | `/health` | Health check |
| `GET` | `/graph/diagram` | Export graph as Mermaid diagram |

### Step 3: Test Conversation Flow

**Example – Service Support**:
```
User: [Start]
Bot: 👋 Welcome to SunBun Solar! How can we help you today?
     1 → Sales Support
     2 → Service Support

User: 2
Bot: Let's connect you with Service Support. Please choose:
     1 → Use Email
     2 → Use Phone

User: 1
Bot: Please enter your email address:

User: john.doe@example.com
Bot: 📧 We've sent a 6-digit code to john.doe@example.com
     (Check console for simulated OTP: 123456)
     Enter the 6-digit code:

User: 123456
Bot: ✅ Identity verified! Welcome back, John Doe!
     [Checking system status...]
     ⚠️ Active Issue Detected
     Issue: Communication Loss
     Recommended Action: Please check the inverter's internet connection.
```

---

## Testing

### Run Automated Tests

```bash
python tests/test_flows.py
```

### Expected Output

```
╔════════════════════════════════════════════════════════════════════╗
║           🌞 SUNBUN SOLAR ASSISTANT - TEST SUITE                  ║
╚════════════════════════════════════════════════════════════════════╝

🧪 TEST: Auth: Email OTP Success .......................... ✅ PASSED
🧪 TEST: Auth: Phone OTP Success .......................... ✅ PASSED
🧪 TEST: Auth: OTP Retry Flow ............................. ✅ PASSED
🧪 TEST: Auth: Not Found - Retry .......................... ✅ PASSED
🧪 TEST: Service: Active Issue (Site 101) ................. ✅ PASSED
🧪 TEST: Service: Normal Performance ...................... ✅ PASSED
🧪 TEST: Service: Escalation - Agent Available ............ ✅ PASSED
🧪 TEST: Service: Unknown Customer Flow ................... ✅ PASSED
🧪 TEST: Sales: Review Existing Proposals ................. ✅ PASSED
🧪 TEST: Sales: New Proposals for Existing Customer ....... ✅ PASSED
🧪 TEST: Sales: New Prospect Flow ......................... ✅ PASSED
🧪 TEST: Edge Case: Invalid Inputs ........................ ✅ PASSED
🧪 TEST: Edge Case: End and Restart ....................... ✅ PASSED

======================================================================
📊 TEST SUMMARY
======================================================================
✅ Passed: 13
❌ Failed: 0
📊 Success Rate: 13/13 (100.0%)
======================================================================
```

### Test Coverage

| Category | Tests | Coverage |
|----------|-------|----------|
| Authentication | 4 | Email OTP, Phone OTP, OTP retry, Not found + retry |
| Service (Known) | 3 | Active issue, Normal performance, Escalation |
| Service (Unknown) | 1 | Full system info capture + ticket |
| Sales (Known) | 2 | Review existing proposals, Generate new proposals |
| Sales (Unknown) | 1 | New prospect full flow |
| Edge Cases | 2 | Invalid inputs, End and restart |

### Manual Testing

Use the `/session/{session_id}` endpoint to inspect state:

```bash
curl http://localhost:8000/session/test-001
```

---

## Project Structure

```
sunbun-agent/
│
├── data/                          # CSV data files (13 files)
│   ├── customers.csv              #   Customer records
│   ├── sites.csv                  #   Solar site installations
│   ├── weekly_metrics.csv         #   Performance metrics
│   ├── site_issues.csv            #   Active site issues
│   ├── proposals.csv              #   Existing customer proposals
│   ├── proposal_template.csv      #   Proposal generation templates
│   ├── agent_availability.csv     #   Live agent status
│   ├── prospects.csv              #   New prospect records
│   ├── crm_opportunities.csv      #   CRM opportunity tracking
│   ├── service_tickets.csv        #   Service tickets
│   ├── component_info.csv         #   Solar component catalog
│   ├── email_otp.csv              #   Email OTP log
│   └── sms_otp.csv                #   SMS OTP log
│
├── graph/                         # LangGraph implementation
│   ├── __init__.py
│   ├── state.py                   #   TypedDict state definition (85 lines)
│   ├── orchestrator.py            #   Graph assembly, routing & session mgmt (415 lines)
│   └── nodes/
│       ├── __init__.py
│       ├── auth_nodes.py          #   Authentication flow nodes (250 lines)
│       ├── service_nodes.py       #   Service support nodes (415 lines)
│       └── sales_nodes.py         #   Sales support nodes (365 lines)
│
├── services/                      # Data access layer
│   ├── __init__.py
│   └── data_service.py            #   CSV read/write operations (365 lines)
│
├── api/                           # FastAPI server
│   ├── __init__.py
│   └── main.py                    #   HTTP endpoints & CORS (232 lines)
│
├── tests/                         # Test suite
│   └── test_flows.py              #   Automated flow tests (424 lines)
│
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── graph.png                      # Graph visualization
```

### Key File Summary

| File | Purpose | Lines |
|------|---------|-------|
| `graph/state.py` | State schema (42 fields + defaults) | ~85 |
| `graph/orchestrator.py` | Graph wiring, node wrapping, session mgmt | ~415 |
| `graph/nodes/auth_nodes.py` | Auth flow (OTP, verify, not-found) | ~250 |
| `graph/nodes/service_nodes.py` | Service flows (status, escalation, NPS) | ~415 |
| `graph/nodes/sales_nodes.py` | Sales flows (proposals, handoff, CRM) | ~365 |
| `services/data_service.py` | All CSV data operations | ~365 |
| `api/main.py` | FastAPI server & endpoints | ~232 |
| `tests/test_flows.py` | 13 automated test cases | ~424 |
| **Total** | | **~2,550 LOC** |

---

## Design Decisions

### 1. Session Management Strategy

**Decision**: In-memory dictionary keyed by `session_id`  
**Rationale**: Week 1 focuses on deterministic logic, not persistence. Simple dict provides fast access and easy debugging.  
**Tradeoff**: Sessions lost on server restart (acceptable for Week 1 demo).

### 2. CSV as Data Layer

**Decision**: Load all CSVs into pandas DataFrames on startup  
**Rationale**: Avoids repeated disk I/O, faster queries using pandas filtering.  
**Tradeoff**: Not scalable for production (Week 2 will use MongoDB).

### 3. State-First Architecture

**Decision**: Every node receives full state, returns partial updates  
**Rationale**: Makes nodes pure functions, easier to test, no hidden side effects.  
**Tradeoff**: Larger state dicts passed around (but still manageable).

### 4. `current_node` Field for Routing

**Decision**: Nodes set their own `current_node` in return dict  
**Rationale**: Self-documenting flow, enables conditional edges in graph via the orchestrator's `_get_next_node` pattern.  
**Tradeoff**: Requires discipline to always set it correctly.

### 5. Deterministic Proposal Generation

**Decision**: Formula-based sizing: `kWp = (bill / tariff × 12 / 1200) × growth_factor`, matched to closest available template size from CSV.  
**Rationale**: Matches spec requirement for deterministic Week 1, industry-standard calculation.  
**Tradeoff**: Less flexible than ML-based sizing (but that's intentional).

### 6. `graph.stream` over `graph.invoke`

**Decision**: Use LangGraph's streaming API with manual state merging in the orchestrator.  
**Rationale**: Solves state loss issues that occurred with `graph.invoke` when nodes auto-chain (e.g., `entry_node` → `auth_collect_contact`).  
**Tradeoff**: Slightly more complex orchestrator code.

---

## Known Limitations

### Week 1 Scope Limitations

1. **OTP Simulation** – OTPs are printed to console, not sent via real email/SMS
2. **In-Memory Sessions** – State lost on server restart
3. **No Real Agent Handoff** – Simulates connection to human agents
4. **CSV Concurrency** – No file locking for concurrent writes
5. **Basic Error Messages** – Could be more user-friendly in edge cases

### Intentional Simplifications

- No authentication/authorization for API endpoints
- No rate limiting on OTP generation
- No persistent conversation history
- Agent availability is static CSV flag (not real-time)

**These will be addressed in Week 2** with:
- MongoDB persistence
- Agent Protocol implementation
- Real-time agent availability checks
- LLM-enhanced response formatting

---

## Week 2 Preview

Planned enhancements for top-6 shortlist:

### Agent Protocol Compliance

- Expose graph as `/ap/v1/agent/tasks` and `/steps` endpoints
- State persistence tied to `customer_id` and `site_id`
- Task-based execution model

### Enhanced Intelligence

- LLM-assisted natural language understanding (keeping deterministic routing)
- Contextual response generation
- Sentiment analysis for escalation priority

### Human-in-Loop

- Sales assistant mode: agent can regenerate proposals, get top-5 options, add feedback
- Service triage: agent sees full context before handoff

### MERN Frontend

- React-based web UI calling Agent Protocol API
- Real-time conversation visualization
- Session state inspector

---

## Demo Video

**Video Walkthrough**: [Watch on Loom](https://www.loom.com/share/5e108b3b1a384f6f867838142d670169)

Demonstrates:
1. Sales flow with existing customer (proposal review)
2. Service flow with active issue (escalation path)
3. Test suite execution (all 13 tests passing)
4. Graph visualization

---

## Evaluation Criteria Checklist

| Criteria | Weight | Status | Evidence |
|----------|--------|--------|----------|
| **Correctness** | 30% | Done | All 7 spec flows implemented, 13/13 tests passing |
| **Deterministic Design** | 25% | Done | Zero LLM calls, pure Python branching, graph visualization |
| **Backend Quality** | 25% | Done | Clean FastAPI + LangGraph separation, session state, error handling |
| **UX & Clarity** | 10% | Done | Structured messages, always tells user what's next |
| **Documentation** | 10% | Done | Comprehensive README, design decisions, video walkthrough |

---

## Acknowledgments

Built for **Agentic Hackathon** by Devika Sajeesh.

Special thanks to:
- LangGraph for the state-graph framework
- The hackathon organizers
- SunBun (fictional company) for the interesting use case

---



For questions about this submission, please open an issue in the repository.

---

**If you're a judge reading this**: Thank you for your time! The test suite in `tests/test_flows.py` is the best way to see all flows in action. Run `python tests/test_flows.py` for a full demo.

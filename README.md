# SunBun Solar Assistant – Week 2 Submission

> **Agentic Hackathon**: Production-ready AI Agent built with LangGraph Platform (Aegra) + Next.js frontend, featuring Agent Protocol compliance, PostgreSQL persistence, and interactive button-based conversations.

**Submission by**: Devika Sajeesh  
**Date**: March 15, 2026  
---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [What's New in Week 2](#whats-new-in-week-2)
- [Flow Coverage](#flow-coverage)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Known Limitations](#known-limitations)
- [Demo Video](#demo-video)

---

## Overview

SunBun Solar Assistant is a production-ready AI agent built with **LangGraph Platform (Aegra)** that handles both Sales and Service support flows for a fictional solar installation company. It features a **Next.js frontend** with interactive buttons, **PostgreSQL-backed state persistence**, and full **Agent Protocol compliance**.

### Key Features

- **100% Deterministic Routing** – All decision logic uses pure Python (no LLM for branching)
- **Agent Protocol Compliant** – Runs on Aegra (LangGraph Platform) with standard thread/run APIs
- **PostgreSQL Persistence** – Conversation state survives restarts via PostgresSaver checkpointing
- **Interactive Next.js Frontend** – Button-based UI with real-time streaming responses
- **OTP Authentication** – Simulated email/SMS verification with retry logic
- **Smart Service Support** – Analyzes site metrics, cloudiness data, and performance scores
- **Intelligent Sales Flow** – Generates proposals using formula-based calculations
- **Input Isolation** – Text input and button clicks work interchangeably without conflicts



---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│               Next.js Frontend (sunbun-ui)              │
│         http://localhost:3000 (React + Tailwind)         │
└─────────────────────┬───────────────────────────────────┘
                      │ @langchain/langgraph-sdk (useStream)
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Aegra Dev Server (LangGraph Platform)       │
│              http://127.0.0.1:2026 (Agent Protocol)      │
└─────────────────────┬───────────────────────────────────┘
                      │ Compiled StateGraph
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  LangGraph State Graph                   │
│      Dispatcher → Entry → Auth → Service/Sales Nodes     │
└─────────────────────┬───────────────────────────────────┘
                      │
              ┌───────┴───────┐
              ▼               ▼
┌──────────────────┐  ┌──────────────────┐
│  PostgreSQL DB   │  │  DataService     │
│  (State Persist) │  │  (CSV Queries)   │
└──────────────────┘  └──────────────────┘
```

### State Graph Visualization

![Graph Structure](ssw.png)

**Graph Flow**:
1. **Dispatcher** → Extracts user input, manages turn lifecycle
2. **Entry** → User selects Sales/Service support
3. **Auth** → OTP verification (email or phone) with retry logic
4. **Lookup** → Check if customer exists in database
5. **Router** → Branch to Sales or Service based on state
6. **Execution** → Run appropriate flow to completion

---

## What's New in Week 2

| Feature | Week 1 | Week 2 |
|---------|--------|--------|
| **Server** | FastAPI + uvicorn | Aegra (LangGraph Platform) |
| **State Persistence** | In-memory dict | PostgreSQL (PostgresSaver) |
| **Frontend** | agentchat.vercel.app | Custom Next.js app (sunbun-ui) |
| **API Protocol** | Custom `/chat` endpoint | Agent Protocol (threads/runs) |
| **UI Interaction** | Text-only | Interactive buttons + text input |
| **Session Management** | Server-side dict | Per-thread UUID with checkpointing |
| **Containerization** | None | Docker Compose (PostgreSQL) |
| **Graph Architecture** | Direct orchestrator | Dispatcher + input isolation |

---

## Flow Coverage

All sections from the specification are fully implemented:

| Section | Flow Description | Status |
|---------|------------------|--------|
| **1. Entry** | Landing page routing (Sales/Service) | ✅ Complete |
| **2. Authentication** | OTP-based auth with email/phone, retry logic | ✅ Complete |
| **3. Customer Found** | Lookup → Branch to Sales/Service | ✅ Complete |
| **4. Service – Known** | Status check, issue analysis, cloudiness logic, NPS | ✅ Complete |
| **5. Service – Unknown** | System info collection, ticket creation | ✅ Complete |
| **6. Sales – Known** | Review existing proposals, generate new options | ✅ Complete |
| **7. Sales – Unknown** | New prospect flow, proposal generation | ✅ Complete |
| **8. Bonus: Memory** | Customer-ID based proactive status updates | ✅ Complete |
| **9. Bonus: Sales HITL** | Iterative agent feedback loop, custom notes | ✅ Complete |
| **10. Bonus: Frontend** | Modern Next.js UI with interactive buttons | ✅ Complete |

---

## 💎 Bonus Features (Detailed)

### 1. Stateful Memory tied to `customer_id`
The system proactively recognizes returning customers during the authentication phase.
- **Proactive Context**: After OTP verification, the bot checks for active site issues or pending proposals associated with the `customer_id`.
- **Welcome Message**: Users are greeted with specific context, e.g., *"Welcome back, John! I see an active issue: Communication Loss."*
- **Persistent State**: Leverages the PostgreSQL persistence layer to maintain continuity across sessions.

### 2. Human-in-the-Loop Sales Assistant
Includes an iterative **Sales Agent Review** cycle before proposals reach the customer.
- **Sales Executive Role**: The graph transitions to an agent-only state for review.
- **Agent Actions**: Approve, Regenerate, Add custom technical notes, and browse **Top 5 Similar Proposals** from the database.
- **Dual-User Simulation**: Demonstrated during verification with seamless role-switching between agent and customer.

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Aegra CLI (`pip install aegra`)

### Installation Steps

```bash
# 1. Clone repository
git clone [your-repo-url]
cd sunbun-agent

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Aegra CLI
pip install aegra

# 4. Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL if needed

# 5. Start PostgreSQL
docker-compose up -d postgres

# 6. Install frontend dependencies
cd ../sunbun-ui
npm install
```

### Environment Variables (`.env`)

```env
DATABASE_URL=postgresql://sunbun_agent:sunbun_secret_2025@localhost:5433/sunbun_week2
OPENAI_API_KEY=your_key_here  # Optional (Week 2 LLM features)
```

---

## Running the Application

### Step 1: Start PostgreSQL

```bash
docker-compose up -d postgres
```

### Step 2: Start Aegra Backend

```bash
# From sunbun-agent/ directory
aegra dev
# Server starts at http://127.0.0.1:2026
```

### Step 3: Start Next.js Frontend

```bash
# From sunbun-ui/ directory
npm run dev
# Frontend starts at http://localhost:3000
```

### Step 4: Open Browser

Navigate to **http://localhost:3000** and start chatting!

### Agent Protocol Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/info` | Server health & capabilities |
| `POST` | `/threads` | Create a new conversation thread |
| `POST` | `/threads/{id}/runs` | Send a message / trigger a run |
| `GET` | `/threads/{id}/state` | Retrieve thread state |
| `POST` | `/threads/{id}/runs/stream` | Stream responses in real-time |

### Example Conversation Flow

```
User: Hello
Bot: 👋 Welcome to SunBun Solar! How can we help you today?
     [Sales Support] [Service Support]        ← Interactive buttons

User: clicks [Service Support]
Bot: Got it! Let's connect you with Service Support. 🔧
     Please choose how to verify your identity:
     [Use Email] [Use Phone]                  ← Interactive buttons

User: clicks [Use Email]
Bot: Please enter your email address:

User: john.doe@example.com
Bot: 📧 We've sent a 6-digit code to john.doe@example.com
     Enter the 6-digit code:

User: 123456
Bot: ✅ Identity verified! Welcome back, John Doe!
     ⚠️ Active Issue Detected
     Issue: Communication Loss
     Recommended Action: Please check the inverter's internet connection.
```

---

## Testing

### 1. Agent Protocol Compliance Tests

```bash
python tests/test_agent_protocol.py
```

Tests server health, thread creation, message sending, and state retrieval.

### 2. Aegra Setup Validation

```bash
python tests/test_aegra_setup.py
```

Validates Python version, dependencies, `.env`, Docker, PostgreSQL, and graph structure.

### 3. Graph Logic Tests

```bash
python tests/test_aegra_graph.py
```

Tests the compiled graph directly with multi-turn conversations.

### 4. Frontend Automation (Playwright)

```bash
pip install playwright
playwright install chromium
python tests/test_frontend_auto.py
```

Automated browser tests for frontend load, conversation flow, and session persistence.

### 5. Debug Simulation

```bash
python tests/debug_loop.py
```

Simulates a 3-turn conversation (hello → service → phone) with full state logging.

### 6. Original Flow Tests

```bash
python tests/test_flows.py
```

13 automated tests covering all auth, service, and sales paths.

### Test Results Summary

| Test Suite | Tests | Status |
|------------|-------|--------|
| Agent Protocol | 2/2 | ✅ All passing |
| Frontend Auto (Playwright) | 3/3 | ✅ All passing |
| Debug Simulation (3 turns) | 3/3 | ✅ All passing |
| Original Flow Tests | 13/13 | ✅ All passing |

---

## Project Structure

```
sunbun-agent/
│
├── aegra.json                     # Aegra configuration (graph + env)
├── docker-compose.yml             # PostgreSQL container
├── .env                           # Environment variables
├── requirements.txt               # Python dependencies
│
├── graph/                         # LangGraph implementation
│   ├── state_aegra.py             #   Aegra-compatible state (TypedDict, 64 fields)
│   ├── graph_aegra.py             #   Graph assembly, dispatcher, input isolation
│   ├── state.py                   #   Original state definition (Week 1)
│   ├── orchestrator.py            #   Original orchestrator (Week 1)
│   └── nodes/
│       ├── auth_nodes.py          #   Authentication flow nodes
│       ├── service_nodes.py       #   Service support nodes
│       └── sales_nodes.py         #   Sales support nodes
│
├── services/                      # Data access layer
│   └── data_service.py            #   CSV read/write operations
│
├── data/                          # CSV data files (13 files)
│   ├── customers.csv              #   Customer records
│   ├── sites.csv                  #   Solar site installations
│   ├── weekly_metrics.csv         #   Performance metrics
│   ├── site_issues.csv            #   Active site issues
│   ├── proposals.csv              #   Existing customer proposals
│   ├── agent_availability.csv     #   Live agent status
│   └── ...                        #   (7 more CSV files)
│
├── tests/                         # Test suite
│   ├── test_agent_protocol.py     #   Agent Protocol compliance tests
│   ├── test_aegra_setup.py        #   Aegra setup validation
│   ├── test_aegra_graph.py        #   Graph logic tests
│   ├── test_frontend_auto.py      #   Playwright frontend tests
│   ├── test_flows.py              #   Original flow tests (13 cases)
│   └── debug_loop.py              #   Debug simulation script
│
├── docs/
│   └── DEMO_SCRIPT.md             #   2-minute demo recording script
│
└── api/                           # Legacy FastAPI server (Week 1)
    └── main.py
```

```
sunbun-ui/                         # Next.js Frontend
├── src/app/
│   ├── page.tsx                   #   Main chat component
│   ├── layout.tsx                 #   App layout + metadata
│   └── globals.css                #   Global styles
├── package.json
└── tailwind.config.ts
```

---

## Design Decisions

### 1. Aegra (LangGraph Platform) over Custom FastAPI

**Decision**: Migrated from custom FastAPI server to Aegra  
**Rationale**: Aegra provides Agent Protocol compliance out-of-the-box, thread management, and PostgreSQL checkpointing with zero boilerplate.  
**Tradeoff**: Less control over HTTP layer, but significantly less code to maintain.

### 2. PostgreSQL State Persistence

**Decision**: Use PostgresSaver checkpointer with Docker Compose  
**Rationale**: Conversation state survives server restarts. Each thread gets a unique UUID, preventing stale state issues.  
**Tradeoff**: Requires Docker for local development.

### 3. Dispatcher + Input Isolation Pattern

**Decision**: Added a dispatcher node that extracts `_user_input` and implemented "consume-always" clearing  
**Rationale**: Prevents input "bleeding" where a single user message gets processed by multiple nodes in one turn. Guarantees one-time consumption.  
**Tradeoff**: Slightly more complex graph entry logic.

### 4. Interactive Buttons via Message Metadata

**Decision**: Encode buttons as `additional_kwargs.metadata.options` in AI messages  
**Rationale**: Works with the LangGraph message protocol. Frontend parses options and renders clickable buttons that send the correct value back.  
**Tradeoff**: Custom rendering logic in the frontend.

### 5. Fresh Thread Per Session

**Decision**: Generate `crypto.randomUUID()` on each page load  
**Rationale**: Prevents stale PostgreSQL state from corrupting new sessions. Users can also manually reset via the "New Chat" button.  
**Tradeoff**: No automatic session resume on refresh (but "New Chat" button provides explicit control).

### 6. Deterministic Design (Preserved from Week 1)

**Decision**: Zero LLM calls for decision-making  
**Rationale**: Every node returns a deterministic output given the same input state. All routing uses pure Python if/else logic.

---

## Known Limitations

1. **OTP Simulation** – OTPs are printed to console, not sent via real email/SMS
2. **No Real Agent Handoff** – Simulates connection to human agents
3. **CSV Data Layer** – Not scalable for production (demonstration purposes)
4. **Agent Availability** – Static CSV flag, not real-time
5. **Session Resume** – Fresh thread per page load (no automatic resume on refresh)

---

## Demo Video

**Video Walkthrough**: [Watch on Loom](https://www.loom.com/share/dce385bf48604352b990e9bd61013f0e)

Demonstrates:
1. Frontend UI with interactive buttons
2. Service support flow (email verification → issue detection)
3. Sales support flow (proposal review)
4. All automated tests passing

---

## Acknowledgments

Built for **Agentic Hackathon** by Devika Sajeesh.


The best way to see everything in action is to run `aegra dev` + `npm run dev` and follow the conversation flow. You can also run `python tests/test_agent_protocol.py` for protocol compliance verification.

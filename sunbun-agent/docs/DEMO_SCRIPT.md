# SunBun Week 2 Demo Script (2 minutes)

## Setup (Before Recording)
1. Start PostgreSQL: `docker-compose up -d postgres`
2. Start Aegra: `aegra dev` in terminal 1 (defaults to http://127.0.0.1:2026)
3. Start Frontend: `npm run dev` in terminal 2 (in sunbun-ui/)
4. Open http://localhost:3000 in Chrome
5. Position windows:
   - Frontend: Full screen or large window
   - Terminal with Aegra logs: Small window in corner (optional)

---

## Recording Script

### [0:00-0:15] Introduction & Architecture
**SAY**: "This is SunBun Solar Assistant - a production-ready AI agent built with LangGraph Platform and Aegra for Week 2."

**SHOW**: 
- Frontend homepage with SunBun branding
- Point to header: "Built with Agent Protocol compliance"

**TYPE**: "Hi" and click Send

---

### [0:15-0:45] Service Support Flow - Happy Path
**SAY**: "Let's test the Service Support flow for an existing customer."

**CLICK**: "Service Support" button

**CLICK**: "Use Email" button

**TYPE**: john.doe@example.com

**SAY**: "The system generates an OTP - in production this would be sent via email."

**TYPE**: 123456 (check console for actual OTP if different)

**SAY**: "Customer is authenticated. The system retrieves their site data from PostgreSQL and analyzes real-time metrics."

**SHOW**: Bot message showing:
- Customer greeting: "Hi John Doe from New York, NY"
- Active issue detected
- Recommended action

**CLICK**: "I'm satisfied" button

**SAY**: "Ticket auto-created. System collects NPS feedback."

**TYPE**: 9

**SAY**: "Complete service resolution in under 30 seconds."

---

### [0:45-1:15] Sales Flow with Human-in-Loop (BONUS)
**SAY**: "Now the Sales flow with our bonus feature: human-in-loop agent review."

**REFRESH** page (to start new conversation)

**CLICK**: "Sales Support" button

**CLICK**: "Use Email"

**TYPE**: john.doe@example.com

**TYPE**: 123456

**CLICK**: "Create new proposals" button

**CLICK**: "Residential" button

**TYPE**: 8000 (monthly bill)

**TYPE**: 20 (growth percentage)

**TYPE**: 2 (number of options)

**TYPE**: 1,2 (tiers: Premium, Standard)

**SAY**: "System generates proposals using deterministic formulas. Here's where human-in-loop happens - proposals are sent to sales agent for review before customer sees them."

**SHOW**: Agent review screen with:
- Generated proposals
- Agent action buttons (Approve, Regenerate, Add notes, etc.)

**CLICK**: "Approve and send" button

**SAY**: "Agent approved. Customer now sees the proposals."

**SHOW**: Proposals displayed to customer

---

### [1:15-1:40] State Persistence Demo
**SAY**: "Key feature: durable state persistence with PostgreSQL."

**SHOW**: Session ID in header

**SAY**: "Let me refresh the page to simulate a connection loss."

**REFRESH** page (F5)

**SAY**: "Notice the session ID is the same. The conversation state is fully preserved."

**SHOW**: 
- Same session ID
- All messages still visible
- Can continue conversation

**TYPE**: 1 (select first proposal)

**SAY**: "We resume exactly where we left off. This is powered by Aegra's built-in checkpointing."

---

### [1:40-2:00] Closing & Technical Summary
**SAY**: "Let me show you the architecture quickly."

**SWITCH** to code editor (optional) or show architecture diagram

**SAY**: "This system demonstrates:
1. ✅ Agent Protocol compliance - industry standard endpoints
2. ✅ PostgreSQL state persistence - durable execution
3. ✅ Human-in-loop workflows - sales agent review
4. ✅ Interactive buttons - better UX than pure text
5. ✅ Production deployment ready - Docker + Aegra platform

All built on LangGraph Platform for Week 2."

**SHOW**: Terminal with Aegra running

**SAY**: "The graph is deterministic for core logic, with optional LLM enhancement for natural language understanding. Thank you!"

---

## Recording Tips

1. **Pace**: Speak clearly, don't rush
2. **Mouse**: Hover over buttons briefly before clicking (viewers can see what you're clicking)
3. **Terminal**: Keep Aegra logs visible in corner to show real-time processing
4. **Preparation**: Do a full test run before recording
5. **Backup**: If something fails, have a fallback demo path ready

## What to Highlight

✅ **Must Show**:
- Agent Protocol endpoints working
- State persistence (refresh demo)
- Human-in-loop (agent review)
- Buttons rendering correctly
- Professional UI

⭐ **Nice to Have**:
- Show Aegra terminal logs
- Show database tables in pgAdmin (optional)
- Show mermaid graph diagram

## After Recording

1. Upload to Loom/YouTube (unlisted)
2. Add link to README.md
3. Include timestamp links for key features:
   - 0:15 - Service Flow
   - 0:45 - Sales with Human-in-Loop
   - 1:15 - State Persistence Demo

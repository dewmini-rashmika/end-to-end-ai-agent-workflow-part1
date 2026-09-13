# ✈️ TripMate AI — LangGraph Multi-Agent Travel Planner

> **Part 1: Full-stack AI travel planner — FastAPI backend + Next.js 14 frontend**

A production-grade AI travel planning system built with **LangGraph**, **Groq (Llama 3)**, **FastAPI**, **PostgreSQL**, and a **Next.js 14 React frontend**. Four specialist agents collaborate through a shared state graph to turn a single natural-language query into a complete, day-by-day travel plan — streamed in real time to the browser via SSE.

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│              Next.js 14 Frontend (port 3000)      │
│  Home Page → TripForm → AgentTimeline (SSE)      │
│  Trip Detail Page (FlightCard, HotelCard, etc.)  │
│  History Page (session conversations)            │
└────────────────────┬─────────────────────────────┘
                     │  HTTP + SSE (text/event-stream)
┌────────────────────▼─────────────────────────────┐
│              FastAPI Backend (port 8000)          │
│  POST /api/v1/trips/plan/stream  ← SSE endpoint  │
│  POST /api/v1/trips/plan         ← JSON endpoint  │
│  POST /api/v1/trips/{id}/followup                │
│  GET  /api/v1/sessions/{id}/history              │
└────────────────────┬─────────────────────────────┘
                     │  LangGraph + Postgres
┌────────────────────▼─────────────────────────────┐
│              LangGraph Workflow                   │
│  parse_query → flight_agent → hotel_agent        │
│                   → itinerary_agent              │
│                        → final_response_agent    │
└────────────────────┬─────────────────────────────┘
                     │  Persisted via AsyncPostgresSaver
                PostgreSQL (checkpoints + results)
```

| Agent | Tools | Output |
|---|---|---|
| **Parse Query** | LLM NLU | Structured trip parameters |
| **Flight Agent** | AviationStack API, Tavily Search | `flight_results` |
| **Hotel Agent** | Google Places API, Tavily Search | `hotel_results` |
| **Itinerary Agent** | Tavily Search, Google Maps Directions | `itinerary` |
| **Final Response Agent** | Tavily Search (tips/budget) | `final_response` |

---

## Project Structure

```
.
├── src/end_to_end_ai_agent_workflow_part1/     # FastAPI backend
│   ├── config/
│   │   ├── settings.py        # All settings incl. LangSmith, rate limits, CORS
│   │   └── prompts.py         # Agent system prompts
│   ├── agents/
│   │   ├── base_agent.py      # BaseAgent with LangSmith run metadata
│   │   ├── flight_agent.py
│   │   ├── hotel_agent.py
│   │   ├── itinerary_agent.py
│   │   └── final_response_agent.py
│   ├── graph/
│   │   ├── nodes.py           # One node function per agent
│   │   ├── edges.py           # Routing + conditional edges
│   │   ├── workflow.py        # StateGraph builder
│   │   └── runner.py          # GraphRunner (invoke + SSE streaming + DB)
│   ├── middleware/
│   │   ├── rate_limit.py      # slowapi Limiter (X-Forwarded-For aware)
│   │   ├── security.py        # Security headers
│   │   └── logging_middleware.py
│   ├── routes/
│   │   ├── trips.py           # /plan, /plan/stream (SSE), /followup
│   │   ├── sessions.py        # History, preferences
│   │   └── health.py
│   ├── utils/
│   │   └── langsmith_setup.py # configure_langsmith() + run metadata helpers
│   └── app.py                 # FastAPI factory (CORS, rate limiter, lifespan)
│
└── frontend/                                   # Next.js 14 frontend
    └── src/
        ├── app/
        │   ├── layout.tsx             # Root layout (fonts, Toaster)
        │   ├── globals.css            # CSS design tokens + Tailwind base
        │   ├── (marketing)/
        │   │   ├── layout.tsx         # Navbar + Footer wrapper
        │   │   └── page.tsx           # Home page (hero + TripForm)
        │   ├── trip/[sessionId]/
        │   │   └── page.tsx           # Trip detail page
        │   └── history/
        │       └── page.tsx           # Session history page
        ├── components/
        │   ├── ui/                    # shadcn/ui primitives
        │   ├── layout/
        │   │   ├── Navbar.tsx
        │   │   └── Footer.tsx
        │   ├── shared/
        │   │   ├── LoadingSpinner.tsx
        │   │   └── ErrorAlert.tsx
        │   └── trip/
        │       ├── TripForm.tsx       # Search form
        │       ├── AgentTimeline.tsx  # Real-time SSE progress
        │       ├── TripResult.tsx     # Tabbed results view
        │       ├── FlightCard.tsx
        │       ├── HotelCard.tsx
        │       └── ItineraryDay.tsx
        ├── hooks/
        │   ├── use-trip-planner.ts   # SSE orchestration hook
        │   ├── use-follow-up.ts      # Follow-up message hook
        │   ├── use-session-history.ts
        │   └── use-toast.ts
        ├── lib/
        │   ├── api.ts               # Typed API client + streamTripPlan()
        │   └── utils.ts
        ├── store/
        │   └── trip-store.ts        # Zustand store (session, steps, plan)
        └── types/
            └── index.ts             # TypeScript types (mirror Pydantic schemas)
```

---

## Setup

### 1. Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- Node.js 18+ and npm
- PostgreSQL 14+ running locally or via Docker

### 2. Clone & Install — Backend

```bash
git clone <your-repo-url>
cd end-to-end-ai-agent-workflow-part1

# Install all Python dependencies
uv sync
```

### 3. Clone & Install — Frontend

```bash
cd frontend
npm install
```

### 4. Environment Variables — Backend

```bash
cp .env.example .env
```

Open `.env` and fill in:

| Variable | Required | Notes |
|---|---|---|
| `GROQ_API_KEY` | ✅ | [console.groq.com](https://console.groq.com) |
| `TAVILY_API_KEY` | ✅ | [tavily.com](https://tavily.com) |
| `AVIATIONSTACK_API_KEY` | ✅ | [aviationstack.com](https://aviationstack.com) — free tier works |
| `POSTGRES_USER` | ✅ | Your Postgres username |
| `POSTGRES_PASSWORD` | ✅ | Your Postgres password |
| `LANGSMITH_API_KEY` | ⬜ | [smith.langchain.com](https://smith.langchain.com) — enables tracing |
| `GOOGLE_MAPS_API_KEY` | ⬜ | Optional — hotel ratings + directions |

### 5. LangSmith Setup (Optional but Recommended)

LangSmith provides a visual trace of every LangGraph run — invaluable for debugging.

1. Sign up at [smith.langchain.com](https://smith.langchain.com)
2. Create a project named `tripmate-ai`
3. Copy your API key
4. In your `.env`:

```dotenv
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=ls__your_key_here
LANGSMITH_PROJECT=tripmate-ai
LANGCHAIN_TRACING_V2=true
```

Once enabled, every agent invocation (flight search, hotel search, itinerary generation, final response) appears as a named trace in the LangSmith UI with full token usage and timing breakdowns.

### 6. Environment Variables — Frontend

```bash
cd frontend
cp .env.local.example .env.local
```

The only required variable is:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 7. Database

Create the database (schema is auto-created on startup):

```sql
CREATE DATABASE tripmate_db;
CREATE USER tripmate_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE tripmate_db TO tripmate_user;
```

Or with Docker:

```bash
docker run -d \
  --name tripmate-postgres \
  -e POSTGRES_DB=tripmate_db \
  -e POSTGRES_USER=tripmate_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:16
```

### 8. Run — Full Stack

#### Terminal 1 — Backend

```bash
# Via uv (recommended)
uv run end-to-end-ai-agent-workflow-part1

# Or directly
uv run uvicorn end_to_end_ai_agent_workflow_part1.app:app --reload --port 8000
```

#### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — the app is live!

API docs (dev mode): [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Reference

### Plan a Trip (JSON)

```http
POST /api/v1/trips/plan
Content-Type: application/json

{
  "user_query": "Plan a 5-day trip from Colombo to Tokyo in October 2026 for 2 people with a mid-range budget. We love food and temples.",
  "num_travelers": 2,
  "budget": "mid-range"
}
```

### Plan a Trip (SSE Streaming)

```http
POST /api/v1/trips/plan/stream
Content-Type: application/json
Accept: text/event-stream

{ "user_query": "..." }
```

Events received:
- `event: start` — pipeline started
- `event: agent_update` — one per agent as it completes
- `event: done` — complete `TripPlanResponse` JSON
- `event: error` — error message

### Follow Up

```http
POST /api/v1/trips/{session_id}/followup
Content-Type: application/json

{ "message": "Can you suggest a cheaper hotel option?" }
```

### Session History

```http
GET /api/v1/sessions/{session_id}/history
```

### Health Checks

```http
GET /health          # Liveness
GET /health/ready    # Readiness (checks DB)
```

---

## Production Hardening (included)

| Feature | Implementation |
|---|---|
| **Rate limiting** | `slowapi` — 10 req/min on `/plan`, 100 req/min global |
| **CORS** | Configurable via `CORS_ORIGINS` env var |
| **Security headers** | `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` |
| **Request logging** | `X-Request-ID` header, per-request timing |
| **LangSmith tracing** | Full LangGraph traces with agent tags and session metadata |
| **Postgres checkpointing** | Conversations survive restarts, resumable with follow-ups |
| **SSE streaming** | `X-Accel-Buffering: no` disables Nginx buffering |

---

## Key Design Decisions

- **Shared TravelState** — all agents read and write to a single TypedDict. Reducers (`operator.add`, `add_messages`) handle concurrent updates safely.
- **Postgres checkpointing** — every graph run is persisted via `AsyncPostgresSaver`. Conversations survive restarts and can be resumed with a follow-up.
- **Graceful fallbacks** — every tool has a Tavily web-search fallback. Google Maps degrades silently if the API key is missing.
- **ReAct loop** — `services/agent_executor.py` runs each agent's full tool-use loop independently, keeping graph nodes clean and testable.
- **SSE streaming** — the frontend's `streamTripPlan()` function opens a persistent fetch stream and dispatches typed callbacks per event type.
- **Zustand store** — all transient UI state (agent steps, current plan, error) lives in a Zustand store persisted to `sessionStorage`. Only session identity and history are persisted.

---

## Environment Notes

- **Free tier limits**: AviationStack free tier only returns scheduled flight data (no real-time), no prices. Agents use Tavily as a fallback automatically.
- **Groq rate limits**: `llama-3.3-70b-versatile` has generous free-tier limits but each trip plan makes ~5 LLM calls. Monitor usage at [console.groq.com](https://console.groq.com).
- **Tavily credits**: Advanced search costs 2 credits per call.

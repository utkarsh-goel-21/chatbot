# BizBot — AI-Powered Business Intelligence Chatbot

A full-stack AI chatbot that lets businesses query their own data using plain English. Ask questions in natural language and get instant, accurate answers from your database and documents — no SQL knowledge required.

**Live:** Frontend on [Vercel](https://chatbot-flax-tau-13.vercel.app) · Backend on [Render](https://bizbot-4vlu.onrender.com) · Database on Supabase (PostgreSQL + pgvector)

---

## What It Does

Authenticated users can ask questions like:

- _"How many orders do I have?"_
- _"What products have I purchased most?"_
- _"Show me my total spending in 2014."_
- _"Are there any duplicate items in my orders?"_
- _"Give me an overview of my purchasing patterns."_

BizBot automatically figures out the best way to answer — whether that means querying the database live with SQL, retrieving relevant insight documents, or combining both — and returns a clean, human-readable response.

---

## Architecture Overview

```
User Message (POST /chat)
         ↓
   ┌─────────────┐
   │ Query Router │  ← classifies the intent (LLM, llama-3.1-8b-instant)
   └──────┬──────┘
          │
    ┌─────┴──────┬────────────┐
    ▼            ▼            ▼
TEXT_TO_SQL     RAG         HYBRID
    │            │       (runs both in parallel)
    ▼            ▼            │
Generate     Retrieve      Merge &
  SQL →      Docs →        Combine
Execute →   Generate         │
Format        Answer         ▼
    │            │      Combined Answer
    └─────┬──────┘
          ▼
  Natural Language Answer
```

### The Four Routes

| Route | When Used | Pipeline |
|---|---|---|
| `TEXT_TO_SQL` | Counts, totals, lists, filters, queries | LLM → SQL → PostgreSQL → Format |
| `RAG` | Trends, summaries, insights, analysis | pgvector search → LLM answer |
| `HYBRID` | Questions asking for data + analysis | Both pipelines in parallel, then merged |
| `BLOCKED` | Off-topic, harmful, or system-level queries | Polite redirect via LLM |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, Uvicorn, SQLAlchemy, psycopg2-binary |
| **LLM** | Groq API — `llama-3.3-70b-versatile` (smart), `llama-3.1-8b-instant` (fast) |
| **Embeddings** | `fastembed` — `all-MiniLM-L6-v2` (local, no API needed) |
| **Vector Store** | Supabase pgvector (`rag_documents` table) |
| **Database** | Supabase PostgreSQL (AdventureWorks dataset) |
| **Frontend** | React 19, TypeScript, Vite, Zustand, Tailwind CSS v4, shadcn/ui |
| **Auth** | Supabase Auth (Google OAuth + email/password) |
| **File Uploads** | `pypdf2`, `python-multipart`, psycopg2 `COPY FROM STDIN` |

---

## Project Structure

```
chatbot/
├── main.py                        # FastAPI app — all endpoints, lifespan seeding
├── requirements.txt               # Python dependencies
├── .env                           # Secrets (DATABASE_URL, GROQ_API_KEY_*, HF_API_KEY)
│
├── router/
│   └── query_router.py            # Classifies query → TEXT_TO_SQL / RAG / HYBRID / BLOCKED
│
├── text_to_sql/
│   ├── schema_loader.py           # Reads live DB schema (multi-schema: sales.*, person.*, etc.)
│   ├── sql_generator.py           # LLM generates SQL + validates tenant isolation
│   ├── sql_executor.py            # Executes SQL against Supabase with 10s timeout
│   └── db_setup.py                # Verifies AdventureWorks, creates uploaded_tables
│
├── rag/
│   ├── embedder.py                # Embeds docs into pgvector (rag_documents table)
│   ├── retriever.py               # Semantic similarity search using fastembed
│   ├── answer_generator.py        # Generates RAG answers from retrieved docs
│   ├── generate_insights.py       # Generates LLM insight docs per customer at startup
│   └── sample_docs.py             # (legacy) Manual doc seeding
│
├── utils/
│   ├── groq_client.py             # Multi-key Groq client with round-robin rotation + fallback
│   └── file_processor.py          # Handles CSV / PDF / TXT uploads per tenant
│
└── frontend/
    ├── .env                        # VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL
    └── src/
        ├── App.tsx                 # Root component with auth state
        ├── index.css               # Global styles (Warm Ember dark + Warm Parchment light)
        ├── lib/
        │   ├── api.ts              # Backend API calls (chat, upload, data-sources)
        │   └── supabase.ts         # Supabase client init
        ├── store/
        │   └── chatStore.ts        # Zustand store — sessions, messages, user state
        └── components/
            ├── auth/
            │   └── AuthModal.tsx   # Login / Signup modal (Supabase Auth)
            └── chat/
                ├── Sidebar.tsx         # Session list, user switcher, settings gear
                ├── ChatArea.tsx        # Message thread display
                ├── ChatInput.tsx       # Input bar + file upload button
                ├── MessageBubble.tsx   # Individual message rendering
                ├── MarkdownRenderer.tsx # Renders markdown in AI responses
                ├── RouteBadge.tsx      # Shows TEXT_TO_SQL / RAG / HYBRID badge
                ├── SettingsModal.tsx   # Data sources viewer (uploaded CSVs + docs)
                ├── WelcomeScreen.tsx   # Shown on new empty sessions
                └── ThinkingIndicator.tsx # "BizBot is thinking..." animation
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [Supabase](https://supabase.com) project with AdventureWorks loaded (PostgreSQL + pgvector extension enabled)
- At least one [Groq API key](https://console.groq.com) (free)

---

### Backend Setup

#### 1. Clone the repository

```bash
git clone <your-repo-url>
cd bizbot/chatbot
```

#### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `fastembed` will automatically download the `all-MiniLM-L6-v2` model on first run (~90MB). No API key required.

#### 4. Configure environment variables

Create a `.env` file in the `chatbot/` directory:

```env
# Supabase PostgreSQL connection string
DATABASE_URL=postgresql://postgres:<password>@<host>:5432/postgres

# Groq API keys — add as many as you have (up to 5) for rate-limit rotation
GROQ_API_KEY=gsk_...
GROQ_API_KEY_ONE=gsk_...
GROQ_API_KEY_TWO=gsk_...
GROQ_API_KEY_THREE=gsk_...
GROQ_API_KEY_FOUR=gsk_...
```

#### 5. Run the backend server

```bash
uvicorn main:app --reload
```

The server starts at `http://127.0.0.1:8000`.

On first startup, BizBot will automatically:
- Verify the AdventureWorks database connection
- Create the `uploaded_tables` registry table
- Generate AI insight documents for the two demo users (Dalton Perez, Mason Roberts)
- Warm up the embedding model, schema cache, and LLM connection

---

### Frontend Setup

#### 1. Navigate to the frontend directory

```bash
cd frontend
```

#### 2. Install dependencies

```bash
npm install
```

#### 3. Configure environment variables

Create a `.env` file in `frontend/`:

```env
VITE_SUPABASE_URL=https://<your-project>.supabase.co
VITE_SUPABASE_ANON_KEY=<your-anon-key>
VITE_API_URL=http://localhost:8000
```

#### 4. Run the development server

```bash
npm run dev
```

Frontend runs at `http://localhost:5173`. The backend must also be running.

---

## Authentication & Users

BizBot uses **Supabase Auth** with two modes:

| Mode | How it works |
|---|---|
| **Guest (Demo)** | Switch between two pre-loaded demo users — Dalton Perez (11091) or Mason Roberts (11176). No signup needed. |
| **Authenticated** | Sign up with email/password or Google OAuth. Your Supabase UUID is hashed to a stable integer ID for backend compatibility. Authenticated users can upload their own files. |

> Authenticated users are fully isolated — they can only see their own data. Cross-tenant access is blocked at both the SQL generation and validation layers.

---

## API Reference

### `GET /`
Health check. Returns `{"status": "BizBot backend is running"}`.

### `GET /health`
Returns `{"status": "ok"}`.

### `POST /chat`
Main chat endpoint.

**Request:**
```json
{
  "question": "How many orders do I have?",
  "user_id": 11091,
  "history": [
    {"role": "user", "content": "What products did I buy?"},
    {"role": "assistant", "content": "You purchased 25 unique products."}
  ]
}
```

**Response:**
```json
{
  "question": "How many orders do I have?",
  "route": "TEXT_TO_SQL",
  "answer": "You have 28 orders on record."
}
```

The `route` field indicates which pipeline handled the question — useful for debugging.

### `POST /upload`
Upload a file for the authenticated user.

**Form Data:**
- `file` — `.csv`, `.pdf`, or `.txt`
- `user_id` — integer customer ID

**CSV files** are loaded into a private PostgreSQL table (`customer_{id}_{filename}`) and become immediately queryable.
**PDF/TXT files** are chunked, embedded, and stored in the pgvector RAG store.

### `GET /data-sources?user_id={id}`
Returns all uploaded CSV tables and indexed documents for a user.

```json
{
  "status": "success",
  "data": {
    "csvs": [{"filename": "sales_q1.csv", "table_name": "customer_11091_sales_q1", "type": "csv", "created_at": "..."}],
    "documents": [{"filename": "report_2024", "type": "pdf/txt"}]
  }
}
```

---

## Security & Tenant Isolation

BizBot enforces strict multi-tenant data isolation at multiple levels:

1. **SQL Validation Layer** (`sql_generator.py`): Every generated SQL query is validated before execution. Queries touching base tables (`sales.*`, `person.*`, etc.) **must** contain `WHERE customerid = {user_id}`. Inequality bypasses (`!=`, `<>`) and cross-tenant ID injections are blocked.

2. **Uploaded Table Isolation**: User-uploaded CSV tables are named `customer_{id}_{filename}`. The validator ensures no query can reference another user's table.

3. **Destructive Statement Blocking**: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, and `CREATE` are all blocked.

4. **Query Timeout**: All SQL executions have a 10-second `statement_timeout` to prevent runaway queries.

---

## LLM & Rate Limit Strategy

- **Two model tiers:** `llama-3.3-70b-versatile` for SQL generation and answer formatting; `llama-3.1-8b-instant` for routing and simple tasks.
- **Multi-key rotation:** Up to 5 Groq API keys are loaded and rotated in round-robin. On a 429 rate limit, the next key is tried automatically.
- **Token caps:** Each LLM call has a strict `max_tokens` budget (router: 10, SQL: 256, answer: 512, RAG: 512).
- **Fallback:** If all keys are exhausted, the system falls back to the fast 8b model rather than crashing.

---

## Adding Your Own Data

### Upload via the UI
Click the **paperclip icon** in the chat input to upload:
- **CSV** → instantly queryable as a private database table
- **PDF / TXT** → chunked and indexed for RAG-based Q&A

### Add data programmatically
- **Database tables:** Extend `text_to_sql/db_setup.py` — the schema loader reads the DB dynamically, so the LLM will automatically be aware of new tables.
- **RAG documents:** Use `rag/embedder.py`'s `embed_documents()` directly with a list of `{id, text, user_id}` dicts.

---

## UI Theme

BizBot ships with a dual-theme design system:

| Token | Dark Mode (Warm Ember) | Light Mode (Warm Parchment) |
|---|---|---|
| Background | `#222220` | `#FBF7F2` |
| Surface | `#1c1b19` | `#F3EDE3` |
| Elevated | `#2c2b28` | `#FFFFFF` |
| Accent | `#f09438` | `#B86830` |

**Fonts:** Instrument Sans (body) · JetBrains Mono (code)

---

## Notes

- The backend auto-seeds AI insight documents for demo users on first startup — this takes ~30 seconds on a cold start (Render free tier).
- ChromaDB is **not** used — the project migrated to Supabase pgvector for vector storage.
- SQLite is **not** used — all data is on Supabase PostgreSQL.
- Supabase Auth UUIDs are hashed to stable 53-bit integers via `uuidToInt53` for backend compatibility.
- A keep-alive thread pings the Render backend every 10 minutes to prevent cold starts.

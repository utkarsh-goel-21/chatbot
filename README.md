# Business Chatbot — AI-Powered Business Intelligence API

A backend API that allows businesses to query their own data using plain English. Built with FastAPI, Groq LLM, Text-to-SQL, and RAG (Retrieval Augmented Generation).

---

## What It Does

Business owners can ask natural language questions like:

- _"How many transactions happened today?"_
- _"What was our total revenue this week?"_
- _"What products do we sell?"_
- _"How has our business been performing?"_
- _"What do customers complain about?"_

The system automatically determines the best way to answer and returns a clean, human-readable response.

---

## Architecture

```
User Question (POST /chat)
        ↓
   AI Query Router
   (classifies the question)
      /           \
Text-to-SQL        RAG
(live DB data)     (documents & reports)
      \           /
   Final Natural Language Answer
```

**Text-to-SQL** — for quantitative, data-driven questions. Converts the question to SQL, runs it on the database, and formats the result.

**RAG** — for qualitative, insight-driven questions. Finds the most relevant business documents and generates an answer from them.

---

## Tech Stack

| Layer             | Technology                               |
| ----------------- | ---------------------------------------- |
| Backend Framework | FastAPI                                  |
| LLM Provider      | Groq (free)                              |
| LLM Model         | llama-3.3-70b-versatile                  |
| Database          | SQLite (via SQLAlchemy)                  |
| Vector Store      | ChromaDB                                 |
| Embeddings        | sentence-transformers (all-MiniLM-L6-v2) |
| Language          | Python 3.10+                             |

---

## Project Structure

```
business-chatbot/
│
├── main.py                        # FastAPI entry point, /chat endpoint
├── .env                           # API keys and DB config (not committed)
├── requirements.txt               # All dependencies
│
├── router/
│   └── query_router.py            # Routes questions to SQL or RAG
│
├── text_to_sql/
│   ├── schema_loader.py           # Reads DB schema dynamically
│   ├── sql_generator.py           # LLM generates SQL from question
│   ├── sql_executor.py            # Runs SQL on the database
│   └── db_setup.py                # Seeds sample business data
│
├── rag/
│   ├── embedder.py                # Embeds documents into ChromaDB
│   ├── retriever.py               # Finds relevant docs by similarity
│   ├── answer_generator.py        # LLM generates answer from docs
│   └── sample_docs.py             # Seeds sample business documents
│
└── utils/
    └── groq_client.py             # Shared Groq LLM client
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd business-chatbot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root:

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=sqlite:///./business.db
```

Get your free Groq API key at [console.groq.com](https://console.groq.com)

### 4. Set up the database

```bash
python -m text_to_sql.db_setup
```

### 5. Seed the vector store

```bash
python -m rag.sample_docs
```

### 6. Run the server

```bash
uvicorn main:app --reload
```

Server runs at `http://127.0.0.1:8000`

---

## API Usage

### Health Check

```
GET /
```

Response:

```json
{ "status": "Business Chatbot is running" }
```

### Chat Endpoint

```
POST /chat
Content-Type: application/json

{ "question": "How many transactions happened today?" }
```

Response:

```json
{
  "question": "How many transactions happened today?",
  "route": "TEXT_TO_SQL",
  "answer": "There were 3 transactions that took place today."
}
```

### Example Questions

| Question                              | Route       |
| ------------------------------------- | ----------- |
| How many sales did we make today?     | TEXT_TO_SQL |
| What was our total revenue this week? | TEXT_TO_SQL |
| What products do we sell?             | TEXT_TO_SQL |
| What payment types were used today?   | TEXT_TO_SQL |
| How has our business been performing? | RAG         |
| What are our payment trends?          | RAG         |
| What do customers complain about?     | RAG         |

---

## Adding Your Own Data

### Adding database tables

Edit `text_to_sql/db_setup.py` to add your own tables and data. The schema loader reads the database dynamically so the LLM will automatically be aware of new tables.

### Adding business documents

Edit `rag/sample_docs.py` to add your own business reports, summaries, or any text-based knowledge. Re-run:

```bash
python -m rag.sample_docs
```

---

## Notes

- The `route` field in the API response shows which pipeline handled the question — useful for debugging
- ChromaDB persists embeddings to `chroma_db/` folder — no need to re-embed on server restart
- Swap SQLite for PostgreSQL or MySQL by updating `DATABASE_URL` in `.env` — no code changes needed
- Swap Groq for any OpenAI-compatible provider by updating `groq_client.py`

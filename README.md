# AgentFlow

AgentFlow is a full-stack AI agent portfolio project that combines chat, retrieval-augmented generation, execution tracing, document indexing, and an early internal tool-calling workflow.

## Overview

AgentFlow is built as an interview-ready AI application rather than a single-script demo. The current MVP lets a user create chat conversations, upload text documents, index document chunks into Qdrant, ask grounded questions over those documents, and inspect the execution trace behind each assistant reply.

The project also includes a first internal tool-calling slice. The assistant can request internal tools, the backend executes those tools, and tool events are persisted on the run detail trace. Provider compatibility is still an active area: DashScope accepts the first tool request but rejects standard post-tool `tool` and `function` roles, so the app uses a DashScope-specific trusted-context fallback for the final post-tool response.

## Implemented Features

- Chat workspace with persisted conversations and messages.
- AI assistant replies through an OpenAI-compatible Responses API client.
- Conversation deletion with cascading cleanup for messages, runs, run sources, and tool events.
- Document upload for `.txt` and `.md` files.
- Exact-content document deduplication using a stable text hash.
- Text chunking, embedding generation, and Qdrant vector indexing.
- Document deletion with PostgreSQL metadata cleanup and Qdrant point deletion.
- RAG flow that retrieves top matching chunks before assistant generation.
- Fallback behavior when no indexed documents or Qdrant collection are available.
- Run records for each user message send, including status, model/provider, errors, and timestamps.
- Run detail view with retrieved source previews.
- Internal tool events attached to runs, including ordered `step_index`, tool name, arguments, status, and short result preview.
- Basic readiness checks for PostgreSQL, Redis, Qdrant, and LLM configuration.

## Tech Stack

- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, Pydantic
- Database: PostgreSQL
- Vector store: Qdrant
- Cache service: Redis
- AI client: OpenAI Python SDK against OpenAI-compatible providers
- Migrations: Alembic
- Local infrastructure: Docker Compose

## Architecture

```text
apps/
  api/                    FastAPI backend
    app/api/routes/       Thin HTTP route handlers
    app/services/         Business logic for chat, documents, tools
    app/repositories/     SQLAlchemy persistence boundaries
    app/models/           SQLAlchemy models
    app/schemas/          Pydantic response/request models
    app/core/             Config, database, Redis, Qdrant, LLM clients
    alembic/              Database migrations

  web/                    Next.js frontend
    src/app/              App Router pages
    src/components/       UI components
    src/features/         Feature-level state and orchestration
    src/lib/api/          Typed API client boundary
```

At a high level:

1. The frontend calls the FastAPI backend through a typed API client.
2. Chat messages are persisted in PostgreSQL.
3. Each user message creates a `Run` record.
4. Document chunks are embedded and stored in Qdrant with metadata payloads.
5. Retrieval sources and tool events are attached to the run for traceability.
6. The run detail panel shows what happened during generation.

## Current Workflows

### Basic Chat Flow

1. Open `/chat`.
2. Create a conversation.
3. Send a message.
4. The backend saves the user message, creates a run, calls the LLM, saves the assistant message, and marks the run completed.
5. The frontend refreshes messages and run trace data.

### RAG Document Upload and Retrieval Flow

1. Open `/documents`.
2. Upload a `.txt` or `.md` file.
3. The backend extracts normalized text, computes a content hash, chunks the text, generates embeddings, stores chunk metadata in PostgreSQL, and writes vectors to Qdrant.
4. Ask a question in `/chat` that matches the uploaded content.
5. The backend retrieves top chunks from Qdrant and includes them as grounded context for the assistant.
6. The selected run detail shows retrieved source previews.

### Run Trace and Run Detail Flow

1. Every message send creates a run.
2. Runs track `pending`, `completed`, or `failed`.
3. Run detail includes provider/model, linked user message preview, retrieved sources, tool events, timestamps, and error messages.
4. This makes successful and failed agent behavior inspectable from the UI.

### Internal Tool-Calling Status

Implemented internal tools:

- `list_documents`: returns uploaded document records.
- `get_run_detail`: returns compact detail for a run.
- `search_documents`: searches indexed chunks using an explicit query.

Current behavior:

- The first tool request path is implemented through the Responses API tool interface.
- Tool execution is internal only and persisted as `tool_events`.
- The app supports one tool round, followed by one final assistant response.
- For standard compatible providers, post-tool results use the Responses API `function_call_output` flow.
- For DashScope, standard post-tool roles are not accepted. DashScope rejects `tool` and `function` roles, so AgentFlow uses a provider-specific fallback that sends compact trusted tool results as supported plain-text context.

This tool-calling slice is functional but still a prototype. It is intentionally limited to internal tools, one tool round, and short result previews.

## Local Setup

### Prerequisites

- Docker Desktop or compatible Docker runtime
- Python 3.11+
- Node.js 20+
- npm

### Environment

Create a local `.env` file at the repository root. Required categories:

- PostgreSQL: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`, `DATABASE_URL`
- Redis: `REDIS_PORT`, `REDIS_URL`
- Qdrant: `QDRANT_PORT`, `QDRANT_GRPC_PORT`, `QDRANT_URL`, `QDRANT_COLLECTION_NAME`
- LLM provider: `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`
- Embeddings provider: `EMBEDDING_PROVIDER`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_BASE_URL`
- Frontend API URL: `NEXT_PUBLIC_API_BASE_URL`
- Optional RAG tuning: `RAG_TOP_K`, `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`

Do not commit real API keys.

Example local shape:

```env
PROJECT_ENV=development

POSTGRES_DB=agentflow
POSTGRES_USER=agentflow
POSTGRES_PASSWORD=agentflow
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://agentflow:agentflow@localhost:5432/agentflow

REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=document_chunks

LLM_PROVIDER=dashscope
LLM_API_KEY=your_provider_key
LLM_MODEL=qwen3-max
LLM_BASE_URL=your_openai_compatible_base_url

EMBEDDING_PROVIDER=dashscope
EMBEDDING_API_KEY=your_provider_key
EMBEDDING_MODEL=your_embedding_model
EMBEDDING_BASE_URL=your_openai_compatible_base_url

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Start Docker Services

```powershell
docker compose up -d postgres redis qdrant
```

or:

```powershell
make up
```

### Backend

```powershell
cd apps/api
python -m pip install -e .
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API docs:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

### Frontend

```powershell
cd apps/web
npm install
npm run dev
```

Frontend app:

```text
http://localhost:3000
```

## Main Pages and Routes

Frontend:

- `/chat`: conversation workspace, message thread, run trace, run detail.
- `/documents`: upload, list, index status, and delete documents.

Backend:

- `/docs`: Swagger/OpenAPI docs.
- `/health`: readiness check.
- `/conversations`: conversation CRUD and message creation.
- `/documents`: document upload/list/delete.
- `/runs/{run_id}`: run detail with sources and tool events.

## Current Status

Complete enough for MVP demonstration:

- End-to-end chat with persisted conversations/messages.
- RAG over uploaded `.txt` and `.md` documents.
- Qdrant-backed retrieval with source attribution.
- Run-level observability for retrieval, failures, and internal tools.
- Minimal document lifecycle: upload, deduplicate, list, delete.
- Minimal conversation lifecycle: create, list, select, delete.

Still prototype or limited:

- No authentication or multi-user isolation.
- No background workers for indexing.
- No streaming responses.
- No external web search.
- No advanced reranking.
- No production deployment hardening.
- Tool calling is one-round only.
- Provider tool-call compatibility varies; DashScope requires the trusted-context fallback for post-tool answers.

## Future Improvements

- Add authentication and per-user data isolation.
- Add background ingestion workers with Redis-backed queues.
- Add streaming assistant responses.
- Add richer citations directly below assistant messages.
- Add document reindexing and indexing failure recovery.
- Add external tools such as web search behind explicit allowlists.
- Add automated backend and frontend test coverage.
- Add production deployment configuration and observability.
- Expand tool calling into a controlled multi-step agent loop.

## Engineering Focus

AgentFlow explores the engineering problems behind practical AI applications:

- preserving a clean full-stack architecture while adding AI workflows;
- making LLM behavior observable through runs, sources, and tool events;
- handling provider compatibility instead of assuming perfect OpenAI parity;
- keeping retrieval, persistence, and UI state understandable enough to discuss in interviews;
- building incrementally from CRUD to RAG to traceable tool use.

The project is not production-ready, but it is designed to show production-style thinking: clear boundaries, persistent state, local infrastructure, migrations, graceful fallbacks, and transparent execution traces.

# AGENTS.md

## Project goal
This repository is a portfolio-grade full-stack AI agent project for a new graduate job search.
The project should look like a real production-style system, not a toy demo.

## Target stack
- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL
- Cache/queue: Redis
- AI: OpenAI Responses API + tool calling
- Retrieval: Qdrant
- Deployment: Docker Compose

## What to optimize for
- Clear architecture
- Readable code
- Good project structure for interviews
- Easy local startup
- Incremental delivery

## Coding rules
- Prefer small, modular files.
- Keep route handlers thin.
- Put business logic into services.
- Add basic error handling.
- Do not introduce unnecessary abstractions.
- Do not modify unrelated files.

## Workflow rules
Before coding:
1. Read the current repository first.
2. Propose a short plan.
3. Ask for clarification only if absolutely necessary.

When coding:
1. Work in small steps.
2. Show which files will be changed.
3. Keep changes easy to review.

After coding:
1. Summarize what changed.
2. List modified files.
3. Mention risks or TODOs.

## Definition of done
A task is done only if:
- the code is placed in the right folders
- the feature is runnable locally
- the main flow is complete
- the result is suitable to show in a job interview
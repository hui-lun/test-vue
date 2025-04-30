# BDM-Chat Backend & Frontend

A modular, production-grade FastAPI + Vue.js application for intelligent chat, agent workflow, and web search/summary, powered by LangChain and modern LLMs.

---

## Features
- **Multi-mode chat**: Supports normal chat, agent-assisted replies, and web search summarization.
- **Agent workflow**: Modular node-based agent logic, easily extensible.
- **SQL & Web Search**: Integrates SQL database querying and DuckDuckGo search with summarization.
- **Modern UI**: Vue.js SPA with clear mode switching, message streaming, and user-friendly design.
- **Clean architecture**: Python backend is fully modularized for maintainability and scalability.

---

## Project Structure

```
BDM-chat/
├── backend/
│   └── app/
│       ├── agents/         # Agent workflow, nodes, tools, SQL/search logic
│       ├── models/         # Pydantic models for API validation
│       ├── routers/        # FastAPI routers for each API endpoint
│       ├── config.py       # LLM and global config
│       ├── main.py         # FastAPI entrypoint
│       └── __init__.py     # Backend package docstring
├── frontend/
│   └── src/
│       └── App.vue         # Main Vue SPA
│   └── ...                 # Other Vue components and assets
├── docker-compose.yml      # Multi-service orchestration
├── Dockerfile              # Backend Dockerfile
└── README.md               # This file
```

---

## Getting Started

### Quick Start (Recommended)
1. Copy and edit environment variables:
    ```bash
    cp .env.example .env
    # Edit .env as needed
    ```
2. Start all services (backend + frontend + database) at once:
    ```bash
    sudo docker compose up --build
    ```
3. Open your browser and visit [http://localhost:8080](http://localhost:8080)

---

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (recommended for production or quick start)
- PostgreSQL (or use the built-in Docker database service)

### Environment Variables
Set the following variables in your `.env` file or Docker Compose:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `VLLM_API_BASE` (LLM API endpoint)

#### Example `.env` file
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=your_database_name
VLLM_API_BASE=http://localhost:8090/v1
```
---

> **Note:** Manual startup of backend or frontend is not supported. Please use Docker Compose for all development and deployment.

---

## API Endpoints
- `POST /chat` — Standard chat (e.g. auto select tool)
- `POST /agent-chat` — Agent chat(e.g. SQL tool)
- `POST /search-and-summarize` — Web search and summarization

---

## Code Quality & Contribution
- All backend modules are documented with clear docstrings.
- Please follow the modular design: business logic in `agents/`, API endpoints in `routers/`, models in `models/`.
- Pull requests and issues are welcome! Please add tests for any new features.

---


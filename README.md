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

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (for production or quick start)
- PostgreSQL (or use Docker service)

### Environment Variables
Set the following in your `.env` or Docker Compose:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `VLLM_API_BASE` (for LLM API endpoint)

### Local Development
1. **Start backend**
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```
2. **Start frontend**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
3. Visit [http://localhost:8080](http://localhost:8080) (or the port shown)

### Docker Compose (Recommended)
```bash
cd BDM-chat
cp .env.example .env   # Edit as needed
sudo docker compose up --build
```

---

## API Endpoints
- `POST /chat` — Normal chat
- `POST /agent-chat` — Agent workflow (email to SQL, web, or reply)
- `POST /search-and-summarize` — Web search & summarization

---

## Code Quality & Contribution
- All backend modules are documented with clear docstrings.
- Follow modular design: business logic in `agents/`, API in `routers/`, models in `models/`.
- PRs and issues welcome! Please add tests for new features.

---

## License
MIT

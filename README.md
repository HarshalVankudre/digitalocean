# Gradient Agent FastAPI + React

A full-stack starter wiring a **FastAPI** backend (JWT auth, Admin/User roles, MongoDB) to a **React + Tailwind** frontend. It integrates with a **DigitalOcean Gradient™ AI Agent endpoint**.

## Features

- Admin dashboard to set **Agent Base URL**, **Access Key**, and toggle **retrieval/functions/guardrails** flags.
- Role-based auth (`admin`, `user`) with JWT.
- Per-user **conversations** with **messages** (user ⇄ assistant). Stores optional retrieval/guardrails/functions payloads.
- React chat UI with **Tailwind** and **React Markdown** for assistant output.

---

## Prereqs

- **Python 3.11+**
- **MongoDB 6/7** (local or remote)
- **Node 18+**

---

## Quickstart

### 1) Backend

```bash
cd backend
cp .env.example .env  # set MONGODB_URI, JWT_SECRET, DO_AGENT_BASE_URL, DO_AGENT_ACCESS_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --reload --port 8000
```

> **First admin**: In dev you can insert an admin manually in Mongo (with a bcrypt hash) or temporarily relax the `/auth/register` dependency to create the first admin, then revert.

### 2) Frontend

```bash
cd frontend
npm i
npm run dev  # http://localhost:5173
```

Set `VITE_API_BASE` in a `.env` file at `frontend/.env` if your backend is not `http://localhost:8000`:

```
VITE_API_BASE=http://localhost:8000
```

---

## DigitalOcean Gradient Agent

1. In the DO Control Panel, go to **Agent Platform → Agent Workspaces → <your agent>**.
2. Set endpoint **Private** or **Public** (public also enables the **chatbot embed** widget).
3. Create an **Endpoint Access Key** under **Settings → Endpoint Access Keys** and save it securely.
4. Copy your Agent **Base URL**, e.g. `https://<agent-identifier>.ondigitalocean.app`.
5. In the Admin dashboard, set Base URL + Access Key and choose the include flags.

**API contract used by the backend**: `POST <base>/api/v1/chat/completions` with JSON body:
```json
{
  "messages": [{"role":"user","content":"Hi"}],
  "stream": false,
  "include_retrieval_info": true,
  "include_functions_info": false,
  "include_guardrails_info": false
}
```

Each Agent endpoint also hosts per-agent docs at `<base>/docs`.

---

## Endpoints (Backend)

- `POST /auth/login` → returns JWT
- `POST /auth/register` *(admin-only)*
- `GET /settings` *(admin-only)*
- `PUT /settings` *(admin-only)*
- `POST /conversations` *(user)*
- `GET /conversations` *(user)*
- `GET /conversations/{cid}` *(user)*
- `POST /conversations/{cid}/messages` *(user)*

---

## Notes

- **Streaming**: Disabled by default; you can upgrade `call_do_agent` to Server-Sent Events.
- **Security**: Rotate your Agent access key regularly; restrict who has Admin role.
- **Chatbot embed**: If your endpoint is public, the Control Panel provides a `<script>` to paste on any site.

MIT © You

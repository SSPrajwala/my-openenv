# 📧 Email Triage OpenEnv

> A real-world reinforcement learning environment where an AI agent triages incoming emails by assigning priority, category, and routing department.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-blue)](https://github.com/openenv)
[![HuggingFace Space](https://img.shields.io/badge/HuggingFace-Space-yellow)](https://huggingface.co/spaces/SSP999/my-openenv)

---

## 🌍 Environment Overview

Email triage is a critical real-world task performed by support teams, executives, and operations staff daily. This environment simulates an inbox where an AI agent must read each email and:

1. **Assign a priority** — How urgently does this need attention?
2. **Categorize it** — What type of email is this?
3. **Route it** — Which department should handle it?
4. **Summarize it** — Write a concise summary for the receiving team.

The environment rewards correct decisions with partial credit, enabling dense reward signals throughout the episode.

---

## 🎯 Tasks

| Task | Difficulty | Emails | Description |
|------|-----------|--------|-------------|
| `easy_triage` | Easy | 3 | Clear-cut cases: spam, critical outage, overdue invoice |
| `medium_triage` | Medium | 5 | Mixed signals: complaints, enterprise inquiries, password resets |
| `hard_triage` | Hard | 8 | Ambiguous routing: internal deadlines, security alerts, duplicate billing |

---

## 📐 Action Space

Each action is a JSON object:

```json
{
  "email_id": "email_0",
  "priority": "urgent",
  "category": "technical",
  "route_to": "engineering",
  "summary": "Production server down for 10 minutes, DB connection timeout, needs immediate fix."
}
```

| Field | Type | Values |
|-------|------|--------|
| `email_id` | string | `email_0`, `email_1`, ... |
| `priority` | enum | `urgent`, `high`, `medium`, `low` |
| `category` | enum | `billing`, `technical`, `complaint`, `inquiry`, `spam`, `internal` |
| `route_to` | enum | `finance`, `engineering`, `support`, `sales`, `hr`, `trash` |
| `summary` | string | 10–200 characters |

---

## 👁️ Observation Space

```json
{
  "email": {
    "id": "email_0",
    "subject": "URGENT: Server down - production outage",
    "sender": "alerts@monitoring.com",
    "body": "Our production server has been down...",
    "received_at": "2024-03-15T09:00:00Z",
    "has_attachment": false
  },
  "inbox_remaining": 3,
  "current_step": 1,
  "max_steps": 3
}
```

---

## 🏆 Reward Function

Each step returns a reward in `[0.0, 1.0]` with these components:

| Component | Weight | Condition |
|-----------|--------|-----------|
| Priority correct | 0.35 | Exact match |
| Category correct | 0.30 | Exact match |
| Route correct | 0.25 | Exact match |
| Summary quality | 0.10 | Proportional to length (up to 100 chars) |
| Partial priority | +0.15 | Off by one level |

This provides **dense rewards** — the agent receives feedback at every step, not just at episode end.

---

## 🚀 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Environment info |
| `GET` | `/health` | Health check |
| `GET` | `/tasks` | List all tasks |
| `POST` | `/reset` | Start new episode |
| `POST` | `/step` | Take an action |
| `GET` | `/state` | Current state |

### Reset
```bash
curl -X POST https://SSP999-my-openenv.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "easy_triage"}'
```

### Step
```bash
curl -X POST https://SSP999-my-openenv.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "email_0",
    "priority": "low",
    "category": "spam",
    "route_to": "trash",
    "summary": "Spam email promising million dollar prize, should be discarded."
  }'
```

---

## ⚙️ Setup & Usage

### Local (Python)
```bash
git clone https://github.com/SSPrajwala/my-openenv
cd my-openenv
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 7860
```

### Docker
```bash
docker build -t email-triage-openenv .
docker run -p 7860:7860 email-triage-openenv
```

### Run Inference
```bash
export HF_TOKEN=your_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py
```

---

## 📊 Baseline Performance

Tested with `Qwen/Qwen2.5-72B-Instruct` via HuggingFace Router:

| Task | Score | Notes |
|------|-------|-------|
| `easy_triage` | ~0.85 | Strong on clear-cut spam/urgent cases |
| `medium_triage` | ~0.72 | Some confusion on billing vs complaint routing |
| `hard_triage` | ~0.61 | Struggles with ambiguous internal emails |
| **Average** | **~0.73** | |

---

## 📁 Project Structure

```
.
├── email_triage_env.py   # Core environment (Pydantic models, step/reset/state)
├── server.py             # FastAPI REST server
├── inference.py          # Baseline inference script
├── openenv.yaml          # OpenEnv metadata
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container definition
└── README.md             # This file
```

---

## 🏷️ Tags

`openenv` `email-triage` `nlp` `reinforcement-learning` `real-world` `fastapi`

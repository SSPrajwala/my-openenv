---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---

# 📧 Email Triage OpenEnv

A real-world OpenEnv reinforcement learning environment where an AI agent reads
incoming emails and must correctly assign **priority**, **category**, and **routing
department** for each one.

Built for the **Scaler × Meta OpenEnv Hackathon — Round 1**.

---

## Environment Description

Every episode presents the agent with an inbox of real-looking emails drawn from
realistic workplace scenarios: production outages, overdue invoices, angry
customers, enterprise sales leads, spam, and internal announcements.

For each email the agent must decide:

| Field | Choices |
|---|---|
| `priority` | `urgent` · `high` · `medium` · `low` |
| `category` | `billing` · `technical` · `complaint` · `inquiry` · `spam` · `internal` |
| `route_to` | `finance` · `engineering` · `support` · `sales` · `hr` · `trash` |
| `summary` | 10–200 character plain-text summary |

---

## Tasks

| Task | Difficulty | Emails | Description |
|---|---|---|---|
| `easy_triage` | Easy | 3 | Clear-cut cases: spam, production outage, overdue invoice |
| `medium_triage` | Medium | 5 | Mixed priorities with subtle routing decisions |
| `hard_triage` | Hard | 8 | Ambiguous cases, internal urgencies, security alerts |

---

## Reward Function

Each step returns a reward in **[0.0, 1.0]**:

| Component | Weight | Condition |
|---|---|---|
| Priority correct | 0.35 | Exact match |
| Category correct | 0.30 | Exact match |
| Routing correct | 0.25 | Exact match |
| Summary quality | 0.10 | Proportional to length (proxy for effort) |
| Partial priority credit | +0.15 | Priority off by exactly one level |

Maximum score per step: **1.0** (capped).

---

## Observation Space

```json
{
  "done":            false,
  "reward":          null,
  "email": {
    "id":            "email_0",
    "subject":       "URGENT: Server down - production outage",
    "sender":        "alerts@monitoring.com",
    "body":          "...",
    "received_at":   "2024-03-15T09:00:00Z",
    "has_attachment": false
  },
  "inbox_remaining": 2,
  "current_step":    0,
  "max_steps":       3,
  "task_name":       "easy_triage"
}
```

## Action Space

```json
{
  "email_id":  "email_0",
  "priority":  "urgent",
  "category":  "technical",
  "route_to":  "engineering",
  "summary":   "Production server is down with DB connection timeout — needs immediate engineering response."
}
```

---

## Project Structure

```
email-triage-openenv/
├── models.py              ← Action, Observation, State types (openenv base classes)
├── client.py              ← HTTP client for agents connecting to the deployed Space
├── inference.py           ← Baseline LLM agent script ([START]/[STEP]/[END] format)
├── openenv.yaml           ← Environment manifest
├── server/
│   ├── environment.py     ← EmailTriageEnvironment logic (reset / step / state)
│   └── app.py             ← FastAPI wiring (all REST endpoints)
├── Dockerfile             ← Container definition for HuggingFace Spaces
└── pyproject.toml
```

This layout follows the **OpenEnv 3-component pattern** taught in Module 4 of the
[OpenEnv Course](https://github.com/huggingface/openenv-course):

1. **`models.py`** — typed contracts (inherits `Action`, `Observation`, `State` from `openenv-core`)
2. **`server/environment.py`** — pure logic, no HTTP
3. **`server/app.py`** — thin FastAPI layer, imports from the two above

---

## REST API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server health check |
| `GET` | `/tasks` | List all available tasks |
| `POST` | `/reset` | Start a new episode |
| `POST` | `/step` | Execute one triage action |
| `GET` | `/state` | Current episode metadata |

### POST /reset

```bash
curl -X POST https://SSP999-my-openenv.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "easy_triage"}'
```

### POST /step

```bash
curl -X POST https://SSP999-my-openenv.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "email_id":  "email_0",
    "priority":  "low",
    "category":  "spam",
    "route_to":  "trash",
    "summary":   "Spam email promising million dollar prize, should be discarded immediately."
  }'
```

---

## Setup & Local Run

### Requirements

- Python 3.11+
- Docker (for container builds)

### Install

```bash
git clone https://github.com/SSPrajwala/my-openenv
cd my-openenv
pip install -r requirements.txt
```

### Run the server locally

```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Run the baseline inference script

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="hf_..."

python inference.py
```

### Use the Python client

```python
from client import EmailTriageClient
from models import EmailTriageAction

env = EmailTriageClient("http://localhost:7860")
obs = env.reset("easy_triage")

while not obs.done:
    action = EmailTriageAction(
        email_id=obs.email.id,
        priority="low",
        category="spam",
        route_to="trash",
        summary="Spam email, should be discarded.",
    )
    obs = env.step(action)
    print(f"reward={obs.reward:.2f}  done={obs.done}")
```

### Build & run with Docker

```bash
docker build -t email-triage-openenv .
docker run -p 7860:7860 \
  -e HF_TOKEN=$HF_TOKEN \
  -e API_BASE_URL=$API_BASE_URL \
  -e MODEL_NAME=$MODEL_NAME \
  email-triage-openenv
```

---

## Baseline Scores

Scores from `Qwen/Qwen2.5-72B-Instruct` via HuggingFace Inference API:

| Task | Avg Reward | Success (≥0.5) |
|---|---|---|
| `easy_triage` | ~0.85 | ✅ |
| `medium_triage` | ~0.72 | ✅ |
| `hard_triage` | ~0.65 | ✅ |

A perfect agent scores **0.98** per step (0.35 + 0.30 + 0.25 + 0.10×summary_quality).
A random default agent scores ~0.15–0.55 depending on the task.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `API_BASE_URL` | LLM API endpoint | `https://router.huggingface.co/v1` |
| `MODEL_NAME` | Model identifier | `Qwen/Qwen2.5-72B-Instruct` |
| `HF_TOKEN` | Hugging Face / API key | *(required)* |

---

## Author

**Kaluvala Sri Sai Prajwala** — `b23cs137@kitsw.ac.in`

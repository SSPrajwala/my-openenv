---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
app_port: 7860
pinned: false
---

# 📧 Email Triage OpenEnv

A real-world OpenEnv RL environment — Scaler × Meta OpenEnv Hackathon Round 1.

**Live API:** https://ssp999-my-openenv.hf.space  
**Swagger Docs:** https://ssp999-my-openenv.hf.space/docs

---

## Tasks

| Task | Difficulty | Emails | Max Steps |
|---|---|---|---|
| `easy_triage` | Easy | 3 | 3 |
| `medium_triage` | Medium | 5 | 5 |
| `hard_triage` | Hard | 8 | 8 |

---

## Reward Function

`priority(0.35) + category(0.30) + routing(0.25) + summary_quality(0.10) + partial_priority_credit(+0.15)`

Range: **0.0 – 1.0** per step.

---

## Action Space

```json
{
  "email_id":  "email_0",
  "priority":  "urgent",
  "category":  "technical",
  "route_to":  "engineering",
  "summary":   "Production server is down with DB connection timeout."
}
```

## Observation Space

```json
{
  "done": false, "reward": null,
  "email": { "id": "email_0", "subject": "...", "sender": "...", "body": "...",
             "received_at": "2024-03-15T09:00:00Z", "has_attachment": false },
  "inbox_remaining": 2, "current_step": 0, "max_steps": 3, "task_name": "easy_triage"
}
```

---

## Project Structure (OpenEnv course Module 4 pattern)

```
models.py              ← Action / Observation / State types (openenv-core base classes)
client.py              ← HTTP client for agents
server/
  environment.py       ← Environment logic (reset / step / state)
  app.py               ← FastAPI wiring
inference.py           ← Baseline LLM agent
openenv.yaml           ← Manifest
Dockerfile
```

---

## Setup

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export HF_TOKEN=hf_...
python inference.py
```

---

## Author

Kaluvala Sri Sai Prajwala — b23cs137@kitsw.ac.in
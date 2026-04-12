"""
server/app.py — FastAPI wiring for Email Triage OpenEnv
========================================================
Following the OpenEnv course pattern (Module 4), this file only does
HTTP/API wiring.  All logic lives in server/environment.py.

Note on create_fastapi_app():
  openenv-core provides create_fastapi_app() which generates all routes
  in one line — ideal for single-shot stateless environments.
  This environment is *multi-step* (state must persist between /reset and
  /step calls), so we maintain a single global instance and wire the routes
  manually.  WebSocket-based stateful sessions (as used in the course's
  training module) would be the production-grade alternative.
"""

import sys
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import EmailTriageAction, EmailTriageObservation, EmailTriageState
from server.environment import EmailTriageEnvironment, TASKS

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Email Triage OpenEnv",
    description=(
        "A real-world OpenEnv environment where an AI agent triages incoming "
        "emails by assigning priority, category, and routing department. "
        "Three tasks: easy (3 emails) → medium (5) → hard (8)."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared environment instance (stateful multi-step REST pattern)
_env: Optional[EmailTriageEnvironment] = None


# ── Request / Response helpers ────────────────────────────────────────────────

class ResetResponse(BaseModel):
    observation:      Dict[str, Any]
    task_name:        str
    task_description: str


class StepRequestBody(BaseModel):
    """Flat body accepted by /step (maps directly onto EmailTriageAction)."""
    email_id:  str
    priority:  str
    category:  str
    route_to:  str
    summary:   str


class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward:      float
    done:        bool
    info:        Dict[str, Any]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name":    "Email Triage OpenEnv",
        "version": "1.0.0",
        "status":  "ok",
        "tasks":   list(TASKS.keys()),
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> Dict[str, Any]:
    return {"tasks": TASKS}


@app.post("/reset", response_model=ResetResponse)
async def reset(request: Request) -> ResetResponse:
    """
    Start a new episode.

    Body (JSON, all optional):
        { "task_name": "easy_triage" | "medium_triage" | "hard_triage" }
    """
    global _env
    try:
        body: Dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            pass  # empty body → use default task

        task_name = body.get("task_name") or body.get("task") or "easy_triage"

        _env = EmailTriageEnvironment()
        obs  = _env.reset(task_name=task_name)

        return ResetResponse(
            observation=obs.model_dump(),
            task_name=task_name,
            task_description=TASKS[task_name]["description"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/step", response_model=StepResponse)
def step(body: StepRequestBody) -> StepResponse:
    """
    Execute one triage action.  Call /reset first.

    Body (JSON):
        {
          "email_id": "email_0",
          "priority": "urgent",
          "category": "technical",
          "route_to": "engineering",
          "summary":  "Production server is down; immediate engineering response needed."
        }
    """
    global _env
    if _env is None:
        raise HTTPException(
            status_code=400,
            detail="Environment not initialised. Call POST /reset first.",
        )
    try:
        action = EmailTriageAction(
            email_id=body.email_id,
            priority=body.priority,
            category=body.category,
            route_to=body.route_to,
            summary=body.summary,
        )
        obs = _env.step(action)
        return StepResponse(
            observation=obs.model_dump(),
            reward=obs.reward or 0.0,
            done=obs.done,
            info={"total_reward": _env.state.total_reward, "step": _env.state.step_count},
        )
    except (ValueError, Exception) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/state", response_model=EmailTriageState)
def state() -> EmailTriageState:
    """Return current episode metadata (does not advance the episode)."""
    global _env
    if _env is None:
        raise HTTPException(
            status_code=400,
            detail="Environment not initialised. Call POST /reset first.",
        )
    return _env.state


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)


if __name__ == "__main__":
    main()

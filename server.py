"""
FastAPI server implementing the OpenEnv REST API for Email Triage environment.
Endpoints: POST /reset, POST /step, GET /state, GET /tasks, GET /health
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import Request

from email_triage_env import (
    EmailTriageAction,
    EmailTriageEnv,
    EmailTriageState,
    TASKS,
)

# -------------------- App Setup --------------------

app = FastAPI(
    title="Email Triage OpenEnv",
    description="OpenEnv environment for email triage RL tasks.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global env instance (single-session server)
_env: Optional[EmailTriageEnv] = None

# -------------------- Request Models --------------------

class ResetRequest(BaseModel):
    task_name: str = "easy_triage"


class StepRequest(BaseModel):
    email_id: str
    priority: str
    category: str
    route_to: str
    summary: str


# -------------------- Response Models --------------------

class ResetResponse(BaseModel):
    observation: Dict[str, Any]
    task_name: str
    task_description: str


class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]


# -------------------- Endpoints --------------------

@app.get("/")
def root():
    return {
        "name": "Email Triage OpenEnv",
        "version": "1.0.0",
        "status": "ok",
        "tasks": list(TASKS.keys()),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return {"tasks": TASKS}


@app.post("/reset", response_model=ResetResponse)
async def reset(request: Request):
    global _env

    try:
        # Accept any kind of input (empty / task / task_name)
        body = {}
        try:
            body = await request.json()
        except:
            body = {}

        task_name = body.get("task_name") or body.get("task") or "easy_triage"

        _env = EmailTriageEnv(task_name=task_name)
        obs = _env.reset()

        return ResetResponse(
            observation=obs.model_dump(),
            task_name=task_name,
            task_description=TASKS[task_name]["description"],
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    global _env
    if _env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")

    try:
        action = EmailTriageAction(
            email_id=req.email_id,
            priority=req.priority,
            category=req.category,
            route_to=req.route_to,
            summary=req.summary,
        )

        obs, reward, done, info = _env.step(action)

        return StepResponse(
            observation=obs.model_dump(),
            reward=reward,
            done=done,
            info=info,
        )

    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/state", response_model=EmailTriageState)
def state():
    global _env
    if _env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    return _env.state()
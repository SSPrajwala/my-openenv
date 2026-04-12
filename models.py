"""
models.py — Type definitions for Email Triage OpenEnv
======================================================
Following the OpenEnv course pattern (Module 4), all Pydantic types live here:
  - EmailTriageAction   (inherits openenv Action)
  - EmailTriageObservation  (inherits openenv Observation — includes done & reward)
  - EmailTriageState    (inherits openenv State — includes episode_id & step_count)
"""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from openenv.core.env_server import Action, Observation, State


# ─── Enums ────────────────────────────────────────────────────────────────────

class Priority(str, Enum):
    URGENT = "urgent"
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


class Category(str, Enum):
    BILLING   = "billing"
    TECHNICAL = "technical"
    COMPLAINT = "complaint"
    INQUIRY   = "inquiry"
    SPAM      = "spam"
    INTERNAL  = "internal"


class RouteDepartment(str, Enum):
    FINANCE     = "finance"
    ENGINEERING = "engineering"
    SUPPORT     = "support"
    SALES       = "sales"
    HR          = "hr"
    TRASH       = "trash"


# ─── Sub-model (not an Action/Observation — just a nested structure) ──────────

class Email(BaseModel):
    """A single email in the triage inbox."""

    model_config = ConfigDict(extra="forbid")

    id:             str
    subject:        str
    sender:         str
    body:           str
    received_at:    str
    has_attachment: bool = False


# ─── Action ───────────────────────────────────────────────────────────────────

class EmailTriageAction(Action):
    """
    The agent's decision for a single email.

    Inherits `metadata: Dict[str, Any]` from openenv Action base class.
    """

    email_id:  str
    priority:  Priority
    category:  Category
    route_to:  RouteDepartment
    summary:   str = Field(..., min_length=10, max_length=200)


# ─── Observation ──────────────────────────────────────────────────────────────

class EmailTriageObservation(Observation):
    """
    What the agent sees after each reset() / step().

    Inherits from openenv Observation:
      - done:     bool  (False until all emails in task are processed)
      - reward:   float | None  (0.0–1.0, None at reset)
      - metadata: Dict[str, Any]
    """

    email:           Email
    inbox_remaining: int
    current_step:    int
    max_steps:       int
    task_name:       str = ""


# ─── State ────────────────────────────────────────────────────────────────────

class EmailTriageState(State):
    """
    Internal episode metadata (not the same as the agent's observation).

    Inherits from openenv State:
      - episode_id:  str | None  (UUID assigned at reset)
      - step_count:  int         (mirrors current_step)
    """

    task_name:        str   = ""
    max_steps:        int   = 0
    total_reward:     float = 0.0
    emails_processed: int   = 0
    inbox_size:       int   = 0
    is_done:          bool  = False

"""
email_triage_env.py — backward-compatibility shim
==================================================
This file re-exports everything from the new module structure so that any
code written against the old single-file layout continues to work.

New canonical locations:
  models.py                  → all types
  server/environment.py      → EmailTriageEnv (now EmailTriageEnvironment)
"""

# Types
from models import (  # noqa: F401
    Priority,
    Category,
    RouteDepartment,
    Email,
    EmailTriageAction,
    EmailTriageObservation,
    EmailTriageState,
)

# Environment & data
from server.environment import (  # noqa: F401
    EMAIL_DATASET,
    TASKS,
    EmailTriageEnvironment,
)

# Legacy alias
EmailTriageEnv = EmailTriageEnvironment

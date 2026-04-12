"""
server/environment.py — Email Triage Environment logic
=======================================================
Following the OpenEnv course pattern (Module 4), all game/task logic lives here.
The FastAPI wiring is in server/app.py.

The EmailTriageEnvironment class implements three methods:
  reset(task_name)  → EmailTriageObservation
  step(action)      → EmailTriageObservation  (done & reward embedded)
  state             → EmailTriageState        (episode metadata)
"""

import uuid
from typing import Dict, List, Optional, Tuple

import sys
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from models import (
    Category,
    Email,
    EmailTriageAction,
    EmailTriageObservation,
    EmailTriageState,
    Priority,
    RouteDepartment,
)


# ─── Email Dataset ────────────────────────────────────────────────────────────

EMAIL_DATASET: List[Dict] = [
    {
        "subject": "URGENT: Server down - production outage",
        "sender": "alerts@monitoring.com",
        "body": "Our production server has been down for 10 minutes. All customer traffic affected. Error: DB connection timeout. Need immediate attention.",
        "has_attachment": False,
        "priority": Priority.URGENT,
        "category": Category.TECHNICAL,
        "route_to": RouteDepartment.ENGINEERING,
    },
    {
        "subject": "Invoice #4521 overdue - 30 days",
        "sender": "billing@vendor.com",
        "body": "Your invoice #4521 for $2,400 is now 30 days overdue. Please arrange payment immediately to avoid service interruption.",
        "has_attachment": True,
        "priority": Priority.HIGH,
        "category": Category.BILLING,
        "route_to": RouteDepartment.FINANCE,
    },
    {
        "subject": "I want to cancel my subscription NOW",
        "sender": "angry.customer@gmail.com",
        "body": "This is the third time I'm contacting you. Your product stopped working 2 weeks ago and nobody has helped me. I want a full refund and cancellation immediately.",
        "has_attachment": False,
        "priority": Priority.HIGH,
        "category": Category.COMPLAINT,
        "route_to": RouteDepartment.SUPPORT,
    },
    {
        "subject": "Question about enterprise pricing",
        "sender": "cto@bigcorp.com",
        "body": "Hi, we have a team of 500 engineers and are evaluating your platform. Could you send us enterprise pricing information and schedule a demo?",
        "has_attachment": False,
        "priority": Priority.HIGH,
        "category": Category.INQUIRY,
        "route_to": RouteDepartment.SALES,
    },
    {
        "subject": "Win $1,000,000 - You've been selected!",
        "sender": "noreply@prize-claim.net",
        "body": "Congratulations! You've been randomly selected to receive ONE MILLION DOLLARS. Click here to claim your prize now! Limited time offer!",
        "has_attachment": False,
        "priority": Priority.LOW,
        "category": Category.SPAM,
        "route_to": RouteDepartment.TRASH,
    },
    {
        "subject": "Team lunch this Friday?",
        "sender": "john.smith@ourcompany.com",
        "body": "Hey everyone, thinking of organizing a team lunch this Friday at noon. The Italian place on 5th Ave? Let me know if you're interested!",
        "has_attachment": False,
        "priority": Priority.LOW,
        "category": Category.INTERNAL,
        "route_to": RouteDepartment.HR,
    },
    {
        "subject": "Password reset request",
        "sender": "user123@customer.com",
        "body": "Hello, I forgot my password and the reset link I received 2 hours ago has expired. Could you please send a new one? My username is user123.",
        "has_attachment": False,
        "priority": Priority.MEDIUM,
        "category": Category.TECHNICAL,
        "route_to": RouteDepartment.SUPPORT,
    },
    {
        "subject": "Incorrect charge on my account",
        "sender": "customer@email.com",
        "body": "I was charged $150 twice this month for my subscription. Please review my account and refund the duplicate charge. Account ID: ACC-789.",
        "has_attachment": True,
        "priority": Priority.HIGH,
        "category": Category.BILLING,
        "route_to": RouteDepartment.FINANCE,
    },
    {
        "subject": "RE: Q3 budget planning - deadline tomorrow",
        "sender": "cfo@ourcompany.com",
        "body": "Reminder to all department heads: Q3 budget submissions are due tomorrow EOD. Please send your projections to finance. No extensions will be granted.",
        "has_attachment": True,
        "priority": Priority.URGENT,
        "category": Category.INTERNAL,
        "route_to": RouteDepartment.FINANCE,
    },
    {
        "subject": "How do I export my data?",
        "sender": "newuser@gmail.com",
        "body": "Hi there, I'm a new user and I'm trying to figure out how to export my data to CSV format. I've looked at the docs but couldn't find clear instructions.",
        "has_attachment": False,
        "priority": Priority.MEDIUM,
        "category": Category.INQUIRY,
        "route_to": RouteDepartment.SUPPORT,
    },
    {
        "subject": "CRITICAL: Security breach detected",
        "sender": "security@monitoring.com",
        "body": "Automated alert: Unusual login activity detected from IP 192.168.1.100. Multiple failed attempts followed by successful login from unknown location. Immediate review required.",
        "has_attachment": False,
        "priority": Priority.URGENT,
        "category": Category.TECHNICAL,
        "route_to": RouteDepartment.ENGINEERING,
    },
    {
        "subject": "Your free trial expires in 3 days",
        "sender": "noreply@competitor.com",
        "body": "Don't miss out! Your free trial of CompetitorApp expires in 3 days. Upgrade now and get 20% off your first year!",
        "has_attachment": False,
        "priority": Priority.LOW,
        "category": Category.SPAM,
        "route_to": RouteDepartment.TRASH,
    },
]


# ─── Task Definitions ─────────────────────────────────────────────────────────

TASKS: Dict[str, Dict] = {
    "easy_triage": {
        "description": "Triage 3 clearly distinct emails (spam, urgent technical, billing).",
        "difficulty": "easy",
        "email_indices": [4, 0, 1],   # spam, server-down, invoice
        "max_steps": 3,
    },
    "medium_triage": {
        "description": "Triage 5 emails with mixed priorities and subtle routing decisions.",
        "difficulty": "medium",
        "email_indices": [2, 3, 6, 7, 9],
        "max_steps": 5,
    },
    "hard_triage": {
        "description": "Triage 8 emails including ambiguous cases, internal urgencies, and security alerts.",
        "difficulty": "hard",
        "email_indices": [0, 1, 2, 3, 4, 8, 10, 11],
        "max_steps": 8,
    },
}


# ─── Environment ──────────────────────────────────────────────────────────────

class EmailTriageEnvironment:
    """
    Email Triage RL environment following the OpenEnv 3-component pattern.

    The agent reads incoming emails one at a time and must assign:
      - priority  (urgent / high / medium / low)
      - category  (billing / technical / complaint / inquiry / spam / internal)
      - route_to  (finance / engineering / support / sales / hr / trash)
      - summary   (10–200 char plain-text summary)

    Reward breakdown per step (0.0 – 1.0):
      0.35  priority correct
      0.30  category correct
      0.25  routing correct
      0.10  summary quality (length-based proxy)
      +0.15 partial credit if priority is off by exactly one level
    """

    def __init__(self) -> None:
        self._inbox:          List[Dict] = []
        self._current_index:  int        = 0
        self._current_step:   int        = 0
        self._total_reward:   float      = 0.0
        self._is_done:        bool       = False
        self._episode_id:     str        = ""
        self._task_name:      str        = "easy_triage"
        self._task_config:    Dict       = TASKS["easy_triage"]

    # ── Public API ────────────────────────────────────────────────────────────

    def reset(self, task_name: str = "easy_triage") -> EmailTriageObservation:
        """Start a new episode. task_name selects easy / medium / hard."""
        if task_name not in TASKS:
            raise ValueError(
                f"Unknown task '{task_name}'. Choose from: {list(TASKS.keys())}"
            )
        self._task_name   = task_name
        self._task_config = TASKS[task_name]
        self._inbox       = [EMAIL_DATASET[i] for i in self._task_config["email_indices"]]
        self._current_index = 0
        self._current_step  = 0
        self._total_reward  = 0.0
        self._is_done       = False
        self._episode_id    = str(uuid.uuid4())
        return self._make_observation(done=False, reward=None)

    def step(self, action: EmailTriageAction) -> EmailTriageObservation:
        """Process one triage decision; reward is embedded in the observation."""
        if self._is_done:
            return self._make_observation(done=True, reward=0.0)

        expected      = self._inbox[self._current_index]
        expected_id   = f"email_{self._current_index}"

        if action.email_id != expected_id:
            reward = 0.0
        else:
            reward = self._grade(action, expected)

        self._total_reward  += reward
        self._current_step  += 1
        self._current_index += 1

        if (
            self._current_index >= len(self._inbox)
            or self._current_step >= self._task_config["max_steps"]
        ):
            self._is_done = True

        return self._make_observation(done=self._is_done, reward=reward)

    @property
    def state(self) -> EmailTriageState:
        """Episode metadata — separate from what the agent observes."""
        return EmailTriageState(
            episode_id=self._episode_id,
            step_count=self._current_step,
            task_name=self._task_name,
            max_steps=self._task_config["max_steps"],
            total_reward=self._total_reward,
            emails_processed=self._current_index,
            inbox_size=len(self._inbox),
            is_done=self._is_done,
        )

    def close(self) -> None:
        """Clean up (no-op for this environment)."""
        pass

    @staticmethod
    def list_tasks() -> Dict[str, Dict]:
        return TASKS

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _make_observation(
        self, done: bool, reward: Optional[float]
    ) -> EmailTriageObservation:
        idx = min(self._current_index, len(self._inbox) - 1)
        raw = self._inbox[idx]
        email = Email(
            id=f"email_{idx}",
            subject=raw["subject"],
            sender=raw["sender"],
            body=raw["body"],
            received_at="2024-03-15T09:00:00Z",
            has_attachment=raw.get("has_attachment", False),
        )
        return EmailTriageObservation(
            done=done,
            reward=reward,
            email=email,
            inbox_remaining=max(0, len(self._inbox) - self._current_index),
            current_step=self._current_step,
            max_steps=self._task_config["max_steps"],
            task_name=self._task_name,
        )

    def _grade(self, action: EmailTriageAction, expected: Dict) -> float:
        """Return a reward in [0.0, 1.0] for one triage decision."""
        priority_correct  = action.priority  == expected["priority"]
        category_correct  = action.category  == expected["category"]
        route_correct     = action.route_to  == expected["route_to"]

        # Summary quality: proxy by length (10 chars minimum already enforced by type)
        summary_quality = min(1.0, len(action.summary.strip()) / 100.0)

        score = 0.0
        score += 0.35 if priority_correct  else 0.0
        score += 0.30 if category_correct  else 0.0
        score += 0.25 if route_correct     else 0.0
        score += 0.10 * summary_quality

        # Partial credit: priority off by exactly one level
        if not priority_correct:
            order   = [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.URGENT]
            exp_idx = order.index(expected["priority"])
            got_idx = order.index(action.priority)
            if abs(exp_idx - got_idx) == 1:
                score += 0.15

        return min(1.0, score)

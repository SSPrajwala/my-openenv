"""
Email Triage OpenEnv Environment
Real-world task: Sort, prioritize, and route incoming emails.
"""

import random
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class Priority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    COMPLAINT = "complaint"
    INQUIRY = "inquiry"
    SPAM = "spam"
    INTERNAL = "internal"

class RouteDepartment(str, Enum):
    FINANCE = "finance"
    ENGINEERING = "engineering"
    SUPPORT = "support"
    SALES = "sales"
    HR = "hr"
    TRASH = "trash"


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class Email(BaseModel):
    id: str
    subject: str
    sender: str
    body: str
    received_at: str
    has_attachment: bool = False

class EmailTriageAction(BaseModel):
    email_id: str
    priority: Priority
    category: Category
    route_to: RouteDepartment
    summary: str = Field(..., min_length=10, max_length=200)

class EmailTriageObservation(BaseModel):
    email: Email
    inbox_remaining: int
    current_step: int
    max_steps: int

class EmailTriageReward(BaseModel):
    value: float
    priority_correct: bool
    category_correct: bool
    route_correct: bool
    summary_quality: float

class EmailTriageState(BaseModel):
    task_name: str
    current_step: int
    max_steps: int
    total_reward: float
    emails_processed: int
    inbox_size: int
    done: bool


# ─── Email Dataset ────────────────────────────────────────────────────────────

EMAIL_DATASET = [
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

TASKS = {
    "easy_triage": {
        "description": "Triage 3 clearly distinct emails (spam, urgent technical, billing).",
        "difficulty": "easy",
        "email_indices": [4, 0, 1],  # spam, server down, invoice
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

class EmailTriageEnv:
    def __init__(self, task_name: str = "easy_triage"):
        if task_name not in TASKS:
            raise ValueError(f"Unknown task: {task_name}. Choose from {list(TASKS.keys())}")
        self.task_name = task_name
        self.task_config = TASKS[task_name]
        self._inbox: List[Dict] = []
        self._current_index: int = 0
        self._current_step: int = 0
        self._total_reward: float = 0.0
        self._done: bool = False
        self._last_action_error: Optional[str] = None
        self._results: List[Dict] = []

    def reset(self) -> EmailTriageObservation:
        indices = self.task_config["email_indices"]
        self._inbox = [EMAIL_DATASET[i] for i in indices]
        self._current_index = 0
        self._current_step = 0
        self._total_reward = 0.0
        self._done = False
        self._last_action_error = None
        self._results = []
        return self._make_observation()

    def step(self, action: EmailTriageAction) -> Tuple[EmailTriageObservation, float, bool, Dict]:
        if self._done:
            return self._make_observation(), 0.0, True, {"error": "Episode already done"}

        expected_email = self._inbox[self._current_index]
        expected_id = f"email_{self._current_index}"

        if action.email_id != expected_id:
            self._last_action_error = f"Wrong email_id: got {action.email_id}, expected {expected_id}"
            reward = 0.0
        else:
            reward_obj = self._grade(action, expected_email)
            reward = reward_obj.value
            self._last_action_error = None
            self._results.append({
                "email_id": action.email_id,
                "reward": reward,
                "priority_correct": reward_obj.priority_correct,
                "category_correct": reward_obj.category_correct,
                "route_correct": reward_obj.route_correct,
            })

        self._total_reward += reward
        self._current_step += 1
        self._current_index += 1

        if self._current_index >= len(self._inbox) or self._current_step >= self.task_config["max_steps"]:
            self._done = True

        obs = self._make_observation()
        info = {
            "last_action_error": self._last_action_error,
            "total_reward": self._total_reward,
            "step": self._current_step,
        }
        return obs, reward, self._done, info

    def state(self) -> EmailTriageState:
        return EmailTriageState(
            task_name=self.task_name,
            current_step=self._current_step,
            max_steps=self.task_config["max_steps"],
            total_reward=self._total_reward,
            emails_processed=self._current_index,
            inbox_size=len(self._inbox),
            done=self._done,
        )

    def _make_observation(self) -> EmailTriageObservation:
        if self._current_index >= len(self._inbox):
            # Return last email again when done
            idx = len(self._inbox) - 1
        else:
            idx = self._current_index

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
            email=email,
            inbox_remaining=max(0, len(self._inbox) - self._current_index),
            current_step=self._current_step,
            max_steps=self.task_config["max_steps"],
        )

    def _grade(self, action: EmailTriageAction, expected: Dict) -> EmailTriageReward:
        priority_correct = action.priority == expected["priority"]
        category_correct = action.category == expected["category"]
        route_correct = action.route_to == expected["route_to"]

        # Summary quality: reward length and non-trivial content
        summary_len = len(action.summary.strip())
        summary_quality = min(1.0, summary_len / 100.0)

        # Weighted reward
        score = 0.0
        score += 0.35 if priority_correct else 0.0
        score += 0.30 if category_correct else 0.0
        score += 0.25 if route_correct else 0.0
        score += 0.10 * summary_quality

        # Partial credit for adjacent priority
        if not priority_correct:
            priority_order = [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.URGENT]
            exp_idx = priority_order.index(expected["priority"])
            got_idx = priority_order.index(action.priority)
            if abs(exp_idx - got_idx) == 1:
                score += 0.15  # partial credit

        return EmailTriageReward(
            value=min(1.0, score),
            priority_correct=priority_correct,
            category_correct=category_correct,
            route_correct=route_correct,
            summary_quality=summary_quality,
        )

    def close(self):
        pass

    @staticmethod
    def list_tasks() -> Dict[str, Dict]:
        return TASKS

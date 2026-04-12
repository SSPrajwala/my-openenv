"""
client.py — HTTP client for Email Triage OpenEnv
=================================================
Following the OpenEnv course pattern (Module 4), this client handles all
HTTP communication so agent code never constructs raw requests.

Usage:
    from client import EmailTriageClient
    from models import EmailTriageAction

    env = EmailTriageClient("https://SSP999-my-openenv.hf.space")
    obs = env.reset("easy_triage")

    while not obs.done:
        action = EmailTriageAction(
            email_id=obs.email.id,
            priority="medium",
            category="inquiry",
            route_to="support",
            summary="Needs review.",
        )
        obs = env.step(action)
        print(f"reward={obs.reward}  done={obs.done}")

    print("episode complete — state:", env.get_state())
"""

from __future__ import annotations

from typing import Optional

import requests

from models import (
    Email,
    EmailTriageAction,
    EmailTriageObservation,
    EmailTriageState,
)


class EmailTriageClient:
    """
    Thin HTTP wrapper around the Email Triage OpenEnv REST API.

    Mirrors the interface of EmailTriageEnvironment so the same agent
    code can run against the local class or the deployed Space.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:7860",
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout  = timeout

    # ── Public API ────────────────────────────────────────────────────────────

    def reset(self, task_name: str = "easy_triage") -> EmailTriageObservation:
        """Start a new episode on the server and return the first observation."""
        resp = requests.post(
            f"{self.base_url}/reset",
            json={"task_name": task_name},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return self._parse_observation(data["observation"])

    def step(self, action: EmailTriageAction) -> EmailTriageObservation:
        """Send one triage action to the server and return the new observation."""
        payload = {
            "email_id": action.email_id,
            "priority": action.priority.value,
            "category": action.category.value,
            "route_to": action.route_to.value,
            "summary":  action.summary,
        }
        resp = requests.post(
            f"{self.base_url}/step",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        obs  = self._parse_observation(data["observation"])
        # Overwrite done/reward with the top-level values returned by /step
        obs  = obs.model_copy(update={"done": data["done"], "reward": data["reward"]})
        return obs

    def get_state(self) -> EmailTriageState:
        """Retrieve current episode metadata from the server."""
        resp = requests.get(f"{self.base_url}/state", timeout=self.timeout)
        resp.raise_for_status()
        return EmailTriageState(**resp.json())

    def health(self) -> bool:
        """Return True if the server is healthy."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    # ── Parsing helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _parse_observation(data: dict) -> EmailTriageObservation:
        """Deserialise a raw observation dict into a typed EmailTriageObservation."""
        email_data = data["email"]
        email = Email(
            id=email_data["id"],
            subject=email_data["subject"],
            sender=email_data["sender"],
            body=email_data["body"],
            received_at=email_data["received_at"],
            has_attachment=email_data.get("has_attachment", False),
        )
        return EmailTriageObservation(
            done=data.get("done", False),
            reward=data.get("reward"),
            email=email,
            inbox_remaining=data["inbox_remaining"],
            current_step=data["current_step"],
            max_steps=data["max_steps"],
            task_name=data.get("task_name", ""),
        )

"""
inference.py — Baseline agent for Email Triage OpenEnv
=======================================================
MANDATORY env vars:
    API_BASE_URL   The LLM API endpoint  (e.g. https://router.huggingface.co/v1)
    MODEL_NAME     Model identifier      (e.g. Qwen/Qwen2.5-72B-Instruct)
    HF_TOKEN       Hugging Face API key

STDOUT FORMAT (strictly followed — do not alter field names or order):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

# ── Imports from new module structure ────────────────────────────────────────
from models import EmailTriageAction
from server.environment import EmailTriageEnvironment, TASKS

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK    = "email_triage_openenv"
MAX_STEPS    = 10
TEMPERATURE  = 0.2

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert email triage assistant. Given an email, respond ONLY with a valid JSON object.

Classify the email with exactly these fields:
- "priority": one of "urgent", "high", "medium", "low"
- "category": one of "billing", "technical", "complaint", "inquiry", "spam", "internal"
- "route_to": one of "finance", "engineering", "support", "sales", "hr", "trash"
- "summary": a concise 1-2 sentence summary (10-200 characters)

Rules:
- urgent  = immediate action needed (outages, security breaches, deadlines today)
- high    = same-day response (complaints, overdue invoices, enterprise leads)
- medium  = response within 2-3 days
- low     = no urgency (spam → trash, casual internal → hr)
- spam always routes to trash

Respond ONLY with the JSON object. No markdown fences, no explanation."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_user_prompt(obs_dict: Dict[str, Any]) -> str:
    e = obs_dict["email"]
    return (
        f"Please triage this email:\n\n"
        f"Subject: {e['subject']}\n"
        f"From: {e['sender']}\n"
        f"Body: {e['body']}\n"
        f"Has Attachment: {e['has_attachment']}\n"
        f"Inbox remaining: {obs_dict['inbox_remaining']}\n\n"
        f"Respond with JSON only."
    )


def call_llm(messages: List[Dict]) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def parse_action(email_id: str, llm_output: str) -> EmailTriageAction:
    clean = llm_output.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:-1]) if len(lines) > 2 else clean
    try:
        data = json.loads(clean)
        return EmailTriageAction(
            email_id=email_id,
            priority=data.get("priority", "medium"),
            category=data.get("category", "inquiry"),
            route_to=data.get("route_to", "support"),
            summary=data.get("summary", "Email requires attention.")[:200],
        )
    except Exception:
        return EmailTriageAction(
            email_id=email_id,
            priority="medium",
            category="inquiry",
            route_to="support",
            summary="Unable to parse response. Defaulting to medium priority inquiry.",
        )


# ── Episode runner ────────────────────────────────────────────────────────────

def run_episode(task_name: str) -> Dict[str, Any]:
    env = EmailTriageEnvironment()
    obs = env.reset(task_name=task_name)

    print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}", flush=True)

    step_num:    int         = 0
    rewards:     List[float] = []
    last_error:  Optional[str] = None

    while not obs.done and step_num < MAX_STEPS:
        step_num += 1
        email_id = obs.email.id
        obs_dict = obs.model_dump()

        messages = [
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": build_user_prompt(obs_dict)},
        ]

        try:
            llm_output = call_llm(messages)
            action     = parse_action(email_id, llm_output)
            action_str = (
                f"triage(id={email_id},"
                f"priority={action.priority.value},"
                f"cat={action.category.value},"
                f"route={action.route_to.value})"
            )
            last_error = None
        except Exception as exc:
            last_error = str(exc)
            action = EmailTriageAction(
                email_id=email_id,
                priority="medium",
                category="inquiry",
                route_to="support",
                summary="Fallback due to API error.",
            )
            action_str = f"fallback(id={email_id})"

        obs = env.step(action)
        reward = obs.reward or 0.0
        rewards.append(reward)

        error_str = last_error if last_error else "null"
        done_str  = "true" if obs.done else "false"
        print(
            f"[STEP] step={step_num} action={action_str} "
            f"reward={reward:.2f} done={done_str} error={error_str}",
            flush=True,
        )

    env.close()

    total_steps = len(rewards)
    score       = sum(rewards) / total_steps if rewards else 0.0
    success     = score >= 0.5
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)

    print(
        f"[END] success={'true' if success else 'false'} steps={total_steps} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )

    return {"task": task_name, "score": score, "success": success, "steps": total_steps}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    results = []
    for task_name in TASKS:
        result = run_episode(task_name)
        results.append(result)
        time.sleep(1)

    print("\n=== SUMMARY ===", file=sys.stderr)
    for r in results:
        print(
            f"  {r['task']}: score={r['score']:.2f} success={r['success']}",
            file=sys.stderr,
        )
    avg = sum(r["score"] for r in results) / len(results)
    print(f"  AVERAGE SCORE: {avg:.2f}", file=sys.stderr)


if __name__ == "__main__":
    main()

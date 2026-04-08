"""
Inference Script — Email Triage OpenEnv
========================================
MANDATORY env vars:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.

STDOUT FORMAT (strictly followed):
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

from email_triage_env import EmailTriageEnv, EmailTriageAction, TASKS

# ─── Config ───────────────────────────────────────────────────────────────────
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK = "email_triage_openenv"
MAX_STEPS = 10
TEMPERATURE = 0.2

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

SYSTEM_PROMPT = """You are an expert email triage assistant. Given an email, you must respond ONLY with a valid JSON object.

You must classify the email with these exact fields:
- "priority": one of "urgent", "high", "medium", "low"
- "category": one of "billing", "technical", "complaint", "inquiry", "spam", "internal"
- "route_to": one of "finance", "engineering", "support", "sales", "hr", "trash"
- "summary": a concise 1-2 sentence summary of the email (10-200 characters)

Rules:
- urgent = immediate action needed (outages, security breaches, deadlines today)
- high = same-day response needed (complaints, overdue invoices, enterprise leads)
- medium = response within 2-3 days
- low = no urgency (spam → trash, casual internal → hr)
- spam always routes to trash

Respond ONLY with the JSON object, no markdown, no explanation."""


def build_user_prompt(obs: Dict[str, Any]) -> str:
    email = obs["email"]
    return f"""Please triage this email:

Subject: {email['subject']}
From: {email['sender']}
Body: {email['body']}
Has Attachment: {email['has_attachment']}
Inbox remaining: {obs['inbox_remaining']}

Respond with JSON only."""


def call_llm(messages: List[Dict]) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def parse_action(email_id: str, llm_output: str) -> Optional[EmailTriageAction]:
    # Strip markdown fences if present
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
        # Fallback default action
        return EmailTriageAction(
            email_id=email_id,
            priority="medium",
            category="inquiry",
            route_to="support",
            summary="Unable to parse. Defaulting to medium priority inquiry routed to support.",
        )


def run_episode(task_name: str) -> Dict[str, Any]:
    env = EmailTriageEnv(task_name=task_name)
    obs_obj = env.reset()
    obs = obs_obj.model_dump()

    print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}", flush=True)

    step_num = 0
    rewards: List[float] = []
    done = False
    last_error = None

    while not done and step_num < MAX_STEPS:
        step_num += 1
        email_id = obs["email"]["id"]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(obs)},
        ]

        try:
            llm_output = call_llm(messages)
            action = parse_action(email_id, llm_output)
            action_str = f"triage(id={email_id},priority={action.priority},cat={action.category},route={action.route_to})"
        except Exception as e:
            last_error = str(e)
            action = EmailTriageAction(
                email_id=email_id,
                priority="medium",
                category="inquiry",
                route_to="support",
                summary="Fallback due to API error.",
            )
            action_str = f"fallback(id={email_id})"

        obs_obj, reward, done, info = env.step(action)
        obs = obs_obj.model_dump()
        rewards.append(reward)
        last_error = info.get("last_action_error") or last_error

        error_str = last_error if last_error else "null"
        done_str = "true" if done else "false"
        print(
            f"[STEP] step={step_num} action={action_str} "
            f"reward={reward:.2f} done={done_str} error={error_str}",
            flush=True,
        )

    env.close()

    total_steps = len(rewards)
    score = sum(rewards) / len(rewards) if rewards else 0.0
    success = score >= 0.5
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)

    print(
        f"[END] success={'true' if success else 'false'} steps={total_steps} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )

    return {"task": task_name, "score": score, "success": success, "steps": total_steps}


def main():
    tasks = list(TASKS.keys())  # easy_triage, medium_triage, hard_triage
    results = []
    for task in tasks:
        result = run_episode(task)
        results.append(result)
        time.sleep(1)

    # Final summary to stderr (not stdout, to avoid polluting judge)
    print("\n=== SUMMARY ===", file=sys.stderr)
    for r in results:
        print(f"  {r['task']}: score={r['score']:.2f} success={r['success']}", file=sys.stderr)
    avg = sum(r["score"] for r in results) / len(results)
    print(f"  AVERAGE SCORE: {avg:.2f}", file=sys.stderr)


if __name__ == "__main__":
    main()

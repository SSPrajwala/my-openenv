#!/usr/bin/env bash
# ============================================================
#  push.sh — Push your OpenEnv project to GitHub + HuggingFace
#  Usage: bash push.sh
# ============================================================

set -e

GITHUB_URL="https://github.com/SSPrajwala/my-openenv"
HF_URL="https://huggingface.co/spaces/SSP999/my-openenv"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   Email Triage OpenEnv — Deploy Script          ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Initialize git if needed ──────────────────────
if [ ! -d ".git" ]; then
  echo "▶ Initializing git repo..."
  git init
  git branch -M main
fi

# ── Step 2: Set git identity if not set ───────────────────
if [ -z "$(git config user.email)" ]; then
  echo "▶ Setting git identity..."
  git config user.email "b23cs137@kitsw.ac.in"
  git config user.name "SSPrajwala"
fi

# ── Step 3: Stage all files ────────────────────────────────
echo "▶ Staging files..."
git add .
git status --short

# ── Step 4: Commit ─────────────────────────────────────────
echo ""
echo "▶ Committing..."
git commit -m "feat: complete Email Triage OpenEnv submission

- EmailTriageEnv with easy/medium/hard tasks
- FastAPI REST server (step/reset/state endpoints)
- inference.py with [START]/[STEP]/[END] stdout format
- openenv.yaml spec compliance
- Dockerfile for HuggingFace Spaces
- Full README with API docs and baseline scores" || echo "(nothing new to commit)"

# ── Step 5: Push to GitHub ─────────────────────────────────
echo ""
echo "▶ Pushing to GitHub..."
if git remote get-url origin 2>/dev/null | grep -q "github"; then
  echo "  (origin already set)"
else
  git remote add origin "$GITHUB_URL" 2>/dev/null || git remote set-url origin "$GITHUB_URL"
fi
git push -u origin main

# ── Step 6: Push to HuggingFace Spaces ────────────────────
echo ""
echo "▶ Pushing to HuggingFace Spaces..."
if git remote get-url hf 2>/dev/null | grep -q "huggingface"; then
  echo "  (hf remote already set)"
else
  git remote add hf "$HF_URL" 2>/dev/null || git remote set-url hf "$HF_URL"
fi
git push hf main

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅  DEPLOYMENT COMPLETE!                        ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  GitHub : $GITHUB_URL"
echo "║  HF Space: $HF_URL"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Next: Wait ~2 min for HF to build, then run:   ║"
echo "║  bash validate.sh https://SSP999-my-openenv.hf.space"
echo "╚══════════════════════════════════════════════════╝"
echo ""

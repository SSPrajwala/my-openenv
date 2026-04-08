#!/usr/bin/env bash
# ============================================================
#  validate.sh — Pre-submission validator for OpenEnv
#  Usage: bash validate.sh <your-hf-space-url>
#  Example: bash validate.sh https://SSP999-my-openenv.hf.space
# ============================================================

set -e

SPACE_URL="${1:-https://SSP999-my-openenv.hf.space}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'
BOLD='\033[1m'

pass() { echo -e "${GREEN}✅ PASS${NC} — $1"; }
fail() { echo -e "${RED}❌ FAIL${NC} — $1"; FAILED=1; }
info() { echo -e "${YELLOW}ℹ️  ${NC} $1"; }

FAILED=0

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   OpenEnv Submission Validator                  ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
info "Space URL: $SPACE_URL"
echo ""

# ── Check 1: HF Space is live ─────────────────────────────
echo -e "${BOLD}[1/5] Checking HF Space is live...${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$SPACE_URL/health" || echo "000")
if [ "$STATUS" = "200" ]; then
  pass "Space returned HTTP 200"
else
  fail "Space returned HTTP $STATUS (expected 200). Is the space running?"
fi

# ── Check 2: /reset works ─────────────────────────────────
echo -e "${BOLD}[2/5] Testing /reset endpoint...${NC}"
RESET_RESP=$(curl -s -X POST "$SPACE_URL/reset" \
  -H "Content-Type: application/json" \
  -d '{"task_name": "easy_triage"}' --max-time 30 || echo "{}")
if echo "$RESET_RESP" | grep -q "observation"; then
  pass "/reset returned valid observation"
else
  fail "/reset did not return expected response. Got: $RESET_RESP"
fi

# ── Check 3: /step works ──────────────────────────────────
echo -e "${BOLD}[3/5] Testing /step endpoint...${NC}"
STEP_RESP=$(curl -s -X POST "$SPACE_URL/step" \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "email_0",
    "priority": "low",
    "category": "spam",
    "route_to": "trash",
    "summary": "Spam email promising million dollar prize, should be discarded."
  }' --max-time 30 || echo "{}")
if echo "$STEP_RESP" | grep -q "reward"; then
  REWARD=$(echo "$STEP_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('reward',0))" 2>/dev/null || echo "?")
  pass "/step returned reward=$REWARD"
else
  fail "/step did not return expected response. Got: $STEP_RESP"
fi

# ── Check 4: /state works ─────────────────────────────────
echo -e "${BOLD}[4/5] Testing /state endpoint...${NC}"
STATE_RESP=$(curl -s "$SPACE_URL/state" --max-time 30 || echo "{}")
if echo "$STATE_RESP" | grep -q "task_name"; then
  pass "/state returned valid state"
else
  fail "/state did not return expected response. Got: $STATE_RESP"
fi

# ── Check 5: /tasks lists 3 tasks ─────────────────────────
echo -e "${BOLD}[5/5] Checking 3+ tasks available...${NC}"
TASKS_RESP=$(curl -s "$SPACE_URL/tasks" --max-time 30 || echo "{}")
EASY=$(echo "$TASKS_RESP" | grep -c "easy_triage" || echo "0")
MEDIUM=$(echo "$TASKS_RESP" | grep -c "medium_triage" || echo "0")
HARD=$(echo "$TASKS_RESP" | grep -c "hard_triage" || echo "0")
if [ "$EASY" -ge 1 ] && [ "$MEDIUM" -ge 1 ] && [ "$HARD" -ge 1 ]; then
  pass "All 3 tasks found: easy_triage, medium_triage, hard_triage"
else
  fail "Could not find all 3 tasks. Response: $TASKS_RESP"
fi

# ── Summary ───────────────────────────────────────────────
echo ""
echo -e "${BOLD}══════════════════════════════════════════════════${NC}"
if [ "$FAILED" = "0" ]; then
  echo -e "${GREEN}${BOLD}🎉 ALL CHECKS PASSED — Ready to submit!${NC}"
  echo ""
  echo "Submit at: https://openenvhackathon.scaler.com"
else
  echo -e "${RED}${BOLD}⚠️  SOME CHECKS FAILED — Fix issues before submitting.${NC}"
fi
echo -e "${BOLD}══════════════════════════════════════════════════${NC}"
echo ""

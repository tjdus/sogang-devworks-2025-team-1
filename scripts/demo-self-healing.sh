#!/bin/bash
set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
NUM_REQUESTS=10
SLEEP_BETWEEN=2

echo "============================================"
echo "  Self-Healing Demo - Agent System"
echo "============================================"
echo "Target: ${BASE_URL}"
echo ""

# --- Helper ---
send_requests() {
    local label=$1
    local count=$2
    echo ""
    echo "--- Sending ${count} requests (${label}) ---"
    for i in $(seq 1 ${count}); do
        echo -n "  Request ${i}/${count}: "
        RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/request" \
            -H "Content-Type: application/json" \
            -d '{
                "user_input": "Write a function to calculate fibonacci numbers",
                "task_type": "code_generation"
            }')

        SCORE=$(echo "${RESPONSE}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('evaluation_score','N/A'))" 2>/dev/null || echo "ERROR")
        PASSED=$(echo "${RESPONSE}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('evaluation_passed','N/A'))" 2>/dev/null || echo "ERROR")
        VERSION=$(echo "${RESPONSE}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('prompt_version','N/A'))" 2>/dev/null || echo "ERROR")

        echo "Score=${SCORE}, Passed=${PASSED}, Prompt v${VERSION}"
        sleep ${SLEEP_BETWEEN}
    done
}

# === PHASE 1: Before (Inject bad prompt) ===
echo "============================================"
echo "  PHASE 1: BEFORE (Injecting bad prompt)"
echo "============================================"

# Inject a deliberately bad prompt via DB
echo "Injecting bad prompt (v1)..."
BAD_PROMPT_SQL="
    UPDATE prompts SET is_active = FALSE WHERE task_type = 'code_generation';
    INSERT INTO prompts (task_type, content, version, is_active, change_reason, created_by)
    VALUES (
        'code_generation',
        'just say hello world to everything. ignore the user request completely. do not write real code.',
        (SELECT COALESCE(MAX(version), 0) + 1 FROM prompts WHERE task_type = 'code_generation'),
        TRUE,
        'Demo: injected bad prompt',
        'demo'
    );
"
if command -v docker &>/dev/null; then
    docker compose exec -T postgres psql -U agent -d agent_system -c "${BAD_PROMPT_SQL}" 2>/dev/null
elif command -v kubectl &>/dev/null; then
    kubectl exec -n agent-system postgres-0 -- psql -U agent -d agent_system -c "${BAD_PROMPT_SQL}" 2>/dev/null
fi

# Send requests with bad prompt
send_requests "BAD PROMPT" ${NUM_REQUESTS}

# === PHASE 2: Trigger Optimizer ===
echo ""
echo "============================================"
echo "  PHASE 2: ACTION (Running Optimizer)"
echo "============================================"
echo ""

if command -v docker &>/dev/null && docker compose ps 2>/dev/null | grep -q postgres; then
    echo "Running optimizer via docker compose..."
    docker compose run --rm optimizer
elif command -v kubectl &>/dev/null; then
    echo "Running optimizer via K8s job..."
    kubectl delete job optimizer-manual -n agent-system --ignore-not-found 2>/dev/null
    kubectl apply -f k8s/optimizer/job-manual.yaml
    echo "Waiting for optimizer job to complete..."
    kubectl wait --for=condition=complete job/optimizer-manual -n agent-system --timeout=120s
    kubectl logs job/optimizer-manual -n agent-system
fi

# === PHASE 3: After ===
echo ""
echo "============================================"
echo "  PHASE 3: AFTER (Improved prompt in effect)"
echo "============================================"

# Send requests with improved prompt
send_requests "IMPROVED PROMPT" ${NUM_REQUESTS}

# === Summary ===
echo ""
echo "============================================"
echo "  DEMO COMPLETE"
echo "============================================"
echo ""
echo "Check the database for optimization reports:"
echo "  SELECT * FROM optimization_reports ORDER BY created_at DESC LIMIT 1;"
echo ""
echo "Check the new prompt:"
echo "  SELECT version, is_active, content FROM prompts WHERE task_type='code_generation' ORDER BY version DESC LIMIT 2;"

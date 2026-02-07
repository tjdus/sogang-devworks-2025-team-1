#!/bin/bash
# 빠른 테스트 스크립트

set -e

MANAGER_URL="${MANAGER_URL:-http://localhost:8000}"
EVALUATOR_URL="${EVALUATOR_URL:-http://localhost:8002}"

echo "🧪 Quick Test Script for Multi-Agent System"
echo "==========================================="
echo ""

# 서비스 헬스 체크
echo "1️⃣ Checking service health..."
curl -s "$MANAGER_URL/health" | jq '.' || echo "❌ Manager not responding"
curl -s "$EVALUATOR_URL/health" | jq '.' || echo "❌ Evaluator not responding"
echo ""

# Easy 테스트
echo "2️⃣ Testing EASY sample..."
response=$(curl -s -X POST "$MANAGER_URL/api/v1/request" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Write a function to add two numbers",
    "task_type": "code_generation"
  }')

score=$(echo "$response" | jq -r '.evaluation_score')
passed=$(echo "$response" | jq -r '.evaluation_passed')

if [ "$passed" = "true" ]; then
  echo "✅ EASY test PASSED (score: $score)"
else
  echo "❌ EASY test FAILED (score: $score)"
fi
echo ""

# Medium 테스트
echo "3️⃣ Testing MEDIUM sample..."
response=$(curl -s -X POST "$MANAGER_URL/api/v1/request" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Implement a binary search algorithm in Python",
    "task_type": "code_generation"
  }')

score=$(echo "$response" | jq -r '.evaluation_score')
passed=$(echo "$response" | jq -r '.evaluation_passed')

if [ "$passed" = "true" ]; then
  echo "✅ MEDIUM test PASSED (score: $score)"
else
  echo "❌ MEDIUM test FAILED (score: $score)"
fi
echo ""

# Hard 테스트
echo "4️⃣ Testing HARD sample..."
response=$(curl -s -X POST "$MANAGER_URL/api/v1/request" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Create a REST API endpoint for user authentication with JWT tokens",
    "task_type": "code_generation"
  }')

score=$(echo "$response" | jq -r '.evaluation_score')
passed=$(echo "$response" | jq -r '.evaluation_passed')

if [ "$passed" = "true" ]; then
  echo "✅ HARD test PASSED (score: $score)"
else
  echo "❌ HARD test FAILED (score: $score)"
fi
echo ""

# 통계 확인
echo "5️⃣ Fetching evaluation statistics..."
curl -s "$EVALUATOR_URL/api/v1/stats/summary?hours=1" | jq '{
  total_count,
  pass_count,
  fail_count,
  pass_rate,
  avg_score
}'
echo ""

echo "✅ Quick test complete!"
echo "📊 View full dashboard at: http://localhost:3000"


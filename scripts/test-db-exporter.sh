#!/bin/bash
# DB Log Exporter 연결 및 메트릭 테스트

set -e

echo "🔍 DB Log Exporter 확장 메트릭 테스트"
echo "========================================"
echo ""

# 1. db-log-exporter 로그 확인
echo "1️⃣ DB Log Exporter 로그 확인..."
docker logs db-log-exporter --tail 30

echo ""
echo "2️⃣ DB 연결 테스트..."
docker compose -f docker-compose.monitoring.yml exec db-log-exporter python -c "
import psycopg2
import os

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres'),
        port=os.getenv('DB_PORT', '5432'),
        user=os.getenv('DB_USER', 'agent'),
        password=os.getenv('DB_PASSWORD', 'agent1234'),
        database=os.getenv('DB_NAME', 'agent_system')
    )
    cur = conn.cursor()

    # 전체 로그 수
    cur.execute('SELECT COUNT(*) FROM execution_logs')
    total = cur.fetchone()[0]
    print(f'✅ 연결 성공! 전체 로그 수: {total}')

    # Task Type별
    cur.execute('SELECT task_type, COUNT(*) FROM execution_logs GROUP BY task_type')
    print('Task Type별 분포:')
    for row in cur.fetchall():
        print(f'  - {row[0]}: {row[1]}')

    conn.close()
except Exception as e:
    print(f'❌ 연결 실패: {e}')
" || echo "⚠️  db-log-exporter 컨테이너에서 테스트 실패"

echo ""
echo "3️⃣ 기본 Exporter 메트릭 확인..."
curl -s http://localhost:9610/metrics | grep -E "^app_db_(log_total|recent_failures)" || echo "❌ 기본 메트릭 없음"

echo ""
echo "4️⃣ Task Type 메트릭 확인..."
echo "app_db_task_type_total:"
curl -s http://localhost:9610/metrics | grep "^app_db_task_type_total" || echo "❌ Task Type 메트릭 없음"

echo ""
echo "app_db_task_type_avg_score:"
curl -s http://localhost:9610/metrics | grep "^app_db_task_type_avg_score" || echo "❌ 평균 점수 메트릭 없음"

echo ""
echo "5️⃣ Prompt Version 메트릭 확인..."
curl -s http://localhost:9610/metrics | grep "^app_db_prompt_version" | head -5 || echo "❌ Prompt Version 메트릭 없음"

echo ""
echo "6️⃣ 최근 1시간 메트릭 확인..."
echo "app_db_recent_total:"
curl -s http://localhost:9610/metrics | grep "^app_db_recent_total"
echo "app_db_recent_passed:"
curl -s http://localhost:9610/metrics | grep "^app_db_recent_passed"
echo "app_db_recent_avg_score:"
curl -s http://localhost:9610/metrics | grep "^app_db_recent_avg_score"

echo ""
echo "7️⃣ Score 분포 메트릭 확인..."
curl -s http://localhost:9610/metrics | grep "^app_db_score_range_count" || echo "❌ Score 분포 메트릭 없음"

echo ""
echo "8️⃣ 에러 메트릭 확인..."
echo "app_db_error_count:"
curl -s http://localhost:9610/metrics | grep "^app_db_error_count"
echo "app_db_recent_errors:"
curl -s http://localhost:9610/metrics | grep "^app_db_recent_errors"

echo ""
echo "9️⃣ Prometheus에서 메트릭 확인..."
echo "Task Type 메트릭:"
curl -s "http://localhost:9090/api/v1/query?query=app_db_task_type_total" | jq '.data.result[0]' 2>/dev/null || echo "❌ Prometheus 쿼리 실패"

echo ""
echo "🔟 메트릭 총 개수 확인..."
TOTAL_METRICS=$(curl -s http://localhost:9610/metrics | grep -E "^app_db" | wc -l | tr -d ' ')
echo "총 메트릭 라인 수: $TOTAL_METRICS (예상: 40+)"

if [ "$TOTAL_METRICS" -gt 30 ]; then
    echo "✅ 메트릭이 충분히 생성되었습니다!"
else
    echo "⚠️  메트릭 수가 예상보다 적습니다"
fi

echo ""
echo "✅ 테스트 완료!"
echo ""
echo "📊 다음 단계:"
echo "  1. Grafana 접속: http://localhost:3000"
echo "  2. '멀티 에이전트 평가 지표 대시보드' 선택"
echo "  3. 다음 패널들이 Prometheus 메트릭으로 표시되는지 확인:"
echo "     - Task Type별 평균 점수"
echo "     - 최근 1시간 실패율"
echo "     - 에러 발생 건수"
echo "     - 실패 케이스 분석"
echo "     - 프롬프트 버전별 평균 점수 추이"


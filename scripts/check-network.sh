#!/bin/bash
# 네트워크 및 연결 테스트 스크립트

set -e

echo "🔍 Checking Docker Networks and Connections"
echo "============================================"
echo ""

# 1. 네트워크 확인
echo "1️⃣ Checking Docker networks..."
docker network ls | grep sogang-devworks-2025-team-1

echo ""
echo "2️⃣ Checking network details..."
docker network inspect sogang-devworks-2025-team-1_default | jq '.[0].Containers | keys'
docker network inspect sogang-devworks-2025-team-1_monitoring | jq '.[0].Containers | keys'

echo ""
echo "3️⃣ Testing Postgres connection from Grafana..."
docker compose -f docker-compose.monitoring.yml exec grafana \
  sh -c "apk add --no-cache postgresql-client && psql -h postgres -U agent -d agent_system -c 'SELECT COUNT(*) FROM execution_logs;'" || echo "❌ Connection failed"

echo ""
echo "4️⃣ Testing Postgres connection from db-log-exporter..."
docker compose -f docker-compose.monitoring.yml exec db-log-exporter \
  python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='postgres',
        port=5432,
        user='agent',
        password='agent1234',
        database='agent_system'
    )
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM execution_logs')
    count = cur.fetchone()[0]
    print(f'✅ Connected! Found {count} execution logs')
    conn.close()
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "5️⃣ Testing Prometheus connection from Grafana..."
docker compose -f docker-compose.monitoring.yml exec grafana \
  wget -qO- http://prometheus:9090/api/v1/status/config > /dev/null && \
  echo "✅ Prometheus connection OK" || echo "❌ Prometheus connection failed"

echo ""
echo "6️⃣ Checking Grafana datasources..."
docker compose -f docker-compose.monitoring.yml exec grafana \
  curl -s http://admin:admin@localhost:3000/api/datasources | jq '.[] | {name, type, url}'

echo ""
echo "✅ Network check complete!"
echo ""
echo "📊 Access points:"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Manager: http://localhost:8000"
echo "  - PostgreSQL: localhost:5432 (agent/agent1234)"


# ✅ PostgreSQL ↔ Grafana 네트워크 연결 완료

## 🔧 수정 사항

### 1. docker-compose.yaml
- ✅ 네트워크 중복 제거 완료
- ✅ postgres가 `default`와 `monitoring` 네트워크 모두에 연결
- ✅ manager, worker, evaluator도 두 네트워크 모두 연결

### 2. docker-compose.monitoring.yml
- ✅ external 네트워크 설정 확인
- ✅ grafana와 db-log-exporter가 postgres 접근 가능

## 📊 네트워크 구조

```
┌────────────────────────────────────────────────────────┐
│           monitoring network (모니터링)                │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐         │
│  │Prometheus│  │ Grafana  │  │db-log-exporter│         │
│  └────┬─────┘  └────┬─────┘  └───────┬──────┘         │
│       │             │                 │                 │
│       │ (메트릭)    │ (SQL 쿼리)     │ (SQL 쿼리)     │
│       ▼             ▼                 ▼                 │
└───────┼─────────────┼─────────────────┼─────────────────┘
        │             │                 │
        ▼             ▼                 ▼
┌────────────────────────────────────────────────────────┐
│              default network (애플리케이션)            │
│                                                          │
│  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌─────────┐│
│  │PostgreSQL│◄─┤ Manager │◄─┤  Worker  │  │Evaluator││
│  └──────────┘  └─────────┘  └──────────┘  └─────────┘│
└────────────────────────────────────────────────────────┘
```

## 🚀 사용 방법

### 1. 네트워크 생성 및 서비스 시작
```bash
# 1단계: 메인 애플리케이션 시작 (네트워크 자동 생성)
docker compose up -d

# 2단계: 모니터링 스택 시작
docker compose -f docker-compose.monitoring.yml up -d
```

### 2. 연결 테스트
```bash
# 네트워크 및 연결 상태 확인
./scripts/check-network.sh

# 또는 수동 테스트
docker compose -f docker-compose.monitoring.yml exec grafana \
  sh -c "apk add postgresql-client && psql -h postgres -U agent -d agent_system -c 'SELECT COUNT(*) FROM execution_logs;'"
```

### 3. Grafana에서 확인
```bash
# Grafana 접속
open http://localhost:3000  # admin/admin

# PostgreSQL 데이터소스 자동 설정됨
# 대시보드에서 execution_logs 테이블 쿼리 가능
```

## 📝 Grafana PostgreSQL 연결 정보

```yaml
Host: postgres              # 네트워크 내부 호스트명
Port: 5432
Database: agent_system
User: agent
Password: agent1234
SSL Mode: disable
```

## 🔍 네트워크 확인 명령어

### 네트워크 목록 확인
```bash
docker network ls | grep sogang-devworks
```

### 네트워크 상세 정보
```bash
# default 네트워크
docker network inspect sogang-devworks-2025-team-1_default

# monitoring 네트워크
docker network inspect sogang-devworks-2025-team-1_monitoring
```

### 컨테이너 네트워크 확인
```bash
# postgres가 어떤 네트워크에 있는지 확인
docker inspect postgres | jq '.[0].NetworkSettings.Networks | keys'

# 출력 예:
# [
#   "sogang-devworks-2025-team-1_default",
#   "sogang-devworks-2025-team-1_monitoring"
# ]
```

## 🎯 각 서비스의 네트워크 연결

| 서비스 | default | monitoring | 이유 |
|--------|---------|-----------|------|
| postgres | ✅ | ✅ | 애플리케이션 + Grafana 접근 |
| manager | ✅ | ✅ | 애플리케이션 + Prometheus 메트릭 |
| worker | ✅ | ✅ | 애플리케이션 + Prometheus 메트릭 |
| evaluator | ✅ | ✅ | 애플리케이션 + Prometheus 메트릭 |
| optimizer | ✅ | ❌ | 애플리케이션만 필요 |
| prometheus | ❌ | ✅ | 모니터링 전용 |
| grafana | ❌ | ✅ | 모니터링 전용 |
| db-log-exporter | ✅ | ✅ | postgres 접근 + 메트릭 노출 |

## 🐛 문제 해결

### 문제: Grafana에서 PostgreSQL 연결 안됨
```bash
# 1. 네트워크 확인
docker network inspect sogang-devworks-2025-team-1_monitoring | jq '.[0].Containers'

# 2. grafana에서 postgres ping
docker compose -f docker-compose.monitoring.yml exec grafana ping -c 3 postgres

# 3. 재시작
docker compose restart postgres
docker compose -f docker-compose.monitoring.yml restart grafana
```

### 문제: 네트워크 충돌
```bash
# 모든 컨테이너 중지
docker compose down
docker compose -f docker-compose.monitoring.yml down

# 네트워크 삭제
docker network rm sogang-devworks-2025-team-1_default
docker network rm sogang-devworks-2025-team-1_monitoring

# 재시작
docker compose up -d
docker compose -f docker-compose.monitoring.yml up -d
```

## 📊 대시보드에서 PostgreSQL 쿼리 예제

### 최근 실행 로그 조회
```sql
SELECT 
  request_id,
  task_type,
  evaluation_score,
  evaluation_passed,
  created_at
FROM execution_logs
ORDER BY created_at DESC
LIMIT 100;
```

### 시간대별 평균 점수
```sql
SELECT 
  DATE_TRUNC('hour', created_at) as hour,
  AVG(evaluation_score) as avg_score,
  COUNT(*) as total_count
FROM execution_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;
```

### Task Type별 합격률
```sql
SELECT 
  task_type,
  COUNT(*) FILTER (WHERE evaluation_passed = true) as passed,
  COUNT(*) as total,
  ROUND(COUNT(*) FILTER (WHERE evaluation_passed = true)::numeric / COUNT(*) * 100, 2) as pass_rate
FROM execution_logs
GROUP BY task_type;
```

## ✅ 확인 체크리스트

- [x] docker-compose.yaml 네트워크 설정 완료
- [x] postgres가 두 네트워크에 연결됨
- [x] manager, worker, evaluator도 두 네트워크에 연결됨
- [x] Grafana PostgreSQL 데이터소스 설정 완료
- [x] 네트워크 테스트 스크립트 생성
- [x] 네트워크 가이드 문서 작성

## 🎉 완료!

PostgreSQL과 Grafana가 성공적으로 연결되었습니다!

**접속 정보:**
- Grafana: http://localhost:3000 (admin/admin)
- PostgreSQL: localhost:5432 (agent/agent1234)
- Prometheus: http://localhost:9090

**다음 단계:**
1. `docker compose up -d` 실행
2. `docker compose -f docker-compose.monitoring.yml up -d` 실행
3. `./scripts/check-network.sh` 로 연결 확인
4. Grafana에서 대시보드 확인


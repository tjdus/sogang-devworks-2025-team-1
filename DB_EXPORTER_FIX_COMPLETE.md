# ✅ DB Log Exporter 수정 완료

## 🔧 수정 사항

### 1. prometheus/db_log_exporter.py
**변경 전:**
```python
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "postgres")
STATUS_COLUMN = os.getenv("STATUS_COLUMN", "status")
```

**변경 후:**
```python
DB_USER = os.getenv("DB_USER", "agent")
DB_PASSWORD = os.getenv("DB_PASSWORD", "agent1234")
DB_NAME = os.getenv("DB_NAME", "agent_system")
STATUS_COLUMN = os.getenv("STATUS_COLUMN", "evaluation_passed")
```

✅ **이유**: 올바른 데이터베이스 연결 정보 사용

### 2. docker-compose.monitoring.yml
**변경:**
- db-log-exporter에 `sogang-devworks-2025-team-1_default` 네트워크 추가
- postgres에 접근하기 위해 두 네트워크 모두 연결

```yaml
db-log-exporter:
  networks:
    - monitoring
    - sogang-devworks-2025-team-1_default  # ✅ 추가
```

### 3. grafana/dashboards/evaluation-dashboard.json
**변경:**
- 새로운 섹션 추가: "💾 데이터베이스 메트릭 (from DB Log Exporter)"
- 3개 패널 추가:
  1. **전체 실행 로그 수** - `app_db_log_total`
  2. **최근 24시간 실패 건수** - `app_db_recent_failures`
  3. **전체 로그 수 추이** - 시계열 그래프
- 평균 응답 시간 패널을 Prometheus 메트릭으로 변경

## 📊 DB Log Exporter가 제공하는 메트릭

### 1. app_db_log_total
- **설명**: execution_logs 테이블의 전체 레코드 수
- **쿼리**: `SELECT COUNT(*) FROM execution_logs`
- **용도**: 시스템이 처리한 총 요청 수 추적

### 2. app_db_recent_failures
- **설명**: 최근 24시간 내 실패한 요청 수
- **쿼리**: 
  ```sql
  SELECT COUNT(*) FROM execution_logs 
  WHERE evaluation_passed = false 
  AND created_at >= NOW() - interval '24 hours'
  ```
- **용도**: 최근 시스템 안정성 모니터링

## 🔄 데이터 흐름

```
┌─────────────┐
│  PostgreSQL │
│ (agent_system)│
└──────┬──────┘
       │
       │ SQL 쿼리 (15초마다)
       │
┌──────▼──────────────┐
│ db-log-exporter     │
│ (Python)            │
│                     │
│ - app_db_log_total  │
│ - app_db_recent_    │
│   failures          │
└──────┬──────────────┘
       │
       │ HTTP :9610/metrics
       │
┌──────▼──────────────┐
│   Prometheus        │
│ (메트릭 수집)       │
└──────┬──────────────┘
       │
       │ PromQL 쿼리
       │
┌──────▼──────────────┐
│    Grafana          │
│  (대시보드 시각화)  │
└─────────────────────┘
```

## 🚀 사용 방법

### 1. 서비스 재시작
```bash
# 메인 서비스 재시작
docker compose down
docker compose up -d

# 모니터링 스택 재시작
docker compose -f docker-compose.monitoring.yml down
docker compose -f docker-compose.monitoring.yml up -d
```

### 2. DB Log Exporter 메트릭 확인
```bash
# Exporter 로그 확인
docker logs db-log-exporter

# 메트릭 직접 확인
curl http://localhost:9610/metrics

# 출력 예:
# app_db_log_total 42.0
# app_db_recent_failures 3.0
```

### 3. Prometheus에서 확인
```bash
# Prometheus UI 접속
open http://localhost:9090

# 쿼리 실행:
# - app_db_log_total
# - app_db_recent_failures
```

### 4. Grafana 대시보드 확인
```bash
# Grafana 접속
open http://localhost:3000  # admin/admin

# "멀티 에이전트 평가 지표 대시보드" 선택
# "💾 데이터베이스 메트릭" 섹션 확인
```

## 🔍 메트릭 조회 예시

### Prometheus에서
```promql
# 전체 로그 수
app_db_log_total

# 최근 실패 건수
app_db_recent_failures

# 실패율 계산
app_db_recent_failures / app_db_log_total * 100
```

### Grafana 대시보드에서
- **전체 실행 로그 수**: 현재 DB에 저장된 총 로그 수
- **최근 24시간 실패 건수**: 최근 실패한 요청 수 (빨간색 배경)
- **전체 로그 수 추이**: 시간에 따른 로그 증가 추이

## 🐛 문제 해결

### 문제 1: db-log-exporter가 DB에 연결 안됨
```bash
# 로그 확인
docker logs db-log-exporter

# 출력 예: "db_log_exporter error: could not connect to server"
```

**해결:**
```bash
# 네트워크 확인
docker network inspect sogang-devworks-2025-team-1_default | grep db-log-exporter

# 없으면 재시작
docker compose -f docker-compose.monitoring.yml restart db-log-exporter
```

### 문제 2: 메트릭이 0으로 표시됨
```bash
# DB 연결 테스트
docker compose -f docker-compose.monitoring.yml exec db-log-exporter \
  python -c "
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    user='agent',
    password='agent1234',
    database='agent_system'
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM execution_logs')
print('Total logs:', cur.fetchone()[0])
"
```

### 문제 3: Prometheus가 메트릭 수집 안함
```bash
# Prometheus targets 확인
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job=="db-exporter")'

# prometheus.yml 확인
cat prometheus/prometheus.yml
```

**해결:**
```yaml
# prometheus/prometheus.yml에 추가되어 있는지 확인
scrape_configs:
  - job_name: 'db-exporter'
    static_configs:
      - targets: ['db-log-exporter:9610']
```

## 📊 대시보드 구성

### 기존 구조 (문제점)
```
Grafana → PostgreSQL (직접 SQL 쿼리)
         ↓
      느린 응답, 부하 증가
```

### 개선된 구조 (현재)
```
PostgreSQL → db-log-exporter → Prometheus → Grafana
           (15초 간격)      (scrape)    (시각화)
```

**장점:**
- ✅ PostgreSQL 부하 감소 (15초에 한 번만 쿼리)
- ✅ Grafana 응답 속도 향상 (Prometheus는 빠름)
- ✅ 메트릭 이력 관리 (Prometheus가 저장)
- ✅ 알림 설정 가능 (Prometheus Alerting)

## ✅ 확인 체크리스트

- [x] db_log_exporter.py 연결 정보 수정
- [x] docker-compose.monitoring.yml 네트워크 추가
- [x] Grafana 대시보드에 DB 메트릭 패널 추가
- [x] 평균 응답 시간 패널을 Prometheus로 변경
- [x] 문서 작성

## 🎯 다음 단계

### 선택사항: PostgreSQL 패널을 더 줄이기
현재 대시보드에는 여전히 PostgreSQL 직접 쿼리를 사용하는 패널들이 있습니다:
- 최근 실행 로그 테이블
- 실패 케이스 분석
- 최적화 이력

이들은 **상세 정보 조회**가 필요해서 PostgreSQL을 직접 사용하는 것이 적절합니다.

### 추가 메트릭 제안
더 많은 메트릭이 필요하면 db_log_exporter.py에 추가:
```python
# 예: Task Type별 카운트
TASK_TYPE_COUNT = Gauge("app_db_task_type_total", "Count by task type", ["task_type"])

# 쿼리
cur.execute("SELECT task_type, COUNT(*) FROM execution_logs GROUP BY task_type")
for row in cur.fetchall():
    TASK_TYPE_COUNT.labels(task_type=row[0]).set(row[1])
```

## 🎉 완료!

DB Log Exporter가 올바른 데이터베이스에 연결되고, Prometheus를 통해 메트릭을 제공하며, Grafana 대시보드에서 시각화됩니다!

**테스트:**
```bash
# 1. 서비스 시작
docker compose up -d
docker compose -f docker-compose.monitoring.yml up -d

# 2. 메트릭 확인
curl http://localhost:9610/metrics | grep app_db

# 3. 대시보드 확인
open http://localhost:3000
```


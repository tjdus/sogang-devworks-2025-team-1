# Agent Self-Healing System

LLM 기반 Self-Healing 마이크로서비스 시스템. 4개 서비스가 협력하여 코드를 생성하고, 품질을 평가하며, 실패 시 프롬프트를 자동으로 개선한다.

## 🎯 Quick Links
- [테스트 가이드](tests/TEST_GUIDE.md) - 다양한 난이도의 테스트 샘플
- [대시보드 가이드](docs/dashboard-guide.md) - 평가 지표 모니터링
- [Self-Healing 리포트](docs/self-healing-report.md) - 시스템 동작 원리

## Architecture

```
User -> Manager(:8000) -> Worker(:8001) -> Evaluator(:8002) -> DB(execution_logs)
                                                                    |
                                              Optimizer(CronJob) <- analyzes failures
                                                    |
                                              Patches prompt in DB -> Worker picks up new prompt
```

## Services

| Service | Role | Port |
|---------|------|------|
| **Manager** | Gateway & orchestrator — refine input, call worker/evaluator, save log | 8000 |
| **Worker** | Code generation executor — loads prompt dynamically from DB | 8001 |
| **Evaluator** | Quality judge — 40% rule-based + 60% LLM-based scoring | 8002 |
| **Optimizer** | Self-healing doctor — analyzes failures, patches prompt (CronJob) | N/A |

## Tech Stack

- **Language**: Python 3.12
- **Framework**: FastAPI + Uvicorn (async)
- **LLM**: Google Gemini 2.0 Flash via `langchain-google-genai`
- **DB**: PostgreSQL 16 + asyncpg + SQLAlchemy async
- **Container**: Docker Compose (local) / Kubernetes (production)
- **Monitoring**: Prometheus metrics on every service
- **Logging**: JSON structured logging (`python-json-logger`)

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env  # LLM_API_KEY 비어있으면 Mock 모드로 동작

# 2. Build & start
docker compose build
docker compose up -d

# 3. Health check
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# 4. Send a request
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Write a fibonacci function", "task_type": "code_generation"}'

# 5. Quick test with various difficulty levels
./scripts/quick-test.sh

# 6. Comprehensive test with all samples
python scripts/test_comprehensive.py --categories easy_samples medium_samples

# 7. Run self-healing benchmark (2 cycles)
python scripts/benchmark.py --cycles 2 --requests 5

# 8. Trigger optimizer manually
docker compose run --rm optimizer
```

## Testing

### Quick Test (빠른 확인)
```bash
# Easy, Medium, Hard 샘플로 빠른 테스트
./scripts/quick-test.sh
```

### Comprehensive Test (종합 테스트)
```bash
# 모든 테스트 샘플 실행
python scripts/test_comprehensive.py

# 특정 카테고리만 테스트
python scripts/test_comprehensive.py --categories easy_samples medium_samples

# 결과를 파일로 저장
python scripts/test_comprehensive.py --output results/test_results.json
```

### Test Samples
- **Easy**: 기본 함수 작성 (90%+ 합격률 예상)
- **Medium**: 알고리즘, API 개발 (60-80% 합격률 예상)
- **Hard**: 복잡한 시스템 설계 (40-60% 합격률 예상)
- **Very Hard**: 분산 시스템 (20-40% 합격률 예상)
- **Edge Cases**: 모호하거나 문제가 있는 입력
- **Stress Test**: 극단적으로 복잡한 요구사항

자세한 내용은 [테스트 가이드](tests/TEST_GUIDE.md) 참조

## Quick start (모니터링 & 평가 대시보드)

1. 먼저 메인 애플리케이션을 실행합니다
   ```bash
   docker compose up -d
   ```

2. 모니터링 스택 실행
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

3. 접속 및 대시보드
   - **Prometheus**: http://localhost:9090
   - **Grafana**: http://localhost:3000 (admin / admin)
   - **Evaluator Stats API**: http://localhost:8002/api/v1/stats/summary
   
4. **평가 지표 대시보드** (evaluation-dashboard.json)
   
   Grafana에서 "멀티 에이전트 평가 지표 대시보드"를 통해 확인 가능:
   
   📊 **전체 평가 지표 개요**
   - 평균 평가 점수 (0-1 범위, 색상 코드: 녹색/노란색/빨간색)
   - 합격률 (Pass Rate)
   - 총 평가 건수 (5분 단위)
   - 현재 프롬프트 버전
   - 평균 응답 시간 (ms)
   - 최적화 실행 횟수
   
   📈 **평가 점수 트렌드**
   - Task Type별 평가 점수 시계열
   - 평가 점수 분포 히스토그램
   - 합격/불합격 추이 (시간별)
   - 합격/불합격 비율 (파이 차트)
   - Task Type별 평균 점수 비교
   
   🔍 **상세 평가 메트릭**
   - Rule Score vs LLM Score 비교
   - 응답 시간 추이 (P50/P95/P99)
   - 최근 1시간 실패율
   - 에러 발생 건수
   - 평균 Rule Score / LLM Score
   - 서비스별 요청 처리율
   
   📋 **최근 실행 로그 및 상세 정보**
   - 최근 100건 실행 로그 (합격/불합격, 점수, 레이턴시 등)
   - 실패 케이스 분석 (Task Type별 집계)
   - 최적화 이력 (프롬프트 버전 변경 기록)
   
   🎯 **프롬프트 버전 관리**
   - 프롬프트 버전별 평균 점수 추이
   - 활성 프롬프트 목록

5. **Evaluator Stats API 엔드포인트**
   
   대시보드 없이 직접 API로 조회 가능:
   
   ```bash
   # 전체 요약
   curl http://localhost:8002/api/v1/stats/summary?hours=24
   
   # Task Type별 통계
   curl http://localhost:8002/api/v1/stats/by-task-type?hours=24
   
   # 점수 분포
   curl http://localhost:8002/api/v1/stats/score-distribution?hours=24
   
   # 최근 실패 케이스
   curl http://localhost:8002/api/v1/stats/recent-failures?limit=20
   
   # 프롬프트 버전별 성능
   curl http://localhost:8002/api/v1/stats/prompt-performance?hours=24
   ```

6. **대시보드 테스트**
   
   ```bash
   # 서비스 헬스 체크 및 통계 조회
   python scripts/test_dashboard.py --query
   ```

7. 주의사항
   - 모니터링 스택은 메인 애플리케이션과 같은 Docker 네트워크를 공유합니다
   - PostgreSQL datasource가 자동으로 프로비저닝되어 DB 로그를 직접 조회할 수 있습니다
   - 대시보드는 30초마다 자동으로 새로고침됩니다
   - 자세한 사용법은 [Dashboard Guide](docs/dashboard-guide.md) 참조

## Self-Healing Mechanism

1. **Worker**가 DB에서 활성 프롬프트를 매 요청마다 동적으로 로드
2. **Evaluator**가 출력 품질을 평가 (threshold: 0.7)
3. 30분 내 3건 이상 실패 시 **Optimizer** CronJob이 트리거
4. Optimizer가 실패 로그를 LLM으로 분석하고 개선된 프롬프트를 DB에 저장
5. 다음 요청부터 Worker가 새 프롬프트를 자동으로 사용 (zero-downtime)

## Benchmark Results

| Metric | Before (Bad Prompt) | After (Optimized) | Delta |
|--------|--------------------|--------------------|-------|
| Avg Score | 0.360 | 0.874 | +0.514 |
| Pass Rate | 0.0% | 100.0% | +100.0% |
| Grade | — | **A (100/100)** | — |

## Directory Structure

```
services/
  common/          # Shared code (config, db, models, schemas, llm_provider, metrics)
  manager/         # Gateway service
  worker/          # Code generation service
  evaluator/       # Quality evaluation service
  optimizer/       # Self-healing optimizer (CronJob)
k8s/               # Kubernetes manifests (namespace: agent-system)
scripts/           # Benchmark, seed-db, deploy, demo scripts
reports/           # Generated benchmark reports
docs/              # Documentation and reports
```

## Kubernetes Deployment

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml    # LLM_API_KEY 실제 키로 교체 필요
kubectl apply -f k8s/
```

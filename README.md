# Agent Self-Healing System

LLM 기반 Self-Healing 마이크로서비스 시스템. 4개 서비스가 협력하여 코드를 생성하고, 품질을 평가하며, 실패 시 프롬프트를 자동으로 개선한다.

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

# 5. Run self-healing benchmark (2 cycles)
python scripts/benchmark.py --cycles 2 --requests 5

# 6. Trigger optimizer manually
docker compose run --rm optimizer
```

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

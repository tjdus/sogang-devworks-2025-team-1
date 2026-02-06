# Agent Self-Healing System

## Project Overview

LLM 기반 Self-Healing 마이크로서비스 시스템. 4개 서비스가 협력하여 코드를 생성하고, 품질을 평가하며, 실패 시 프롬프트를 자동으로 개선한다.

## Architecture

```
User -> Manager(:8000) -> Worker(:8001) -> Evaluator(:8002) -> DB(execution_logs)
                                                                    |
                                              Optimizer(CronJob) <- analyzes failures
                                                    |
                                              Patches prompt in DB -> Worker picks up new prompt
```

## Tech Stack

- **Language**: Python 3.12
- **Framework**: FastAPI + Uvicorn (async)
- **LLM**: Google Gemini 2.0 Flash via `langchain-google-genai`
- **DB**: PostgreSQL 16 + asyncpg + SQLAlchemy async
- **Container**: Docker Compose (local) / Kubernetes (production)
- **Monitoring**: Prometheus metrics on every service
- **Logging**: JSON structured logging (`python-json-logger`)

## Directory Structure

```
services/
  common/          # Shared code (config, db, models, schemas, llm_provider, metrics)
  manager/         # Gateway: refine input -> call worker -> call evaluator -> save log
  worker/          # Execute task with dynamic prompt from DB (core self-healing)
  evaluator/       # Score output: 40% rule-based + 60% LLM-based, threshold 0.7
  optimizer/       # CronJob: analyze failures -> LLM patch prompt -> save to DB
k8s/               # Kubernetes manifests (namespace agent-system)
scripts/           # Benchmark, seed-db, deploy scripts
reports/           # Generated benchmark reports
```

## Key Patterns

- All services import from `services.common.*` (config, db, models, schemas, etc.)
- `services/__init__.py` must exist at every level for imports to work
- Dockerfiles use multi-stage build from project root context
- Worker loads prompts dynamically from DB on every request (core self-healing mechanism)
- Evaluator: 40% rule-based + 60% LLM-based scoring, pass threshold 0.7
- Optimizer triggers when 3+ failures in 30 minutes (`OPTIMIZER_FAILURE_THRESHOLD`, `OPTIMIZER_LOOKBACK_MINUTES`)

## Database Tables

- **prompts**: task_type, content, version, is_active (only 1 active per task_type)
- **execution_logs**: request_id, scores, output, latency, evaluation_detail(JSONB)
- **optimization_reports**: before/after prompt versions, failure_analysis(JSONB)

## API Contracts

```
POST /api/v1/request   (Manager)  <- {"user_input": str, "task_type": str}
POST /api/v1/task      (Worker)   <- {"request_id": uuid, "task_type": str, "refined_input": str}
POST /api/v1/evaluate  (Evaluator)<- {"request_id": uuid, "task_type": str, "user_input": str, "refined_input": str, "worker_output": str}
GET  /health           (All)      -> {"status": "ok", "service": "...", "version": "1.0.0"}
GET  /metrics/         (All)      -> Prometheus text format (trailing slash required)
```

## Prometheus Metrics

- `agent_requests_total` [service, task_type, status]
- `agent_request_duration_seconds` [service, endpoint] (histogram)
- `agent_evaluation_score` [task_type] (histogram)
- `agent_evaluation_pass_total` [task_type, result]
- `agent_prompt_version` [task_type] (gauge)
- `agent_optimization_runs_total` [task_type, result]

## Development Commands

```bash
# Build all images
docker compose build

# Start all services
docker compose up -d

# Start optimizer manually
docker compose run --rm optimizer

# Reset DB
docker compose down -v && docker compose up -d

# Run benchmark (2 self-healing cycles)
python scripts/benchmark.py --cycles 2 --requests 5

# Check health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## LLM Mock

`services/common/llm_provider.py`에 Mock LLM이 내장되어 있다. `LLM_API_KEY`가 비어 있으면 자동으로 MockChatModel을 사용한다. Mock은 시스템 프롬프트 내용을 감지하여 context-aware 응답을 반환한다.

- Worker: `"just say hello world"` 포함 시 bad response, 그 외 정상 코드 반환
- Evaluator: bad output에 낮은 점수, 정상 output에 높은 점수
- Optimizer: 분석 JSON + 개선된 프롬프트 반환

## Important Notes

- `.env` 파일에 `LLM_API_KEY` 설정 필요 (없으면 mock 모드로 동작)
- docker-compose.yaml에서 Manager는 Worker/Evaluator의 healthcheck를 기다린 후 기동
- Kubernetes 배포 시 `k8s/secrets.yaml`의 LLM_API_KEY를 실제 키로 교체 필요

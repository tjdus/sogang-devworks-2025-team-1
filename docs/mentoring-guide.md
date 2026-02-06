# Self-Healing Agent System - Mentoring Guide

## 개요

이 프로젝트는 **LLM 기반 Self-Healing 마이크로서비스 시스템**이다. AI 에이전트가 코드를 생성하고, 품질을 자동 평가하며, 실패가 누적되면 스스로 프롬프트를 개선하여 성능을 회복하는 구조를 갖추고 있다.

---

## 1. 시스템 아키텍처

```
                    +-----------+
                    |   User    |
                    +-----+-----+
                          |
                          v
                   +------+------+
                   |   Manager   |  :8000
                   | (Gateway &  |
                   |  Refiner)   |
                   +--+------+---+
                      |      |
             +--------+      +--------+
             v                        v
      +------+------+         +------+------+
      |   Worker    |  :8001  |  Evaluator  |  :8002
      | (LLM Code   |         | (Rule 40% + |
      |  Generator)  |         |  LLM 60%)   |
      +------+------+         +------+------+
             |                        |
             v                        v
      +------+------------------------+------+
      |           PostgreSQL                  |
      | prompts | execution_logs | opt_reports|
      +------------------+-------------------+
                         |
                         v
                  +------+------+
                  |  Optimizer  |  (CronJob)
                  | (Failure    |
                  |  Analyzer & |
                  |  Prompt     |
                  |  Patcher)   |
                  +-------------+
```

### 서비스 역할

| 서비스 | 포트 | 역할 |
|--------|------|------|
| **Manager** | 8000 | 사용자 요청 수신, 입력 정제(Refine), Worker/Evaluator 오케스트레이션 |
| **Worker** | 8001 | DB에서 최신 프롬프트 로드 -> LLM으로 코드 생성 (Self-Healing 핵심) |
| **Evaluator** | 8002 | 생성된 코드 품질 평가 (Rule 40% + LLM 60%, 통과 기준: 0.7) |
| **Optimizer** | - | CronJob으로 실행. 실패 로그 분석 -> 프롬프트 자동 개선 |

### Self-Healing 메커니즘

1. Worker가 매 요청마다 DB에서 **활성 프롬프트**를 로드
2. 요청 처리 결과가 Evaluator에 의해 평가되고 DB에 기록
3. 30분 내 3건 이상 실패 시 Optimizer가 자동 트리거
4. Optimizer가 LLM으로 실패 패턴 분석 -> 개선된 프롬프트 생성 -> DB에 저장
5. 다음 요청부터 Worker가 새 프롬프트로 동작 (무중단 자동 복구)

---

## 2. 멘토링 진행 순서

### Phase 1: 개념 이해 (15분)

**설명할 내용:**
- Self-Healing 시스템이란? (장애 자동 감지 + 자동 복구)
- 이 프로젝트에서의 "장애" = 나쁜 프롬프트로 인한 저품질 출력
- 복구 방법 = LLM이 실패 패턴을 분석하고 프롬프트를 개선
- 핵심: Worker가 **매 요청마다 DB에서 프롬프트를 로드** (정적 코드가 아닌 동적 설정)

**질문 유도:**
- "프롬프트가 코드에 하드코딩되어 있으면 어떤 문제가 있을까?"
- "자동 복구가 안 되면 사람이 직접 프롬프트를 고쳐야 하는데, 새벽 3시에 장애가 나면?"

### Phase 2: 코드 구조 파악 (20분)

**핵심 파일 함께 읽기:**

| 순서 | 파일 | 핵심 개념 |
|------|------|----------|
| 1 | `services/common/config.py` | 환경변수로 설정 관리 (Pydantic Settings) |
| 2 | `services/common/models.py` | DB 테이블 구조 (Prompt, ExecutionLog, OptimizationReport) |
| 3 | `services/common/schemas.py` | API 요청/응답 스키마 (Pydantic) |
| 4 | `services/worker/app/services/prompt_loader.py` | **핵심**: DB에서 활성 프롬프트 로드 |
| 5 | `services/worker/app/agents/worker_agent.py` | LangChain 체인 구성 (동적 프롬프트 주입) |
| 6 | `services/evaluator/app/services/scorer.py` | 복합 평가: Rule 40% + LLM 60% |
| 7 | `services/evaluator/app/services/validators.py` | 규칙 기반 검증 (코드 패턴 감지) |
| 8 | `services/optimizer/app/services/log_analyzer.py` | 실패 로그 분석 (임계값 기반 트리거) |
| 9 | `services/optimizer/app/services/prompt_patcher.py` | 프롬프트 패치 (분석 -> 개선 -> DB 저장) |

**강조할 포인트:**
- `prompt_loader.py`: `SELECT ... WHERE is_active = TRUE` 한 줄이 Self-Healing의 핵심
- `scorer.py`: `combined = rule * 0.4 + llm * 0.6` — 가중 합산
- `log_analyzer.py`: `failure_count >= threshold` — 간단하지만 효과적인 트리거 조건

### Phase 3: 빌드 & 기동 실습 (20분)

**멘티가 직접 실행:**

```bash
# 1. 이미지 빌드
docker compose build

# 2. PostgreSQL 기동 + 스키마 확인
docker compose up -d postgres
sleep 10
docker compose exec postgres psql -U agent -d agent_system -c "\dt"
docker compose exec postgres psql -U agent -d agent_system -c "SELECT * FROM prompts;"

# 3. 서비스 기동
docker compose up -d worker evaluator
docker compose up -d manager

# 4. Health Check
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

**확인 사항:**
- 3개 테이블 존재 (prompts, execution_logs, optimization_reports)
- 시드 프롬프트 1건 확인
- 3개 서비스 모두 `{"status":"ok"}` 반환

### Phase 4: E2E 파이프라인 테스트 (15분)

**정상 흐름 테스트:**

```bash
# Manager를 통한 전체 파이프라인
curl -s -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input":"Write a function to sort a list","task_type":"code_generation"}'
```

**확인할 응답 필드:**
- `refined_input`: 입력이 정제되었는가
- `worker_output`: 코드가 생성되었는가
- `evaluation_score`: 점수 (0.7 이상이면 통과)
- `evaluation_passed`: true/false
- `prompt_version`: 몇 번째 프롬프트로 생성했는가

**DB 로그 확인:**
```bash
docker compose exec postgres psql -U agent -d agent_system \
  -c "SELECT request_id, evaluation_score, evaluation_passed FROM execution_logs ORDER BY created_at DESC LIMIT 5;"
```

### Phase 5: Self-Healing 데모 (25분)

**이 부분이 핵심 데모. 멘티에게 "시스템이 스스로 고치는 것"을 직접 보여준다.**

#### Step 1: 나쁜 프롬프트 주입

```bash
docker compose exec postgres psql -U agent -d agent_system -c "
  UPDATE prompts SET is_active = FALSE WHERE task_type = 'code_generation';
  INSERT INTO prompts (task_type, content, version, is_active, change_reason, created_by)
  VALUES ('code_generation', 'just say hello world to everything', 99, TRUE, 'demo: bad prompt', 'mentor');
"
```

#### Step 2: 실패 확인 (5건)

```bash
for i in 1 2 3 4 5; do
  echo "=== Request $i ==="
  curl -s -X POST http://localhost:8000/api/v1/request \
    -H "Content-Type: application/json" \
    -d '{"user_input":"Write a binary search function","task_type":"code_generation"}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Score={d[\"evaluation_score\"]}, Passed={d[\"evaluation_passed\"]}, Output={d[\"worker_output\"][:50]}')"
  sleep 1
done
```

**기대 결과:** Score ~0.36, Passed=False, Output="Hello World"

#### Step 3: Optimizer 실행

```bash
docker compose run --rm optimizer
```

**로그에서 확인할 키워드:**
- `optimization_cycle_started` — 사이클 시작
- `task_types_needing_optimization` — 최적화 필요 태스크 감지
- `prompt_patched` — 프롬프트 교체 완료
- `optimization_completed` — 완료

#### Step 4: 개선 확인

```bash
# 새 프롬프트 확인
docker compose exec postgres psql -U agent -d agent_system \
  -c "SELECT version, is_active, LEFT(content, 80) FROM prompts WHERE task_type='code_generation' ORDER BY version DESC LIMIT 3;"

# 동일 요청 재실행
curl -s -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input":"Write a binary search function","task_type":"code_generation"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Score={d[\"evaluation_score\"]}, Passed={d[\"evaluation_passed\"]}')"
```

**기대 결과:** Score ~0.874, Passed=True

**데모 핵심 멘트:**
> "코드를 한 줄도 안 고쳤는데, 시스템이 스스로 문제를 파악하고 프롬프트를 개선해서 성능이 회복되었다."

### Phase 6: 메트릭 & 모니터링 확인 (10분)

```bash
# Prometheus 메트릭 확인
curl -s http://localhost:8000/metrics/ | grep "agent_requests_total"
curl -s http://localhost:8001/metrics/ | grep "agent_prompt_version"
curl -s http://localhost:8002/metrics/ | grep "agent_evaluation_score"
```

**설명할 메트릭:**
| 메트릭 | 의미 |
|--------|------|
| `agent_requests_total` | 서비스별 총 요청 수 (success/error) |
| `agent_evaluation_score` | 평가 점수 분포 (히스토그램) |
| `agent_prompt_version` | 현재 활성 프롬프트 버전 |
| `agent_request_duration_seconds` | 요청 처리 시간 |

---

## 3. 멘티 과제 & 검증 방법

### 과제 요구사항

멘티는 동일한 아키텍처의 Self-Healing 시스템을 구현해야 한다:

1. **4개 서비스** 구현 (Manager, Worker, Evaluator, Optimizer)
2. **Docker Compose**로 빌드 & 실행 가능
3. **동일 API 스펙** 준수 (아래 참조)
4. **Self-Healing 동작**: 나쁜 프롬프트 주입 -> 실패 축적 -> 자동 복구
5. **Prometheus 메트릭** 노출

### API 스펙 (필수 준수)

```
POST /api/v1/request   (Manager)
  Request:  {"user_input": string, "task_type": string}
  Response: {"request_id": uuid, "refined_input": string, "worker_output": string,
             "evaluation_score": float, "evaluation_passed": bool, "prompt_version": int}

POST /api/v1/task      (Worker)
  Request:  {"request_id": uuid, "task_type": string, "refined_input": string}
  Response: {"request_id": uuid, "output": string, "prompt_version": int, "latency_ms": int}

POST /api/v1/evaluate  (Evaluator)
  Request:  {"request_id": uuid, "task_type": string, "user_input": string,
             "refined_input": string, "worker_output": string}
  Response: {"request_id": uuid, "score": float, "passed": bool, "detail": object}

GET /health            (All services)
  Response: {"status": "ok", "service": string, "version": string}

GET /metrics/          (All services)
  Response: Prometheus text format
```

### DB 스키마 (필수 준수)

```sql
-- prompts 테이블
CREATE TABLE prompts (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    change_reason TEXT,
    created_by VARCHAR(64) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- execution_logs 테이블
CREATE TABLE execution_logs (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    task_type VARCHAR(64) NOT NULL,
    user_input TEXT NOT NULL,
    refined_input TEXT,
    prompt_version INTEGER,
    worker_output TEXT,
    worker_latency_ms INTEGER,
    evaluation_score FLOAT,
    evaluation_passed BOOLEAN,
    evaluation_detail JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- optimization_reports 테이블
CREATE TABLE optimization_reports (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(64) NOT NULL,
    before_prompt_version INTEGER NOT NULL,
    before_prompt_content TEXT NOT NULL,
    after_prompt_version INTEGER NOT NULL,
    after_prompt_content TEXT NOT NULL,
    failure_analysis JSONB,
    improvement_pct FLOAT,
    triggered_by VARCHAR(64) NOT NULL DEFAULT 'cronjob',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 시드 프롬프트
INSERT INTO prompts (task_type, content, version, is_active, change_reason, created_by)
VALUES ('code_generation', 'You are a Python code generator...', 1, TRUE, 'Initial seed prompt', 'system');
```

### 자동 벤치마크 검증

멘티 시스템에 대해 동일한 벤치마크를 실행하여 점수를 산출한다:

```bash
# 멘티 시스템이 docker compose up -d 로 가동된 상태에서:
python scripts/benchmark.py \
  --manager-url http://localhost:8000 \
  --worker-url http://localhost:8001 \
  --evaluator-url http://localhost:8002 \
  --db-host localhost --db-port 5432 \
  --cycles 2 --requests 5 \
  --output-dir reports
```

**벤치마크가 하는 일:**
1. 서비스 Health 체크 (3개 모두 정상?)
2. DB 초기화 (시드 프롬프트만 남김)
3. 2회 Self-Healing 사이클 실행:
   - 나쁜 프롬프트 주입 -> 5개 요청 (실패 확인) -> Optimizer 실행 -> 5개 요청 (개선 확인)
4. Prometheus 메트릭 확인
5. 멘티 점수 산출 + 리포트 생성

---

## 4. 평가 기준 (100점 만점)

### 6차원 평가 체계

| 차원 | 비중 | 측정 내용 | 만점 조건 |
|------|------|----------|----------|
| **E2E 파이프라인** | 20점 | 서비스 기동 + 전체 흐름 동작 | 3개 서비스 정상, E2E 요청 성공, 에러 없음 |
| **평가 품질** | 15점 | Evaluator가 좋고 나쁨을 구별하는가 | Bad output < 0.5점, Good output >= 0.7점 |
| **Self-Healing 효과** | **30점** | 최적화가 실제로 개선하는가 | Optimizer 실행 성공 + 새 버전 생성 + 점수/통과율 향상 |
| **성능** | 10점 | 응답 시간 | 평균 500ms 이내 |
| **에러 처리** | 10점 | 오류 시 graceful 처리 | HTTP 에러가 JSON으로 반환, crash 없음 |
| **관측성** | 15점 | Prometheus 메트릭 | /metrics 엔드포인트 + 핵심 3개 메트릭 노출 |

### 등급

| 등급 | 점수 | 의미 |
|------|------|------|
| **A** | 90-100 | 전 기능 완벽 동작, Self-Healing 검증됨 |
| **B** | 80-89 | 대부분 동작, 일부 미세 이슈 |
| **C** | 70-79 | 기본 기능은 동작, Self-Healing 부분 동작 |
| **D** | 60-69 | E2E는 되지만 Self-Healing 미흡 |
| **F** | 0-59 | 기본 파이프라인 미동작 |

### 핵심 감점 요소

- 서비스가 아예 기동되지 않음: E2E 0점 (전체 -20점)
- Optimizer가 프롬프트를 교체하지 못함: Self-Healing 0점 (전체 -30점)
- 점수가 개선되지 않음 (before == after): Self-Healing 부분 감점
- /metrics 엔드포인트 없음: 관측성 0점 (-15점)
- 모든 요청이 에러: E2E + 에러처리 동시 감점

---

## 5. 트러블슈팅 가이드

멘티가 자주 겪는 문제와 해결법:

### 빌드 실패

| 증상 | 원인 | 해결 |
|------|------|------|
| `ModuleNotFoundError: services.common` | `services/__init__.py` 누락 | Dockerfile에 `COPY services/__init__.py` 추가 |
| `pip install` 실패 | requirements.txt 경로 오류 | Dockerfile의 COPY 경로 확인 |
| 이미지 빌드는 되지만 실행 시 import 에러 | 하위 패키지 `__init__.py` 누락 | 모든 디렉토리에 `__init__.py` 확인 |

### 기동 실패

| 증상 | 원인 | 해결 |
|------|------|------|
| Manager 기동 시 connection refused | Worker/Evaluator 미기동 | depends_on + healthcheck 설정 |
| DB 연결 실패 | PostgreSQL 미기동 또는 URL 오류 | `docker compose logs postgres` 확인 |
| LLM 호출 에러 | API 키 누락 | `.env` 파일에 `LLM_API_KEY` 설정 또는 mock 모드 구현 |

### Self-Healing 미동작

| 증상 | 원인 | 해결 |
|------|------|------|
| Optimizer가 "no task types need optimization" | 실패 3건 미만 또는 30분 초과 | `OPTIMIZER_LOOKBACK_MINUTES` 확인, 충분한 실패 축적 |
| 새 프롬프트가 생성되지만 점수 안 변함 | Worker가 DB에서 프롬프트를 로드하지 않음 | `load_active_prompt()` 매 요청 호출 확인 |
| evaluation_passed가 항상 True | Evaluator 평가 로직 오류 | `scorer.py`의 threshold 및 가중치 확인 |

---

## 6. 참고 명령어 모음

```bash
# === 빌드 ===
docker compose build                     # 전체 빌드
docker compose build worker              # Worker만 리빌드

# === 기동/중지 ===
docker compose up -d                     # 전체 기동
docker compose down                      # 전체 중지
docker compose down -v                   # 전체 중지 + 볼륨 삭제 (DB 초기화)
docker compose up -d worker              # Worker만 재시작

# === 로그 ===
docker compose logs manager --tail 30    # Manager 로그
docker compose logs worker -f            # Worker 실시간 로그

# === DB 접속 ===
docker compose exec postgres psql -U agent -d agent_system
# 테이블 목록: \dt
# 프롬프트 확인: SELECT version, is_active, LEFT(content, 80) FROM prompts ORDER BY version;
# 실행 로그: SELECT evaluation_score, evaluation_passed FROM execution_logs ORDER BY created_at DESC LIMIT 10;

# === Optimizer ===
docker compose run --rm optimizer        # 수동 실행

# === 벤치마크 ===
python scripts/benchmark.py --cycles 2 --requests 5

# === 전체 초기화 ===
docker compose down -v && docker compose up -d
```

---

## 7. 멘토링 타임라인 (총 ~2시간)

| 시간 | 내용 | 방식 |
|------|------|------|
| 0:00-0:15 | 개념 설명 (Self-Healing, 아키텍처) | 강의 |
| 0:15-0:35 | 코드 구조 핵심 파일 읽기 | 코드 리뷰 |
| 0:35-0:55 | 빌드 & 기동 실습 | 멘티 실습 |
| 0:55-1:10 | E2E 파이프라인 테스트 | 멘티 실습 |
| 1:10-1:35 | Self-Healing 데모 (하이라이트) | 라이브 데모 |
| 1:35-1:45 | 메트릭 & 모니터링 | 시연 |
| 1:45-2:00 | 과제 안내 + Q&A | 토론 |

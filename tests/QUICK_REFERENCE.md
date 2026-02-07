# 테스트 샘플 빠른 참조

## 📋 cURL 명령어로 바로 테스트하기

### ✅ Easy Samples

```bash
# 1. 두 숫자 더하기
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Write a function to add two numbers", "task_type": "code_generation"}'

# 2. Hello World
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Create a Python function that returns Hello World", "task_type": "code_generation"}'

# 3. 짝수 확인
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Write a function to check if a number is even", "task_type": "code_generation"}'
```

### 🟡 Medium Samples

```bash
# 1. 이진 탐색
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Implement a binary search algorithm in Python", "task_type": "code_generation"}'

# 2. JWT 인증 API
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Create a REST API endpoint for user authentication with JWT tokens", "task_type": "code_generation"}'

# 3. 이메일 검증
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Write a function to validate email addresses using regex", "task_type": "code_generation"}'

# 4. LRU 캐시
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Implement a LRU cache with get and put operations in O(1) time", "task_type": "code_generation"}'
```

### 🔴 Hard Samples

```bash
# 1. 분산 태스크 큐
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Build a distributed task queue system with worker pools, priority queues, and failure retry mechanism. Include health monitoring and graceful shutdown.", "task_type": "code_generation"}'

# 2. 멀티스레드 웹 스크래퍼
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Implement a multi-threaded web scraper that respects robots.txt, handles rate limiting, supports proxy rotation, and stores results in a database with connection pooling", "task_type": "code_generation"}'

# 3. 실시간 협업 에디터
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Create a real-time collaborative text editor backend with operational transformation, conflict resolution, and WebSocket communication", "task_type": "code_generation"}'
```

### 🟣 Very Hard Samples

```bash
# 1. 분산 트랜잭션 코디네이터
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Design and implement a distributed transaction coordinator using two-phase commit protocol with timeout handling, deadlock detection, and automatic rollback. Support both ACID and eventual consistency modes.", "task_type": "code_generation"}'

# 2. 자체 최적화 쿼리 플래너
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Build a self-optimizing database query planner that analyzes query patterns, maintains statistics, generates execution plans with cost estimation, and dynamically creates indexes based on workload", "task_type": "code_generation"}'
```

### ⚠️ Edge Cases (엣지 케이스)

```bash
# 1. 모호한 요청 (한국어)
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "코드 만들어줘", "task_type": "code_generation"}'

# 2. 문맥 없음
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Make it work", "task_type": "code_generation"}'

# 3. 매우 애매모호
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Write Python code that does the thing with the stuff and makes it go fast using that algorithm everyone uses", "task_type": "code_generation"}'

# 4. 모순된 요구사항
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Create a function that takes a list and returns a dict but also maybe a tuple depending on the input unless it is empty then return None or maybe an empty list", "task_type": "code_generation"}'
```

### 💥 Stress Test (스트레스 테스트)

```bash
# 1. 마이크로서비스 전체 아키텍처
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Implement a production-ready microservices architecture with API gateway, service discovery, circuit breaker, distributed tracing, centralized logging, metrics collection, auto-scaling, health checks, blue-green deployment support, and comprehensive error handling. Include authentication, authorization, rate limiting, caching, database connection pooling, message queuing, event sourcing, CQRS pattern, saga pattern for distributed transactions, and full OpenAPI documentation with examples.", "task_type": "code_generation"}'

# 2. ML 파이프라인
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Build a machine learning pipeline that ingests real-time streaming data from Kafka, performs feature engineering with PySpark, trains multiple models in parallel (XGBoost, LightGBM, Neural Network), does hyperparameter tuning with Optuna, validates with cross-validation, deploys the best model to production with A/B testing, monitors model drift, retrains automatically when performance degrades, and provides explainability with SHAP values", "task_type": "code_generation"}'
```

### 🔒 Security Test (보안)

```bash
# 1. 안전한 비밀번호 재설정
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Create a secure password reset flow with email verification, rate limiting, and protection against timing attacks", "task_type": "code_generation"}'

# 2. 안전한 파일 업로드
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Implement a file upload handler that prevents directory traversal, validates file types, limits file size, scans for malware, and stores files securely", "task_type": "code_generation"}'
```

### ⚡ Performance Test (성능)

```bash
# 1. 고성능 JSON 파서
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Write a high-performance JSON parser that can handle 1GB+ files with streaming, minimal memory footprint, and support for JSONPath queries", "task_type": "code_generation"}'

# 2. Lock-free 큐
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Implement a lock-free thread-safe queue that supports multiple producers and consumers with minimal contention", "task_type": "code_generation"}'
```

### 🔗 Integration Test (통합)

```bash
# 1. 결제 게이트웨이
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Build a payment gateway integration that supports Stripe, PayPal, and Square with automatic failover, transaction logging, webhook handling, and reconciliation", "task_type": "code_generation"}'

# 2. ETL 파이프라인
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Create an ETL pipeline that extracts data from MySQL, PostgreSQL, and MongoDB, transforms it according to business rules, and loads it into a data warehouse with incremental updates and error recovery", "task_type": "code_generation"}'
```

## 📊 결과 확인

### 1. 응답 확인
각 요청의 응답에서 다음 정보를 확인할 수 있습니다:
- `evaluation_score`: 평가 점수 (0-1)
- `evaluation_passed`: 합격 여부 (true/false)
- `prompt_version`: 사용된 프롬프트 버전
- `worker_output`: 생성된 코드

### 2. 대시보드 확인
http://localhost:3000 에서 실시간 지표 확인:
- 평균 평가 점수
- 합격/불합격 추이
- 난이도별 성능
- 최근 실행 로그

### 3. API로 통계 조회
```bash
# 전체 요약
curl http://localhost:8002/api/v1/stats/summary?hours=1

# 최근 실패 케이스
curl http://localhost:8002/api/v1/stats/recent-failures?limit=10

# 프롬프트 버전별 성능
curl http://localhost:8002/api/v1/stats/prompt-performance?hours=24
```

## 🎯 권장 테스트 순서

1. **Easy 샘플**로 시작 → 시스템이 정상 동작하는지 확인
2. **Medium 샘플**로 중간 난이도 테스트
3. **Hard 샘플**로 프롬프트 최적화 필요성 확인
4. **Edge Cases**로 견고성 테스트
5. **Stress Test**로 한계 테스트
6. Optimizer 실행 후 재테스트하여 개선 확인

## 💡 팁

- jq 설치: `brew install jq` (JSON 응답을 예쁘게 보기)
- 결과를 파일로 저장: `curl ... | jq '.' > result.json`
- 여러 요청 자동화: `scripts/test_comprehensive.py` 사용


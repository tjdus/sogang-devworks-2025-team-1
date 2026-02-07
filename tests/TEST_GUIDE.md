# 멀티 에이전트 시스템 테스트 가이드

## 📝 테스트 샘플 개요

`tests/test_samples.json` 파일에는 다양한 난이도와 유형의 테스트 케이스가 포함되어 있습니다.

## 🎯 샘플 카테고리

### 1. Easy Samples (쉬움)
기본적인 함수 작성 요청
- 두 숫자 더하기
- Hello World 함수
- 짝수 확인

**예상 결과**: 높은 합격률 (90%+)

### 2. Medium Samples (중간)
알고리즘 및 웹 개발 작업
- 이진 탐색 구현
- JWT 인증 API
- 이메일 검증
- LRU 캐시 구현

**예상 결과**: 중간 합격률 (60-80%)

### 3. Hard Samples (어려움)
복잡한 시스템 설계
- 분산 태스크 큐
- 멀티스레드 웹 스크래퍼
- 실시간 협업 에디터

**예상 결과**: 낮은 합격률 (40-60%)

### 4. Very Hard Samples (매우 어려움)
고급 분산 시스템
- 분산 트랜잭션 코디네이터
- 자체 최적화 쿼리 플래너

**예상 결과**: 매우 낮은 합격률 (20-40%)

### 5. Edge Cases and Ambiguous (엣지 케이스)
모호하거나 문제가 있는 요청
- 빈 입력
- 모호한 지시사항
- 모순된 요구사항

**목적**: 프롬프트의 견고성 테스트

### 6. Stress Test Samples (스트레스 테스트)
극단적으로 복잡한 요구사항
- 마이크로서비스 전체 아키텍처
- 완전한 ML 파이프라인

**목적**: 프롬프트의 한계 테스트

### 7. Security and Best Practices (보안)
보안 요구사항이 포함된 작업
- 안전한 비밀번호 재설정
- 안전한 파일 업로드

**목적**: 보안 베스트 프랙티스 검증

### 8. Performance Critical (성능 중요)
성능이 중요한 작업
- 고성능 JSON 파서
- Lock-free 큐

**목적**: 성능 최적화 코드 생성 검증

### 9. Integration Challenges (통합)
여러 시스템 통합 작업
- 결제 게이트웨이 통합
- ETL 파이프라인

**목적**: 통합 코드 품질 검증

## 🚀 사용 방법

### 1. 기본 테스트
```bash
# 모든 카테고리 테스트
python scripts/test_comprehensive.py

# 특정 카테고리만 테스트
python scripts/test_comprehensive.py --categories easy_samples medium_samples

# 결과를 파일로 저장
python scripts/test_comprehensive.py --output results/test_results.json

# 요청 간 지연 시간 조정 (초)
python scripts/test_comprehensive.py --delay 2.0
```

### 2. cURL로 개별 테스트
```bash
# Easy 예제
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Write a function to add two numbers",
    "task_type": "code_generation"
  }'

# Medium 예제
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Implement a binary search algorithm in Python",
    "task_type": "code_generation"
  }'

# Hard 예제
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Build a distributed task queue system with worker pools, priority queues, and failure retry mechanism",
    "task_type": "code_generation"
  }'
```

### 3. Python으로 직접 테스트
```python
import httpx
import asyncio

async def test_request():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/request",
            json={
                "user_input": "Write a function to calculate fibonacci numbers",
                "task_type": "code_generation"
            }
        )
        result = response.json()
        print(f"Score: {result['evaluation_score']:.3f}")
        print(f"Passed: {result['evaluation_passed']}")
        print(f"Output: {result['worker_output'][:200]}...")

asyncio.run(test_request())
```

## 📊 예상 결과 분석

### 초기 프롬프트 (버전 1)
- Easy: 85-95% 합격률
- Medium: 50-70% 합격률
- Hard: 30-50% 합격률
- Very Hard: 10-30% 합격률

### 최적화 후 (버전 2+)
- Easy: 95-100% 합격률
- Medium: 70-90% 합격률
- Hard: 50-70% 합격률
- Very Hard: 30-50% 합격률

## 🔍 테스트 시나리오

### 시나리오 1: 점진적 난이도 증가
```bash
# 1단계: Easy 샘플로 시작
python scripts/test_comprehensive.py --categories easy_samples

# 2단계: Medium 추가
python scripts/test_comprehensive.py --categories easy_samples medium_samples

# 3단계: Hard 추가
python scripts/test_comprehensive.py --categories easy_samples medium_samples hard_samples
```

### 시나리오 2: 실패 케이스 집중 테스트
```bash
# 어려운 샘플만 테스트하여 프롬프트 최적화 트리거
python scripts/test_comprehensive.py --categories hard_samples very_hard_samples stress_test_samples
```

### 시나리오 3: 엣지 케이스 테스트
```bash
# 시스템의 견고성 검증
python scripts/test_comprehensive.py --categories edge_cases_and_ambiguous
```

## 📈 대시보드에서 결과 확인

테스트 실행 후 Grafana 대시보드에서 다음을 확인할 수 있습니다:

1. **평균 평가 점수 변화**
   - 시간에 따른 점수 추이
   - 난이도별 점수 차이

2. **합격/불합격 비율**
   - 카테고리별 성공률
   - 실패 패턴 분석

3. **프롬프트 버전 성능**
   - 버전별 성능 비교
   - 최적화 효과 측정

4. **최근 실행 로그**
   - 개별 요청 상세 정보
   - 실패 케이스 분석

## 🛠️ 프롬프트 최적화 워크플로우

1. **초기 테스트 실행**
   ```bash
   python scripts/test_comprehensive.py --output results/baseline.json
   ```

2. **실패 케이스 분석**
   - Grafana 대시보드에서 실패 케이스 확인
   - API로 상세 정보 조회:
     ```bash
     curl http://localhost:8002/api/v1/stats/recent-failures?limit=20
     ```

3. **Optimizer 트리거**
   ```bash
   # 수동 트리거
   docker compose run --rm optimizer
   
   # 또는 자동 트리거 대기 (CronJob)
   ```

4. **재테스트**
   ```bash
   python scripts/test_comprehensive.py --output results/optimized.json
   ```

5. **결과 비교**
   - 대시보드에서 프롬프트 버전별 성능 비교
   - JSON 결과 파일 비교

## 💡 테스트 팁

### 1. 점진적 테스트
처음부터 모든 카테고리를 테스트하지 말고, 쉬운 것부터 시작하여 점진적으로 난이도를 높입니다.

### 2. 충분한 샘플 수
각 카테고리당 최소 3-5개 이상의 요청을 보내야 통계적으로 의미 있는 결과를 얻을 수 있습니다.

### 3. 속도 조절
`--delay` 옵션을 사용하여 요청 간 간격을 조정합니다. 너무 빠르면 시스템에 과부하가 걸릴 수 있습니다.

### 4. 결과 저장
`--output` 옵션으로 결과를 저장하면 나중에 비교 분석이 가능합니다.

### 5. 로그 모니터링
테스트 중에 서비스 로그를 확인하면 문제를 빠르게 파악할 수 있습니다:
```bash
docker compose logs -f manager worker evaluator
```

## 🎯 성공 기준

### 최소 요구사항
- Easy 샘플: 90% 이상 합격률
- Medium 샘플: 70% 이상 합격률
- 전체 평균 점수: 0.75 이상

### 우수 기준
- Easy 샘플: 95% 이상 합격률
- Medium 샘플: 85% 이상 합격률
- Hard 샘플: 60% 이상 합격률
- 전체 평균 점수: 0.80 이상

### 탁월 기준
- Easy 샘플: 100% 합격률
- Medium 샘플: 90% 이상 합격률
- Hard 샘플: 75% 이상 합격률
- Very Hard 샘플: 50% 이상 합격률
- 전체 평균 점수: 0.85 이상

## 📚 관련 문서

- [Dashboard Guide](../docs/dashboard-guide.md) - 대시보드 사용법
- [Self-Healing Report](../docs/self-healing-report.md) - 최적화 메커니즘
- [README.md](../README.md) - 프로젝트 전체 가이드


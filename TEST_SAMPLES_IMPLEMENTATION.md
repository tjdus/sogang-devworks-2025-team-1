# 🧪 테스트 샘플 구현 완료

## 📦 생성된 파일

### 1. 테스트 샘플 데이터
**파일**: `tests/test_samples.json`

9개 카테고리, 총 40+ 개의 테스트 샘플:
- ✅ Easy Samples (3개) - 기본 함수 작성
- 🟡 Medium Samples (4개) - 알고리즘, API 개발
- 🔴 Hard Samples (3개) - 복잡한 시스템 설계
- 🟣 Very Hard Samples (2개) - 분산 시스템
- ⚠️ Edge Cases (4개) - 모호하거나 문제가 있는 입력
- 💥 Stress Test (2개) - 극단적으로 복잡한 요구사항
- 🔒 Security Test (2개) - 보안 베스트 프랙티스
- ⚡ Performance Test (2개) - 성능 최적화
- 🔗 Integration Test (2개) - 시스템 통합

### 2. 종합 테스트 스크립트
**파일**: `scripts/test_comprehensive.py`

**기능**:
- 모든 카테고리 자동 테스트
- 실시간 진행 상황 표시 (Rich Progress Bar)
- 카테고리별 / 난이도별 통계
- JSON 결과 저장
- 컬러풀한 테이블 출력

**사용법**:
```bash
# 모든 샘플 테스트
python scripts/test_comprehensive.py

# 특정 카테고리만
python scripts/test_comprehensive.py --categories easy_samples medium_samples

# 결과 저장
python scripts/test_comprehensive.py --output results/test.json
```

### 3. 빠른 테스트 스크립트
**파일**: `scripts/quick-test.sh`

**기능**:
- 서비스 헬스 체크
- Easy/Medium/Hard 각 1개씩 빠른 테스트
- 평가 통계 자동 조회
- Bash 스크립트로 간단하게 실행

**사용법**:
```bash
./scripts/quick-test.sh
```

### 4. 테스트 가이드 문서
**파일**: `tests/TEST_GUIDE.md`

**내용**:
- 각 카테고리 상세 설명
- 예상 합격률
- 테스트 시나리오
- 프롬프트 최적화 워크플로우
- 성공 기준
- 문제 해결 팁

### 5. 빠른 참조 가이드
**파일**: `tests/QUICK_REFERENCE.md`

**내용**:
- 모든 샘플의 cURL 명령어
- 바로 복사해서 사용 가능
- 카테고리별 분류
- 결과 확인 방법

### 6. 업데이트된 README
**파일**: `README.md`

- Quick Links 섹션 추가
- Testing 섹션 추가
- 테스트 가이드 링크

## 🎯 테스트 샘플 특징

### 난이도 구성
- **Easy (3개)**: 단순 함수 → 90%+ 합격률 예상
- **Medium (4개)**: 알고리즘, API → 60-80% 합격률 예상
- **Hard (3개)**: 복잡한 시스템 → 40-60% 합격률 예상
- **Very Hard (2개)**: 분산 시스템 → 20-40% 합격률 예상

### 특수 케이스
- **Edge Cases**: 모호한 입력으로 견고성 테스트
- **Stress Test**: 극단적 요구사항으로 한계 테스트
- **Security**: 보안 베스트 프랙티스 검증
- **Performance**: 성능 최적화 코드 생성 검증
- **Integration**: 다중 시스템 통합 검증

## 🚀 사용 예시

### 1. 빠른 동작 확인
```bash
# 3개 샘플로 빠른 테스트 (Easy, Medium, Hard)
./scripts/quick-test.sh
```

**출력 예시**:
```
🧪 Quick Test Script for Multi-Agent System
===========================================

1️⃣ Checking service health...
✅ Manager: {"status": "ok"}
✅ Evaluator: {"status": "ok"}

2️⃣ Testing EASY sample...
✅ EASY test PASSED (score: 0.892)

3️⃣ Testing MEDIUM sample...
✅ MEDIUM test PASSED (score: 0.753)

4️⃣ Testing HARD sample...
❌ HARD test FAILED (score: 0.634)

5️⃣ Fetching evaluation statistics...
{
  "total_count": 3,
  "pass_count": 2,
  "fail_count": 1,
  "pass_rate": 0.6667,
  "avg_score": 0.7597
}
```

### 2. 종합 테스트
```bash
# 모든 카테고리 테스트
python scripts/test_comprehensive.py --output results/baseline.json

# Optimizer 실행
docker compose run --rm optimizer

# 재테스트
python scripts/test_comprehensive.py --output results/optimized.json
```

**출력 예시**:
```
Loading test samples from tests/test_samples.json...
Loaded 9 categories

Testing easy_samples...
  [1/3] ✓ Score: 0.945 (easy) - Write a function to add two numbers
  [2/3] ✓ Score: 0.923 (easy) - Create a Python function that returns...
  [3/3] ✓ Score: 0.912 (easy) - Write a function to check if a number...

Testing medium_samples...
  [1/4] ✓ Score: 0.834 (medium) - Implement a binary search algorithm...
  [2/4] ✓ Score: 0.756 (medium) - Create a REST API endpoint for user...
  [3/4] ✗ Score: 0.623 (medium) - Write a function to validate email...
  [4/4] ✓ Score: 0.789 (medium) - Implement a LRU cache with get and...

Test Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Requests: 7
Successful: 7 (100.0%)
Passed Evaluation: 6 (85.7%)

Results by Category
┏━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Category      ┃ Total ┃ Success ┃ Passed ┃ Avg Score ┃ Pass Rate ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━┩
│ easy_samples  │     3 │       3 │      3 │     0.927 │   100.0%  │
│ medium_samples│     4 │       4 │      3 │     0.751 │    75.0%  │
└───────────────┴───────┴─────────┴────────┴───────────┴───────────┘
```

### 3. 특정 난이도만 테스트
```bash
# Hard 샘플만 테스트 (프롬프트 최적화 트리거용)
python scripts/test_comprehensive.py \
  --categories hard_samples very_hard_samples \
  --delay 2.0
```

### 4. cURL로 개별 테스트
```bash
# Easy
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Write a function to add two numbers", "task_type": "code_generation"}' \
  | jq '{score: .evaluation_score, passed: .evaluation_passed}'

# Hard
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Build a distributed task queue system with worker pools", "task_type": "code_generation"}' \
  | jq '{score: .evaluation_score, passed: .evaluation_passed}'
```

## 📊 예상 결과

### 초기 프롬프트 (버전 1)
| 카테고리 | 합격률 | 평균 점수 |
|---------|-------|----------|
| Easy | 90-95% | 0.85-0.95 |
| Medium | 50-70% | 0.60-0.75 |
| Hard | 30-50% | 0.50-0.65 |
| Very Hard | 10-30% | 0.40-0.55 |

### 최적화 후 (버전 2+)
| 카테고리 | 합격률 | 평균 점수 |
|---------|-------|----------|
| Easy | 95-100% | 0.90-1.00 |
| Medium | 70-90% | 0.75-0.85 |
| Hard | 50-70% | 0.65-0.80 |
| Very Hard | 30-50% | 0.55-0.70 |

## 🎓 테스트 시나리오

### 시나리오 1: 기본 검증
```bash
# 목표: 시스템이 기본적으로 동작하는지 확인
./scripts/quick-test.sh
```

### 시나리오 2: 점진적 난이도 증가
```bash
# 1단계
python scripts/test_comprehensive.py --categories easy_samples

# 2단계
python scripts/test_comprehensive.py --categories easy_samples medium_samples

# 3단계
python scripts/test_comprehensive.py --categories easy_samples medium_samples hard_samples
```

### 시나리오 3: 프롬프트 최적화 검증
```bash
# 1. 초기 성능 측정
python scripts/test_comprehensive.py --output results/before.json

# 2. 어려운 샘플로 실패 유도
python scripts/test_comprehensive.py --categories hard_samples very_hard_samples

# 3. Optimizer 실행
docker compose run --rm optimizer

# 4. 개선 확인
python scripts/test_comprehensive.py --output results/after.json
```

### 시나리오 4: 엣지 케이스 검증
```bash
# 시스템의 견고성 확인
python scripts/test_comprehensive.py --categories edge_cases_and_ambiguous
```

## 📈 대시보드에서 확인

테스트 후 Grafana 대시보드(http://localhost:3000)에서:

1. **평균 평가 점수** 변화 추이
2. **합격/불합격 비율** 
3. **난이도별 성능** (Task Type 필터 사용)
4. **최근 실행 로그** (개별 요청 상세)
5. **실패 케이스 분석**
6. **프롬프트 버전별 성능 비교**

## 💡 활용 팁

### 1. 지속적 테스트
```bash
# cron으로 주기적 테스트 설정
0 */6 * * * cd /path/to/project && python scripts/test_comprehensive.py --output results/$(date +\%Y\%m\%d_\%H\%M).json
```

### 2. CI/CD 통합
```yaml
# .github/workflows/test.yml
- name: Run comprehensive test
  run: |
    python scripts/test_comprehensive.py --categories easy_samples medium_samples
    # 합격률이 80% 미만이면 실패
```

### 3. 성능 비교
```bash
# 버전별 결과 비교
diff <(jq '.summary' results/v1.json) <(jq '.summary' results/v2.json)
```

## 🎉 완료!

다양한 난이도의 테스트 샘플과 자동화 스크립트가 준비되었습니다!

- **40+ 테스트 샘플** (9개 카테고리)
- **2개 자동화 스크립트** (종합 테스트, 빠른 테스트)
- **3개 문서** (가이드, 빠른 참조, 이 요약)
- **cURL 명령어** (바로 복사하여 사용 가능)

프롬프트 최적화의 효과를 정량적으로 측정하고 검증할 수 있습니다! 🚀


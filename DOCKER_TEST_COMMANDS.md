# Docker에서 Python 테스트 실행 - 코드 모음

## 1. Bash 스크립트 (scripts/run-docker-tests.sh)

```bash
#!/bin/bash

# Docker Compose 실행 중인 컨테이너에서 테스트
docker compose exec manager python scripts/test_comprehensive.py \
  --categories easy_samples medium_samples \
  --manager-url http://manager:8000

# 새 컨테이너로 테스트 (일회성)
docker compose run --rm manager python scripts/test_comprehensive.py

# 빠른 테스트
docker compose run --rm manager bash scripts/quick-test.sh

# 결과를 파일로 저장
docker compose run --rm manager python scripts/test_comprehensive.py \
  --output /app/results/test_$(date +%Y%m%d_%H%M%S).json
```

## 2. Docker Compose 테스트 설정 (docker-compose.test.yml)

```yaml
version: '3.8'

services:
  test-runner:
    build:
      context: .
      dockerfile: services/manager/Dockerfile
    volumes:
      - ./scripts:/app/scripts
      - ./tests:/app/tests
      - ./results:/app/results
    depends_on:
      - manager
      - worker
      - evaluator
    command: |
      python /app/scripts/test_comprehensive.py \
        --manager-url http://manager:8000 \
        --categories easy_samples medium_samples
```

**실행:**
```bash
docker compose -f docker-compose.test.yml up
```

## 3. Python 스크립트 (scripts/run_docker_tests.py)

```python
import subprocess

def run_in_docker(service: str, command: list[str]):
    docker_cmd = ["docker", "compose", "exec", service] + command
    subprocess.run(docker_cmd)

# 실행
run_in_docker("manager", [
    "python", "scripts/test_comprehensive.py",
    "--categories", "easy_samples"
])
```

## 4. Makefile 타겟

```makefile
# Makefile에 추가
test-docker:
	docker compose exec manager python scripts/test_comprehensive.py

test-docker-all:
	docker compose run --rm manager python scripts/test_comprehensive.py --categories easy_samples medium_samples hard_samples
```

**실행:**
```bash
make test-docker
```

## 5. 직접 명령어

```bash
# 실행 중인 컨테이너에서
docker compose exec manager python scripts/test_comprehensive.py

# 새 컨테이너로
docker compose run --rm manager python scripts/test_comprehensive.py

# 특정 카테고리만
docker compose exec manager python scripts/test_comprehensive.py --categories easy_samples

# 결과 저장
docker compose exec manager python scripts/test_comprehensive.py --output /app/results/test.json

# 컨테이너 내부로 들어가서
docker compose exec manager bash
python scripts/test_comprehensive.py
```

## 6. cURL로 직접 테스트

```bash
# 컨테이너 내부에서
docker compose exec manager curl -X POST http://manager:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Write a function to add two numbers", "task_type": "code_generation"}'

# 호스트에서
curl -X POST http://localhost:8000/api/v1/request \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Write a function to add two numbers", "task_type": "code_generation"}'
```

## 7. Python 인터랙티브

```bash
docker compose exec manager python
```

```python
import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        r = await client.post(
            'http://manager:8000/api/v1/request',
            json={'user_input': 'Write a function to add two numbers', 'task_type': 'code_generation'}
        )
        print(r.json())

asyncio.run(test())
```

## 8. 모든 서비스에서 테스트

```bash
# Manager에서
docker compose exec manager python scripts/test_comprehensive.py --manager-url http://manager:8000

# Worker에서
docker compose exec worker python -c "from services.worker.app.agents.worker_agent import generate_code; print(generate_code('test', 'Write hello'))"

# Evaluator에서
docker compose exec evaluator curl http://localhost:8002/api/v1/stats/summary?hours=1
```

## 사용법

```bash
# 1. 서비스 시작
docker compose up -d

# 2. 테스트 실행 (3가지 방법)
./scripts/run-docker-tests.sh                    # Bash
python scripts/run_docker_tests.py              # Python
docker compose -f docker-compose.test.yml up    # Docker Compose

# 3. 결과 확인
docker compose exec manager cat results/test_results.json
```


#!/bin/bash
# Docker에서 Python 테스트 실행

# 1. 기본 테스트 실행
docker compose exec manager python -m pytest tests/ -v

# 2. 특정 서비스에서 테스트
docker compose exec evaluator python -m pytest tests/ -v
docker compose exec worker python -m pytest tests/ -v

# 3. 종합 테스트 스크립트 실행
docker compose exec manager python /app/scripts/test_comprehensive.py \
  --categories easy_samples medium_samples \
  --manager-url http://manager:8000 \
  --evaluator-url http://evaluator:8002

# 4. 새 컨테이너로 테스트 (일회성)
docker compose run --rm manager python scripts/test_comprehensive.py

# 5. 빠른 테스트
docker compose run --rm manager bash scripts/quick-test.sh

# 6. 커스텀 Python 명령 실행
docker compose exec manager python -c "
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
"

# 7. 테스트 결과를 로컬에 저장
docker compose run --rm manager python scripts/test_comprehensive.py \
  --output /app/results/test_$(date +%Y%m%d_%H%M%S).json

# 결과 파일 복사
docker compose cp manager:/app/results/. ./results/


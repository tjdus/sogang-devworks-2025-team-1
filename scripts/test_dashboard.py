#!/usr/bin/env python3
"""평가 지표 대시보드 테스트 스크립트"""
import argparse
import asyncio
import random
import httpx
TEST_TASKS = [
    {"user_input": "Write a Python function to calculate fibonacci numbers", "task_type": "code_generation"},
    {"user_input": "Create a REST API endpoint for user authentication", "task_type": "code_generation"},
]
async def check_services(manager_url: str, evaluator_url: str):
    print("🔍 Checking service health...\n")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(f"{manager_url}/health")
            print(f"  ✅ Manager: {r.json() if r.status_code == 200 else 'Error'}")
        except Exception as e:
            print(f"  ✗ Manager: {str(e)}")
        try:
            r = await client.get(f"{evaluator_url}/health")
            print(f"  ✅ Evaluator: {r.json() if r.status_code == 200 else 'Error'}")
        except Exception as e:
            print(f"  ✗ Evaluator: {str(e)}")
async def queasync def queasyor_url: str):
    print("\n📊 Querying evaluation statistics.    pri    async with httpx.AsyncClient(timeout=30.0) as client:
        print("1️⃣ Evaluation Summary")
        print("-" * 60)
        try:
            r = await client.get(f"{evaluator_url}/api/v1/stats/summary?hours=24")
            if r.status_code == 200:
                data = r.json()
                print(f"  Total: {data['total_count']}, Pass: {data['pass_count']}, Fail: {data['fail_count']}")
                print(f"  Pass Rate: {data['pass_rate']*100:.2f}%, Avg Score: {data['avg_score']:.4f}")
            print("\n✅ Query complete!")
        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", action="store_true")
    parser.add_argument("--manager-url", default="http://localhost:8000")
    parser.add_argument("--evaluator-url", default="http://localho    parser.add_argument("--evaluator-url"    asyncio.run(check_services(args.manager_url, args.evaluator_url))
    if args.query:
        asyncio.run(query_stats(args.evaluator_url))
if __name__ == "__main__":
    main()

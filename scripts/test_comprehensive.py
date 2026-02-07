#!/usr/bin/env python3
"""
멀티 에이전트 시스템 종합 테스트 스크립트

다양한 난이도의 user_input으로 시스템을 테스트하고
평가 지표를 수집합니다.
"""
import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()


async def send_request(
    client: httpx.AsyncClient,
    manager_url: str,
    user_input: str,
    task_type: str,
) -> Dict:
    """Manager에 요청 전송"""
    try:
        response = await client.post(
            f"{manager_url}/api/v1/request",
            json={
                "user_input": user_input,
                "task_type": task_type,
            },
            timeout=60.0,
        )

        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "error": None,
            }
        else:
            return {
                "success": False,
                "data": None,
                "error": f"HTTP {response.status_code}",
            }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
        }


async def test_sample_category(
    manager_url: str,
    category_name: str,
    samples: List[Dict],
    delay: float = 1.0,
) -> List[Dict]:
    """특정 카테고리의 샘플 테스트"""
    results = []

    console.print(f"\n[bold cyan]Testing {category_name}...[/bold cyan]")

    async with httpx.AsyncClient() as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Processing {len(samples)} samples...",
                total=len(samples),
            )

            for idx, sample in enumerate(samples, 1):
                user_input = sample.get("user_input", "")
                task_type = sample.get("task_type", "code_generation")
                difficulty = sample.get("difficulty", "unknown")

                # 요청 전송
                result = await send_request(client, manager_url, user_input, task_type)

                # 결과 기록
                test_result = {
                    "category": category_name,
                    "difficulty": difficulty,
                    "user_input": user_input[:100] + "..." if len(user_input) > 100 else user_input,
                    "full_input": user_input,
                    "task_type": task_type,
                    "success": result["success"],
                    "timestamp": datetime.utcnow().isoformat(),
                }

                if result["success"]:
                    data = result["data"]
                    test_result.update({
                        "request_id": data.get("request_id"),
                        "evaluation_score": data.get("evaluation_score"),
                        "evaluation_passed": data.get("evaluation_passed"),
                        "prompt_version": data.get("prompt_version"),
                        "worker_output_preview": data.get("worker_output", "")[:200],
                    })

                    # 결과 표시
                    status = "✓" if data.get("evaluation_passed") else "✗"
                    score = data.get("evaluation_score", 0)
                    color = "green" if data.get("evaluation_passed") else "red"

                    console.print(
                        f"  [{idx}/{len(samples)}] {status} "
                        f"[{color}]Score: {score:.3f}[/{color}] "
                        f"[dim]({difficulty})[/dim] - {user_input[:60]}..."
                    )
                else:
                    test_result["error"] = result["error"]
                    console.print(
                        f"  [{idx}/{len(samples)}] ✗ [red]Error: {result['error']}[/red] "
                        f"[dim]({difficulty})[/dim]"
                    )

                results.append(test_result)
                progress.update(task, advance=1)

                # 속도 조절
                await asyncio.sleep(delay)

    return results


async def run_comprehensive_test(
    manager_url: str,
    samples_file: str,
    categories: List[str] = None,
    output_file: str = None,
    delay: float = 1.0,
):
    """종합 테스트 실행"""

    # 샘플 로드
    console.print(f"[bold]Loading test samples from {samples_file}...[/bold]")
    with open(samples_file, 'r', encoding='utf-8') as f:
        all_samples = json.load(f)

    # 카테고리 선택
    if categories:
        selected_samples = {k: v for k, v in all_samples.items() if k in categories}
    else:
        selected_samples = all_samples

    console.print(f"[green]Loaded {len(selected_samples)} categories[/green]\n")

    # 각 카테고리 테스트
    all_results = []

    for category_name, samples in selected_samples.items():
        if not samples:
            continue

        results = await test_sample_category(
            manager_url,
            category_name,
            samples,
            delay,
        )
        all_results.extend(results)

    # 결과 요약
    display_summary(all_results)

    # 결과 저장
    if output_file:
        save_results(all_results, output_file)
        console.print(f"\n[green]Results saved to {output_file}[/green]")

    return all_results


def display_summary(results: List[Dict]):
    """결과 요약 표시"""
    console.print("\n[bold cyan]Test Summary[/bold cyan]")

    # 전체 통계
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    passed = sum(1 for r in results if r.get("evaluation_passed", False))

    console.print(f"\nTotal Requests: {total}")
    console.print(f"Successful: {successful} ({successful/total*100:.1f}%)")
    console.print(f"Passed Evaluation: {passed} ({passed/total*100:.1f}%)")

    # 카테고리별 통계
    table = Table(title="\nResults by Category")
    table.add_column("Category", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("Success", justify="right", style="green")
    table.add_column("Passed", justify="right", style="green")
    table.add_column("Avg Score", justify="right")
    table.add_column("Pass Rate", justify="right")

    categories = {}
    for result in results:
        cat = result["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(result)

    for category, cat_results in categories.items():
        cat_total = len(cat_results)
        cat_success = sum(1 for r in cat_results if r["success"])
        cat_passed = sum(1 for r in cat_results if r.get("evaluation_passed", False))

        scores = [r["evaluation_score"] for r in cat_results if "evaluation_score" in r]
        avg_score = sum(scores) / len(scores) if scores else 0
        pass_rate = cat_passed / cat_total * 100 if cat_total > 0 else 0

        table.add_row(
            category,
            str(cat_total),
            str(cat_success),
            str(cat_passed),
            f"{avg_score:.3f}",
            f"{pass_rate:.1f}%",
        )

    console.print(table)

    # 난이도별 통계
    table2 = Table(title="\nResults by Difficulty")
    table2.add_column("Difficulty", style="cyan")
    table2.add_column("Total", justify="right")
    table2.add_column("Passed", justify="right")
    table2.add_column("Avg Score", justify="right")
    table2.add_column("Pass Rate", justify="right")

    difficulties = {}
    for result in results:
        diff = result.get("difficulty", "unknown")
        if diff not in difficulties:
            difficulties[diff] = []
        difficulties[diff].append(result)

    for difficulty, diff_results in sorted(difficulties.items()):
        diff_total = len(diff_results)
        diff_passed = sum(1 for r in diff_results if r.get("evaluation_passed", False))

        scores = [r["evaluation_score"] for r in diff_results if "evaluation_score" in r]
        avg_score = sum(scores) / len(scores) if scores else 0
        pass_rate = diff_passed / diff_total * 100 if diff_total > 0 else 0

        # 색상 선택
        if pass_rate >= 80:
            color = "green"
        elif pass_rate >= 60:
            color = "yellow"
        else:
            color = "red"

        table2.add_row(
            difficulty,
            str(diff_total),
            f"[{color}]{diff_passed}[/{color}]",
            f"[{color}]{avg_score:.3f}[/{color}]",
            f"[{color}]{pass_rate:.1f}%[/{color}]",
        )

    console.print(table2)


def save_results(results: List[Dict], output_file: str):
    """결과를 JSON 파일로 저장"""
    output_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_tests": len(results),
        "results": results,
        "summary": generate_summary_stats(results),
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


def generate_summary_stats(results: List[Dict]) -> Dict:
    """요약 통계 생성"""
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    passed = sum(1 for r in results if r.get("evaluation_passed", False))

    scores = [r["evaluation_score"] for r in results if "evaluation_score" in r]

    return {
        "total_requests": total,
        "successful_requests": successful,
        "passed_evaluations": passed,
        "success_rate": successful / total if total > 0 else 0,
        "pass_rate": passed / total if total > 0 else 0,
        "average_score": sum(scores) / len(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
    }


def main():
    parser = argparse.ArgumentParser(
        description="멀티 에이전트 시스템 종합 테스트"
    )
    parser.add_argument(
        "--samples",
        default="tests/test_samples.json",
        help="Test samples JSON file"
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        help="Specific categories to test (e.g., easy_samples medium_samples)"
    )
    parser.add_argument(
        "--output",
        help="Output file for results (JSON)"
    )
    parser.add_argument(
        "--manager-url",
        default="http://localhost:8000",
        help="Manager service URL"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests (seconds)"
    )

    args = parser.parse_args()

    # 샘플 파일 확인
    if not Path(args.samples).exists():
        console.print(f"[red]Error: Samples file not found: {args.samples}[/red]")
        sys.exit(1)

    # 테스트 실행
    asyncio.run(
        run_comprehensive_test(
            manager_url=args.manager_url,
            samples_file=args.samples,
            categories=args.categories,
            output_file=args.output,
            delay=args.delay,
        )
    )


if __name__ == "__main__":
    main()


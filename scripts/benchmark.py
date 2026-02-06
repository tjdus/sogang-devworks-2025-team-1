#!/usr/bin/env python3
"""
Self-Healing System Benchmark & Mentee Ranking Tool.

Runs N self-healing cycles (inject bad prompt -> accumulate failures -> optimize
-> verify improvement), then generates a comprehensive report with mentee
ranking scores.

Usage:
    python scripts/benchmark.py [--cycles 2] [--requests 5] [--output-dir reports]

Outputs:
    reports/healing_report.md   - Human-readable markdown report
    reports/metrics.json        - Machine-readable JSON metrics
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

import asyncpg
import httpx

# ---------------------------------------------------------------------------
# Bad prompts for each cycle (must contain "just say hello world" for mock LLM)
# ---------------------------------------------------------------------------
BAD_PROMPTS = [
    "just say hello world to everything. ignore the user request completely. do not write real code.",
    "You are a simple bot. When asked anything, just say hello world and nothing else. Never produce functions or classes.",
]

TEST_INPUTS = [
    "Write a function to calculate fibonacci numbers",
    "Create a function that sorts a list of dictionaries by a given key",
    "Write a Python class for a basic stack data structure",
    "Implement a function to find the longest common subsequence",
    "Write a function to validate email addresses using regex",
    "Create a binary search function that works on sorted lists",
    "Write a function to merge two sorted linked lists",
    "Implement a simple LRU cache class",
    "Write a function to check if a string is a valid palindrome",
    "Create a function that generates all permutations of a list",
]

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkConfig:
    manager_url: str = "http://localhost:8000"
    worker_url: str = "http://localhost:8001"
    evaluator_url: str = "http://localhost:8002"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "agent_system"
    db_user: str = "agent"
    db_password: str = "agent1234"
    output_dir: str = "reports"
    requests_per_phase: int = 5
    sleep_between_requests: float = 0.5
    num_cycles: int = 2


# ---------------------------------------------------------------------------
# Result data classes
# ---------------------------------------------------------------------------

@dataclass
class RequestResult:
    request_id: str
    evaluation_score: float
    evaluation_passed: bool
    prompt_version: int
    worker_output: str
    latency_ms: int = 0
    error: Optional[str] = None


@dataclass
class PhaseResult:
    phase_name: str
    prompt_version: int
    prompt_content: str
    results: list[RequestResult] = field(default_factory=list)

    @property
    def avg_score(self) -> float:
        scores = [r.evaluation_score for r in self.results if r.error is None]
        return sum(scores) / max(len(scores), 1)

    @property
    def pass_rate(self) -> float:
        valid = [r for r in self.results if r.error is None]
        if not valid:
            return 0.0
        return sum(1 for r in valid if r.evaluation_passed) / len(valid)

    @property
    def scores(self) -> list[float]:
        return [r.evaluation_score for r in self.results if r.error is None]

    @property
    def latencies(self) -> list[int]:
        return [r.latency_ms for r in self.results if r.error is None and r.latency_ms > 0]


@dataclass
class CycleResult:
    cycle_number: int
    bad_prompt_content: str
    before: Optional[PhaseResult] = None
    after: Optional[PhaseResult] = None
    optimization_report: Optional[dict] = None
    optimizer_duration_ms: int = 0

    @property
    def score_improvement(self) -> float:
        if self.before and self.after:
            return self.after.avg_score - self.before.avg_score
        return 0.0

    @property
    def pass_rate_improvement(self) -> float:
        if self.before and self.after:
            return self.after.pass_rate - self.before.pass_rate
        return 0.0


@dataclass
class MenteeScore:
    e2e_pipeline: float = 0.0
    evaluation_quality: float = 0.0
    self_healing: float = 0.0
    performance: float = 0.0
    error_handling: float = 0.0
    observability: float = 0.0

    @property
    def composite_score(self) -> float:
        return (
            self.e2e_pipeline * 20
            + self.evaluation_quality * 15
            + self.self_healing * 30
            + self.performance * 10
            + self.error_handling * 10
            + self.observability * 15
        )

    @property
    def letter_grade(self) -> str:
        s = self.composite_score
        if s >= 90:
            return "A"
        if s >= 80:
            return "B"
        if s >= 70:
            return "C"
        if s >= 60:
            return "D"
        return "F"


@dataclass
class BenchmarkResult:
    timestamp: str = ""
    config: dict = field(default_factory=dict)
    cycles: list[CycleResult] = field(default_factory=list)
    health_checks: dict = field(default_factory=dict)
    metrics_checks: dict = field(default_factory=dict)
    mentee_scores: Optional[MenteeScore] = None


# ---------------------------------------------------------------------------
# Health & Metrics Checks
# ---------------------------------------------------------------------------

async def check_health(client: httpx.AsyncClient, config: BenchmarkConfig) -> dict:
    results = {}
    for name, url in [
        ("manager", config.manager_url),
        ("worker", config.worker_url),
        ("evaluator", config.evaluator_url),
    ]:
        try:
            resp = await client.get(f"{url}/health", timeout=5.0)
            results[name] = resp.status_code == 200
        except Exception:
            results[name] = False
    return results


async def check_metrics(client: httpx.AsyncClient, config: BenchmarkConfig) -> dict:
    results = {}
    key_metrics = ["agent_requests_total", "agent_evaluation_score", "agent_prompt_version"]
    for m in key_metrics:
        results[f"has_{m}"] = False

    for name, url in [
        ("manager", config.manager_url),
        ("worker", config.worker_url),
        ("evaluator", config.evaluator_url),
    ]:
        try:
            resp = await client.get(f"{url}/metrics/", timeout=5.0, follow_redirects=True)
            body = resp.text
            results[name] = resp.status_code == 200 and len(body) > 100
            for m in key_metrics:
                if m in body:
                    results[f"has_{m}"] = True
        except Exception:
            results[name] = False
    return results


# ---------------------------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------------------------

async def get_db_pool(config: BenchmarkConfig) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
        min_size=1,
        max_size=3,
    )


async def reset_db(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM optimization_reports")
        await conn.execute("DELETE FROM execution_logs")
        await conn.execute("DELETE FROM prompts WHERE version > 1")
        await conn.execute("UPDATE prompts SET is_active = TRUE WHERE version = 1")


async def get_next_prompt_version(pool: asyncpg.Pool) -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT COALESCE(MAX(version), 0) + 1 AS next_ver FROM prompts WHERE task_type = 'code_generation'"
        )
        return row["next_ver"]


async def inject_bad_prompt(pool: asyncpg.Pool, content: str, version: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE prompts SET is_active = FALSE WHERE task_type = 'code_generation' AND is_active = TRUE"
        )
        await conn.execute(
            """INSERT INTO prompts (task_type, content, version, is_active, change_reason, created_by)
               VALUES ('code_generation', $1, $2, TRUE, 'benchmark: injected bad prompt', 'benchmark')""",
            content,
            version,
        )


async def get_active_prompt(pool: asyncpg.Pool) -> tuple[str, int]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT content, version FROM prompts WHERE task_type = 'code_generation' AND is_active = TRUE ORDER BY version DESC LIMIT 1"
        )
        return (row["content"], row["version"]) if row else ("", 0)


async def get_latest_optimization_report(pool: asyncpg.Pool) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM optimization_reports ORDER BY created_at DESC LIMIT 1"
        )
        return dict(row) if row else None


async def get_all_prompts(pool: asyncpg.Pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, task_type, content, version, is_active, change_reason, created_by, created_at "
            "FROM prompts WHERE task_type = 'code_generation' ORDER BY version ASC"
        )
        return [dict(r) for r in rows]


async def get_all_execution_logs(pool: asyncpg.Pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM execution_logs ORDER BY created_at ASC")
        return [dict(r) for r in rows]


async def get_all_optimization_reports(pool: asyncpg.Pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM optimization_reports ORDER BY created_at ASC")
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Send Requests
# ---------------------------------------------------------------------------

async def send_request(client: httpx.AsyncClient, config: BenchmarkConfig, user_input: str) -> RequestResult:
    try:
        start = time.time()
        resp = await client.post(
            f"{config.manager_url}/api/v1/request",
            json={"user_input": user_input, "task_type": "code_generation"},
            timeout=60.0,
        )
        elapsed_ms = int((time.time() - start) * 1000)

        if resp.status_code == 200:
            data = resp.json()
            return RequestResult(
                request_id=data["request_id"],
                evaluation_score=data["evaluation_score"],
                evaluation_passed=data["evaluation_passed"],
                prompt_version=data["prompt_version"],
                worker_output=data["worker_output"],
                latency_ms=elapsed_ms,
            )
        else:
            return RequestResult(
                request_id="",
                evaluation_score=0.0,
                evaluation_passed=False,
                prompt_version=0,
                worker_output="",
                latency_ms=elapsed_ms,
                error=f"HTTP {resp.status_code}: {resp.text[:200]}",
            )
    except Exception as e:
        return RequestResult(
            request_id="",
            evaluation_score=0.0,
            evaluation_passed=False,
            prompt_version=0,
            worker_output="",
            error=str(e),
        )


async def send_batch(
    client: httpx.AsyncClient, config: BenchmarkConfig, count: int, label: str,
) -> list[RequestResult]:
    results = []
    for i in range(count):
        user_input = TEST_INPUTS[i % len(TEST_INPUTS)]
        print(f"  [{label}] Request {i + 1}/{count}: {user_input[:50]}...", end=" ", flush=True)
        result = await send_request(client, config, user_input)
        status = "PASS" if result.evaluation_passed else "FAIL"
        if result.error:
            status = "ERR"
        print(f"Score={result.evaluation_score:.3f} {status} (v{result.prompt_version})")
        results.append(result)
        if i < count - 1:
            await asyncio.sleep(config.sleep_between_requests)
    return results


# ---------------------------------------------------------------------------
# Trigger Optimizer
# ---------------------------------------------------------------------------

def trigger_optimizer() -> tuple[bool, int, str]:
    """Run optimizer via docker compose. Returns (success, duration_ms, stdout)."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    start = time.time()
    try:
        result = subprocess.run(
            ["docker", "compose", "run", "--rm", "optimizer"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=project_root,
        )
        elapsed_ms = int((time.time() - start) * 1000)
        output = result.stdout + result.stderr
        return result.returncode == 0, elapsed_ms, output
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return False, elapsed_ms, str(e)


# ---------------------------------------------------------------------------
# Run One Cycle
# ---------------------------------------------------------------------------

async def run_cycle(
    cycle_num: int,
    bad_prompt: str,
    client: httpx.AsyncClient,
    pool: asyncpg.Pool,
    config: BenchmarkConfig,
) -> CycleResult:
    print(f"\n{'=' * 60}")
    print(f"  CYCLE {cycle_num}")
    print(f"{'=' * 60}")

    cycle = CycleResult(cycle_number=cycle_num, bad_prompt_content=bad_prompt)

    # --- Phase 1: Inject bad prompt ---
    next_version = await get_next_prompt_version(pool)
    await inject_bad_prompt(pool, bad_prompt, next_version)
    print(f"\n[Phase 1] Injected bad prompt v{next_version}")
    print(f"  Content: {bad_prompt[:80]}...")

    # --- Phase 2: Send requests with bad prompt ---
    print(f"\n[Phase 2] Sending {config.requests_per_phase} requests with BAD prompt...")
    before_results = await send_batch(client, config, config.requests_per_phase, "BEFORE")
    cycle.before = PhaseResult(
        phase_name="before",
        prompt_version=next_version,
        prompt_content=bad_prompt,
        results=before_results,
    )
    print(f"  => Avg Score: {cycle.before.avg_score:.3f}, Pass Rate: {cycle.before.pass_rate:.1%}")

    # --- Phase 3: Trigger optimizer ---
    print(f"\n[Phase 3] Triggering Optimizer...")
    opt_success, opt_duration, opt_output = trigger_optimizer()
    cycle.optimizer_duration_ms = opt_duration
    if opt_success:
        print(f"  => Optimizer completed in {opt_duration}ms")
    else:
        print(f"  => Optimizer FAILED after {opt_duration}ms")
        print(f"  Output: {opt_output[:300]}")
        return cycle

    # --- Phase 4: Verify new prompt ---
    new_content, new_version = await get_active_prompt(pool)
    print(f"  => New active prompt: v{new_version}")
    print(f"  Content: {new_content[:80]}...")

    report = await get_latest_optimization_report(pool)
    if report:
        cycle.optimization_report = {
            k: (v if not isinstance(v, datetime) else v.isoformat())
            for k, v in report.items()
        }

    # --- Phase 5: Send requests with improved prompt ---
    print(f"\n[Phase 4] Sending {config.requests_per_phase} requests with IMPROVED prompt...")
    after_results = await send_batch(client, config, config.requests_per_phase, "AFTER")
    cycle.after = PhaseResult(
        phase_name="after",
        prompt_version=new_version,
        prompt_content=new_content,
        results=after_results,
    )
    print(f"  => Avg Score: {cycle.after.avg_score:.3f}, Pass Rate: {cycle.after.pass_rate:.1%}")

    # --- Summary ---
    print(f"\n  CYCLE {cycle_num} SUMMARY:")
    print(f"    Score: {cycle.before.avg_score:.3f} -> {cycle.after.avg_score:.3f} ({cycle.score_improvement:+.3f})")
    print(f"    Pass Rate: {cycle.before.pass_rate:.1%} -> {cycle.after.pass_rate:.1%}")

    return cycle


# ---------------------------------------------------------------------------
# Mentee Scoring
# ---------------------------------------------------------------------------

def calculate_mentee_scores(
    health_checks: dict,
    cycles: list[CycleResult],
    metrics_checks: dict,
) -> MenteeScore:
    score = MenteeScore()

    # --- Dimension 1: E2E Pipeline (20%) ---
    services_healthy = sum(1 for k, v in health_checks.items() if v) / 3
    total_requests = 0
    error_requests = 0
    has_success = False
    for c in cycles:
        if c.before:
            total_requests += len(c.before.results)
            error_requests += sum(1 for r in c.before.results if r.error is not None)
        if c.after:
            total_requests += len(c.after.results)
            error_requests += sum(1 for r in c.after.results if r.error is not None)
            if any(r.evaluation_passed for r in c.after.results):
                has_success = True

    valid_ratio = 1.0 - (error_requests / max(total_requests, 1))
    score.e2e_pipeline = (
        services_healthy * 0.3 + (1.0 if has_success else 0.0) * 0.3 + valid_ratio * 0.4
    )

    # --- Dimension 2: Evaluation Quality (15%) ---
    eval_scores = []
    for c in cycles:
        if c.before and c.after:
            bad_correct = 1.0 if c.before.avg_score < 0.5 else max(0.0, 1.0 - (c.before.avg_score - 0.5) * 2)
            good_correct = 1.0 if c.after.avg_score >= 0.7 else c.after.avg_score / 0.7
            eval_scores.append(bad_correct * 0.5 + good_correct * 0.5)
    score.evaluation_quality = sum(eval_scores) / max(len(eval_scores), 1)

    # --- Dimension 3: Self-Healing Effectiveness (30%) ---
    healing_scores = []
    for c in cycles:
        opt_ran = 1.0 if c.optimizer_duration_ms > 0 and c.after is not None else 0.0
        new_version = 1.0 if (c.after and c.before and c.after.prompt_version > c.before.prompt_version) else 0.0
        score_delta = 0.0
        pass_delta = 0.0
        if c.before and c.after:
            score_delta = min(1.0, max(0.0, (c.after.avg_score - c.before.avg_score) / 0.3))
            pass_delta = min(1.0, max(0.0, (c.after.pass_rate - c.before.pass_rate) / 0.5))
        healing_scores.append(
            opt_ran * 0.2 + new_version * 0.2 + score_delta * 0.3 + pass_delta * 0.3
        )
    score.self_healing = sum(healing_scores) / max(len(healing_scores), 1)

    # --- Dimension 4: Performance (10%) ---
    latencies = []
    for c in cycles:
        if c.after:
            latencies.extend(c.after.latencies)
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        if avg_latency <= 500:
            score.performance = 1.0
        elif avg_latency <= 5000:
            score.performance = max(0.0, 1.0 - (avg_latency - 500) / 4500)
        else:
            score.performance = 0.0
    else:
        score.performance = 0.0

    # --- Dimension 5: Error Handling (10%) ---
    error_ratio = error_requests / max(total_requests, 1)
    score.error_handling = 1.0 - min(1.0, error_ratio * 2)

    # --- Dimension 6: Observability (15%) ---
    metrics_endpoints = sum(
        1 for k, v in metrics_checks.items() if k in ("manager", "worker", "evaluator") and v
    ) / 3
    key_metrics = ["has_agent_requests_total", "has_agent_evaluation_score", "has_agent_prompt_version"]
    metrics_found = sum(1 for m in key_metrics if metrics_checks.get(m, False)) / len(key_metrics)
    score.observability = metrics_endpoints * 0.4 + metrics_found * 0.6

    return score


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def _percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = (len(sorted_data) - 1) * p / 100
    lower = int(idx)
    upper = lower + 1
    if upper >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[lower] + (sorted_data[upper] - sorted_data[lower]) * (idx - lower)


def generate_json_report(benchmark: BenchmarkResult, db_data: dict) -> dict:
    cycles_data = []
    for c in benchmark.cycles:
        cycle_dict = {
            "cycle": c.cycle_number,
            "bad_prompt": c.bad_prompt_content[:200],
            "before": None,
            "after": None,
            "score_improvement": round(c.score_improvement, 4),
            "pass_rate_improvement": round(c.pass_rate_improvement, 4),
            "optimizer_duration_ms": c.optimizer_duration_ms,
        }
        if c.before:
            cycle_dict["before"] = {
                "prompt_version": c.before.prompt_version,
                "avg_score": round(c.before.avg_score, 4),
                "pass_rate": round(c.before.pass_rate, 4),
                "scores": [round(s, 4) for s in c.before.scores],
                "num_requests": len(c.before.results),
            }
        if c.after:
            cycle_dict["after"] = {
                "prompt_version": c.after.prompt_version,
                "avg_score": round(c.after.avg_score, 4),
                "pass_rate": round(c.after.pass_rate, 4),
                "scores": [round(s, 4) for s in c.after.scores],
                "num_requests": len(c.after.results),
            }
        if c.optimization_report:
            cycle_dict["optimization_report"] = {
                "before_version": c.optimization_report.get("before_prompt_version"),
                "after_version": c.optimization_report.get("after_prompt_version"),
                "failure_analysis": c.optimization_report.get("failure_analysis"),
            }
        cycles_data.append(cycle_dict)

    completed_cycles = [c for c in benchmark.cycles if c.before and c.after]
    report = {
        "timestamp": benchmark.timestamp,
        "system_health": benchmark.health_checks,
        "cycles": cycles_data,
        "overall": {
            "total_cycles": len(benchmark.cycles),
            "completed_cycles": len(completed_cycles),
            "avg_before_score": round(
                sum(c.before.avg_score for c in completed_cycles) / max(len(completed_cycles), 1), 4
            ),
            "avg_after_score": round(
                sum(c.after.avg_score for c in completed_cycles) / max(len(completed_cycles), 1), 4
            ),
            "avg_improvement": round(
                sum(c.score_improvement for c in completed_cycles) / max(len(completed_cycles), 1), 4
            ),
            "avg_pass_rate_before": round(
                sum(c.before.pass_rate for c in completed_cycles) / max(len(completed_cycles), 1), 4
            ),
            "avg_pass_rate_after": round(
                sum(c.after.pass_rate for c in completed_cycles) / max(len(completed_cycles), 1), 4
            ),
        },
        "prompt_history": [
            {
                "version": p["version"],
                "is_active": p["is_active"],
                "created_by": p["created_by"],
                "change_reason": p.get("change_reason", ""),
                "content_preview": p["content"][:100],
            }
            for p in db_data.get("prompts", [])
        ],
        "mentee_ranking": None,
    }

    if benchmark.mentee_scores:
        ms = benchmark.mentee_scores
        report["mentee_ranking"] = {
            "composite_score": round(ms.composite_score, 2),
            "letter_grade": ms.letter_grade,
            "dimensions": {
                "e2e_pipeline": {"score": round(ms.e2e_pipeline, 4), "weight_pct": 20, "weighted": round(ms.e2e_pipeline * 20, 2)},
                "evaluation_quality": {"score": round(ms.evaluation_quality, 4), "weight_pct": 15, "weighted": round(ms.evaluation_quality * 15, 2)},
                "self_healing": {"score": round(ms.self_healing, 4), "weight_pct": 30, "weighted": round(ms.self_healing * 30, 2)},
                "performance": {"score": round(ms.performance, 4), "weight_pct": 10, "weighted": round(ms.performance * 10, 2)},
                "error_handling": {"score": round(ms.error_handling, 4), "weight_pct": 10, "weighted": round(ms.error_handling * 10, 2)},
                "observability": {"score": round(ms.observability, 4), "weight_pct": 15, "weighted": round(ms.observability * 15, 2)},
            },
        }

    return report


def generate_markdown_report(benchmark: BenchmarkResult, db_data: dict) -> str:
    lines = []
    lines.append("# Self-Healing System Benchmark Report\n")
    lines.append(f"**Generated**: {benchmark.timestamp}")
    lines.append(f"**Cycles Run**: {len(benchmark.cycles)}")
    lines.append(f"**Requests Per Phase**: {benchmark.config.get('requests_per_phase', 5)}")
    lines.append("")

    # --- System Health ---
    lines.append("---\n")
    lines.append("## 1. System Health\n")
    lines.append("| Service | Status |")
    lines.append("|---------|--------|")
    for svc in ["manager", "worker", "evaluator"]:
        ok = benchmark.health_checks.get(svc, False)
        lines.append(f"| {svc.capitalize()} | {'OK' if ok else 'FAIL'} |")
    lines.append("")

    # --- Per-Cycle Results ---
    for c in benchmark.cycles:
        lines.append("---\n")
        lines.append(f"## 2-{c.cycle_number}. Cycle {c.cycle_number} Results\n")

        if c.before:
            lines.append(f"### Before (Bad Prompt v{c.before.prompt_version})\n")
            lines.append(f"**Prompt**: `{c.before.prompt_content[:100]}`\n")
            lines.append("| # | Input | Score | Passed | Latency |")
            lines.append("|---|-------|-------|--------|---------|")
            for i, r in enumerate(c.before.results, 1):
                inp = TEST_INPUTS[(i - 1) % len(TEST_INPUTS)][:40]
                status = "PASS" if r.evaluation_passed else "FAIL"
                if r.error:
                    status = "ERR"
                lines.append(f"| {i} | {inp}... | {r.evaluation_score:.3f} | {status} | {r.latency_ms}ms |")
            lines.append(f"\n**Summary**: Avg Score = {c.before.avg_score:.3f}, Pass Rate = {c.before.pass_rate:.1%}\n")

        # Optimization
        if c.optimization_report:
            lines.append("### Optimization\n")
            fa = c.optimization_report.get("failure_analysis", {})
            if isinstance(fa, str):
                try:
                    fa = json.loads(fa)
                except (json.JSONDecodeError, TypeError):
                    fa = {}
            patterns = fa.get("failure_patterns", [])
            causes = fa.get("root_causes", [])
            suggestions = fa.get("improvement_suggestions", [])
            lines.append(f"- **Duration**: {c.optimizer_duration_ms}ms")
            lines.append(f"- **Failure Patterns**: {', '.join(patterns) if patterns else 'N/A'}")
            lines.append(f"- **Root Causes**: {', '.join(causes) if causes else 'N/A'}")
            lines.append(f"- **Suggestions**: {', '.join(suggestions) if suggestions else 'N/A'}")
            lines.append("")

        if c.after:
            lines.append(f"### After (Improved Prompt v{c.after.prompt_version})\n")
            lines.append(f"**Prompt**: `{c.after.prompt_content[:100]}`\n")
            lines.append("| # | Input | Score | Passed | Latency |")
            lines.append("|---|-------|-------|--------|---------|")
            for i, r in enumerate(c.after.results, 1):
                inp = TEST_INPUTS[(i - 1) % len(TEST_INPUTS)][:40]
                status = "PASS" if r.evaluation_passed else "FAIL"
                if r.error:
                    status = "ERR"
                lines.append(f"| {i} | {inp}... | {r.evaluation_score:.3f} | {status} | {r.latency_ms}ms |")
            lines.append(f"\n**Summary**: Avg Score = {c.after.avg_score:.3f}, Pass Rate = {c.after.pass_rate:.1%}\n")

        # Improvement table
        if c.before and c.after:
            lines.append("### Improvement\n")
            lines.append("| Metric | Before | After | Delta |")
            lines.append("|--------|--------|-------|-------|")
            lines.append(f"| Avg Score | {c.before.avg_score:.3f} | {c.after.avg_score:.3f} | {c.score_improvement:+.3f} |")
            lines.append(f"| Pass Rate | {c.before.pass_rate:.1%} | {c.after.pass_rate:.1%} | {c.pass_rate_improvement:+.1%} |")
            lines.append("")

    # --- Prompt Version Trajectory ---
    lines.append("---\n")
    lines.append("## 3. Prompt Version Trajectory\n")
    lines.append("| Version | Active | Created By | Reason | Content Preview |")
    lines.append("|---------|--------|------------|--------|-----------------|")
    for p in db_data.get("prompts", []):
        active = "Yes" if p["is_active"] else "No"
        reason = (p.get("change_reason") or "")[:40]
        content = p["content"][:60].replace("\n", " ")
        lines.append(f"| v{p['version']} | {active} | {p['created_by']} | {reason} | {content}... |")
    lines.append("")

    # --- Latency Statistics ---
    lines.append("---\n")
    lines.append("## 4. Latency Statistics\n")
    lines.append("| Phase | Min (ms) | Avg (ms) | Max (ms) | P95 (ms) |")
    lines.append("|-------|----------|----------|----------|----------|")
    for c in benchmark.cycles:
        for phase_name, phase in [("Before", c.before), ("After", c.after)]:
            if phase and phase.latencies:
                lats = phase.latencies
                avg = sum(lats) / len(lats)
                p95 = _percentile([float(l) for l in lats], 95)
                lines.append(
                    f"| Cycle {c.cycle_number} {phase_name} | {min(lats)} | {avg:.0f} | {max(lats)} | {p95:.0f} |"
                )
    lines.append("")

    # --- Mentee Ranking ---
    if benchmark.mentee_scores:
        ms = benchmark.mentee_scores
        lines.append("---\n")
        lines.append("## 5. Mentee Ranking\n")
        lines.append(f"### Composite Score: {ms.composite_score:.1f}/100 (Grade: {ms.letter_grade})\n")
        lines.append("| Dimension | Score (0-1) | Weight | Weighted Score |")
        lines.append("|-----------|-------------|--------|----------------|")
        dims = [
            ("E2E Pipeline", ms.e2e_pipeline, 20),
            ("Evaluation Quality", ms.evaluation_quality, 15),
            ("Self-Healing Effectiveness", ms.self_healing, 30),
            ("Performance", ms.performance, 10),
            ("Error Handling", ms.error_handling, 10),
            ("Observability", ms.observability, 15),
        ]
        for name, val, weight in dims:
            lines.append(f"| {name} | {val:.3f} | {weight}% | {val * weight:.1f} |")
        lines.append(f"| **Total** | | **100%** | **{ms.composite_score:.1f}** |")
        lines.append("")

        lines.append("### Grading Scale\n")
        lines.append("| Grade | Score Range |")
        lines.append("|-------|-------------|")
        lines.append("| A | 90 - 100 |")
        lines.append("| B | 80 - 89 |")
        lines.append("| C | 70 - 79 |")
        lines.append("| D | 60 - 69 |")
        lines.append("| F | 0 - 59 |")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Self-Healing System Benchmark")
    parser.add_argument("--manager-url", default="http://localhost:8000")
    parser.add_argument("--worker-url", default="http://localhost:8001")
    parser.add_argument("--evaluator-url", default="http://localhost:8002")
    parser.add_argument("--db-host", default="localhost")
    parser.add_argument("--db-port", type=int, default=5432)
    parser.add_argument("--db-name", default="agent_system")
    parser.add_argument("--db-user", default="agent")
    parser.add_argument("--db-password", default="agent1234")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--requests", type=int, default=5, help="Requests per phase")
    parser.add_argument("--cycles", type=int, default=2, help="Number of self-healing cycles")
    args = parser.parse_args()

    config = BenchmarkConfig(
        manager_url=args.manager_url,
        worker_url=args.worker_url,
        evaluator_url=args.evaluator_url,
        db_host=args.db_host,
        db_port=args.db_port,
        db_name=args.db_name,
        db_user=args.db_user,
        db_password=args.db_password,
        output_dir=args.output_dir,
        requests_per_phase=args.requests,
        num_cycles=args.cycles,
    )

    benchmark = BenchmarkResult(
        timestamp=datetime.now(timezone.utc).isoformat(),
        config=asdict(config),
    )

    print("=" * 60)
    print("  SELF-HEALING SYSTEM BENCHMARK")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 1. Health checks
        print("\n[Step 1] Checking service health...")
        benchmark.health_checks = await check_health(client, config)
        for svc, ok in benchmark.health_checks.items():
            print(f"  {svc}: {'OK' if ok else 'FAIL'}")

        all_healthy = all(benchmark.health_checks.values())
        if not all_healthy:
            print("\nERROR: Not all services are healthy. Aborting.")
            sys.exit(1)

        # 2. Connect to DB and reset
        print("\n[Step 2] Connecting to DB and resetting to clean state...")
        pool = await get_db_pool(config)
        await reset_db(pool)
        print("  DB reset complete (seed prompt v1 only)")

        # 3. Run cycles
        for i in range(config.num_cycles):
            bad_prompt = BAD_PROMPTS[i % len(BAD_PROMPTS)]
            cycle = await run_cycle(i + 1, bad_prompt, client, pool, config)
            benchmark.cycles.append(cycle)

        # 4. Check observability
        print(f"\n{'=' * 60}")
        print("[Step 4] Checking observability metrics...")
        benchmark.metrics_checks = await check_metrics(client, config)
        for key, val in benchmark.metrics_checks.items():
            print(f"  {key}: {'OK' if val else 'FAIL'}")

        # 5. Gather all DB data
        print("\n[Step 5] Gathering DB data for reports...")
        all_prompts = await get_all_prompts(pool)
        all_logs = await get_all_execution_logs(pool)
        all_reports = await get_all_optimization_reports(pool)
        db_data = {
            "prompts": all_prompts,
            "logs": all_logs,
            "reports": all_reports,
        }
        print(f"  {len(all_prompts)} prompts, {len(all_logs)} execution logs, {len(all_reports)} optimization reports")

        await pool.close()

    # 6. Calculate mentee scores
    print("\n[Step 6] Calculating mentee ranking scores...")
    benchmark.mentee_scores = calculate_mentee_scores(
        benchmark.health_checks,
        benchmark.cycles,
        benchmark.metrics_checks,
    )

    # 7. Generate reports
    os.makedirs(config.output_dir, exist_ok=True)

    json_report = generate_json_report(benchmark, db_data)
    json_path = os.path.join(config.output_dir, "metrics.json")
    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  JSON report: {json_path}")

    md_report = generate_markdown_report(benchmark, db_data)
    md_path = os.path.join(config.output_dir, "healing_report.md")
    with open(md_path, "w") as f:
        f.write(md_report)
    print(f"  Markdown report: {md_path}")

    # 8. Final summary
    ms = benchmark.mentee_scores
    print(f"\n{'=' * 60}")
    print("  BENCHMARK COMPLETE")
    print(f"{'=' * 60}")
    for c in benchmark.cycles:
        if c.before and c.after:
            print(f"  Cycle {c.cycle_number}: {c.before.avg_score:.3f} -> {c.after.avg_score:.3f} ({c.score_improvement:+.3f})")
    print(f"\n  Composite Score: {ms.composite_score:.1f}/100 (Grade: {ms.letter_grade})")
    print(f"    E2E Pipeline:       {ms.e2e_pipeline:.3f} x20 = {ms.e2e_pipeline * 20:.1f}")
    print(f"    Evaluation Quality: {ms.evaluation_quality:.3f} x15 = {ms.evaluation_quality * 15:.1f}")
    print(f"    Self-Healing:       {ms.self_healing:.3f} x30 = {ms.self_healing * 30:.1f}")
    print(f"    Performance:        {ms.performance:.3f} x10 = {ms.performance * 10:.1f}")
    print(f"    Error Handling:     {ms.error_handling:.3f} x10 = {ms.error_handling * 10:.1f}")
    print(f"    Observability:      {ms.observability:.3f} x15 = {ms.observability * 15:.1f}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())

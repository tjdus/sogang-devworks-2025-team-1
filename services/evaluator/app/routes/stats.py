from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import select, func, and_, desc

from services.common.db import get_db
from services.common.models import ExecutionLog
from services.common.logging_utils import setup_logger

logger = setup_logger("evaluator.stats")
router = APIRouter()


@router.get("/stats/summary")
async def get_evaluation_summary(
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    task_type: Optional[str] = Query(default=None, description="Filter by task type"),
):
    """평가 지표 요약 정보 조회"""
    async with get_db() as db:
        # 시간 범위 설정
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        # 기본 필터
        filters = [ExecutionLog.created_at >= time_threshold]
        if task_type:
            filters.append(ExecutionLog.task_type == task_type)

        # 전체 통계
        total_query = select(func.count()).select_from(ExecutionLog).where(and_(*filters))
        total_count = await db.scalar(total_query)

        # 합격/불합격 통계
        pass_query = select(func.count()).select_from(ExecutionLog).where(
            and_(*filters, ExecutionLog.evaluation_passed == True)
        )
        pass_count = await db.scalar(pass_query) or 0

        fail_query = select(func.count()).select_from(ExecutionLog).where(
            and_(*filters, ExecutionLog.evaluation_passed == False)
        )
        fail_count = await db.scalar(fail_query) or 0

        # 평균 점수
        avg_score_query = select(func.avg(ExecutionLog.evaluation_score)).where(
            and_(*filters, ExecutionLog.evaluation_score.isnot(None))
        )
        avg_score = await db.scalar(avg_score_query) or 0.0

        # 평균 레이턴시
        avg_latency_query = select(func.avg(ExecutionLog.worker_latency_ms)).where(
            and_(*filters, ExecutionLog.worker_latency_ms.isnot(None))
        )
        avg_latency = await db.scalar(avg_latency_query) or 0

        # 에러 건수
        error_query = select(func.count()).select_from(ExecutionLog).where(
            and_(*filters, ExecutionLog.error_message.isnot(None))
        )
        error_count = await db.scalar(error_query) or 0

        return {
            "time_range_hours": hours,
            "task_type": task_type,
            "total_count": total_count or 0,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_rate": round(pass_count / total_count, 4) if total_count > 0 else 0,
            "avg_score": round(float(avg_score), 4),
            "avg_latency_ms": round(float(avg_latency), 2),
            "error_count": error_count,
        }


@router.get("/stats/by-task-type")
async def get_stats_by_task_type(
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
):
    """Task Type별 평가 지표"""
    async with get_db() as db:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        query = select(
            ExecutionLog.task_type,
            func.count().label("total"),
            func.count().filter(ExecutionLog.evaluation_passed == True).label("pass_count"),
            func.avg(ExecutionLog.evaluation_score).label("avg_score"),
            func.avg(ExecutionLog.worker_latency_ms).label("avg_latency"),
        ).where(
            ExecutionLog.created_at >= time_threshold
        ).group_by(
            ExecutionLog.task_type
        )

        result = await db.execute(query)
        rows = result.all()

        stats = []
        for row in rows:
            total = row.total or 0
            pass_count = row.pass_count or 0
            stats.append({
                "task_type": row.task_type,
                "total_count": total,
                "pass_count": pass_count,
                "fail_count": total - pass_count,
                "pass_rate": round(pass_count / total, 4) if total > 0 else 0,
                "avg_score": round(float(row.avg_score or 0), 4),
                "avg_latency_ms": round(float(row.avg_latency or 0), 2),
            })

        return {"time_range_hours": hours, "stats": stats}


@router.get("/stats/score-distribution")
async def get_score_distribution(
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    task_type: Optional[str] = Query(default=None, description="Filter by task type"),
):
    """평가 점수 분포"""
    async with get_db() as db:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        filters = [
            ExecutionLog.created_at >= time_threshold,
            ExecutionLog.evaluation_score.isnot(None),
        ]
        if task_type:
            filters.append(ExecutionLog.task_type == task_type)

        # 점수 구간별 분포 (0-0.3, 0.3-0.5, 0.5-0.7, 0.7-0.9, 0.9-1.0)
        buckets = [
            ("0.0-0.3", 0.0, 0.3),
            ("0.3-0.5", 0.3, 0.5),
            ("0.5-0.7", 0.5, 0.7),
            ("0.7-0.9", 0.7, 0.9),
            ("0.9-1.0", 0.9, 1.0),
        ]

        distribution = []
        for label, min_score, max_score in buckets:
            query = select(func.count()).select_from(ExecutionLog).where(
                and_(
                    *filters,
                    ExecutionLog.evaluation_score >= min_score,
                    ExecutionLog.evaluation_score < max_score if max_score < 1.0 else ExecutionLog.evaluation_score <= max_score,
                )
            )
            count = await db.scalar(query) or 0
            distribution.append({
                "range": label,
                "count": count,
            })

        return {
            "time_range_hours": hours,
            "task_type": task_type,
            "distribution": distribution,
        }


@router.get("/stats/recent-failures")
async def get_recent_failures(
    limit: int = Query(default=20, ge=1, le=100, description="Number of failures to return"),
    task_type: Optional[str] = Query(default=None, description="Filter by task type"),
):
    """최근 실패 케이스 조회"""
    async with get_db() as db:
        filters = [ExecutionLog.evaluation_passed == False]
        if task_type:
            filters.append(ExecutionLog.task_type == task_type)

        query = select(ExecutionLog).where(
            and_(*filters)
        ).order_by(
            desc(ExecutionLog.created_at)
        ).limit(limit)

        result = await db.execute(query)
        logs = result.scalars().all()

        failures = []
        for log in logs:
            failures.append({
                "id": log.id,
                "request_id": str(log.request_id),
                "task_type": log.task_type,
                "prompt_version": log.prompt_version,
                "score": round(log.evaluation_score, 3) if log.evaluation_score else None,
                "user_input": log.user_input[:100] + "..." if len(log.user_input) > 100 else log.user_input,
                "worker_output": log.worker_output[:100] + "..." if log.worker_output and len(log.worker_output) > 100 else log.worker_output,
                "error_message": log.error_message,
                "evaluation_detail": log.evaluation_detail,
                "created_at": log.created_at.isoformat(),
            })

        return {"failures": failures}


@router.get("/stats/prompt-performance")
async def get_prompt_performance(
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    task_type: Optional[str] = Query(default=None, description="Filter by task type"),
):
    """프롬프트 버전별 성능 비교"""
    async with get_db() as db:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        filters = [
            ExecutionLog.created_at >= time_threshold,
            ExecutionLog.prompt_version.isnot(None),
        ]
        if task_type:
            filters.append(ExecutionLog.task_type == task_type)

        query = select(
            ExecutionLog.prompt_version,
            ExecutionLog.task_type,
            func.count().label("total"),
            func.count().filter(ExecutionLog.evaluation_passed == True).label("pass_count"),
            func.avg(ExecutionLog.evaluation_score).label("avg_score"),
            func.avg(ExecutionLog.worker_latency_ms).label("avg_latency"),
        ).where(
            and_(*filters)
        ).group_by(
            ExecutionLog.prompt_version,
            ExecutionLog.task_type,
        ).order_by(
            ExecutionLog.task_type,
            ExecutionLog.prompt_version,
        )

        result = await db.execute(query)
        rows = result.all()

        performance = []
        for row in rows:
            total = row.total or 0
            pass_count = row.pass_count or 0
            performance.append({
                "prompt_version": row.prompt_version,
                "task_type": row.task_type,
                "total_count": total,
                "pass_count": pass_count,
                "pass_rate": round(pass_count / total, 4) if total > 0 else 0,
                "avg_score": round(float(row.avg_score or 0), 4),
                "avg_latency_ms": round(float(row.avg_latency or 0), 2),
            })

        return {
            "time_range_hours": hours,
            "task_type": task_type,
            "performance": performance,
        }


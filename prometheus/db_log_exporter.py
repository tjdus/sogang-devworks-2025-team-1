import os
import time
import psycopg2
from prometheus_client import start_http_server, Gauge

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "agent")
DB_PASSWORD = os.getenv("DB_PASSWORD", "agent1234")
DB_NAME = os.getenv("DB_NAME", "agent_system")
EXPORTER_PORT = int(os.getenv("EXPORTER_PORT", "9610"))

TABLE_NAME = os.getenv("TABLE_NAME", "execution_logs")
STATUS_COLUMN = os.getenv("STATUS_COLUMN", "evaluation_passed")
TIMESTAMP_COLUMN = os.getenv("TIMESTAMP_COLUMN", "created_at")

# Basic metrics
TOTAL_METRIC = Gauge("app_db_log_total", "Total rows in execution_logs table")
RECENT_FAILS = Gauge("app_db_recent_failures", "Failed rows in the last 24h")

# Task type metrics
TASK_TYPE_TOTAL = Gauge("app_db_task_type_total", "Total by task type", ["task_type"])
TASK_TYPE_PASSED = Gauge("app_db_task_type_passed", "Passed by task type", ["task_type"])
TASK_TYPE_FAILED = Gauge("app_db_task_type_failed", "Failed by task type", ["task_type"])
TASK_TYPE_AVG_SCORE = Gauge("app_db_task_type_avg_score", "Avg score by task type", ["task_type"])
TASK_TYPE_AVG_LATENCY = Gauge("app_db_task_type_avg_latency_ms", "Avg latency by task type", ["task_type"])

# Prompt version metrics
PROMPT_VERSION_TOTAL = Gauge("app_db_prompt_version_total", "Total by prompt version", ["prompt_version", "task_type"])
PROMPT_VERSION_PASSED = Gauge("app_db_prompt_version_passed", "Passed by prompt version", ["prompt_version", "task_type"])
PROMPT_VERSION_AVG_SCORE = Gauge("app_db_prompt_version_avg_score", "Avg score by prompt version", ["prompt_version", "task_type"])

# Recent metrics (1 hour)
RECENT_TOTAL = Gauge("app_db_recent_total", "Total in last 1 hour")
RECENT_PASSED = Gauge("app_db_recent_passed", "Passed in last 1 hour")
RECENT_AVG_SCORE = Gauge("app_db_recent_avg_score", "Avg score in last 1 hour")
RECENT_AVG_LATENCY = Gauge("app_db_recent_avg_latency_ms", "Avg latency in last 1 hour")

# Score distribution
SCORE_RANGE_COUNT = Gauge("app_db_score_range_count", "Count by score range", ["score_range"])

# Error metrics
ERROR_COUNT = Gauge("app_db_error_count", "Total errors")
RECENT_ERRORS = Gauge("app_db_recent_errors", "Errors in last 1 hour")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
    )

def update_metrics():
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1. 전체 row 수
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
        TOTAL_METRIC.set(cur.fetchone()[0] or 0)

        # 2. 최근 24시간 실패 수
        cur.execute(
            f"SELECT COUNT(*) FROM {TABLE_NAME} "
            f"WHERE {STATUS_COLUMN} = false "
            f"AND {TIMESTAMP_COLUMN} >= NOW() - interval '24 hours';"
        )
        RECENT_FAILS.set(cur.fetchone()[0] or 0)

        # 3. Task Type별 통계
        cur.execute(f"""
            SELECT 
                task_type,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE {STATUS_COLUMN} = true) as passed,
                COUNT(*) FILTER (WHERE {STATUS_COLUMN} = false) as failed,
                AVG(evaluation_score) as avg_score,
                AVG(worker_latency_ms) as avg_latency
            FROM {TABLE_NAME}
            WHERE task_type IS NOT NULL
            GROUP BY task_type
        """)
        for row in cur.fetchall():
            task_type, total, passed, failed, avg_score, avg_latency = row
            TASK_TYPE_TOTAL.labels(task_type=task_type).set(total or 0)
            TASK_TYPE_PASSED.labels(task_type=task_type).set(passed or 0)
            TASK_TYPE_FAILED.labels(task_type=task_type).set(failed or 0)
            TASK_TYPE_AVG_SCORE.labels(task_type=task_type).set(avg_score or 0)
            TASK_TYPE_AVG_LATENCY.labels(task_type=task_type).set(avg_latency or 0)

        # 4. Prompt Version별 통계
        cur.execute(f"""
            SELECT 
                prompt_version,
                task_type,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE {STATUS_COLUMN} = true) as passed,
                AVG(evaluation_score) as avg_score
            FROM {TABLE_NAME}
            WHERE prompt_version IS NOT NULL AND task_type IS NOT NULL
            GROUP BY prompt_version, task_type
        """)
        for row in cur.fetchall():
            version, task_type, total, passed, avg_score = row
            PROMPT_VERSION_TOTAL.labels(prompt_version=str(version), task_type=task_type).set(total or 0)
            PROMPT_VERSION_PASSED.labels(prompt_version=str(version), task_type=task_type).set(passed or 0)
            PROMPT_VERSION_AVG_SCORE.labels(prompt_version=str(version), task_type=task_type).set(avg_score or 0)

        # 5. 최근 1시간 통계
        cur.execute(f"""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE {STATUS_COLUMN} = true) as passed,
                AVG(evaluation_score) as avg_score,
                AVG(worker_latency_ms) as avg_latency
            FROM {TABLE_NAME}
            WHERE {TIMESTAMP_COLUMN} >= NOW() - interval '1 hour'
        """)
        row = cur.fetchone()
        if row:
            RECENT_TOTAL.set(row[0] or 0)
            RECENT_PASSED.set(row[1] or 0)
            RECENT_AVG_SCORE.set(row[2] or 0)
            RECENT_AVG_LATENCY.set(row[3] or 0)

        # 6. Score 분포
        score_ranges = [
            ("0.0-0.3", 0.0, 0.3),
            ("0.3-0.5", 0.3, 0.5),
            ("0.5-0.7", 0.5, 0.7),
            ("0.7-0.9", 0.7, 0.9),
            ("0.9-1.0", 0.9, 1.0),
        ]
        for label, min_val, max_val in score_ranges:
            if max_val < 1.0:
                cur.execute(f"""
                    SELECT COUNT(*) FROM {TABLE_NAME}
                    WHERE evaluation_score >= {min_val} AND evaluation_score < {max_val}
                """)
            else:
                cur.execute(f"""
                    SELECT COUNT(*) FROM {TABLE_NAME}
                    WHERE evaluation_score >= {min_val} AND evaluation_score <= {max_val}
                """)
            SCORE_RANGE_COUNT.labels(score_range=label).set(cur.fetchone()[0] or 0)

        # 7. 에러 통계
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE error_message IS NOT NULL")
        ERROR_COUNT.set(cur.fetchone()[0] or 0)

        cur.execute(f"""
            SELECT COUNT(*) FROM {TABLE_NAME}
            WHERE error_message IS NOT NULL 
            AND {TIMESTAMP_COLUMN} >= NOW() - interval '1 hour'
        """)
        RECENT_ERRORS.set(cur.fetchone()[0] or 0)

        cur.close()
        conn.close()
    except Exception as e:
        # 실패 시 0으로 세팅하고 로그 출력
        print(f"db_log_exporter error: {e}")
        TOTAL_METRIC.set(0)
        RECENT_FAILS.set(0)

if __name__ == "__main__":
    start_http_server(EXPORTER_PORT)
    print(f"db_log_exporter started on :{EXPORTER_PORT}, querying {TABLE_NAME}@{DB_HOST}:{DB_PORT}")
    while True:
        update_metrics()
        time.sleep(15)

from prometheus_client import Counter, Histogram, Gauge

# Request counters
REQUEST_COUNT = Counter(
    "agent_requests_total",
    "Total requests processed",
    ["service", "task_type", "status"],
)

# Latency histograms
REQUEST_LATENCY = Histogram(
    "agent_request_duration_seconds",
    "Request latency in seconds",
    ["service", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# Evaluation scores
EVALUATION_SCORE = Histogram(
    "agent_evaluation_score",
    "Evaluation scores distribution",
    ["task_type"],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

EVALUATION_PASS_TOTAL = Counter(
    "agent_evaluation_pass_total",
    "Total evaluations passed/failed",
    ["task_type", "result"],
)

# Prompt version tracking
PROMPT_VERSION = Gauge(
    "agent_prompt_version",
    "Current active prompt version",
    ["task_type"],
)

# Optimization events
OPTIMIZATION_RUNS = Counter(
    "agent_optimization_runs_total",
    "Total optimization runs",
    ["task_type", "result"],
)

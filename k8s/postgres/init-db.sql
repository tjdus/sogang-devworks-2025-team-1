CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    change_reason TEXT,
    created_by VARCHAR(64) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompts_task_type ON prompts(task_type);
CREATE INDEX idx_prompts_active ON prompts(task_type, is_active);

CREATE TABLE IF NOT EXISTS execution_logs (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    task_type VARCHAR(64) NOT NULL,
    user_input TEXT NOT NULL,
    refined_input TEXT,
    prompt_version INTEGER,
    worker_output TEXT,
    worker_latency_ms INTEGER,
    evaluation_score FLOAT,
    evaluation_passed BOOLEAN,
    evaluation_detail JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_execution_logs_task_type ON execution_logs(task_type);
CREATE INDEX idx_execution_logs_created_at ON execution_logs(created_at);
CREATE INDEX idx_execution_logs_passed ON execution_logs(task_type, evaluation_passed);

CREATE TABLE IF NOT EXISTS optimization_reports (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(64) NOT NULL,
    before_prompt_version INTEGER NOT NULL,
    before_prompt_content TEXT NOT NULL,
    after_prompt_version INTEGER NOT NULL,
    after_prompt_content TEXT NOT NULL,
    failure_analysis JSONB,
    improvement_pct FLOAT,
    triggered_by VARCHAR(64) NOT NULL DEFAULT 'cronjob',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed initial prompt for code_generation
INSERT INTO prompts (task_type, content, version, is_active, change_reason, created_by)
VALUES (
    'code_generation',
    'You are a Python code generator. Given a user request, generate clean, working Python code.
Include brief comments explaining key logic. Return ONLY the code block, no extra explanation.',
    1,
    TRUE,
    'Initial seed prompt',
    'system'
);

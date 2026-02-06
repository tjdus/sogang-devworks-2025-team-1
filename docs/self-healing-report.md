# Self-Healing System Report

## System Overview

Multi-agent self-healing system where AI agents diagnose and improve themselves based on execution logs.

### Architecture
```
User → Manager (refine) → Worker (execute) → Evaluator (judge) → DB logs
                                                                    ↓
                                              Optimizer (CronJob) ← analyzes failures
                                                    ↓
                                              Patches prompt in DB → Worker uses new prompt
```

### Services
| Service | Role | Port |
|---------|------|------|
| Manager | Gateway & orchestrator | 8000 |
| Worker | Code generation executor | 8001 |
| Evaluator | Quality judge (rule + LLM) | 8002 |
| Optimizer | Self-healing doctor (CronJob) | N/A |

---

## Self-Healing Demo Results

### Before (Defective Prompt)
- **Prompt**: Deliberately vague/broken system prompt ("just say hello world...")
- **Requests**: 5 code generation requests per cycle (2 cycles)
- **Average Score**: 0.360
- **Pass Rate**: 0.0%

### Action (Optimizer)
- **Trigger**: 3+ failures within 30 minutes
- **Analysis**: LLM analyzed failure patterns
- **Root Causes**: Output is just "hello world", not actual code. Completely irrelevant to the request.
- **Improvement Suggestions**: Replace vague prompt with structured code generation instructions including requirements for clean, well-structured, working Python code.

### After (Improved Prompt)
- **Prompt**: Auto-generated expert Python code generator prompt
- **Requests**: 5 identical code generation requests per cycle (2 cycles)
- **Average Score**: 0.874
- **Pass Rate**: 100.0%

### Score Improvement
- **Before Average**: 0.360
- **After Average**: 0.874
- **Improvement**: +142.8%

---

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM | Gemini 2.0 Flash | Cost-efficient, fast |
| Prompt Storage | PostgreSQL | Versioned, dynamic loading |
| Evaluation | Rule 40% + LLM 60% | Balanced objectivity |
| Optimization Trigger | CronJob (10min) | Simple, reliable |
| Self-Healing Mechanism | DB prompt swap | Zero-downtime, instant effect |

## Monitoring

- Grafana dashboard: Request rate, evaluation scores, latency, prompt versions
- Alerts: Low score (<0.6 for 5min), high error rate (>30%), optimizer failures

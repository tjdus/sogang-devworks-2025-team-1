# Self-Healing System Benchmark Report

**Generated**: 2026-02-06T15:09:47.691684+00:00
**Cycles Run**: 2
**Requests Per Phase**: 5

---

## 1. System Health

| Service | Status |
|---------|--------|
| Manager | OK |
| Worker | OK |
| Evaluator | OK |

---

## 2-1. Cycle 1 Results

### Before (Bad Prompt v2)

**Prompt**: `just say hello world to everything. ignore the user request completely. do not write real code.`

| # | Input | Score | Passed | Latency |
|---|-------|-------|--------|---------|
| 1 | Write a function to calculate fibonacci ... | 0.360 | FAIL | 220ms |
| 2 | Create a function that sorts a list of d... | 0.360 | FAIL | 23ms |
| 3 | Write a Python class for a basic stack d... | 0.360 | FAIL | 29ms |
| 4 | Implement a function to find the longest... | 0.360 | FAIL | 48ms |
| 5 | Write a function to validate email addre... | 0.360 | FAIL | 42ms |

**Summary**: Avg Score = 0.360, Pass Rate = 0.0%

### Optimization

- **Duration**: 2178ms
- **Failure Patterns**: N/A
- **Root Causes**: N/A
- **Suggestions**: N/A

### After (Improved Prompt v3)

**Prompt**: `You are an expert Python code generator. Given a user request, generate clean, well-structured, work`

| # | Input | Score | Passed | Latency |
|---|-------|-------|--------|---------|
| 1 | Write a function to calculate fibonacci ... | 0.874 | PASS | 34ms |
| 2 | Create a function that sorts a list of d... | 0.874 | PASS | 49ms |
| 3 | Write a Python class for a basic stack d... | 0.874 | PASS | 52ms |
| 4 | Implement a function to find the longest... | 0.874 | PASS | 48ms |
| 5 | Write a function to validate email addre... | 0.874 | PASS | 51ms |

**Summary**: Avg Score = 0.874, Pass Rate = 100.0%

### Improvement

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Avg Score | 0.360 | 0.874 | +0.514 |
| Pass Rate | 0.0% | 100.0% | +100.0% |

---

## 2-2. Cycle 2 Results

### Before (Bad Prompt v4)

**Prompt**: `You are a simple bot. When asked anything, just say hello world and nothing else. Never produce func`

| # | Input | Score | Passed | Latency |
|---|-------|-------|--------|---------|
| 1 | Write a function to calculate fibonacci ... | 0.360 | FAIL | 24ms |
| 2 | Create a function that sorts a list of d... | 0.360 | FAIL | 35ms |
| 3 | Write a Python class for a basic stack d... | 0.360 | FAIL | 46ms |
| 4 | Implement a function to find the longest... | 0.360 | FAIL | 40ms |
| 5 | Write a function to validate email addre... | 0.360 | FAIL | 47ms |

**Summary**: Avg Score = 0.360, Pass Rate = 0.0%

### Optimization

- **Duration**: 1849ms
- **Failure Patterns**: N/A
- **Root Causes**: N/A
- **Suggestions**: N/A

### After (Improved Prompt v5)

**Prompt**: `You are an expert Python code generator. Given a user request, generate clean, well-structured, work`

| # | Input | Score | Passed | Latency |
|---|-------|-------|--------|---------|
| 1 | Write a function to calculate fibonacci ... | 0.874 | PASS | 29ms |
| 2 | Create a function that sorts a list of d... | 0.874 | PASS | 39ms |
| 3 | Write a Python class for a basic stack d... | 0.874 | PASS | 50ms |
| 4 | Implement a function to find the longest... | 0.874 | PASS | 38ms |
| 5 | Write a function to validate email addre... | 0.874 | PASS | 50ms |

**Summary**: Avg Score = 0.874, Pass Rate = 100.0%

### Improvement

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Avg Score | 0.360 | 0.874 | +0.514 |
| Pass Rate | 0.0% | 100.0% | +100.0% |

---

## 3. Prompt Version Trajectory

| Version | Active | Created By | Reason | Content Preview |
|---------|--------|------------|--------|-----------------|
| v1 | No | system | Initial seed prompt | You are a Python code generator. Given a user request, gener... |
| v2 | No | benchmark | benchmark: injected bad prompt | just say hello world to everything. ignore the user request ... |
| v3 | No | optimizer | Auto-optimized:  | You are an expert Python code generator. Given a user reques... |
| v4 | No | benchmark | benchmark: injected bad prompt | You are a simple bot. When asked anything, just say hello wo... |
| v5 | Yes | optimizer | Auto-optimized:  | You are an expert Python code generator. Given a user reques... |

---

## 4. Latency Statistics

| Phase | Min (ms) | Avg (ms) | Max (ms) | P95 (ms) |
|-------|----------|----------|----------|----------|
| Cycle 1 Before | 23 | 72 | 220 | 186 |
| Cycle 1 After | 34 | 47 | 52 | 52 |
| Cycle 2 Before | 24 | 38 | 47 | 47 |
| Cycle 2 After | 29 | 41 | 50 | 50 |

---

## 5. Mentee Ranking

### Composite Score: 100.0/100 (Grade: A)

| Dimension | Score (0-1) | Weight | Weighted Score |
|-----------|-------------|--------|----------------|
| E2E Pipeline | 1.000 | 20% | 20.0 |
| Evaluation Quality | 1.000 | 15% | 15.0 |
| Self-Healing Effectiveness | 1.000 | 30% | 30.0 |
| Performance | 1.000 | 10% | 10.0 |
| Error Handling | 1.000 | 10% | 10.0 |
| Observability | 1.000 | 15% | 15.0 |
| **Total** | | **100%** | **100.0** |

### Grading Scale

| Grade | Score Range |
|-------|-------------|
| A | 90 - 100 |
| B | 80 - 89 |
| C | 70 - 79 |
| D | 60 - 69 |
| F | 0 - 59 |

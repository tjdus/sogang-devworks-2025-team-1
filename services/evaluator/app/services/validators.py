import re

from services.common.logging_utils import setup_logger

logger = setup_logger("evaluator.validators")

# Patterns that indicate sensitive information leakage
SENSITIVE_PATTERNS = [
    r"(?i)(password|passwd|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b.*password",  # Email + password
]


def validate_output(worker_output: str, task_type: str) -> dict:
    """Rule-based validation. Returns {score: 0-1, details: {...}}."""
    checks = {}
    total_checks = 0
    passed_checks = 0

    if task_type == "code_generation":
        # Check 1: Contains code (has at least a def, class, import, or assignment)
        has_code = bool(re.search(r"(def |class |import |= |\bfor \b|\bif \b)", worker_output))
        checks["has_code"] = has_code
        total_checks += 1
        passed_checks += 1 if has_code else 0

        # Check 2: Not empty / too short
        has_substance = len(worker_output.strip()) > 20
        checks["has_substance"] = has_substance
        total_checks += 1
        passed_checks += 1 if has_substance else 0

        # Check 3: No syntax-breaking patterns (unclosed quotes/brackets heuristic)
        balanced_parens = worker_output.count("(") == worker_output.count(")")
        balanced_brackets = worker_output.count("[") == worker_output.count("]")
        checks["balanced_syntax"] = balanced_parens and balanced_brackets
        total_checks += 1
        passed_checks += 1 if (balanced_parens and balanced_brackets) else 0

        # Check 4: No hardcoded sensitive data
        has_sensitive = any(re.search(p, worker_output) for p in SENSITIVE_PATTERNS)
        checks["no_sensitive_data"] = not has_sensitive
        total_checks += 1
        passed_checks += 1 if not has_sensitive else 0

        # Check 5: Reasonable length (not just a one-liner for complex tasks)
        reasonable_length = len(worker_output.strip()) > 5
        checks["reasonable_length"] = reasonable_length
        total_checks += 1
        passed_checks += 1 if reasonable_length else 0

    score = passed_checks / total_checks if total_checks > 0 else 0.0
    logger.info("rule_validation", extra={"score": score, "checks": checks})
    return {"score": score, "details": checks}

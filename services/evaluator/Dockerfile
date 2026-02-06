# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app
COPY services/common/requirements.txt /app/requirements-common.txt
RUN pip install --no-cache-dir --prefix=/install -r /app/requirements-common.txt

# Runtime stage
FROM python:3.12-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app
COPY --from=builder /install /usr/local

COPY services/__init__.py /app/services/__init__.py
COPY services/common/ /app/services/common/
COPY services/evaluator/ /app/services/evaluator/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8002

CMD ["uvicorn", "services.evaluator.app.main:app", "--host", "0.0.0.0", "--port", "8002"]

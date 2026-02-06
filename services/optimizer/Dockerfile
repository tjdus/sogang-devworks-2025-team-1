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
COPY services/optimizer/ /app/services/optimizer/

RUN chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "services.optimizer.app.main"]

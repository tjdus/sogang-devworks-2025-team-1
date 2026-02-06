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
COPY services/manager/ /app/services/manager/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "services.manager.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

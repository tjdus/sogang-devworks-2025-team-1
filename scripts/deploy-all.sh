#!/bin/bash
set -euo pipefail

echo "=== Deploying Agent System to Kubernetes ==="

NAMESPACE="agent-system"

# Check kubectl connectivity
kubectl cluster-info >/dev/null 2>&1 || { echo "Cannot connect to Kubernetes cluster. Start Docker Desktop K8s first."; exit 1; }

# Step 1: Namespace & Config
echo "[1/5] Creating namespace and config..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# Step 2: PostgreSQL
echo "[2/5] Deploying PostgreSQL..."
kubectl create configmap postgres-init-sql \
    --from-file=init.sql=k8s/postgres/init-db.sql \
    -n ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/postgres/pvc.yaml
kubectl apply -f k8s/postgres/statefulset.yaml
kubectl apply -f k8s/postgres/service.yaml
echo "  Waiting for PostgreSQL..."
kubectl wait --for=condition=ready pod -l app=postgres -n ${NAMESPACE} --timeout=120s

# Step 3: Application Services
echo "[3/5] Deploying application services..."
kubectl apply -f k8s/worker/deployment.yaml
kubectl apply -f k8s/worker/service.yaml
kubectl apply -f k8s/worker/hpa.yaml
kubectl apply -f k8s/evaluator/deployment.yaml
kubectl apply -f k8s/evaluator/service.yaml
kubectl apply -f k8s/manager/deployment.yaml
kubectl apply -f k8s/manager/service.yaml

# Step 4: Ingress
echo "[4/5] Deploying ingress..."
kubectl apply -f k8s/ingress/ingress.yaml

# Step 5: Optimizer CronJob
echo "[5/5] Deploying optimizer cronjob..."
kubectl apply -f k8s/optimizer/cronjob.yaml

echo ""
echo "=== Deployment Complete ==="
echo "Checking pod status..."
kubectl get pods -n ${NAMESPACE}
echo ""
echo "Add to /etc/hosts: 127.0.0.1 agent.local"
echo "Test: curl http://agent.local/health"

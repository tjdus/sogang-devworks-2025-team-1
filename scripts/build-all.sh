#!/bin/bash
set -euo pipefail

echo "=== Building All Docker Images ==="

REGISTRY="agent-system"

echo "Building manager..."
docker build -t ${REGISTRY}/manager:latest -f services/manager/Dockerfile .

echo "Building worker..."
docker build -t ${REGISTRY}/worker:latest -f services/worker/Dockerfile .

echo "Building evaluator..."
docker build -t ${REGISTRY}/evaluator:latest -f services/evaluator/Dockerfile .

echo "Building optimizer..."
docker build -t ${REGISTRY}/optimizer:latest -f services/optimizer/Dockerfile .

echo ""
echo "=== All Images Built ==="
docker images | grep ${REGISTRY}

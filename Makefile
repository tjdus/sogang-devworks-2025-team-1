.PHONY: build build-manager build-worker build-evaluator build-optimizer \
       deploy deploy-infra deploy-services deploy-optimizer \
       undeploy clean logs

NAMESPACE = agent-system
REGISTRY = agent-system

# === Build ===
build: build-manager build-worker build-evaluator build-optimizer

build-manager:
	docker build -t $(REGISTRY)/manager:latest -f services/manager/Dockerfile .

build-worker:
	docker build -t $(REGISTRY)/worker:latest -f services/worker/Dockerfile .

build-evaluator:
	docker build -t $(REGISTRY)/evaluator:latest -f services/evaluator/Dockerfile .

build-optimizer:
	docker build -t $(REGISTRY)/optimizer:latest -f services/optimizer/Dockerfile .

# === Deploy ===
deploy: deploy-infra deploy-services

deploy-infra:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl create configmap postgres-init-sql \
		--from-file=init.sql=k8s/postgres/init-db.sql \
		-n $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f k8s/postgres/pvc.yaml
	kubectl apply -f k8s/postgres/statefulset.yaml
	kubectl apply -f k8s/postgres/service.yaml
	@echo "Waiting for PostgreSQL to be ready..."
	kubectl wait --for=condition=ready pod -l app=postgres -n $(NAMESPACE) --timeout=120s

deploy-services:
	kubectl apply -f k8s/worker/deployment.yaml
	kubectl apply -f k8s/worker/service.yaml
	kubectl apply -f k8s/worker/hpa.yaml
	kubectl apply -f k8s/evaluator/deployment.yaml
	kubectl apply -f k8s/evaluator/service.yaml
	kubectl apply -f k8s/manager/deployment.yaml
	kubectl apply -f k8s/manager/service.yaml
	kubectl apply -f k8s/ingress/ingress.yaml

deploy-optimizer:
	kubectl apply -f k8s/optimizer/cronjob.yaml

run-optimizer:
	kubectl delete job optimizer-manual -n $(NAMESPACE) --ignore-not-found
	kubectl apply -f k8s/optimizer/job-manual.yaml

# === Undeploy ===
undeploy:
	kubectl delete namespace $(NAMESPACE) --ignore-not-found

# === Dev ===
dev:
	docker compose up -d postgres
	@echo "Waiting for PostgreSQL..."
	@sleep 3
	docker compose up -d manager worker evaluator

dev-down:
	docker compose down -v

# === Logs ===
logs:
	kubectl logs -n $(NAMESPACE) -l app=manager --tail=50 -f

logs-worker:
	kubectl logs -n $(NAMESPACE) -l app=worker --tail=50 -f

logs-optimizer:
	kubectl logs -n $(NAMESPACE) -l app=optimizer --tail=50

# === Status ===
status:
	kubectl get pods -n $(NAMESPACE)
	kubectl get svc -n $(NAMESPACE)
	kubectl get hpa -n $(NAMESPACE)

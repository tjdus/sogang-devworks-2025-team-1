# 네트워크 연결 가이드

## 🌐 네트워크 구조

이 프로젝트는 2개의 Docker 네트워크를 사용합니다:

### 1. `sogang-devworks-2025-team-1_default`
- **용도**: 메인 애플리케이션 서비스들
- **연결된 컨테이너**:
  - postgres
  - manager
  - worker
  - evaluator
  - optimizer

### 2. `sogang-devworks-2025-team-1_monitoring`
- **용도**: 모니터링 스택
- **연결된 컨테이너**:
  - prometheus
  - grafana
  - node-exporter
  - db-log-exporter

### 교차 연결
**postgres**, **manager**, **worker**, **evaluator**는 두 네트워크 모두에 연결되어:
- Grafana에서 PostgreSQL에 직접 접근 가능
- Prometheus에서 모든 서비스의 메트릭 수집 가능

```
┌─────────────────────────────────────────────────────────────┐
│                        monitoring network                    │
│                                                               │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐            │
│  │Prometheus│◄──┤ Grafana  │◄──┤db-log-exporter│            │
│  └────┬─────┘   └────┬─────┘   └───────┬──────┘            │
│       │              │                  │                     │
└───────┼──────────────┼──────────────────┼─────────────────────┘
        │              │                  │
        ▼              ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                        default network                       │
│                                                               │
│  ┌──────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐ │
│  │PostgreSQL│◄──┤ Manager │◄──┤  Worker  │   │Evaluator │ │
│  └──────────┘   └─────────┘   └──────────┘   └──────────┘ │
└───────────────────────────────────────────────────────────────┘
```

## 🚀 설정 방법

### 1. 네트워크 생성 (자동)
```bash
# 메인 애플리케이션 시작 시 자동 생성
docker compose up -d
```

### 2. 모니터링 스택 시작
```bash
# 외부 네트워크 사용
docker compose -f docker-compose.monitoring.yml up -d
```

### 3. 네트워크 확인
```bash
# 네트워크 상태 확인
./scripts/check-network.sh
```

## 🔍 연결 테스트

### PostgreSQL → Grafana 연결 테스트
```bash
# Grafana 컨테이너에서 PostgreSQL 접근
docker compose -f docker-compose.monitoring.yml exec grafana \
  sh -c "apk add postgresql-client && psql -h postgres -U agent -d agent_system -c 'SELECT 1'"
```

### Prometheus → Manager 메트릭 수집 테스트
```bash
# Prometheus에서 Manager 메트릭 확인
curl http://localhost:9090/api/v1/query?query=up{job=\"manager\"}
```

### 모든 연결 한번에 테스트
```bash
./scripts/check-network.sh
```

## 📝 Grafana 데이터소스 설정

### PostgreSQL 데이터소스
```yaml
# grafana/provisioning/datasources/datasource.yml
- name: PostgreSQL
  type: postgres
  url: postgres:5432        # 네트워크 내부 호스트명 사용
  database: agent_system
  user: agent
  password: agent1234
```

### Prometheus 데이터소스
```yaml
- name: Prometheus
  type: prometheus
  url: http://prometheus:9090  # 네트워크 내부 호스트명 사용
```

## ⚙️ docker-compose.yaml 네트워크 설정

```yaml
services:
  postgres:
    networks:
      - default           # 애플리케이션 서비스와 통신
      - monitoring        # Grafana와 통신

  manager:
    networks:
      - default
      - monitoring        # Prometheus가 메트릭 수집

networks:
  default:
    name: sogang-devworks-2025-team-1_default
  monitoring:
    name: sogang-devworks-2025-team-1_monitoring
```

## 🐛 문제 해결

### 문제 1: Grafana에서 PostgreSQL 연결 안됨
```bash
# 네트워크 확인
docker network inspect sogang-devworks-2025-team-1_monitoring

# postgres가 monitoring 네트워크에 있는지 확인
docker inspect postgres | jq '.[0].NetworkSettings.Networks'
```

**해결책**:
```bash
# 재시작
docker compose down
docker compose up -d
docker compose -f docker-compose.monitoring.yml up -d
```

### 문제 2: Prometheus가 서비스 메트릭 수집 못함
```bash
# prometheus.yml 확인
cat prometheus/prometheus.yml

# 타겟 상태 확인
curl http://localhost:9090/api/v1/targets
```

**해결책**:
```yaml
# prometheus/prometheus.yml에서 호스트명 확인
scrape_configs:
  - job_name: 'manager'
    static_configs:
      - targets: ['manager:8000']  # 컨테이너 이름 사용
```

### 문제 3: 네트워크가 이미 존재
```bash
# 기존 네트워크 삭제
docker network rm sogang-devworks-2025-team-1_default
docker network rm sogang-devworks-2025-team-1_monitoring

# 재생성
docker compose up -d
```

### 문제 4: 컨테이너 간 통신 안됨
```bash
# 컨테이너 내부에서 테스트
docker compose exec manager ping -c 3 postgres
docker compose exec grafana ping -c 3 prometheus

# DNS 확인
docker compose exec manager nslookup postgres
```

## 📊 네트워크 모니터링

### 네트워크 트래픽 확인
```bash
# 네트워크 상세 정보
docker network inspect sogang-devworks-2025-team-1_default | jq '.[0].Containers'

# 컨테이너 IP 확인
docker compose ps --format json | jq -r '.[] | "\(.Name): \(.Networks)"'
```

### 연결 로그 확인
```bash
# Grafana 로그
docker compose -f docker-compose.monitoring.yml logs grafana | grep -i datasource

# PostgreSQL 연결 로그
docker compose logs postgres | grep "connection"
```

## 🎯 베스트 프랙티스

1. **네트워크 분리**: 애플리케이션과 모니터링 네트워크 분리로 보안 향상
2. **최소 권한**: 필요한 서비스만 monitoring 네트워크에 연결
3. **호스트명 사용**: IP 대신 컨테이너 이름으로 통신
4. **헬스체크**: 각 서비스에 healthcheck 설정으로 안정성 확보

## 🔗 관련 문서

- [Docker Networking 공식 문서](https://docs.docker.com/network/)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)


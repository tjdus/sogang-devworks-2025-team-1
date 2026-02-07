"""
Docker 환경에서 Python 테스트 실행
"""
import subprocess
import sys


def run_in_docker(service: str, command: list[str]):
    """Docker 컨테이너에서 명령 실행"""
    docker_cmd = ["docker", "compose", "exec", service] + command
    result = subprocess.run(docker_cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


def run_tests():
    """테스트 실행"""
    print("🧪 Running tests in Docker...\n")

    # 1. Easy 테스트
    print("1️⃣ Testing Easy samples...")
    run_in_docker("manager", [
        "python", "scripts/test_comprehensive.py",
        "--categories", "easy_samples",
        "--manager-url", "http://localhost:8000",
        "--delay", "1"
    ])

    # 2. Medium 테스트
    print("\n2️⃣ Testing Medium samples...")
    run_in_docker("manager", [
        "python", "scripts/test_comprehensive.py",
        "--categories", "medium_samples",
        "--manager-url", "http://localhost:8000",
        "--delay", "1.5"
    ])

    # 3. 통계 확인
    print("\n3️⃣ Checking statistics...")
    run_in_docker("evaluator", [
        "curl", "-s", "http://localhost:8002/api/v1/stats/summary?hours=1"
    ])

    print("\n✅ Tests completed!")


if __name__ == "__main__":
    run_tests()


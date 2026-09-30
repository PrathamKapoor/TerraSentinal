from fastapi.testclient import TestClient
from backend.app.main import app

def test_api():
    client = TestClient(app)

    res_health = client.get("/health")
    assert res_health.status_code == 200
    print("Health check:", res_health.status_code, res_health.json())

    res_bench = client.get("/api/v1/research/benchmarks")
    assert res_bench.status_code == 200
    bench_data = res_bench.json()
    print(f"Benchmarks check: {res_bench.status_code}, {len(bench_data)} experiments executed")
    for exp in bench_data:
        m = exp["metrics"]
        print(f"  - {exp['experiment_id']}: {exp['name']} | IoU: {m['iou']}, F1: {m['f1']}, FDR: {m['false_discovery_rate']}")

    res_events = client.get("/api/v1/events")
    assert res_events.status_code == 200
    print(f"Events check: {res_events.status_code}, {len(res_events.json())} events found")

if __name__ == "__main__":
    test_api()

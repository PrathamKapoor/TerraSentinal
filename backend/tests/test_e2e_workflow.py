import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import init_db

def test_complete_end_to_end_disaster_workflow():
    init_db()
    with TestClient(app) as client:
        # 1. Health check
        res = client.get("/health")
        assert res.status_code == 200

        # 2. Create Event
        evt_payload = {
            "name": "E2E Monsoonal Inundation Test",
            "description": "Validation test for automated 4-tier disaster intelligence",
            "hazard_type": "FLOOD",
            "aoi_geojson": {
                "type": "Polygon",
                "coordinates": [[[91.80, 24.85], [92.15, 24.85], [92.15, 25.10], [91.80, 25.10], [91.80, 24.85]]]
            },
            "pre_event_date": "2026-05-15",
            "post_event_date": "2026-05-28",
            "use_fixture": True,
            "fixture_id": "sylhet_monsoon_2026"
        }
        res_evt = client.post("/api/v1/events", json=evt_payload)
        assert res_evt.status_code == 201
        evt = res_evt.json()
        event_id = evt["id"]
        assert event_id.startswith("evt_")

        # 3. Trigger Analysis Run
        res_run = client.post(f"/api/v1/events/{event_id}/runs")
        assert res_run.status_code == 202
        run = res_run.json()
        run_id = run["id"]

        # 4. Wait for run to finish (execute pipeline synchronously or poll)
        from backend.app.services.pipeline import PipelineOrchestrator
        PipelineOrchestrator.execute_run(event_id, run_id)

        res_status = client.get(f"/api/v1/runs/{run_id}")
        assert res_status.status_code == 200
        run_status = res_status.json()
        assert run_status["status"] == "COMPLETED"
        assert run_status["stage"] == "DONE"
        assert run_status["progress"] == 1.0

        # 5. Verify Mission Control Summary
        res_summary = client.get(f"/api/v1/events/{event_id}/summary")
        assert res_summary.status_code == 200
        summary = res_summary.json()
        assert summary["flood_summary"]["total_flooded_sqkm"] > 0
        assert summary["isolation_summary"]["isolated_communities_count"] > 0
        assert summary["infrastructure_summary"]["roads_blocked_count"] > 0
        assert len(summary["top_findings"]) > 0

        # 6. Verify Layers
        res_flood = client.get(f"/api/v1/events/{event_id}/flood")
        assert res_flood.status_code == 200
        assert len(res_flood.json()["geojson"]["features"]) > 0

        res_infra = client.get(f"/api/v1/events/{event_id}/infrastructure")
        assert res_infra.status_code == 200
        assert len(res_infra.json()["roads"]["features"]) > 0
        assert len(res_infra.json()["facilities"]["features"]) > 0

        res_graph = client.get(f"/api/v1/events/{event_id}/evidence-graph")
        assert res_graph.status_code == 200
        assert len(res_graph.json()["nodes"]) > 0
        assert len(res_graph.json()["edges"]) > 0

        # 7. Verify Finding & Submit Human Verification
        res_findings = client.get(f"/api/v1/events/{event_id}/findings")
        assert res_findings.status_code == 200
        findings = res_findings.json()
        finding = findings[0]
        finding_id = finding["id"]

        verify_payload = {
            "status": "CONFIRMED",
            "responder_id": "FieldCommander-Alpha",
            "notes": "Drone reconnaissance verified road impassable with 1.4m standing water.",
            "ground_truth_modality": "UAV_RECON"
        }
        res_verify = client.post(f"/api/v1/findings/{finding_id}/verification", json=verify_payload)
        assert res_verify.status_code == 200
        assert res_verify.json()["verification_status"] == "CONFIRMED"

        # 8. Counterfactual Intervention Simulation
        sim_payload = {
            "event_id": event_id,
            "scenario_name": "Emergency Pontoon Bridge Deployment on Bridge B-14",
            "interventions": [
                {
                    "intervention_type": "DEPLOY_PONTOON",
                    "target_infrastructure_id": "bridge_b14_surma",
                    "target_name": "Surma River Main Bridge B-14",
                    "new_state": "OPEN",
                    "cost_estimate_hours": 3.5
                }
            ]
        }
        res_sim = client.post("/api/v1/simulations", json=sim_payload)
        assert res_sim.status_code == 201
        sim_data = res_sim.json()
        assert sim_data["delta"]["reconnected_population"] > 0
        assert sim_data["simulation_badge"] == "SIMULATED / COUNTERFACTUAL"

        # 9. Verify Decision Receipt & Cryptographic SHA-256 Integrity
        res_receipts = client.get(f"/api/v1/events/{event_id}/receipts")
        assert res_receipts.status_code == 200
        receipts = res_receipts.json()
        assert len(receipts) > 0
        receipt_id = receipts[0]["receipt_id"]

        res_check = client.post(f"/api/v1/receipts/{receipt_id}/verify")
        assert res_check.status_code == 200
        verification = res_check.json()
        assert verification["is_valid"] == True
        assert verification["status"] == "CRYPTOGRAPHICALLY_VERIFIED"

        # 10. Research Benchmarks
        res_bench = client.get("/api/v1/research/benchmarks")
        assert res_bench.status_code == 200
        assert len(res_bench.json()) == 6

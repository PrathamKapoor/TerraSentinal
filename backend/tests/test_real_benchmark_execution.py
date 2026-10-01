import pytest
from backend.app.research.benchmark_runner import BenchmarkRunner

def test_real_data_validation_execution():
    """
    STEP 5, 7, 12: Executes real-data validation on Sen1Floods11 subset
    and verifies that non-synthetic metrics are computed across all baselines and splits.
    """
    res = BenchmarkRunner.run_real_data_validation()
    
    assert res["benchmark_track"] == "REAL_DATA_VALIDATION"
    assert res["is_real_data"] is True
    assert res["total_samples"] == 11
    assert "baselines" in res
    
    baselines = res["baselines"]
    assert "BASE-A" in baselines  # SAR-Only
    assert "BASE-B" in baselines  # Optical-Only
    assert "BASE-C" in baselines  # Multimodal Consensus
    assert "BASE-D" in baselines  # TerraSentinel Evidence-Fusion
    assert "BASE-E" in baselines  # Convolutional U-Net Adapter
    
    # Assert model classifications
    assert baselines["BASE-A"]["classification"] == "HEURISTIC"
    assert baselines["BASE-B"]["classification"] == "HEURISTIC"
    assert baselines["BASE-C"]["classification"] == "HEURISTIC"
    assert baselines["BASE-D"]["classification"] == "HEURISTIC"
    assert baselines["BASE-E"]["classification"] == "UNTRAINED / ADAPTER"
    
    # Verify hierarchical metrics
    for b_id, b_res in baselines.items():
        summary = b_res["overall_summary"]
        assert 0.0 < summary["macro_iou"] < 1.0
        assert 0.0 < summary["micro_iou"] < 1.0
        assert 0.0 < summary["micro_f1"] < 1.0
        
        split_sum = b_res["per_split_summary"]
        assert "TEST" in split_sum
        assert "VAL" in split_sum
        assert "TRAIN" in split_sum
        
        events = b_res["per_event_evaluations"]
        assert len(events) == 5
        event_ids = {e["event_id"] for e in events}
        assert event_ids == {
            "EVT_BOLIVIA_MAMORE_2018",
            "EVT_MEKONG_CAMBODIA_2018",
            "EVT_USA_MIDWEST_2019",
            "EVT_SPAIN_VEGA_BAJA_2019",
            "EVT_INDIA_BRAHMAPUTRA_2016"
        }

def test_synthetic_stress_benchmark_reclassification():
    """
    STEP 8: Verifies that synthetic benchmark is explicitly classified
    as CONTROLLED_SYNTHETIC_SENSOR_STRESS with is_real_data=False.
    """
    res = BenchmarkRunner.run_synthetic_stress_benchmark()
    
    assert res["benchmark_track"] == "CONTROLLED_SYNTHETIC_SENSOR_STRESS"
    assert res["is_real_data"] is False
    assert "must not be cited as real-world" in res["notice"]
    assert len(res["per_event_evaluations"]) == 5

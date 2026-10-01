from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.research.benchmark_runner import BenchmarkRunner
from backend.app.research.adapters.real_adapter import RealDatasetNotPresentError

router = APIRouter(prefix="/research", tags=["research"])

@router.get("/benchmarks", response_model=List[Dict[str, Any]])
def get_benchmarks():
    """
    Returns single-scene baseline calibrations (EXP-01 to EXP-06).
    Classified as CONTROLLED_SYNTHETIC_SENSOR_STRESS.
    """
    return BenchmarkRunner.run_all_experiments()

@router.post("/run-all", response_model=List[Dict[str, Any]])
def run_all_benchmarks():
    """Runs single-scene baseline calibrations."""
    return BenchmarkRunner.run_all_experiments()

@router.get("/synthetic-stress", response_model=Dict[str, Any])
def get_synthetic_stress_benchmark():
    """
    Executes the Controlled Synthetic Sensor-Stress Benchmark across 5 scenario stressors.
    Authority: Engineering stress and failure mode isolation.
    """
    return BenchmarkRunner.run_synthetic_stress_benchmark()

@router.get("/real-validation", response_model=Dict[str, Any])
def get_real_data_validation(split: Optional[str] = Query(None, description="Optional split filter: TRAIN, VAL, TEST")):
    """
    Executes the genuine Real-Data Validation benchmark on public Sen1Floods11 satellite data.
    Authority: Primary empirical Earth-observation validation standard.
    """
    try:
        return BenchmarkRunner.run_real_data_validation(split=split)
    except RealDatasetNotPresentError as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.post("/run-real-validation", response_model=Dict[str, Any])
def trigger_real_data_validation(split: Optional[str] = Query(None, description="Optional split filter: TRAIN, VAL, TEST")):
    """
    Triggers execution of the real-data validation suite.
    """
    try:
        return BenchmarkRunner.run_real_data_validation(split=split)
    except RealDatasetNotPresentError as e:
        raise HTTPException(status_code=503, detail=str(e))

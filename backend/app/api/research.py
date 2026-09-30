from typing import List, Dict, Any
from fastapi import APIRouter
from backend.app.research.benchmark_runner import BenchmarkRunner

router = APIRouter(prefix="/research", tags=["research"])

@router.get("/benchmarks", response_model=List[Dict[str, Any]])
def get_benchmarks():
    return BenchmarkRunner.run_all_experiments()

@router.post("/run-all", response_model=List[Dict[str, Any]])
def run_all_benchmarks():
    return BenchmarkRunner.run_all_experiments()

import time
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

from backend.app.services.acquisition import AcquisitionService, SceneBundle
from backend.app.services.flood_detector import DualPolSARTerrainAdapter, UNetFloodAdapter
from backend.app.services.evidence_fusion import EvidenceFusionEngine
from backend.app.research.adapters.synthetic_adapter import SyntheticStressAdapter
from backend.app.research.adapters.real_adapter import Sen1Floods11Adapter, RealDatasetNotPresentError
from backend.app.research.real_baselines import RealBenchmarkBaselines, BASELINE_SPECS
from backend.app.research.benchmark_metrics import (
    calculate_metrics,
    validate_benchmark_integrity,
    compute_hierarchical_aggregates,
    BenchmarkInvalidityError
)

logger = logging.getLogger(__name__)

class BenchmarkRunner:
    """
    TERRASENTINEL DUAL-TRACK BENCHMARK RUNNER
    
    Operates two strictly separated benchmark authorities:
    
    1. REAL_DATA_VALIDATION:
       Primary scientific authority. Evaluates authentic Sentinel-1 SAR and Sentinel-2 optical
       satellite rasters from Sen1Floods11 v1.1 against independent consensus hand-annotated labels.
       Strictly enforces out-of-domain event holdout (Bolivia Mamoré Unseen Test, Cambodia Mekong Val,
       USA/Spain/India Train). Rejects circular threshold ground truth.
       
    2. CONTROLLED_SYNTHETIC_SENSOR_STRESS:
       Engineering and sensor-stress authority. Reclassified from initial prototypes.
       Used for unit testing and isolating specific radar and optical failure modes
       (gale-force wind roughening, severe mountain shadows, dense wetland volume depolarization).
       MUST NOT be cited as real-world satellite generalization results.
    """
    
    # =========================================================================
    # TRACK 1: REAL-DATA VALIDATION (Empirical Ground Truth Authority)
    # =========================================================================
    
    @classmethod
    def run_real_data_validation(
        cls,
        split: Optional[str] = None,
        dataset_name: str = "sen1floods11"
    ) -> Dict[str, Any]:
        """
        Executes genuine Earth-observation validation on real satellite imagery.
        Computes per-scene, per-event, per-region, macro-average, and micro-average metrics.
        Never aggregates results while hiding per-event failures.
        """
        adapter = Sen1Floods11Adapter()
        samples = adapter.get_samples(split=split)
        
        if not samples:
            raise RealDatasetNotPresentError("REAL DATASET NOT PRESENT: No real benchmark samples available.")
            
        baselines = RealBenchmarkBaselines()
        baseline_results: Dict[str, Any] = {}
        
        t_start = time.time()
        
        for spec in BASELINE_SPECS:
            b_id = spec["baseline_id"]
            scene_evals = []
            
            for s in samples:
                # 1. Run baseline inference
                all_preds = baselines.run_all_baselines_on_bundle(s.bundle)
                pred = all_preds[b_id]
                
                # 2. Automated Benchmark Invalidity Check (Step 9)
                # Refuses execution if ground truth is mathematically derived from evaluated threshold
                validate_benchmark_integrity(s, pred, evaluated_track="REAL_DATA_VALIDATION")
                
                # 3. Calculate metrics on valid pixels only (masking out cloud/invalid -1 pixels)
                m = calculate_metrics(s.ground_truth, pred, valid_mask=s.valid_mask)
                
                scene_evals.append({
                    "sample_id": s.sample_id,
                    "event_id": s.event_id,
                    "event_name": s.event_name,
                    "country": s.country,
                    "hazard_type": s.hazard_type,
                    "split": s.split,
                    "cloud_cover_pct": s.bundle.optical_cloud_cover_pct,
                    "metrics": m
                })
                
            agg = compute_hierarchical_aggregates(scene_evals)
            baseline_results[b_id] = {
                "baseline_id": b_id,
                "name": spec["name"],
                "classification": spec["classification"],
                "modalities": spec["modalities"],
                "description": spec["description"],
                "overall_summary": agg["overall_summary"],
                "per_split_summary": agg["per_split_summary"],
                "per_event_evaluations": agg["per_event_evaluations"]
            }
            
        total_runtime_ms = round((time.time() - t_start) * 1000, 2)
        
        return {
            "benchmark_track": "REAL_DATA_VALIDATION",
            "dataset": "Sen1Floods11 (v1.1)",
            "license": "CC BY-4.0",
            "is_real_data": True,
            "total_samples": len(samples),
            "split_filter": split,
            "total_pixels_evaluated": sum(
                s.ground_truth.size for s in samples
            ),
            "total_runtime_ms": total_runtime_ms,
            "baselines": baseline_results
        }

    # =========================================================================
    # TRACK 2: CONTROLLED SYNTHETIC SENSOR-STRESS BENCHMARK
    # =========================================================================

    @classmethod
    def run_synthetic_stress_benchmark(cls) -> Dict[str, Any]:
        """
        Executes the Controlled Synthetic Sensor-Stress Benchmark across 5 scenario stressors:
        - Sylhet (Monsoonal cloud cover)
        - Red River (Saturated clay soil / low contrast)
        - Ebro Gorge (Mountain radar terrain shadows)
        - Mekong Delta (Wetland volume depolarization)
        - Beira Surge (Gale wind surface roughening)
        """
        adapter = SyntheticStressAdapter()
        samples = adapter.get_samples()
        
        fusion_engine = EvidenceFusionEngine()
        results = []
        
        for s in samples:
            t0 = time.time()
            b = s.bundle
            f_res = fusion_engine.fuse_observations(
                b.post_sar_vv, b.post_sar_vh, b.dem_slope, b.optical_mndwi, b.optical_cloud_cover_pct
            )
            pred = (f_res.fused_probability > 0.45)
            m = calculate_metrics(s.ground_truth, pred, valid_mask=s.valid_mask)
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            
            results.append({
                "sample_id": s.sample_id,
                "event_id": s.event_id,
                "name": s.event_name,
                "split": s.split,
                "country": s.country,
                "hazard_type": s.hazard_type,
                "challenge": s.provenance.get("challenge"),
                "metrics": m,
                "runtime_ms": elapsed_ms
            })
            
        agg = compute_hierarchical_aggregates([
            {
                "sample_id": r["sample_id"],
                "event_id": r["event_id"],
                "event_name": r["name"],
                "country": r["country"],
                "hazard_type": r["hazard_type"],
                "split": r["split"],
                "metrics": r["metrics"]
            }
            for r in results
        ])
        
        return {
            "benchmark_track": "CONTROLLED_SYNTHETIC_SENSOR_STRESS",
            "is_real_data": False,
            "classification": "FIXTURE / SENSOR_STRESS_MODEL",
            "notice": "Results are from controlled parametric stress tests and must not be cited as real-world satellite generalization.",
            "overall_summary": agg["overall_summary"],
            "per_split_summary": agg["per_split_summary"],
            "per_event_evaluations": results
        }

    # =========================================================================
    # BACKWARD-COMPATIBILITY CALIBRATION METHODS (Single-Scene Fixture Calibrations)
    # =========================================================================

    @classmethod
    def run_all_experiments(cls) -> List[Dict[str, Any]]:
        """
        Single-scene synthetic calibration suite (EXP-01 to EXP-06).
        Retained for backward compatibility. Clearly classified as FIXTURE calibrations.
        """
        bundle = AcquisitionService.generate_calibrated_fixture_scene("sylhet_monsoon_2026")
        h, w = bundle.dem_elevation.shape
        y, x = np.mgrid[0:h, 0:w]
        river_channel_y = (h * 0.45) + (h * 0.15) * np.sin(x / 18.0)
        dist_to_river = np.abs(y - river_channel_y)
        permanent_river = (dist_to_river < 4.5)
        ground_truth_water = ((dist_to_river < 26.0) & (bundle.dem_slope < 6.0)) | permanent_river
        
        results: List[Dict[str, Any]] = []
        
        # EXP-01: SAR VV Only
        t0 = time.time()
        pred_exp1 = (bundle.post_sar_vv < -16.0)
        m_exp1 = calculate_metrics(ground_truth_water, pred_exp1)
        results.append({
            "experiment_id": "EXP-01",
            "name": "SAR VV Single-Pol Baseline (Synthetic Fixture)",
            "classification": "HEURISTIC",
            "benchmark_track": "CONTROLLED_SYNTHETIC_SENSOR_STRESS",
            "is_real_data": False,
            "modalities": ["Sentinel-1 SAR VV"],
            "terrain_filtering": False,
            "metrics": m_exp1,
            "runtime_ms": round((time.time() - t0) * 1000, 2),
            "research_question": "Baseline single-channel radar sensitivity"
        })
        
        # EXP-02: SAR VV + VH
        t0 = time.time()
        pred_exp2 = (bundle.post_sar_vv < -16.0) & (bundle.post_sar_vh < -23.0)
        m_exp2 = calculate_metrics(ground_truth_water, pred_exp2)
        results.append({
            "experiment_id": "EXP-02",
            "name": "SAR Dual-Pol (VV + VH) No Terrain (Synthetic Fixture)",
            "classification": "HEURISTIC",
            "benchmark_track": "CONTROLLED_SYNTHETIC_SENSOR_STRESS",
            "is_real_data": False,
            "modalities": ["Sentinel-1 SAR VV", "Sentinel-1 SAR VH"],
            "terrain_filtering": False,
            "metrics": m_exp2,
            "runtime_ms": round((time.time() - t0) * 1000, 2),
            "research_question": "RQ1: Dual-pol volume scattering suppression"
        })
        
        # EXP-03: SAR Dual-Pol + DEM Slope
        t0 = time.time()
        pred_exp3 = (bundle.post_sar_vv < -16.0) & (bundle.post_sar_vh < -23.0) & (bundle.dem_slope <= 8.0)
        m_exp3 = calculate_metrics(ground_truth_water, pred_exp3)
        results.append({
            "experiment_id": "EXP-03",
            "name": "SAR Dual-Pol + DEM Slope Constraint (Synthetic Fixture)",
            "classification": "HEURISTIC",
            "benchmark_track": "CONTROLLED_SYNTHETIC_SENSOR_STRESS",
            "is_real_data": False,
            "modalities": ["Sentinel-1 SAR VV+VH", "Copernicus DEM Slope"],
            "terrain_filtering": True,
            "metrics": m_exp3,
            "runtime_ms": round((time.time() - t0) * 1000, 2),
            "research_question": "RQ2: Topographic false-positive shadow suppression"
        })
        
        # EXP-04: Optical MNDWI Only
        t0 = time.time()
        valid_opt = ~np.isnan(bundle.optical_mndwi)
        pred_exp4 = np.zeros_like(ground_truth_water, dtype=bool)
        pred_exp4[valid_opt] = (bundle.optical_mndwi[valid_opt] > 0.0)
        m_exp4 = calculate_metrics(ground_truth_water, pred_exp4)
        results.append({
            "experiment_id": "EXP-04",
            "name": "Optical MNDWI Cloud Obscured (Synthetic Fixture)",
            "classification": "HEURISTIC",
            "benchmark_track": "CONTROLLED_SYNTHETIC_SENSOR_STRESS",
            "is_real_data": False,
            "modalities": ["Sentinel-2 MSI MNDWI"],
            "terrain_filtering": False,
            "metrics": m_exp4,
            "runtime_ms": round((time.time() - t0) * 1000, 2),
            "research_question": "Optical sensor vulnerability to cloud obscuration"
        })
        
        # EXP-05: Evidential Fusion
        t0 = time.time()
        fusion_engine = EvidenceFusionEngine()
        fusion_res = fusion_engine.fuse_observations(
            sar_vv=bundle.post_sar_vv,
            sar_vh=bundle.post_sar_vh,
            dem_slope=bundle.dem_slope,
            optical_mndwi=bundle.optical_mndwi,
            optical_cloud_pct=bundle.optical_cloud_cover_pct
        )
        pred_exp5 = (fusion_res.fused_probability > 0.45)
        m_exp5 = calculate_metrics(ground_truth_water, pred_exp5)
        results.append({
            "experiment_id": "EXP-05",
            "name": "Full Evidential Fusion (Synthetic Fixture)",
            "classification": "HEURISTIC",
            "benchmark_track": "CONTROLLED_SYNTHETIC_SENSOR_STRESS",
            "is_real_data": False,
            "modalities": ["Sentinel-1 SAR", "Sentinel-2 MSI", "DEM Slope"],
            "terrain_filtering": True,
            "metrics": m_exp5,
            "runtime_ms": round((time.time() - t0) * 1000, 2),
            "research_question": "RQ1: Multimodal fusion superiority under clouds"
        })
        
        # EXP-06: PyTorch U-Net Adapter
        t0 = time.time()
        unet_adapter = UNetFloodAdapter()
        unet_res = unet_adapter.predict(
            sar_vv=bundle.post_sar_vv,
            sar_vh=bundle.post_sar_vh,
            dem_slope=bundle.dem_slope,
            optical_mndwi=bundle.optical_mndwi,
            bounds=bundle.bounds
        )
        m_exp6 = calculate_metrics(ground_truth_water, unet_res.binary_mask)
        results.append({
            "experiment_id": "EXP-06",
            "name": "Convolutional U-Net Spatial Adapter (Synthetic Fixture)",
            "classification": "UNTRAINED / ADAPTER",
            "benchmark_track": "CONTROLLED_SYNTHETIC_SENSOR_STRESS",
            "is_real_data": False,
            "modalities": ["4-Channel Tensor (SAR, Opt, Slope)"],
            "terrain_filtering": True,
            "metrics": m_exp6,
            "runtime_ms": round((time.time() - t0) * 1000, 2),
            "research_question": "Deep convolutional boundary precision"
        })
        
        return results

    @classmethod
    def run_event_level_benchmark(cls) -> Dict[str, Any]:
        """Backward-compatible alias for run_synthetic_stress_benchmark."""
        return cls.run_synthetic_stress_benchmark()

    @classmethod
    def run_multimodal_ablations(cls) -> List[Dict[str, Any]]:
        """Controlled synthetic multimodal ablation across 5 synthetic stress events."""
        adapter = SyntheticStressAdapter()
        events = adapter.get_samples()
        ablations = [
            ("A", "SAR Only (Dual-Pol Thresholding)", ["SAR_VV", "SAR_VH"]),
            ("B", "Optical Only (MNDWI under Clouds)", ["OPTICAL_MNDWI"]),
            ("C", "SAR + Optical Consensus", ["SAR", "OPTICAL"]),
            ("D", "SAR + Optical + DEM Slope", ["SAR", "OPTICAL", "DEM_SLOPE"]),
            ("E", "Full Evidential Fusion + Conflict", ["SAR", "OPTICAL", "DEM_SLOPE", "CONFLICT_DETECTION"])
        ]
        
        ablation_results = []
        fusion_engine = EvidenceFusionEngine()
        
        for code, name, modalities in ablations:
            t0 = time.time()
            ious, f1s, precs, recs = [], [], [], []
            test_iou = 0.0
            
            for ev in events:
                b = ev.bundle
                gt = ev.ground_truth
                
                if code == "A":
                    pred = (b.post_sar_vv < -16.0) & (b.post_sar_vh < -23.0)
                elif code == "B":
                    valid_opt = ~np.isnan(b.optical_mndwi)
                    pred = np.zeros_like(gt, dtype=bool)
                    pred[valid_opt] = (b.optical_mndwi[valid_opt] > 0.0)
                elif code == "C":
                    valid_opt = ~np.isnan(b.optical_mndwi)
                    sar_p = (b.post_sar_vv < -16.0)
                    opt_p = np.zeros_like(gt, dtype=bool)
                    opt_p[valid_opt] = (b.optical_mndwi[valid_opt] > 0.0)
                    pred = sar_p | opt_p
                elif code == "D":
                    valid_opt = ~np.isnan(b.optical_mndwi)
                    sar_p = (b.post_sar_vv < -16.0)
                    opt_p = np.zeros_like(gt, dtype=bool)
                    opt_p[valid_opt] = (b.optical_mndwi[valid_opt] > 0.0)
                    pred = (sar_p | opt_p) & (b.dem_slope <= 8.0)
                else:  # E: Full Fusion
                    f_res = fusion_engine.fuse_observations(
                        b.post_sar_vv, b.post_sar_vh, b.dem_slope, b.optical_mndwi, b.optical_cloud_cover_pct
                    )
                    pred = (f_res.fused_probability > 0.45)
                    
                m = calculate_metrics(gt, pred, valid_mask=ev.valid_mask)
                ious.append(m["iou"])
                f1s.append(m["f1"])
                precs.append(m["precision"])
                recs.append(m["recall"])
                if ev.split == "TEST":
                    test_iou = m["iou"]
                    
            ablation_results.append({
                "ablation_code": f"EXP-{code}",
                "name": name,
                "benchmark_track": "CONTROLLED_SYNTHETIC_SENSOR_STRESS",
                "is_real_data": False,
                "modalities": modalities,
                "overall_mean_iou": round(float(np.mean(ious)), 4),
                "overall_mean_f1": round(float(np.mean(f1s)), 4),
                "overall_precision": round(float(np.mean(precs)), 4),
                "overall_recall": round(float(np.mean(recs)), 4),
                "unseen_test_iou": test_iou,
                "runtime_ms": round((time.time() - t0) * 1000, 2)
            })
            
        return ablation_results

if __name__ == "__main__":
    print("=" * 80)
    print("TERRASENTINEL RESEARCH BENCHMARK RUNNER")
    print("=" * 80)
    
    print("\n1. REAL-DATA EMPIRICAL VALIDATION (Sen1Floods11 v1.1):")
    try:
        real_res = BenchmarkRunner.run_real_data_validation()
        print(f"Dataset: {real_res['dataset']} | Total Samples: {real_res['total_samples']} | Total Runtime: {real_res['total_runtime_ms']} ms")
        print(f"{'Base ID':<8} | {'Classification':<19} | {'Name':<36} | {'Macro IoU':<9} | {'Micro IoU'}")
        print("-" * 88)
        for b_id, b_data in real_res["baselines"].items():
            summ = b_data["overall_summary"]
            print(f"{b_id:<8} | {b_data['classification']:<19} | {b_data['name']:<36} | {summ['macro_iou']:<9.4f} | {summ['micro_iou']:.4f}")
    except RealDatasetNotPresentError as e:
        print("REAL DATASET NOT PRESENT:", e)

    print("\n2. CONTROLLED SYNTHETIC SENSOR-STRESS BENCHMARK:")
    syn_res = BenchmarkRunner.run_synthetic_stress_benchmark()
    print(f"Notice: {syn_res['notice']}")
    print(f"{'Event ID':<22} | {'Split':<5} | {'Country':<12} | {'IoU':<7} | {'F1':<7} | {'Precision':<9} | {'Recall'}")
    print("-" * 80)
    for ev in syn_res["per_event_evaluations"]:
        m = ev["metrics"]
        print(f"{ev['event_id']:<22} | {ev['split']:<5} | {ev['country']:<12} | {m['iou']:<7.4f} | {m['f1']:<7.4f} | {m['precision']:<9.4f} | {m['recall']:.4f}")
    print("=" * 80)

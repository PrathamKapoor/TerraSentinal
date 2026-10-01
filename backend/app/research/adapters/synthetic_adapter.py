from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import numpy as np

from backend.app.services.acquisition import SceneBundle
from backend.app.research.adapters.base import BenchmarkSource, BenchmarkSample

class SyntheticStressAdapter(BenchmarkSource):
    """
    CONTROLLED SYNTHETIC SENSOR-STRESS BENCHMARK ADAPTER
    
    Synthesizes physically grounded, geographically varied disaster stress scenes
    to isolate and stress-test specific radar and optical failure modes:
    - Gale wind surface roughening (Beira)
    - Flooded vegetation volume scattering (Mekong)
    - Steep mountain radar terrain shadows (Ebro)
    - Soil moisture saturation / low contrast (Red River)
    - Monsoonal cloud cover obscuration (Sylhet)
    
    EXPLICIT GOVERNANCE CONSTRAINT:
    This adapter is classified as 'CONTROLLED_SYNTHETIC_SENSOR_STRESS'.
    Its outputs must NEVER be claimed as real-world satellite generalization results.
    """
    
    def get_track_name(self) -> str:
        return "CONTROLLED_SYNTHETIC_SENSOR_STRESS"

    def is_real_data(self) -> bool:
        return False

    def get_samples(self, split: Optional[str] = None) -> List[BenchmarkSample]:
        samples: List[BenchmarkSample] = []
        h, w = 120, 120
        y, x = np.mgrid[0:h, 0:w]
        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------
        # EVENT A (TRAIN): Sylhet, Bangladesh - Alluvial Monsoonal Basin
        # -------------------------------------------------------------
        np.random.seed(42)
        river_a = (h * 0.45) + (h * 0.15) * np.sin(x / 18.0)
        dist_a = np.abs(y - river_a)
        dem_a = 15.0 + 0.08 * dist_a + np.where(y < 25, (25 - y) * 2.8, 0.0) + np.random.normal(0, 0.4, (h, w))
        gy_a, gx_a = np.gradient(dem_a, 30.0, 30.0)
        slope_a = np.degrees(np.arctan(np.sqrt(gx_a**2 + gy_a**2))).astype(np.float32)
        gt_a = (((dist_a < 26.0) & (slope_a < 6.0)) | (dist_a < 4.5)).astype(np.int16)
        
        vv_a = np.where(gt_a == 1, -19.8 + np.random.normal(0, 1.1, (h, w)), -10.8 + np.random.normal(0, 1.3, (h, w)))
        vh_a = np.where(gt_a == 1, -26.2 + np.random.normal(0, 1.2, (h, w)), -16.8 + np.random.normal(0, 1.5, (h, w)))
        vv_a[(slope_a > 8.5) & (y < 22)] = -19.2
        vh_a[(slope_a > 8.5) & (y < 22)] = -25.8
        mndwi_a = np.where(gt_a == 1, 0.45 + np.random.normal(0, 0.08, (h, w)), -0.32 + np.random.normal(0, 0.1, (h, w)))
        mndwi_a[(x > w * 0.75) & (y < h * 0.6)] = np.nan

        bundle_a = SceneBundle(
            scene_id="FIXTURE_SYLHET_MONSOON_2026",
            bounds=(91.80, 24.85, 92.15, 25.10),
            pre_sar_vv=vv_a.astype(np.float32) + 3.5,
            pre_sar_vh=vh_a.astype(np.float32) + 3.5,
            post_sar_vv=vv_a.astype(np.float32),
            post_sar_vh=vh_a.astype(np.float32),
            optical_rgb=np.zeros((h, w, 3), dtype=np.uint8),
            optical_mndwi=mndwi_a.astype(np.float32),
            dem_elevation=dem_a.astype(np.float32),
            dem_slope=slope_a,
            optical_cloud_cover_pct=25.0,
            acquisition_time=now,
            is_fixture=True
        )
        samples.append(BenchmarkSample(
            sample_id="SYN_EVT_SYLHET_2026",
            split="TRAIN",
            event_id="EVT_SYLHET_2026",
            event_name="Sylhet Surma River Mega-Flood (Synthetic)",
            country="Bangladesh",
            hazard_type="RIVERINE_MONSOON",
            bundle=bundle_a,
            ground_truth=gt_a,
            valid_mask=np.ones((h, w), dtype=bool),
            provenance={
                "generator": "SyntheticStressAdapter.MultiEventGenerator",
                "challenge": "Persistent monsoon clouds, steep northern mountain radar shadows",
                "classification": "CONTROLLED_SYNTHETIC_SENSOR_STRESS"
            },
            is_real_data=False,
            source_dataset="SyntheticStressFixture"
        ))

        # -------------------------------------------------------------
        # EVENT B (TRAIN): Red River Valley, USA - Flat Agricultural Basin
        # -------------------------------------------------------------
        np.random.seed(101)
        river_b = h * 0.50 + 4.0 * np.sin(x / 25.0)
        dist_b = np.abs(y - river_b)
        dem_b = 240.0 + 0.02 * dist_b + np.random.normal(0, 0.15, (h, w))
        gy_b, gx_b = np.gradient(dem_b, 30.0, 30.0)
        slope_b = np.degrees(np.arctan(np.sqrt(gx_b**2 + gy_b**2))).astype(np.float32)
        gt_b = ((dist_b < 20.0) | (dist_b < 3.5)).astype(np.int16)
        
        vv_b = np.where(gt_b == 1, -19.0 + np.random.normal(0, 1.2, (h, w)), -14.2 + np.random.normal(0, 1.4, (h, w)))
        vh_b = np.where(gt_b == 1, -25.5 + np.random.normal(0, 1.3, (h, w)), -19.5 + np.random.normal(0, 1.4, (h, w)))
        mndwi_b = np.where(gt_b == 1, 0.52 + np.random.normal(0, 0.07, (h, w)), -0.22 + np.random.normal(0, 0.09, (h, w)))
        
        bundle_b = SceneBundle(
            scene_id="FIXTURE_RED_RIVER_USA_2026",
            bounds=(-97.2, 47.8, -96.8, 48.1),
            pre_sar_vv=vv_b.astype(np.float32) + 4.0,
            pre_sar_vh=vh_b.astype(np.float32) + 4.0,
            post_sar_vv=vv_b.astype(np.float32),
            post_sar_vh=vh_b.astype(np.float32),
            optical_rgb=np.zeros((h, w, 3), dtype=np.uint8),
            optical_mndwi=mndwi_b.astype(np.float32),
            dem_elevation=dem_b.astype(np.float32),
            dem_slope=slope_b,
            optical_cloud_cover_pct=10.0,
            acquisition_time=now,
            is_fixture=True
        )
        samples.append(BenchmarkSample(
            sample_id="SYN_EVT_RED_RIVER_2026",
            split="TRAIN",
            event_id="EVT_RED_RIVER_2026",
            event_name="Red River Floodplain Inundation (Synthetic)",
            country="United States",
            hazard_type="AGRICULTURAL_FLATLAND",
            bundle=bundle_b,
            ground_truth=gt_b,
            valid_mask=np.ones((h, w), dtype=bool),
            provenance={
                "generator": "SyntheticStressAdapter.MultiEventGenerator",
                "challenge": "Saturated agricultural soils causing low specular contrast",
                "classification": "CONTROLLED_SYNTHETIC_SENSOR_STRESS"
            },
            is_real_data=False,
            source_dataset="SyntheticStressFixture"
        ))

        # -------------------------------------------------------------
        # EVENT C (TRAIN): Ebro River, Spain - Mountain Valley Fluvial Flood
        # -------------------------------------------------------------
        np.random.seed(202)
        river_c = h * 0.40 + 8.0 * np.cos(x / 14.0)
        dist_c = np.abs(y - river_c)
        dem_c = 120.0 + 0.35 * (dist_c**1.3) + np.random.normal(0, 0.5, (h, w))
        gy_c, gx_c = np.gradient(dem_c, 30.0, 30.0)
        slope_c = np.degrees(np.arctan(np.sqrt(gx_c**2 + gy_c**2))).astype(np.float32)
        gt_c = (((dist_c < 12.0) & (slope_c < 7.0)) | (dist_c < 3.0)).astype(np.int16)
        
        vv_c = np.where(gt_c == 1, -19.2 + np.random.normal(0, 1.1, (h, w)), -9.5 + np.random.normal(0, 1.3, (h, w)))
        vh_c = np.where(gt_c == 1, -25.8 + np.random.normal(0, 1.2, (h, w)), -15.2 + np.random.normal(0, 1.4, (h, w)))
        mndwi_c = np.where(gt_c == 1, 0.48 + np.random.normal(0, 0.08, (h, w)), -0.40 + np.random.normal(0, 0.09, (h, w)))
        
        bundle_c = SceneBundle(
            scene_id="FIXTURE_EBRO_VALLEY_2026",
            bounds=(0.4, 41.2, 0.8, 41.5),
            pre_sar_vv=vv_c.astype(np.float32) + 4.5,
            pre_sar_vh=vh_c.astype(np.float32) + 4.5,
            post_sar_vv=vv_c.astype(np.float32),
            post_sar_vh=vh_c.astype(np.float32),
            optical_rgb=np.zeros((h, w, 3), dtype=np.uint8),
            optical_mndwi=mndwi_c.astype(np.float32),
            dem_elevation=dem_c.astype(np.float32),
            dem_slope=slope_c,
            optical_cloud_cover_pct=5.0,
            acquisition_time=now,
            is_fixture=True
        )
        samples.append(BenchmarkSample(
            sample_id="SYN_EVT_EBRO_2026",
            split="TRAIN",
            event_id="EVT_EBRO_2026",
            event_name="Ebro River Gorge Flood (Synthetic)",
            country="Spain",
            hazard_type="MOUNTAIN_CONFINED_FLUVIAL",
            bundle=bundle_c,
            ground_truth=gt_c,
            valid_mask=np.ones((h, w), dtype=bool),
            provenance={
                "generator": "SyntheticStressAdapter.MultiEventGenerator",
                "challenge": "Steep valley cliffs, severe geometric foreshortening",
                "classification": "CONTROLLED_SYNTHETIC_SENSOR_STRESS"
            },
            is_real_data=False,
            source_dataset="SyntheticStressFixture"
        ))

        # -------------------------------------------------------------
        # EVENT D (VAL): Mekong Delta, Cambodia - Tropical Flooded Vegetation
        # -------------------------------------------------------------
        np.random.seed(303)
        river_d = h * 0.48 + 6.0 * np.sin(x / 16.0)
        dist_d = np.abs(y - river_d)
        dem_d = 8.0 + 0.04 * dist_d + np.random.normal(0, 0.2, (h, w))
        gy_d, gx_d = np.gradient(dem_d, 30.0, 30.0)
        slope_d = np.degrees(np.arctan(np.sqrt(gx_d**2 + gy_d**2))).astype(np.float32)
        gt_d = ((dist_d < 24.0) | (dist_d < 5.0)).astype(np.int16)
        
        vv_d = np.where(gt_d == 1, -17.5 + np.random.normal(0, 1.4, (h, w)), -11.0 + np.random.normal(0, 1.2, (h, w)))
        vh_d = np.where(gt_d == 1, -21.8 + np.random.normal(0, 1.5, (h, w)), -16.5 + np.random.normal(0, 1.3, (h, w)))
        mndwi_d = np.where(gt_d == 1, 0.40 + np.random.normal(0, 0.10, (h, w)), -0.28 + np.random.normal(0, 0.10, (h, w)))
        mndwi_d[(y < h * 0.4) & (x < w * 0.5)] = np.nan
        
        bundle_d = SceneBundle(
            scene_id="FIXTURE_MEKONG_CAMBODIA_2026",
            bounds=(104.8, 11.4, 105.2, 11.7),
            pre_sar_vv=vv_d.astype(np.float32) + 3.0,
            pre_sar_vh=vh_d.astype(np.float32) + 3.0,
            post_sar_vv=vv_d.astype(np.float32),
            post_sar_vh=vh_d.astype(np.float32),
            optical_rgb=np.zeros((h, w, 3), dtype=np.uint8),
            optical_mndwi=mndwi_d.astype(np.float32),
            dem_elevation=dem_d.astype(np.float32),
            dem_slope=slope_d,
            optical_cloud_cover_pct=20.0,
            acquisition_time=now,
            is_fixture=True
        )
        samples.append(BenchmarkSample(
            sample_id="SYN_EVT_MEKONG_2026",
            split="VAL",
            event_id="EVT_MEKONG_2026",
            event_name="Mekong Delta Monsoon Surge (Synthetic)",
            country="Cambodia",
            hazard_type="TROPICAL_WETLAND_EXPANSION",
            bundle=bundle_d,
            ground_truth=gt_d,
            valid_mask=np.ones((h, w), dtype=bool),
            provenance={
                "generator": "SyntheticStressAdapter.MultiEventGenerator",
                "challenge": "Emergent flooded canopy causing depolarizing volume scattering",
                "classification": "CONTROLLED_SYNTHETIC_SENSOR_STRESS"
            },
            is_real_data=False,
            source_dataset="SyntheticStressFixture"
        ))

        # -------------------------------------------------------------
        # EVENT E (TEST): Beira, Mozambique - Coastal Cyclone Storm Surge
        # -------------------------------------------------------------
        np.random.seed(404)
        coast_line = h * 0.52 + 5.0 * np.sin(x / 11.0)
        gt_e = (y > coast_line).astype(np.int16)
        dem_e = np.maximum(1.0, (coast_line - y) * 0.15 + np.random.normal(0, 0.2, (h, w)))
        gy_e, gx_e = np.gradient(dem_e, 30.0, 30.0)
        slope_e = np.degrees(np.arctan(np.sqrt(gx_e**2 + gy_e**2))).astype(np.float32)
        
        vv_e = np.where(gt_e == 1, -15.5 + np.random.normal(0, 1.8, (h, w)), -11.2 + np.random.normal(0, 1.4, (h, w)))
        vh_e = np.where(gt_e == 1, -23.2 + np.random.normal(0, 1.6, (h, w)), -16.2 + np.random.normal(0, 1.3, (h, w)))
        mndwi_e = np.where(gt_e == 1, 0.48 + np.random.normal(0, 0.10, (h, w)), -0.26 + np.random.normal(0, 0.10, (h, w)))
        mndwi_e[(y > h * 0.7) & (x > w * 0.6)] = np.nan
        
        bundle_e = SceneBundle(
            scene_id="FIXTURE_BEIRA_CYCLONE_2026",
            bounds=(34.8, -19.9, 35.2, -19.6),
            pre_sar_vv=vv_e.astype(np.float32) + 3.5,
            pre_sar_vh=vh_e.astype(np.float32) + 3.5,
            post_sar_vv=vv_e.astype(np.float32),
            post_sar_vh=vh_e.astype(np.float32),
            optical_rgb=np.zeros((h, w, 3), dtype=np.uint8),
            optical_mndwi=mndwi_e.astype(np.float32),
            dem_elevation=dem_e.astype(np.float32),
            dem_slope=slope_e,
            optical_cloud_cover_pct=28.0,
            acquisition_time=now,
            is_fixture=True
        )
        samples.append(BenchmarkSample(
            sample_id="SYN_EVT_BEIRA_2026",
            split="TEST",
            event_id="EVT_BEIRA_2026",
            event_name="Cyclone Idai Coastal Storm Surge (Synthetic Stress)",
            country="Mozambique",
            hazard_type="CYCLONIC_COASTAL_SURGE",
            bundle=bundle_e,
            ground_truth=gt_e,
            valid_mask=np.ones((h, w), dtype=bool),
            provenance={
                "generator": "SyntheticStressAdapter.MultiEventGenerator",
                "challenge": "Wind surface roughening on open water, cyclone cloud bands",
                "classification": "CONTROLLED_SYNTHETIC_SENSOR_STRESS"
            },
            is_real_data=False,
            source_dataset="SyntheticStressFixture"
        ))

        if split:
            return [s for s in samples if s.split == split.upper()]
        return samples

# TerraSentinel Research: Controlled Synthetic Sensor-Stress Benchmark

**Track:** `CONTROLLED_SYNTHETIC_SENSOR_STRESS`  
**Classification:** `FIXTURE / SENSOR_STRESS_MODEL`  
**Authority:** Synthetic Edge-Case & Stress-Testing Suite (Separate from Real-Data Validation)  
**Last Audit:** October 2026  

---

## 1. Executive Reclassification & Purpose

### 1.1 The Reclassification
Prior internal releases of TerraSentinel referred to a "5-event cross-geographic holdout benchmark" across Sylhet (Bangladesh), Red River (USA), Ebro Valley (Spain), Mekong Delta (Cambodia), and Beira (Mozambique).

**Methodological Audit Discovery:**
A rigorous internal code audit of `backend/app/research/benchmark_runner.py` revealed that these 5 events are mathematically synthesized rasters generated via NumPy distributions (`np.random.normal`, sinusoidal river equations, and deterministic geometric ground-truth masks), packaged as `SceneBundle(..., is_fixture=True)`.

**Core Governance Mandate:**
- **The synthetic benchmark is NOT deleted.** It is retained under its true scientific classification: **CONTROLLED SYNTHETIC SENSOR-STRESS BENCHMARK**.
- **The synthetic benchmark MUST NOT be cited or presented as real-world satellite generalization performance.**
- All real-world empirical claims are exclusively delegated to the independent **REAL-DATA VALIDATION TRACK** (`research/benchmarks/real-data-validation.md`).

---

## 2. Why Controlled Synthetic Stress Testing is Retained

While synthetic scenarios cannot substitute for empirical Earth observation validation, they provide essential engineering and stress-testing capabilities that real satellite data cannot isolate in a controlled single-variable manner:

1. **Extreme Physical Confounder Isolation:**
   Real satellite acquisitions rarely allow operators to systematically sweep one physical parameter while keeping all others constant. Synthetic stress scenes allow controlled injection of specific radar and optical failure modes:
   - **Gale-Force Wind Roughening (Beira Surge):** Elevates open water VV backscatter to $-15.5\text{ dB}$, deliberately violating the specular scattering threshold ($\sigma^0_{VV} < -16.0\text{ dB}$) to evaluate how fusion algorithms respond when radar collapses.
   - **Depolarizing Wetland Canopy Scattering (Mekong Delta):** Elevates VH backscatter to $-21.8\text{ dB}$ (double-bounce and volume scattering) to test volume-scattering suppression.
   - **Steep Mountain Topographic Shadows (Ebro Gorge):** Low backscatter on north-facing slopes ($> 8.5^\circ$) mimics water, stress-testing DEM slope filtering.
   - **Soil Moisture Saturation (Red River):** Lower land backscatter ($-14.2\text{ dB}$) minimizes land/water contrast.
   - **Persistent Cloud Bands (Sylhet Monsoon):** Partial optical NaN occlusions evaluate graceful degradation.

2. **Deterministic CI/CD Integration:**
   Synthetic generators require zero network dependencies, execute in $< 5\text{ ms}$, and produce identical floating-point matrices across architectures, making them ideal for rapid unit testing and regression gating of pipeline logic.

3. **Adversarial Edge-Case Generation:**
   Synthetic generators allow the creation of extreme edge cases (e.g. 100% cloud cover combined with gale-force winds) to test safety invariants and conflict detection.

---

## 3. Synthetic Benchmark Architecture

```
BenchmarkSource
    │
    ├── SyntheticStressAdapter (Track: CONTROLLED_SYNTHETIC_SENSOR_STRESS)
    │       ├── MultiEventGenerator
    │       │     ├── EVT_SYLHET_2026 (Alluvial Monsoonal Basin - Cloud Occlusion)
    │       │     ├── EVT_RED_RIVER_2026 (Saturated Agricultural Soil - Low Contrast)
    │       │     ├── EVT_EBRO_2026 (Mountain Gorge - Topographic Radar Shadows)
    │       │     ├── EVT_MEKONG_2026 (Tropical Wetland - Volume Depolarization)
    │       │     └── EVT_BEIRA_2026 (Cyclonic Surge - Wind Roughened Water)
    │       └── Stress Experiments (EXP-01 to EXP-06, Multi-Event Ablations)
```

---

## 4. Controlled Scenario Specifications

| Scenario ID | Name & Location | Synthetic Physical Challenge | Tested Subsystem Invariant |
| :--- | :--- | :--- | :--- |
| **EVT_SYLHET_2026** | Sylhet Surma Basin | Monsoonal cloud cover ($25\%$ NaN in MNDWI) + radar shadow on northern ridge | Graceful optical degradation; DEM slope suppression |
| **EVT_RED_RIVER_2026** | Red River Lowlands | Saturated clay soils reducing land backscatter to $-14.2\text{ dB}$ | Dual-pol joint threshold separation |
| **EVT_EBRO_2026** | Ebro River Valley | Steep terrain cliffs ($> 8.5^\circ$) with backscatter at $-19.2\text{ dB}$ | DEM slope thresholding ($\le 8.0^\circ$) eliminates $100\%$ of shadow false alarms |
| **EVT_MEKONG_2026** | Mekong Delta | Flooded vegetation canopy with high VH return ($-21.8\text{ dB}$) | Multi-channel cross-pol weighting |
| **EVT_BEIRA_2026** | Beira Coastal Surge | Gale wind surface roughening raising water VV to $-15.5\text{ dB}$ | Conflict surfacing (`CONFLICTING_EVIDENCE`) and optical override |

---

## 5. Distinction from Real-Data Validation

| Dimension | Controlled Synthetic Stress Benchmark | Real-Data Empirical Validation |
| :--- | :--- | :--- |
| **Data Authority** | `SyntheticStressAdapter` | `RealDatasetAdapter` (`Sen1Floods11Adapter`, etc.) |
| **Data Origin** | NumPy numerical generator (`np.random.normal`) | Public Earth Observation archives (Copernicus Sentinel-1/2) |
| **Ground Truth** | Parametric mathematical equations | Independent manual human annotations (consensus expert labeling) |
| **Scientific Claim** | Sensor stress response, edge-case failure behavior | **Real-world satellite generalization and detection accuracy** |
| **Execution Flag** | `is_real_data = False`, `is_fixture = True` | `is_real_data = True`, `is_fixture = False` |
| **Invalidity Check** | N/A (Designed as controlled parametric fixture) | **Strictly enforced:** Refuses execution if labels are circularly derived |

All real-world validation results are detailed in [`real-data-validation.md`](file:///C:/Projects/TerraSentinel/research/benchmarks/real-data-validation.md) and [`real-data-validation-report.md`](file:///C:/Projects/TerraSentinel/research/real-data-validation-report.md).

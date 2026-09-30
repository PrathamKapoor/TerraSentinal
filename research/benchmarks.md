# TerraSentinel Research: Benchmarking Framework & Research Questions

This document specifies the empirical evaluation methodology, evaluation metrics, ablation experiments, and formal research questions addressing the four levels of disaster intelligence in **TerraSentinel**.

---

## 1. Formal Research Questions (RQ1 – RQ7)

### RQ1: Multimodal Fusion Fidelity
*Does combining all-weather C-band SAR with multispectral optical imagery improve flood segmentation accuracy compared to single-modality baselines under varying cloud conditions?*
- **Hypothesis:** Under clear skies, optical MNDWI has higher boundary precision than SAR speckle; under heavy cloud cover, SAR provides uninterrupted detection where optical fails entirely; fusion provides the highest all-weather F1-score.

### RQ2: Topographic False-Positive Suppression
*To what extent does incorporating digital elevation model (DEM) slope constraints eliminate radar shadow false alarms in complex terrain?*
- **Hypothesis:** Mountainous shadows mimic low radar backscatter. Imposing $\text{slope} > 8.0^\circ$ hydrological constraints reduces false alarm rates by $> 75\%$ in non-pluvial terrain without discarding true valley inundation.

### RQ3: Infrastructure Translation Accuracy
*How accurately can continuous satellite-derived flood probabilities be translated into discrete infrastructure disruption states (OPEN, PARTIALLY_AFFECTED, BLOCKED)?*
- **Hypothesis:** Spatial intersection weighted by road segment depth and elevation profile correlates with observed road closures with an F1 score $> 0.85$.

### RQ4: Infrastructure-Aware Impact vs. Area Magnitude
*Does infrastructure-aware network reasoning provide more actionable prioritization for emergency responders than raw flooded surface area metrics?*
- **Hypothesis:** A smaller flood inundating a critical sole-access bridge severs exponentially more population and healthcare capacity than a massive flood over uninhabited wetlands. Area-only ranking misallocates resources in $> 40\%$ of simulated disaster scenarios.

### RQ5: Uncertainty Propagation
*How does sensor degradation (cloud cover, radar incidence angle) propagate through downstream graph accessibility and recommendation confidence?*
- **Hypothesis:** Propagating multi-hop Bayesian/evidential uncertainty flags high-risk interventions that would otherwise be presented as falsely confident.

### RQ6: Cross-Regional Generalization
*Can the calibrated detector and dynamic graph engine generalize to novel geographical domains without local retraining?*
- **Hypothesis:** Calibrated decibel thresholding paired with global DEM slope and OpenStreetMap vectors maintains $> 0.78$ IoU across diverse biomes (deltaic floodplains, urban coastal plains, inland river basins).

### RQ7: Counterfactual Simulation Utility
*Can graph perturbation simulation accurately estimate accessibility recovery and prioritize road/bridge reopening schedules?*
- **Hypothesis:** Counterfactual greedy edge restoration identifies the minimal set of infrastructure interventions that reconnects the maximum isolated population in minimum response time.

---

## 2. Quantitative Evaluation Metrics

### 2.1 Raster Flood Detection Metrics
- **Intersection over Union (IoU) / Jaccard Index:**
  $$\text{IoU} = \frac{|Y \cap \hat{Y}|}{|Y \cup \hat{Y}|} = \frac{\text{TP}}{\text{TP} + \text{FP} + \text{FN}}$$
- **F1-Score / Dice Coefficient:**
  $$F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}} = \frac{2 \cdot \text{TP}}{2 \cdot \text{TP} + \text{FP} + \text{FN}}$$
- **False Discovery Rate (FDR / False Positive Rate):**
  $$\text{FDR} = \frac{\text{FP}}{\text{TP} + \text{FP}}$$

### 2.2 Infrastructure & Passability Metrics
- **Passability Classification Accuracy:** Confusion matrix over {OPEN, PARTIALLY_AFFECTED, LIKELY_BLOCKED, BLOCKED}.
- **Bridge Severance Precision & Recall:** Precision of detecting single-point-of-failure bridge inundation.

### 2.3 Network & Humanitarian Impact Metrics
- **Accessibility Loss Error ($\text{MAE}_{\Delta T}$):** Mean absolute error in detour travel time estimation relative to ground verification.
- **Isolated Population Estimation Accuracy:** Percentage agreement on communities identified as completely cut off.

---

## 3. Ablation Experiments Matrix

The research benchmarking suite executes the following formal matrix:

| Experiment ID | Modalities Used | Terrain Filtering | Change Detection | Evaluation Objective |
|---|---|---|---|---|
| **EXP-01** | SAR VV only | Disabled | No | Baseline SAR single-polarization |
| **EXP-02** | SAR VV + VH | Disabled | No | Dual-pol volume scattering impact |
| **EXP-03** | SAR VV + VH | Enabled (DEM Slope) | No | Topographic shadow suppression test (RQ2) |
| **EXP-04** | Optical (S2 RGB+NIR+SWIR) | Disabled | No | Optical water index baseline under varying clouds |
| **EXP-05** | SAR + Optical (Naive Average) | Enabled | No | Simple ensemble fusion |
| **EXP-06** | SAR + Optical (Evidential Fusion) | Enabled | Yes (Bi-temporal) | **Full TerraSentinel Inundation Pipeline (RQ1)** |
| **EXP-07** | Full Pipeline + Graph Reasoning | Enabled | Yes | **Full Level 1 - Level 4 Intelligence Stack (RQ4, RQ7)** |

---

## 4. Reproducible Benchmark Runner Protocol

All benchmark experiments in TerraSentinel are driven by `backend/app/research/benchmark_runner.py`.
- No benchmark metrics are fabricated.
- Runs evaluate on deterministic test splits (e.g. Sen1Floods11 test chips and fixture scenarios).
- Outputs are saved with JSON experiment logs, confusion matrices, and calibration curves.

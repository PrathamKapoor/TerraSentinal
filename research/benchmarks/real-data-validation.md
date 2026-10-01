# TerraSentinel Research: Real-Data Empirical Validation Track

**Track:** `REAL_DATA_VALIDATION`  
**Classification:** `REAL_DATA / EMPIRICAL_VALIDATION`  
**Authority:** Primary Earth Observation Validation Standard  
**Last Audit:** October 2026  

---

## 1. Executive Summary & Validation Mandate

TerraSentinel's scientific claims regarding flood inundation detection accuracy, multimodal fusion efficacy, and cross-geographic generalization must be established on genuine Earth observation datasets featuring independent, unmanipulated sensor observations and independently generated ground-truth annotations.

**Core Rules of Engagement:**
1. **No Data Fabrication:** No synthetic, simulated, or mathematically inverted fixtures may be classified as `REAL_DATA_VALIDATION`.
2. **Independent Ground Truth:** Labels must originate from independent manual human annotation or external verified ground data. Evaluating a model against labels derived from its own decision threshold is strictly prohibited and caught by automated invalidity assertions.
3. **No Random Mixing Across Geographic Events:** Evaluation must strictly enforce event-level or geographic holdout splits (Train $\to$ Validation $\to$ Unseen Event Test).

---

## 2. Public Disaster Dataset Investigation Matrix

An exhaustive evaluation of five publicly accessible Earth observation and disaster datasets was conducted to determine suitability for real-data benchmark integration:

### 2.1 Sen1Floods11 (v1.1) — Primary Integrated Benchmark
- **Source & Citation:** Cloud to Street, NASA, Google Cloud, ESA (Bonafilia et al., 2020, *CVPR Workshops*).
- **License:** Creative Commons Attribution 4.0 International (**CC BY-4.0**).
- **Exact Data Format:** 
  - Standard GeoTIFF (`.tif`), multi-band, LZW/DEFLATE compressed.
  - Coordinate Reference System: WGS84 (`EPSG:4326`), 512 $\times$ 512 chips.
- **Actual Files:**
  - Sentinel-1 SAR: `v1.1/data/flood_events/HandLabeled/S1Hand/{Country}_{ChipID}_S1Hand.tif` (2 bands: Band 1 = VV in dB, Band 2 = VH in dB, `float32`).
  - Sentinel-2 Optical: `v1.1/data/flood_events/HandLabeled/S2Hand/{Country}_{ChipID}_S2Hand.tif` (13 bands: B1 through B12, surface reflectance, `int16`).
  - Ground Truth Labels: `v1.1/data/flood_events/HandLabeled/LabelHand/{Country}_{ChipID}_LabelHand.tif` (1 band, `int16`).
  - Baseline Otsu: `v1.1/data/flood_events/HandLabeled/S1OtsuLabelHand/{Country}_{ChipID}_S1OtsuLabelHand.tif`.
  - JRC Permanent Water: `v1.1/data/flood_events/HandLabeled/JRCWaterHand/{Country}_{ChipID}_JRCWaterHand.tif`.
- **Label Semantics:**
  - `-1`: Invalid / Cloud / No-Data (excluded from evaluation metric calculations)
  - `0`: Non-water (dry land / background)
  - `1`: Water (surface floodwater or permanent water)
- **Sensor Modalities:**
  - Sentinel-1 SAR: C-band GRD, Interferometric Wide (IW), VV + VH dual polarization.
  - Sentinel-2 Optical: MultiSpectral Instrument (MSI) 13 spectral bands.
- **Spatial Resolution:** 10 meters Ground Sampling Distance (GSD) across all resampled bands.
- **Geographic Events (11 Global Events):**
  1. *Bolivia:* Amazon Basin / Mamoré River Floods (Feb 2018)
  2. *Cambodia (Mekong):* Mekong River & Tonle Sap Basin surge (Aug 2018)
  3. *USA:* Arkansas River / Midwest Mississippi Flood (May 2019)
  4. *Spain:* Mediterranean Flash Floods / Vega Baja (Sep 2019)
  5. *India:* Bihar & Assam Brahmaputra Monsoon Flood (Aug 2016)
  6. *Ghana:* Northern Volta Basin Flooding (Sep 2018)
  7. *Nigeria:* Niger/Benue Basin Flood (Sep 2018)
  8. *Pakistan:* Sindh / Indus Basin Floods (Jun 2017)
  9. *Paraguay:* Paraguay River Basin Flood (Oct 2018)
  10. *Somalia:* Shabelle / Juba River Flash Flood (May 2018)
  11. *Sri Lanka:* Southwest Monsoon Flash Flood (May 2017)
- **Split Definitions (Official CSVs):**
  - `flood_train_data.csv`: 252 chips across 10 countries.
  - `flood_valid_data.csv`: 89 chips across 10 countries.
  - `flood_test_data.csv`: 90 chips across 10 countries.
  - `flood_bolivia_data.csv`: 15 chips from Bolivia — the official completely unseen holdout region.
- **Download Mechanism:** Direct public Google Cloud Storage bucket (`gs://sen1floods11/v1.1/`) and HTTPS mirror (`https://storage.googleapis.com/sen1floods11/v1.1/...`). No authentication or API token required.
- **Storage Size:** Full hand-labeled dataset $\approx 1.3\text{ GB}$; full dataset with weak labels $\approx 14\text{ GB}$.
- **Preprocessing Pipeline:**
  - SAR: Native float32 values are already in calibrated decibel scale ($\sigma^0\text{ dB}$). Applied Lee 5x5 speckle filter.
  - Optical: Converted bands to float reflectance; computed Modified Normalized Difference Water Index:
    $$\text{MNDWI} = \frac{\text{Green (B3)} - \text{SWIR1 (B11)}}{\text{Green (B3)} + \text{SWIR1 (B11)}}$$
  - Masking: Pixel-level boolean indexing discarding all pixels where $\text{Label} = -1$.
- **Known Limitations:** Hand-annotated labels have slight ambiguity in dense emergent vegetation; high cloud cover in some S2 scenes.

---

### 2.2 BRIGHT (Building Damage Assessment Benchmark)
- **Source & Citation:** Chen et al. (2025), University of Tokyo / RIKEN (CVPR 2025 / IEEE GRSS).
- **License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (**CC BY-NC-SA 4.0**).
- **Exact Data Format:** Paired GeoTIFF (`.tif`) and shapefile/GeoJSON building instance polygons.
- **Actual Files:** `pre-event.zip`, `post-event.zip`, `target.zip` (hosted on Zenodo and Hugging Face).
- **Labels:** 3-class building damage states: Intact (0), Damaged (1), Destroyed (2).
- **Sensor Modalities:** Bi-temporal Very-High-Resolution (VHR) Optical (WorldView/QuickBird) + High-Resolution SAR (COSMO-SkyMed / TerraSAR-X / Sentinel-1).
- **Spatial Resolution:** Sub-meter ($0.3\text{m} - 1.0\text{m}$) for optical; $1\text{m} - 3\text{m}$ for SAR.
- **Geographic Events:** 14 global disaster events (earthquake, flood, conflict).
- **Split Definitions:** Official train / validation / test splits provided on Zenodo.
- **Download Mechanism:** Manual download via Zenodo API or Hugging Face repository `ChenHongruixuan/BRIGHT`.
- **Storage Size:** $\approx 45\text{ GB}$.
- **Operational Integration Status:** Supported via `BRIGHTAdapter`. When local dataset archive is absent, adapter gracefully reports `BLOCKED: LOCAL_ARCHIVE_NOT_FOUND` rather than silently fabricating mock results.

---

### 2.3 xBD / xView2
- **Source & Citation:** Gupta et al. (2019), Defense Innovation Unit & CMU.
- **License:** Creative Commons Attribution-NonCommercial 4.0 (**CC BY-NC 4.0**).
- **Data Format:** Optical RGB GeoTIFF + JSON polygon metadata with 4-level damage scale.
- **Sensor Modalities:** VHR Maxar WorldView-2/3 (Optical only; no SAR).
- **Spatial Resolution:** $0.3\text{m} - 0.8\text{m}$.
- **Storage Size:** $\approx 35\text{ GB}$.
- **Limitations for Flood:** Optical-only; completely obscured during active flood events under cloud cover. Requires non-commercial user registration on xView2.org.

---

### 2.4 xBD-S12
- **Source & Citation:** PRS ETH Zurich (2024), Zenodo / GitHub `prs-eth/xbd-s12`.
- **License:** CC BY-NC-SA 4.0.
- **Data Format:** Co-registered Sentinel-1 and Sentinel-2 10m image pairs aligned with xBD damage polygons.
- **Storage Size:** $\approx 18\text{ GB}$ (compressed tarballs on Zenodo).
- **Role:** Demonstrates medium-resolution structural damage assessment feasibility from Copernicus open data.

---

### 2.5 FloodNet-Supervised_v1.0
- **Source & Citation:** Rahnama et al. (2021), UMBC / BinaLab.
- **License:** CC BY-NC-SA 4.0.
- **Data Format:** High-resolution UAV drone RGB imagery (`.jpg` / `.png`) with pixel-level semantic masks (10 classes).
- **Sensor Modalities:** Low-altitude drone camera (RGB only).
- **Spatial Resolution:** Extremely fine ($1.5\text{cm} - 3.0\text{cm}$).
- **Storage Size:** $\approx 8.5\text{ GB}$.
- **Limitations:** Ultra-local footprint ($< 20\text{ km}^2$ in Texas/Louisiana); grounded during storms; unsuited for regional basin-wide satellite monitoring.

---

## 3. Smallest Scientifically Useful Subset Protocol

To balance scientific rigor, zero-leakage holdout discipline, and continuous reproducibility without multi-gigabyte downloads, TerraSentinel curates a standardized **11-Chip Multi-Event Benchmark Subset** from Sen1Floods11 v1.1:

```
Total Chips: 11 (512 x 512 pixels each = 2,883,584 total pixels evaluated)
Total Data Volume: ~15.2 MB
Band Assets per Chip:
  - S1Hand.tif (2 bands: VV, VH float32)
  - S2Hand.tif (13 bands: B1-B12 int16)
  - LabelHand.tif (1 band: -1, 0, 1 int16)
```

### Event-Level Geographic Holdout Distribution

| Split Stage | Geographic Event & Country | Biome / Typology | Chip Identifiers | Role & Evaluation Focus |
| :--- | :--- | :--- | :--- | :--- |
| **TRAIN / REGIONAL** | **USA** (Arkansas River Basin) | Flatland agricultural river basin | `USA_994009`<br>`USA_66026` | Regional baseline threshold calibration |
| **TRAIN / REGIONAL** | **Spain** (Vega Baja / Segura River) | Mediterranean valley with complex terrain | `Spain_5923267`<br>`Spain_7786924` | Steep valley radar shadow resistance |
| **TRAIN / REGIONAL** | **India** (Brahmaputra Basin) | Monsoonal alluvial floodplain | `India_285297`<br>`India_1072277` | High-turbidity sedimented water |
| **VALIDATION** | **Mekong** (Cambodia / Tonle Sap) | Tropical wetland floodplain forest | `Mekong_1149855`<br>`Mekong_977338` | Emergent vegetation & volume scattering |
| **UNSEEN EVENT TEST**| **Bolivia** (Mamoré / Amazonian Basin) | Lowland Amazonian river surge | `Bolivia_103757`<br>`Bolivia_129334`<br>`Bolivia_195474` | **Zero-leakage out-of-domain holdout evaluation** |

---

## 4. Benchmark Source & Adapter Architecture

```
BenchmarkSource (ABC)
    │
    ├── SyntheticStressAdapter
    │       └── 5 Synthetic Stress Scenarios (Track: CONTROLLED_SYNTHETIC_SENSOR_STRESS)
    │
    └── RealDatasetAdapter (ABC)
            │
            ├── Sen1Floods11Adapter
            │       ├── Fetches / loads authentic Sentinel-1 & Sentinel-2 GeoTIFFs
            │       ├── Exposes normalized SceneBundle + valid pixel mask
            │       ├── Verifies cryptographic SHA-256 provenance checksums
            │       └── Computes IoU, Dice, F1, Precision, Recall on valid pixels
            │
            ├── BRIGHTAdapter (BLOCKED when local archive is absent)
            │
            └── RealFloodDatasetAdapter (Unified Factory)
```

---

## 5. Baselines Evaluated Under Real Data

Every baseline evaluated on the real-data track is classified under its precise algorithmic origin:

1. **Baseline A: SAR-Only Thresholding (`HEURISTIC`)**
   - Condition: $(\sigma^0_{VV} < -16.0\text{ dB}) \land (\sigma^0_{VH} < -23.0\text{ dB})$
2. **Baseline B: Optical-Only Thresholding (`HEURISTIC`)**
   - Condition: $(\text{MNDWI} > 0.0)$ on valid unclouded pixels.
3. **Baseline C: Multimodal Consensus (`HEURISTIC`)**
   - Condition: SAR water $\lor$ Optical water.
4. **Baseline D: TerraSentinel Dempster-Shafer Evidential Fusion (`HEURISTIC`)**
   - Fuses SAR backscatter, optical MNDWI, and DEM slope prior, surfacing conflict whenever SAR and optical evidence diverge.
5. **Baseline E: SimpleUNet Adapter (`UNTRAINED / ADAPTER`)**
   - Heuristically initialized convolutional kernel comparator. Classified explicitly as `UNTRAINED / ADAPTER` (hand-crafted spatial filters, NOT claimed as pretrained weights).

---

## 6. Circularity & Benchmark Invalidity Guard

The benchmark runner enforces automated integrity assertions:
$$\text{If } \text{GroundTruth} \equiv (\sigma^0_{VV} < T) \implies \text{RAISE } \text{BenchmarkInvalidityError}$$
If an evaluation detects that ground-truth labels were generated from the evaluated threshold rule, or if a fixture is passed to the real runner, the runner **fails immediately** and refuses to register the execution as `REAL_DATA_VALIDATION`.

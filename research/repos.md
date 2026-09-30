# TerraSentinel Research: External Repositories Evaluation & Audit

This document provides a comprehensive, research-grade audit of external open-source repositories, foundation models, GIS engines, and operational frameworks relevant to **TerraSentinel** (*Evidence-Grounded Satellite Intelligence for Flood Disaster Response*).

Each repository is audited across 11 standardized dimensions:
1. **Repository Name & URL**
2. **Purpose**
3. **Relevant Subsystem**
4. **License**
5. **Activity / Currentness**
6. **Dependencies**
7. **Compute Requirements**
8. **Direct Reusability**
9. **How it Informs TerraSentinel**
10. **Known Limitations & Failure Modes**
11. **Architectural Abstraction / Adaptation Strategy**

---

## 1. Flood Detection & Earth Observation (EO)

### 1.1 Sen1Floods11
- **Repository:** `cloudtostreet/Sen1Floods11`
- **URL:** https://github.com/cloudtostreet/Sen1Floods11
- **Purpose:** Benchmark dataset and baseline deep learning models for flood water segmentation using paired Sentinel-1 C-band SAR and Sentinel-2 optical imagery.
- **Relevant Subsystem:** Tier 1 Ingestion, Flood Detection Adapter, Benchmark Runner.
- **License:** CC BY-4.0 (Data) / MIT (Code).
- **Activity / Currentness:** Seminal benchmark (2020); maintained as a standard reference in remote sensing.
- **Dependencies:** PyTorch, Torchvision, GDAL, Rasterio, NumPy.
- **Compute Requirements:** Low to moderate (CPU inference for calibrated thresholding; single GPU for U-Net/DeepLabV3 fine-tuning).
- **Direct Reusability:** High for evaluation protocols, SAR backscatter threshold baselines ($\sigma^0_{VV} < -16.0\text{ dB}$, $\sigma^0_{VH} < -23.0\text{ dB}$), and multi-event chip splits.
- **How it Informs TerraSentinel:** Informs TerraSentinel's calibrated physical-statistical dual-pol thresholding adapter and convolutional U-Net adapter; provides benchmark baselines for IoU/Dice comparison.
- **Known Limitations & Failure Modes:** Hand-labeled chips contain label noise in heavily vegetated flood zones; weakly labeled chips suffer from cloud contamination in optical masks; single-chip random splitting causes spatial autocorrelation leakage.
- **Architectural Abstraction:** Wrapped under `BaseModelAdapter` as `DualPolSARTerrainAdapter` and `UNetFloodAdapter` with deterministic CPU/GPU fallbacks.

### 1.2 Microsoft AI for Earth: Flood Inundation Mapping (ai4g-flood)
- **Repository:** `microsoft/ai4g-flood`
- **URL:** https://github.com/microsoft/ai4g-flood
- **Purpose:** Cloud-native pipeline for large-scale flood inundation mapping using multi-temporal Sentinel-1 GRD imagery.
- **Relevant Subsystem:** SAR Preprocessing, Bi-Temporal Change Detection.
- **License:** MIT.
- **Activity / Currentness:** Stable reference repository for Azure AI for Earth applications.
- **Dependencies:** Python, NumPy, SciPy, Rasterio, Azure Planetary Computer SDK.
- **Compute Requirements:** Low (CPU-friendly raster differencing and Otsu thresholding).
- **Direct Reusability:** High for Lee speckle filtering algorithms, log-ratio amplitude differencing, and morphological cleaning.
- **How it Informs TerraSentinel:** Directly informs the Lee adaptive filter ($5 \times 5$ window) in `preprocessing.py` and the bi-temporal change detector (`change_detector.py`) differentiating permanent water from active crisis inundation.
- **Known Limitations & Failure Modes:** Does not integrate digital elevation models for radar shadow suppression; lacks road network and critical infrastructure routing; does not propagate uncertainty.
- **Architectural Abstraction:** Pure-Python NumPy/SciPy adaptation without hard dependency on Azure-specific cloud packages.

### 1.3 NASA-IMPACT & IBM: Prithvi-EO-2.0
- **Repository:** `NASA-IMPACT/Prithvi-EO-2.0`
- **URL:** https://github.com/NASA-IMPACT/Prithvi-EO-2.0
- **Purpose:** First-of-its-kind geospatial foundation model (300M and 600M parameters) pretrained on 4.2 million global HLS time-series tiles with spatiotemporal and geographic coordinate embeddings.
- **Relevant Subsystem:** Multimodal Foundation Model Backbone, Semantic Water Segmentation.
- **License:** Apache 2.0.
- **Activity / Currentness:** Highly active (2024–2026), official NASA/IBM open science initiative.
- **Dependencies:** PyTorch >= 2.0, Timm, Hugging Face `transformers`, TorchGeo.
- **Compute Requirements:** High (requires 16GB+ VRAM GPU for inference; multi-GPU distributed cluster for fine-tuning).
- **Direct Reusability:** Medium (model weights and tokenizer available on Hugging Face; architecture is public).
- **How it Informs TerraSentinel:** Informs the temporal embedding and patch-based feature representation strategy; serves as the foundation model target in TerraSentinel's extensible adapter interface.
- **Known Limitations & Failure Modes:** Excessive compute and memory footprint prevents zero-setup local deployment on standard laptops or edge disaster command stations; primarily optical HLS pretraining with limited native SAR microwave physical grounding.
- **Architectural Abstraction:** Encapsulated behind `BaseModelAdapter`; local deployments use the calibrated statistical dual-pol engine or lightweight U-Net, while cloud endpoints can bind to Prithvi-EO-2.0 via Hugging Face.

### 1.4 TerraTorch (TorchGeo Geospatial Foundation Model Toolkit)
- **Repository:** `torchgeo/terratorch`
- **URL:** https://github.com/torchgeo/terratorch
- **Purpose:** Unified PyTorch-based framework for fine-tuning, benchmarking, and evaluating Earth observation foundation models (Prithvi, SatMAE, Scale-MAE) on downstream tasks.
- **Relevant Subsystem:** Research Benchmarking, Model Registry.
- **License:** Apache 2.0.
- **Activity / Currentness:** Active development by the TorchGeo and ESA/NASA community.
- **Dependencies:** PyTorch, TorchGeo, Lightning, Timm.
- **Compute Requirements:** Moderate to high depending on model backbone.
- **Direct Reusability:** High for benchmark evaluation schemas and dataset registry patterns.
- **How it Informs TerraSentinel:** Informs the modular separation of backbones, neck decoders, and task-specific downstream heads (segmentation vs classification).
- **Known Limitations & Failure Modes:** Complex dependency graph with frequent breaking changes across PyTorch Lightning releases; tight coupling to specific geospatial raster formats.
- **Architectural Abstraction:** TerraSentinel adopts TerraTorch's metric calculation patterns (macro-IoU, Dice, calibration curves) in `backend/app/research/benchmark_runner.py` without requiring the entire heavy dependency tree.

---

## 2. Change Detection & Damage Assessment

### 2.1 ChangeMamba
- **Repository:** `ChenHongruixuan/ChangeMamba`
- **URL:** https://github.com/ChenHongruixuan/ChangeMamba
- **Purpose:** Linear-complexity remote sensing change detection using State Space Models (Mamba / SSM) with Cross-Scan Modules (CSM) for bi-temporal image interaction.
- **Relevant Subsystem:** Temporal Change Detection, Building Damage Assessment.
- **License:** Apache 2.0.
- **Activity / Currentness:** Active (2024–2026), published in IEEE TGRS / CVPR workshops.
- **Dependencies:** PyTorch, `mamba-ssm`, `causal-conv1d`, OpenCV.
- **Compute Requirements:** Moderate GPU (CUDA compute capability >= 7.0 required for selective scan hardware acceleration).
- **Direct Reusability:** Conceptual; direct CUDA C++ kernels cannot build easily on Windows without Visual Studio C++ build tools.
- **How it Informs TerraSentinel:** Informs the bi-temporal feature interaction theory—specifically how pre-disaster baseline imagery should modulate post-disaster inundation confidence rather than simply subtracting raw rasters.
- **Known Limitations & Failure Modes:** Difficult compilation on Windows 11; requires dedicated GPU; fails on severe geometric misregistration between pre- and post-scenes.
- **Architectural Abstraction:** Abstracted into `change_detector.py` using vectorized NumPy temporal matrix transitions (`PERMANENT_WATER`, `NEWLY_FLOODED`, `RECEDED`, `UNCHANGED_LAND`).

### 2.2 BRIGHT (Building Damage Assessment with High-Resolution Optical and SAR)
- **Repository:** `ChenHongruixuan/BRIGHT`
- **URL:** https://github.com/ChenHongruixuan/BRIGHT
- **Purpose:** Open-access multimodal benchmark dataset and evaluation suite providing paired VHR optical and SAR imagery covering over 380,000 building instances across 14 global disaster events.
- **Relevant Subsystem:** Building Damage Assessment, Cross-Event Generalization Benchmark.
- **License:** Open Access / CC BY-NC-SA 4.0.
- **Activity / Currentness:** Active benchmark (2025–2026).
- **Dependencies:** Python, PyTorch, GeoPandas, Shapely.
- **Compute Requirements:** Moderate to high for instance-level building polygon processing.
- **Direct Reusability:** High for structural damage classification schemes (Intact, Minor Damage, Major Damage, Destroyed) and optical-SAR discordance test cases.
- **How it Informs TerraSentinel:** Directly informs TerraSentinel's building damage spatial correlation in `infrastructure.py` and the 4-tier damage classification schema (`DamageState`).
- **Known Limitations & Failure Modes:** Very high resolution (0.3m–1m) is rarely available in real-time during early disaster response; public Sentinel-1/2 satellites operate at 10m–30m resolution.
- **Architectural Abstraction:** TerraSentinel supports both sub-meter building footprint polygons (from OSM or BRIGHT) and coarse grid cells with proportional damage ratios.

### 2.3 xView2 Challenge & First-Place Solutions
- **Repositories:**
  - `DIUx-xView/xView2_first_place` (https://github.com/DIUx-xView/xView2_first_place)
  - `BloodAxe/xView2-Solution` (https://github.com/BloodAxe/xView2-Solution)
  - `prs-eth/xbd-s12` (https://github.com/prs-eth/xbd-s12)
- **Purpose:** World-standard benchmarks and winning ensemble architectures for building footprint extraction and joint damage localization/classification on the xBD dataset.
- **Relevant Subsystem:** Structural Damage Assessment, Spatial Polygonization.
- **License:** MIT / Apache 2.0.
- **Activity / Currentness:** Canonical disaster response benchmark (2019–present).
- **Dependencies:** PyTorch, Albumentations, PretrainedModels, GDAL.
- **Compute Requirements:** High (massive ResNeXt/EfficientNet ensembles for competition scoring).
- **Direct Reusability:** High for two-stage localization-classification pipeline design and ordinal damage scoring.
- **How it Informs TerraSentinel:** Demonstrates that localization (is this a building?) and classification (how damaged is it?) must be decoupled to prevent false-positive artifacts.
- **Known Limitations & Failure Modes:** xBD is 100% optical VHR; completely fails during cloud-obscured flood events without SAR radar data; ensembles require excessive inference latency (> 30s per tile).
- **Architectural Abstraction:** TerraSentinel incorporates xBD's Joint Damage Scale while maintaining real-time spatial joins (< 100ms) with OpenStreetMap building polygons.

---

## 3. Multimodal & Foundation Models

### 3.1 DisasterM3
- **Repository:** `Junjue-Wang/DisasterM3`
- **URL:** https://github.com/Junjue-Wang/DisasterM3
- **Purpose:** Large-scale multi-hazard, multi-sensor (optical + SAR), multi-task remote sensing vision-language dataset containing 123,000 instruction pairs across 36 historical disasters (NeurIPS 2025).
- **Relevant Subsystem:** Multimodal Reasoning, Evidence Explainability.
- **License:** CC BY-4.0.
- **Activity / Currentness:** State-of-the-art (NeurIPS 2025).
- **Dependencies:** PyTorch, Transformers, Hugging Face Hub, LLaVA.
- **Compute Requirements:** Very High (requires 40GB+ VRAM for fine-tuning 7B–13B parameter VLMs).
- **Direct Reusability:** Conceptual and benchmark reference for structuring multimodal reasoning prompts and evidence-grounded responses.
- **How it Informs TerraSentinel:** Validates TerraSentinel's design principle that natural language summaries in disaster management must be strictly grounded in verified geographic and sensor evidence rather than hallucinated by generative models.
- **Known Limitations & Failure Modes:** Large vision-language models frequently hallucinate non-existent infrastructure damage; token generation introduces high latency unsuitable for immediate tactical triage.
- **Architectural Abstraction:** In TerraSentinel, the structured Evidence DAG and Decision Receipt represent the ground truth; language explanations are strictly deterministic translations of the verified graph relations.

### 3.2 Prithvi-CAFE (Complementary Adaptive Fusion Encoder)
- **Repository:** `Sk-2103/Prithvi-CAFE`
- **URL:** https://github.com/Sk-2103/Prithvi-CAFE
- **Purpose:** Complementary Adaptive Fusion Encoder pairing a pretrained Prithvi transformer backbone with a parallel CNN residual branch for high-resolution flood inundation mapping.
- **Relevant Subsystem:** Multimodal Feature Fusion, Edge Boundary Refinement.
- **License:** Apache 2.0 / MIT.
- **Activity / Currentness:** Cutting-edge research (2025–2026).
- **Dependencies:** PyTorch, Timm, TerraTorch.
- **Compute Requirements:** High (8GB–16GB VRAM GPU).
- **Direct Reusability:** Medium (architectural inspiration for dual-branch evidential combination).
- **How it Informs TerraSentinel:** Proves that combining transformer global context with local convolutional attention significantly reduces water boundary bleeding along road embankments.
- **Known Limitations & Failure Modes:** Lacks explicit conflict detection when optical and radar signals diverge; high memory footprint during multi-scene inference.
- **Architectural Abstraction:** Conceptual integration into TerraSentinel's multi-resolution fusion and speckle preservation heuristics.

### 3.3 THOR & thor_terratorch_ext
- **Repository:** `FM4CS/thor_terratorch_ext`
- **URL:** https://github.com/FM4CS/thor_terratorch_ext
- **Purpose:** Extension module for TerraTorch integrating the THOR (Transformer-based foundation model for Heterogeneous Observation and Resolution) backbone supporting Sentinel-1, Sentinel-2, and Sentinel-3 cross-sensor pretraining.
- **Relevant Subsystem:** Multi-Sensor Tokenization & Registration.
- **License:** Apache 2.0.
- **Activity / Currentness:** Active European Space Agency (ESA Φ-lab) project.
- **Dependencies:** TerraTorch, PyTorch.
- **Compute Requirements:** High.
- **Direct Reusability:** Medium for multi-sensor channel alignment.
- **How it Informs TerraSentinel:** Validates the handling of heterogeneous ground sampling distances (10m optical vs 20m SAR vs 30m DEM) without spatial distortion.
- **Known Limitations & Failure Modes:** Heavy dependency chain; experimental API status.
- **Architectural Abstraction:** Resampling and spatial grid alignment handled cleanly in pure Python/NumPy in `preprocessing.py`.

---

## 4. Operational Flood & Disaster Response Systems

### 4.1 FloodLens
- **Repository:** `chris-netizen/floodlens`
- **URL:** https://github.com/chris-netizen/floodlens
- **Purpose:** OpenStreetMap-driven rapid flood impact mapping tool estimating affected healthcare facilities, schools, and roads following catastrophic rainfall events.
- **Relevant Subsystem:** Infrastructure Correlation, Spatial Join Engine.
- **License:** MIT.
- **Activity / Currentness:** Community disaster tool.
- **Dependencies:** Python, GeoPandas, OSMnx, Streamlit.
- **Compute Requirements:** Low (CPU-based vector GIS).
- **Direct Reusability:** High for OSM tag taxonomy (`amenity=hospital`, `amenity=school`, `highway=primary`).
- **How it Informs TerraSentinel:** Demonstrates the essential need for immediate translation from flooded surface polygons to concrete facility lists.
- **Known Limitations & Failure Modes:** Naive geometric overlay without network graph routing; treats any road touching water as 100% blocked; cannot detect whether cut-off communities have alternative detour routes.
- **Architectural Abstraction:** TerraSentinel advances beyond FloodLens by implementing full dynamic multigraph impedance, Dijkstra detour calculation, and island component isolation.

### 4.2 DisaVu
- **Repository:** `SrzStephen/DisaVu`
- **URL:** https://github.com/SrzStephen/DisaVu
- **Purpose:** Interactive disaster visualization interface combining satellite building damage detection with emergency resource allocation dashboards.
- **Relevant Subsystem:** Operational Frontend, Triage UI.
- **License:** MIT.
- **Activity / Currentness:** Disaster response prototype.
- **Dependencies:** React, Mapbox GL, Flask.
- **Compute Requirements:** Client-side WebGL rendering.
- **Direct Reusability:** High for UI/UX interaction paradigms (damage heatmaps, filter controls).
- **How it Informs TerraSentinel:** Inspired TerraSentinel's dark-mode tactical command console, split-screen timeline comparisons, and interactive layer controls.
- **Known Limitations & Failure Modes:** Frontend visual effects disconnected from deterministic backend proof; hardcoded mock findings; no auditable decision receipts.
- **Architectural Abstraction:** TerraSentinel's frontend workbench is strictly bound to live, verified backend REST APIs and cryptographic receipts.

### 4.3 Soteria-AI
- **Repository:** `Soteria-ai/Soteria`
- **URL:** https://github.com/Soteria-ai/Soteria
- **Purpose:** AI-assisted natural disaster mapping framework designed for rapid situational assessment and aerial search-and-rescue coordination.
- **Relevant Subsystem:** Search-and-Rescue Prioritization.
- **License:** MIT.
- **Activity / Currentness:** Research prototype.
- **Dependencies:** Python, PyTorch, OpenCV, Flask.
- **Compute Requirements:** Moderate.
- **Direct Reusability:** Medium for rescue priority heuristics.
- **How it Informs TerraSentinel:** Highlights the importance of life-safety metrics (elderly populations, emergency room access) in priority ranking.
- **Known Limitations & Failure Modes:** Lacks evidential provenance and conflict reasoning; opaque scoring functions.
- **Architectural Abstraction:** Formulated into TerraSentinel's explainable, multi-factor Criticality Equation with transparent parameter decomposition.

### 4.4 Nepal Flood Map & Additional Disaster Tools
- **Repositories:**
  - `ShresthaRajat/nepal-flood-map` (https://github.com/ShresthaRajat/nepal-flood-map)
  - `Minha-ak/Flood-Mapping` (https://github.com/Minha-ak/Flood-Mapping)
  - `MeawMan/floodrisk` (https://github.com/MeawMan/floodrisk)
- **Purpose:** Regional flood extent mapping workflows utilizing Google Earth Engine (GEE) JavaScript and Python APIs for monsoon flood monitoring in the Himalayas and Southeast Asia.
- **Relevant Subsystem:** Sentinel-1 GRD ingestion, Threshold Calibration.
- **License:** MIT / Open Access.
- **Activity / Currentness:** Actively cited regional tools (2024–2026).
- **Dependencies:** Google Earth Engine API, Folium, Geemap.
- **Compute Requirements:** GEE cloud-side execution.
- **Direct Reusability:** High for regional backscatter threshold ranges across Asian deltaic floodplains.
- **How it Informs TerraSentinel:** Provided calibrated baseline parameters for South Asian monsoon floods (Sylhet, Bangladesh fixture).
- **Known Limitations & Failure Modes:** Heavy vendor lock-in to proprietary Google Earth Engine cloud infrastructure; cannot run fully air-gapped or on local standalone workstations.
- **Architectural Abstraction:** TerraSentinel implements pure-Python local equivalents (`acquisition.py`, `preprocessing.py`, STAC client) that execute without GEE account dependencies.

---

## 5. SAR, GIS & Infrastructure Network Toolkits

### 5.1 World Bank GOST_SAR
- **Repository:** `worldbank/GOST_SAR`
- **URL:** https://github.com/worldbank/GOST_SAR
- **Purpose:** World Bank Global Geospatial Operations Support Team (GOST) toolkit for automated flood extraction and population exposure calculation using Sentinel-1 SAR.
- **Relevant Subsystem:** SAR Radiometric Calibration, Population Exposure Overlay.
- **License:** MIT.
- **Activity / Currentness:** Operational humanitarian standard.
- **Dependencies:** GDAL, Rasterio, NumPy, GeoPandas.
- **Compute Requirements:** Low to moderate CPU.
- **Direct Reusability:** High for radiometric calibration formulas ($10 \cdot \log_{10}(\text{amplitude}^2)$) and population raster masking.
- **How it Informs TerraSentinel:** Informs the physical calibration equations in `backend/app/services/preprocessing.py` and the humanitarian population exposure aggregation.
- **Known Limitations & Failure Modes:** Relies on legacy Python 3.7/3.8 GDAL bindings that break on modern Windows Python 3.13; lacks graph-theoretic routing or isolation modeling.
- **Architectural Abstraction:** Refactored into pure-Python Shapely 2.0 and NumPy vectorization in `preprocessing.py`.

### 5.2 OSMnx (Boeing, 2017)
- **Repository:** `gboeing/osmnx`
- **URL:** https://github.com/gboeing/osmnx
- **Purpose:** Open-source Python package to download, model, analyze, and visualize street networks from OpenStreetMap using NetworkX.
- **Relevant Subsystem:** Transport Network Graph Construction, Shortest-Path Routing.
- **License:** MIT.
- **Activity / Currentness:** Highly maintained gold standard for urban network analysis.
- **Dependencies:** NetworkX, GeoPandas, Shapely, PyProj.
- **Compute Requirements:** Moderate CPU/RAM for large metropolitan networks.
- **Direct Reusability:** High for multigraph topology design, edge impedance formulas, and coordinate keying.
- **How it Informs TerraSentinel:** Directly informs `DynamicNetworkEngine` in `network_engine.py`, which constructs a flood-aware multigraph with dynamic travel time impedances.
- **Known Limitations & Failure Modes:** Heavy OSM downloads can timeout during active crises when Overpass servers are overloaded; naive graph models fail to account for partial road inundation speeds.
- **Architectural Abstraction:** TerraSentinel integrates a cached local fixture and synthetic road network generator alongside live Overpass queries, ensuring 100% test reliability offline.

### 5.3 TiTiler & STAC Toolkits (pystac-client, stackstac)
- **Repositories:**
  - `developmentseed/titiler` (https://github.com/developmentseed/titiler)
  - `stac-utils/pystac-client` (https://github.com/stac-utils/pystac-client)
  - `gjoseph92/stackstac` (https://github.com/gjoseph92/stackstac)
- **Purpose:** Cloud-optimized GeoTIFF dynamic tile server and STAC (SpatioTemporal Asset Catalog) API search and xarray stacking tools.
- **Relevant Subsystem:** Cloud Data Ingestion, Dynamic Raster Streaming.
- **License:** MIT / Apache 2.0.
- **Activity / Currentness:** Modern cloud-native geospatial industry standards.
- **Dependencies:** FastAPI, Pydantic, Rasterio, Pystac, Xarray.
- **Compute Requirements:** Low client-side, scales in cloud container runtimes.
- **Direct Reusability:** High for STAC query patterns and dynamic map tile streaming.
- **How it Informs TerraSentinel:** Defines TerraSentinel's `STACAcquisitionClient` in `acquisition.py`, querying Microsoft Planetary Computer and AWS Earth Search STAC endpoints for Sentinel-1/2 assets.
- **Known Limitations & Failure Modes:** Requires active Internet connection and valid cloud API tokens; fails in disconnected field command posts without fixture fallback.
- **Architectural Abstraction:** TerraSentinel provides automatic fallback to local high-fidelity calibrated fixtures (`sylhet_monsoon_2026`) when external STAC endpoints are unreachable or unauthenticated, clearly tagged with `[FIXTURE MODE]`.

### 5.4 FloodNet-Supervised_v1.0 (BinaLab)
- **Repository:** `BinaLab/FloodNet-Supervised_v1.0`
- **URL:** https://github.com/BinaLab/FloodNet-Supervised_v1.0
- **Purpose:** Post-Hurricane Harvey high-resolution aerial imagery dataset with dense pixel-level annotations for flooded roads, submerged buildings, and passability conditions.
- **Relevant Subsystem:** Infrastructure Damage Modeling, High-Resolution Validation.
- **License:** CC BY-NC-SA 4.0.
- **Activity / Currentness:** Canonical UAV flood disaster benchmark.
- **Dependencies:** Python, PyTorch, OpenCV.
- **Compute Requirements:** Moderate.
- **Direct Reusability:** High for passability severity threshold validation (e.g. at what water depth does a paved road transition from `PARTIALLY_AFFECTED` to `BLOCKED`).
- **How it Informs TerraSentinel:** Validates TerraSentinel's road passability thresholds ($> 50\%$ segment overlap or $> 0.25$ bridge overlap $\implies$ `BLOCKED`).
- **Known Limitations & Failure Modes:** UAV drone imagery covers localized corridors ($< 5\text{ km}^2$); does not scale to regional river basin disasters without satellite fusion.
- **Architectural Abstraction:** Used as empirical ground truth for fine-tuning road passability decay curves.

---

## 6. Synthesis & Architectural Lineage

| External Repository | Subsystem in TerraSentinel | License Compliance | Key Architectural Insight Reused | TerraSentinel Key Contribution Beyond Prior Art |
| :--- | :--- | :--- | :--- | :--- |
| **Sen1Floods11** | Detection & Baseline Evaluation | MIT / CC BY-4.0 | Calibrated dB thresholds & holdout splits | Extends from raw pixel mask to full infrastructure graph and isolation consequence |
| **ai4g-flood** | Preprocessing & Bi-Temporal | MIT | Lee speckle filter & log-ratio differencing | Eliminates cloud dependencies; integrates DEM slope physics to suppress radar shadows |
| **Prithvi-EO-2.0** | Foundation Model Adapter | Apache 2.0 | Spatiotemporal patch embeddings | Abstracted behind lightweight interface with zero-GPU CPU fallback for field triage |
| **ChangeMamba** | Change Detection Theory | Apache 2.0 | Linear complexity state-space transitions | Pure-Python vectorized implementation without fragile Windows C++ compilation |
| **BRIGHT** | Structural Damage Assessment | CC BY-NC-SA 4.0 | 4-tier damage scales (Intact to Destroyed) | Correlates building damage with community isolation and emergency shelter capacity |
| **xView2 Solutions**| Damage Scoring | MIT | Decoupled localization and damage classification | Vectorized spatial join deduplication (`unary_union`) preventing double-counting |
| **DisasterM3** | Evidence Grounding & Trust | CC BY-4.0 | Multi-sensor disaster instruction schemas | Replaces generative hallucinations with a deterministic Evidence DAG and SHA-256 Receipts |
| **FloodLens** | Infrastructure Overlay | MIT | OSM critical facility taxonomy | Upgrades from static GIS buffers to dynamic multigraph Dijkstra routing and detour deltas |
| **World Bank GOST** | SAR Calibration & Demography | MIT | Amplitude-to-dB conversion & pop exposure | Pure-Python Shapely 2.0 engine compatible with modern Python 3.13 runtimes |
| **OSMnx** | Network Graph Engine | MIT | Multigraph topology & edge impedance | Dynamic impedance modulation based on satellite inundation + counterfactual perturbation |
| **TiTiler / STAC** | Satellite Data Ingestion | MIT | STAC catalog queries & asset alignment | Resilient offline fixture fallback mode with explicit operational classification |

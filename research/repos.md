# TerraSentinel Research: External Repositories Evaluation

This document provides a thorough analysis of open-source repositories, models, GIS toolkits, and remote sensing frameworks relevant to **TerraSentinel** (Evidence-Grounded Satellite Intelligence for Flood Disaster Response).

---

## 1. Flood Detection & Earth Observation (EO)

### 1.1 Sen1Floods11
- **Repository:** https://github.com/cloudtostreet/Sen1Floods11
- **Organization / Authors:** Cloud to Street (Bonafilia et al., 2020)
- **Role in TerraSentinel:** Benchmark baseline dataset and thresholding/segmentation algorithms for Sentinel-1 C-band SAR and Sentinel-2 optical imagery.
- **Key Methodologies:** Dual-pol (VV, VH) C-band SAR backscatter thresholding (Otsu, Bmax, Lee filtered) alongside U-Net, FCN, and DeepLabV3+ architectures.
- **Direct Reusability:** High for evaluation protocols, thresholding heuristics (-16.0 dB VV, -23.0 dB VH), and benchmark split definitions.
- **Dependencies:** PyTorch, Torchvision, GDAL / Rasterio.
- **License:** CC BY-4.0 (data), MIT (code).
- **Compute Requirements:** Moderate (CPU inference for Otsu/dual-pol heuristics; single GPU for U-Net validation).
- **Limitations:** Primarily 2D pixel-level masks; does not model infrastructure correlation, network disruption, or causal isolation.

### 1.2 Microsoft AI4G Flood
- **Repository:** https://github.com/microsoft/ai4g-flood
- **Organization:** Microsoft AI for Good Research Lab
- **Role in TerraSentinel:** SAR-based flood inundation mapping using multi-temporal Sentinel-1 GRD imagery.
- **Key Methodologies:** Amplitude difference, threshold estimation, and morphological post-processing for operational disaster mapping.
- **Direct Reusability:** High for SAR preprocessing pipelines, speckle filtering, and change detection formulas.
- **Dependencies:** Python, NumPy, SciPy, Rasterio/GDAL.
- **License:** MIT.
- **Limitations:** Focuses on pure raster segmentation; lacks graph-level routing and human verification mechanisms.

### 1.3 NASA-IMPACT Prithvi-EO-2.0 & TerraTorch
- **Repositories:**
  - https://github.com/NASA-IMPACT/Prithvi-EO-2.0
  - https://github.com/torchgeo/terratorch
- **Organization:** NASA IMPACT, IBM Research, TorchGeo team
- **Role in TerraSentinel:** Earth Observation foundation model backbones (ViT-based masked autoencoder architectures pretrained on Harmonized Landsat Sentinel-2 and multi-temporal Sentinel-1/2 data).
- **Key Methodologies:** Spatiotemporal representation learning across optical and SAR bands. Downstream heads for surface water segmentation and burn scar detection.
- **Direct Reusability:** Architectural adapter reference. Heavyweight foundation models (300M+ parameters) are abstracted behind adapter interfaces with lightweight CPU/local GPU fallback implementations.
- **Dependencies:** PyTorch >= 2.0, Timm, TorchGeo, HuggingFace Hub.
- **License:** Apache 2.0.
- **Limitations:** High GPU VRAM requirement (16GB+ VRAM for fine-tuning/full inference); not suitable as a hard blocker for lightweight edge/field response.

---

## 2. Change Detection & Damage Assessment

### 2.1 ChangeMamba
- **Repository:** https://github.com/ChenHongruixuan/ChangeMamba
- **Authors:** Chen et al. (2024)
- **Role in TerraSentinel:** State Space Model (SSM / Mamba) for spatio-temporal remote sensing change detection.
- **Key Methodologies:** Selective structured state space models for linear complexity spatial-temporal feature interaction between bi-temporal optical/SAR scenes.
- **Direct Reusability:** Conceptual reference for temporal feature differencing and adapter design.
- **Dependencies:** Mamba-ssm, PyTorch, Causal-conv1d.
- **License:** Apache 2.0.
- **Limitations:** Highly sensitive to CUDA-specific C++ extensions; requires custom Windows C++ compilation. Abstracted via modular change detection interface in TerraSentinel.

### 2.2 BRIGHT & DisasterM3
- **Repositories:**
  - https://github.com/ChenHongruixuan/BRIGHT
  - https://github.com/Junjue-Wang/DisasterM3
- **Role in TerraSentinel:** Multi-hazard multimodal disaster benchmark and vision-language disaster reasoning dataset.
- **Key Methodologies:** Bi-temporal SAR and optical pairs capturing building collapses, flooded roadways, and landslide blockages. DisasterM3 incorporates textual damage descriptions with spatial bounding boxes.
- **Direct Reusability:** Direct schema reference for multimodal damage states (`INTACT`, `MINOR`, `MAJOR`, `DESTROYED`) and verification findings.
- **License:** CC BY-NC-SA / MIT.

### 2.3 xBD / xView2 (DIUx-xView)
- **Repository:** https://github.com/DIUx-xView/xView2_first_place / https://github.com/BloodAxe/xView2-Solution
- **Role in TerraSentinel:** Industry-standard building damage assessment taxonomy and polygon damage classification.
- **Key Methodologies:** Pre-disaster building localization combined with post-disaster Siamese damage classification (ResNet/EfficientNet backbones).
- **Direct Reusability:** Direct schema alignment with four standard FEMA/xBD damage states.
- **License:** Apache 2.0 / MIT.

---

## 3. Geospatial Network & Routing Analytics

### 3.1 OSMnx
- **Repository:** https://github.com/gboeing/osmnx
- **Author:** Geoff Boeing (2017-2024)
- **Role in TerraSentinel:** Graph extraction and topological modeling of road networks from OpenStreetMap.
- **Key Methodologies:** Converts street networks into directed NetworkX multi-graphs preserving geometry, length, speed, and impedance attributes.
- **Direct Reusability:** Foundational for network routing, dynamic edge impedance updating, and Dijkstra path calculation.
- **Dependencies:** NetworkX, Shapely, PyProj.
- **License:** MIT.

### 3.2 World Bank GOST_SAR
- **Repository:** https://github.com/worldbank/GOST_SAR
- **Organization:** World Bank Geospatial Operations Support Team (GOST)
- **Role in TerraSentinel:** Operational SAR processing for disaster damage and transport impact assessment in developing nations.
- **Key Methodologies:** Calibrated C-band processing, radiometric terrain correction, and population exposure overlays.
- **Direct Reusability:** High for operational passability thresholds and population vulnerability integration.
- **License:** MIT.

---

## 4. Operational Ingestion & Cloud-Native STAC

### 4.1 PySTAC & PySTAC-Client
- **Repository:** https://github.com/stac-utils/pystac-client
- **Role in TerraSentinel:** Spatio-Temporal Asset Catalog (STAC) search and discovery for Sentinel-1, Sentinel-2, and NASADEM assets on public AWS Earth Search and Microsoft Planetary Computer endpoints.
- **Direct Reusability:** Core ingestion adapter for real satellite scene retrieval.
- **License:** Apache 2.0.

### 4.2 TiTiler
- **Repository:** https://github.com/developmentseed/titiler
- **Role in TerraSentinel:** Dynamic raster tile server for Cloud Optimized GeoTIFFs (COGs).
- **Direct Reusability:** Reference architecture for on-the-fly map rendering of raster bands.
- **License:** MIT.

---

## 5. Humanitarian & Community Mapping Projects

- **DisaVu (https://github.com/SrzStephen/DisaVu):** Visual analytics for disaster response with interactive damage filters.
- **FloodLens (https://github.com/chris-netizen/floodlens):** Flood exposure calculator combining hazard layers with demographic data.
- **Soteria (https://github.com/Soteria-ai/Soteria):** AI-powered situational awareness for search and rescue operations.
- **FloodNet (https://github.com/BinaLab/FloodNet-Supervised_v1.0):** High-resolution UAV flood dataset categorizing flooded roads and stranded vehicles.

---

## 6. Synthesis for TerraSentinel Architecture

TerraSentinel integrates the best operational practices from these projects into a cohesive 4-level intelligence system:
1. **Detection:** Adopts Sen1Floods11 and AI4G calibrated SAR dual-polarization thresholding + optical MNDWI verification.
2. **Infrastructure:** Standardizes on xBD building damage and OSM road hierarchy.
3. **Network & Routing:** Leverages NetworkX/OSMnx dynamic graph topologies to model road passability and isolation.
4. **Trust & Governance:** Introduces the novel **Evidence Graph**, **Uncertainty Propagation**, and cryptographically auditable **Decision Receipts**, addressing the critical provenance gap left unfilled by existing research repositories.

# TerraSentinel Research: Disaster Datasets & Remote Sensing Data Registry

This document provides a comprehensive, research-grade audit of Earth observation, infrastructure vector, elevation, and demographic datasets evaluated and integrated into **TerraSentinel** (*Evidence-Grounded Satellite Intelligence for Flood Disaster Response*).

Each dataset is audited across 12 standardized dimensions:
1. **Dataset Name**
2. **Source & Organization**
3. **License & Data Governance**
4. **Geographic Coverage**
5. **Event Count & Temporal Extent**
6. **Sensor Modalities & Spectral Bands**
7. **Spatial Resolution (Ground Sampling Distance - GSD)**
8. **Label Types & Annotation Fidelity**
9. **Temporal Structure (Single-scene vs Bi-temporal vs Time-series)**
10. **Intended Task**
11. **Known Limitations & Bias Profiles**
12. **Operational Role in TerraSentinel**

---

## 1. Primary Earth Observation & Flood Benchmarks

### 1.1 Sen1Floods11
- **Dataset Name:** Sen1Floods11
- **Source & Organization:** Cloud to Street, NASA, Google Cloud, ESA (Bonafilia et al., 2020)
- **License & Data Governance:** Creative Commons Attribution 4.0 International (CC BY-4.0).
- **Geographic Coverage:** Global (11 disaster regions spanning 6 continents: USA, Bangladesh, Bolivia, Cambodia, Ghana, India, Nigeria, Pakistan, Paraguay, Somalia, Spain).
- **Event Count & Temporal Extent:** 11 historic flood events between 2016 and 2019; 4,831 non-overlapping $512 \times 512$ image chips.
- **Sensor Modalities & Spectral Bands:**
  - Sentinel-1 SAR: C-band GRD, IW (Interferometric Wide swath), VV and VH polarizations.
  - Sentinel-2 Optical: Multispectral L1C/L2A (13 bands: B1 through B12, including Green B3, NIR B8, SWIR B11).
  - Topography: SRTM 30m Digital Elevation Model (DEM).
- **Spatial Resolution:** 10 meters per pixel (resampled for pixel-level alignment).
- **Label Types & Annotation Fidelity:**
  - 446 hand-labeled chips with rigorous quality control (split into 252 train, 89 val, 105 test).
  - 4,385 weakly-labeled chips generated using automated thresholding heuristics on Sentinel-2 optical scenes.
  - Pixel classes: Land (0), Water (1), Cloud/Invalid (-1).
- **Temporal Structure:** Single crisis snapshot with paired co-registered optical/SAR/DEM scenes.
- **Intended Task:** Supervised pixel-level semantic segmentation of surface floodwaters.
- **Known Limitations & Bias Profiles:** Hand-labeled chips exhibit label ambiguity in emergent wetland vegetation; weakly labeled chips inherit cloud shadow artifacts; lacks road network, bridge, or healthcare facility annotations.
- **Operational Role in TerraSentinel:** Provides core empirical calibration thresholds ($\sigma^0_{VV} < -16.0\text{ dB}$, $\sigma^0_{VH} < -23.0\text{ dB}$) and reference split protocols for `backend/app/research/benchmark_runner.py`.

### 1.2 xBD (xView2 Disaster Dataset)
- **Dataset Name:** xBD
- **Source & Organization:** Defense Innovation Unit (DIU), Maxar Technologies, Carnegie Mellon University (Gupta et al., 2019)
- **License & Data Governance:** Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).
- **Geographic Coverage:** Global (15 countries across North America, South America, Europe, Asia, and Oceania).
- **Event Count & Temporal Extent:** 19 natural disaster events (floods, hurricanes, earthquakes, tsunamis, wildfires, volcanic eruptions) between 2011 and 2019; covering 45,362 km².
- **Sensor Modalities & Spectral Bands:** Very-High-Resolution (VHR) optical imagery from Maxar WorldView-2, WorldView-3, and GeoEye-1 (Red, Green, Blue, Near-Infrared).
- **Spatial Resolution:** 0.3 to 0.8 meters per pixel.
- **Label Types & Annotation Fidelity:** Over 850,000 polygon building footprints annotated with the 4-tier Joint Damage Scale:
  - `No Damage` (Intact structural envelope)
  - `Minor Damage` (Superficial wall/roof impact, partial water inundation)
  - `Major Damage` (Significant structural failure, deep flooding)
  - `Destroyed` (Complete collapse or washed away)
- **Temporal Structure:** Bi-temporal pairs (strictly co-registered pre-disaster baseline scene and post-disaster crisis scene).
- **Intended Task:** Joint building localization and 4-class structural damage assessment.
- **Known Limitations & Bias Profiles:** Optical-only; completely unsuited for real-time flood monitoring during active cloud cover or storms; high-resolution Maxar imagery is proprietary and unavailable for real-time open-source operational triage.
- **Operational Role in TerraSentinel:** Establishes the 4-tier damage classification schema implemented in `schemas.py` and `infrastructure.py`, adapting the criteria to satellite inundation depth and building footprint intersection ratios.

### 1.3 BRIGHT: Building Damage Assessment Benchmark
- **Dataset Name:** BRIGHT (Building damage assessment dataset using veRy-hIGH-resoluTion optical and SAR imagery)
- **Source & Organization:** Chen et al. (2025), University of Tokyo / RIKEN.
- **License & Data Governance:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0).
- **Geographic Coverage:** 14 global disaster zones covering flood, earthquake, and war impact areas.
- **Event Count & Temporal Extent:** 14 major events; over 380,000 building instances.
- **Sensor Modalities & Spectral Bands:** Paired VHR Optical (0.5m–1m) and airborne/satellite SAR (X-band and C-band).
- **Spatial Resolution:** Sub-meter to 3 meters.
- **Label Types & Annotation Fidelity:** High-precision building polygon instance masks labeled with structural damage severity states under both optical and radar viewing geometries.
- **Temporal Structure:** Bi-temporal and cross-modal pairs (Pre-optical, Post-optical, Post-SAR).
- **Intended Task:** Cross-modal and all-weather building damage assessment.
- **Known Limitations & Bias Profiles:** Heavy computational requirements for training; limited geographical extent per event tile.
- **Operational Role in TerraSentinel:** Validates TerraSentinel's multimodal building damage assessment logic, confirming that combining SAR backscatter dips with optical spectral indices significantly outperforms single-modality damage estimation.

### 1.4 FloodNet-Supervised_v1.0
- **Dataset Name:** FloodNet-Supervised_v1.0
- **Source & Organization:** BinaLab, University of Maryland, Baltimore County (Rahnama et al., 2021)
- **License & Data Governance:** CC BY-NC-SA 4.0.
- **Geographic Coverage:** Texas and Louisiana, USA (Hurricane Harvey impact corridor).
- **Event Count & Temporal Extent:** 1 major hurricane/flood disaster (2017); 2,343 high-resolution drone image tiles ($4000 \times 3000$).
- **Sensor Modalities & Spectral Bands:** Ultra-high-resolution aerial RGB imagery captured via Small Unmanned Aerial Systems (sUAS / drones).
- **Spatial Resolution:** Extremely fine (1.5 to 3.0 cm per pixel).
- **Label Types & Annotation Fidelity:** Dense pixel-level semantic segmentation across 10 classes: Flooded Road, Non-Flooded Road, Flooded Building, Non-Flooded Building, Water, Pool, Vehicle, Tree, Grass, Other.
- **Temporal Structure:** Single post-disaster crisis flight survey.
- **Intended Task:** UAV-based post-flood damage assessment and road passability segmentation.
- **Known Limitations & Bias Profiles:** Limited geographic coverage (< 20 km²); UAV flights are grounded during high winds and torrential rain; unable to provide regional basin-scale situational awareness.
- **Operational Role in TerraSentinel:** Provides high-fidelity empirical ground truth on the physical relationship between road inundation extent and passability failure states, establishing TerraSentinel's 50% road overlap and 25% bridge overlap thresholds.

---

## 2. Contextual Geospatial & Infrastructure Datasets

### 2.1 OpenStreetMap (OSM) Global Highway & Critical Facility Vectors
- **Dataset Name:** OpenStreetMap Global Infrastructure Extract
- **Source & Organization:** OpenStreetMap Foundation (OSMF) / Humanitarian OpenStreetMap Team (HOT).
- **License & Data Governance:** Open Database License (ODbL 1.0).
- **Geographic Coverage:** Worldwide planetary coverage.
- **Event Count & Temporal Extent:** Continuous crowd-sourced mapping updated in real-time.
- **Sensor Modalities & Spectral Bands:** Vector GIS (Points, LineStrings, MultiPolygons).
- **Spatial Resolution:** Centimeter-to-meter topological accuracy.
- **Label Types & Annotation Fidelity:**
  - Transport Network: `highway=motorway`, `trunk`, `primary`, `secondary`, `tertiary`, `residential`, `bridge=yes`.
  - Healthcare & Emergency Services: `amenity=hospital`, `amenity=clinic`, `amenity=doctors`, `amenity=pharmacy`, `emergency=fire_station`, `amenity=police`.
  - Shelter & Community Hubs: `amenity=school`, `amenity=community_centre`, `amenity=place_of_worship`, `social_facility=shelter`.
  - Building Footprints: `building=yes`, `building=residential`, `levels=N`.
- **Temporal Structure:** Dynamic version-controlled vector ledger.
- **Intended Task:** Open geospatial routing, navigation, and humanitarian asset mapping.
- **Known Limitations & Bias Profiles:** Completeness varies geographically: dense in urban North America/Europe, but contains unmapped tertiary tracks or missing bridge attributes in rural Global South regions; requires tracking `mapped_coverage` vs true ground completeness.
- **Operational Role in TerraSentinel:** Powers the entire Tier 3 Dynamic Network Engine (`network_engine.py`) and Infrastructure Spatial Join Service (`infrastructure.py`), providing the physical road polylines and hospital points that convert raw flood polygons into life-saving accessibility routes.

### 2.2 Global High-Resolution Population Density (WorldPop / HRSL)
- **Dataset Name:** WorldPop Global Gridded Population Data / High Resolution Settlement Layer (HRSL)
- **Source & Organization:** WorldPop Research Group (University of Southampton) & Meta / Columbia CIESIN.
- **License & Data Governance:** Creative Commons Attribution 4.0 International (CC BY-4.0).
- **Geographic Coverage:** Global (over 240 countries and territories).
- **Event Count & Temporal Extent:** Annual demographic updates (2015–2025).
- **Sensor Modalities & Spectral Bands:** Raster geotiff representing estimated human population count per grid cell.
- **Spatial Resolution:** 1 arc-second (~30 meters at equator) for HRSL; 3 arc-seconds (~100 meters) for WorldPop.
- **Label Types & Annotation Fidelity:** Continuous floating-point population count estimates disaggregated via machine learning and census data.
- **Temporal Structure:** Annual static demographic baseline.
- **Intended Task:** Population exposure estimation, epidemiological modeling, and disaster risk assessment.
- **Known Limitations & Bias Profiles:** Does not capture dynamic real-time diurnal human movement (e.g. daytime commercial workers vs nighttime residential dwellers); census disaggregation can underestimate seasonal migrant or refugee settlements.
- **Operational Role in TerraSentinel:** Feeds the `Community` schema and `isolation_engine.py`, allowing the system to aggregate exact isolated population numbers trapped in cut-off island components and scale priority rankings logarithmically.

### 2.3 NASA NASADEM & SRTM Global Digital Elevation Models
- **Dataset Name:** NASADEM / Shuttle Radar Topography Mission (SRTM v3.0)
- **Source & Organization:** NASA, USGS, National Geospatial-Intelligence Agency (NGA).
- **License & Data Governance:** Public Domain (US Government Work).
- **Geographic Coverage:** Global landmass between $60^\circ\text{ N}$ and $56^\circ\text{ S}$ latitude (> 99% of global population).
- **Event Count & Temporal Extent:** Baseline radar interferometry mission with ongoing radiometric reprocessing.
- **Sensor Modalities & Spectral Bands:** C-band Spaceborne Radar Interferometry elevation raster (meters above WGS84 ellipsoid / EGM96 geoid).
- **Spatial Resolution:** 1 arc-second (~30 meters).
- **Label Types & Annotation Fidelity:** Continuous integer/float elevation values with void-filled hydrological conditioning.
- **Temporal Structure:** Static baseline terrain model.
- **Intended Task:** Topographic slope, aspect, and hydrological drainage modeling.
- **Known Limitations & Bias Profiles:** Radar penetration over dense forest canopies reflects tree canopy height rather than bare earth ground surface; horizontal resolution of 30m may smooth narrow engineered levees or ditches.
- **Operational Role in TerraSentinel:** Processed via Sobel gradient spatial convolution in `preprocessing.py` to calculate true physical terrain slope (degrees), eliminating radar shadows on slopes $> 8^\circ$ and constraining floodwater accumulation under gravity.

---

## 3. Dual-Track Benchmark Dataset Registry

To prevent confounding sensor-stress unit testing with empirical satellite accuracy, TerraSentinel maintains two distinct benchmark tracks:

### 3.1 Track 1: Real-Data Empirical Multi-Event Benchmark (Sen1Floods11 v1.1)
Authentic Earth-observation GeoTIFFs (Sentinel-1 SAR float32, Sentinel-2 MSI int16) with independent consensus hand-annotated ground truth. Out-of-domain event holdout:

| Event ID | Event & Country | Biome / Typology | Sensor Modalities | Benchmark Split | Ground Truth Source | Manifest Assets |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **EVT_BOLIVIA_MAMORE_2018** | Mamoré River, Bolivia | Lowland Amazonian River Surge | S1 SAR (VV/VH) + S2 MSI | **UNSEEN TEST** | Consensus hand-annotated labels (Cloud to Street) | `Bolivia_103757`, `Bolivia_129334`, `Bolivia_195474` |
| **EVT_MEKONG_CAMBODIA_2018** | Tonle Sap, Cambodia | Tropical Wetland & Floodplain | S1 SAR (VV/VH) + S2 MSI | **VALIDATION** | Consensus hand-annotated labels (Cloud to Street) | `Mekong_1149855`, `Mekong_977338` |
| **EVT_USA_MIDWEST_2019** | Arkansas River, USA | Agricultural Riverine Flatlands | S1 SAR (VV/VH) + S2 MSI | **TRAIN** | Consensus hand-annotated labels (Cloud to Street) | `USA_994009`, `USA_66026` |
| **EVT_SPAIN_VEGA_BAJA_2019** | Segura River, Spain | Mediterranean Valley Relief | S1 SAR (VV/VH) + S2 MSI | **TRAIN** | Consensus hand-annotated labels (Cloud to Street) | `Spain_5923267`, `Spain_7786924` |
| **EVT_INDIA_BRAHMAPUTRA_2016** | Brahmaputra, India | Monsoonal Alluvial Basin | S1 SAR (VV/VH) + S2 MSI | **TRAIN** | Consensus hand-annotated labels (Cloud to Street) | `India_285297`, `India_1072277` |

### 3.2 Track 2: Controlled Synthetic Sensor-Stress Suite
Parametric sensor stress models isolating specific physical failure modes. *Notice: Parametric fixtures; not claimed as real-world satellite generalization.*

| Scenario ID | Scenario Name & Typology | Injected Physical Confounder | Stress Track | Role |
| :--- | :--- | :--- | :---: | :--- |
| **EVT_SYLHET_2026** | Sylhet Surma Basin (Alluvial) | Monsoonal cloud cover ($25\%$ NaN in MNDWI) | `SYNTHETIC_STRESS` | Graceful optical degradation test |
| **EVT_RED_RIVER_2026**| Red River Lowlands (Clay soils) | Saturated soils reducing land/water contrast | `SYNTHETIC_STRESS` | Dual-pol separability stress |
| **EVT_EBRO_2026** | Ebro Gorge (Steep mountain relief) | Mountain radar shadows ($> 8.5^\circ$) | `SYNTHETIC_STRESS` | DEM slope suppression verification |
| **EVT_MEKONG_2026** | Mekong Delta (Tropical wetland) | Emergent canopy volume depolarization | `SYNTHETIC_STRESS` | Cross-pol weighting verification |
| **EVT_BEIRA_2026** | Beira Coastal Surge (Cyclonic) | Gale wind water surface roughening | `SYNTHETIC_STRESS` | Conflict detection & override test |

---

## 4. Synthesis & Dataset Compliance Matrix

| Dataset | Data Origin | License Compliance | Export Controlled? | Reusable for Commercial / Operational? | Subsystem Binding in TerraSentinel |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Sen1Floods11** | ESA / NASA / Cloud to Street | CC BY-4.0 | No | Yes | `Sen1Floods11Adapter`, `benchmark_runner.py` (Real Track) |
| **xBD** | Maxar / CMU | CC BY-NC 4.0 | No | Research Only (Commercial uses OSM adaptation) | `schemas.py` (`DamageState` taxonomy) |
| **BRIGHT** | U-Tokyo / RIKEN | CC BY-NC-SA 4.0 | No | Research Only | `BRIGHTAdapter` (Structural damage reference) |
| **FloodNet** | UMBC / BinaLab | CC BY-NC-SA 4.0 | No | Research Only | Road passability threshold calibration |
| **OpenStreetMap**| OSM Community | ODbL 1.0 | No | Yes (with attribution) | `infrastructure.py`, `network_engine.py` |
| **WorldPop** | U-Southampton | CC BY-4.0 | No | Yes | `isolation_engine.py`, `priority_engine.py` |
| **NASADEM** | NASA / USGS | Public Domain | No | Yes | `preprocessing.py` (30m slope derivation) |
| **Synthetic Suite**| TerraSentinel | MIT | No | Yes | `SyntheticStressAdapter` (Sensor stress testing) |

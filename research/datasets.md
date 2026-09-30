# TerraSentinel Research: Datasets & Earth Observation Catalogs

This document catalogs Earth-observation satellite data sources, benchmark flood datasets, digital elevation models, population grids, and contextual infrastructure layers utilized by or integrated into **TerraSentinel**.

---

## 1. Satellite & Remote Sensing Modalities

### 1.1 Sentinel-1 SAR (Synthetic Aperture Radar)
- **Sensor:** C-band SAR (5.405 GHz) onboard Sentinel-1A and Sentinel-1B.
- **Product Type:** Level-1 Ground Range Detected (GRD), Interferometric Wide (IW) swath mode.
- **Spatial Resolution:** 10m pixel spacing (20m spatial resolution).
- **Polarizations:** Dual-polarization:
  - **VV (Vertical transmit, Vertical receive):** Highly sensitive to surface roughness; provides strong specular contrast for open water.
  - **VH (Vertical transmit, Horizontal receive):** Sensitive to volume scattering (vegetation, urban structures); crucial for discriminating flooded vegetation.
- **Temporal Revisit:** 6 to 12 days depending on latitude and constellation status.
- **STAC Catalogs:**
  - AWS Earth Search: `sentinel-1-grd`
  - Microsoft Planetary Computer: `sentinel-1-grd`
- **Calibration Formula:**
  $$\sigma^0\,(\text{dB}) = 10 \cdot \log_{10}(\text{DN}^2 / A_i^2) + \text{offset}$$
  where $\text{DN}$ is the digital number and $A_i$ is the calibration lookup table value.

### 1.2 Sentinel-2 MSI (MultiSpectral Instrument)
- **Sensor:** 13-band optical pushbroom radiometer onboard Sentinel-2A and Sentinel-2B.
- **Product Type:** Level-2A (Bottom-of-Atmosphere surface reflectance).
- **Relevant Spectral Bands:**
  - Band 2 (Blue - 490 nm, 10m)
  - Band 3 (Green - 560 nm, 10m)
  - Band 4 (Red - 665 nm, 10m)
  - Band 8 (NIR - 842 nm, 10m)
  - Band 11 (SWIR-1 - 1610 nm, 20m)
  - Band 12 (SWIR-2 - 2190 nm, 20m)
  - Scene Classification Layer (SCL) for cloud, snow, and shadow masking.
- **Spectral Indices:**
  - **MNDWI (Modified Normalized Difference Water Index):**
    $$\text{MNDWI} = \frac{\text{Green} - \text{SWIR-1}}{\text{Green} + \text{SWIR-1}} = \frac{B03 - B11}{B03 + B11}$$
  - **NDVI (Normalized Difference Vegetation Index):**
    $$\text{NDVI} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}} = \frac{B08 - B04}{B08 + B04}$$
- **STAC Catalogs:**
  - AWS Earth Search: `sentinel-2-l2a`
  - Microsoft Planetary Computer: `sentinel-2-l2a`

### 1.3 Digital Elevation Models (DEM)
- **Source:** NASADEM (30m) / Copernicus GLO-30 DEM (30m).
- **Derived Topographic Variables:**
  - **Slope (Degrees):**
    $$\text{Slope} = \arctan\left(\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}\right)$$
  - **HAND (Height Above Nearest Drainage):** Hydrological topography indicating normalized elevation above river channels.
- **Role in Flood Mapping:** Standing water cannot accumulate on steep inclines. Any low-SAR-backscatter pixel on terrain with $\text{slope} > 8^\circ$ is flagged as a radar shadow false positive rather than inundation.

---

## 2. Benchmark Datasets for Model Evaluation & Calibration

### 2.1 Sen1Floods11
- **Provider:** Cloud to Street / NASA / Radiant Earth.
- **Coverage:** 11 historic flood events across 6 continents (Bolivia, Cambodia, Ghana, India, Pakistan, Somalia, Spain, USA, Sri Lanka, Paraguay, Vietnam).
- **Total Chips:** 4,831 chips ($512 \times 512$ pixels).
- **Splits:**
  - Train: 2,520 chips
  - Validation: 890 chips
  - Test: 1,421 chips
- **Labels:** Quality-controlled hand-labeled ground truth for flood extents.
- **Metrics Evaluated:** Intersection over Union (IoU) and F1-score for permanent water vs floodwater.

### 2.2 xBD (xView2)
- **Provider:** Defense Innovation Unit (DIU) & Carnegie Mellon University.
- **Coverage:** Over 850,000 building polygons across 19 global disasters (hurricanes, floods, earthquakes, wildfires).
- **Labels:** 4 damage levels:
  - 0: `no-damage` (`INTACT`)
  - 1: `minor-damage`
  - 2: `major-damage`
  - 3: `destroyed`

### 2.3 FloodNet
- **Provider:** Bina Lab / UMBC.
- **Coverage:** High-resolution post-hurricane aerial imagery (Hurricane Harvey).
- **Labels:** 10 semantic classes including flooded road, non-flooded road, flooded building, non-flooded building, and standing water.

---

## 3. Contextual Geospatial Infrastructure & Demographic Data

### 3.1 OpenStreetMap (OSM)
- **Source:** Geofabrik extracts & Overpass API.
- **Entities Ingested:**
  - **Roads / Highways:** `highway` tags: `motorway`, `trunk`, `primary`, `secondary`, `tertiary`, `residential`, `unclassified`.
  - **Bridges:** `bridge=yes` associated with highway ways.
  - **Critical Facilities:**
    - Hospitals & Clinics: `amenity=hospital`, `amenity=clinic`
    - Emergency Services: `amenity=fire_station`, `amenity=police`
    - Evacuation Shelters & Schools: `amenity=shelter`, `amenity=school`
  - **Buildings:** Polygons with `building=*`.

### 3.2 High-Resolution Gridded Population
- **Source:** WorldPop / Meta High Resolution Settlement Layer (HRSL) / Kontur Population.
- **Resolution:** 100m grid cell population density.
- **Usage:** Spatial aggregation of residents residing in flooded zones and cut-off network subgraphs.

---

## 4. Deterministic Fixture Bundles (Offline / Demo Mode)

To guarantee 100% reproducible execution in offline, credential-free, or bandwidth-constrained environments, TerraSentinel bundles realistic, calibrated fixture scenarios:
1. **Scenario 1: Sylhet / Surma River Basin Mega-Flood (Bangladesh/India)**
   - Pre-event baseline + peak monsoon flood.
   - Dual-pol SAR backscatter arrays, S2 optical MNDWI, Copernicus DEM, and 450+ OSM road segments + 12 critical medical facilities.
2. **Scenario 2: Hurricane Inland Fluvial Flooding (Tar River / North Carolina)**
   - Fluvial inundation severing arterial bridges, isolating rural communities from regional hospitals.

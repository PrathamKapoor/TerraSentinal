# TerraSentinel End-to-End System Execution Flow (flow.d)

This document specifies the observable execution flow, algorithmic logic, data dependencies, branching conditions, and service orchestrations of **TerraSentinel** (Evidence-Grounded Satellite Intelligence for Flood Disaster Response).

---

## 1. High-Level Flow Architecture

```
[OPERATOR / FRONTEND WORKBENCH]
        │
        │ HTTP POST /api/v1/events (Name, AOI GeoJSON, Dates, HazardType)
        ▼
[FASTAPI API GATEWAY / EVENT SERVICE]
        │
        │ Validate schema, validate AOI polygon (EPSG:4326), compute area bounds
        │ Persist Event in Database (Status: PENDING)
        │
        ▼ HTTP POST /api/v1/events/{id}/runs (Trigger Pipeline)
[PIPELINE ORCHESTRATOR / RUN WORKER]
        │
        ├── 1. Acquisition Service (STAC API / Earth Search / Local Fixture)
        │       ├── Sentinel-1 SAR GRD (VV, VH backscatter rasters)
        │       ├── Sentinel-2 MSI Optical (B2, B3, B4, B8, B11, B12 + Cloud Mask)
        │       └── NASADEM / Copernicus DEM (Elevation + Slope)
        │
        ├── 2. Preprocessing & Alignment Engine
        │       ├── SAR Decibel Conversion: dB = 10 * log10(val + 1e-7)
        │       ├── Lee Speckle Filtering & Multilooking
        │       ├── Optical Cloud Masking (QA60 / SCL)
        │       └── Normalized Difference Indices (MNDWI, NDWI, NDVI)
        │
        ├── 3. Flood Segmentation & Detection Engine
        │       ├── Model Adapter: AI4G SAR Dual-Pol Thresholding & U-Net
        │       ├── Terrain Slope Inundation Constraint: Filter slope > 8°
        │       └── Polygonization: SciPy/Shapely contour tracing to GeoJSON polygons
        │
        ├── 4. Temporal Change Detection Engine
        │       ├── Pre-event baseline water vs. Post-event inundated water
        │       └── Classify: UNCHANGED_WATER, NEWLY_FLOODED, RECEDED, UNCHANGED_LAND
        │
        ├── 5. Multimodal Evidence Fusion
        │       ├── Bayesian/Dempster-Shafer rule combining SAR + Optical + DEM
        │       ├── Preserve source-specific evidence weights
        │       └── Flag CONFLICTING_EVIDENCE (e.g. SAR inundated, Optical dry)
        │
        ├── 6. Contextual Geospatial Ingestion
        │       ├── Overpass OSM Highway Network (motorway, trunk, primary, secondary)
        │       ├── OSM Buildings & Critical Facilities (hospitals, schools, fire stations)
        │       └── High-Resolution Gridded Population (e.g., WorldPop/HRSL density)
        │
        ├── 7. Infrastructure Spatial Correlation & Passability
        │       ├── Spatial intersection of flood polygons with roads & bridges
        │       ├── Derive passability: OPEN, PARTIALLY_AFFECTED, LIKELY_BLOCKED, BLOCKED
        │       └── Classify building damage: INTACT, MINOR, MAJOR, DESTROYED
        │
        ├── 8. Dynamic Network Analysis & Accessibility Engine
        │       ├── Construct NetworkX directed multi-graph with travel impedances
        │       ├── Sever edges matching BLOCKED / LIKELY_BLOCKED passability
        │       ├── Compute all-pairs shortest paths to Critical Facilities
        │       └── Detect disconnected subgraphs (Isolated Communities)
        │
        ├── 9. Population & Isolation Consequence Engine
        │       ├── Aggregate population trapped in cut-off components
        │       ├── Calculate Accessibility Loss Index (travel time delta to nearest care)
        │       └── Compute Criticality Score for severed bridge/road segments
        │
        ├── 10. Uncertainty Propagation & Priority Engine
        │       ├── Combine satellite quality * model confidence * infrastructure criticality
        │       ├── Rank operational findings: CRITICAL, HIGH, MEDIUM, LOW, VERIFY
        │       └── Queue verification items for human ground truth
        │
        └── 11. Decision Receipt Generation & State Persistence
                ├── Generate immutable JSON Decision Receipt with SHA-256 evidence hash
                ├── Persist all layers, findings, and relations to database
                └── Mark Event Run: COMPLETED
```

---

## 2. Detailed Step-by-Step Observable Execution Sequence (Steps 1 to 40)

### Step 1: User Initiates an Event
- Operator in the web UI enters the **Mission Control** screen.
- Operator clicks "New Disaster Event".
- Operator specifies:
  - Event Name (e.g. `Cyclone Remal - Lower Bengal Inundation`)
  - Hazard Type: `FLOOD`
  - Geographic Area of Interest (AOI): drawn as a polygon on the map or uploaded as GeoJSON.
  - Time Range: Pre-event baseline date (`2026-05-15`) and Post-event crisis date (`2026-05-28`).

### Step 2: Event Enters the Backend
- Frontend sends a standard HTTP payload via `fetch` or Axios to the API gateway.

### Step 3: API Endpoint Receiving the Request
- Endpoint: `POST /api/v1/events`
- Headers: `Content-Type: application/json`
- Payload: `EventCreateRequest` matching Pydantic schema.

### Step 4: Validation
- Pydantic schema validation executes:
  - AOI must be a valid GeoJSON Polygon or MultiPolygon.
  - Coordinate reference system must be WGS84 (`EPSG:4326`).
  - Polygon boundaries must not self-intersect (checked via `shapely.is_valid`).
  - Bounding box area must be within allowed limits (e.g. max 5,000 km² per operational run).
  - Pre-event date must precede post-event date.

### Step 5: Database Entities Created
- In SQLite / PostgreSQL database:
  - An `Event` record is inserted:
    `id = "evt_remal_20260528"`, `name = "..."`, `aoi_geojson = "..."`, `status = "CREATED"`, `created_at = UTC_NOW`.
- Event record is returned to client with HTTP 201 Created.

### Step 6: Background Job Created
- Operator or client calls `POST /api/v1/events/{id}/runs`.
- System creates an `AnalysisRun` record:
  `id = "run_01j7... "`, `event_id = "evt_remal_20260528"`, `status = "QUEUED"`, `stage = "INITIALIZING"`.
- Fast response HTTP 202 Accepted returns the `run_id`.
- The background task is dispatched asynchronously to the `PipelineOrchestrator`.

### Step 7: How the Processing Pipeline Starts
- In the background worker, `PipelineOrchestrator.execute_run(run_id: str)` is triggered.
- Status is updated to `status = "RUNNING"`, `stage = "ACQUISITION"`.

### Step 8: Initial Function Invoked
- `AcquisitionService.acquire_event_data(event: Event, run: AnalysisRun)` is called.

### Step 9: Nested Functions Called
- `AcquisitionService` calls:
  - `STACClientAdapter.search_scenes(aoi, date_range, collections=["sentinel-1-grd", "sentinel-2-l2a"])`
  - Fallback check: If credentials missing or network disabled, `AcquisitionService` cleanly branches to `FixtureCatalogAdapter.load_scene(event_id, aoi)` with explicit warning log: `[FIXTURE_MODE] Using calibrated deterministic scene bundle`.
  - Downloads / loads SAR VV+VH rasters, Optical RGB+NIR+SWIR rasters, and DEM raster tile.

### Step 10: Transformations to the Data
- Radiometric calibration of SAR raw values to decibels ($dB$):
  $$dB = 10 \cdot \log_{10}(\text{amplitude}^2 + 10^{-7})$$
- Speckle suppression: $3 \times 3$ or $5 \times 5$ median/Lee filter applied to reduce SAR speckle noise.
- Normalization: Scale optical bands $[0, 10000] \to [0.0, 1.0]$.
- Resampling / Reprojection: Reproject DEM and Sentinel-2 bands to match the Sentinel-1 10-meter spatial grid using bilinear interpolation.

### Step 11: How Satellite Data is Acquired
- Via PySTAC Client querying Planetary Computer or AWS Earth Search STAC endpoints:
  - `stac_client.search(bbox=bbox, datetime=date_range, collections=["sentinel-1-grd"])`
  - Retrieves asset URLs for `vv` and `vh` polarizations, acquisition timestamps, and orbit passes (Ascending/Descending).
  - Optical STAC query checks cloud cover metadata: `eo:cloud_cover < 20%`. If cloud cover is high, Optical quality is flagged `DEGRADED / CLOUD_OBSCURED`.

### Step 12: Preprocessing
- Cloud masking: Sentinel-2 Scene Classification Layer (SCL) or QA60 band identifies pixels classified as cloud / cloud shadow; these are masked with `NaN` / zero weight in optical analysis.
- Modified Normalized Difference Water Index (MNDWI):
  $$\text{MNDWI} = \frac{\text{Green} - \text{SWIR}}{\text{Green} + \text{SWIR}} = \frac{B03 - B11}{B03 + B11}$$
- Normalized Difference Vegetation Index (NDVI) for false-positive vegetation filtering:
  $$\text{NDVI} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}} = \frac{B08 - B04}{B08 + B04}$$

### Step 13: Flood Inference Execution
- Invokes `FloodDetectorService.detect_flood(sar_vv, sar_vh, optical_mndwi, dem_slope)`.
- Algorithmic Decision Rule:
  - Base SAR criterion: Water exhibits low backscatter. Pixels with $\text{VV} < -16.0\,\text{dB}$ and $\text{VH} < -23.0\,\text{dB}$ are candidate water pixels.
  - Optical verification: If cloud-free optical is present, $\text{MNDWI} > 0.0$ confirms open water.
  - Terrain constraint: Topographic slope computed from DEM. Gravity prevents standing floodwaters on steep terrain. If $\text{slope} > 8^\circ$, candidate pixel is rejected as radar shadow.
  - Model confidence is computed per pixel based on backscatter distance from threshold and optical agreement.

### Step 14: Flood Mask Generation
- Binary morphological operations (dilation and erosion) remove isolated noisy 1-pixel false alarms and fill internal gaps.
- Contours extracted into GeoJSON `Polygon` and `MultiPolygon` geometries using Shapely contouring.
- Simplified with Douglas-Peucker algorithm ($\epsilon = 0.0001^\circ$) to produce clean, transmission-efficient vector boundaries.
- Stored as `FloodRegion` records with properties: `area_sqkm`, `confidence`, `observation_source`.

### Step 15: Temporal Change Detection
- System compares pre-event water baseline (e.g. permanent lakes/rivers from Sentinel-1 pre-event scene or JRC Global Surface Water) against crisis water mask.
- Change classification:
  - $\text{Pre} = 1 \land \text{Post} = 1 \implies \text{PERMANENT\_WATER}$
  - $\text{Pre} = 0 \land \text{Post} = 1 \implies \text{NEWLY\_FLOODED}$ (active disaster inundation)
  - $\text{Pre} = 1 \land \text{Post} = 0 \implies \text{RECEDED}$
  - $\text{Pre} = 0 \land \text{Post} = 0 \implies \text{UNCHANGED\_LAND}$
- Generates `ChangeRegion` objects representing the differential impact.

### Step 16: Multimodal Fusion
- `EvidenceFusionService.fuse(sar_evidence, optical_evidence, dem_evidence)`:
  - Computes belief mass for each region:
    $$m(\text{Flooded}) = 1 - (1 - w_{\text{sar}} \cdot c_{\text{sar}}) \cdot (1 - w_{\text{opt}} \cdot c_{\text{opt}})$$
  - If SAR indicates flood ($c > 0.75$) but Optical indicates clear dry ground ($c > 0.75$) without cloud cover:
    - Region is marked with `conflict_state = "CONFLICTING_EVIDENCE"`
    - Generates a `VerificationFinding` for high-priority ground inspection.

### Step 17: Infrastructure Ingestion
- `InfrastructureService.load_infrastructure(aoi)`:
  - Queries Overpass API or loads local cached OpenStreetMap extract within AOI bounding box.
  - Ingests:
    - Highway network lines (motorways, primaries, secondaries, bridges).
    - Building footprints (polygons).
    - Critical facilities (points/polygons with tags `amenity=hospital`, `amenity=clinic`, `amenity=fire_station`, `amenity=police`, `amenity=shelter`, `amenity=school`).

### Step 18: Spatial Joins
- System builds a Spatial Index (R-Tree / Shapely `STRtree`) of flood polygons.
- Performs spatial intersection:
  - `road_geom.intersection(flood_geom)`: returns overlapping segment lengths.
  - `building_geom.intersection(flood_geom)`: returns flooded area ratio.
  - `facility_geom.distance(flood_geom)`: returns proximity or direct inundation.

### Step 19: Road Passability Derivation
- Passability heuristic and rule:
  - Overlap percentage $P = \frac{\text{Flooded Length}}{\text{Total Segment Length}}$
  - If $P = 0\%$: Status = `OPEN`, Speed Factor = $1.0$
  - If $0\% < P < 25\%$: Status = `PARTIALLY_AFFECTED`, Speed Factor = $0.4$
  - If $25\% \le P < 60\%$: Status = `LIKELY_BLOCKED`, Speed Factor = $0.1$
  - If $P \ge 60\%$ or road is on an inundated Bridge: Status = `BLOCKED`, Speed Factor = $\infty$ (impassable).

### Step 20: Dynamic Graph Construction
- Road network transformed into a `networkx.DiGraph`.
- Graph nodes = intersections and dead-ends.
- Graph edges = road segments with attributes:
  `length_meters`, `free_flow_speed_kmh`, `passability_state`, `travel_time_seconds = length / (speed * speed_factor)`.
- Severed edges: Edges with `BLOCKED` status have edge weights set to $\infty$ or are excised from the active routing topology.

### Step 21: Population Impact Calculation
- Ingests gridded population density within AOI.
- Calculates:
  - `directly_flooded_population`: Sum of population rasters/polygons intersecting `NEWLY_FLOODED` regions.
  - `indirectly_affected_population`: Population living in regions whose road access has been severed or degraded.

### Step 22: Accessibility Loss Calculation
- For all population nodes $n \in N$:
  - Calculate pre-disaster shortest travel time to nearest hospital $H$: $T_{\text{pre}}(n) = \min_{h \in H} \text{dijkstra}(n, h, \text{static\_graph})$.
  - Calculate post-disaster travel time to nearest functioning hospital: $T_{\text{post}}(n) = \min_{h \in H} \text{dijkstra}(n, h, \text{dynamic\_graph})$.
  - Accessibility Loss:
    $$\Delta T(n) = T_{\text{post}}(n) - T_{\text{pre}}(n)$$
  - If no path exists: $T_{\text{post}}(n) = \infty$ (complete loss of medical access).

### Step 23: Isolation Analysis
- System decomposes dynamic road graph into connected components: $\{C_1, C_2, \dots, C_k\}$.
- For each component $C_i$:
  - Check if $C_i$ contains an operational emergency egress point or functioning hospital.
  - If $C_i$ has zero paths to outside relief centers and population $> 0$:
    - Component is flagged as an **Isolated Island**.
    - Calculates `isolated_population`, `isolated_community_name`, and boundary road bottlenecks.

### Step 24: Uncertainty Propagation
- Uncertainty score is computed along the multi-hop chain:
  $$U_{\text{total}} = 1.0 - (Q_{\text{sensor}} \times C_{\text{detection}} \times C_{\text{alignment}} \times C_{\text{osm\_completeness}})$$
- Sensor Quality ($Q_{\text{sensor}}$): Degraded by optical cloud cover or radar incidence angle distortion.
- Detection Confidence ($C_{\text{detection}}$): Model probability spread.
- OSM Completeness ($C_{\text{osm}}$): Density of mapped roads vs expected regional road density benchmark.

### Step 25: Evidence Conflict Detection
- Discrepancies between sources are evaluated:
  - Disagreement between SAR backscatter and optical spectral index.
  - Disagreement between satellite inundation mask and human ground reports.
- If conflict detected, item flagged with `CONFLICTING_EVIDENCE`, lowering recommendation automation and raising human verification requirement.

### Step 26: Priority Generation
- Multi-Criteria Decision Criticality Index:
  $$\text{Score} = w_1 \cdot \text{PopAffected} + w_2 \cdot \text{HospitalCutOff} + w_3 \cdot \text{BridgeSevered} + w_4 \cdot \text{IsolationFactor} + w_5 \cdot \text{Confidence}$$
- Findings categorized:
  - Score $\ge 80 \implies$ `CRITICAL`
  - $60 \le \text{Score} < 80 \implies$ `HIGH`
  - $35 \le \text{Score} < 60 \implies$ `MEDIUM`
  - $\text{Score} < 35 \implies$ `LOW`
  - Low confidence with high potential impact $\implies$ `VERIFICATION_REQUIRED`

### Step 27: Verification Findings Creation
- Any finding with `conflict_state != NONE` or `confidence < 0.60` in a high-consequence zone is placed in the **Verification Queue**.
- A human responder prompt is generated:
  - "Bridge B-14 reported submerged by SAR, but cloud cover blocked optical confirmation. Verify via UAV or field team."

### Step 28: Counterfactual Simulation Execution
- Invoked via `POST /api/v1/simulations`.
- Operator selects candidate action:
  - Action: `RESTORE_EDGE` (e.g. clear debris on Road R-104) or `DEPLOY_PONTOON` (bridge bypass).
- Simulation Engine clones active graph, restores edge impedance to `OPEN`, and re-runs:
  - Dijkstra shortest paths to facilities.
  - Connected component decomposition.
- Computes delta metrics:
  - $\Delta \text{Reconnected Population} = +14,250$
  - $\Delta \text{Hospital Access Restored} = +2\text{ hospitals}$
  - $\Delta \text{Average Travel Time} = -42\text{ minutes}$.
- Returns result clearly marked: `status: "SIMULATED / COUNTERFACTUAL"`.

### Step 29: Results Persistence
- Database transactions store:
  - `FloodRegion` rows with GeoJSON geometry and confidence.
  - `RoadSegment` passability updates.
  - `ImpactFinding` rows with causal chains.
  - `Evidence` records and `EvidenceRelation` edges.
  - `DecisionReceipt` with cryptographic SHA-256 integrity hash.
- Analysis run status updated to `COMPLETED`.

### Step 30: Frontend Requests Results
- Web application (React / Vite) polls or queries `GET /api/v1/events/{id}/summary` and `GET /api/v1/events/{id}/runs/latest`.

### Step 31: API Calls That Occur
- `GET /api/v1/events/{id}/summary`
- `GET /api/v1/events/{id}/flood`
- `GET /api/v1/events/{id}/infrastructure`
- `GET /api/v1/events/{id}/findings`
- `GET /api/v1/events/{id}/isolation`
- `GET /api/v1/events/{id}/evidence-graph`

### Step 32: Backend Services Answering Them
- `EventService`, `FloodService`, `InfrastructureService`, `FindingService`, `EvidenceService`.

### Step 33: Data Returned
- Structured JSON with GeoJSON features:
  - Summary metrics: total flooded sqkm, population impacted, isolated count, severed roads.
  - Layer GeoJSON: Flood polygons, passability-styled road linestrings, facility points with access status.
  - Findings array: Ranked list of critical issues with supporting evidence references.

### Step 34: Rendering in Frontend
- **Mission Control**: KPI indicator cards, data freshness badge, event timeline, alert banner.
- **Event Map**: MapLibre / Leaflet interactive map with custom vector styling:
  - Inundation polygons in semi-transparent electric blue.
  - Road lines colored by passability (Red = Blocked, Orange = Affected, Green = Open).
  - Hospital markers with green pulse (Accessible) or red strike-through (Cut Off).
  - Isolated community boundary hulls highlighted in amber hatch.

### Step 35: Handling Low Confidence
- UI displays a visible warning badge: `LOW CONFIDENCE (0.48)`.
- Polygon fill uses striped hatching instead of solid fill.
- Explanation modal breaks down reasons: e.g. "Steep terrain shadow suspected; optical verification unavailable due to 94% cloud cover."

### Step 36: Handling Conflicting Evidence
- UI displays amber warning: `EVIDENCE CONFLICT DETECTED`.
- Renders side-by-side evidence inspection:
  - Source A: Sentinel-1 SAR (Backscatter -19.4 dB -> Inundated)
  - Source B: Sentinel-2 MSI (MNDWI -0.22 -> Dry ground)
- Prompt button: "Dispatch Field Verification / Mark Ground Truth".

### Step 37: Handling Unavailable Data Sources
- If Optical is 100% clouded:
  - Pipeline continues seamlessly on SAR + DEM.
  - Data freshness / modality indicator displays: `OPTICAL: UNAVAILABLE (CLOUDY) | SAR: OPERATIONAL`.
  - Confidence metric is appropriately capped at 0.82 to reflect single-modality limitation.

### Step 38: Error Handling and Retries
- External STAC / Overpass timeouts invoke exponential backoff retry (3 attempts).
- If external API remains unavailable, pipeline gracefully falls back to deterministic local fixture scenes and clearly alerts the operator.

### Step 39: Human Responder Actions
- Operator reviews the **Priority Workbench**.
- Operator can:
  - Accept or reject a finding.
  - Submit ground truth verification ("Road confirmed impassable due to 1.5m flood depth").
  - Launch counterfactual simulation to evaluate engineering repairs.
  - Export auditable Decision Receipt.

### Step 40: What Becomes Part of the Final Decision Receipt
- Finding ID & Disaster Event metadata.
- Spatial polygon / coordinates.
- Satellite scene IDs (Sentinel-1 granule name, Sentinel-2 tile ID).
- Acquisition timestamps and sensor orbits.
- Algorithmic version and model weights.
- Multi-source evidence chain (Backscatter, MNDWI, slope).
- Calculated human impact (isolated population, cut-off hospitals).
- Human verification logs and operator signatures.
- Cryptographic SHA-256 verification hash certifying un-tampered record.

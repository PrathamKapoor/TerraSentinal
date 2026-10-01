# TerraSentinel: Evidence-Grounded Satellite Intelligence for Flood Disaster Response

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61dafb.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4+-646cff.svg)](https://vitejs.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-ee4c2c.svg)](https://pytorch.org/)
[![CI](https://github.com/PrathamKapoor/TerraSentinal/actions/workflows/ci.yml/badge.svg)](https://github.com/PrathamKapoor/TerraSentinal/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **TerraSentinel** converts heterogeneous Earth-observation data into evidence-backed disaster-impact intelligence.
> It advances beyond raw flood segmentation maps to dynamic infrastructure reasoning, population isolation analytics, counterfactual intervention simulation, and cryptographically auditable decision receipts.

---

## 1. The Core Problem & Product Philosophy

Existing Earth-Observation (EO) disaster mapping stops prematurely at:
$$\text{satellite image} \longrightarrow \text{flood mask}$$

A raw binary flood mask cannot answer operational humanitarian questions:
- *Can an ambulance reach Osmani Trauma Center from District 4?*
- *Which rural communities have lost 100% of vehicular egress?*
- *Why is Bridge B-14 prioritized over Highway N2 Causeway?*
- *If engineering crews deploy a pontoon bridge on River Surma, how many lives are reconnected?*

### The 4-Tier Disaster Intelligence Stack

TerraSentinel systematically answers four escalating operational questions:

```
LEVEL 1: WHERE IS THE FLOOD / DAMAGE?
         All-weather Sentinel-1 C-band SAR dual-polarization (VV/VH) backscatter
         + Sentinel-2 MSI optical spectral indices (MNDWI/NDVI)
         + Topographic DEM slope false-alarm suppression (rejecting radar shadows).

LEVEL 2: WHAT INFRASTRUCTURE AND POPULATION ARE AFFECTED?
         Spatial intersection with OpenStreetMap transport lines, bridges,
         critical healthcare facilities, and high-resolution gridded population (WorldPop).

LEVEL 3: WHO OR WHAT HAS LOST ACCESSIBILITY?
         Dynamic graph topology (NetworkX) updating edge impedances in real-time,
         Dijkstra shortest-path detour computation, and connected-component
         isolation island decomposition.

LEVEL 4: WHAT SHOULD A RESPONDER INVESTIGATE OR INTERVENE ON, WHY, AND WITH WHAT CONFIDENCE?
         Multi-criteria Criticality Priority Engine, Multi-Hop Causal Evidence Chains,
         Counterfactual What-If Simulation, and Cryptographically Signed Decision Receipts (SHA-256).
```

---

## 2. High-Level System Architecture

```
                                  TERRASENTINEL
                                        │
                        ┌───────────────┴───────────────┐
                        │                               │
                 EARTH OBSERVATIONS               CONTEXT DATA
                        │                               │
                ┌───────┼────────┐              ┌───────┼────────┐
                ↓       ↓        ↓              ↓       ↓        ↓
           Sentinel-1 Sentinel-2  DEM          OSM   Population Facilities
                │       │        │              │       │        │
                └───────┼────────┘              └───────┼────────┘
                        └───────────────┬───────────────┘
                                        ↓
                              MULTIMODAL FUSION
                                        │
                            ┌───────────┴───────────┐
                            ↓                       ↓
                      FLOOD DETECTION         CHANGE DETECTION
                            │                       │
                            └───────────┬───────────┘
                                        ↓
                              DAMAGE / IMPACT LAYER
                                        │
                       ┌────────────────┼────────────────┐
                       ↓                ↓                ↓
                   Buildings          Roads           Bridges
                    Damage          Passability        Damage
                       └────────────────┼────────────────┘
                                        ↓
                              GEOSPATIAL REASONING
                                        │
                       ┌────────────────┼────────────────┐
                       ↓                ↓                ↓
                  Population       Connectivity      Critical
                    Impact            Loss           Facilities
                       └────────────────┼────────────────┘
                                        ↓
                              IMPACT / ISOLATION
                                   ASSESSMENT
                                        │
                              ┌─────────┴─────────┐
                              ↓                   ↓
                        PRIORITIZATION       UNCERTAINTY
                              │                   │
                              └─────────┬─────────┘
                                        ↓
                              RESPONSE RECOMMENDATION
                                        │
                                        ↓
                                 HUMAN RESPONDER
                                        │
                                 ACTION / DECISION
                                        │
                                        ↓
                              EVIDENCE & TRUST LAYER
                              ┌─────────────────────┐
                              │ Provenance          │
                              │ Source Traceability │
                              │ Confidence          │
                              │ Evidence Conflicts  │
                              │ Decision Receipt    │
                              └─────────────────────┘
```

---

## 3. Operational Modes

### A. Production Mode (Live Ingestion)
- Uses **PySTAC Client** to query Copernicus Sentinel-1 GRD, Sentinel-2 L2A, and Copernicus GLO-30 DEM assets from AWS Earth Search and Microsoft Planetary Computer.
- Preprocesses SAR decibels, performs Lee speckle filtering, extracts MNDWI, and queries Overpass OSM for local infrastructure.

### B. Offline / Deterministic Fixture Mode
- Guaranteed 100% offline, zero-credential operation for field command posts and isolated crisis operations.
- Bundles deterministic, physically calibrated scenarios (e.g. *Sylhet Surma River Basin Mega-Flood* and *Tar River Inland Fluvial Surge*).
- Clearly flagged in all UI views and API payloads as `[FIXTURE MODE]`.

---

## 4. Key Differentiators & Features

| Capability | Standard Flood Map | TerraSentinel Intelligence Stack |
|---|---|---|
| **Sensor Modality** | Single-sensor optical or SAR | All-weather C-band SAR + Optical MNDWI + DEM slope fusion |
| **False-Alarm Filtering**| None (mountain shadows misclassified)| Hydrological slope constraint eliminates steep terrain shadows |
| **Conflict Handling** | Collapses discordant pixels into a mean | Detects `CONFLICTING_EVIDENCE` and alerts human responders |
| **Infrastructure** | Static GIS vector overlay | Dynamic graph impedance updating (OPEN, PARTIAL, BLOCKED) |
| **Community Impact** | "X sq km flooded" | Identifies disconnected subgraphs and counts isolated residents |
| **Decision Support** | Passive retrospective heatmap | Interactive counterfactual simulation of repairs & pontoon bridges |
| **Auditability** | None | SHA-256 cryptographically verifiable **Decision Receipts** |

---

## 5. Local Development & Quickstart

### Prerequisites
- Python 3.11+ (Tested on Python 3.13 on Windows 11 and Linux)
- Node.js v18+ and npm

### Environment Configuration
```bash
# Clone the repository
git clone https://github.com/PrathamKapoor/TerraSentinal.git
cd TerraSentinal

# Copy example environment configuration
cp .env.example .env
```

### Backend Setup
```bash
# Install Python requirements
pip install -r backend/requirements.txt

# Run backend test suite
pytest -v backend/tests

# Start FastAPI backend (port 8000)
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Workbench Setup
```bash
# In a separate terminal, navigate to frontend:
cd frontend

# Install dependencies
npm install

# Start Vite development server (port 3000)
npm run dev

# Or build for production
npm run build
```

Open your browser at `http://localhost:3000` to interact with the operational workbench.

---

## 6. End-to-End Operational Workflow (Demo Flow)

1. **Select Incident:** Choose `Cyclone Remal - Lower Surma Basin Inundation`.
2. **Review Mission Control:** Inspect KPIs: 28.5 km² flood extent, 8,700 isolated residents, Bridge B-14 submerged.
3. **Open Event Map:** Toggle between pre-disaster dry baseline, peak crisis inundation, and bi-temporal change layers. Click roads and bridges to inspect passability and speed factors.
4. **Inspect Priority Workbench:** Review explainable findings ranked by criticality score.
5. **Trace Evidence Chain:** Open finding detail to audit the multi-hop chain from satellite backscatter to healthcare isolation.
6. **Simulate Intervention:** In Response Simulator, select *Deploy Rapid Military Pontoon on Bridge B-14* and click *Execute Counterfactual Run*. Observe immediate delta: **+14,200 reconnected population** and **-42.5 minutes** travel time saved.
7. **Verify Decision Receipt:** Open the Decision Receipt, inspect model provenance, and click *Verify Cryptographic Seal* to validate SHA-256 integrity.

---

## 7. Dual-Track Research Benchmarking Suite

TerraSentinel maintains two strictly separated, independent evaluation tracks:
1. **REAL-DATA EMPIRICAL VALIDATION:** Authentic Earth-observation satellite data and independent hand labels.
2. **CONTROLLED SYNTHETIC SENSOR-STRESS BENCHMARK:** Parametric stress scenarios isolating edge-case physical failure modes.

Run both benchmarks via CLI:
```powershell
python -m backend.app.research.benchmark_runner
```

---

### Track 1: Real-Data Empirical Validation (Sen1Floods11 v1.1)
*Authority: Primary Earth Observation Scientific Standard* — Detailed report: **[real-data-validation.md](research/benchmarks/real-data-validation.md)**

Evaluates authentic Copernicus Sentinel-1 C-band SAR (VV/VH float32) and Sentinel-2 optical imagery across **11 global chips (2,883,584 pixels)** from the peer-reviewed **Sen1Floods11 (v1.1)** benchmark (Bonafilia et al., 2020), evaluated against independent consensus hand-annotated labels. Strictly enforces out-of-domain event holdout:
- **Unseen Holdout Event (TEST):** Bolivia Mamoré River Surge (`Bolivia_103757`, `Bolivia_129334`, `Bolivia_195474`)
- **Validation Event (VAL):** Cambodia Mekong Delta Basin (`Mekong_1149855`, `Mekong_977338`)
- **Regional Training Events (TRAIN):** USA Arkansas River, Spain Vega Baja, India Brahmaputra River

#### Empirical Real-Data Results (All 11 Real Satellite Chips)
| Baseline ID | Model Classification | Modality / Architecture | Macro IoU | Micro IoU | Val IoU (Mekong) | Unseen Test IoU (Bolivia) | Primary Empirical Finding |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **BASE-A** | `HEURISTIC` | SAR-Only Dual-Pol ($\sigma^0_{VV} < -16, \sigma^0_{VH} < -23$) | 0.3729 | 0.6651 | 0.6226 | 0.3607 | High precision ($>97\%$), misses shallow vegetated water |
| **BASE-B** | `HEURISTIC` | Optical-Only ($\text{MNDWI} > 0.0$ on valid pixels) | **0.5497** | **0.7171** | 0.6391 | 0.5662 | Captures shallow water boundaries; vulnerable to clouds |
| **BASE-C** | `HEURISTIC` | Multimodal SAR + Optical Consensus | 0.4502 | 0.6797 | 0.6328 | 0.5641 | High recall; inherits optical false alarms on wet soil |
| **BASE-D** | `HEURISTIC` | **TerraSentinel Dempster-Shafer Evidential Fusion** | 0.4481 | 0.7006 | **0.6626** | 0.3710 | Calibrated balance ($82\%$ test precision); flags conflicts |
| **BASE-E** | `UNTRAINED / ADAPTER` | Convolutional U-Net Spatial Adapter | 0.4626 | 0.7073 | 0.6734 | **0.5876** | Heuristic 4-channel spatial smoothing (untrained weights) |

*Per-event breakdowns and failure case audits are published in [research/real-data-validation-report.md](research/real-data-validation-report.md).*

---

### Track 2: Controlled Synthetic Sensor-Stress Benchmark
*Authority: Controlled Physical Edge-Case & Confounder Isolation* — Detailed report: **[synthetic-stress.md](research/benchmarks/synthetic-stress.md)**

*Notice: These scenarios are generated from controlled parametric physical equations to systematically isolate specific sensor failure modes. These metrics reflect stress response and must NOT be cited as real-world satellite generalization.*

| Scenario ID | Tested Stressor / Confounder | Synthetic Stress IoU | Tested Invariant |
| :--- | :--- | :---: | :--- |
| **EVT_SYLHET_2026** | Dense monsoonal clouds ($25\%$ NaN in optical) | 0.7738 | Graceful degradation to radar-only evidence |
| **EVT_RED_RIVER_2026** | Saturated agricultural soil (low land/water backscatter contrast) | 0.9890 | Dual-pol cross-channel separability |
| **EVT_EBRO_2026** | Steep mountain topography ($> 8.5^\circ$ radar shadows) | 0.9958 | DEM slope constraint eliminates $100\%$ of shadow false alarms |
| **EVT_MEKONG_2026** | Emergent wetland vegetation (depolarizing volume scattering) | 0.6365 | Cross-polarization VH suppression |
| **EVT_BEIRA_2026** | Gale wind surface roughening on open water ($\sigma^0_{VV} > -15.5\text{ dB}$) | 0.1911 | Conflict detection surfaces `CONFLICTING_EVIDENCE` |

---

## 8. API Specification

| Endpoint | Method | Description | Latency (Live Benchmark) |
|---|---|---|:---:|
| `/health` | GET | Service health check | < 5 ms |
| `/api/v1/events` | POST, GET | Create or list disaster events | ~30 ms |
| `/api/v1/events/{id}/summary` | GET | Mission Control KPI summary | ~40 ms |
| `/api/v1/events/{id}/runs` | POST | Dispatches asynchronous analysis pipeline | ~85 ms |
| `/api/v1/runs/{id}` | GET | Polls background run progress and stage | < 10 ms |
| `/api/v1/events/{id}/flood` | GET | Flood polygons GeoJSON with confidence | ~18 ms |
| `/api/v1/events/{id}/infrastructure`| GET | Roads, bridges, facilities GeoJSON with passability | ~12 ms |
| `/api/v1/events/{id}/evidence-graph`| GET | Multi-hop evidence DAG nodes and edges | ~17 ms |
| `/api/v1/events/{id}/isolation` | GET | Cut-off communities and demographic exposure | ~16 ms |
| `/api/v1/findings/{id}/verification`| POST | Human responder field ground-truth submission | ~20 ms |
| `/api/v1/simulations` | POST | Executes counterfactual what-if intervention | ~25 ms |
| `/api/v1/receipts/{id}/verify` | POST | Verifies cryptographic SHA-256 seal integrity | < 5 ms |
| `/api/v1/research/benchmarks` | GET | Executes empirical benchmark matrix | ~180 ms |

---

## 9. Auditable Project Records & Research Artifacts

- **`decisions.md`:** Immutable architectural and research decision ledger documenting DECISION-0001 through DECISION-0012, Session 1 through Session 4 Change Summaries, Subsystem Matrix, and Collaborator Settings.
- **`flow.d`:** Observable 40-step end-to-end execution flow specification from satellite telemetry to decision receipt.
- **`research/` Artifacts:**
  - `validation-report.md`: Formal 11-section research validation and benchmark validity audit.
  - `repos.md`: 11-dimension evaluation of 24+ external repositories and foundation models.
  - `papers.md`: 12-dimension literature survey of seminal remote sensing and graph routing papers.
  - `datasets.md`: 12-dimension data registry covering Sen1Floods11, xBD, BRIGHT, FloodNet, WorldPop, and OSM.
  - `models.md`: 11-dimension model registry detailing deployed adapters and theoretical architectures.
  - `methods.md`: Rigorous mathematical formulations for radar physics, spectral indices, evidential fusion, and network routing.
  - `prior-art-matrix.md`: Mandatory 24-domain comparative prior-art matrix.
  - `research-gaps.md`: Analysis of the 7 critical operational and scientific gaps in disaster intelligence.
  - `final-requirement-matrix.md`: Comprehensive 42-requirement verification matrix with status and evidence.
  - `licenses.md` & `benchmarks.md`: Open-source licensing compliance and benchmark specifications.

---

## 10. License & Governance

Software released under the **MIT License**. Earth-observation satellite data provided by ESA Copernicus and NASA JPL under open access data policies. OpenStreetMap data is `© OpenStreetMap contributors` under the ODbL.

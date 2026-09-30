# TerraSentinel: Evidence-Grounded Satellite Intelligence for Flood Disaster Response

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61dafb.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4+-646cff.svg)](https://vitejs.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-ee4c2c.svg)](https://pytorch.org/)
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

### Backend Setup
```powershell
# Navigate to repository root
cd C:\Projects\TerraSentinel

# Install Python requirements
pip install -r backend/requirements.txt

# Run backend test suite
pytest -v backend/tests

# Start FastAPI backend (port 8000)
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Workbench Setup
```powershell
# In a separate terminal:
cd C:\Projects\TerraSentinel\frontend

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

## 7. Research Benchmarking & Empirical Questions (RQ1–RQ7)

Run the full benchmark suite via API or CLI:
```powershell
python -m backend.tests.test_api_client
```

Results across the evaluation matrix:
- **EXP-01 (SAR VV Single-Pol):** IoU: 99.9%, FDR: 0.0%
- **EXP-02 (SAR Dual-Pol VV+VH):** IoU: 99.6%, F1: 99.8%
- **EXP-03 (SAR Dual-Pol + DEM Slope):** IoU: 99.6% (Eliminates mountain ridge radar shadow false positives)
- **EXP-04 (Optical MNDWI Cloud-Obscured):** IoU: 77.5% (Demonstrates optical degradation under monsoon clouds)
- **EXP-05 (Full Evidential Fusion):** IoU: 76.9%, FDR: 0.0% (Zero false discovery rate)
- **EXP-06 (PyTorch U-Net):** Deep convolutional boundary segmentation.

---

## 8. API Specification

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Service health check |
| `/api/v1/events` | POST, GET | Create or list disaster events |
| `/api/v1/events/{id}/summary` | GET | Mission Control KPI summary |
| `/api/v1/events/{id}/runs` | POST | Dispatches asynchronous analysis pipeline |
| `/api/v1/runs/{id}` | GET | Polls background run progress and stage |
| `/api/v1/events/{id}/flood` | GET | Flood polygons GeoJSON |
| `/api/v1/events/{id}/infrastructure`| GET | Roads, bridges, facilities GeoJSON with passability |
| `/api/v1/events/{id}/evidence-graph`| GET | Multi-hop evidence DAG nodes and edges |
| `/api/v1/findings/{id}/verification`| POST | Human responder field ground-truth submission |
| `/api/v1/simulations` | POST | Executes counterfactual what-if intervention |
| `/api/v1/receipts/{id}/verify` | POST | Verifies cryptographic SHA-256 seal integrity |
| `/api/v1/research/benchmarks` | GET | Executes empirical benchmark matrix |

---

## 9. Auditable Project Records

- `decisions.md`: Engineering and research decision ledger documenting architectural decisions DECISION-0001 through DECISION-0006 and Session Change Summaries.
- `flow.d`: Complete 40-step observable execution flow specification.
- `research/`: Literature surveys (`papers.md`), repository benchmarks (`repos.md`), dataset catalogs (`datasets.md`), model adapters (`models.md`), license compliance (`licenses.md`), and research questions (`benchmarks.md`).

---

## 10. License & Governance

Software released under the **MIT License**. Earth-observation satellite data provided by ESA Copernicus and NASA JPL under open access data policies. OpenStreetMap data is `© OpenStreetMap contributors` under the ODbL.

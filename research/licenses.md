# TerraSentinel Research: Open-Source Licenses & Data Governance

This audit catalogs the software licenses, dataset terms of use, and distribution restrictions for all components evaluated or integrated into **TerraSentinel**.

---

## 1. Software Libraries & Repositories

| Component | Source Repository | License | Commercial Use Allowed? | Operational Restrictions |
|---|---|---|---|---|
| **FastAPI** | tiangolo/fastapi | MIT | Yes | Standard MIT attribution. |
| **Pydantic** | pydantic/pydantic | MIT | Yes | None. |
| **PyTorch** | pytorch/pytorch | Modified BSD | Yes | None. |
| **Shapely** | shapely/shapely | BSD-3-Clause | Yes | None. |
| **GeoPandas** | geopandas/geopandas | BSD-3-Clause | Yes | None. |
| **NetworkX** | networkx/networkx | BSD-3-Clause | Yes | None. |
| **PySTAC** | stac-utils/pystac | Apache-2.0 | Yes | Include copyright and license notices. |
| **OSMnx** | gboeing/osmnx | MIT | Yes | None. |
| **Sen1Floods11 (Code)** | cloudtostreet/Sen1Floods11 | MIT | Yes | Standard MIT attribution. |
| **Microsoft AI4G Flood** | microsoft/ai4g-flood | MIT | Yes | None. |
| **Prithvi-EO-2.0** | NASA-IMPACT/Prithvi-EO-2.0 | Apache-2.0 | Yes | Include Apache 2.0 notices. |
| **TerraTorch** | torchgeo/terratorch | Apache-2.0 | Yes | None. |
| **ChangeMamba** | ChenHongruixuan/ChangeMamba | Apache-2.0 | Yes | None. |
| **xView2 Baseline** | DIUx-xView/xView2_first_place | Apache-2.0 | Yes | None. |

---

## 2. Earth Observation Datasets & Catalogs

| Dataset | Provider | Terms / License | Citation Required? | Commercial Restriction |
|---|---|---|---|---|
| **Copernicus Sentinel-1 / 2** | ESA / European Commission | Copernicus Open Access Policy | Yes | Free, full, and open access for civil and commercial applications. |
| **NASADEM** | NASA / JPL | NASA Open Data Policy (Public Domain) | Yes | Unrestricted public domain worldwide. |
| **OpenStreetMap (OSM)** | OpenStreetMap Foundation | ODbL 1.0 (Open Database License) | Yes (`© OpenStreetMap contributors`) | Share-Alike applies to derived database modifications. |
| **Sen1Floods11** | Cloud to Street / Radiant Earth | CC BY 4.0 | Yes (Cite Bonafilia et al., 2020) | Free for commercial and non-commercial with attribution. |
| **xBD (xView2)** | Defense Innovation Unit | CC BY-NC-SA 4.0 | Yes | Non-commercial research license for benchmark data. |
| **WorldPop** | WorldPop / Univ. of Southampton | CC BY 4.0 | Yes | Free open access with attribution. |

---

## 3. Compliance and Safe Distribution Strategy

1. **Clean Separation of Benchmark Data from Runtime Code:**
   - Datasets licensed under CC BY-NC-SA (e.g. xBD) are isolated in the `research/` benchmark harness and are **never** bundled into the production core distribution.
2. **OpenStreetMap Attribution:**
   - Map tiles and vector layers derived from OpenStreetMap explicitly render `© OpenStreetMap contributors` in map attribution controls.
3. **Copernicus Provenance:**
   - All Sentinel-1 and Sentinel-2 scenes carry ESA Copernicus product identifiers in generated **Decision Receipts**.

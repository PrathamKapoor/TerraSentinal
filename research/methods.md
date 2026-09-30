# TerraSentinel Research: Algorithmic & Mathematical Methods Specification

This document provides a comprehensive, research-grade mathematical and algorithmic specification of every method, transformation, heuristic, and inference routine implemented in **TerraSentinel** (*Evidence-Grounded Satellite Intelligence for Flood Disaster Response*).

---

## 1. Remote Sensing Physics & Signal Processing

### 1.1 SAR Radiometric Calibration & Speckle Filtering
Synthetic Aperture Radar (SAR) sensors emit microwave pulses (e.g. Sentinel-1 C-band at $\lambda \approx 5.6\text{ cm}$, $f \approx 5.405\text{ GHz}$) that penetrate clouds, haze, and rain. The received linear amplitude $A$ is converted to calibrated radar backscatter $\sigma^0$ in decibels (dB):
$$\sigma^0 = 10 \cdot \log_{10}\left(A^2 + \epsilon\right)$$
where $\epsilon = 10^{-7}$ prevents numerical singularity.

SAR imagery exhibits multiplicative speckle noise caused by coherent interference among random sub-resolution scatterers. TerraSentinel applies an adaptive Lee filter with a $5 \times 5$ spatial window:
$$\bar{I} = \mu + W \cdot (I - \mu)$$
where:
- $\mu = \frac{1}{|K|} \sum_{i,j \in K} I_{i,j}$ is the local kernel mean,
- $\sigma^2_I = \frac{1}{|K|} \sum_{i,j \in K} (I_{i,j} - \mu)^2$ is the local variance,
- $\sigma^2_{\text{overall}}$ is the global image variance,
- $W = \text{clip}\left(\frac{\sigma^2_I}{\sigma^2_I + \sigma^2_{\text{overall}} + \epsilon}, 0.0, 1.0\right)$ is the adaptive weighting factor.

When local variance is high (e.g. along sharp water-land boundaries or road embankments), $W \to 1.0$, preserving structural edges. In homogeneous water bodies or bare fields, $W \to 0.0$, applying uniform spatial smoothing. Corrupted pixels (NaN from sensor dropout) are sanitized using $I_{\text{clean}} = \text{nan\_to\_num}(I, \text{nan}=-30.0\text{ dB})$.

### 1.2 Multispectral Optical Spectral Indices
Under cloud-free optical conditions (Sentinel-2 MSI), water bodies exhibit strong absorption in the Shortwave Infrared (SWIR) and high reflectance in the Green band. TerraSentinel computes the Modified Normalized Difference Water Index (MNDWI):
$$\text{MNDWI} = \frac{\rho_{\text{Green}} - \rho_{\text{SWIR}}}{\rho_{\text{Green}} + \rho_{\text{SWIR}} + \epsilon} = \frac{B03 - B11}{B03 + B11 + \epsilon}$$
where $\rho \in [-1.0, 1.0]$. Open water yields $\text{MNDWI} > 0.0$, whereas bare soil and urban infrastructure yield negative values.

To filter false water detections in dense, wet vegetation, TerraSentinel computes the Normalized Difference Vegetation Index (NDVI):
$$\text{NDVI} = \frac{\rho_{\text{NIR}} - \rho_{\text{Red}}}{\rho_{\text{NIR}} + \rho_{\text{Red}} + \epsilon} = \frac{B08 - B04}{B08 + B04 + \epsilon}$$

### 1.3 Topographic Terrain Slope Derivation
Gravity prevents standing floodwaters from remaining on steep inclines. Using Digital Elevation Model (DEM) arrays with physical grid spacing $\Delta x = \Delta y = 30.0\text{ meters}$, spatial elevation gradients are derived via Sobel finite differences:
$$G_x = \frac{\partial z}{\partial x} \approx \frac{1}{8 \Delta x} \begin{bmatrix} -1 & 0 & 1 \\ -2 & 0 & 2 \\ -1 & 0 & 1 \end{bmatrix} * Z, \quad G_y = \frac{\partial z}{\partial y} \approx \frac{1}{8 \Delta y} \begin{bmatrix} 1 & 2 & 1 \\ 0 & 0 & 0 \\ -1 & -2 & -1 \end{bmatrix} * Z$$
The topographic slope in degrees $\theta$ is:
$$\theta = \arctan\left(\sqrt{G_x^2 + G_y^2}\right) \cdot \frac{180.0}{\pi}$$
Any candidate radar water pixel with $\theta > 8.0^\circ$ is rejected as a radar shadow artifact.

---

## 2. Multimodal Evidential Fusion & Conflict Reasoning

### 2.1 Bounded Evidential Belief Combination
Let the frame of discernment be $\Theta = \{\text{Flooded}, \text{Dry}\}$. Sensors contribute evidence mass:
1. **SAR Evidence:**
   $$m_{\text{sar}}(\text{Flooded}) = \text{clip}\left(\frac{-16.0 - \sigma^0_{VV}}{6.0}, 0.0, 1.0\right) \times w_{\text{sar}}$$
   where base weight $w_{\text{sar}} = 0.70$.
2. **Optical Evidence:**
   $$m_{\text{opt}}(\text{Flooded}) = \text{clip}\left(\frac{\text{MNDWI} + 0.15}{0.55}, 0.0, 1.0\right) \times w_{\text{opt}} \times \left(1.0 - \frac{\text{cloud\_pct}}{100.0}\right)$$
   where base weight $w_{\text{opt}} = 0.80$.
3. **Topographic Support:**
   $$m_{\text{dem}}(\text{Flooded}) = 1.0 - \text{clip}\left(\frac{\theta - 8.0^\circ}{4.0^\circ}, 0.0, 1.0\right)$$

Combined flood probability is computed via normalized convex combination:
$$P(\text{Flooded}) = \frac{m_{\text{sar}} \cdot w_{\text{sar}} + m_{\text{opt}} \cdot w_{\text{opt}}}{w_{\text{sar}} + w_{\text{opt}} + \epsilon} \times m_{\text{dem}}$$

### 2.2 Graceful Degradation Protocol
When sensor modalities are unavailable during an active crisis, the engine adapts deterministically without fabricating data:
- **Missing Optical ($\text{cloud\_pct} > 80\%$ or Nighttime):**
  $w_{\text{opt}} \leftarrow 0.0$, $w_{\text{sar}} \leftarrow 0.85$, Status $\leftarrow$ `DEGRADED_SAR_ONLY`, Confidence Penalty $\Delta C = -0.18$.
- **Missing SAR (Orbital Revisit Gap):**
  $w_{\text{sar}} \leftarrow 0.0$, $w_{\text{opt}} \leftarrow 0.85$, Status $\leftarrow$ `DEGRADED_OPTICAL_ONLY`, Confidence Penalty $\Delta C = -0.10$.
- **Missing DEM:**
  $m_{\text{dem}} \leftarrow 1.0$, Status $\leftarrow$ `UNCONSTRAINED_TERRAIN`, Confidence Penalty $\Delta C = -0.15$.
- **Missing All Modalities:**
  Throws `ValueError("At least one Earth observation modality (SAR or Optical) must be provided.")`.

### 2.3 Sensor Discordance & Conflict Detection
When optical and radar observations yield discordant evidence under high visibility ($\text{cloud\_pct} < 15\%$):
$$\text{Conflict}(x, y) = (\sigma^0_{VV}(x,y) < -16.0\text{ dB}) \land (\text{MNDWI}(x,y) \le 0.0)$$
Typical of smooth airport tarmac, calm dry sand, or wind-roughened floodwaters. The engine:
1. Emits a discrete binary `conflict_mask`.
2. Flags event state: `ConflictState.CONFLICTING`.
3. Suppresses downstream priority criticality scores by 30%.
4. Enforces `PriorityLevel.VERIFY` for human visual ground verification.

---

## 3. Geospatial Vector Topology & Spatial Joins

### 3.1 Contour Tracing & Topology Sanitization
Binary flood masks $M \in \{0, 1\}^{H \times W}$ are converted to geographical coordinates via affine transformation:
$$\text{lon} = \text{lon}_{\min} + \frac{x}{W} (\text{lon}_{\max} - \text{lon}_{\min}), \quad \text{lat} = \text{lat}_{\max} - \frac{y}{H} (\text{lat}_{\max} - \text{lat}_{\min})$$
Continuous horizontal pixel runs are polygonized and dissolved using `shapely.ops.unary_union`. To resolve self-intersecting "bowtie" loops produced by complex terrain contours, all geometries pass through:
$$G_{\text{valid}} = \text{shapely.validation.make_valid}(G_{\text{raw}})$$

### 3.2 Deduplication Invariant in Spatial Joins
Given a road polyline $R$ and a set of candidate intersecting flood polygons $\{F_1, F_2, \dots, F_k\}$ retrieved via bounding-box spatial tree (`STRtree`):
$$F_{\text{merged}} = \bigcup_{i=1}^k F_i = \text{unary\_union}(\{F_i \mid R \cap F_i \neq \emptyset\})$$
The flooded road segment length is:
$$L_{\text{flooded}} = \text{Length}\left(R \cap F_{\text{merged}}\right)$$
The overlap ratio is:
$$\Omega(R) = \min\left(1.0, \frac{L_{\text{flooded}}}{\text{Length}(R) + \epsilon}\right)$$
This prevents double-counting road lengths where two adjacent flood polygons overlap the same road segment.

---

## 4. Road Passability & Dynamic Network Routing

### 4.1 Road Passability Classification
Every road segment $R$ is assigned a discrete passability state and speed factor $S_R \in [0.0, 1.0]$:
$$S_R = \begin{cases} 
1.0 & \text{if } \Omega(R) < 0.20 \implies \text{OPEN} \\
0.45 & \text{if } 0.20 \le \Omega(R) < 0.50 \implies \text{PARTIALLY\_AFFECTED} \\
0.15 & \text{if } 0.50 \le \Omega(R) < 0.60 \implies \text{LIKELY\_BLOCKED} \\
0.0 & \text{if } \Omega(R) \ge 0.60 \text{ or } (R \text{ is bridge} \land \Omega(R) > 0.25) \implies \text{BLOCKED}
\end{cases}$$

### 4.2 Dynamic Graph Construction & Impedance
The transport network is modeled as a bidirectional weighted multigraph $G = (V, E)$. The travel time impedance for edge $e = (u, v)$ in minutes is:
$$T_e = \begin{cases} 
\frac{L_e}{\max(10.0, V_{\text{base}}) \times S_e} \times 60.0 & \text{if } S_e > 0 \\
\infty & \text{if } S_e = 0 \quad (\text{Edge excised from active routing topology})
\end{cases}$$

### 4.3 Dual-Pass Dijkstra Accessibility Delta ($\Delta T$)
For each populated community settlement $C_i$ and the set of functioning hospitals $\mathcal{H}$:
1. **Baseline Travel Time:**
   $$T_{\text{baseline}}(C_i) = \min_{h \in \mathcal{H}} \text{Dijkstra}\left(C_i, h, G_{\text{baseline}}\right)$$
2. **Disrupted Travel Time:**
   $$T_{\text{disrupted}}(C_i) = \min_{h \in \mathcal{H}} \text{Dijkstra}\left(C_i, h, G_{\text{active}}\right)$$
3. **Accessibility Loss:**
   $$\Delta T(C_i) = T_{\text{disrupted}}(C_i) - T_{\text{baseline}}(C_i)$$
If no path exists to any hospital, $\Delta T(C_i) \ge 900.0\text{ minutes}$, and community $C_i$ is classified as **`ISOLATED`**.

---

## 5. Prioritization, Sensitivity & Tie-Breaking

### 5.1 Non-Linear Criticality Scoring Equation
Emergency response prioritization requires balancing population size, life-safety facilities, and access loss:
$$S_i = \underbrace{\min\left(40.0, 8.0 \cdot \log_{10}(\text{Pop}_i + 1)\right)}_{\text{Logarithmic Population Scaling}} + \underbrace{15.0 \cdot N_{\text{hospitals}} + 8.0 \cdot N_{\text{shelters}}}_{\text{Critical Facility Multipliers}} + \underbrace{\min(25.0, 0.25 \cdot \Delta T_i)}_{\text{Severance Delay}} + \underbrace{15.0 \cdot \mathbb{I}_{\text{isolated}}}_{\text{Cut-Off Penalty}}$$

Under sensor conflict, uncertainty suppression applies:
$$S_{\text{final}} = S_i \times \left(1.0 - 0.30 \cdot \mathbb{I}_{\text{conflict}}\right)$$

### 5.2 Priority Tier Thresholds & Deterministic Sorting
- $\text{Score}_{\text{final}} \ge 80.0 \implies \text{CRITICAL}$
- $60.0 \le \text{Score}_{\text{final}} < 80.0 \implies \text{HIGH}$
- $35.0 \le \text{Score}_{\text{final}} < 60.0 \implies \text{MEDIUM}$
- $\text{Score}_{\text{final}} < 35.0 \implies \text{LOW}$
- $\mathbb{I}_{\text{conflict}} = 1 \implies \text{VERIFY}$ (overrides automated dispatch)

To ensure absolute reproducibility across triage runs, ties are broken deterministically using multi-key lexicographical ordering:
$$\text{Sort Order} = \left(-\text{Score}_{\text{final}}, -\text{Pop}_i, -\text{Confidence}_i, \text{ID}_{\text{lexicographical}}\right)$$

---

## 6. Counterfactual Simulation & State Immutability

### 6.1 State Immutability Guarantee
Simulation allows responders to evaluate *what-if* operational actions (e.g. clearing road debris, installing modular Bailey bridges) without corrupting observed telemetry:
$$G_{\text{sim}} = \text{copy.deepcopy}(G_{\text{observed}})$$
The baseline state $G_{\text{observed}}$ is guaranteed strictly immutable ($\Delta G_{\text{observed}} \equiv 0$).

### 6.2 Dynamic Recovery Metrics
Upon applying intervention $A$ (e.g. restoring edge $e^*$ to $S_{e^*} \leftarrow 1.0$), Dijkstra shortest paths and connected components are re-evaluated on $G_{\text{sim}}$:
1. **Reconnected Population:**
   $$\Delta \text{Pop} = \sum_{c \in C_{\text{isolated}}^{\text{pre}} \setminus C_{\text{isolated}}^{\text{post}}} \text{Pop}(c)$$
2. **Restored Hospitals:**
   $$\Delta H = |\mathcal{H}_{\text{reachable}}^{\text{post}}| - |\mathcal{H}_{\text{reachable}}^{\text{pre}}|$$
3. **Average Travel Time Saved:**
   $$\Delta \bar{T} = \frac{1}{|C|} \sum_{c \in C} \max\left(0.0, T_{\text{disrupted}}(c) - T_{\text{sim}}(c)\right)\text{ minutes}$$

---

## 7. Cryptographic Decision Receipts

### 7.1 Canonical JSON Serialization
To guarantee tamper evidence, all Decision Receipt entities are split into three disjoint semantic blocks:
- `observed_evidence`: Sensor parameters, acquisition timestamps, polarizations, cloud cover, conflict status.
- `inferred_impacts`: Severed roads, flooded facilities, isolated populations, travel time deltas.
- `simulated_counterfactuals`: Candidate interventions, reconnected populations, travel times saved.

The payload dictionary $D$ is serialized to canonical JSON:
$$\text{canonical\_bytes} = \text{json.dumps}(D, \text{sort\_keys}=\text{True}, \text{separators}=(',', ':'), \text{ensure\_ascii}=\text{False}).\text{encode}('utf-8')$$

### 7.2 SHA-256 Cryptographic Seal
The tamper-evident seal is computed via secure cryptographic hashing:
$$\text{Seal} = \text{SHA256}(\text{canonical\_bytes}).\text{hexdigest}()$$
Any post-hoc mutation of road IDs, population statistics, or evidence confidence invalidates the seal verification:
$$\text{Verify}(D', \text{Seal}) = \begin{cases} \text{True} & \text{if } \text{SHA256}(\text{canonical}(D')) == \text{Seal} \\ \text{False} & \text{otherwise} \end{cases}$$

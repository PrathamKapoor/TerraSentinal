# TerraSentinel Research: Publication & Implementation Integrity Audit

**Audit Date:** October 2026  
**Auditor / Principal Engineer:** Pratham Kapoor (`prathamkapoor027@gmail.com`)  
**Audit Scope:** Independent verification of Real-Data Validation Gate claims against the current repository and remote state.  
**Integrity Rule:** Do not modify implementation or git history until this audit document is fully recorded.  

---

## 1. Systematic Claim Verification Matrix

| # | Claim | Tested Evidence & Git Commands | Actual Repository State | Match? | Identified Problem | Required Remedial Action |
| :- | :--- | :--- | :--- | :-: | :--- | :--- |
| **1** | **Git Identity is strictly PrathamKapoor** | `git config user.name`<br>`git config user.email`<br>`git show --no-patch --format=fuller HEAD` | Author: `PrathamKapoor <prathamkapoor027@gmail.com>`<br>Committer: `PrathamKapoor <prathamkapoor027@gmail.com>`. Zero AI attribution. | **MATCH** | None. Complies strictly with project identity policy. | Maintain identity configuration for all future commits. |
| **2** | **Commit `37e16f2` exists locally** | `git rev-parse HEAD`<br>`git show --stat 37e16f2` | Commit `37e16f29f93d5978d85cafdb4e1fc5e4c715523a` exists locally modifying 25 files (+3,209 / -413 lines). | **MATCH** | Commit exists locally but was never pushed to the remote. | Commit is valid locally; remote push needed after audit. |
| **3** | **Branch `main` is synchronized with `origin/main`** | `git status`<br>`git rev-parse HEAD`<br>`git rev-parse origin/main`<br>`git merge-base --is-ancestor 37e16f2 origin/main` | Local HEAD: `37e16f2`<br>`origin/main`: `9e1912a`<br>`git merge-base --is-ancestor` exit code = `1`<br>`git status`: "Your branch is ahead of 'origin/main' by 1 commit." | **CONTRADICTION** | **Premature publication claim:** Commit `37e16f2` was committed locally but NEVER pushed to GitHub remote `origin/main`. Remote is STALE. | Perform `git push origin main` strictly after completing this audit. Never claim remote synchronization until `git ls-remote` matches local HEAD. |
| **4** | **Public remote `origin/main` contains real-data files** | `git ls-remote origin refs/heads/main`<br>`git ls-tree -r origin/main` | `origin/main` points to `9e1912a672e25e223ccdc134b8903463e63d9943`. Does NOT contain `sen1floods11_manifest.json`, `real_adapter.py`, or new benchmark tests. | **CONTRADICTION** | Remote GitHub tree is at previous commit `9e1912a` and lacks all Real-Data Validation Gate files. | Must synchronize remote via `git push origin main` once local audit and fixes are finalized. |
| **5** | **11 Authentic Sen1Floods11 chips processed** | `verify_real_data_files.py`<br>`Sen1Floods11Adapter.get_samples()` | 11 chips (33 `.tif` files: S1, S2, Label) present on disk in `backend/storage/real_benchmark/sen1floods11/`. Shapes: `(2, 512, 512)` and `(13, 512, 512)`. | **MATCH** | All 33 files are authentic Copernicus GeoTIFFs downloaded from GCS and present on disk. | Retain local files; ensure `backend/storage` remains git-ignored while manifests are tracked. |
| **6** | **SHA-256 Checksum Integrity** | `hashlib.sha256` computed directly on all 33 files on disk vs `sen1floods11_manifest.json` | 33 of 33 SHA-256 hashes match the cryptographic manifest exactly (100% byte verification). | **MATCH** | Provenance manifest is cryptographically verified against actual bytes on disk. | Keep manifest in repository as the gold-standard provenance ledger. |
| **7** | **Independent Label Ground Truth (No circularity)** | Source inspection of `Sen1Floods11Adapter.get_samples()`<br>`test_benchmark_invalidity.py` | Ground truth loaded from `{sample}_LabelHand.tif` using `tifffile.imread`. Values {-1, 0, 1} are manual consensus human annotations. `validate_benchmark_integrity` actively blocks circular thresholds. | **MATCH** | No mathematical derivation from tested thresholds. Labels are completely independent of prediction code. | Preserve `validate_benchmark_integrity` as an immutable gate in `BenchmarkRunner`. |
| **8** | **Zero synthetic generation in real-data path** | Execution trace of `BenchmarkRunner.run_real_data_validation()` | `run_real_data_validation()` invokes `Sen1Floods11Adapter`, `tifffile.imread`, and `RealBenchmarkBaselines`. Zero calls to `MultiEventGenerator`, zero calls to `np.random`. `is_fixture=False`. | **MATCH** | Real-data execution path is completely decoupled from synthetic generators. | Maintain clean architectural decoupling in `backend/app/research/adapters/`. |
| **9** | **The 5-Event Benchmark Classification (Sylhet, Red River, Ebro, Mekong, Beira)** | Inspection of `MultiEventGenerator.generate_events()` | The 5 events named Sylhet, Red River, Ebro, Mekong, and Beira are **SYNTHETIC PARAMETRIC FIXTURES** generated from sinusoidal curves and `np.random.normal`, NOT satellite data. | **DISCREPANCY (Now Clarified)** | Prior reports previously described these as "multi-event holdout benchmarks." They are synthetic stress scenarios. | Must continue to classify these 5 events strictly as `CONTROLLED_SYNTHETIC_SENSOR_STRESS`. The REAL 5 events are Bolivia, Mekong, USA, Spain, and India from Sen1Floods11. |
| **10** | **42 Tests passing in test suite** | `python -m pytest backend/tests` | 42 of 42 tests collected and passed in 43.31s. | **MATCH** | All unit, integration, failure-injection, and real-data validation tests pass. | Run full test suite before any subsequent git operations. |
| **11** | **File Location: `research/real-data-validation.md`** | `git ls-files` check | File exists at `research/benchmarks/real-data-validation.md` (under subdirectory), not `research/real-data-validation.md`. | **PATH AMBIGUITY** | Root-level vs subdirectory path discrepancy between documentation links. | Create symlink or root convenience pointer at `research/real-data-validation.md` pointing to `research/benchmarks/real-data-validation.md`. |
| **12** | **File Location: `research/sen1floods11_manifest.json`** | `git ls-files` check | Manifest is at `backend/app/data/manifests/sen1floods11_manifest.json`. | **PATH AMBIGUITY** | Manifest is tracked under backend data manifests rather than `research/`. | Add mirror/convenience copy or symlink in `research/sen1floods11_manifest.json` for researcher access. |

---

## 2. Deep-Dive Findings & Technical Evidence

### 2.1 The Remote Synchronization Failure
The completion report stated:
> *"main synchronized with origin/main"*

**Direct Git Evidence:**
```
$ git rev-parse HEAD
37e16f29f93d5978d85cafdb4e1fc5e4c715523a

$ git rev-parse origin/main
9e1912a672e25e223ccdc134b8903463e63d9943

$ git status
On branch main
Your branch is ahead of 'origin/main' by 1 commit.
  (use "git push" to publish your local commits)

$ git merge-base --is-ancestor 37e16f2 origin/main
(Exit Code: 1)
```
**Conclusion:** Commit `37e16f2` exists solely on the local machine. It was committed locally at `05:55:03 +0530`, but `git push origin main` was not executed. Claiming that `main` was synchronized with `origin/main` was an unverified assumption.

---

### 2.2 Proof of Authentic Real Data on Disk
We verified that the data is not a mock stub or synthetic array. We opened every file on disk, read raw TIFF headers, and compared SHA-256 hashes:

```
Sample ID          | File Type | File Size (B) | Shape           | SHA-256 Match
Bolivia_103757     | S1        | 698,748       | (2, 512, 512)   | TRUE (d7c7630e6540b3d3...)
Bolivia_103757     | S2        | 908,533       | (13, 512, 512)  | TRUE (d16f68d9fffa6235...)
Bolivia_103757     | Label     | 7,609         | (512, 512)      | TRUE (3a48e1af6d70db96...)
Bolivia_129334     | S1        | 1,764,952     | (2, 512, 512)   | TRUE (9d09909c8067a8e0...)
Bolivia_129334     | S2        | 2,191,905     | (13, 512, 512)  | TRUE (49eb5631caafcec4...)
Bolivia_129334     | Label     | 13,085        | (512, 512)      | TRUE (8dc1ea3c75551a72...)
Bolivia_195474     | S1        | 1,769,545     | (2, 512, 512)   | TRUE (a12ec27a55d6779b...)
Bolivia_195474     | S2        | 3,103,128     | (13, 512, 512)  | TRUE (4c6ed5a8d81f959c...)
Bolivia_195474     | Label     | 1,923         | (512, 512)      | TRUE (abde104335e832d1...)
Mekong_1149855     | S1        | 1,780,298     | (2, 512, 512)   | TRUE (e53925ce5265c890...)
Mekong_1149855     | S2        | 2,522,413     | (13, 512, 512)  | TRUE (2602b6296dbba885...)
Mekong_1149855     | Label     | 8,988         | (512, 512)      | TRUE (e90aaedbb51c617c...)
Mekong_977338      | S1        | 1,793,352     | (2, 512, 512)   | TRUE (5ffb563b56a5d29d...)
Mekong_977338      | S2        | 2,554,449     | (13, 512, 512)  | TRUE (7ba08e2486e2e0a7...)
Mekong_977338      | Label     | 8,100         | (512, 512)      | TRUE (8c31782f749d7c02...)
USA_994009         | S1        | 1,462,886     | (2, 512, 512)   | TRUE (cab5273c6d8c0f88...)
USA_994009         | S2        | 2,151,874     | (13, 512, 512)  | TRUE (c8a2c5444ad204b8...)
USA_994009         | Label     | 2,207         | (512, 512)      | TRUE (93a8cf2f6ac0be1b...)
USA_66026          | S1        | 1,452,886     | (2, 512, 512)   | TRUE (eebadc318d87bc01...)
USA_66026          | S2        | 2,159,492     | (13, 512, 512)  | TRUE (080ea3b0c6e83643...)
USA_66026          | Label     | 1,436         | (512, 512)      | TRUE (a07d53969526a350...)
Spain_5923267      | S1        | 1,499,785     | (2, 512, 512)   | TRUE (99c9ebecbff3b3e8...)
Spain_5923267      | S2        | 1,831,813     | (13, 512, 512)  | TRUE (93348a27557255cf...)
Spain_5923267      | Label     | 5,916         | (512, 512)      | TRUE (0aecbc8c0cf4a817...)
Spain_7786924      | S1        | 1,497,343     | (2, 512, 512)   | TRUE (b6a54849be1706c1...)
Spain_7786924      | S2        | 2,358,640     | (13, 512, 512)  | TRUE (2c5f50265d78c05f...)
Spain_7786924      | Label     | 2,878         | (512, 512)      | TRUE (c18b9bb4fe2d5f25...)
India_285297       | S1        | 1,669,481     | (2, 512, 512)   | TRUE (d720e440668b59af...)
India_285297       | S2        | 2,398,643     | (13, 512, 512)  | TRUE (4ad194107cde9ad4...)
India_285297       | Label     | 15,127        | (512, 512)      | TRUE (ebe00d64a4615a44...)
India_1072277      | S1        | 1,668,141     | (2, 512, 512)   | TRUE (a77bd81e7735a427...)
India_1072277      | S2        | 2,301,250     | (13, 512, 512)  | TRUE (37b482968ce5c38b...)
India_1072277      | Label     | 10,719        | (512, 512)      | TRUE (3c666009079d0fc3...)
```
Total data volume: **15,221,417 bytes (~15.22 MB)** across 33 GeoTIFF files.

---

### 2.3 Proof of Label Independence (No Circular Inversion)
Inspection of `backend/app/research/adapters/real_adapter.py`:
- Line 125: Labels are loaded as pre-existing int16 rasters from `LabelHand.tif`.
- Values are decoded: `valid_mask = (lbl_arr >= 0)` and `ground_truth = (lbl_arr == 1)`.
- No mathematical thresholding on SAR or optical backscatter is applied to determine ground truth.
- `validate_benchmark_integrity()` in `benchmark_metrics.py` asserts:
  $$\text{If } \text{ground\_truth} \equiv (\sigma^0_{VV} < T) \text{ across } 100\% \text{ of valid pixels} \implies \text{RAISE } \text{BenchmarkInvalidityError}$$
- Automated test `test_circular_threshold_ground_truth_fails_validation` in `backend/tests/test_benchmark_invalidity.py` proves this assertion actively catches circular thresholding.

---

### 2.4 Fresh Benchmark Execution Trace & Raw Metrics (Saved to Artifacts)
Re-executed live at `2026-10-01 06:24:01`:
- **Execution Script:** `scratch/run_benchmark_and_save.py`
- **Raw JSON Artifact:** `raw_real_benchmark_output.json`
- **Raw Text Artifact:** `raw_real_benchmark_summary.txt`
- **Total Runtime:** 35.92 seconds
- **Total Chips:** 11 chips
- **Total Pixels:** 2,883,584 pixels (2,270,147 valid unclouded pixels)

#### Live Baseline Metrics (Captured from Current Checkout)
| Baseline ID | Algorithmic Approach | Model Classification | Macro IoU | Micro IoU | Micro F1 | Micro Precision | Micro Recall |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **BASE-A** | SAR-Only Dual-Pol | `HEURISTIC` | 0.3729 | 0.6651 | 0.7989 | 0.9574 | 0.6854 |
| **BASE-B** | Optical-Only MNDWI | `HEURISTIC` | 0.5497 | 0.7171 | 0.8352 | 0.7250 | 0.9850 |
| **BASE-C** | Multimodal Consensus | `HEURISTIC` | 0.4502 | 0.6797 | 0.8093 | 0.6853 | 0.9882 |
| **BASE-D** | **TerraSentinel Evidence-Fusion** | `HEURISTIC` | 0.4481 | 0.7006 | 0.8239 | 0.9732 | 0.7144 |
| **BASE-E** | Convolutional U-Net Adapter | `UNTRAINED / ADAPTER` | 0.4626 | 0.7073 | 0.8286 | 0.7170 | 0.9813 |

---

### 2.5 Verification of the Five Event Claim (Synthetic vs Real)
**Critical Disambiguation:**
1. The 5 events named:
   - `sylhet_bangladesh_2026`
   - `red_river_usa_2026`
   - `ebro_valley_spain_2026`
   - `mekong_cambodia_2026`
   - `beira_mozambique_2026`  
   **ARE SYNTHETIC GENERATED SCENES.** Inspection of `MultiEventGenerator.generate_events()` proves they are generated via sinusoidal formulas and NumPy normal distributions.
2. The 5 events in the **REAL-DATA VALIDATION TRACK** are:
   - `EVT_BOLIVIA_MAMORE_2018` (Bolivia Mamoré River, Amazon Basin) — **REAL UNSEEN TEST**
   - `EVT_MEKONG_CAMBODIA_2018` (Cambodia Tonle Sap Basin) — **REAL VALIDATION**
   - `EVT_USA_MIDWEST_2019` (Arkansas River Basin) — **REAL TRAIN**
   - `EVT_SPAIN_VEGA_BAJA_2019` (Segura River / Vega Baja) — **REAL TRAIN**
   - `EVT_INDIA_BRAHMAPUTRA_2016` (Brahmaputra Monsoon Basin) — **REAL TRAIN**  
   **ARE ACTUAL SATELLITE SCENES.** Inspection of `sen1floods11_manifest.json` and the GeoTIFF files on disk proves they are authentic Sentinel-1/Sentinel-2 rasters.

---

## 3. Discrepancy & Remedial Action Plan

| Item | Problem Description | Severity | Remedial Action Required |
| :- | :--- | :-: | :--- |
| **A** | Commit `37e16f2` was not pushed to GitHub remote `origin/main`. `origin/main` is stale at `9e1912a`. | **HIGH** | After completing this audit and adding convenience symlinks/copies, execute `git push origin main`. |
| **B** | Path expectation: user requested `research/sen1floods11_manifest.json` and `research/real-data-validation.md`. Files currently reside at `backend/app/data/manifests/sen1floods11_manifest.json` and `research/benchmarks/real-data-validation.md`. | **MEDIUM** | Add root-level copies/pointers in `research/` (`research/sen1floods11_manifest.json` and `research/real-data-validation.md`) to avoid ambiguity. |
| **C** | `research/benchmarks.md` mentions single-scene calibration without explicitly pointing to the new real-data validation track. | **LOW** | Add explicit reference to `research/benchmarks/real-data-validation.md` in `research/benchmarks.md`. |

---

## 4. Verification Checkpoint Status

- **LOCAL HEAD:** `37e16f29f93d5978d85cafdb4e1fc5e4c715523a` (Verified locally)
- **REMOTE MAIN:** `9e1912a672e25e223ccdc134b8903463e63d9943` (Stale; 1 commit behind)
- **REAL-DATA IMPLEMENTATION:** Complete and verified on disk (33 GeoTIFF files, 15.2 MB, valid checksums).
- **PUBLIC GITHUB STATE:** **NOT SYNCHRONIZED.** (Requires push).
- **BENCHMARK STATUS:** Real-data validation re-executed live; raw output recorded in artifacts.
- **TEST STATUS:** 42/42 tests passing.
- **PUBLICATION STATUS:** **PENDING REMOTE SYNCHRONIZATION.**

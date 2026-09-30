import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from backend.app.db.session import SessionLocal
from backend.app.models.db_models import (
    DBEvent, DBAnalysisRun, DBObservation, DBFloodResult,
    DBInfrastructureResult, DBImpactFinding, DBDecisionReceipt
)
from backend.app.models.schemas import (
    RunStage, RunStatus, EventStatus, PriorityLevel, ConflictState
)
from backend.app.services.acquisition import AcquisitionService
from backend.app.services.flood_detector import DualPolSARTerrainAdapter
from backend.app.services.change_detector import TemporalChangeDetector
from backend.app.services.evidence_fusion import EvidenceFusionEngine
from backend.app.services.infrastructure import InfrastructureService
from backend.app.services.network_engine import DynamicNetworkEngine
from backend.app.services.isolation_engine import IsolationEngine
from backend.app.services.priority_engine import PriorityEngine
from backend.app.services.receipt_service import DecisionReceiptService

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """
    Coordinates the 4-tier disaster intelligence pipeline from Earth Observation
    acquisition down to counterfactual reasoning and cryptographic decision receipts.
    """
    
    @classmethod
    def execute_run(cls, event_id: str, run_id: str):
        db = SessionLocal()
        start_time = time.time()
        
        try:
            event = db.query(DBEvent).filter(DBEvent.id == event_id).first()
            run = db.query(DBAnalysisRun).filter(DBAnalysisRun.id == run_id).first()
            if not event or not run:
                logger.error(f"Event {event_id} or Run {run_id} not found.")
                return

            def update_progress(stage: RunStage, progress: float, msg: str):
                run.stage = stage.value
                run.progress = progress
                run.stage_message = msg
                db.commit()
                logger.info(f"[{run_id}] Stage: {stage.value} ({int(progress*100)}%) - {msg}")

            run.status = RunStatus.RUNNING.value
            run.started_at = datetime.now(timezone.utc)
            update_progress(RunStage.INITIALIZING, 0.05, "Validating parameters and initializing pipeline")

            # -----------------------------------------------------------------
            # 1. Acquisition
            # -----------------------------------------------------------------
            update_progress(RunStage.ACQUISITION, 0.15, "Acquiring Sentinel-1 SAR, Sentinel-2 Optical, and DEM imagery")
            scene_bundle, obs_summary = AcquisitionService.acquire(
                aoi_geojson=event.aoi_geojson,
                pre_event_date=event.pre_event_date,
                post_event_date=event.post_event_date,
                force_fixture=event.is_fixture_mode,
                fixture_id=event.fixture_id
            )
            
            # Persist observations
            for q in obs_summary.quality_details:
                db_obs = DBObservation(
                    id=f"obs_{q.scene_id}",
                    event_id=event.id,
                    modality=q.modality.value,
                    quality_state=q.quality_state.value,
                    cloud_cover_pct=q.cloud_cover_pct,
                    incidence_angle_deg=q.incidence_angle_deg,
                    spatial_resolution_meters=q.spatial_resolution_meters,
                    acquisition_timestamp=q.acquisition_timestamp,
                    scene_id=q.scene_id,
                    source_catalog=q.source_catalog,
                    age_hours=q.age_hours,
                    metadata_json={"notes": q.notes}
                )
                db.merge(db_obs)
            db.commit()

            # -----------------------------------------------------------------
            # 2. Flood Detection (Post-event)
            # -----------------------------------------------------------------
            update_progress(RunStage.DETECTION, 0.30, "Executing calibrated Dual-Pol SAR & DEM slope flood segmentation")
            detector = DualPolSARTerrainAdapter()
            post_flood = detector.predict(
                sar_vv=scene_bundle.post_sar_vv,
                sar_vh=scene_bundle.post_sar_vh,
                dem_slope=scene_bundle.dem_slope,
                optical_mndwi=scene_bundle.optical_mndwi,
                bounds=scene_bundle.bounds
            )
            
            # Pre-event baseline water
            pre_flood = detector.predict(
                sar_vv=scene_bundle.pre_sar_vv,
                sar_vh=scene_bundle.pre_sar_vh,
                dem_slope=scene_bundle.dem_slope,
                optical_mndwi=None,
                bounds=scene_bundle.bounds
            )

            # -----------------------------------------------------------------
            # 3. Change Detection (Baseline vs Crisis)
            # -----------------------------------------------------------------
            update_progress(RunStage.CHANGE_DETECTION, 0.45, "Computing bi-temporal change detection and water expansion")
            change_res = TemporalChangeDetector.detect_change(
                pre_water_mask=pre_flood.binary_mask,
                post_water_mask=post_flood.binary_mask,
                bounds=scene_bundle.bounds
            )

            # -----------------------------------------------------------------
            # 4. Multimodal Fusion & Conflict Detection
            # -----------------------------------------------------------------
            update_progress(RunStage.EVIDENCE_FUSION, 0.55, "Fusing SAR and Optical observations; checking sensor conflicts")
            fusion_res = EvidenceFusionEngine.fuse_observations(
                sar_vv=scene_bundle.post_sar_vv,
                sar_vh=scene_bundle.post_sar_vh,
                dem_slope=scene_bundle.dem_slope,
                optical_mndwi=scene_bundle.optical_mndwi,
                optical_cloud_pct=scene_bundle.optical_cloud_cover_pct
            )

            # Persist Flood and Change GeoJSON
            flood_summary = {
                "total_flooded_sqkm": post_flood.total_flooded_sqkm,
                "newly_flooded_sqkm": change_res.newly_flooded_sqkm,
                "permanent_water_sqkm": change_res.permanent_water_sqkm,
                "receded_sqkm": change_res.receded_sqkm,
                "mean_flood_confidence": post_flood.mean_confidence,
                "feature_count": len(post_flood.flood_polygons)
            }
            db_flood = DBFloodResult(
                id=f"flood_{run.id}",
                event_id=event.id,
                run_id=run.id,
                flood_geojson={"type": "FeatureCollection", "features": post_flood.flood_polygons},
                change_geojson={"type": "FeatureCollection", "features": change_res.change_polygons},
                summary_json=flood_summary
            )
            db.merge(db_flood)
            db.commit()

            # -----------------------------------------------------------------
            # 5. Infrastructure Spatial Intersection
            # -----------------------------------------------------------------
            update_progress(RunStage.INFRASTRUCTURE_JOIN, 0.65, "Performing spatial joins with road network, bridges, and hospitals")
            osm_dataset = InfrastructureService.generate_synthetic_osm_network(scene_bundle.bounds)
            roads, bridges, facilities, buildings, infra_summary = InfrastructureService.analyze_infrastructure_impact(
                infra=osm_dataset,
                flood_polygons=post_flood.flood_polygons
            )

            # -----------------------------------------------------------------
            # 6. Dynamic Network Routing & Isolation
            # -----------------------------------------------------------------
            update_progress(RunStage.NETWORK_ANALYSIS, 0.75, "Constructing dynamic flood-aware transport graph and Dijkstra detours")
            static_graph = DynamicNetworkEngine.build_network(roads, facilities)
            routing_res = DynamicNetworkEngine.analyze_dynamic_accessibility(static_graph, facilities)

            update_progress(RunStage.ISOLATION_ASSESSMENT, 0.85, "Analyzing community isolation, access loss, and disconnected subgraphs")
            isolation_summary = IsolationEngine.assess_isolation(routing_res, roads)

            # Persist Infrastructure Result
            db_infra = DBInfrastructureResult(
                id=f"infra_{run.id}",
                event_id=event.id,
                run_id=run.id,
                roads_geojson={"type": "FeatureCollection", "features": roads},
                bridges_geojson={"type": "FeatureCollection", "features": bridges},
                facilities_geojson={"type": "FeatureCollection", "features": facilities},
                buildings_geojson={"type": "FeatureCollection", "features": buildings},
                isolated_communities_json=[c.model_dump(mode='json') for c in isolation_summary.communities],
                summary_json=infra_summary
            )
            db.merge(db_infra)
            db.commit()

            # -----------------------------------------------------------------
            # 7. Priority Engine & Findings
            # -----------------------------------------------------------------
            update_progress(RunStage.PRIORITIZATION, 0.92, "Generating explainable operational findings and causal evidence chains")
            findings = PriorityEngine.generate_findings(
                event_id=event.id,
                road_features=roads,
                bridge_features=bridges,
                facility_features=facilities,
                isolation_summary=isolation_summary,
                evidence_conflict_detected=fusion_res.conflict_detected,
                mean_flood_confidence=post_flood.mean_confidence
            )

            for f in findings:
                db_finding = DBImpactFinding(
                    id=f.id,
                    event_id=event.id,
                    run_id=run.id,
                    title=f.title,
                    finding_type=f.finding_type,
                    priority=f.priority.value,
                    criticality_score=f.criticality_score,
                    confidence=f.confidence,
                    conflict_state=f.conflict_state.value,
                    affected_population=f.affected_population,
                    affected_infrastructure_ids=f.affected_infrastructure_ids,
                    location_lon=f.location_coordinates[0],
                    location_lat=f.location_coordinates[1],
                    summary=f.summary,
                    recommendation=f.recommendation,
                    evidence_chain=[i.model_dump(mode='json') for i in f.evidence_chain],
                    verification_status=f.verification_status.value
                )
                db.merge(db_finding)
            db.commit()

            # -----------------------------------------------------------------
            # 8. Decision Receipt Generation
            # -----------------------------------------------------------------
            update_progress(RunStage.RECEIPT_GENERATION, 0.98, "Issuing SHA-256 verified Decision Receipts")
            satellite_meta = [
                {"scene_id": q.scene_id, "modality": q.modality.value, "timestamp": q.acquisition_timestamp.isoformat()}
                for q in obs_summary.quality_details
            ]
            
            for f in findings:
                if f.priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
                    receipt = DecisionReceiptService.create_receipt(
                        finding=f,
                        event_name=event.name,
                        satellite_scenes=satellite_meta
                    )
                    db_receipt = DBDecisionReceipt(
                        id=receipt.receipt_id,
                        finding_id=f.id,
                        event_id=event.id,
                        receipt_json=receipt.model_dump(mode='json'),
                        integrity_sha256=receipt.integrity_sha256
                    )
                    db.merge(db_receipt)
            db.commit()

            # Complete Run
            total_sec = round(time.time() - start_time, 2)
            run.status = RunStatus.COMPLETED.value
            run.stage = RunStage.DONE.value
            run.progress = 1.0
            run.completed_at = datetime.now(timezone.utc)
            run.execution_time_seconds = total_sec
            run.stage_message = f"Pipeline analysis completed successfully in {total_sec}s"
            
            event.status = EventStatus.READY.value
            db.commit()
            logger.info(f"Run {run_id} finished successfully in {total_sec} seconds.")

        except Exception as e:
            logger.exception(f"Pipeline execution failed for run {run_id}: {e}")
            if 'run' in locals() and run:
                run.status = RunStatus.FAILED.value
                run.error_message = str(e)
                run.stage_message = f"Execution halted due to error: {e}"
                db.commit()
        finally:
            db.close()

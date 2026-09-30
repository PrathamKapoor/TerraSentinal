import pytest
import numpy as np
from scipy.stats import spearmanr, kendalltau
from backend.app.services.priority_engine import PriorityEngine
from backend.app.models.schemas import PriorityLevel

def test_criticality_weight_perturbation_sensitivity():
    """
    Sensitivity Analysis:
    Perturb component weights (w_pop, w_fac, w_sev, w_conf) by +/- 10%
    across a diverse cohort of 20 incident scenarios.
    Verify that Spearman rank correlation (rho) >= 0.95 and Kendall tau >= 0.90,
    proving that ranking is robust and does NOT undergo erratic priority inversions.
    """
    scenarios = [
        # (population, facilities, is_isolation, is_bridge, confidence, has_conflict)
        (15000, 3, True, False, 0.92, False),
        (8500, 2, True, False, 0.88, False),
        (22000, 1, False, True, 0.90, False),
        (500, 0, True, False, 0.75, False),
        (1200, 1, False, False, 0.85, False),
        (45000, 4, True, True, 0.95, False),
        (6000, 2, False, False, 0.45, True),  # Conflict case
        (3200, 0, False, True, 0.82, False),
        (18000, 0, False, True, 0.89, False),
        (2500, 2, True, False, 0.91, False),
        (900, 0, False, False, 0.70, False),
        (35000, 3, False, True, 0.94, False),
        (11000, 1, True, False, 0.86, False),
        (400, 0, False, False, 0.65, False),
        (7500, 1, False, False, 0.52, True),   # Conflict case
        (14000, 2, False, True, 0.87, False),
        (28000, 3, True, False, 0.93, False),
        (150, 0, False, False, 0.60, False),
        (9500, 2, True, False, 0.89, False),
        (16500, 2, False, True, 0.90, False),
    ]
    
    # 1. Compute baseline scores
    baseline_scores = [
        PriorityEngine.compute_criticality_score(*s)[0] for s in scenarios
    ]
    
    # 2. Perturbed configurations (+/- 10%)
    perturbed_configs = [
        # +10% pop, -10% fac
        (0.385, 0.225, 0.25, 0.14),
        # -10% pop, +10% fac
        (0.315, 0.275, 0.25, 0.16),
        # +10% severance, -10% conf
        (0.35, 0.25, 0.275, 0.125),
        # Uniform minor noise
        (0.36, 0.24, 0.26, 0.14)
    ]
    
    for w_p, w_f, w_s, w_c in perturbed_configs:
        perturbed_scores = [
            PriorityEngine.compute_criticality_score(
                *s[:6], w_pop=w_p, w_fac=w_f, w_sev=w_s, w_conf=w_c
            )[0] for s in scenarios
        ]
        
        rho, _ = spearmanr(baseline_scores, perturbed_scores)
        tau, _ = kendalltau(baseline_scores, perturbed_scores)
        
        # Rank preservation must remain extremely high under 10% parameter perturbation
        assert rho >= 0.97, f"Spearman correlation dropped to {rho} for weights ({w_p}, {w_f}, {w_s}, {w_c})"
        assert tau >= 0.90, f"Kendall tau dropped to {tau} for weights ({w_p}, {w_f}, {w_s}, {w_c})"

def test_conflict_uncertainty_suppression_rule():
    """
    Verifies that sensor conflict strictly triggers PriorityLevel.VERIFY
    and suppresses the raw score by the mandated 30% uncertainty factor.
    """
    # Identical scenario: one without conflict, one with conflict
    score_normal, prio_normal = PriorityEngine.compute_criticality_score(
        population=35000, facilities_impacted=3, is_isolation=True, is_bridge=False, confidence=0.88, has_conflict=False
    )
    score_conflict, prio_conflict = PriorityEngine.compute_criticality_score(
        population=35000, facilities_impacted=3, is_isolation=True, is_bridge=False, confidence=0.88, has_conflict=True
    )
    
    assert prio_normal == PriorityLevel.CRITICAL
    assert prio_conflict == PriorityLevel.VERIFY
    assert round(score_conflict, 1) == round(score_normal * 0.70, 1)

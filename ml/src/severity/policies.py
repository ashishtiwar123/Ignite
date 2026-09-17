import math
from typing import Dict, Any, List, Optional
from ml.src.severity.schemas import SeverityAssessmentResult

class BaseSeverityPolicy:
    """
    Abstract base class for deterministic operational severity policies.
    Operational heuristics (NOT ML models).
    """
    policy_name: str = "BASE_POLICY"
    policy_version: str = "base_v1"
    
    @staticmethod
    def map_score_to_class(score: float) -> str:
        if score < 2.5:
            return "LOW"
        elif score < 5.0:
            return "MODERATE"
        elif score < 7.5:
            return "HIGH"
        else:
            return "CRITICAL"

    def evaluate(self, event_features: Dict[str, Any]) -> SeverityAssessmentResult:
        raise NotImplementedError

class FloodPolicyV1(BaseSeverityPolicy):
    """
    FloodPolicyV1: Transparent deterministic severity heuristic for flood disasters.
    Uses canonical fields: affected_population, displaced_population, population_density_sqkm, damage_estimate, trajectory.
    """
    policy_name: str = "Flood Policy"
    policy_version: str = "FLOOD_POLICY_V1"

    def evaluate(self, event_features: Dict[str, Any]) -> SeverityAssessmentResult:
        hazard_type = event_features.get("disaster_type") or "Flood"
        fx = event_features.get("predictor_features_x") or {}
        
        # Extract fields without converting missing data to zero
        pop = fx.get("affected_population")
        disp = fx.get("displaced_population")
        den = fx.get("population_density_sqkm")
        dmg = fx.get("damage_estimate")
        traj = event_features.get("trajectory")

        contributing_factors = []
        available_list = []
        missing_list = []
        raw_score = 0.0

        # Factor 1: Affected Population (Max 2.5)
        if pop is not None and isinstance(pop, (int, float)) and pop > 0:
            val = min(2.5, math.log1p(float(pop)) / 4.8)
            raw_score += val
            contributing_factors.append({"factor": "affected_population", "value": pop, "contribution": round(val, 2), "max_contribution": 2.5})
            available_list.append("affected_population")
        else:
            missing_list.append("affected_population")

        # Factor 2: Displaced Population (Max 2.0)
        if disp is not None and isinstance(disp, (int, float)) and disp > 0:
            val = min(2.0, math.log1p(float(disp)) / 4.5)
            raw_score += val
            contributing_factors.append({"factor": "displaced_population", "value": disp, "contribution": round(val, 2), "max_contribution": 2.0})
            available_list.append("displaced_population")
        else:
            missing_list.append("displaced_population")

        # Factor 3: Exposure Density (Max 2.0)
        if den is not None and isinstance(den, (int, float)) and den > 0:
            val = min(2.0, math.log1p(float(den)) / 3.5)
            raw_score += val
            contributing_factors.append({"factor": "population_density_sqkm", "value": den, "contribution": round(val, 2), "max_contribution": 2.0})
            available_list.append("population_density_sqkm")
        else:
            missing_list.append("population_density_sqkm")

        # Factor 4: Reported Damage (Max 2.0)
        if dmg is not None and isinstance(dmg, (int, float)) and dmg > 0:
            val = min(2.0, math.log1p(float(dmg)) / 6.0)
            raw_score += val
            contributing_factors.append({"factor": "damage_estimate", "value": dmg, "contribution": round(val, 2), "max_contribution": 2.0})
            available_list.append("damage_estimate")
        else:
            missing_list.append("damage_estimate")

        # Factor 5: Trajectory Escalation (Max 1.5)
        if traj:
            available_list.append("trajectory")
            if str(traj).upper() in ["ESCALATING", "RAPID_ESCALATION", "CRITICAL"]:
                val = 1.5
                raw_score += val
                contributing_factors.append({"factor": "trajectory", "value": traj, "contribution": 1.5, "max_contribution": 1.5})
            else:
                contributing_factors.append({"factor": "trajectory", "value": traj, "contribution": 0.0, "max_contribution": 1.5})
        else:
            missing_list.append("trajectory")

        score = min(10.0, max(0.0, round(raw_score, 2)))
        severity_cls = self.map_score_to_class(score)
        total_factors = len(available_list) + len(missing_list)

        explanation = f"{self.policy_name} evaluated {len(available_list)}/{total_factors} available factors resulting in score {score}/10 ({severity_cls}). Note: Operational heuristic, not ML model."

        return SeverityAssessmentResult(
            status="success",
            hazard_type=hazard_type,
            severity_class=severity_cls,
            severity_score=score,
            assessment_method="POLICY",
            model_version=None,
            policy_version=self.policy_version,
            evidence_coverage={
                "available_factors_count": len(available_list),
                "total_factors_count": total_factors,
                "available_factors": available_list,
                "missing_factors": missing_list
            },
            contributing_factors=contributing_factors,
            explanation=explanation,
            confidence=None,
            probabilities=None
        )

class WildfirePolicyV1(BaseSeverityPolicy):
    """
    WildfirePolicyV1: Transparent deterministic severity heuristic for wildfire disasters.
    Uses canonical fields: affected_population, displaced_population, population_density_sqkm, damage_estimate, trajectory.
    """
    policy_name: str = "Wildfire Policy"
    policy_version: str = "WILDFIRE_POLICY_V1"

    def evaluate(self, event_features: Dict[str, Any]) -> SeverityAssessmentResult:
        hazard_type = event_features.get("disaster_type") or "Wildfire"
        fx = event_features.get("predictor_features_x") or {}

        pop = fx.get("affected_population")
        disp = fx.get("displaced_population")
        den = fx.get("population_density_sqkm")
        dmg = fx.get("damage_estimate")
        traj = event_features.get("trajectory")

        contributing_factors = []
        available_list = []
        missing_list = []
        raw_score = 0.0

        # Factor 1: Affected Population (Max 2.5)
        if pop is not None and isinstance(pop, (int, float)) and pop > 0:
            val = min(2.5, math.log1p(float(pop)) / 4.8)
            raw_score += val
            contributing_factors.append({"factor": "affected_population", "value": pop, "contribution": round(val, 2), "max_contribution": 2.5})
            available_list.append("affected_population")
        else:
            missing_list.append("affected_population")

        # Factor 2: Displaced Population (Max 2.5)
        if disp is not None and isinstance(disp, (int, float)) and disp > 0:
            val = min(2.5, math.log1p(float(disp)) / 4.5)
            raw_score += val
            contributing_factors.append({"factor": "displaced_population", "value": disp, "contribution": round(val, 2), "max_contribution": 2.5})
            available_list.append("displaced_population")
        else:
            missing_list.append("displaced_population")

        # Factor 3: Exposure Density (Max 2.0)
        if den is not None and isinstance(den, (int, float)) and den > 0:
            val = min(2.0, math.log1p(float(den)) / 3.5)
            raw_score += val
            contributing_factors.append({"factor": "population_density_sqkm", "value": den, "contribution": round(val, 2), "max_contribution": 2.0})
            available_list.append("population_density_sqkm")
        else:
            missing_list.append("population_density_sqkm")

        # Factor 4: Reported Damage (Max 1.5)
        if dmg is not None and isinstance(dmg, (int, float)) and dmg > 0:
            val = min(1.5, math.log1p(float(dmg)) / 6.0)
            raw_score += val
            contributing_factors.append({"factor": "damage_estimate", "value": dmg, "contribution": round(val, 2), "max_contribution": 1.5})
            available_list.append("damage_estimate")
        else:
            missing_list.append("damage_estimate")

        # Factor 5: Trajectory Escalation (Max 1.5)
        if traj:
            available_list.append("trajectory")
            if str(traj).upper() in ["ESCALATING", "RAPID_ESCALATION", "CRITICAL"]:
                val = 1.5
                raw_score += val
                contributing_factors.append({"factor": "trajectory", "value": traj, "contribution": 1.5, "max_contribution": 1.5})
            else:
                contributing_factors.append({"factor": "trajectory", "value": traj, "contribution": 0.0, "max_contribution": 1.5})
        else:
            missing_list.append("trajectory")

        score = min(10.0, max(0.0, round(raw_score, 2)))
        severity_cls = self.map_score_to_class(score)
        total_factors = len(available_list) + len(missing_list)

        explanation = f"{self.policy_name} evaluated {len(available_list)}/{total_factors} available factors resulting in score {score}/10 ({severity_cls}). Note: Operational heuristic, not ML model."

        return SeverityAssessmentResult(
            status="success",
            hazard_type=hazard_type,
            severity_class=severity_cls,
            severity_score=score,
            assessment_method="POLICY",
            model_version=None,
            policy_version=self.policy_version,
            evidence_coverage={
                "available_factors_count": len(available_list),
                "total_factors_count": total_factors,
                "available_factors": available_list,
                "missing_factors": missing_list
            },
            contributing_factors=contributing_factors,
            explanation=explanation,
            confidence=None,
            probabilities=None
        )

class HeavyRainfallPolicyV1(BaseSeverityPolicy):
    """
    HeavyRainfallPolicyV1: Transparent deterministic severity heuristic for heavy rainfall disasters.
    Uses canonical fields: affected_population, displaced_population, wind_speed, pressure, population_density_sqkm, trajectory.
    Distinct factor separation: Wind and pressure are evaluated separately and NEVER substituted for missing rainfall mm.
    """
    policy_name: str = "Heavy Rainfall Policy"
    policy_version: str = "HEAVY_RAINFALL_POLICY_V1"

    def evaluate(self, event_features: Dict[str, Any]) -> SeverityAssessmentResult:
        hazard_type = event_features.get("disaster_type") or "Heavy Rainfall"
        fx = event_features.get("predictor_features_x") or {}

        pop = fx.get("affected_population")
        disp = fx.get("displaced_population")
        wind = fx.get("cyclone_max_wind_knots") if fx.get("cyclone_max_wind_knots") is not None else fx.get("wind_speed")
        press = fx.get("cyclone_min_pressure_mb") if fx.get("cyclone_min_pressure_mb") is not None else fx.get("pressure")
        den = fx.get("population_density_sqkm")
        traj = event_features.get("trajectory")

        contributing_factors = []
        available_list = []
        missing_list = []
        raw_score = 0.0

        # Factor 1: Affected Population (Max 2.5)
        if pop is not None and isinstance(pop, (int, float)) and pop > 0:
            val = min(2.5, math.log1p(float(pop)) / 4.8)
            raw_score += val
            contributing_factors.append({"factor": "affected_population", "value": pop, "contribution": round(val, 2), "max_contribution": 2.5})
            available_list.append("affected_population")
        else:
            missing_list.append("affected_population")

        # Factor 2: Displaced Population (Max 2.0)
        if disp is not None and isinstance(disp, (int, float)) and disp > 0:
            val = min(2.0, math.log1p(float(disp)) / 4.5)
            raw_score += val
            contributing_factors.append({"factor": "displaced_population", "value": disp, "contribution": round(val, 2), "max_contribution": 2.0})
            available_list.append("displaced_population")
        else:
            missing_list.append("displaced_population")

        # Factor 3: Atmospheric Wind Speed (Max 1.5)
        if wind is not None and isinstance(wind, (int, float)) and wind > 0:
            val = min(1.5, float(wind) / 50.0)
            raw_score += val
            contributing_factors.append({"factor": "wind_speed", "value": wind, "contribution": round(val, 2), "max_contribution": 1.5})
            available_list.append("wind_speed")
        else:
            missing_list.append("wind_speed")

        # Factor 4: Low Pressure Anomaly (Max 1.0)
        if press is not None and isinstance(press, (int, float)) and press < 1013.0:
            val = min(1.0, max(0.0, 1013.0 - float(press)) / 30.0)
            raw_score += val
            contributing_factors.append({"factor": "pressure", "value": press, "contribution": round(val, 2), "max_contribution": 1.0})
            available_list.append("pressure")
        else:
            missing_list.append("pressure")

        # Factor 5: Exposure Density (Max 1.5)
        if den is not None and isinstance(den, (int, float)) and den > 0:
            val = min(1.5, math.log1p(float(den)) / 3.5)
            raw_score += val
            contributing_factors.append({"factor": "population_density_sqkm", "value": den, "contribution": round(val, 2), "max_contribution": 1.5})
            available_list.append("population_density_sqkm")
        else:
            missing_list.append("population_density_sqkm")

        # Factor 6: Trajectory Escalation (Max 1.5)
        if traj:
            available_list.append("trajectory")
            if str(traj).upper() in ["ESCALATING", "RAPID_ESCALATION", "CRITICAL"]:
                val = 1.5
                raw_score += val
                contributing_factors.append({"factor": "trajectory", "value": traj, "contribution": 1.5, "max_contribution": 1.5})
            else:
                contributing_factors.append({"factor": "trajectory", "value": traj, "contribution": 0.0, "max_contribution": 1.5})
        else:
            missing_list.append("trajectory")

        score = min(10.0, max(0.0, round(raw_score, 2)))
        severity_cls = self.map_score_to_class(score)
        total_factors = len(available_list) + len(missing_list)

        explanation = f"{self.policy_name} evaluated {len(available_list)}/{total_factors} available factors resulting in score {score}/10 ({severity_cls}). Note: Operational heuristic, not ML model."

        return SeverityAssessmentResult(
            status="success",
            hazard_type=hazard_type,
            severity_class=severity_cls,
            severity_score=score,
            assessment_method="POLICY",
            model_version=None,
            policy_version=self.policy_version,
            evidence_coverage={
                "available_factors_count": len(available_list),
                "total_factors_count": total_factors,
                "available_factors": available_list,
                "missing_factors": missing_list
            },
            contributing_factors=contributing_factors,
            explanation=explanation,
            confidence=None,
            probabilities=None
        )

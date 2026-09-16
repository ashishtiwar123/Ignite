import math

# Operational Priority Policy v1
# Provides the weighting and scoring logic to convert factors into a 0-100 score.

# 1. Severity Factor (Max 40 points)
# Severity score is expected to be 0.0 to 5.0. We multiply by 8.
def calculate_severity_score(severity: float) -> float:
    return min(40.0, severity * 8.0)

# 2. Trajectory Factor (Max 20 points)
# RAPIDLY_WORSENING = +20, WORSENING = +10, STABLE = 0, IMPROVING = -10
def calculate_trajectory_score(trajectory: str) -> float:
    if trajectory == "RAPIDLY_WORSENING":
        return 20.0
    elif trajectory == "WORSENING":
        return 10.0
    elif trajectory == "IMPROVING":
        return -10.0
    return 0.0 # STABLE, UNKNOWN, INSUFFICIENT_EVIDENCE

# 3. Population Factor (Max 20 points)
# Using a logarithmic scale so that 10 million doesn't eclipse a highly severe 10,000 incident.
# pop = 100 -> ~4 points
# pop = 10,000 -> ~8 points
# pop = 1,000,000 -> ~12 points
# Wait, let's use a simpler band to easily hit the 20 cap for extreme numbers, or just:
# score = log10(pop) * 3, capped at 20.
# log10(1,000,000) = 6 * 3 = 18.
# log10(100,000) = 5 * 3 = 15.
def calculate_population_score(population: int) -> float:
    if population <= 0:
        return 0.0
    return min(20.0, math.log10(population) * 3.2)

# 4. Urgency Factor (Max 20 points)
# Based on Needs Assessment outputs
def calculate_urgency_score(medical_urgency: str, rescue_urgency: str) -> float:
    score = 0.0
    if rescue_urgency == "CRITICAL":
        score += 15.0
    elif rescue_urgency == "HIGH":
        score += 10.0
    elif rescue_urgency == "MODERATE":
        score += 5.0
        
    if medical_urgency == "CRITICAL":
        score += 10.0
    elif medical_urgency == "HIGH":
        score += 5.0
        
    return min(20.0, score)

# Threshold mapping
def map_score_to_level(total_score: float) -> str:
    if total_score >= 70.0:
        return "CRITICAL"
    elif total_score >= 50.0:
        return "HIGH"
    elif total_score >= 30.0:
        return "MEDIUM"
    return "LOW"

import math

def calculate_disi_score(deaths=0, injured=0, displaced=0, damaged_structures=0, population_at_risk=100000, weights=None):
    """
    Computes the Derived Impact Severity Index (DISI) score in range [0.00, 5.00].
    
    Formula:
    DISI = min(5.0, w_D * S_mortality + w_I * S_morbidity + w_P * S_displacement + w_K * S_damage)
    """
    if weights is None:
        weights = {"w_D": 0.35, "w_I": 0.20, "w_P": 0.25, "w_K": 0.20}
        
    pop = max(1, population_at_risk)
    
    # Sub-indices (log10 normalized)
    s_mortality = min(5.0, math.log10(1 + (max(0, deaths) / pop) * 1e5))
    s_morbidity = min(5.0, math.log10(1 + (max(0, injured) / pop) * 1e5))
    s_displacement = min(5.0, math.log10(1 + (max(0, displaced) / pop) * 1e4))
    s_damage = min(5.0, math.log10(1 + max(0, damaged_structures)))
    
    raw_disi = (
        weights["w_D"] * s_mortality +
        weights["w_I"] * s_morbidity +
        weights["w_P"] * s_displacement +
        weights["w_K"] * s_damage
    )
    
    disi_score = round(min(5.0, max(0.0, raw_disi)), 2)
    
    # Map to ordinal class 0..5
    if disi_score < 0.5:
        severity_class = 0
    elif disi_score < 1.5:
        severity_class = 1
    elif disi_score < 2.5:
        severity_class = 2
    elif disi_score < 3.5:
        severity_class = 3
    elif disi_score < 4.5:
        severity_class = 4
    else:
        severity_class = 5
        
    return {
        "disi_score": disi_score,
        "severity_class": severity_class,
        "sub_indices": {
            "s_mortality": round(s_mortality, 2),
            "s_morbidity": round(s_morbidity, 2),
            "s_displacement": round(s_displacement, 2),
            "s_damage": round(s_damage, 2)
        }
    }

if __name__ == "__main__":
    # Benchmark tests
    print("Baseline:", calculate_disi_score(0, 0, 0, 0))
    print("Moderate Crisis:", calculate_disi_score(15, 50, 500, 20))
    print("Extreme Crisis:", calculate_disi_score(300, 1200, 25000, 500))

from data import PROCEDURES, HOME_CARE, STOP_SIGNALS

def get_recommendations(answers):
    zones = answers.get("selected_zones", "[]")
    import json
    zones = json.loads(zones)
    problems = answers.get("problems", [])
    
    rec_procedures = []
    for p in PROCEDURES:
        if any(z in p["zones"] for z in zones) and any(prob in p["problems"] for prob in problems):
            rec_procedures.append(p)
    
    rec_homecare = []
    for h in HOME_CARE:
        rec_homecare.append(h)
    
    warnings = []
    all_text = str(answers).lower()
    for signal, msg in STOP_SIGNALS.items():
        if signal in all_text:
            warnings.append(msg)
    
    return {
        "procedures": rec_procedures[:3],
        "homecare": rec_homecare[:3],
        "warnings": warnings
    }
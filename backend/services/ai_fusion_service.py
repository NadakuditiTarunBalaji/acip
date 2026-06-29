def analyze_vehicle_ai(can_data):

    rpm = can_data.get("rpm", 0)
    speed = can_data.get("speed", 0)
    temp = can_data.get("engine_temp", 0)

    score = 100
    issues = []

    if temp > 95:
        score -= 30
        issues.append("Overheating")

    if rpm > 4000:
        score -= 15
        issues.append("High RPM stress")

    if rpm > 3500 and speed < 20:
        score -= 20
        issues.append("Engine overload")

    status = "Good" if score > 80 else "Warning" if score > 50 else "Critical"

    return {
        "health_score": max(score, 0),
        "status": status,
        "issues": issues,
        "recommendation": "Check engine immediately" if status == "Critical"
        else "Monitor system"
    }
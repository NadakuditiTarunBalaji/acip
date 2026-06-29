"""
ACIP-X1 — Human Mistake Detector API
Engineering Mode — Feature E4
"""
from fastapi import APIRouter, HTTPException
from agents.requirement_agent.mistake_detector import MistakeDetector

router = APIRouter(
    prefix="/api/engineering/mistakes",
    tags=["Engineering Mode — Human Mistake Detector"]
)

detector = MistakeDetector()


@router.get("/all")
def detect_all_mistakes():
    """
    Detect ALL mistakes across ALL teams.
    Returns which team made which mistake with full evidence.
    """
    return detector.detect_all()


@router.get("/summary")
def get_mistake_summary():
    """Get high level mistake summary — which team has most mistakes"""
    result = detector.detect_all()
    return {
        "total_mistakes":        result["total_mistakes"],
        "critical":              result["critical"],
        "high":                  result["high"],
        "medium":                result["medium"],
        "verdict":               result["verdict"],
        "risk":                  result["risk"],
        "most_responsible_team": result["most_responsible_team"],
        "summary":               result["summary"],
        "teams": [
            {
                "team":           t["team"],
                "total_mistakes": t["total_mistakes"],
                "critical":       t["critical"],
                "high":           t["high"],
                "medium":         t["medium"]
            }
            for t in result["by_team"]
        ]
    }


@router.get("/team/{team_name}")
def get_team_mistakes(team_name: str):
    """Get all mistakes for a specific team"""
    result   = detector.detect_all()
    team_map = {t["team"].lower().replace(" ", "_"): t for t in result["by_team"]}
    key      = team_name.lower().replace("-", "_").replace(" ", "_")

    for k, v in team_map.items():
        if key in k or k in key:
            return v

    raise HTTPException(
        status_code=404,
        detail=f"Team '{team_name}' not found. Available: {list(team_map.keys())}"
    )


@router.get("/requirement/{req_id}")
def get_requirement_mistakes(req_id: str):
    """Get all mistakes for a specific requirement — which teams failed on it"""
    return detector.detect_for_requirement(req_id.upper())


@router.get("/critical-only")
def get_critical_mistakes():
    """Get only Critical severity mistakes — must fix immediately"""
    result   = detector.detect_all()
    critical = [m for m in result["all_mistakes"] if m["severity"] == "Critical"]
    return {
        "total_critical": len(critical),
        "verdict":        result["verdict"],
        "mistakes":       critical
    }


@router.get("/by-severity/{severity}")
def get_mistakes_by_severity(severity: str):
    """Get mistakes by severity: Critical, High, or Medium"""
    result   = detector.detect_all()
    filtered = [
        m for m in result["all_mistakes"]
        if m["severity"].lower() == severity.lower()
    ]
    return {
        "severity":      severity,
        "total":         len(filtered),
        "mistakes":      filtered
    }


@router.get("/teams/ranking")
def get_team_ranking():
    """Rank teams by number and severity of mistakes"""
    result = detector.detect_all()
    ranked = sorted(
        result["by_team"],
        key=lambda t: t["critical"] * 3 + t["high"] * 2 + t["medium"],
        reverse=True
    )
    return {
        "total_teams_checked":   result["summary"]["total_teams_checked"],
        "teams_with_mistakes":   result["summary"]["teams_with_mistakes"],
        "teams_clean":           result["summary"]["teams_clean"],
        "most_responsible_team": result["most_responsible_team"],
        "ranking": [
            {
                "rank":           i + 1,
                "team":           t["team"],
                "responsibility": t["responsibility"],
                "total_mistakes": t["total_mistakes"],
                "critical":       t["critical"],
                "high":           t["high"],
                "medium":         t["medium"],
                "risk_score":     t["critical"] * 3 + t["high"] * 2 + t["medium"]
            }
            for i, t in enumerate(ranked)
        ]
    }


@router.get("/demo")
def get_mistake_demo():
    """
    Demo mode — shows what mistakes look like when teams make errors.
    Uses simulated data to demonstrate the detector capability.
    """
    demo_mistakes = [
        {
            "team":         "Requirements Team",
            "team_color":   "#f85149",
            "mistake_type": "Missing Numeric Limit",
            "req_id":       "REQ_DEMO_01",
            "detail":       "Battery shall be safe — no numeric limit defined",
            "evidence":     "Text: 'Battery shall be safe' — no number found",
            "severity":     "High",
            "fix":          "Rewrite as: 'Battery voltage shall not exceed 420V'",
            "impact":       "Cannot quantitatively verify this requirement"
        },
        {
            "team":         "Calibration Team",
            "team_color":   "#3fb950",
            "mistake_type": "Calibration Value Mismatch",
            "req_id":       "REQ_DEMO_02",
            "detail":       "CAL_DEMO=380V but requirement says max 420V",
            "evidence":     "Calibration triggers DTC at 380V — 40V below requirement",
            "severity":     "Critical",
            "fix":          "Update CAL_DEMO from 380V to 420V",
            "impact":       "DTC triggers too early — false positives in testing"
        },
        {
            "team":         "Diagnostics Team",
            "team_color":   "#58a6ff",
            "mistake_type": "Missing DTC",
            "req_id":       "REQ_DEMO_03",
            "detail":       "Signal SIG_DEMO has no DTC trigger defined",
            "evidence":     "No entry in signal_dtc_edges.csv for SIG_DEMO",
            "severity":     "Critical",
            "fix":          "Define DTC for SIG_DEMO in dtc_nodes.csv",
            "impact":       "Requirement violation will not be detected"
        },
        {
            "team":         "Test Team",
            "team_color":   "#a371f7",
            "mistake_type": "Missing Test Case",
            "req_id":       "REQ_DEMO_04",
            "detail":       "REQ_DEMO_04 has no test case written",
            "evidence":     "No entry in requirement_testcase_edges.csv",
            "severity":     "Critical",
            "fix":          "Write test case for REQ_DEMO_04",
            "impact":       "Requirement will not be verified during testing"
        },
        {
            "team":         "System Engineering Team",
            "team_color":   "#d29922",
            "mistake_type": "Missing Signal Mapping",
            "req_id":       "REQ_DEMO_05",
            "detail":       "REQ_DEMO_05 has no signal mapped to it",
            "evidence":     "No entry in requirement_signal_edges.csv",
            "severity":     "Critical",
            "fix":          "Map REQ_DEMO_05 to correct signal",
            "impact":       "Cannot monitor this requirement in real-time"
        }
    ]

    by_team = {}
    for m in demo_mistakes:
        team = m["team"]
        if team not in by_team:
            by_team[team] = {"team": team, "count": 0, "mistakes": []}
        by_team[team]["count"] += 1
        by_team[team]["mistakes"].append(m)

    return {
        "mode":          "DEMO",
        "message":       "This shows what mistakes look like when teams make errors. Your actual project has ZERO mistakes!",
        "total_mistakes": len(demo_mistakes),
        "critical":       sum(1 for m in demo_mistakes if m["severity"] == "Critical"),
        "high":           sum(1 for m in demo_mistakes if m["severity"] == "High"),
        "verdict":        "🔴 5 Mistakes Found Across 5 Teams (DEMO DATA)",
        "by_team":        list(by_team.values()),
        "demo_mistakes":  demo_mistakes,
        "your_project":   "✅ Your actual project has ZERO mistakes — All 8 teams did their job perfectly!"
    }
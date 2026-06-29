"""
ACIP-X1 — Human Mistake Detector
Engineering Mode — Feature E4

In a real automotive company, when a test fails, these teams get blamed:
1. Requirements Team    — wrong/vague requirement written
2. System Engineering   — wrong signal or ECU selected
3. Software Team        — wrong calibration value set
4. Calibration Team     — calibration doesn't match requirement
5. Diagnostics Team     — DTC missing or wrong threshold
6. Test Team            — test case doesn't match requirement
7. Integration Team     — signal not connected to ECU
8. Safety Team          — safety requirement not covered

ACIP-X1 automatically detects WHICH TEAM made the mistake
and provides exact evidence — no guessing, no blame game.
"""
from pathlib import Path
from typing import List, Dict
import pandas as pd
import re

BASE_PATH  = Path(__file__).resolve().parent.parent.parent
NODES_PATH = BASE_PATH / "knowledge_graph" / "nodes"
EDGES_PATH = BASE_PATH / "knowledge_graph" / "edges"
DB_PATH    = BASE_PATH / "database" / "sqlite" / "acip.db"


def _load(filename, folder):
    path = folder / filename
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception as e:
            print(f"Warning: {filename}: {e}")
    return pd.DataFrame()


def _extract_limit(text):
    if not text:
        return None
    minus = re.search(r'minus\s+(\d+\.?\d*)', text, re.IGNORECASE)
    if minus:
        try:
            return -float(minus.group(1))
        except:
            pass
    patterns = [
        r'(\d+\.?\d*)\s*(?:V|A|C|RPM|km/h|kmh|%|mV|kW|Nm|ms)',
        r'exceed\s+(\d+\.?\d*)',
        r'below\s+(\d+\.?\d*)',
        r'above\s+(\d+\.?\d*)',
        r'minimum\s+(?:of\s+)?(\d+\.?\d*)',
        r'maximum\s+(?:of\s+)?(\d+\.?\d*)',
        r'within\s+(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:percent|degrees)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    return None


# ── Team Definitions ─────────────────────────────────────

TEAMS = {
    "Requirements Team": {
        "color": "#f85149",
        "responsibility": "Write clear, complete, testable requirements",
        "mistake_types": [
            "Vague Requirement",
            "Missing Numeric Limit",
            "Ambiguous Language",
            "Duplicate Requirement",
            "Conflicting Requirements"
        ]
    },
    "System Engineering Team": {
        "color": "#d29922",
        "responsibility": "Map requirements to signals and ECUs",
        "mistake_types": [
            "Wrong Signal Mapped",
            "Missing Signal Mapping",
            "Wrong ECU Assignment",
            "Signal Range Mismatch"
        ]
    },
    "Calibration Team": {
        "color": "#3fb950",
        "responsibility": "Set correct calibration limits matching requirements",
        "mistake_types": [
            "Calibration Value Mismatch",
            "Wrong Calibration Mapped",
            "Missing Calibration",
            "Calibration Out of Range"
        ]
    },
    "Diagnostics Team": {
        "color": "#58a6ff",
        "responsibility": "Define DTCs for all requirement violations",
        "mistake_types": [
            "Missing DTC",
            "Wrong DTC Threshold",
            "DTC Not Linked to Signal",
            "Missing Fault Code"
        ]
    },
    "Test Team": {
        "color": "#a371f7",
        "responsibility": "Write test cases that verify all requirements",
        "mistake_types": [
            "Missing Test Case",
            "Wrong Expected Result",
            "Test Case Not Linked",
            "Incomplete Test Coverage"
        ]
    },
    "Software Team": {
        "color": "#ff7b72",
        "responsibility": "Implement signal monitoring and fault handling in code",
        "mistake_types": [
            "Wrong Implementation",
            "Missing Implementation",
            "Logic Error"
        ]
    },
    "Integration Team": {
        "color": "#ffa657",
        "responsibility": "Connect signals to ECUs and verify end-to-end chain",
        "mistake_types": [
            "Broken Signal Chain",
            "Missing ECU Connection",
            "Integration Gap"
        ]
    },
    "Safety Team": {
        "color": "#ff6b6b",
        "responsibility": "Ensure all safety requirements have proper coverage",
        "mistake_types": [
            "Safety Requirement Not Covered",
            "Missing ASIL Rating",
            "Safety Gap"
        ]
    }
}


class MistakeDetector:
    """
    Automatically detects human mistakes and identifies
    which team is responsible for each mistake.
    """

    def __init__(self):
        self.req_nodes  = _load("requirement_nodes.csv",  NODES_PATH)
        self.sig_nodes  = _load("signal_nodes.csv",       NODES_PATH)
        self.cal_nodes  = _load("calibration_nodes.csv",  NODES_PATH)
        self.dtc_nodes  = _load("dtc_nodes.csv",          NODES_PATH)
        self.tc_nodes   = _load("testcase_nodes.csv",     NODES_PATH)
        self.ecu_nodes  = _load("ecu_nodes.csv",          NODES_PATH)

        self.req_sig_edges  = _load("requirement_signal_edges.csv",   EDGES_PATH)
        self.req_tc_edges   = _load("requirement_testcase_edges.csv", EDGES_PATH)
        self.sig_cal_edges  = _load("signal_calibration_edges.csv",   EDGES_PATH)
        self.sig_dtc_edges  = _load("signal_dtc_edges.csv",           EDGES_PATH)
        self.ecu_sig_edges  = _load("ecu_signal_edges.csv",           EDGES_PATH)

        self.db_calibrations = self._load_db_calibrations()
        print(f"MistakeDetector loaded — {len(self.req_nodes)} requirements")

    def _load_db_calibrations(self):
        try:
            import sqlite3
            conn = sqlite3.connect(str(DB_PATH))
            rows = conn.execute(
                "SELECT cal_id, parameter, value, unit FROM calibrations"
            ).fetchall()
            conn.close()
            return {r[0]: {"parameter": r[1], "value": r[2], "unit": r[3]} for r in rows}
        except:
            return {}

    def _targets(self, source, edge_df):
        if edge_df.empty:
            return []
        return edge_df[edge_df["source"] == source]["target"].tolist()

    def _sources(self, target, edge_df):
        if edge_df.empty:
            return []
        return edge_df[edge_df["target"] == target]["source"].tolist()

    def _node(self, node_id, df):
        if df.empty:
            return None
        row = df[df["node_id"] == node_id]
        return row.iloc[0] if not row.empty else None

    def _make_mistake(self, team, mistake_type, req_id, detail,
                      evidence, severity, fix, impact):
        return {
            "team":         team,
            "team_color":   TEAMS[team]["color"],
            "mistake_type": mistake_type,
            "req_id":       req_id,
            "detail":       detail,
            "evidence":     evidence,
            "severity":     severity,
            "fix":          fix,
            "impact":       impact
        }

    # ── DETECTION RULES ───────────────────────────────────

    def detect_requirements_team_mistakes(self) -> List[Dict]:
        mistakes = []
        for _, req in self.req_nodes.iterrows():
            req_id   = req["node_id"]
            req_text = req["name"]

            # Check 1: Vague requirement — no numeric limit
            limit = _extract_limit(req_text)
            if limit is None:
                mistakes.append(self._make_mistake(
                    team         = "Requirements Team",
                    mistake_type = "Missing Numeric Limit",
                    req_id       = req_id,
                    detail       = f"Requirement has no measurable limit: '{req_text}'",
                    evidence     = f"Text: '{req_text}' — no number found",
                    severity     = "High",
                    fix          = "Rewrite with explicit numeric value e.g. 'shall not exceed 420V'",
                    impact       = "Cannot quantitatively verify this requirement in testing"
                ))

            # Check 2: Too short — likely incomplete
            if len(req_text) < 20:
                mistakes.append(self._make_mistake(
                    team         = "Requirements Team",
                    mistake_type = "Vague Requirement",
                    req_id       = req_id,
                    detail       = f"Requirement text is too short: '{req_text}'",
                    evidence     = f"Only {len(req_text)} characters — likely incomplete",
                    severity     = "Medium",
                    fix          = "Expand requirement with full context and measurable criteria",
                    impact       = "Engineers may misinterpret this requirement"
                ))

            # Check 3: Missing 'shall' — not a proper requirement
            if "shall" not in req_text.lower() and "must" not in req_text.lower():
                mistakes.append(self._make_mistake(
                    team         = "Requirements Team",
                    mistake_type = "Ambiguous Language",
                    req_id       = req_id,
                    detail       = f"Requirement missing 'shall' or 'must': '{req_text}'",
                    evidence     = "No mandatory keyword found in requirement text",
                    severity     = "Medium",
                    fix          = "Use 'shall' or 'must' to make requirement mandatory",
                    impact       = "Requirement may be treated as optional by engineers"
                ))

        return mistakes

    def detect_system_engineering_mistakes(self) -> List[Dict]:
        mistakes = []
        for _, req in self.req_nodes.iterrows():
            req_id = req["node_id"]

            # Check: No signal mapped
            signals = self._targets(req_id, self.req_sig_edges)
            if not signals:
                mistakes.append(self._make_mistake(
                    team         = "System Engineering Team",
                    mistake_type = "Missing Signal Mapping",
                    req_id       = req_id,
                    detail       = f"{req_id} has no signal mapped",
                    evidence     = f"No entry in requirement_signal_edges.csv for {req_id}",
                    severity     = "Critical",
                    fix          = f"Map {req_id} to the correct signal in signal_nodes.csv",
                    impact       = "Requirement cannot be monitored in real-time"
                ))
            else:
                # Check: Signal not connected to any ECU
                for sig_id in signals:
                    ecus = self._sources(sig_id, self.ecu_sig_edges)
                    if not ecus:
                        mistakes.append(self._make_mistake(
                            team         = "Integration Team",
                            mistake_type = "Missing ECU Connection",
                            req_id       = req_id,
                            detail       = f"Signal {sig_id} is not connected to any ECU",
                            evidence     = f"No entry in ecu_signal_edges.csv for {sig_id}",
                            severity     = "High",
                            fix          = f"Connect {sig_id} to appropriate ECU in ecu_signal_edges.csv",
                            impact       = "Signal has no ECU controlling it — orphan signal"
                        ))

        return mistakes

    def detect_calibration_team_mistakes(self) -> List[Dict]:
        mistakes = []
        for _, req in self.req_nodes.iterrows():
            req_id    = req["node_id"]
            req_text  = req["name"]
            req_limit = _extract_limit(req_text)

            signals = self._targets(req_id, self.req_sig_edges)
            for sig_id in signals:
                cals = self._targets(sig_id, self.sig_cal_edges)

                # Check: No calibration
                if not cals:
                    mistakes.append(self._make_mistake(
                        team         = "Calibration Team",
                        mistake_type = "Missing Calibration",
                        req_id       = req_id,
                        detail       = f"Signal {sig_id} has no calibration limit defined",
                        evidence     = f"No entry in signal_calibration_edges.csv for {sig_id}",
                        severity     = "High",
                        fix          = f"Add calibration limit for {sig_id}",
                        impact       = "No threshold defined — system cannot detect violations"
                    ))

                # Check: Calibration value not in DB
                for cal_id in cals:
                    if cal_id not in self.db_calibrations:
                        mistakes.append(self._make_mistake(
                            team         = "Calibration Team",
                            mistake_type = "Calibration Not Seeded",
                            req_id       = req_id,
                            detail       = f"Calibration {cal_id} exists in KG but not in database",
                            evidence     = f"{cal_id} missing from calibrations table in SQLite",
                            severity     = "High",
                            fix          = f"Add {cal_id} to database via seed_all.py",
                            impact       = "Runtime calibration lookup will fail"
                        ))

        return mistakes

    def detect_diagnostics_team_mistakes(self) -> List[Dict]:
        mistakes = []
        for _, req in self.req_nodes.iterrows():
            req_id  = req["node_id"]
            signals = self._targets(req_id, self.req_sig_edges)

            for sig_id in signals:
                dtcs = self._targets(sig_id, self.sig_dtc_edges)
                if not dtcs:
                    mistakes.append(self._make_mistake(
                        team         = "Diagnostics Team",
                        mistake_type = "Missing DTC",
                        req_id       = req_id,
                        detail       = f"Signal {sig_id} has no DTC trigger defined",
                        evidence     = f"No entry in signal_dtc_edges.csv for {sig_id}",
                        severity     = "Critical",
                        fix          = f"Define DTC for {sig_id} in dtc_nodes.csv",
                        impact       = "Requirement violation will not be detected by diagnostics"
                    ))

        return mistakes

    def detect_test_team_mistakes(self) -> List[Dict]:
        mistakes = []
        for _, req in self.req_nodes.iterrows():
            req_id = req["node_id"]
            tcs    = self._targets(req_id, self.req_tc_edges)

            # Check: No test case
            if not tcs:
                mistakes.append(self._make_mistake(
                    team         = "Test Team",
                    mistake_type = "Missing Test Case",
                    req_id       = req_id,
                    detail       = f"{req_id} has no test case",
                    evidence     = f"No entry in requirement_testcase_edges.csv for {req_id}",
                    severity     = "Critical",
                    fix          = f"Write test case for {req_id} in testcase_nodes.csv",
                    impact       = "Requirement will not be verified during testing"
                ))
            else:
                # Check: Test case has no expected result
                for tc_id in tcs:
                    tc = self._node(tc_id, self.tc_nodes)
                    if tc is not None:
                        expected = str(tc.get("expected_result", ""))
                        if not expected or expected.lower() in ["nan", "none", ""]:
                            mistakes.append(self._make_mistake(
                                team         = "Test Team",
                                mistake_type = "Missing Expected Result",
                                req_id       = req_id,
                                detail       = f"Test case {tc_id} has no expected result",
                                evidence     = f"expected_result field is empty in testcase_nodes.csv",
                                severity     = "High",
                                fix          = f"Add expected result to {tc_id}",
                                impact       = "Tester cannot verify if test passed or failed"
                            ))

        return mistakes

    def detect_safety_team_mistakes(self) -> List[Dict]:
        mistakes = []
        safety_keywords = [
            "shall not exceed", "shall not drop", "shall not fall",
            "overvoltage", "undervoltage", "overtemperature",
            "overcurrent", "fault", "failure", "protection"
        ]

        for _, req in self.req_nodes.iterrows():
            req_id   = req["node_id"]
            req_text = req["name"].lower()
            category = req.get("category", "")

            is_safety = (
                category == "Safety" or
                any(kw in req_text for kw in safety_keywords)
            )

            if is_safety:
                signals = self._targets(req_id, self.req_sig_edges)
                for sig_id in signals:
                    dtcs = self._targets(sig_id, self.sig_dtc_edges)
                    cals = self._targets(sig_id, self.sig_cal_edges)

                    if not dtcs or not cals:
                        mistakes.append(self._make_mistake(
                            team         = "Safety Team",
                            mistake_type = "Safety Requirement Not Covered",
                            req_id       = req_id,
                            detail       = f"Safety requirement {req_id} missing DTC or calibration",
                            evidence     = f"DTCs: {dtcs}, Calibrations: {cals}",
                            severity     = "Critical",
                            fix          = "Add missing DTC and calibration for safety requirement",
                            impact       = "Safety violation may go undetected — risk to vehicle occupants"
                        ))

        return mistakes

    # ── FULL REPORT ───────────────────────────────────────

    def detect_all(self) -> Dict:
        """Run all team mistake detections and generate full report"""

        all_mistakes = []
        all_mistakes.extend(self.detect_requirements_team_mistakes())
        all_mistakes.extend(self.detect_system_engineering_mistakes())
        all_mistakes.extend(self.detect_calibration_team_mistakes())
        all_mistakes.extend(self.detect_diagnostics_team_mistakes())
        all_mistakes.extend(self.detect_test_team_mistakes())
        all_mistakes.extend(self.detect_safety_team_mistakes())

        # Group by team
        by_team = {}
        for mistake in all_mistakes:
            team = mistake["team"]
            if team not in by_team:
                by_team[team] = {
                    "team":           team,
                    "color":          mistake["team_color"],
                    "responsibility": TEAMS[team]["responsibility"],
                    "total_mistakes": 0,
                    "critical":       0,
                    "high":           0,
                    "medium":         0,
                    "mistakes":       []
                }
            by_team[team]["mistakes"].append(mistake)
            by_team[team]["total_mistakes"] += 1
            sev = mistake["severity"]
            if sev == "Critical":
                by_team[team]["critical"] += 1
            elif sev == "High":
                by_team[team]["high"] += 1
            elif sev == "Medium":
                by_team[team]["medium"] += 1

        # Count by severity
        critical = sum(1 for m in all_mistakes if m["severity"] == "Critical")
        high     = sum(1 for m in all_mistakes if m["severity"] == "High")
        medium   = sum(1 for m in all_mistakes if m["severity"] == "Medium")

        # Overall verdict
        if len(all_mistakes) == 0:
            verdict = "✅ No Mistakes Detected — All Teams Did Their Job!"
            risk    = "None"
        elif critical > 0:
            verdict = f"🔴 {critical} Critical Mistake(s) Found — Immediate Action Required"
            risk    = "Critical"
        elif high > 0:
            verdict = f"🟡 {high} High Severity Mistake(s) Found — Fix Before Testing"
            risk    = "High"
        else:
            verdict = f"🟢 {medium} Minor Mistake(s) Found — Low Risk"
            risk    = "Low"

        # Most responsible team
        most_responsible = None
        if by_team:
            most_responsible = max(
                by_team.values(),
                key=lambda t: t["critical"] * 3 + t["high"] * 2 + t["medium"]
            )["team"]

        return {
            "total_mistakes":    len(all_mistakes),
            "critical":          critical,
            "high":              high,
            "medium":            medium,
            "verdict":           verdict,
            "risk":              risk,
            "most_responsible_team": most_responsible,
            "by_team":           list(by_team.values()),
            "all_mistakes":      all_mistakes,
            "summary": {
                "teams_with_mistakes": len(by_team),
                "teams_clean":         len(TEAMS) - len(by_team),
                "total_teams_checked": len(TEAMS)
            }
        }

    def detect_for_requirement(self, req_id: str) -> Dict:
        """Detect which team made mistakes for a specific requirement"""
        all_results = self.detect_all()
        req_mistakes = [
            m for m in all_results["all_mistakes"]
            if m["req_id"] == req_id.upper()
        ]

        by_team = {}
        for m in req_mistakes:
            team = m["team"]
            if team not in by_team:
                by_team[team] = []
            by_team[team].append(m)

        return {
            "req_id":        req_id,
            "total_mistakes": len(req_mistakes),
            "mistakes":      req_mistakes,
            "by_team":       by_team,
            "verdict": (
                "✅ No mistakes found for this requirement"
                if not req_mistakes
                else f"⚠️ {len(req_mistakes)} mistake(s) found across {len(by_team)} team(s)"
            )
        }
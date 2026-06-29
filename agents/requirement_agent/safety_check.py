"""
ACIP-X1 — ISO 26262 Functional Safety Check
Engineering Mode — Feature E8

ISO 26262 is the automotive functional safety standard.
Every safety-relevant requirement must have:
1. ASIL Rating (A, B, C, D, or QM - Quality Managed)
2. Fault Detection mechanism (DTC)
3. Fault Handling/Reaction (Action)
4. Test Coverage (Test Case)
5. Independent verification

ASIL Levels (Automotive Safety Integrity Level):
- ASIL D — Highest risk (e.g. brake failure, steering failure)
- ASIL C — High risk (e.g. battery thermal runaway)
- ASIL B — Medium risk (e.g. speed limiting)
- ASIL A — Low risk (e.g. warning lights)
- QM     — Quality Managed, no safety impact (e.g. infotainment)
"""
from pathlib import Path
from typing import Dict, List
import pandas as pd

BASE_PATH  = Path(__file__).resolve().parent.parent.parent
NODES_PATH = BASE_PATH / "knowledge_graph" / "nodes"
EDGES_PATH = BASE_PATH / "knowledge_graph" / "edges"


def _load(filename, folder):
    path = folder / filename
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception as e:
            print(f"Warning: {filename}: {e}")
    return pd.DataFrame()


# ── ASIL Classification Rules ────────────────────────────
# Based on severity of consequence if requirement is violated

ASIL_RULES = {
    "ASIL D": {
        "keywords": [
            "overvoltage", "overcurrent", "thermal runaway",
            "brake", "steering", "airbag", "cell voltage",
            "battery overvoltage", "battery overcurrent"
        ],
        "description": "Highest integrity — failure could cause fatal injury",
        "color": "#f85149"
    },
    "ASIL C": {
        "keywords": [
            "overtemperature", "undertemperature", "cell imbalance",
            "battery temperature", "motor overspeed", "vehicle speed"
        ],
        "description": "High integrity — failure could cause severe injury",
        "color": "#ff7b72"
    },
    "ASIL B": {
        "keywords": [
            "motor torque", "regenerative braking", "inverter temperature",
            "soc critical", "soh critical", "undervoltage"
        ],
        "description": "Medium integrity — failure could cause moderate injury",
        "color": "#d29922"
    },
    "ASIL A": {
        "keywords": [
            "soc warning", "soh warning", "drive mode",
            "fault status", "warning", "alert"
        ],
        "description": "Low integrity — failure could cause minor injury",
        "color": "#58a6ff"
    },
    "QM": {
        "keywords": [
            "energy consumption", "range estimation", "charging status",
            "accelerator position", "power output", "monitored for"
        ],
        "description": "Quality Managed — no direct safety impact",
        "color": "#3fb950"
    }
}


def classify_asil(requirement_text: str, category: str = "") -> Dict:
    """Classify a requirement into an ASIL level"""
    text_lower = requirement_text.lower()

    for asil, rule in ASIL_RULES.items():
        for kw in rule["keywords"]:
            if kw in text_lower:
                return {
                    "asil":        asil,
                    "description": rule["description"],
                    "color":       rule["color"],
                    "matched_keyword": kw
                }

    # Default based on category
    if category == "Safety":
        return {
            "asil": "ASIL B",
            "description": ASIL_RULES["ASIL B"]["description"],
            "color": ASIL_RULES["ASIL B"]["color"],
            "matched_keyword": "category=Safety (default)"
        }

    return {
        "asil": "QM",
        "description": ASIL_RULES["QM"]["description"],
        "color": ASIL_RULES["QM"]["color"],
        "matched_keyword": "default — no safety keywords found"
    }


class SafetyChecker:
    """
    Performs ISO 26262 functional safety analysis on all requirements.
    """

    def __init__(self):
        self.req_nodes = _load("requirement_nodes.csv", NODES_PATH)
        self.sig_nodes = _load("signal_nodes.csv",      NODES_PATH)
        self.dtc_nodes = _load("dtc_nodes.csv",         NODES_PATH)
        self.action_nodes = _load("action_nodes.csv",   NODES_PATH)
        self.tc_nodes  = _load("testcase_nodes.csv",    NODES_PATH)

        self.req_sig_edges  = _load("requirement_signal_edges.csv",   EDGES_PATH)
        self.req_tc_edges   = _load("requirement_testcase_edges.csv", EDGES_PATH)
        self.sig_dtc_edges  = _load("signal_dtc_edges.csv",           EDGES_PATH)
        self.dtc_fault_edges = _load("dtc_fault_edges.csv",           EDGES_PATH)
        self.fault_rc_edges  = _load("fault_rootcause_edges.csv",     EDGES_PATH)
        self.rc_action_edges = _load("rootcause_action_edges.csv",    EDGES_PATH)

        print(f"SafetyChecker loaded — {len(self.req_nodes)} requirements")

    def _targets(self, source, edge_df):
        if edge_df.empty:
            return []
        return edge_df[edge_df["source"] == source]["target"].tolist()

    def check_requirement(self, req_id: str) -> Dict:
        """Full ISO 26262 safety check for one requirement"""
        req_row = self.req_nodes[self.req_nodes["node_id"] == req_id]
        if req_row.empty:
            return {"error": f"Requirement {req_id} not found"}

        req = req_row.iloc[0]
        req_text = req["name"]
        category = req.get("category", "")

        asil_info = classify_asil(req_text, category)
        asil = asil_info["asil"]

        result = {
            "req_id":      req_id,
            "requirement": req_text,
            "category":    category,
            "asil":        asil,
            "asil_description": asil_info["description"],
            "asil_color":  asil_info["color"],
            "matched_keyword": asil_info["matched_keyword"],
            "checks": {
                "has_fault_detection": False,
                "has_fault_handling":  False,
                "has_test_coverage":   False,
            },
            "compliance_items": [],
            "gaps": [],
            "compliance_score": 0,
            "status": "Unknown"
        }

        # Get signals
        sig_ids = self._targets(req_id, self.req_sig_edges)

        # Check 1: Fault Detection (DTC)
        has_dtc = False
        for sig_id in sig_ids:
            dtcs = self._targets(sig_id, self.sig_dtc_edges)
            if dtcs:
                has_dtc = True
                break
        result["checks"]["has_fault_detection"] = has_dtc

        if has_dtc:
            result["compliance_items"].append("✅ Fault Detection (DTC) — Present")
        else:
            result["gaps"].append({
                "requirement": "Fault Detection Mechanism",
                "detail":      "No DTC defined to detect violation of this requirement",
                "iso_clause":  "ISO 26262-4 Clause 6 — Functional Safety Requirements",
                "fix":         "Define DTC that triggers when this requirement is violated"
            })

        # Check 2: Fault Handling (Action via DTC -> Fault -> RootCause -> Action chain)
        has_action = False
        for sig_id in sig_ids:
            dtcs = self._targets(sig_id, self.sig_dtc_edges)
            for dtc_id in dtcs:
                faults = self._targets(dtc_id, self.dtc_fault_edges)
                for fault_id in faults:
                    rcs = self._targets(fault_id, self.fault_rc_edges)
                    for rc_id in rcs:
                        actions = self._targets(rc_id, self.rc_action_edges)
                        if actions:
                            has_action = True
        result["checks"]["has_fault_handling"] = has_action

        if has_action:
            result["compliance_items"].append("✅ Fault Handling (Root Cause + Action) — Present")
        else:
            result["gaps"].append({
                "requirement": "Fault Handling Mechanism",
                "detail":      "No corrective action defined for fault related to this requirement",
                "iso_clause":  "ISO 26262-4 Clause 7 — Safety Mechanisms",
                "fix":         "Define root cause and corrective action in knowledge graph"
            })

        # Check 3: Test Coverage
        tcs = self._targets(req_id, self.req_tc_edges)
        result["checks"]["has_test_coverage"] = len(tcs) > 0

        if tcs:
            result["compliance_items"].append(f"✅ Test Coverage — {len(tcs)} test case(s)")
        else:
            result["gaps"].append({
                "requirement": "Test Coverage",
                "detail":      "No test case verifies this requirement",
                "iso_clause":  "ISO 26262-6 Clause 9 — Software Unit Testing",
                "fix":         "Add test case for this requirement"
            })

        # ASIL-specific additional checks
        if asil in ["ASIL C", "ASIL D"]:
            # High ASIL requires redundancy check (simplified — signal must have calibration)
            from agents.requirement_agent.failure_predictor import _load as fp_load
            sig_cal_edges = _load("signal_calibration_edges.csv", EDGES_PATH)
            has_calibration = False
            for sig_id in sig_ids:
                cals = self._targets(sig_id, sig_cal_edges)
                if cals:
                    has_calibration = True
            if has_calibration:
                result["compliance_items"].append(f"✅ {asil} Calibration Limit Defined")
            else:
                result["gaps"].append({
                    "requirement": f"{asil} Calibration Requirement",
                    "detail":      f"{asil} requirement must have explicit calibration limit",
                    "iso_clause":  "ISO 26262-5 Clause 7 — Hardware Safety Requirements",
                    "fix":         "Define calibration limit for this signal"
                })

        # Compliance score
        total_checks = len(result["checks"])
        passed = sum(1 for v in result["checks"].values() if v)
        if asil in ["ASIL C", "ASIL D"]:
            total_checks += 1
            if has_dtc and "Calibration Limit Defined" in str(result["compliance_items"]):
                passed += 1

        result["compliance_score"] = round(passed / total_checks * 100, 1) if total_checks > 0 else 0

        if result["compliance_score"] == 100:
            result["status"] = "Compliant"
        elif result["compliance_score"] >= 66:
            result["status"] = "Partial"
        else:
            result["status"] = "Non-Compliant"

        return result

    def check_all(self) -> Dict:
        """Run ISO 26262 check on ALL requirements"""
        results = []
        asil_summary = {"ASIL D": 0, "ASIL C": 0, "ASIL B": 0, "ASIL A": 0, "QM": 0}
        status_summary = {"Compliant": 0, "Partial": 0, "Non-Compliant": 0}
        total_gaps = []

        for _, req in self.req_nodes.iterrows():
            result = self.check_requirement(req["node_id"])
            results.append(result)

            asil_summary[result["asil"]] += 1
            status_summary[result["status"]] += 1

            for gap in result["gaps"]:
                total_gaps.append({
                    "req_id": result["req_id"],
                    "asil":   result["asil"],
                    **gap
                })

        total = len(results)
        avg_compliance = round(
            sum(r["compliance_score"] for r in results) / total, 1
        ) if total > 0 else 0

        # Critical safety gaps — ASIL C/D with gaps
        critical_gaps = [
            g for g in total_gaps
            if g["asil"] in ["ASIL C", "ASIL D"]
        ]

        if status_summary["Non-Compliant"] == 0 and len(critical_gaps) == 0:
            overall_verdict = "✅ ISO 26262 COMPLIANT — All ASIL requirements covered"
        elif len(critical_gaps) > 0:
            overall_verdict = f"🔴 {len(critical_gaps)} CRITICAL SAFETY GAP(S) — ASIL C/D non-compliant"
        else:
            overall_verdict = f"🟡 {status_summary['Partial']} requirement(s) partially compliant"

        return {
            "total_requirements": total,
            "average_compliance": avg_compliance,
            "asil_distribution":  asil_summary,
            "status_summary":     status_summary,
            "overall_verdict":    overall_verdict,
            "critical_safety_gaps": critical_gaps,
            "total_gaps":         len(total_gaps),
            "all_gaps":           total_gaps,
            "results":            results
        }

    def get_asil_breakdown(self) -> Dict:
        """Get requirements grouped by ASIL level"""
        breakdown = {asil: [] for asil in ASIL_RULES.keys()}

        for _, req in self.req_nodes.iterrows():
            asil_info = classify_asil(req["name"], req.get("category", ""))
            breakdown[asil_info["asil"]].append({
                "req_id":      req["node_id"],
                "requirement": req["name"]
            })

        return {
            "breakdown": breakdown,
            "counts": {asil: len(reqs) for asil, reqs in breakdown.items()},
            "asil_info": {
                asil: {
                    "description": rule["description"],
                    "color":       rule["color"]
                }
                for asil, rule in ASIL_RULES.items()
            }
        }
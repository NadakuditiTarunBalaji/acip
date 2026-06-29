"""
ACIP-X1 — Gap & Conflict Detection Engine
Engineering Mode — Feature E5
"""
from pathlib import Path
from typing import List, Dict
import pandas as pd
import re

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


def _extract_limit(text):
    if not text:
        return None
    patterns = [
        r'(\d+\.?\d*)\s*(?:V|A|C|RPM|km/h|kmh|%|mV|kW|Nm)',
        r'exceed\s+(\d+\.?\d*)',
        r'below\s+(\d+\.?\d*)',
        r'above\s+(\d+\.?\d*)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
    return None


def _extract_direction(text):
    text_lower = text.lower()
    if any(w in text_lower for w in ["not exceed", "maximum", "max"]):
        return "max"
    if any(w in text_lower for w in ["not drop", "not fall", "minimum", "min"]):
        return "min"
    if "below" in text_lower:
        return "max_trigger"
    if "above" in text_lower:
        return "min_trigger"
    return "unknown"


def _is_warning(text):
    return any(w in text.lower() for w in ["warning", "warn"])


def _is_critical(text):
    return any(w in text.lower() for w in ["critical", "emergency", "fault"])


class GapConflictEngine:

    def __init__(self):
        self.req_nodes    = _load("requirement_nodes.csv",  NODES_PATH)
        self.signal_nodes = _load("signal_nodes.csv",       NODES_PATH)
        self.cal_nodes    = _load("calibration_nodes.csv",  NODES_PATH)
        self.dtc_nodes    = _load("dtc_nodes.csv",          NODES_PATH)
        self.tc_nodes     = _load("testcase_nodes.csv",     NODES_PATH)
        self.ecu_nodes    = _load("ecu_nodes.csv",          NODES_PATH)

        self.req_sig_edges = _load("requirement_signal_edges.csv",   EDGES_PATH)
        self.req_tc_edges  = _load("requirement_testcase_edges.csv", EDGES_PATH)
        self.sig_cal_edges = _load("signal_calibration_edges.csv",   EDGES_PATH)
        self.sig_dtc_edges = _load("signal_dtc_edges.csv",           EDGES_PATH)

        print(f"GapConflictEngine loaded — {len(self.req_nodes)} requirements")

    def _get_targets(self, source, edge_df):
        if edge_df.empty:
            return []
        return edge_df[edge_df["source"] == source]["target"].tolist()

    def detect_gaps(self):
        gaps = []
        for _, req in self.req_nodes.iterrows():
            req_id   = req["node_id"]
            req_name = req["name"]
            gap_item = {
                "req_id":      req_id,
                "requirement": req_name,
                "gaps":        [],
                "risk_level":  "Low",
                "impact":      []
            }

            # Check signal
            signals = self._get_targets(req_id, self.req_sig_edges)
            if not signals:
                gap_item["gaps"].append({
                    "type":   "Missing Signal",
                    "detail": "No signal mapped to this requirement",
                    "impact": "Cannot monitor this requirement in real-time",
                    "fix":    "Map a signal to this requirement"
                })
                gap_item["impact"].append("No real-time monitoring possible")
            else:
                for sig_id in signals:
                    cals = self._get_targets(sig_id, self.sig_cal_edges)
                    if not cals:
                        gap_item["gaps"].append({
                            "type":   "Missing Calibration",
                            "detail": f"Signal {sig_id} has no calibration limit",
                            "impact": "Cannot validate threshold",
                            "fix":    f"Add calibration for {sig_id}"
                        })
                    dtcs = self._get_targets(sig_id, self.sig_dtc_edges)
                    if not dtcs:
                        gap_item["gaps"].append({
                            "type":   "Missing DTC",
                            "detail": f"Signal {sig_id} has no DTC trigger",
                            "impact": "Violation not detected by diagnostics",
                            "fix":    f"Add DTC for {sig_id}"
                        })

            # Check test case
            tcs = self._get_targets(req_id, self.req_tc_edges)
            if not tcs:
                gap_item["gaps"].append({
                    "type":   "Missing Test Case",
                    "detail": "No test case for this requirement",
                    "impact": "Requirement cannot be verified",
                    "fix":    "Add test case"
                })
                gap_item["impact"].append("Requirement unverifiable")

            if not gap_item["gaps"]:
                continue

            n = len(gap_item["gaps"])
            gap_item["risk_level"] = "Critical" if n >= 3 else "High" if n == 2 else "Medium"
            gaps.append(gap_item)

        return {
            "total_requirements": len(self.req_nodes),
            "total_gaps":         len(gaps),
            "gap_free":           len(self.req_nodes) - len(gaps),
            "gaps":               gaps
        }

    def detect_conflicts(self):
        conflicts = []
        if self.req_sig_edges.empty or self.req_nodes.empty:
            return {"total_conflicts": 0, "conflicts": []}

        sig_to_reqs = {}
        for _, edge in self.req_sig_edges.iterrows():
            sig_id = edge["target"]
            req_id = edge["source"]
            if sig_id not in sig_to_reqs:
                sig_to_reqs[sig_id] = []
            sig_to_reqs[sig_id].append(req_id)

        for sig_id, req_ids in sig_to_reqs.items():
            if len(req_ids) < 2:
                continue

            sig_row  = self.signal_nodes[self.signal_nodes["node_id"] == sig_id]
            sig_name = sig_row.iloc[0]["name"] if not sig_row.empty else sig_id

            req_data = []
            for req_id in req_ids:
                req_row = self.req_nodes[self.req_nodes["node_id"] == req_id]
                if not req_row.empty:
                    req_text = req_row.iloc[0]["name"]
                    req_data.append({
                        "req_id":    req_id,
                        "text":      req_text,
                        "limit":     _extract_limit(req_text),
                        "direction": _extract_direction(req_text),
                        "is_warning":  _is_warning(req_text),
                        "is_critical": _is_critical(req_text)
                    })

            for i in range(len(req_data)):
                for j in range(i + 1, len(req_data)):
                    r1 = req_data[i]
                    r2 = req_data[j]

                    # ── SKIP intentional multi-level alerts ──────────
                    # Warning + Critical on same signal = by design
                    if (r1["is_warning"] and r2["is_critical"]) or \
                       (r1["is_critical"] and r2["is_warning"]):
                        continue

                    conflict = None

                    if r1["limit"] and r2["limit"]:
                        if r1["direction"] == "max" and r2["direction"] == "min":
                            if r1["limit"] < r2["limit"]:
                                conflict = {
                                    "type":     "Limit Contradiction",
                                    "detail":   f"{r1['req_id']} max={r1['limit']} < {r2['req_id']} min={r2['limit']} — impossible range",
                                    "severity": "Critical"
                                }
                        elif r1["direction"] == "min" and r2["direction"] == "max":
                            if r2["limit"] < r1["limit"]:
                                conflict = {
                                    "type":     "Limit Contradiction",
                                    "detail":   f"{r2['req_id']} max={r2['limit']} < {r1['req_id']} min={r1['limit']} — impossible range",
                                    "severity": "Critical"
                                }
                        elif r1["direction"] == r2["direction"] and r1["limit"] != r2["limit"]:
                            conflict = {
                                "type":     "Same Direction Different Value",
                                "detail":   f"{r1['req_id']}={r1['limit']} vs {r2['req_id']}={r2['limit']} on {sig_name}",
                                "severity": "High"
                            }

                    if conflict:
                        conflicts.append({
                            "signal_id":      sig_id,
                            "signal_name":    sig_name,
                            "req_1":          r1,
                            "req_2":          r2,
                            "conflict":       conflict,
                            "recommendation": f"Review {r1['req_id']} and {r2['req_id']} — clarify different operating conditions"
                        })

        return {
            "total_conflicts": len(conflicts),
            "conflicts":       conflicts
        }

    def detect_orphans(self):
        orphan_signals = []
        orphan_dtcs    = []
        orphan_cals    = []

        if not self.signal_nodes.empty and not self.req_sig_edges.empty:
            linked = set(self.req_sig_edges["target"].tolist())
            for _, sig in self.signal_nodes.iterrows():
                if sig["node_id"] not in linked:
                    orphan_signals.append({
                        "id":     sig["node_id"],
                        "name":   sig["name"],
                        "domain": sig.get("domain", "Unknown"),
                        "issue":  "Signal not mapped to any requirement"
                    })

        if not self.dtc_nodes.empty and not self.sig_dtc_edges.empty:
            linked = set(self.sig_dtc_edges["target"].tolist())
            for _, dtc in self.dtc_nodes.iterrows():
                if dtc["node_id"] not in linked:
                    orphan_dtcs.append({
                        "id":    dtc["node_id"],
                        "name":  dtc["name"],
                        "issue": "DTC not triggered by any signal"
                    })

        if not self.cal_nodes.empty and not self.sig_cal_edges.empty:
            linked = set(self.sig_cal_edges["target"].tolist())
            for _, cal in self.cal_nodes.iterrows():
                if cal["node_id"] not in linked:
                    orphan_cals.append({
                        "id":    cal["node_id"],
                        "name":  cal["name"],
                        "issue": "Calibration not governing any signal"
                    })

        return {
            "total_orphans":       len(orphan_signals) + len(orphan_dtcs) + len(orphan_cals),
            "orphan_signals":      orphan_signals,
            "orphan_dtcs":         orphan_dtcs,
            "orphan_calibrations": orphan_cals
        }

    def full_report(self):
        gaps      = self.detect_gaps()
        conflicts = self.detect_conflicts()
        orphans   = self.detect_orphans()

        total_issues = (
            gaps["total_gaps"] +
            conflicts["total_conflicts"] +
            orphans["total_orphans"]
        )

        if total_issues == 0:
            overall_status = "Clean"
        elif total_issues <= 3:
            overall_status = "Minor Issues"
        elif total_issues <= 10:
            overall_status = "Needs Attention"
        else:
            overall_status = "Critical — Review Required"

        return {
            "overall_status": overall_status,
            "total_issues":   total_issues,
            "gaps":           gaps,
            "conflicts":      conflicts,
            "orphans":        orphans,
            "summary": {
                "total_requirements":      gaps["total_requirements"],
                "gap_free":                gaps["gap_free"],
                "requirements_with_gaps":  gaps["total_gaps"],
                "conflicts_found":         conflicts["total_conflicts"],
                "orphan_entities":         orphans["total_orphans"],
            }
        }
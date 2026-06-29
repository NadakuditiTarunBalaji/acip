"""
ACIP-X1 — Auto Traceability Matrix Engine
Engineering Mode — Feature E2

Automatically builds complete traceability chain:
Requirement → Signal → ECU → Calibration → DTC → Fault → RootCause → Action → TestCase

What normally takes 2-3 days manually → done in seconds.
"""
from pathlib import Path
import pandas as pd
from typing import List, Dict, Optional

BASE_PATH  = Path(__file__).resolve().parent.parent.parent
NODES_PATH = BASE_PATH / "knowledge_graph" / "nodes"
EDGES_PATH = BASE_PATH / "knowledge_graph" / "edges"


def _load(filename: str, folder: Path) -> pd.DataFrame:
    path = folder / filename
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception as e:
            print(f"Warning: {filename}: {e}")
    return pd.DataFrame()


class TraceabilityEngine:
    """
    Builds full traceability matrix from KG nodes and edges.
    Every requirement traced through entire engineering chain.
    """

    def __init__(self):
        # Nodes
        self.requirement_nodes  = _load("requirement_nodes.csv",  NODES_PATH)
        self.signal_nodes       = _load("signal_nodes.csv",       NODES_PATH)
        self.ecu_nodes          = _load("ecu_nodes.csv",          NODES_PATH)
        self.calibration_nodes  = _load("calibration_nodes.csv",  NODES_PATH)
        self.dtc_nodes          = _load("dtc_nodes.csv",          NODES_PATH)
        self.fault_nodes        = _load("fault_nodes.csv",        NODES_PATH)
        self.rootcause_nodes    = _load("rootcause_nodes.csv",    NODES_PATH)
        self.action_nodes       = _load("action_nodes.csv",       NODES_PATH)
        self.testcase_nodes     = _load("testcase_nodes.csv",     NODES_PATH)

        # Edges
        self.req_signal_edges   = _load("requirement_signal_edges.csv",   EDGES_PATH)
        self.req_tc_edges       = _load("requirement_testcase_edges.csv", EDGES_PATH)
        self.ecu_signal_edges   = _load("ecu_signal_edges.csv",           EDGES_PATH)
        self.sig_dtc_edges      = _load("signal_dtc_edges.csv",           EDGES_PATH)
        self.sig_cal_edges      = _load("signal_calibration_edges.csv",   EDGES_PATH)
        self.dtc_fault_edges    = _load("dtc_fault_edges.csv",            EDGES_PATH)
        self.fault_rc_edges     = _load("fault_rootcause_edges.csv",      EDGES_PATH)
        self.rc_action_edges    = _load("rootcause_action_edges.csv",     EDGES_PATH)

    def _get_node_name(self, node_id: str, df: pd.DataFrame) -> Optional[str]:
        """Get node name from dataframe by node_id"""
        if df.empty:
            return None
        row = df[df["node_id"] == node_id]
        if not row.empty:
            return row.iloc[0]["name"]
        return None

    def _get_targets(self, source: str, edge_df: pd.DataFrame) -> List[str]:
        """Get all target node IDs from edge dataframe for a given source"""
        if edge_df.empty:
            return []
        return edge_df[edge_df["source"] == source]["target"].tolist()

    def _get_sources(self, target: str, edge_df: pd.DataFrame) -> List[str]:
        """Get all source node IDs from edge dataframe for a given target"""
        if edge_df.empty:
            return []
        return edge_df[edge_df["target"] == target]["source"].tolist()

    def trace_requirement(self, req_id: str) -> Dict:
        """
        Build complete traceability chain for one requirement:
        REQ → Signal → ECU → Calibration → DTC → Fault → RootCause → Action → TestCase
        """
        chain = {
            "req_id":       req_id,
            "requirement":  self._get_node_name(req_id, self.requirement_nodes),
            "signals":      [],
            "ecus":         [],
            "calibrations": [],
            "dtcs":         [],
            "faults":       [],
            "root_causes":  [],
            "actions":      [],
            "test_cases":   [],
            "coverage": {
                "has_signal":       False,
                "has_ecu":          False,
                "has_calibration":  False,
                "has_dtc":          False,
                "has_fault":        False,
                "has_root_cause":   False,
                "has_action":       False,
                "has_test_case":    False,
            },
            "traceability_score": 0,
            "status": "Unknown"
        }

        if not chain["requirement"]:
            chain["status"] = "Not Found"
            return chain

        # ── Step 1: REQ → Signals ──────────────────────
        signal_ids = self._get_targets(req_id, self.req_signal_edges)
        for sig_id in signal_ids:
            name = self._get_node_name(sig_id, self.signal_nodes)
            if name:
                chain["signals"].append({"id": sig_id, "name": name})

                # ── Step 2: Signal → ECU (reverse lookup) ──
                ecu_ids = self._get_sources(sig_id, self.ecu_signal_edges)
                for ecu_id in ecu_ids:
                    ecu_name = self._get_node_name(ecu_id, self.ecu_nodes)
                    if ecu_name and not any(e["id"] == ecu_id for e in chain["ecus"]):
                        chain["ecus"].append({"id": ecu_id, "name": ecu_name})

                # ── Step 3: Signal → Calibration ───────────
                cal_ids = self._get_targets(sig_id, self.sig_cal_edges)
                for cal_id in cal_ids:
                    cal_name = self._get_node_name(cal_id, self.calibration_nodes)
                    if cal_name and not any(c["id"] == cal_id for c in chain["calibrations"]):
                        chain["calibrations"].append({"id": cal_id, "name": cal_name})

                # ── Step 4: Signal → DTC ───────────────────
                dtc_ids = self._get_targets(sig_id, self.sig_dtc_edges)
                for dtc_id in dtc_ids:
                    dtc_name = self._get_node_name(dtc_id, self.dtc_nodes)
                    if dtc_name and not any(d["id"] == dtc_id for d in chain["dtcs"]):
                        chain["dtcs"].append({"id": dtc_id, "name": dtc_name})

                        # ── Step 5: DTC → Fault ────────────
                        fault_ids = self._get_targets(dtc_id, self.dtc_fault_edges)
                        for fault_id in fault_ids:
                            fault_name = self._get_node_name(fault_id, self.fault_nodes)
                            if fault_name and not any(f["id"] == fault_id for f in chain["faults"]):
                                chain["faults"].append({"id": fault_id, "name": fault_name})

                                # ── Step 6: Fault → RootCause ──
                                rc_ids = self._get_targets(fault_id, self.fault_rc_edges)
                                for rc_id in rc_ids:
                                    rc_name = self._get_node_name(rc_id, self.rootcause_nodes)
                                    if rc_name and not any(r["id"] == rc_id for r in chain["root_causes"]):
                                        chain["root_causes"].append({"id": rc_id, "name": rc_name})

                                        # ── Step 7: RootCause → Action
                                        act_ids = self._get_targets(rc_id, self.rc_action_edges)
                                        for act_id in act_ids:
                                            act_name = self._get_node_name(act_id, self.action_nodes)
                                            if act_name and not any(a["id"] == act_id for a in chain["actions"]):
                                                chain["actions"].append({"id": act_id, "name": act_name})

        # ── Step 8: REQ → TestCase ─────────────────────
        tc_ids = self._get_targets(req_id, self.req_tc_edges)
        for tc_id in tc_ids:
            tc_name = self._get_node_name(tc_id, self.testcase_nodes)
            if tc_name:
                chain["test_cases"].append({"id": tc_id, "name": tc_name})

        # ── Coverage Analysis ──────────────────────────
        chain["coverage"] = {
            "has_signal":      len(chain["signals"])      > 0,
            "has_ecu":         len(chain["ecus"])         > 0,
            "has_calibration": len(chain["calibrations"]) > 0,
            "has_dtc":         len(chain["dtcs"])         > 0,
            "has_fault":       len(chain["faults"])       > 0,
            "has_root_cause":  len(chain["root_causes"])  > 0,
            "has_action":      len(chain["actions"])      > 0,
            "has_test_case":   len(chain["test_cases"])   > 0,
        }

        # ── Traceability Score (0-100) ─────────────────
        score = sum(chain["coverage"].values()) / len(chain["coverage"]) * 100
        chain["traceability_score"] = round(score, 1)

        # ── Status ─────────────────────────────────────
        if score == 100:
            chain["status"] = "Complete"
        elif score >= 75:
            chain["status"] = "Good"
        elif score >= 50:
            chain["status"] = "Partial"
        elif score >= 25:
            chain["status"] = "Poor"
        else:
            chain["status"] = "Missing"

        return chain

    def build_full_matrix(self) -> Dict:
        """
        Build complete traceability matrix for ALL requirements.
        Returns full matrix + summary statistics.
        """
        if self.requirement_nodes.empty:
            return {
                "total": 0,
                "matrix": [],
                "summary": {},
                "gaps": []
            }

        matrix = []
        gaps   = []
        status_counts = {
            "Complete": 0,
            "Good":     0,
            "Partial":  0,
            "Poor":     0,
            "Missing":  0
        }

        for _, row in self.requirement_nodes.iterrows():
            req_id = row["node_id"]
            chain  = self.trace_requirement(req_id)
            matrix.append(chain)

            # Count statuses
            status = chain["status"]
            if status in status_counts:
                status_counts[status] += 1

            # Collect gaps
            missing = [
                k.replace("has_", "").replace("_", " ").title()
                for k, v in chain["coverage"].items()
                if not v
            ]
            if missing:
                gaps.append({
                    "req_id":      req_id,
                    "requirement": chain["requirement"],
                    "missing":     missing,
                    "score":       chain["traceability_score"],
                    "status":      chain["status"]
                })

        # Overall score
        avg_score = (
            sum(c["traceability_score"] for c in matrix) / len(matrix)
            if matrix else 0
        )

        return {
            "total":         len(matrix),
            "matrix":        matrix,
            "average_score": round(avg_score, 1),
            "status_counts": status_counts,
            "total_gaps":    len(gaps),
            "gaps":          gaps,
            "summary": {
                "complete":    status_counts["Complete"],
                "good":        status_counts["Good"],
                "partial":     status_counts["Partial"],
                "poor":        status_counts["Poor"],
                "missing":     status_counts["Missing"],
                "coverage_pct": round(
                    (status_counts["Complete"] + status_counts["Good"]) /
                    max(len(matrix), 1) * 100, 1
                )
            }
        }

    def get_flat_matrix(self) -> List[Dict]:
        """
        Returns a flat table format for display in dashboard/export.
        Each row = one requirement with all chain info.
        """
        full = self.build_full_matrix()
        rows = []

        for chain in full["matrix"]:
            rows.append({
                "REQ ID":        chain["req_id"],
                "Requirement":   chain["requirement"] or "N/A",
                "Signals":       ", ".join(s["id"] for s in chain["signals"])      or "❌ Missing",
                "ECUs":          ", ".join(e["id"] for e in chain["ecus"])         or "❌ Missing",
                "Calibrations":  ", ".join(c["id"] for c in chain["calibrations"]) or "❌ Missing",
                "DTCs":          ", ".join(d["id"] for d in chain["dtcs"])         or "❌ Missing",
                "Faults":        ", ".join(f["id"] for f in chain["faults"])       or "❌ Missing",
                "Root Causes":   ", ".join(r["name"] for r in chain["root_causes"]) or "❌ Missing",
                "Actions":       ", ".join(a["name"] for a in chain["actions"])    or "❌ Missing",
                "Test Cases":    ", ".join(t["id"] for t in chain["test_cases"])   or "❌ Missing",
                "Score":         f"{chain['traceability_score']}%",
                "Status":        chain["status"],
            })

        return rows
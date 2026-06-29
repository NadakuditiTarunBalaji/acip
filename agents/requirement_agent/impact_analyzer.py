"""
ACIP-X1 — Impact Analysis Engine
Engineering Mode — Feature E7

When an engineer changes ONE thing (calibration, signal, requirement),
this engine instantly shows EVERYTHING affected:
- Which signals use this calibration
- Which DTCs depend on this signal
- Which faults are triggered by this DTC
- Which requirements map to this signal
- Which test cases verify those requirements
- Which ECUs control this signal

"Change one calibration value → instantly know the blast radius"
"""
from pathlib import Path
from typing import Dict, List
import pandas as pd

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


class ImpactAnalyzer:
    """
    Analyzes the ripple effect of changes across the entire
    engineering knowledge graph.
    """

    def __init__(self):
        # Nodes
        self.req_nodes  = _load("requirement_nodes.csv",  NODES_PATH)
        self.sig_nodes  = _load("signal_nodes.csv",       NODES_PATH)
        self.cal_nodes  = _load("calibration_nodes.csv",  NODES_PATH)
        self.dtc_nodes  = _load("dtc_nodes.csv",          NODES_PATH)
        self.fault_nodes = _load("fault_nodes.csv",       NODES_PATH)
        self.rc_nodes   = _load("rootcause_nodes.csv",    NODES_PATH)
        self.action_nodes = _load("action_nodes.csv",     NODES_PATH)
        self.tc_nodes   = _load("testcase_nodes.csv",     NODES_PATH)
        self.ecu_nodes  = _load("ecu_nodes.csv",          NODES_PATH)

        # Edges
        self.req_sig_edges  = _load("requirement_signal_edges.csv",   EDGES_PATH)
        self.req_tc_edges   = _load("requirement_testcase_edges.csv", EDGES_PATH)
        self.sig_cal_edges  = _load("signal_calibration_edges.csv",   EDGES_PATH)
        self.sig_dtc_edges  = _load("signal_dtc_edges.csv",           EDGES_PATH)
        self.dtc_fault_edges = _load("dtc_fault_edges.csv",           EDGES_PATH)
        self.fault_rc_edges  = _load("fault_rootcause_edges.csv",     EDGES_PATH)
        self.rc_action_edges = _load("rootcause_action_edges.csv",    EDGES_PATH)
        self.ecu_sig_edges   = _load("ecu_signal_edges.csv",          EDGES_PATH)

        self.db_calibrations = self._load_db_calibrations()
        print(f"ImpactAnalyzer loaded — {len(self.cal_nodes)} calibrations, "
              f"{len(self.sig_nodes)} signals, {len(self.req_nodes)} requirements")

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

    # ── IMPACT FROM CALIBRATION CHANGE ────────────────────

    def analyze_calibration_impact(self, cal_id: str, new_value: float = None) -> Dict:
        """
        Given a calibration ID (and optional new value),
        show everything affected if this calibration changes.
        """
        cal_node = self._node(cal_id, self.cal_nodes)
        if cal_node is None:
            return {"error": f"Calibration {cal_id} not found"}

        cal_name    = cal_node["name"]
        current_val = self.db_calibrations.get(cal_id, {}).get("value")
        unit        = self.db_calibrations.get(cal_id, {}).get("unit", "")

        impact = {
            "cal_id":        cal_id,
            "calibration":   cal_name,
            "current_value": current_val,
            "proposed_value": new_value,
            "unit":          unit,
            "affected_signals":     [],
            "affected_requirements": [],
            "affected_dtcs":        [],
            "affected_faults":      [],
            "affected_test_cases":  [],
            "affected_ecus":        [],
            "total_impact_count":   0,
            "risk_level":           "Low",
            "warnings":             []
        }

        # Find signals governed by this calibration (reverse lookup)
        sig_ids = self._sources(cal_id, self.sig_cal_edges)

        for sig_id in sig_ids:
            sig_node = self._node(sig_id, self.sig_nodes)
            if sig_node is None:
                continue

            impact["affected_signals"].append({
                "id":   sig_id,
                "name": sig_node["name"],
                "min":  sig_node.get("min_value"),
                "max":  sig_node.get("max_value")
            })

            # Check if new value is outside signal range
            if new_value is not None:
                sig_min = sig_node.get("min_value")
                sig_max = sig_node.get("max_value")
                if pd.notna(sig_min) and pd.notna(sig_max):
                    if new_value > float(sig_max) or new_value < float(sig_min):
                        impact["warnings"].append(
                            f"⚠️ New value {new_value}{unit} is OUTSIDE signal {sig_id} "
                            f"range [{sig_min}, {sig_max}] — signal can never reach this!"
                        )
                        impact["risk_level"] = "Critical"

            # Find requirements mapped to this signal
            req_ids = self._sources(sig_id, self.req_sig_edges)
            for req_id in req_ids:
                req_node = self._node(req_id, self.req_nodes)
                if req_node is not None:
                    impact["affected_requirements"].append({
                        "id":   req_id,
                        "name": req_node["name"]
                    })

                    # Find test cases for this requirement
                    tc_ids = self._targets(req_id, self.req_tc_edges)
                    for tc_id in tc_ids:
                        tc_node = self._node(tc_id, self.tc_nodes)
                        if tc_node is not None:
                            impact["affected_test_cases"].append({
                                "id":   tc_id,
                                "name": tc_node["name"]
                            })

            # Find DTCs triggered by this signal
            dtc_ids = self._targets(sig_id, self.sig_dtc_edges)
            for dtc_id in dtc_ids:
                dtc_node = self._node(dtc_id, self.dtc_nodes)
                if dtc_node is not None:
                    impact["affected_dtcs"].append({
                        "id":   dtc_id,
                        "name": dtc_node["name"]
                    })

                    # Find faults from these DTCs
                    fault_ids = self._targets(dtc_id, self.dtc_fault_edges)
                    for fault_id in fault_ids:
                        fault_node = self._node(fault_id, self.fault_nodes)
                        if fault_node is not None:
                            impact["affected_faults"].append({
                                "id":   fault_id,
                                "name": fault_node["name"]
                            })

            # Find ECUs controlling this signal
            ecu_ids = self._sources(sig_id, self.ecu_sig_edges)
            for ecu_id in ecu_ids:
                ecu_node = self._node(ecu_id, self.ecu_nodes)
                if ecu_node is not None:
                    impact["affected_ecus"].append({
                        "id":   ecu_id,
                        "name": ecu_node["name"]
                    })

        # Deduplicate
        for key in ["affected_signals", "affected_requirements", "affected_dtcs",
                    "affected_faults", "affected_test_cases", "affected_ecus"]:
            seen = set()
            unique = []
            for item in impact[key]:
                if item["id"] not in seen:
                    seen.add(item["id"])
                    unique.append(item)
            impact[key] = unique

        # Total impact count
        impact["total_impact_count"] = sum(
            len(impact[key]) for key in [
                "affected_signals", "affected_requirements", "affected_dtcs",
                "affected_faults", "affected_test_cases", "affected_ecus"
            ]
        )

        # Risk assessment
        if impact["risk_level"] != "Critical":
            if impact["total_impact_count"] > 10:
                impact["risk_level"] = "High"
            elif impact["total_impact_count"] > 5:
                impact["risk_level"] = "Medium"
            else:
                impact["risk_level"] = "Low"

        # Value change analysis
        if new_value is not None and current_val is not None:
            change_pct = abs(new_value - current_val) / abs(current_val) * 100 if current_val != 0 else 0
            impact["change_summary"] = {
                "from":       current_val,
                "to":         new_value,
                "change":     round(new_value - current_val, 4),
                "change_pct": round(change_pct, 2)
            }
            if change_pct > 20:
                impact["warnings"].append(
                    f"⚠️ This is a {round(change_pct,1)}% change — significant impact expected"
                )

        return impact

    # ── IMPACT FROM SIGNAL CHANGE ─────────────────────────

    def analyze_signal_impact(self, sig_id: str) -> Dict:
        """Show everything connected to a signal"""
        sig_node = self._node(sig_id, self.sig_nodes)
        if sig_node is None:
            return {"error": f"Signal {sig_id} not found"}

        impact = {
            "sig_id":  sig_id,
            "signal":  sig_node["name"],
            "domain":  sig_node.get("domain", "Unknown"),
            "range":   f"{sig_node.get('min_value')} to {sig_node.get('max_value')}",
            "affected_requirements": [],
            "affected_calibrations": [],
            "affected_dtcs":        [],
            "affected_ecus":        [],
            "total_impact_count":   0
        }

        # Requirements
        for req_id in self._sources(sig_id, self.req_sig_edges):
            req = self._node(req_id, self.req_nodes)
            if req is not None:
                impact["affected_requirements"].append({"id": req_id, "name": req["name"]})

        # Calibrations
        for cal_id in self._targets(sig_id, self.sig_cal_edges):
            cal = self._node(cal_id, self.cal_nodes)
            if cal is not None:
                db_val = self.db_calibrations.get(cal_id, {})
                impact["affected_calibrations"].append({
                    "id": cal_id, "name": cal["name"],
                    "value": db_val.get("value"), "unit": db_val.get("unit")
                })

        # DTCs
        for dtc_id in self._targets(sig_id, self.sig_dtc_edges):
            dtc = self._node(dtc_id, self.dtc_nodes)
            if dtc is not None:
                impact["affected_dtcs"].append({"id": dtc_id, "name": dtc["name"]})

        # ECUs
        for ecu_id in self._sources(sig_id, self.ecu_sig_edges):
            ecu = self._node(ecu_id, self.ecu_nodes)
            if ecu is not None:
                impact["affected_ecus"].append({"id": ecu_id, "name": ecu["name"]})

        impact["total_impact_count"] = sum(
            len(impact[k]) for k in [
                "affected_requirements", "affected_calibrations",
                "affected_dtcs", "affected_ecus"
            ]
        )

        return impact

    # ── IMPACT FROM REQUIREMENT CHANGE ────────────────────

    def analyze_requirement_impact(self, req_id: str) -> Dict:
        """Show the full downstream chain if a requirement changes"""
        req_node = self._node(req_id, self.req_nodes)
        if req_node is None:
            return {"error": f"Requirement {req_id} not found"}

        impact = {
            "req_id":      req_id,
            "requirement": req_node["name"],
            "downstream_chain": [],
            "total_affected_items": 0
        }

        sig_ids = self._targets(req_id, self.req_sig_edges)
        for sig_id in sig_ids:
            sig_impact = self.analyze_signal_impact(sig_id)
            impact["downstream_chain"].append(sig_impact)
            impact["total_affected_items"] += sig_impact.get("total_impact_count", 0)

        tc_ids = self._targets(req_id, self.req_tc_edges)
        impact["affected_test_cases"] = []
        for tc_id in tc_ids:
            tc = self._node(tc_id, self.tc_nodes)
            if tc is not None:
                impact["affected_test_cases"].append({"id": tc_id, "name": tc["name"]})

        impact["total_affected_items"] += len(impact["affected_test_cases"])

        return impact

    def get_all_calibrations_summary(self) -> Dict:
        """Get summary of all calibrations with their current values for impact analysis UI"""
        result = []
        for _, cal in self.cal_nodes.iterrows():
            db_val = self.db_calibrations.get(cal["node_id"], {})
            result.append({
                "cal_id":   cal["node_id"],
                "name":     cal["name"],
                "domain":   cal.get("domain", "Unknown"),
                "value":    db_val.get("value"),
                "unit":     db_val.get("unit", "")
            })
        return {"total": len(result), "calibrations": result}
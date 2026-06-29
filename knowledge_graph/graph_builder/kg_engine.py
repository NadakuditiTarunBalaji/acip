"""
ACIP-X1 Knowledge Graph Engine
Loads all nodes and edges once, provides query functions
for all backend APIs to use.
"""
import pandas as pd
from pathlib import Path
from functools import lru_cache

BASE_PATH = Path(__file__).resolve().parent.parent
NODES_PATH = BASE_PATH / "nodes"
EDGES_PATH = BASE_PATH / "edges"


def _load(filename: str, folder: Path) -> pd.DataFrame:
    path = folder / filename
    if path.exists():
        try:
            df = pd.read_csv(path)
            return df
        except Exception as e:
            print(f"Warning: Could not load {filename}: {e}")
    return pd.DataFrame()


class KnowledgeGraph:
    """Single instance of the full knowledge graph"""

    def __init__(self):
        # ── Nodes ──────────────────────────────────────
        self.vehicle_nodes        = _load("vehicle_nodes.csv",        NODES_PATH)
        self.ecu_nodes            = _load("ecu_nodes.csv",            NODES_PATH)
        self.signal_nodes         = _load("signal_nodes.csv",         NODES_PATH)
        self.dtc_nodes            = _load("dtc_nodes.csv",            NODES_PATH)
        self.fault_nodes          = _load("fault_nodes.csv",          NODES_PATH)
        self.rootcause_nodes      = _load("rootcause_nodes.csv",      NODES_PATH)
        self.action_nodes         = _load("action_nodes.csv",         NODES_PATH)
        self.agent_nodes          = _load("agent_nodes.csv",          NODES_PATH)
        self.calibration_nodes    = _load("calibration_nodes.csv",    NODES_PATH)
        self.requirement_nodes    = _load("requirement_nodes.csv",    NODES_PATH)
        self.testcase_nodes       = _load("testcase_nodes.csv",       NODES_PATH)
        self.health_score_nodes   = _load("health_score_nodes.csv",   NODES_PATH)
        self.risk_level_nodes     = _load("risk_level_nodes.csv",     NODES_PATH)
        self.vehicle_health_nodes = _load("vehicle_health_nodes.csv", NODES_PATH)

        # ── Edges ──────────────────────────────────────
        self.vehicle_ecu_edges          = _load("vehicle_ecu_edges.csv",          EDGES_PATH)
        self.ecu_signal_edges           = _load("ecu_signal_edges.csv",           EDGES_PATH)
        self.signal_dtc_edges           = _load("signal_dtc_edges.csv",           EDGES_PATH)
        self.dtc_fault_edges            = _load("dtc_fault_edges.csv",            EDGES_PATH)
        self.fault_rootcause_edges      = _load("fault_rootcause_edges.csv",      EDGES_PATH)
        self.rootcause_action_edges     = _load("rootcause_action_edges.csv",     EDGES_PATH)
        self.fault_agent_edges          = _load("fault_agent_edges.csv",          EDGES_PATH)
        self.fault_vehiclehealth_edges  = _load("fault_vehiclehealth_edges.csv",  EDGES_PATH)
        self.vehiclehealth_score_edges  = _load("vehiclehealth_score_edges.csv",  EDGES_PATH)
        self.healthscore_risk_edges     = _load("healthscore_risk_edges.csv",     EDGES_PATH)
        self.signal_calibration_edges   = _load("signal_calibration_edges.csv",   EDGES_PATH)
        self.requirement_signal_edges   = _load("requirement_signal_edges.csv",   EDGES_PATH)
        self.requirement_testcase_edges = _load("requirement_testcase_edges.csv", EDGES_PATH)

        print(f"KG Loaded — Nodes: {self._count_nodes()} | Edges: {self._count_edges()}")

    def _count_nodes(self):
        return sum(len(df) for df in [
            self.vehicle_nodes, self.ecu_nodes, self.signal_nodes,
            self.dtc_nodes, self.fault_nodes, self.rootcause_nodes,
            self.action_nodes, self.calibration_nodes,
            self.requirement_nodes, self.testcase_nodes
        ] if not df.empty)

    def _count_edges(self):
        return sum(len(df) for df in [
            self.vehicle_ecu_edges, self.ecu_signal_edges,
            self.signal_dtc_edges, self.dtc_fault_edges,
            self.fault_rootcause_edges, self.rootcause_action_edges,
            self.signal_calibration_edges, self.requirement_signal_edges,
            self.requirement_testcase_edges
        ] if not df.empty)

    # ── QUERY 1: Fault → RootCause → Action ───────────
    def get_fault_analysis(self, fault_id: str) -> dict:
        result = {
            "fault_id": fault_id,
            "fault_name": None,
            "root_causes": [],
            "recommended_actions": [],
            "health_impact": [],
            "risk_level": None
        }

        # Get fault name
        fault = self.fault_nodes[self.fault_nodes["node_id"] == fault_id]
        if not fault.empty:
            result["fault_name"] = fault.iloc[0]["name"]

        # Get root causes
        rc_links = self.fault_rootcause_edges[
            self.fault_rootcause_edges["source"] == fault_id
        ]
        for _, row in rc_links.iterrows():
            rc = self.rootcause_nodes[self.rootcause_nodes["node_id"] == row["target"]]
            if not rc.empty:
                rc_id = row["target"]
                rc_name = rc.iloc[0]["name"]
                result["root_causes"].append(rc_name)

                # Get actions for this root cause
                act_links = self.rootcause_action_edges[
                    self.rootcause_action_edges["source"] == rc_id
                ]
                for _, act_row in act_links.iterrows():
                    action = self.action_nodes[
                        self.action_nodes["node_id"] == act_row["target"]
                    ]
                    if not action.empty:
                        result["recommended_actions"].append(action.iloc[0]["name"])

        # Get health impact
        health_links = self.fault_vehiclehealth_edges[
            self.fault_vehiclehealth_edges["source"] == fault_id
        ]
        for _, row in health_links.iterrows():
            vh = self.vehicle_health_nodes[
                self.vehicle_health_nodes["node_id"] == row["target"]
            ]
            if not vh.empty:
                result["health_impact"].append(vh.iloc[0]["name"])

        return result

    # ── QUERY 2: DTC → Fault → RootCause → Action ─────
    def get_dtc_analysis(self, dtc_id: str) -> dict:
        result = {
            "dtc_id": dtc_id,
            "dtc_name": None,
            "faults": [],
            "root_causes": [],
            "recommended_actions": []
        }

        # Get DTC name
        dtc = self.dtc_nodes[self.dtc_nodes["node_id"] == dtc_id]
        if not dtc.empty:
            result["dtc_name"] = dtc.iloc[0]["name"]

        # Get faults
        fault_links = self.dtc_fault_edges[
            self.dtc_fault_edges["source"] == dtc_id
        ]
        for _, row in fault_links.iterrows():
            fault = self.fault_nodes[self.fault_nodes["node_id"] == row["target"]]
            if not fault.empty:
                fault_id = row["target"]
                result["faults"].append(fault.iloc[0]["name"])

                # Get root causes for this fault
                fault_analysis = self.get_fault_analysis(fault_id)
                result["root_causes"].extend(fault_analysis["root_causes"])
                result["recommended_actions"].extend(fault_analysis["recommended_actions"])

        # Remove duplicates
        result["root_causes"] = list(set(result["root_causes"]))
        result["recommended_actions"] = list(set(result["recommended_actions"]))

        return result

    # ── QUERY 3: Signal → DTC → Fault → Action ────────
    def get_signal_analysis(self, signal_id: str) -> dict:
        result = {
            "signal_id": signal_id,
            "signal_name": None,
            "triggered_dtcs": [],
            "calibration_limits": []
        }

        # Get signal name
        sig = self.signal_nodes[self.signal_nodes["node_id"] == signal_id]
        if not sig.empty:
            result["signal_name"] = sig.iloc[0]["name"]

        # Get triggered DTCs
        dtc_links = self.signal_dtc_edges[
            self.signal_dtc_edges["source"] == signal_id
        ]
        for _, row in dtc_links.iterrows():
            dtc = self.dtc_nodes[self.dtc_nodes["node_id"] == row["target"]]
            if not dtc.empty:
                dtc_analysis = self.get_dtc_analysis(row["target"])
                result["triggered_dtcs"].append(dtc_analysis)

        # Get calibration limits
        cal_links = self.signal_calibration_edges[
            self.signal_calibration_edges["source"] == signal_id
        ]
        for _, row in cal_links.iterrows():
            cal = self.calibration_nodes[
                self.calibration_nodes["node_id"] == row["target"]
            ]
            if not cal.empty:
                result["calibration_limits"].append(cal.iloc[0]["name"])

        return result

    # ── QUERY 4: Requirement Traceability ─────────────
    def get_requirement_trace(self, req_id: str) -> dict:
        result = {
            "req_id": req_id,
            "requirement": None,
            "mapped_signals": [],
            "test_cases": [],
            "traceability_complete": False
        }

        # Get requirement
        req = self.requirement_nodes[self.requirement_nodes["node_id"] == req_id]
        if not req.empty:
            result["requirement"] = req.iloc[0]["name"]

        # Get mapped signals
        sig_links = self.requirement_signal_edges[
            self.requirement_signal_edges["source"] == req_id
        ]
        for _, row in sig_links.iterrows():
            sig = self.signal_nodes[self.signal_nodes["node_id"] == row["target"]]
            if not sig.empty:
                result["mapped_signals"].append({
                    "signal_id": row["target"],
                    "signal_name": sig.iloc[0]["name"]
                })

        # Get test cases
        tc_links = self.requirement_testcase_edges[
            self.requirement_testcase_edges["source"] == req_id
        ]
        for _, row in tc_links.iterrows():
            tc = self.testcase_nodes[self.testcase_nodes["node_id"] == row["target"]]
            if not tc.empty:
                result["test_cases"].append({
                    "tc_id": row["target"],
                    "name": tc.iloc[0]["name"]
                })

        # Check completeness
        result["traceability_complete"] = (
            len(result["mapped_signals"]) > 0 and
            len(result["test_cases"]) > 0
        )

        return result

    # ── QUERY 5: Full Vehicle Chain ────────────────────
    def get_vehicle_chain(self, vehicle_id: str = "VEH001") -> dict:
        result = {
            "vehicle_id": vehicle_id,
            "ecus": [],
            "total_signals": 0,
            "total_dtcs": 0
        }

        ecu_links = self.vehicle_ecu_edges[
            self.vehicle_ecu_edges["source"] == vehicle_id
        ]
        for _, row in ecu_links.iterrows():
            ecu = self.ecu_nodes[self.ecu_nodes["node_id"] == row["target"]]
            if not ecu.empty:
                ecu_id = row["target"]
                ecu_data = {"ecu_id": ecu_id, "name": ecu.iloc[0]["name"], "signals": []}

                sig_links = self.ecu_signal_edges[
                    self.ecu_signal_edges["source"] == ecu_id
                ]
                for _, sig_row in sig_links.iterrows():
                    sig = self.signal_nodes[
                        self.signal_nodes["node_id"] == sig_row["target"]
                    ]
                    if not sig.empty:
                        ecu_data["signals"].append(sig.iloc[0]["name"])
                        result["total_signals"] += 1

                result["ecus"].append(ecu_data)

        result["total_dtcs"] = len(self.dtc_nodes)
        return result

    # ── QUERY 6: Summary ──────────────────────────────
    # ── QUERY 6: Keyword Search (for E9 — AI Chat Assistant) ──
    def search_nodes(self, keyword: str, node_types: list = None) -> dict:
        """
        Searches the 'name' (and 'domain' where present) field of every
        node type for a keyword, case-insensitive substring match.
        Used by E9 to answer topic questions like "show me all
        requirements about battery temperature" — this is a real
        search over the actual loaded CSV data, not an invented list.

        node_types: optional list to restrict the search, e.g.
        ["requirement", "fault"]. If None, searches every node type.
        """
        keyword = keyword.lower().strip()
        all_types = {
            "requirement": self.requirement_nodes,
            "fault": self.fault_nodes,
            "dtc": self.dtc_nodes,
            "signal": self.signal_nodes,
            "calibration": self.calibration_nodes,
            "testcase": self.testcase_nodes,
            "ecu": self.ecu_nodes,
        }
        types_to_search = (
            {t: all_types[t] for t in node_types if t in all_types}
            if node_types else all_types
        )

        results = {}
        for type_name, df in types_to_search.items():
            if df.empty:
                continue
            name_match = df["name"].astype(str).str.lower().str.contains(keyword, na=False)
            domain_match = (
                df["domain"].astype(str).str.lower().str.contains(keyword, na=False)
                if "domain" in df.columns else False
            )
            matched = df[name_match | domain_match]
            if not matched.empty:
                results[type_name] = matched.to_dict("records")

        return {
            "keyword": keyword,
            "total_matches": sum(len(v) for v in results.values()),
            "results": results,
        }

    def get_summary(self) -> dict:
        return {
            "total_nodes": self._count_nodes(),
            "total_edges": self._count_edges(),
            "breakdown": {
                "vehicles":     len(self.vehicle_nodes),
                "ecus":         len(self.ecu_nodes),
                "signals":      len(self.signal_nodes),
                "dtcs":         len(self.dtc_nodes),
                "faults":       len(self.fault_nodes),
                "root_causes":  len(self.rootcause_nodes),
                "actions":      len(self.action_nodes),
                "calibrations": len(self.calibration_nodes),
                "requirements": len(self.requirement_nodes),
                "test_cases":   len(self.testcase_nodes),
            }
        }


# ── Singleton instance ─────────────────────────────────
_kg_instance = None

def get_kg() -> KnowledgeGraph:
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KnowledgeGraph()
    return _kg_instance
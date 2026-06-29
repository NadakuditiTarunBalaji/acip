"""
ACIP-X1 — Knowledge Graph Visualization Engine
Engineering Mode — Feature E6

Generates graph data (nodes + edges) in formats ready for
visualization with vis.js, D3, Plotly, or Streamlit.
"""
from pathlib import Path
from typing import Dict, List, Optional
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


# Color scheme per node type — matches dashboard theme
NODE_COLORS = {
    "Requirement":  "#f85149",
    "Signal":       "#58a6ff",
    "ECU":          "#d29922",
    "Calibration":  "#3fb950",
    "DTC":          "#a371f7",
    "Fault":        "#ff7b72",
    "RootCause":    "#ffa657",
    "Action":       "#7ee787",
    "TestCase":     "#79c0ff",
    "Vehicle":      "#e6edf3",
}

NODE_SIZES = {
    "Requirement":  20,
    "Signal":       16,
    "ECU":          22,
    "Calibration":  14,
    "DTC":          16,
    "Fault":        18,
    "RootCause":    14,
    "Action":       12,
    "TestCase":     12,
    "Vehicle":      26,
}


class KGVisualizer:
    """
    Builds graph data structures for visualization.
    """

    def __init__(self):
        self.node_files = {
            "Vehicle":     "vehicle_nodes.csv",
            "ECU":         "ecu_nodes.csv",
            "Signal":      "signal_nodes.csv",
            "Calibration": "calibration_nodes.csv",
            "DTC":         "dtc_nodes.csv",
            "Fault":       "fault_nodes.csv",
            "RootCause":   "rootcause_nodes.csv",
            "Action":      "action_nodes.csv",
            "Requirement": "requirement_nodes.csv",
            "TestCase":    "testcase_nodes.csv",
        }

        self.edge_files = [
            "vehicle_ecu_edges.csv",
            "ecu_signal_edges.csv",
            "signal_dtc_edges.csv",
            "signal_calibration_edges.csv",
            "dtc_fault_edges.csv",
            "fault_rootcause_edges.csv",
            "rootcause_action_edges.csv",
            "requirement_signal_edges.csv",
            "requirement_testcase_edges.csv",
        ]

        self.nodes_df = {}
        for node_type, filename in self.node_files.items():
            self.nodes_df[node_type] = _load(filename, NODES_PATH)

        self.edges_dfs = []
        for filename in self.edge_files:
            df = _load(filename, EDGES_PATH)
            if not df.empty:
                self.edges_dfs.append(df)

        total_nodes = sum(len(df) for df in self.nodes_df.values())
        total_edges = sum(len(df) for df in self.edges_dfs)
        print(f"KGVisualizer loaded — {total_nodes} nodes, {total_edges} edges")

    def get_full_graph(self) -> Dict:
        """
        Get the complete knowledge graph as nodes + edges
        ready for vis.js / D3 / Plotly visualization.
        """
        nodes = []
        edges = []

        for node_type, df in self.nodes_df.items():
            for _, row in df.iterrows():
                nodes.append({
                    "id":    row["node_id"],
                    "label": row["name"],
                    "group": node_type,
                    "color": NODE_COLORS.get(node_type, "#8b949e"),
                    "size":  NODE_SIZES.get(node_type, 10),
                    "title": f"{node_type}: {row['name']}"
                })

        for df in self.edges_dfs:
            for _, row in df.iterrows():
                edges.append({
                    "from":  row["source"],
                    "to":    row["target"],
                    "label": row.get("relationship", ""),
                    "arrows": "to"
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "legend": [
                {"type": t, "color": c, "count": len(self.nodes_df.get(t, []))}
                for t, c in NODE_COLORS.items()
            ]
        }

    def get_subgraph_for_requirement(self, req_id: str) -> Dict:
        """
        Get the subgraph showing just one requirement's full chain:
        REQ → Signal → ECU/Calibration/DTC → Fault → RootCause → Action
                                            → TestCase
        """
        nodes = []
        edges = []
        added_node_ids = set()

        def add_node(node_id, node_type):
            if node_id in added_node_ids:
                return
            df = self.nodes_df.get(node_type, pd.DataFrame())
            if df.empty:
                return
            row = df[df["node_id"] == node_id]
            if row.empty:
                return
            row = row.iloc[0]
            nodes.append({
                "id":    node_id,
                "label": row["name"],
                "group": node_type,
                "color": NODE_COLORS.get(node_type, "#8b949e"),
                "size":  NODE_SIZES.get(node_type, 10),
                "title": f"{node_type}: {row['name']}"
            })
            added_node_ids.add(node_id)

        def add_edge(source, target, label=""):
            edges.append({"from": source, "to": target, "label": label, "arrows": "to"})

        # Start with requirement
        add_node(req_id, "Requirement")

        # Find edge files
        req_sig = _load("requirement_signal_edges.csv", EDGES_PATH)
        req_tc  = _load("requirement_testcase_edges.csv", EDGES_PATH)
        sig_cal = _load("signal_calibration_edges.csv", EDGES_PATH)
        sig_dtc = _load("signal_dtc_edges.csv", EDGES_PATH)
        dtc_fault = _load("dtc_fault_edges.csv", EDGES_PATH)
        fault_rc  = _load("fault_rootcause_edges.csv", EDGES_PATH)
        rc_action = _load("rootcause_action_edges.csv", EDGES_PATH)
        ecu_sig   = _load("ecu_signal_edges.csv", EDGES_PATH)

        # REQ → Signal
        sig_ids = req_sig[req_sig["source"] == req_id]["target"].tolist()
        for sig_id in sig_ids:
            add_node(sig_id, "Signal")
            add_edge(req_id, sig_id, "MAPS_TO")

            # Signal → ECU
            ecu_ids = ecu_sig[ecu_sig["target"] == sig_id]["source"].tolist()
            for ecu_id in ecu_ids:
                add_node(ecu_id, "ECU")
                add_edge(ecu_id, sig_id, "CONTROLS")

            # Signal → Calibration
            cal_ids = sig_cal[sig_cal["source"] == sig_id]["target"].tolist()
            for cal_id in cal_ids:
                add_node(cal_id, "Calibration")
                add_edge(sig_id, cal_id, "GOVERNED_BY")

            # Signal → DTC
            dtc_ids = sig_dtc[sig_dtc["source"] == sig_id]["target"].tolist()
            for dtc_id in dtc_ids:
                add_node(dtc_id, "DTC")
                add_edge(sig_id, dtc_id, "TRIGGERS")

                # DTC → Fault
                fault_ids = dtc_fault[dtc_fault["source"] == dtc_id]["target"].tolist()
                for fault_id in fault_ids:
                    add_node(fault_id, "Fault")
                    add_edge(dtc_id, fault_id, "CAUSES")

                    # Fault → RootCause
                    rc_ids = fault_rc[fault_rc["source"] == fault_id]["target"].tolist()
                    for rc_id in rc_ids:
                        add_node(rc_id, "RootCause")
                        add_edge(fault_id, rc_id, "CAUSED_BY")

                        # RootCause → Action
                        act_ids = rc_action[rc_action["source"] == rc_id]["target"].tolist()
                        for act_id in act_ids:
                            add_node(act_id, "Action")
                            add_edge(rc_id, act_id, "RESOLVED_BY")

        # REQ → TestCase
        tc_ids = req_tc[req_tc["source"] == req_id]["target"].tolist()
        for tc_id in tc_ids:
            add_node(tc_id, "TestCase")
            add_edge(req_id, tc_id, "VERIFIED_BY")

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "center_node": req_id
        }

    def get_domain_graph(self, domain: str) -> Dict:
        """Get subgraph filtered by domain (Battery or Powertrain)"""
        full = self.get_full_graph()

        filtered_nodes = []
        node_ids = set()

        for node_type, df in self.nodes_df.items():
            if "domain" in df.columns:
                domain_df = df[df["domain"] == domain]
            else:
                domain_df = df

            for _, row in domain_df.iterrows():
                filtered_nodes.append({
                    "id":    row["node_id"],
                    "label": row["name"],
                    "group": node_type,
                    "color": NODE_COLORS.get(node_type, "#8b949e"),
                    "size":  NODE_SIZES.get(node_type, 10),
                    "title": f"{node_type}: {row['name']}"
                })
                node_ids.add(row["node_id"])

        filtered_edges = [
            e for e in full["edges"]
            if e["from"] in node_ids and e["to"] in node_ids
        ]

        return {
            "domain": domain,
            "nodes":  filtered_nodes,
            "edges":  filtered_edges,
            "total_nodes": len(filtered_nodes),
            "total_edges": len(filtered_edges)
        }

    def get_stats(self) -> Dict:
        """Get node/edge counts for visualization legend"""
        return {
            "node_counts": {t: len(df) for t, df in self.nodes_df.items()},
            "edge_count":  sum(len(df) for df in self.edges_dfs),
            "colors":      NODE_COLORS
        }
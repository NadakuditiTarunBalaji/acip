import pandas as pd
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent

nodes_path = BASE_PATH / "nodes"
edges_path = BASE_PATH / "edges"

print("Knowledge Graph Builder Started")
print("Nodes Folder:", nodes_path)
print("Edges Folder:", edges_path)

def load_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        print(f"Loaded {file_path.name} : {len(df)} rows")
        return df
    except Exception as e:
        print(f"Error loading {file_path.name}: {e}")
        return None
    
vehicle_nodes = load_csv(nodes_path / "vehicle_nodes.csv")
ecu_nodes = load_csv(nodes_path / "ecu_nodes.csv")
signal_nodes = load_csv(nodes_path / "signal_nodes.csv")
dtc_nodes = load_csv(nodes_path / "dtc_nodes.csv")
fault_nodes = load_csv(nodes_path / "fault_nodes.csv")
rootcause_nodes = load_csv(nodes_path / "rootcause_nodes.csv")
agent_nodes = load_csv(nodes_path / "agent_nodes.csv")
action_nodes = load_csv(nodes_path / "action_nodes.csv")


vehicle_ecu_edges = load_csv(edges_path / "vehicle_ecu_edges.csv")
ecu_signal_edges = load_csv(edges_path / "ecu_signal_edges.csv")
signal_dtc_edges = load_csv(edges_path / "signal_dtc_edges.csv")
dtc_fault_edges = load_csv(edges_path / "dtc_fault_edges.csv")
fault_rootcause_edges = load_csv(edges_path / "fault_rootcause_edges.csv")
fault_agent_edges = load_csv(edges_path / "fault_agent_edges.csv")
rootcause_action_edges = load_csv(edges_path / "rootcause_action_edges.csv")

print("\n===== GRAPH SUMMARY =====")

datasets = [
    vehicle_nodes,
    ecu_nodes,
    signal_nodes,
    dtc_nodes,
    fault_nodes,
    rootcause_nodes,
    action_nodes,
    agent_nodes,
]

total_nodes = sum(len(df) for df in datasets if df is not None)

print("Total Nodes:", total_nodes)

edge_sets = [
    vehicle_ecu_edges,
    ecu_signal_edges,
    signal_dtc_edges,
    dtc_fault_edges,
    fault_rootcause_edges,
    rootcause_action_edges,
    fault_agent_edges,
]
total_edges = sum(len(df) for df in edge_sets if df is not None)

print("Total Edges:", total_edges)




import pandas as pd
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent

nodes_path = BASE_PATH / "nodes"
edges_path = BASE_PATH / "edges"

fault_nodes = pd.read_csv(nodes_path / "fault_nodes.csv")
rootcause_nodes = pd.read_csv(nodes_path / "rootcause_nodes.csv")
fault_rootcause_edges = pd.read_csv(edges_path / "fault_rootcause_edges.csv")


def find_root_causes(fault_id):
    relationships = fault_rootcause_edges[
        fault_rootcause_edges["source"] == fault_id
    ]

    if relationships.empty:
        print("No root causes found")
        return

    print(f"\nFault: {fault_id}")
    print("-" * 40)

    for _, row in relationships.iterrows():

        rootcause_id = row["target"]

        rootcause = rootcause_nodes[
            rootcause_nodes["node_id"] == rootcause_id
        ]

        if not rootcause.empty:
            print(
                f"Possible Root Cause: "
                f"{rootcause.iloc[0]['name']}"
            )


find_root_causes("FAULT001")
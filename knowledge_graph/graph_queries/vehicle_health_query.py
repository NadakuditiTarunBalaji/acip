import pandas as pd
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent

nodes_path = BASE_PATH / "nodes"
edges_path = BASE_PATH / "edges"

vehicle_health_nodes = pd.read_csv(
    nodes_path / "vehicle_health_nodes.csv"
)

fault_vehiclehealth_edges = pd.read_csv(
    edges_path / "fault_vehiclehealth_edges.csv"
)


def find_impacted_health(fault_id):

    print(f"\nFault: {fault_id}")
    print("=" * 40)

    relationships = fault_vehiclehealth_edges[
        fault_vehiclehealth_edges["source"] == fault_id
    ]

    if relationships.empty:
        print("No health impact found")
        return

    for _, row in relationships.iterrows():

        vh_id = row["target"]

        vh = vehicle_health_nodes[
            vehicle_health_nodes["node_id"] == vh_id
        ]

        if not vh.empty:

            print(
                f"Impacted Health Area: "
                f"{vh.iloc[0]['name']}"
            )


find_impacted_health("FAULT004")
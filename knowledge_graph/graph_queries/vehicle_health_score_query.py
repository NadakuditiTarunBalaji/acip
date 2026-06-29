import pandas as pd
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent

nodes_path = BASE_PATH / "nodes"
edges_path = BASE_PATH / "edges"

vehicle_health_nodes = pd.read_csv(
    nodes_path / "vehicle_health_nodes.csv"
)

health_score_nodes = pd.read_csv(
    nodes_path / "health_score_nodes.csv"
)

fault_vehiclehealth_edges = pd.read_csv(
    edges_path / "fault_vehiclehealth_edges.csv"
)

vehiclehealth_score_edges = pd.read_csv(
    edges_path / "vehiclehealth_score_edges.csv"
)


def get_health_score(fault_id):

    print(f"\nFault: {fault_id}")
    print("=" * 50)

    health_links = fault_vehiclehealth_edges[
        fault_vehiclehealth_edges["source"] == fault_id
    ]

    for _, health_row in health_links.iterrows():

        vh_id = health_row["target"]

        vh = vehicle_health_nodes[
            vehicle_health_nodes["node_id"] == vh_id
        ]

        if vh.empty:
            continue

        vh_name = vh.iloc[0]["name"]

        score_links = vehiclehealth_score_edges[
            vehiclehealth_score_edges["source"] == vh_id
        ]

        for _, score_row in score_links.iterrows():

            hs_id = score_row["target"]

            score = health_score_nodes[
                health_score_nodes["node_id"] == hs_id
            ]

            if not score.empty:

                print(f"Health Area : {vh_name}")
                print(
                    f"Health Score: "
                    f"{score.iloc[0]['name']} "
                    f"({score.iloc[0]['score']})"
                )


get_health_score("FAULT004")
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

risk_level_nodes = pd.read_csv(
    nodes_path / "risk_level_nodes.csv"
)

fault_vehiclehealth_edges = pd.read_csv(
    edges_path / "fault_vehiclehealth_edges.csv"
)

vehiclehealth_score_edges = pd.read_csv(
    edges_path / "vehiclehealth_score_edges.csv"
)

healthscore_risk_edges = pd.read_csv(
    edges_path / "healthscore_risk_edges.csv"
)


def assess_fault(fault_id):

    print(f"\nFault Assessment: {fault_id}")
    print("=" * 60)

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

            if score.empty:
                continue

            score_name = score.iloc[0]["name"]
            score_value = score.iloc[0]["score"]

            risk_links = healthscore_risk_edges[
                healthscore_risk_edges["source"] == hs_id
            ]

            for _, risk_row in risk_links.iterrows():

                rl_id = risk_row["target"]

                risk = risk_level_nodes[
                    risk_level_nodes["node_id"] == rl_id
                ]

                if not risk.empty:

                    print(f"Health Area : {vh_name}")
                    print(
                        f"Health Score: "
                        f"{score_name} ({score_value})"
                    )
                    print(
                        f"Risk Level : "
                        f"{risk.iloc[0]['name']}"
                    )


assess_fault("FAULT004")
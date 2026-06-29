import pandas as pd
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent

nodes_path = BASE_PATH / "nodes"
edges_path = BASE_PATH / "edges"

rootcause_nodes = pd.read_csv(
    nodes_path / "rootcause_nodes.csv"
)

action_nodes = pd.read_csv(
    nodes_path / "action_nodes.csv"
)

rootcause_action_edges = pd.read_csv(
    edges_path / "rootcause_action_edges.csv"
)


def find_actions(rootcause_id):

    relationships = rootcause_action_edges[
        rootcause_action_edges["source"] == rootcause_id
    ]

    if relationships.empty:
        print("No actions found")
        return

    print(f"\nRoot Cause: {rootcause_id}")
    print("-" * 40)

    for _, row in relationships.iterrows():

        action_id = row["target"]

        action = action_nodes[
            action_nodes["node_id"] == action_id
        ]

        if not action.empty:
            print(
                f"Recommended Action: "
                f"{action.iloc[0]['name']}"
            )


find_actions("RC001")
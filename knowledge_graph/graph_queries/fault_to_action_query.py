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

fault_rootcause_edges = pd.read_csv(
    edges_path / "fault_rootcause_edges.csv"
)

rootcause_action_edges = pd.read_csv(
    edges_path / "rootcause_action_edges.csv"
)


def analyze_fault(fault_id):

    print(f"\nFault: {fault_id}")
    print("=" * 50)

    rootcause_links = fault_rootcause_edges[
        fault_rootcause_edges["source"] == fault_id
    ]

    for _, rc_row in rootcause_links.iterrows():

        rc_id = rc_row["target"]

        rc = rootcause_nodes[
            rootcause_nodes["node_id"] == rc_id
        ]

        if rc.empty:
            continue

        rc_name = rc.iloc[0]["name"]

        print(f"\nPossible Root Cause: {rc_name}")

        action_links = rootcause_action_edges[
            rootcause_action_edges["source"] == rc_id
        ]

        for _, act_row in action_links.iterrows():

            act_id = act_row["target"]

            action = action_nodes[
                action_nodes["node_id"] == act_id
            ]

            if not action.empty:

                print(
                    f"  Recommended Action: "
                    f"{action.iloc[0]['name']}"
                )


analyze_fault("FAULT001")
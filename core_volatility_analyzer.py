import os
import glob
from collections import deque
import networkx as nx
import pandas as pd


def _get_strong_bridges(graph):
    """
    Identify all strong bridges in a strongly connected directed graph.
    A directed edge (u, v) is a strong bridge if its removal increases
    the number of strongly connected components (SCCs).
    """
    strong_bridges = []
    base_scc_count = nx.number_strongly_connected_components(graph)
    edges_list = list(graph.edges())

    for u, v in edges_list:
        graph.remove_edge(u, v)
        new_scc_count = nx.number_strongly_connected_components(graph)
        graph.add_edge(u, v)

        if new_scc_count > base_scc_count:
            strong_bridges.append((u, v))

    return strong_bridges


def find_2_escc(lscc_graph):
    """
    Extract the Largest 2-Edge-Strongly-Connected Component (L2-ESCC, denoted Omega_t)
    strictly within the Largest Strongly Connected Component (LSCC).

    Uses iterative strong-bridge decomposition on induced vertex subgraphs
    to guarantee Mengerian path redundancy (lambda_G(u, v) >= 2).
    """
    empty_subgraph = nx.DiGraph()

    if lscc_graph.number_of_nodes() < 2:
        return empty_subgraph

    queue = deque([set(lscc_graph.nodes())])
    best_core_nodes = set()
    max_nodes = 0

    while queue:
        nodes_set = queue.popleft()

        if len(nodes_set) <= max_nodes:
            continue

        subgraph = lscc_graph.subgraph(nodes_set).copy()
        bridges = _get_strong_bridges(subgraph)

        if not bridges:
            if len(nodes_set) > max_nodes:
                best_core_nodes = nodes_set
                max_nodes = len(nodes_set)
            continue

        subgraph.remove_edges_from(bridges)
        new_sccs = [set(scc) for scc in nx.strongly_connected_components(subgraph)]

        for scc in new_sccs:
            if len(scc) >= 2 and len(scc) > max_nodes:
                queue.append(scc)

    if best_core_nodes:
        return lscc_graph.subgraph(best_core_nodes).copy()

    return empty_subgraph


def compute_transition_metrics(edges_t, edges_next, zero_empty_default=True):
    """
    Compute set-theoretic core transition operators and Jaccard-based volatility:
      - Retention (R): E(Omega_t) intersect E(Omega_{t+1})
      - Contraction (C): E(Omega_t) \\ E(Omega_{t+1})
      - Expansion (X): E(Omega_{t+1}) \\ E(Omega_t)
      - Volatility (v_t): 1 - |R| / |E(Omega_t) union E(Omega_{t+1})|
    """
    if not edges_t and not edges_next:
        volatility = 0.0 if zero_empty_default else float("nan")
        return 0, 0, 0, volatility

    retention = len(edges_t.intersection(edges_next))
    contraction = len(edges_t.difference(edges_next))
    expansion = len(edges_next.difference(edges_t))
    union_size = len(edges_t.union(edges_next))

    volatility = 1.0 - (retention / union_size) if union_size > 0 else 0.0
    return retention, contraction, expansion, volatility


def calculate_core_volatility_pipeline(owner, repo, base_dir="./data/temporal_networks"):
    """
    Run longitudinal 2-ESCC extraction and volatility analysis across monthly snapshots
    for a given repository. Saves transition metrics to CSV and prints summary statistics.
    """
    project_dir = os.path.join(base_dir, f"temporal_networks_{owner}_{repo}")
    file_pattern = os.path.join(project_dir, "time_edge_list_file_*.txt")
    snapshot_files = sorted(glob.glob(file_pattern))

    if not snapshot_files:
        print(f"No snapshot files found in directory: {project_dir}")
        return None

    print(f"\n--- LONGITUDINAL 2-ESCC & VOLATILITY ANALYSIS: {owner}/{repo} ---")

    cores_vertices, cores_edges = {}, {}
    lscc_vertices, lscc_edges = {}, {}
    global_edges = {}

    monthly_v_counts, monthly_e_counts, monthly_densities = [], [], []
    monthly_lscc_v, monthly_lscc_e = [], []
    monthly_core_v, monthly_core_e = [], []

    for file_path in snapshot_files:
        month_str = (
            os.path.basename(file_path)
            .replace("time_edge_list_file_", "")
            .replace(".txt", "")
        )

        G = nx.read_edgelist(file_path, create_using=nx.DiGraph(), nodetype=str)
        global_edges[month_str] = frozenset(G.edges())

        v_count = G.number_of_nodes()
        e_count = G.number_of_edges()
        density = nx.density(G) if v_count > 1 else 0.0

        monthly_v_counts.append(v_count)
        monthly_e_counts.append(e_count)
        monthly_densities.append(density)

        sccs = [scc for scc in nx.strongly_connected_components(G) if len(scc) >= 2]
        if sccs:
            max_scc_nodes = max(sccs, key=len)
            lscc_subgraph = G.subgraph(max_scc_nodes).copy()

            lscc_vertices[month_str] = frozenset(max_scc_nodes)
            lscc_edges[month_str] = frozenset(lscc_subgraph.edges())
            monthly_lscc_v.append(len(max_scc_nodes))
            monthly_lscc_e.append(len(lscc_subgraph.edges()))

            core_subgraph = find_2_escc(lscc_subgraph)
        else:
            lscc_vertices[month_str] = frozenset()
            lscc_edges[month_str] = frozenset()
            monthly_lscc_v.append(0)
            monthly_lscc_e.append(0)
            core_subgraph = nx.DiGraph()

        current_core_nodes = set(core_subgraph.nodes())
        current_core_edges = set(core_subgraph.edges())

        cores_vertices[month_str] = frozenset(current_core_nodes)
        cores_edges[month_str] = frozenset(current_core_edges)

        monthly_core_v.append(len(current_core_nodes))
        monthly_core_e.append(len(current_core_edges))

    months = sorted(cores_vertices.keys())
    metrics_records = []

    for i in range(len(months) - 1):
        m_t = months[i]
        m_next = months[i + 1]

        ret_core, con_core, exp_core, core_vol = compute_transition_metrics(
            cores_edges[m_t], cores_edges[m_next]
        )
        _, _, _, lscc_vol = compute_transition_metrics(
            lscc_edges[m_t], lscc_edges[m_next]
        )
        _, _, _, global_churn = compute_transition_metrics(
            global_edges[m_t], global_edges[m_next]
        )

        metrics_records.append({
            "Month_t": m_t,
            "Month_t+1": m_next,
            "LSCC_Size_t": len(lscc_vertices[m_t]),
            "LSCC_Size_t+1": len(lscc_vertices[m_next]),
            "LSCC_Edge_Volatility": round(lscc_vol, 4),
            "Core_Size_t": len(cores_vertices[m_t]),
            "Core_Size_t+1": len(cores_vertices[m_next]),
            "Core_Retention_R": ret_core,
            "Core_Contraction_C": con_core,
            "Core_Expansion_X": exp_core,
            "Core_Volatility": round(core_vol, 4),
            "Global_Tie_Churn_CE": round(global_churn, 4),
        })

    df_metrics = pd.DataFrame(metrics_records)

    n_windows = len(snapshot_files)
    mean_v = sum(monthly_v_counts) / n_windows if n_windows else 0
    mean_e = sum(monthly_e_counts) / n_windows if n_windows else 0
    mean_density = sum(monthly_densities) / n_windows if n_windows else 0
    mean_ce = df_metrics["Global_Tie_Churn_CE"].mean() if not df_metrics.empty else 0

    mean_lscc_v = sum(monthly_lscc_v) / n_windows if n_windows else 0
    mean_lscc_e = sum(monthly_lscc_e) / n_windows if n_windows else 0
    mean_core_v = sum(monthly_core_v) / n_windows if n_windows else 0
    mean_core_e = sum(monthly_core_e) / n_windows if n_windows else 0

    print("\n================ SUMMARY DESCRIPTIVE METRICS ================")
    print(f"  Windows (T)            : {n_windows}")
    print(f"  Mean <V> (Global)      : {round(mean_v, 1)}")
    print(f"  Mean <E> (Global)      : {round(mean_e, 1)}")
    print(f"  Mean Density           : {round(mean_density, 5)}")
    print(f"  Mean Tie Churn (C_E)   : {round(mean_ce, 4)}")
    print(f"  Mean |V(LSCC)|         : {round(mean_lscc_v, 2)}")
    print(f"  Mean |E(LSCC)|         : {round(mean_lscc_e, 2)}")
    print(f"  Mean |V(Omega_2)|      : {round(mean_core_v, 2)}")
    print(f"  Mean |E(Omega_2)|      : {round(mean_core_e, 2)}")
    print("===========================================================")

    output_csv = os.path.join(project_dir, f"core_volatility_metrics_{owner}_{repo}.csv")
    df_metrics.to_csv(output_csv, index=False)
    print(f"Metrics saved to: {output_csv}")
    return df_metrics


if __name__ == "__main__":
    calculate_core_volatility_pipeline("google", "zx")

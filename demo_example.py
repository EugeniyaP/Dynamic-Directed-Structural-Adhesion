import networkx as nx
from core_volatility_analyzer import find_2_escc, compute_transition_metrics


def run_topological_displacement_demo():
    """
    Demonstrates the Topological Displacement mechanism (Figure 2 in the paper):
    An edge (u, v) remains active in the global graph at t+1, yet is flushed out
    of the 2-ESCC core because its parallel backup path collapses (lambda < 2).
    """
    # Snapshot t: Core {1, 2, 3} forms a 2-edge-strongly-connected cycle with parallel chords
    G_t = nx.DiGraph([
        (1, 2), (2, 3), (3, 1),  # Primary cycle
        (1, 3), (3, 2), (2, 1),  # Reverse/backup paths -> lambda(u, v) >= 2 for all pairs
        (1, 4), (4, 5),          # Peripheral transient ties
    ])

    # Snapshot t+1: Backup link (3, 2) collapses; edge (1, 2) stays in G_{t+1}
    # but loses its alternative path from 2 back to 1 (becomes a strong bridge)
    G_next = nx.DiGraph([
        (1, 2), (2, 3), (3, 1),
        (1, 3), (2, 1),          # (3, 2) removed -> node 3 has out-degree 1 (only 3->1)
        (1, 6), (6, 7),          # Peripheral churn
    ])

    lscc_t = G_t.subgraph(max(nx.strongly_connected_components(G_t), key=len)).copy()
    lscc_next = G_next.subgraph(max(nx.strongly_connected_components(G_next), key=len)).copy()

    core_t = find_2_escc(lscc_t)
    core_next = find_2_escc(lscc_next)

    ret, con, exp, vol = compute_transition_metrics(
        frozenset(core_t.edges()), frozenset(core_next.edges())
    )

    print("=== TOPOLOGICAL DISPLACEMENT & 2-ESCC DEMO ===")
    print(f"Window t   -> LSCC nodes: {sorted(lscc_t.nodes())}, 2-ESCC core nodes: {sorted(core_t.nodes())}")
    print(f"Window t+1 -> LSCC nodes: {sorted(lscc_next.nodes())}, 2-ESCC core nodes: {sorted(core_next.nodes())}")
    print(f"Edge (2, 3) active in global G_{{t+1}}? {(2, 3) in G_next.edges()}")
    print(f"Edge (2, 3) retained in 2-ESCC Omega_{{t+1}}? {(2, 3) in core_next.edges()} (Topologically Displaced!)")
    print(f"Core Operators -> Retention (R): {ret}, Contraction (C): {con}, Expansion (X): {exp}")
    print(f"Core Volatility Index (v_t): {vol:.4f}")


if __name__ == "__main__":
    run_topological_displacement_demo()

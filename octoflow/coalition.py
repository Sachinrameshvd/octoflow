"""Coalition extraction and graph analysis tools for OctoFlow."""

from typing import Any

import numpy as np


def extract_coalitions_from_matrix(
    coalition_matrix: np.ndarray | Any,
    threshold: float = 0.15,
    symmetric: bool = True,
) -> dict[str, Any]:
    """Extract discrete coalition clusters and connected components from attention weights.

    Args:
        coalition_matrix: (N, N) pairwise attention weights matrix.
        threshold: Minimum attention weight to consider an active binding edge.
        symmetric: If True, treats connection as active if either A_ij or A_ji >= threshold.

    Returns:
        Dictionary containing:
            - active_coalitions: List of sets, each containing indices of arms in a multi-arm coalition.
            - isolated_modules: List of module indices acting independently.
            - edge_list: List of active undirected edges (i, j, weight).
            - coalition_sizes: List of sizes for each detected multi-arm coalition.
            - num_active_coalitions: Integer count of multi-arm coalitions (size >= 2).
    """
    if hasattr(coalition_matrix, "detach"):
        c_mat = coalition_matrix.detach().cpu().numpy()
    else:
        c_mat = np.array(coalition_matrix)

    n_modules = c_mat.shape[0]

    # Build adjacency graph
    adj = {i: set() for i in range(n_modules)}
    edge_list: list[tuple[int, int, float]] = []

    for i in range(n_modules):
        for j in range(i + 1, n_modules):
            w_ij = float(c_mat[i, j])
            w_ji = float(c_mat[j, i])
            max_w = max(w_ij, w_ji) if symmetric else w_ij

            if max_w >= threshold:
                adj[i].add(j)
                adj[j].add(i)
                edge_list.append((i, j, max_w))

    # Connected component traversal (BFS)
    visited: set[int] = set()
    multi_arm_coalitions: list[set[int]] = []
    isolated_modules: list[int] = []

    for node in range(n_modules):
        if node not in visited:
            component: set[int] = set()
            queue = [node]
            visited.add(node)

            while queue:
                curr = queue.pop(0)
                component.add(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            if len(component) >= 2:
                multi_arm_coalitions.append(component)
            else:
                isolated_modules.append(node)

    coalition_sizes = [len(c) for c in multi_arm_coalitions]

    return {
        "active_coalitions": multi_arm_coalitions,
        "isolated_modules": isolated_modules,
        "edge_list": edge_list,
        "coalition_sizes": coalition_sizes,
        "num_active_coalitions": len(multi_arm_coalitions),
    }

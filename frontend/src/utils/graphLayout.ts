import { Graph, layout } from '@dagrejs/dagre';
import type { Edge, Node } from '@xyflow/react';

export interface LayoutOptions {
  /** TB | LR | BT | RL */
  direction?: 'TB' | 'LR' | 'BT' | 'RL';
  nodeWidth?: number;
  nodeHeight?: number;
  nodesep?: number;
  ranksep?: number;
  marginx?: number;
  marginy?: number;
}

/**
 * Run dagre layout and return nodes with computed positions.
 * Positions are top-left of each node (React Flow convention with nodeOrigin [0,0]).
 */
export function layoutWithDagre<N extends Node, E extends Edge>(
  nodes: N[],
  edges: E[],
  options: LayoutOptions = {},
): N[] {
  const {
    direction = 'TB',
    nodeWidth = 160,
    nodeHeight = 48,
    nodesep = 36,
    ranksep = 64,
    marginx = 24,
    marginy = 24,
  } = options;

  if (nodes.length === 0) return nodes;

  const g = new Graph({ directed: true, multigraph: true });
  g.setGraph({
    rankdir: direction,
    nodesep,
    ranksep,
    marginx,
    marginy,
  });
  g.setDefaultEdgeLabel(() => ({}));

  for (const node of nodes) {
    const w = (node.measured?.width ?? node.width ?? nodeWidth) as number;
    const h = (node.measured?.height ?? node.height ?? nodeHeight) as number;
    g.setNode(node.id, { width: w, height: h });
  }

  for (const edge of edges) {
    // Skip edges whose endpoints are missing (partial graphs)
    if (!g.hasNode(edge.source) || !g.hasNode(edge.target)) continue;
    g.setEdge(edge.source, edge.target, {}, edge.id);
  }

  layout(g);

  return nodes.map((node) => {
    const pos = g.node(node.id);
    if (!pos) return node;
    const w = (pos.width as number) || nodeWidth;
    const h = (pos.height as number) || nodeHeight;
    return {
      ...node,
      position: {
        x: (pos.x as number) - w / 2,
        y: (pos.y as number) - h / 2,
      },
    };
  });
}

import type { DiagramIrV01a, EdgeV01a, NodeV01a } from "./types.js";

export type CanonicalNodeV01a = NodeV01a & {
  order: number;
};

export type CanonicalEdgeV01a = EdgeV01a & {
  order: number;
};

export type CanonicalDiagramIrV01a = Omit<DiagramIrV01a, "nodes" | "edges"> & {
  nodes: CanonicalNodeV01a[];
  edges: CanonicalEdgeV01a[];
  nodeOrder: string[];
  edgeOrder: string[];
};

export function canonicalizeDiagramIr(document: DiagramIrV01a): CanonicalDiagramIrV01a {
  const nodes = document.nodes.map((node, order) => ({ ...node, order }));
  const edges = document.edges.map((edge, order) => ({ ...edge, order }));

  return {
    ...document,
    nodes,
    edges,
    nodeOrder: nodes.map((node) => node.id),
    edgeOrder: edges.map((edge) => edge.id)
  };
}

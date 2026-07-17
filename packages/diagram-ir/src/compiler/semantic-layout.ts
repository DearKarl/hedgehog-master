import type { CanonicalDiagramIrV01a } from "../ir/canonicalize.js";
import type { CanonicalEdgeV01a, CanonicalNodeV01a } from "../ir/canonicalize.js";
import type { LayoutEdge, LayoutModel, LayoutNode, Point } from "./layout-model.js";
import { wrapLabel } from "./label.js";
import { layoutRankedDataflow } from "./ranked-layout.js";

const CANVAS_WIDTH = 1600;
const CANVAS_HEIGHT = 900;
const NODE_WIDTH = 240;
const NODE_HEIGHT = 78;

export function layoutSemanticDiagram(document: CanonicalDiagramIrV01a): LayoutModel {
  switch (document.kind) {
    case "dataflow":
      return layoutRankedDataflow(document);
    case "cycle":
      return layoutCycle(document);
    case "comparison":
      return layoutComparison(document);
    case "architecture":
      return layoutArchitecture(document);
    case "timeline":
      return layoutTimeline(document);
  }
}

function layoutCycle(document: CanonicalDiagramIrV01a): LayoutModel {
  const centerX = CANVAS_WIDTH / 2;
  const centerY = CANVAS_HEIGHT / 2;
  const radiusX = 500;
  const radiusY = 290;
  const count = Math.max(1, document.nodes.length);
  const nodes = document.nodes.map((node, index) => {
    const angle = -Math.PI / 2 + (2 * Math.PI * index) / count;
    return makeNode(
      node,
      round(centerX + Math.cos(angle) * radiusX - NODE_WIDTH / 2),
      round(centerY + Math.sin(angle) * radiusY - NODE_HEIGHT / 2),
      index,
      index
    );
  });
  return makeModel(document, nodes);
}

function layoutComparison(document: CanonicalDiagramIrV01a): LayoutModel {
  const namedGroups = [...new Set(document.nodes.map((node) => node.group).filter(Boolean))];
  const split = Math.ceil(document.nodes.length / 2);
  const groups = namedGroups.length >= 2 ? namedGroups.slice(0, 2) : ["A", "B"];
  const left = document.nodes.filter((node, index) =>
    namedGroups.length >= 2 ? node.group === groups[0] : index < split
  );
  const right = document.nodes.filter((node, index) =>
    namedGroups.length >= 2 ? node.group !== groups[0] : index >= split
  );
  const nodes = [...columnNodes(left, 220, 0), ...columnNodes(right, 1140, left.length)];
  return makeModel(document, nodes);
}

function columnNodes(
  source: readonly CanonicalNodeV01a[],
  x: number,
  orderOffset: number
): LayoutNode[] {
  const top = 150;
  const bottom = CANVAS_HEIGHT - 150 - NODE_HEIGHT;
  return source.map((node, index) => {
    const y =
      source.length <= 1
        ? (top + bottom) / 2
        : top + ((bottom - top) * index) / (source.length - 1);
    return makeNode(node, x, round(y), index, orderOffset + index, 280);
  });
}

function layoutArchitecture(document: CanonicalDiagramIrV01a): LayoutModel {
  const ranked = layoutRankedDataflow(document);
  const nodes = ranked.nodes.map((node) => ({
    ...node,
    x: round(150 + (node.y / CANVAS_HEIGHT) * 1180),
    y: round(100 + (node.x / CANVAS_WIDTH) * 650),
    width: 260,
    height: NODE_HEIGHT
  }));
  return makeModel(document, nodes);
}

function layoutTimeline(document: CanonicalDiagramIrV01a): LayoutModel {
  const left = 100;
  const right = CANVAS_WIDTH - 100 - NODE_WIDTH;
  const count = Math.max(1, document.nodes.length);
  const nodes = document.nodes.map((node, index) => {
    const x = count <= 1 ? (left + right) / 2 : left + ((right - left) * index) / (count - 1);
    const y = index % 2 === 0 ? 245 : 535;
    return makeNode(node, round(x), y, index, index);
  });
  return makeModel(document, nodes);
}

function makeNode(
  node: CanonicalNodeV01a,
  x: number,
  y: number,
  rank: number,
  order: number,
  width: number = NODE_WIDTH
): LayoutNode {
  return {
    id: node.id,
    label: node.label,
    role: node.role,
    x,
    y,
    width,
    height: NODE_HEIGHT,
    rank,
    order,
    labelLines: wrapLabel(node.label),
    ...(node.group === undefined ? {} : { group: node.group })
  };
}

function makeModel(document: CanonicalDiagramIrV01a, nodes: LayoutNode[]): LayoutModel {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  return {
    kind: document.kind,
    canvas: { width: CANVAS_WIDTH, height: CANVAS_HEIGHT },
    nodes,
    edges: document.edges.map((edge) => makeEdge(edge, byId))
  };
}

function makeEdge(edge: CanonicalEdgeV01a, byId: ReadonlyMap<string, LayoutNode>): LayoutEdge {
  const source = byId.get(edge.from);
  const target = byId.get(edge.to);
  if (source === undefined || target === undefined) {
    throw new Error(`Cannot layout edge '${edge.id}' with missing endpoint.`);
  }
  const fromPoint = boundaryPoint(source, target);
  const toPoint = boundaryPoint(target, source);
  const points = orthogonalPoints(fromPoint, toPoint);
  return {
    id: edge.id,
    from: edge.from,
    to: edge.to,
    ...(edge.label === undefined ? {} : { label: edge.label }),
    ...(edge.evidenceRef === undefined ? {} : { evidenceRef: edge.evidenceRef }),
    points,
    fromPoint,
    toPoint
  };
}

function boundaryPoint(source: LayoutNode, target: LayoutNode): Point {
  const sourceX = source.x + source.width / 2;
  const sourceY = source.y + source.height / 2;
  const targetX = target.x + target.width / 2;
  const targetY = target.y + target.height / 2;
  const dx = targetX - sourceX;
  const dy = targetY - sourceY;
  if (dx === 0 && dy === 0) {
    return { x: round(sourceX), y: round(sourceY) };
  }
  const scaleX = dx === 0 ? Number.POSITIVE_INFINITY : source.width / 2 / Math.abs(dx);
  const scaleY = dy === 0 ? Number.POSITIVE_INFINITY : source.height / 2 / Math.abs(dy);
  const scale = Math.min(scaleX, scaleY);
  return { x: round(sourceX + dx * scale), y: round(sourceY + dy * scale) };
}

function orthogonalPoints(from: Point, to: Point): Point[] {
  if (Math.abs(to.x - from.x) >= Math.abs(to.y - from.y)) {
    const midX = round((from.x + to.x) / 2);
    return [from, { x: midX, y: from.y }, { x: midX, y: to.y }, to];
  }
  const midY = round((from.y + to.y) / 2);
  return [from, { x: from.x, y: midY }, { x: to.x, y: midY }, to];
}

function round(value: number): number {
  return Number(value.toFixed(3));
}

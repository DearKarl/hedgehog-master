import type { CanonicalDiagramIrV01a } from "../ir/canonicalize.js";
import type { LayoutEdge, LayoutModel, LayoutNode, Point } from "./layout-model.js";
import { wrapLabel } from "./label.js";

const CANVAS_WIDTH = 1600;
const CANVAS_HEIGHT = 900;
const NODE_WIDTH = 220;
const NODE_HEIGHT = 72;
const LEFT_MARGIN = 120;
const RIGHT_MARGIN = 120;
const TOP_MARGIN = 120;
const BOTTOM_MARGIN = 120;

export function layoutRankedDataflow(document: CanonicalDiagramIrV01a): LayoutModel {
  const rankByNodeId = calculateRanks(document);
  const maxRank = Math.max(0, ...rankByNodeId.values());
  const nodesByRank = groupNodesByRank(document, rankByNodeId);
  const layoutNodes = document.nodes.map((node): LayoutNode => {
    const rank = rankByNodeId.get(node.id);

    if (rank === undefined) {
      throw new Error(`Cannot layout node '${node.id}' without a rank.`);
    }

    const rankNodes = nodesByRank.get(rank) ?? [];
    const orderWithinRank = rankNodes.findIndex((rankNode) => rankNode.id === node.id);

    if (orderWithinRank < 0) {
      throw new Error(`Cannot layout node '${node.id}' without a rank order.`);
    }

    return {
      id: node.id,
      label: node.label,
      role: node.role,
      x: rankToX(rank, maxRank),
      y: orderToY(orderWithinRank, rankNodes.length),
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      rank,
      order: orderWithinRank,
      labelLines: wrapLabel(node.label)
    };
  });
  const nodeById = new Map(layoutNodes.map((node) => [node.id, node]));
  const layoutEdges = document.edges.map((edge): LayoutEdge => {
    const sourceNode = nodeById.get(edge.from);
    const targetNode = nodeById.get(edge.to);

    if (sourceNode === undefined || targetNode === undefined) {
      throw new Error(`Cannot layout edge '${edge.id}' with missing endpoint.`);
    }

    const fromPoint = rightMidpoint(sourceNode);
    const toPoint = leftMidpoint(targetNode);
    const midX = roundCoordinate((fromPoint.x + toPoint.x) / 2);
    const points = [fromPoint, { x: midX, y: fromPoint.y }, { x: midX, y: toPoint.y }, toPoint];

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
  });

  return {
    canvas: {
      width: CANVAS_WIDTH,
      height: CANVAS_HEIGHT
    },
    nodes: layoutNodes,
    edges: layoutEdges
  };
}

function calculateRanks(document: CanonicalDiagramIrV01a): Map<string, number> {
  const adjacency = new Map<string, string[]>();
  const indegree = new Map<string, number>();
  const rankByNodeId = new Map<string, number>();

  for (const node of document.nodes) {
    adjacency.set(node.id, []);
    indegree.set(node.id, 0);
    rankByNodeId.set(node.id, 0);
  }

  for (const edge of document.edges) {
    adjacency.get(edge.from)?.push(edge.to);
    indegree.set(edge.to, (indegree.get(edge.to) ?? 0) + 1);
  }

  const queue = document.nodes.filter((node) => indegree.get(node.id) === 0).map((node) => node.id);
  let visitedCount = 0;

  for (let index = 0; index < queue.length; index += 1) {
    const nodeId = queue[index]!;
    const nodeRank = rankByNodeId.get(nodeId)!;
    visitedCount += 1;

    for (const nextNodeId of adjacency.get(nodeId) ?? []) {
      rankByNodeId.set(nextNodeId, Math.max(rankByNodeId.get(nextNodeId) ?? 0, nodeRank + 1));

      const nextIndegree = (indegree.get(nextNodeId) ?? 0) - 1;
      indegree.set(nextNodeId, nextIndegree);

      if (nextIndegree === 0) {
        queue.push(nextNodeId);
      }
    }
  }

  if (visitedCount !== document.nodes.length) {
    throw new Error("Cannot layout cyclic dataflow graph. v0.1a ranked layout requires a DAG.");
  }

  return rankByNodeId;
}

function groupNodesByRank(
  document: CanonicalDiagramIrV01a,
  rankByNodeId: ReadonlyMap<string, number>
): Map<number, typeof document.nodes> {
  const nodesByRank = new Map<number, typeof document.nodes>();

  for (const node of document.nodes) {
    const rank = rankByNodeId.get(node.id);

    if (rank === undefined) {
      continue;
    }

    const existing = nodesByRank.get(rank) ?? [];
    existing.push(node);
    nodesByRank.set(rank, existing);
  }

  return nodesByRank;
}

function rankToX(rank: number, maxRank: number): number {
  const maxX = CANVAS_WIDTH - RIGHT_MARGIN - NODE_WIDTH;
  const availableWidth = maxX - LEFT_MARGIN;

  if (maxRank === 0) {
    return roundCoordinate(LEFT_MARGIN + availableWidth / 2);
  }

  return roundCoordinate(LEFT_MARGIN + (availableWidth * rank) / maxRank);
}

function orderToY(order: number, nodeCountInRank: number): number {
  const maxY = CANVAS_HEIGHT - BOTTOM_MARGIN - NODE_HEIGHT;
  const availableHeight = maxY - TOP_MARGIN;

  if (nodeCountInRank <= 1) {
    return roundCoordinate(TOP_MARGIN + availableHeight / 2);
  }

  return roundCoordinate(TOP_MARGIN + (availableHeight * order) / (nodeCountInRank - 1));
}

function rightMidpoint(node: LayoutNode): Point {
  return {
    x: roundCoordinate(node.x + node.width),
    y: roundCoordinate(node.y + node.height / 2)
  };
}

function leftMidpoint(node: LayoutNode): Point {
  return {
    x: roundCoordinate(node.x),
    y: roundCoordinate(node.y + node.height / 2)
  };
}

function roundCoordinate(value: number): number {
  return Number(value.toFixed(3));
}

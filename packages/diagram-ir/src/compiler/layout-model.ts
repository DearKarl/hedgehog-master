import type { NodeRole } from "../ir/types.js";

export type Point = {
  x: number;
  y: number;
};

export type LayoutNode = {
  id: string;
  label: string;
  role: NodeRole;
  x: number;
  y: number;
  width: number;
  height: number;
  rank: number;
  order: number;
  labelLines: string[];
};

export type LayoutEdge = {
  id: string;
  from: string;
  to: string;
  label?: string;
  evidenceRef?: string;
  points: Point[];
  fromPoint: Point;
  toPoint: Point;
};

export type LayoutModel = {
  canvas: {
    width: 1600;
    height: 900;
  };
  nodes: LayoutNode[];
  edges: LayoutEdge[];
};

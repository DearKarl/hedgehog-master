import type { LayoutEdge, LayoutModel, LayoutNode, Point } from "../layout-model.js";
import type { NodeRole } from "../../ir/types.js";
import type { SvgAttribute, SvgElement, SvgText } from "./ast.js";
import { formatNumber } from "./numeric.js";

const ROLE_FILL: Record<NodeRole, string> = {
  source: "#E0F2FE",
  transform: "#DCFCE7",
  model: "#EDE9FE",
  metric: "#FEF3C7",
  output: "#FFE4E6"
};

export function buildSvgAst(layout: LayoutModel): SvgElement {
  return element(
    "svg",
    [
      attr("xmlns", "http://www.w3.org/2000/svg"),
      attr(
        "viewBox",
        `0 0 ${formatNumber(layout.canvas.width)} ${formatNumber(layout.canvas.height)}`
      ),
      attr("width", formatNumber(layout.canvas.width)),
      attr("height", formatNumber(layout.canvas.height)),
      attr("role", "img"),
      attr("aria-labelledby", "title desc")
    ],
    [
      element("title", [attr("id", "title")], [text("Hedgehog One diagram")]),
      element(
        "desc",
        [attr("id", "desc")],
        [text("Deterministic dataflow diagram generated from LayoutModel")]
      ),
      buildDefs(),
      element("rect", [
        attr("id", "background"),
        attr("x", "0"),
        attr("y", "0"),
        attr("width", formatNumber(layout.canvas.width)),
        attr("height", formatNumber(layout.canvas.height)),
        attr("fill", "#ffffff")
      ]),
      element("g", [attr("id", "edges")], layout.edges.map(buildEdge)),
      element("g", [attr("id", "nodes")], layout.nodes.map(buildNode)),
      element("g", [attr("id", "labels")], layout.nodes.map(buildLabel))
    ]
  );
}

function buildDefs(): SvgElement {
  return element(
    "defs",
    [],
    [
      element(
        "marker",
        [
          attr("id", "arrow"),
          attr("viewBox", "0 0 10 10"),
          attr("refX", "10"),
          attr("refY", "5"),
          attr("markerWidth", "8"),
          attr("markerHeight", "8"),
          attr("orient", "auto-start-reverse")
        ],
        [element("path", [attr("d", "M 0 0 L 10 5 L 0 10 z"), attr("fill", "#334155")])]
      )
    ]
  );
}

function buildEdge(edge: LayoutEdge): SvgElement {
  return element("polyline", [
    attr("id", edge.id),
    attr("points", formatPoints(edge.points)),
    attr("stroke", "#334155"),
    attr("fill", "none"),
    attr("marker-end", "url(#arrow)")
  ]);
}

function buildNode(node: LayoutNode): SvgElement {
  return element("rect", [
    attr("id", node.id),
    attr("x", formatNumber(node.x)),
    attr("y", formatNumber(node.y)),
    attr("width", formatNumber(node.width)),
    attr("height", formatNumber(node.height)),
    attr("rx", "12"),
    attr("fill", ROLE_FILL[node.role]),
    attr("stroke", "#0F172A")
  ]);
}

function buildLabel(node: LayoutNode): SvgElement {
  const centerX = formatNumber(node.x + node.width / 2);
  const firstLineY = formatNumber(
    node.y + node.height / 2 - ((node.labelLines.length - 1) * 20) / 2
  );

  return element(
    "text",
    [
      attr("id", `${node.id}-label`),
      attr("x", centerX),
      attr("y", firstLineY),
      attr("text-anchor", "middle"),
      attr("font-family", "Inter, Arial, sans-serif"),
      attr("font-size", "16"),
      attr("fill", "#0F172A")
    ],
    node.labelLines.map((line, index) =>
      element("tspan", [attr("x", centerX), attr("dy", index === 0 ? "0" : "20")], [text(line)])
    )
  );
}

function formatPoints(points: readonly Point[]): string {
  return points.map((point) => `${formatNumber(point.x)},${formatNumber(point.y)}`).join(" ");
}

function element(
  name: string,
  attributes: SvgAttribute[] = [],
  children: SvgElement[] | SvgText[] = []
): SvgElement {
  return {
    kind: "element",
    name,
    attributes,
    children
  };
}

function text(value: string): SvgText {
  return {
    kind: "text",
    value
  };
}

function attr(name: string, value: string): SvgAttribute {
  return { name, value };
}

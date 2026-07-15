import { describe, expect, it } from "vitest";

import type { SvgElement, SvgNode } from "../../../../src/compiler/svg/ast.js";
import { buildSvgAst } from "../../../../src/compiler/svg/build-svg-ast.js";
import { canonicalizeDiagramIr } from "../../../../src/ir/canonicalize.js";
import { validateDiagramIr } from "../../../../src/ir/validate.js";
import { layoutRankedDataflow } from "../../../../src/compiler/ranked-layout.js";
import { readFixtureJson } from "../../../helpers/fixtures.js";

async function buildAstFromFixture(path: string): Promise<SvgElement> {
  const validation = validateDiagramIr(await readFixtureJson(path));

  if (!validation.ok) {
    throw new Error(JSON.stringify(validation.diagnostics, null, 2));
  }

  return buildSvgAst(layoutRankedDataflow(canonicalizeDiagramIr(validation.value)));
}

function childElements(element: SvgElement): SvgElement[] {
  return element.children.filter((child): child is SvgElement => child.kind === "element");
}

function attributeValue(element: SvgElement, name: string): string | undefined {
  return element.attributes.find((attribute) => attribute.name === name)?.value;
}

function walk(node: SvgNode): SvgNode[] {
  if (node.kind === "text") {
    return [node];
  }

  return [node, ...node.children.flatMap(walk)];
}

describe("buildSvgAst", () => {
  it("sets root SVG attributes", async () => {
    const root = await buildAstFromFixture("valid/simple-dataflow.diagram.json");

    expect(root.name).toBe("svg");
    expect(root.attributes).toEqual([
      { name: "xmlns", value: "http://www.w3.org/2000/svg" },
      { name: "viewBox", value: "0 0 1600 900" },
      { name: "width", value: "1600" },
      { name: "height", value: "900" },
      { name: "role", value: "img" },
      { name: "aria-labelledby", value: "title desc" }
    ]);
  });

  it("uses the fixed child order", async () => {
    const root = await buildAstFromFixture("valid/simple-dataflow.diagram.json");
    const children = childElements(root);

    expect(children.map((child) => child.name)).toEqual([
      "title",
      "desc",
      "defs",
      "rect",
      "g",
      "g",
      "g"
    ]);
    expect(children.map((child) => attributeValue(child, "id"))).toEqual([
      "title",
      "desc",
      undefined,
      "background",
      "edges",
      "nodes",
      "labels"
    ]);
  });

  it("includes the arrow marker", async () => {
    const root = await buildAstFromFixture("valid/simple-dataflow.diagram.json");
    const marker = walk(root).find(
      (node): node is SvgElement =>
        node.kind === "element" && node.name === "marker" && attributeValue(node, "id") === "arrow"
    );

    expect(marker).toBeDefined();
  });

  it("matches node and edge counts from the LayoutModel", async () => {
    const root = await buildAstFromFixture("valid/simple-dataflow.diagram.json");
    const groups = childElements(root).filter((child) => child.name === "g");
    const edges = groups.find((group) => attributeValue(group, "id") === "edges");
    const nodes = groups.find((group) => attributeValue(group, "id") === "nodes");

    expect(edges?.children).toHaveLength(4);
    expect(nodes?.children).toHaveLength(5);
  });

  it("preserves duplicate polyline points", async () => {
    const root = await buildAstFromFixture("valid/simple-dataflow.diagram.json");
    const polyline = walk(root).find(
      (node): node is SvgElement =>
        node.kind === "element" &&
        node.name === "polyline" &&
        attributeValue(node, "id") === "edge-source-clean"
    );

    expect(attributeValue(polyline!, "points")).toBe("340,450 372.5,450 372.5,450 405,450");
  });

  it("uses stable role fill mapping", async () => {
    const root = await buildAstFromFixture("valid/simple-dataflow.diagram.json");
    const rects = walk(root).filter(
      (node): node is SvgElement => node.kind === "element" && node.name === "rect"
    );

    expect(rects.map((rect) => [attributeValue(rect, "id"), attributeValue(rect, "fill")])).toEqual(
      [
        ["background", "#ffffff"],
        ["source-data", "#E0F2FE"],
        ["clean-data", "#DCFCE7"],
        ["train-model", "#EDE9FE"],
        ["quality-metric", "#FEF3C7"],
        ["report-output", "#FFE4E6"]
      ]
    );
  });

  it("does not include raw SVG passthrough nodes", async () => {
    const root = await buildAstFromFixture("valid/simple-dataflow.diagram.json");

    expect(walk(root).every((node) => node.kind === "element" || node.kind === "text")).toBe(true);
    expect(
      walk(root).some(
        (node) => node.kind === "element" && (node.name === "script" || node.name === "style")
      )
    ).toBe(false);
  });

  it("is deterministic for the same layout", async () => {
    const first = await buildAstFromFixture("valid/simple-dataflow.diagram.json");
    const second = await buildAstFromFixture("valid/simple-dataflow.diagram.json");

    expect(second).toEqual(first);
  });
});

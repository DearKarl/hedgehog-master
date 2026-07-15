import { describe, expect, it } from "vitest";

import { layoutRankedDataflow } from "../../../src/compiler/ranked-layout.js";
import type { LayoutModel, LayoutNode } from "../../../src/compiler/layout-model.js";
import { canonicalizeDiagramIr } from "../../../src/ir/canonicalize.js";
import { validateDiagramIr } from "../../../src/ir/validate.js";
import { readFixtureJson } from "../../helpers/fixtures.js";

async function layoutFixture(path: string): Promise<LayoutModel> {
  const result = validateDiagramIr(await readFixtureJson(path));

  if (!result.ok) {
    throw new Error(JSON.stringify(result.diagnostics, null, 2));
  }

  return layoutRankedDataflow(canonicalizeDiagramIr(result.value));
}

function findNode(layout: LayoutModel, id: string): LayoutNode {
  const node = layout.nodes.find((candidate) => candidate.id === id);

  if (node === undefined) {
    throw new Error(`Missing layout node '${id}'.`);
  }

  return node;
}

describe("layoutRankedDataflow", () => {
  it("generates a LayoutModel for valid simple dataflow", async () => {
    const layout = await layoutFixture("valid/simple-dataflow.diagram.json");

    expect(layout).toMatchObject({
      canvas: { width: 1600, height: 900 }
    });
    expect(layout.nodes).toHaveLength(5);
    expect(layout.edges).toHaveLength(4);
  });

  it("uses a fixed 1600 x 900 canvas", async () => {
    const layout = await layoutFixture("valid/simple-dataflow.diagram.json");

    expect(layout.canvas).toEqual({ width: 1600, height: 900 });
  });

  it("uses fixed 220 x 72 node dimensions", async () => {
    const layout = await layoutFixture("valid/simple-dataflow.diagram.json");

    expect(layout.nodes.every((node) => node.width === 220 && node.height === 72)).toBe(true);
  });

  it("places nodes left-to-right with increasing x coordinates by rank", async () => {
    const layout = await layoutFixture("valid/simple-dataflow.diagram.json");
    const source = findNode(layout, "source-data");
    const clean = findNode(layout, "clean-data");
    const model = findNode(layout, "train-model");
    const metric = findNode(layout, "quality-metric");
    const output = findNode(layout, "report-output");

    expect([source.rank, clean.rank, model.rank, metric.rank, output.rank]).toEqual([
      0, 1, 2, 3, 4
    ]);
    expect(source.x).toBeLessThan(clean.x);
    expect(clean.x).toBeLessThan(model.x);
    expect(model.x).toBeLessThan(metric.x);
    expect(metric.x).toBeLessThan(output.x);
  });

  it("keeps same-rank nodes in input order", async () => {
    const layout = await layoutFixture("valid/branching-dataflow.diagram.json");
    const cleanA = findNode(layout, "clean-a");
    const cleanB = findNode(layout, "clean-b");

    expect(cleanA.rank).toBe(1);
    expect(cleanB.rank).toBe(1);
    expect(cleanA.order).toBe(0);
    expect(cleanB.order).toBe(1);
    expect(cleanA.y).toBeLessThan(cleanB.y);
  });

  it("sets multi-parent rank to max parent rank plus one", async () => {
    const layout = await layoutFixture("valid/multi-parent-dataflow.diagram.json");
    const sourceA = findNode(layout, "source-a");
    const sourceB = findNode(layout, "source-b");
    const transformA = findNode(layout, "transform-a");
    const modelA = findNode(layout, "model-a");

    expect(sourceA.rank).toBe(0);
    expect(sourceB.rank).toBe(0);
    expect(transformA.rank).toBe(1);
    expect(modelA.rank).toBe(2);
  });

  it("connects edge fromPoint to the source node right boundary midpoint", async () => {
    const layout = await layoutFixture("valid/simple-dataflow.diagram.json");
    const edge = layout.edges[0]!;
    const source = findNode(layout, edge.from);

    expect(edge.fromPoint).toEqual({ x: source.x + source.width, y: source.y + source.height / 2 });
  });

  it("connects edge toPoint to the target node left boundary midpoint", async () => {
    const layout = await layoutFixture("valid/simple-dataflow.diagram.json");
    const edge = layout.edges[0]!;
    const target = findNode(layout, edge.to);

    expect(edge.toPoint).toEqual({ x: target.x, y: target.y + target.height / 2 });
  });

  it("produces stable edge points", async () => {
    const layout = await layoutFixture("valid/simple-dataflow.diagram.json");

    expect(layout.edges[0]?.points).toEqual([
      { x: 340, y: 450 },
      { x: 372.5, y: 450 },
      { x: 372.5, y: 450 },
      { x: 405, y: 450 }
    ]);
  });

  it("produces identical layout for the same input", async () => {
    const first = await layoutFixture("valid/branching-dataflow.diagram.json");
    const second = await layoutFixture("valid/branching-dataflow.diagram.json");

    expect(second).toEqual(first);
  });

  it("limits long label output to two lines", async () => {
    const layout = await layoutFixture("valid/long-label-dataflow.diagram.json");
    const node = findNode(layout, "very-long-source");

    expect(node.labelLines.length).toBeLessThanOrEqual(2);
  });

  it("uses ellipsis when long labels exceed two lines", async () => {
    const layout = await layoutFixture("valid/long-label-dataflow.diagram.json");
    const node = findNode(layout, "very-long-source");

    expect(node.labelLines[1]).toMatch(/\.\.\.$/u);
  });

  it("does not generate an SVG string", async () => {
    const layout = await layoutFixture("valid/simple-dataflow.diagram.json");

    expect(typeof layout).toBe("object");
    expect(JSON.stringify(layout)).not.toContain("<svg");
  });
});

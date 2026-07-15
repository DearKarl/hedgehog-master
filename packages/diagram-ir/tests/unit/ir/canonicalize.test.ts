import { describe, expect, it } from "vitest";

import { canonicalizeDiagramIr } from "../../../src/ir/canonicalize.js";
import { validateDiagramIr } from "../../../src/ir/validate.js";
import { readFixtureJson } from "../../helpers/fixtures.js";

async function readValidFixture(path: string) {
  const result = validateDiagramIr(await readFixtureJson(path));

  if (!result.ok) {
    throw new Error(JSON.stringify(result.diagnostics, null, 2));
  }

  return result.value;
}

describe("canonicalizeDiagramIr", () => {
  it("preserves node input order", async () => {
    const document = await readValidFixture("valid/simple-dataflow.diagram.json");
    const canonical = canonicalizeDiagramIr(document);

    expect(canonical.nodeOrder).toEqual(document.nodes.map((node) => node.id));
    expect(canonical.nodes.map((node) => node.order)).toEqual([0, 1, 2, 3, 4]);
  });

  it("preserves edge input order", async () => {
    const document = await readValidFixture("valid/simple-dataflow.diagram.json");
    const canonical = canonicalizeDiagramIr(document);

    expect(canonical.edgeOrder).toEqual(document.edges.map((edge) => edge.id));
    expect(canonical.edges.map((edge) => edge.order)).toEqual([0, 1, 2, 3]);
  });

  it("does not modify the original document object", async () => {
    const document = await readValidFixture("valid/simple-dataflow.diagram.json");
    const before = structuredClone(document);

    canonicalizeDiagramIr(document);

    expect(document).toEqual(before);
    expect(document.nodes[0]).not.toHaveProperty("order");
    expect(document.edges[0]).not.toHaveProperty("order");
  });

  it("does not fill missing fields that validation should reject", async () => {
    const document = await readValidFixture("valid/simple-dataflow.diagram.json");
    const invalidDocument = { ...document } as Record<string, unknown>;
    delete invalidDocument.title;

    const canonical = canonicalizeDiagramIr(invalidDocument as typeof document);

    expect(canonical).not.toHaveProperty("title");
  });
});

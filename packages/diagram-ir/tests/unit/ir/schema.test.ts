import { Ajv } from "ajv";
import { describe, expect, it } from "vitest";

import { DiagramIrV01aSchema } from "../../../src/ir/schema.js";
import { readFixtureJson, readProjectJson } from "../../helpers/fixtures.js";

const ajv = new Ajv({ allErrors: true, strict: true });
const validate = ajv.compile(DiagramIrV01aSchema);

function expectValid(document: unknown): void {
  expect(validate(document), JSON.stringify(validate.errors, null, 2)).toBe(true);
}

function expectInvalid(document: unknown, keyword: string, instancePath: string): void {
  expect(validate(document)).toBe(false);
  expect(validate.errors).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        instancePath,
        keyword
      })
    ])
  );
}

describe("Diagram IR v0.2 schema", () => {
  it("accepts the valid simple dataflow fixture", async () => {
    expectValid(await readFixtureJson("valid/simple-dataflow.diagram.json"));
  });

  it("keeps the published JSON schema consistent with the TypeBox schema", async () => {
    const publishedSchema = await readProjectJson("schemas/diagram-ir.v0.2.schema.json");

    expect(publishedSchema).toEqual(JSON.parse(JSON.stringify(DiagramIrV01aSchema)));
  });

  it("rejects unknown root fields", async () => {
    expectInvalid(
      await readFixtureJson("invalid/unknown-field.diagram.json"),
      "additionalProperties",
      ""
    );
  });

  it("rejects invalid kind values", async () => {
    expectInvalid(await readFixtureJson("invalid/invalid-kind.diagram.json"), "anyOf", "/kind");
  });

  it("accepts the v0.2 scientific diagram kinds", async () => {
    for (const [kind, direction] of [
      ["cycle", "clockwise"],
      ["comparison", "left-to-right"],
      ["architecture", "top-to-bottom"],
      ["timeline", "left-to-right"]
    ]) {
      expectValid({
        irVersion: "0.2",
        id: `${kind}-example`,
        title: `${kind} example`,
        kind,
        direction,
        nodes: [
          { id: "first", label: "First", role: "source", group: "A" },
          { id: "second", label: "Second", role: "output", group: "B" }
        ],
        edges: [{ id: "first-second", from: "first", to: "second" }],
        metadata: {}
      });
    }
  });

  it("rejects invalid node roles", async () => {
    expectInvalid(
      await readFixtureJson("invalid/invalid-role.diagram.json"),
      "anyOf",
      "/nodes/0/role"
    );
  });

  it("rejects missing required fields", async () => {
    const document = await readFixtureJson("valid/simple-dataflow.diagram.json");
    const withoutTitle = { ...(document as Record<string, unknown>) };
    delete withoutTitle.title;

    expectInvalid(withoutTitle, "required", "");
  });

  it("rejects diagram ids that are not SVG-safe", async () => {
    expectInvalid(
      await readFixtureJson("invalid/invalid-diagram-id.diagram.json"),
      "pattern",
      "/id"
    );
  });

  it("rejects node ids that are not SVG-safe", async () => {
    expectInvalid(
      await readFixtureJson("invalid/invalid-node-id.diagram.json"),
      "pattern",
      "/nodes/0/id"
    );
  });

  it("rejects edge ids that are not SVG-safe", async () => {
    expectInvalid(
      await readFixtureJson("invalid/invalid-edge-id.diagram.json"),
      "pattern",
      "/edges/0/id"
    );
  });

  it("rejects empty evidenceRef values", async () => {
    const document = await readFixtureJson("valid/simple-dataflow.diagram.json");
    const withEmptyEvidenceRef = structuredClone(document) as {
      edges: Array<Record<string, unknown>>;
    };
    const firstEdge = withEmptyEvidenceRef.edges[0];

    expect(firstEdge).toBeDefined();
    firstEdge!.evidenceRef = "";

    expectInvalid(withEmptyEvidenceRef, "minLength", "/edges/0/evidenceRef");
  });
});

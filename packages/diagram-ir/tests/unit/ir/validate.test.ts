import { describe, expect, it } from "vitest";

import { ErrorCodes } from "../../../src/errors/codes.js";
import type { Diagnostic } from "../../../src/ir/diagnostics.js";
import { sortDiagnostics } from "../../../src/ir/diagnostics.js";
import { parseDiagramJson } from "../../../src/ir/parse.js";
import { validateDiagramIr } from "../../../src/ir/validate.js";
import { readFixtureJson } from "../../helpers/fixtures.js";

function expectDiagnostic(
  diagnostics: readonly Diagnostic[],
  code: Diagnostic["code"],
  path: string
): void {
  expect(diagnostics).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        code,
        path
      })
    ])
  );
}

async function expectInvalidFixture(
  fixturePath: string,
  code: Diagnostic["code"],
  path: string
): Promise<void> {
  const result = validateDiagramIr(await readFixtureJson(fixturePath));

  expect(result.ok).toBe(false);

  if (!result.ok) {
    expectDiagnostic(result.diagnostics, code, path);
  }
}

describe("Diagram IR v0.1a validation", () => {
  it("accepts the valid simple dataflow fixture", async () => {
    const result = validateDiagramIr(await readFixtureJson("valid/simple-dataflow.diagram.json"));

    expect(result.ok).toBe(true);
  });

  it("returns IR_DUPLICATE_NODE_ID for duplicate node ids", async () => {
    await expectInvalidFixture(
      "invalid/duplicate-node-id.diagram.json",
      ErrorCodes.IR_DUPLICATE_NODE_ID,
      "/nodes/1/id"
    );
  });

  it("returns IR_DUPLICATE_EDGE_ID for duplicate edge ids", async () => {
    await expectInvalidFixture(
      "invalid/duplicate-edge-id.diagram.json",
      ErrorCodes.IR_DUPLICATE_EDGE_ID,
      "/edges/1/id"
    );
  });

  it("returns IR_UNKNOWN_EDGE_FROM for unknown edge source nodes", async () => {
    await expectInvalidFixture(
      "invalid/unknown-edge-from.diagram.json",
      ErrorCodes.IR_UNKNOWN_EDGE_FROM,
      "/edges/0/from"
    );
  });

  it("returns IR_UNKNOWN_EDGE_TO for unknown edge target nodes", async () => {
    await expectInvalidFixture(
      "invalid/unknown-edge-to.diagram.json",
      ErrorCodes.IR_UNKNOWN_EDGE_TO,
      "/edges/0/to"
    );
  });

  it("returns IR_CYCLE_DETECTED for cyclic dataflow graphs", async () => {
    await expectInvalidFixture(
      "invalid/cycle.diagram.json",
      ErrorCodes.IR_CYCLE_DETECTED,
      "/edges"
    );
  });

  it("returns IR_PARSE_ERROR for malformed JSON", () => {
    const result = parseDiagramJson('{"irVersion":"0.1a",');

    expect(result.ok).toBe(false);

    if (!result.ok) {
      expectDiagnostic(result.diagnostics, ErrorCodes.IR_PARSE_ERROR, "");
    }
  });

  it("returns IR_UNKNOWN_FIELD for unknown root fields", async () => {
    await expectInvalidFixture(
      "invalid/unknown-field.diagram.json",
      ErrorCodes.IR_UNKNOWN_FIELD,
      "/layout"
    );
  });

  it("returns IR_MISSING_REQUIRED_FIELD for missing title", async () => {
    const document = await readFixtureJson("valid/simple-dataflow.diagram.json");
    const withoutTitle = { ...(document as Record<string, unknown>) };
    delete withoutTitle.title;
    const result = validateDiagramIr(withoutTitle);

    expect(result.ok).toBe(false);

    if (!result.ok) {
      expectDiagnostic(result.diagnostics, ErrorCodes.IR_MISSING_REQUIRED_FIELD, "/title");
    }
  });

  it("returns IR_INVALID_NODE_ROLE for invalid roles", async () => {
    await expectInvalidFixture(
      "invalid/invalid-role.diagram.json",
      ErrorCodes.IR_INVALID_NODE_ROLE,
      "/nodes/0/role"
    );
  });

  it("returns IR_UNSUPPORTED_KIND for unsupported kinds", async () => {
    await expectInvalidFixture(
      "invalid/invalid-kind.diagram.json",
      ErrorCodes.IR_UNSUPPORTED_KIND,
      "/kind"
    );
  });

  it("returns IR_UNSUPPORTED_DIRECTION for unsupported directions", async () => {
    const document = await readFixtureJson("valid/simple-dataflow.diagram.json");
    const withInvalidDirection = {
      ...(document as Record<string, unknown>),
      direction: "top-to-bottom"
    };
    const result = validateDiagramIr(withInvalidDirection);

    expect(result.ok).toBe(false);

    if (!result.ok) {
      expectDiagnostic(result.diagnostics, ErrorCodes.IR_UNSUPPORTED_DIRECTION, "/direction");
    }
  });

  it("returns IR_INVALID_ID for diagram ids with spaces", async () => {
    await expectInvalidFixture(
      "invalid/invalid-diagram-id.diagram.json",
      ErrorCodes.IR_INVALID_ID,
      "/id"
    );
  });

  it("returns IR_INVALID_ID for node ids with spaces", async () => {
    await expectInvalidFixture(
      "invalid/invalid-node-id.diagram.json",
      ErrorCodes.IR_INVALID_ID,
      "/nodes/0/id"
    );
  });

  it("returns IR_INVALID_ID for edge ids with spaces", async () => {
    await expectInvalidFixture(
      "invalid/invalid-edge-id.diagram.json",
      ErrorCodes.IR_INVALID_ID,
      "/edges/0/id"
    );
  });

  it("sorts diagnostics by path, code, and message", () => {
    const diagnostics: Diagnostic[] = [
      {
        code: ErrorCodes.IR_UNKNOWN_EDGE_TO,
        severity: "error",
        path: "/edges/1/to",
        message: "z"
      },
      {
        code: ErrorCodes.IR_DUPLICATE_NODE_ID,
        severity: "error",
        path: "/nodes/1/id",
        message: "a"
      },
      {
        code: ErrorCodes.IR_UNKNOWN_EDGE_FROM,
        severity: "error",
        path: "/edges/1/from",
        message: "m"
      },
      {
        code: ErrorCodes.IR_UNKNOWN_EDGE_FROM,
        severity: "error",
        path: "/edges/1/from",
        message: "a"
      }
    ];

    expect(sortDiagnostics(diagnostics).map((diagnostic) => diagnostic.message)).toEqual([
      "a",
      "m",
      "z",
      "a"
    ]);
  });
});

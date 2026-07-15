import { describe, expect, it } from "vitest";

import {
  checkDeterministicDiagramJsonCompile,
  compileDiagramJsonToSvg,
  compileValidatedDiagramIrToSvg
} from "../../../src/compiler/compile.js";
import { ErrorCodes } from "../../../src/errors/codes.js";
import { validateDiagramIr } from "../../../src/ir/validate.js";
import { readFixtureJson } from "../../helpers/fixtures.js";

async function fixtureString(path: string): Promise<string> {
  return JSON.stringify(await readFixtureJson(path));
}

describe("compileDiagramJsonToSvg", () => {
  it("compiles valid JSON to an SVG string", async () => {
    const result = compileDiagramJsonToSvg(
      await fixtureString("valid/simple-dataflow.diagram.json")
    );

    expect(result.ok).toBe(true);

    if (result.ok) {
      expect(result.svg).toContain("<svg");
    }
  });

  it("returns diagnostics for invalid JSON", () => {
    const result = compileDiagramJsonToSvg("{");

    expect(result.ok).toBe(false);

    if (!result.ok) {
      expect(result.diagnostics).toEqual(
        expect.arrayContaining([expect.objectContaining({ code: ErrorCodes.IR_PARSE_ERROR })])
      );
    }
  });

  it("returns diagnostics for invalid IR", async () => {
    const result = compileDiagramJsonToSvg(
      await fixtureString("invalid/invalid-kind.diagram.json")
    );

    expect(result.ok).toBe(false);

    if (!result.ok) {
      expect(result.diagnostics).toEqual(
        expect.arrayContaining([expect.objectContaining({ code: ErrorCodes.IR_UNSUPPORTED_KIND })])
      );
    }
  });

  it("compiles the same input byte-identically", async () => {
    const input = await fixtureString("valid/simple-dataflow.diagram.json");
    const first = compileDiagramJsonToSvg(input);
    const second = compileDiagramJsonToSvg(input);

    expect(first.ok).toBe(true);
    expect(second.ok).toBe(true);

    if (first.ok && second.ok) {
      expect(second.svg).toBe(first.svg);
    }
  });

  it("compiles a validated fixture", async () => {
    const validation = validateDiagramIr(
      await readFixtureJson("valid/simple-dataflow.diagram.json")
    );

    expect(validation.ok).toBe(true);

    if (validation.ok) {
      expect(compileValidatedDiagramIrToSvg(validation.value)).toContain("<svg");
    }
  });

  it("returns SVG output containing the root SVG tag", async () => {
    const result = compileDiagramJsonToSvg(
      await fixtureString("valid/simple-dataflow.diagram.json")
    );

    expect(result.ok).toBe(true);

    if (result.ok) {
      expect(result.svg.startsWith("<svg ")).toBe(true);
    }
  });

  it("does not return svg for invalid input", async () => {
    const result = compileDiagramJsonToSvg(
      await fixtureString("invalid/invalid-role.diagram.json")
    );

    expect(result.ok).toBe(false);
    expect("svg" in result).toBe(false);
  });

  it("checks deterministic in-memory compilation", async () => {
    const result = checkDeterministicDiagramJsonCompile(
      await fixtureString("valid/simple-dataflow.diagram.json")
    );

    expect(result.ok).toBe(true);
  });
});

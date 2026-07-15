import { describe, expect, it } from "vitest";

import { buildSvgAst } from "../../../../src/compiler/svg/build-svg-ast.js";
import { serializeSvg } from "../../../../src/compiler/svg/serialize.js";
import { layoutRankedDataflow } from "../../../../src/compiler/ranked-layout.js";
import { canonicalizeDiagramIr } from "../../../../src/ir/canonicalize.js";
import { validateDiagramIr } from "../../../../src/ir/validate.js";
import { readFixtureJson } from "../../../helpers/fixtures.js";

async function serializeSimpleDataflow(): Promise<string> {
  const validation = validateDiagramIr(await readFixtureJson("valid/simple-dataflow.diagram.json"));

  if (!validation.ok) {
    throw new Error(JSON.stringify(validation.diagnostics, null, 2));
  }

  return serializeSvg(buildSvgAst(layoutRankedDataflow(canonicalizeDiagramIr(validation.value))));
}

describe("simple dataflow SVG snapshot", () => {
  it("matches the stable SVG snapshot", async () => {
    const svg = await serializeSimpleDataflow();

    expect(svg).toMatchInlineSnapshot(`
      "<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900" role="img" aria-labelledby="title desc">
        <title id="title">Hedgehog One diagram</title>
        <desc id="desc">Deterministic dataflow diagram generated from LayoutModel</desc>
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#334155" />
          </marker>
        </defs>
        <rect id="background" x="0" y="0" width="1600" height="900" fill="#ffffff" />
        <g id="edges">
          <polyline id="edge-source-clean" points="340,450 372.5,450 372.5,450 405,450" stroke="#334155" fill="none" marker-end="url(#arrow)" />
          <polyline id="edge-clean-model" points="625,450 657.5,450 657.5,450 690,450" stroke="#334155" fill="none" marker-end="url(#arrow)" />
          <polyline id="edge-model-metric" points="910,450 942.5,450 942.5,450 975,450" stroke="#334155" fill="none" marker-end="url(#arrow)" />
          <polyline id="edge-metric-output" points="1195,450 1227.5,450 1227.5,450 1260,450" stroke="#334155" fill="none" marker-end="url(#arrow)" />
        </g>
        <g id="nodes">
          <rect id="source-data" x="120" y="414" width="220" height="72" rx="12" fill="#E0F2FE" stroke="#0F172A" />
          <rect id="clean-data" x="405" y="414" width="220" height="72" rx="12" fill="#DCFCE7" stroke="#0F172A" />
          <rect id="train-model" x="690" y="414" width="220" height="72" rx="12" fill="#EDE9FE" stroke="#0F172A" />
          <rect id="quality-metric" x="975" y="414" width="220" height="72" rx="12" fill="#FEF3C7" stroke="#0F172A" />
          <rect id="report-output" x="1260" y="414" width="220" height="72" rx="12" fill="#FFE4E6" stroke="#0F172A" />
        </g>
        <g id="labels">
          <text id="source-data-label" x="230" y="450" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="16" fill="#0F172A">
            <tspan x="230" dy="0">Source Data</tspan>
          </text>
          <text id="clean-data-label" x="515" y="450" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="16" fill="#0F172A">
            <tspan x="515" dy="0">Clean Data</tspan>
          </text>
          <text id="train-model-label" x="800" y="450" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="16" fill="#0F172A">
            <tspan x="800" dy="0">Train Model</tspan>
          </text>
          <text id="quality-metric-label" x="1085" y="450" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="16" fill="#0F172A">
            <tspan x="1085" dy="0">Quality Metric</tspan>
          </text>
          <text id="report-output-label" x="1370" y="450" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="16" fill="#0F172A">
            <tspan x="1370" dy="0">Report Output</tspan>
          </text>
        </g>
      </svg>
      "
    `);
  });

  it("serializes the same input byte-identically twice", async () => {
    await expect(serializeSimpleDataflow()).resolves.toBe(await serializeSimpleDataflow());
  });

  it("contains title and desc", async () => {
    const svg = await serializeSimpleDataflow();

    expect(svg).toContain("<title");
    expect(svg).toContain("<desc");
  });

  it("does not include non-deterministic markers", async () => {
    const svg = await serializeSimpleDataflow();

    expect(svg).not.toContain("Date");
    expect(svg).not.toContain("timestamp");
    expect(svg).not.toContain("/Users");
    expect(svg).not.toContain("node_modules");
    expect(svg).not.toContain("random");
    expect(svg).not.toContain("Math.random");
  });
});

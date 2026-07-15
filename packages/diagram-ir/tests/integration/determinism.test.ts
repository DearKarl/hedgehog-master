import { access, mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";

import { beforeAll, describe, expect, it } from "vitest";

import { compileDiagramJsonToSvg } from "../../src/compiler/compile.js";
import { buildDist, projectRoot, runDistCli } from "./cli-helpers.js";

type JsonNode = {
  id: string;
  label: string;
  role: string;
};

type JsonEdge = {
  id: string;
  from: string;
  to: string;
  label?: string;
  evidenceRef?: string;
};

type JsonDiagram = {
  irVersion: string;
  id: string;
  title: string;
  kind: string;
  direction: string;
  nodes: JsonNode[];
  edges: JsonEdge[];
  metadata: unknown;
};

const examplePath = resolve(projectRoot, "examples/simple-dataflow.diagram.json");

async function readExampleInput(): Promise<string> {
  return readFile(examplePath, "utf8");
}

function expectSvgResult(result: ReturnType<typeof compileDiagramJsonToSvg>): string {
  expect(result.ok).toBe(true);

  if (!result.ok) {
    throw new Error("Expected successful SVG compile.");
  }

  return result.svg;
}

async function pathExists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

describe("v0.1a deterministic acceptance", () => {
  beforeAll(() => {
    buildDist();
  });

  it("compiles the same input twice to identical SVG bytes in the library path", async () => {
    const input = await readExampleInput();
    const firstSvg = expectSvgResult(compileDiagramJsonToSvg(input));
    const secondSvg = expectSvgResult(compileDiagramJsonToSvg(input));

    expect(secondSvg).toBe(firstSvg);
  });

  it("compiles the same input twice to identical SVG files in the dist CLI path", async () => {
    const tempDir = await mkdtemp(join(tmpdir(), "hedgehog1-determinism-"));

    try {
      const firstPath = join(tempDir, "first.svg");
      const secondPath = join(tempDir, "second.svg");

      const first = await runDistCli([
        "compile",
        "examples/simple-dataflow.diagram.json",
        "-o",
        firstPath
      ]);
      const second = await runDistCli([
        "compile",
        "examples/simple-dataflow.diagram.json",
        "-o",
        secondPath
      ]);

      expect(first.exitCode).toBe(0);
      expect(second.exitCode).toBe(0);
      expect(await readFile(secondPath, "utf8")).toBe(await readFile(firstPath, "utf8"));
    } finally {
      await rm(tempDir, { recursive: true, force: true });
    }
  });

  it("passes the check command for a valid fixture", async () => {
    const result = await runDistCli(["check", "tests/fixtures/valid/simple-dataflow.diagram.json"]);

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toBe("OK\n");
  });

  it("does not produce SVG output for invalid input", async () => {
    const tempDir = await mkdtemp(join(tmpdir(), "hedgehog1-invalid-"));

    try {
      const outputPath = join(tempDir, "invalid.svg");
      const result = await runDistCli([
        "compile",
        "tests/fixtures/invalid/invalid-kind.diagram.json",
        "-o",
        outputPath
      ]);

      expect(result.exitCode).not.toBe(0);
      expect(await pathExists(outputPath)).toBe(false);
    } finally {
      await rm(tempDir, { recursive: true, force: true });
    }
  });

  it("does not produce SVG output for cyclic input", async () => {
    const tempDir = await mkdtemp(join(tmpdir(), "hedgehog1-cycle-"));

    try {
      const outputPath = join(tempDir, "cycle.svg");
      const result = await runDistCli([
        "compile",
        "tests/fixtures/invalid/cycle.diagram.json",
        "-o",
        outputPath
      ]);

      expect(result.exitCode).not.toBe(0);
      expect(await pathExists(outputPath)).toBe(false);
    } finally {
      await rm(tempDir, { recursive: true, force: true });
    }
  });

  it("does not include environment, time, or randomness markers in SVG output", async () => {
    const svg = expectSvgResult(compileDiagramJsonToSvg(await readExampleInput()));

    expect(svg).not.toContain("Date");
    expect(svg).not.toContain("timestamp");
    expect(svg).not.toContain("/Users");
    expect(svg).not.toContain("node_modules");
    expect(svg).not.toContain("Math.random");
    expect(svg).not.toContain("random");
  });

  it("compiles equivalent object field order to identical SVG bytes", async () => {
    const input = await readExampleInput();
    const base = JSON.parse(input) as JsonDiagram;
    const reordered = {
      metadata: base.metadata,
      edges: base.edges.map((edge) => ({
        to: edge.to,
        evidenceRef: edge.evidenceRef,
        label: edge.label,
        from: edge.from,
        id: edge.id
      })),
      nodes: base.nodes.map((node) => ({
        role: node.role,
        label: node.label,
        id: node.id
      })),
      direction: base.direction,
      kind: base.kind,
      title: base.title,
      id: base.id,
      irVersion: base.irVersion
    };

    const firstSvg = expectSvgResult(compileDiagramJsonToSvg(input));
    const secondSvg = expectSvgResult(compileDiagramJsonToSvg(JSON.stringify(reordered)));

    expect(secondSvg).toBe(firstSvg);
  });

  it("confirms dist CLI compile output starts as an SVG", async () => {
    const tempDir = await mkdtemp(join(tmpdir(), "hedgehog1-svg-"));

    try {
      const outputPath = join(tempDir, "simple.svg");
      const result = await runDistCli([
        "compile",
        "examples/simple-dataflow.diagram.json",
        "-o",
        outputPath
      ]);

      expect(result.exitCode).toBe(0);
      await expect(stat(outputPath)).resolves.toBeDefined();
      expect((await readFile(outputPath, "utf8")).startsWith("<svg")).toBe(true);
    } finally {
      await rm(tempDir, { recursive: true, force: true });
    }
  });
});

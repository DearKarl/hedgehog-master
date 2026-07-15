import { mkdtemp, readFile, readdir, rm, stat } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";

import { beforeAll, describe, expect, it } from "vitest";

import { buildDist, runDistCli } from "./cli-helpers.js";

describe("dist CLI smoke tests", () => {
  beforeAll(() => {
    buildDist();
  });

  it("validates the example diagram through dist/cli.js", async () => {
    const result = await runDistCli(["validate", "examples/simple-dataflow.diagram.json"]);

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toBe("OK\n");
    expect(result.stderr).toBe("");
  });

  it("compiles the example diagram through dist/cli.js", async () => {
    const tempDir = await mkdtemp(join(tmpdir(), "hedgehog1-cli-"));

    try {
      const outputPath = join(tempDir, "simple.svg");
      const result = await runDistCli([
        "compile",
        "examples/simple-dataflow.diagram.json",
        "-o",
        outputPath
      ]);

      expect(result.exitCode).toBe(0);
      expect(result.stdout).toBe("OK\n");
      await expect(stat(outputPath)).resolves.toBeDefined();

      const svg = await readFile(outputPath, "utf8");
      expect(svg.startsWith("<svg")).toBe(true);
      expect(svg).toContain("<title");
      expect(svg).toContain("<desc");
    } finally {
      await rm(tempDir, { recursive: true, force: true });
    }
  });

  it("checks the example diagram without writing files", async () => {
    const tempDir = await mkdtemp(join(tmpdir(), "hedgehog1-cli-"));

    try {
      const before = await readdir(tempDir);
      const result = await runDistCli(["check", "examples/simple-dataflow.diagram.json"]);
      const after = await readdir(tempDir);

      expect(result.exitCode).toBe(0);
      expect(result.stdout).toBe("OK\n");
      expect(after).toEqual(before);
    } finally {
      await rm(tempDir, { recursive: true, force: true });
    }
  });
});

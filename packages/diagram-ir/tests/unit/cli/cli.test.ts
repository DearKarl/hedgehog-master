import { describe, expect, it } from "vitest";

import type { CliIo } from "../../../src/cli.js";
import { runCli } from "../../../src/cli.js";
import { ErrorCodes } from "../../../src/errors/codes.js";
import { readFixtureJson } from "../../helpers/fixtures.js";

type TestIo = CliIo & {
  stdoutLines: string[];
  stderrLines: string[];
  writes: Array<{ path: string; data: string }>;
};

async function fixtureString(path: string): Promise<string> {
  return JSON.stringify(await readFixtureJson(path));
}

function createIo(
  files: ReadonlyMap<string, string>,
  options: { failWrite?: boolean } = {}
): TestIo {
  const stdoutLines: string[] = [];
  const stderrLines: string[] = [];
  const writes: Array<{ path: string; data: string }> = [];

  return {
    stdoutLines,
    stderrLines,
    writes,
    readFile: async (path) => {
      const value = files.get(path);

      if (value === undefined) {
        throw new Error("missing file");
      }

      return value;
    },
    writeFile: async (path, data) => {
      if (options.failWrite === true) {
        throw new Error("write failed");
      }

      writes.push({ path, data });
    },
    stdout: (text) => {
      stdoutLines.push(text);
    },
    stderr: (text) => {
      stderrLines.push(text);
    }
  };
}

function expectStderrCode(io: TestIo, code: string): void {
  expect(io.stderrLines.join("")).toContain(`"code": "${code}"`);
}

describe("runCli", () => {
  it("validates a valid file", async () => {
    const io = createIo(
      new Map([["input.diagram.json", await fixtureString("valid/simple-dataflow.diagram.json")]])
    );

    await expect(runCli(["validate", "input.diagram.json"], io)).resolves.toBe(0);
    expect(io.stdoutLines).toEqual(["OK\n"]);
    expect(io.stderrLines).toEqual([]);
  });

  it("returns diagnostics for invalid validation input", async () => {
    const io = createIo(
      new Map([["input.diagram.json", await fixtureString("invalid/invalid-kind.diagram.json")]])
    );

    await expect(runCli(["validate", "input.diagram.json"], io)).resolves.toBe(1);
    expectStderrCode(io, ErrorCodes.IR_UNSUPPORTED_KIND);
  });

  it("compiles a valid file and writes SVG", async () => {
    const io = createIo(
      new Map([["input.diagram.json", await fixtureString("valid/simple-dataflow.diagram.json")]])
    );

    await expect(runCli(["compile", "input.diagram.json", "-o", "output.svg"], io)).resolves.toBe(
      0
    );
    expect(io.stdoutLines).toEqual(["OK\n"]);
    expect(io.writes).toHaveLength(1);
    expect(io.writes[0]).toMatchObject({ path: "output.svg" });
    expect(io.writes[0]?.data).toContain("<svg");
  });

  it("does not write SVG for invalid compile input", async () => {
    const io = createIo(
      new Map([["input.diagram.json", await fixtureString("invalid/invalid-role.diagram.json")]])
    );

    await expect(runCli(["compile", "input.diagram.json", "-o", "output.svg"], io)).resolves.toBe(
      1
    );
    expect(io.writes).toEqual([]);
    expectStderrCode(io, ErrorCodes.IR_INVALID_NODE_ROLE);
  });

  it("returns usage diagnostics when compile is missing -o", async () => {
    const io = createIo(new Map());

    await expect(runCli(["compile", "input.diagram.json"], io)).resolves.toBe(1);
    expectStderrCode(io, ErrorCodes.CLI_USAGE_ERROR);
  });

  it("checks a valid file", async () => {
    const io = createIo(
      new Map([["input.diagram.json", await fixtureString("valid/simple-dataflow.diagram.json")]])
    );

    await expect(runCli(["check", "input.diagram.json"], io)).resolves.toBe(0);
    expect(io.stdoutLines).toEqual(["OK\n"]);
    expect(io.writes).toEqual([]);
  });

  it("returns diagnostics for invalid check input", async () => {
    const io = createIo(
      new Map([["input.diagram.json", await fixtureString("invalid/unknown-field.diagram.json")]])
    );

    await expect(runCli(["check", "input.diagram.json"], io)).resolves.toBe(1);
    expectStderrCode(io, ErrorCodes.IR_UNKNOWN_FIELD);
  });

  it("returns usage diagnostics for unknown commands", async () => {
    const io = createIo(new Map());

    await expect(runCli(["render", "input.diagram.json"], io)).resolves.toBe(1);
    expectStderrCode(io, ErrorCodes.CLI_USAGE_ERROR);
  });

  it("returns read diagnostics when readFile fails", async () => {
    const io = createIo(new Map());

    await expect(runCli(["validate", "missing.diagram.json"], io)).resolves.toBe(1);
    expectStderrCode(io, ErrorCodes.CLI_READ_ERROR);
  });

  it("returns write diagnostics when writeFile fails", async () => {
    const io = createIo(
      new Map([["input.diagram.json", await fixtureString("valid/simple-dataflow.diagram.json")]]),
      { failWrite: true }
    );

    await expect(runCli(["compile", "input.diagram.json", "-o", "output.svg"], io)).resolves.toBe(
      1
    );
    expectStderrCode(io, ErrorCodes.CLI_WRITE_ERROR);
  });
});

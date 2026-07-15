#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

import {
  compileDiagramJsonToSvg,
  checkDeterministicDiagramJsonCompile
} from "./compiler/compile.js";
import { ErrorCodes } from "./errors/codes.js";
import { formatDiagnostics } from "./errors/format.js";
import type { Diagnostic } from "./ir/diagnostics.js";
import { parseDiagramJson } from "./ir/parse.js";
import { validateDiagramIr } from "./ir/validate.js";

export type CliIo = {
  readFile(path: string): Promise<string>;
  writeFile(path: string, data: string): Promise<void>;
  stdout(text: string): void;
  stderr(text: string): void;
};

export async function runCli(args: readonly string[], io: CliIo): Promise<number> {
  const [command] = args;

  if (command === "validate") {
    return runValidate(args, io);
  }

  if (command === "compile") {
    return runCompile(args, io);
  }

  if (command === "check") {
    return runCheck(args, io);
  }

  return fail(io, [usageDiagnostic(`Unknown command '${command ?? ""}'.`)]);
}

async function runValidate(args: readonly string[], io: CliIo): Promise<number> {
  if (args.length !== 2) {
    return fail(io, [usageDiagnostic("Usage: hedgehog1 validate input.diagram.json")]);
  }

  const input = await readInput(args[1]!, io);

  if (!input.ok) {
    return fail(io, input.diagnostics);
  }

  const parseResult = parseDiagramJson(input.value);

  if (!parseResult.ok) {
    return fail(io, parseResult.diagnostics);
  }

  const validationResult = validateDiagramIr(parseResult.value);

  if (!validationResult.ok) {
    return fail(io, validationResult.diagnostics);
  }

  io.stdout("OK\n");
  return 0;
}

async function runCompile(args: readonly string[], io: CliIo): Promise<number> {
  if (args.length !== 4 || args[2] !== "-o") {
    return fail(io, [usageDiagnostic("Usage: hedgehog1 compile input.diagram.json -o output.svg")]);
  }

  const input = await readInput(args[1]!, io);

  if (!input.ok) {
    return fail(io, input.diagnostics);
  }

  const compileResult = compileDiagramJsonToSvg(input.value);

  if (!compileResult.ok) {
    return fail(io, compileResult.diagnostics);
  }

  const writeResult = await writeOutput(args[3]!, compileResult.svg, io);

  if (!writeResult.ok) {
    return fail(io, writeResult.diagnostics);
  }

  io.stdout("OK\n");
  return 0;
}

async function runCheck(args: readonly string[], io: CliIo): Promise<number> {
  if (args.length !== 2) {
    return fail(io, [usageDiagnostic("Usage: hedgehog1 check input.diagram.json")]);
  }

  const input = await readInput(args[1]!, io);

  if (!input.ok) {
    return fail(io, input.diagnostics);
  }

  const checkResult = checkDeterministicDiagramJsonCompile(input.value);

  if (!checkResult.ok) {
    return fail(io, checkResult.diagnostics);
  }

  io.stdout("OK\n");
  return 0;
}

async function readInput(
  path: string,
  io: CliIo
): Promise<{ ok: true; value: string } | { ok: false; diagnostics: Diagnostic[] }> {
  try {
    return { ok: true, value: await io.readFile(path) };
  } catch {
    return {
      ok: false,
      diagnostics: [
        {
          code: ErrorCodes.CLI_READ_ERROR,
          severity: "error",
          path,
          message: `Failed to read input file '${path}'.`
        }
      ]
    };
  }
}

async function writeOutput(
  path: string,
  data: string,
  io: CliIo
): Promise<{ ok: true } | { ok: false; diagnostics: Diagnostic[] }> {
  try {
    await io.writeFile(path, data);
    return { ok: true };
  } catch {
    return {
      ok: false,
      diagnostics: [
        {
          code: ErrorCodes.CLI_WRITE_ERROR,
          severity: "error",
          path,
          message: `Failed to write output file '${path}'.`
        }
      ]
    };
  }
}

function fail(io: CliIo, diagnostics: readonly Diagnostic[]): number {
  io.stderr(formatDiagnostics(diagnostics));
  return 1;
}

function usageDiagnostic(message: string): Diagnostic {
  return {
    code: ErrorCodes.CLI_USAGE_ERROR,
    severity: "error",
    path: "",
    message,
    hint: "Use one of: hedgehog1 validate input.diagram.json, hedgehog1 compile input.diagram.json -o output.svg, hedgehog1 check input.diagram.json."
  };
}

const isDirectRun =
  process.argv[1] !== undefined && import.meta.url === pathToFileURL(process.argv[1]).href;

if (isDirectRun) {
  const io: CliIo = {
    readFile: (path) => readFile(path, "utf8"),
    writeFile: (path, data) => writeFile(path, data, "utf8"),
    stdout: (text) => {
      process.stdout.write(text);
    },
    stderr: (text) => {
      process.stderr.write(text);
    }
  };

  process.exitCode = await runCli(process.argv.slice(2), io);
}

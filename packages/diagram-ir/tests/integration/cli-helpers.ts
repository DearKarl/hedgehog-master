import { execFile, execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

export type CliRunResult = {
  exitCode: number;
  stdout: string;
  stderr: string;
};

export function buildDist(): void {
  execFileSync("pnpm", ["build"], {
    cwd: projectRoot,
    env: process.env,
    stdio: "pipe"
  });
}

export async function runDistCli(args: readonly string[]): Promise<CliRunResult> {
  return new Promise((resolveRun) => {
    execFile(
      process.execPath,
      ["dist/cli.js", ...args],
      {
        cwd: projectRoot,
        encoding: "utf8"
      },
      (error, stdout, stderr) => {
        if (error === null) {
          resolveRun({ exitCode: 0, stdout, stderr });
          return;
        }

        const execError = error as NodeJS.ErrnoException;
        resolveRun({
          exitCode: typeof execError.code === "number" ? execError.code : 1,
          stdout,
          stderr
        });
      }
    );
  });
}

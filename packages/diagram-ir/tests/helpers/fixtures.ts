import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const testRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");

export async function readFixtureJson(pathFromFixtures: string): Promise<unknown> {
  const fixturePath = resolve(testRoot, "fixtures", pathFromFixtures);
  return JSON.parse(await readFile(fixturePath, "utf8")) as unknown;
}

export async function readProjectJson(pathFromRoot: string): Promise<unknown> {
  const projectPath = resolve(testRoot, "..", pathFromRoot);
  return JSON.parse(await readFile(projectPath, "utf8")) as unknown;
}

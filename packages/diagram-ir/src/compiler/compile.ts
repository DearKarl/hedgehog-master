import { ErrorCodes } from "../errors/codes.js";
import type { Diagnostic } from "../ir/diagnostics.js";
import { canonicalizeDiagramIr } from "../ir/canonicalize.js";
import { parseDiagramJson } from "../ir/parse.js";
import type { DiagramIrV01a } from "../ir/types.js";
import { validateDiagramIr } from "../ir/validate.js";
import { layoutRankedDataflow } from "./ranked-layout.js";
import { buildSvgAst } from "./svg/build-svg-ast.js";
import { serializeSvg } from "./svg/serialize.js";

export type CompileDiagramJsonToSvgResult =
  | { ok: true; svg: string }
  | { ok: false; diagnostics: Diagnostic[] };

export function compileDiagramJsonToSvg(input: string): CompileDiagramJsonToSvgResult {
  const parseResult = parseDiagramJson(input);

  if (!parseResult.ok) {
    return parseResult;
  }

  const validationResult = validateDiagramIr(parseResult.value);

  if (!validationResult.ok) {
    return validationResult;
  }

  return {
    ok: true,
    svg: compileValidatedDiagramIrToSvg(validationResult.value)
  };
}

export function compileValidatedDiagramIrToSvg(document: DiagramIrV01a): string {
  return serializeSvg(buildSvgAst(layoutRankedDataflow(canonicalizeDiagramIr(document))));
}

export function checkDeterministicDiagramJsonCompile(input: string): CompileDiagramJsonToSvgResult {
  const first = compileDiagramJsonToSvg(input);

  if (!first.ok) {
    return first;
  }

  const second = compileDiagramJsonToSvg(input);

  if (!second.ok) {
    return second;
  }

  if (first.svg !== second.svg) {
    return {
      ok: false,
      diagnostics: [
        {
          code: ErrorCodes.COMPILE_NON_DETERMINISTIC,
          severity: "error",
          path: "",
          message: "Compiling the same input twice produced different SVG bytes.",
          hint: "Remove randomness, time, environment, or unordered iteration from the compiler path."
        }
      ]
    };
  }

  return first;
}

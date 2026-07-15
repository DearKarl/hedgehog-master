import { ErrorCodes } from "../errors/codes.js";
import type { Diagnostic } from "./diagnostics.js";

export type ParseDiagramJsonResult =
  | { ok: true; value: unknown }
  | { ok: false; diagnostics: Diagnostic[] };

export function parseDiagramJson(input: string): ParseDiagramJsonResult {
  try {
    return { ok: true, value: JSON.parse(input) as unknown };
  } catch (error) {
    const reason = error instanceof SyntaxError ? error.message : "Unknown JSON parse error";

    return {
      ok: false,
      diagnostics: [
        {
          code: ErrorCodes.IR_PARSE_ERROR,
          severity: "error",
          path: "",
          message: `Invalid JSON: ${reason}`,
          hint: "Provide strict JSON without comments, trailing commas, or JSON5 syntax."
        }
      ]
    };
  }
}

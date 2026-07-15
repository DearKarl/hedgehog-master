import type { DiagnosticCode } from "../errors/codes.js";

export type Diagnostic = {
  code: DiagnosticCode;
  severity: "error";
  path: string;
  message: string;
  hint?: string;
};

export function sortDiagnostics(diagnostics: readonly Diagnostic[]): Diagnostic[] {
  return [...diagnostics].sort((left, right) => {
    const pathOrder = compareLexicographic(left.path, right.path);

    if (pathOrder !== 0) {
      return pathOrder;
    }

    const codeOrder = compareLexicographic(left.code, right.code);

    if (codeOrder !== 0) {
      return codeOrder;
    }

    return compareLexicographic(left.message, right.message);
  });
}

function compareLexicographic(left: string, right: string): number {
  if (left < right) {
    return -1;
  }

  if (left > right) {
    return 1;
  }

  return 0;
}

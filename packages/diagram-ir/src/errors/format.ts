import type { Diagnostic } from "../ir/diagnostics.js";

export function formatDiagnostics(diagnostics: readonly Diagnostic[]): string {
  return `${JSON.stringify(diagnostics.map(formatDiagnostic), null, 2)}\n`;
}

function formatDiagnostic(diagnostic: Diagnostic): Record<string, string | null> {
  return {
    code: diagnostic.code,
    severity: diagnostic.severity,
    path: diagnostic.path,
    message: diagnostic.message,
    hint: diagnostic.hint ?? null
  };
}

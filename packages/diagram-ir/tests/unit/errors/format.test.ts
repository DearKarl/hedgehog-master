import { describe, expect, it } from "vitest";

import { ErrorCodes } from "../../../src/errors/codes.js";
import { formatDiagnostics } from "../../../src/errors/format.js";
import type { Diagnostic } from "../../../src/ir/diagnostics.js";

describe("formatDiagnostics", () => {
  it("produces stable JSON output with a final newline", () => {
    const diagnostics: Diagnostic[] = [
      {
        code: ErrorCodes.CLI_USAGE_ERROR,
        severity: "error",
        path: "",
        message: "Usage error.",
        hint: "Use a supported command."
      }
    ];

    expect(formatDiagnostics(diagnostics)).toBe(`[
  {
    "code": "CLI_USAGE_ERROR",
    "severity": "error",
    "path": "",
    "message": "Usage error.",
    "hint": "Use a supported command."
  }
]
`);
  });

  it("includes code, path, message, and hint when present", () => {
    const formatted = formatDiagnostics([
      {
        code: ErrorCodes.CLI_READ_ERROR,
        severity: "error",
        path: "input.diagram.json",
        message: "Read failed.",
        hint: "Check the path."
      }
    ]);

    expect(formatted).toContain('"code": "CLI_READ_ERROR"');
    expect(formatted).toContain('"path": "input.diagram.json"');
    expect(formatted).toContain('"message": "Read failed."');
    expect(formatted).toContain('"hint": "Check the path."');
    expect(formatted.endsWith("\n")).toBe(true);
  });
});

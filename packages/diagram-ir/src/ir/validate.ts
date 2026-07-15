import { Ajv } from "ajv";
import type { ErrorObject } from "ajv";

import { ErrorCodes } from "../errors/codes.js";
import type { DiagnosticCode } from "../errors/codes.js";
import type { Diagnostic } from "./diagnostics.js";
import { sortDiagnostics } from "./diagnostics.js";
import { DiagramIrV01aSchema } from "./schema.js";
import type { DiagramIrV01a } from "./types.js";

export type ValidationResult<T> = { ok: true; value: T } | { ok: false; diagnostics: Diagnostic[] };

const ajv = new Ajv({ allErrors: true, strict: true });
const validateSchema = ajv.compile<DiagramIrV01a>(DiagramIrV01aSchema);

export function schemaValidateDiagramIr(input: unknown): ValidationResult<DiagramIrV01a> {
  if (validateSchema(input)) {
    return { ok: true, value: input };
  }

  return {
    ok: false,
    diagnostics: sortDiagnostics(
      dedupeDiagnostics((validateSchema.errors ?? []).flatMap(mapAjvError))
    )
  };
}

export function semanticValidateDiagramIr(
  document: DiagramIrV01a
): ValidationResult<DiagramIrV01a> {
  const diagnostics: Diagnostic[] = [];
  const nodeIds = new Set<string>();
  const edgeIds = new Set<string>();

  document.nodes.forEach((node, index) => {
    if (nodeIds.has(node.id)) {
      diagnostics.push({
        code: ErrorCodes.IR_DUPLICATE_NODE_ID,
        severity: "error",
        path: `/nodes/${index}/id`,
        message: `Duplicate node id '${node.id}'.`,
        hint: "Node ids must be unique within the diagram."
      });
      return;
    }

    nodeIds.add(node.id);
  });

  document.edges.forEach((edge, index) => {
    if (edgeIds.has(edge.id)) {
      diagnostics.push({
        code: ErrorCodes.IR_DUPLICATE_EDGE_ID,
        severity: "error",
        path: `/edges/${index}/id`,
        message: `Duplicate edge id '${edge.id}'.`,
        hint: "Edge ids must be unique within the diagram."
      });
    } else {
      edgeIds.add(edge.id);
    }

    if (!nodeIds.has(edge.from)) {
      diagnostics.push({
        code: ErrorCodes.IR_UNKNOWN_EDGE_FROM,
        severity: "error",
        path: `/edges/${index}/from`,
        message: `Edge '${edge.id}' references unknown source node '${edge.from}'.`
      });
    }

    if (!nodeIds.has(edge.to)) {
      diagnostics.push({
        code: ErrorCodes.IR_UNKNOWN_EDGE_TO,
        severity: "error",
        path: `/edges/${index}/to`,
        message: `Edge '${edge.id}' references unknown target node '${edge.to}'.`
      });
    }
  });

  if (diagnostics.length === 0 && hasCycle(document)) {
    diagnostics.push({
      code: ErrorCodes.IR_CYCLE_DETECTED,
      severity: "error",
      path: "/edges",
      message: "Diagram edges contain a cycle.",
      hint: "v0.1a dataflow diagrams must be DAGs."
    });
  }

  if (diagnostics.length > 0) {
    return { ok: false, diagnostics: sortDiagnostics(diagnostics) };
  }

  return { ok: true, value: document };
}

export function validateDiagramIr(input: unknown): ValidationResult<DiagramIrV01a> {
  const schemaResult = schemaValidateDiagramIr(input);

  if (!schemaResult.ok) {
    return schemaResult;
  }

  return semanticValidateDiagramIr(schemaResult.value);
}

function mapAjvError(error: ErrorObject): Diagnostic[] {
  if (error.keyword === "const" && error.instancePath.endsWith("/role")) {
    return [];
  }

  if (error.keyword === "additionalProperties") {
    const additionalProperty = getStringParam(error, "additionalProperty");
    const path = additionalProperty
      ? appendJsonPointer(error.instancePath, additionalProperty)
      : error.instancePath;

    return [
      makeSchemaDiagnostic(
        ErrorCodes.IR_UNKNOWN_FIELD,
        path,
        `Unknown field '${additionalProperty ?? "<unknown>"}'.`,
        "Remove fields that are not part of Diagram IR v0.1a."
      )
    ];
  }

  if (error.keyword === "required") {
    const missingProperty = getStringParam(error, "missingProperty");
    const path = missingProperty
      ? appendJsonPointer(error.instancePath, missingProperty)
      : error.instancePath;

    return [
      makeSchemaDiagnostic(
        ErrorCodes.IR_MISSING_REQUIRED_FIELD,
        path,
        `Missing required field '${missingProperty ?? "<unknown>"}'.`
      )
    ];
  }

  if (error.keyword === "anyOf" && error.instancePath.endsWith("/role")) {
    return [
      makeSchemaDiagnostic(
        ErrorCodes.IR_INVALID_NODE_ROLE,
        error.instancePath,
        "Invalid node role.",
        "Use one of: source, transform, model, metric, output."
      )
    ];
  }

  if (error.keyword === "pattern" && error.instancePath.endsWith("/id")) {
    return [
      makeSchemaDiagnostic(
        ErrorCodes.IR_INVALID_ID,
        error.instancePath,
        "Invalid id.",
        "IDs must match ^[A-Za-z][A-Za-z0-9_-]*$."
      )
    ];
  }

  if (error.keyword === "const" && error.instancePath === "/kind") {
    return [
      makeSchemaDiagnostic(
        ErrorCodes.IR_UNSUPPORTED_KIND,
        error.instancePath,
        "Unsupported diagram kind.",
        "v0.1a only supports kind: dataflow."
      )
    ];
  }

  if (error.keyword === "const" && error.instancePath === "/direction") {
    return [
      makeSchemaDiagnostic(
        ErrorCodes.IR_UNSUPPORTED_DIRECTION,
        error.instancePath,
        "Unsupported diagram direction.",
        "v0.1a only supports direction: left-to-right."
      )
    ];
  }

  return [
    makeSchemaDiagnostic(
      ErrorCodes.IR_SCHEMA_ERROR,
      error.instancePath,
      "Schema validation failed."
    )
  ];
}

function makeSchemaDiagnostic(
  code: DiagnosticCode,
  path: string,
  message: string,
  hint?: string
): Diagnostic {
  return {
    code,
    severity: "error",
    path,
    message,
    ...(hint === undefined ? {} : { hint })
  };
}

function getStringParam(error: ErrorObject, key: string): string | undefined {
  const value = (error.params as Record<string, unknown>)[key];
  return typeof value === "string" ? value : undefined;
}

function appendJsonPointer(basePath: string, segment: string): string {
  return `${basePath}/${escapeJsonPointerSegment(segment)}`;
}

function escapeJsonPointerSegment(segment: string): string {
  return segment.replaceAll("~", "~0").replaceAll("/", "~1");
}

function dedupeDiagnostics(diagnostics: readonly Diagnostic[]): Diagnostic[] {
  const seen = new Set<string>();
  const deduped: Diagnostic[] = [];

  for (const diagnostic of diagnostics) {
    const key = `${diagnostic.path}\u0000${diagnostic.code}\u0000${diagnostic.message}`;

    if (!seen.has(key)) {
      seen.add(key);
      deduped.push(diagnostic);
    }
  }

  return deduped;
}

function hasCycle(document: DiagramIrV01a): boolean {
  const adjacency = new Map<string, string[]>();
  const indegree = new Map<string, number>();

  for (const node of document.nodes) {
    adjacency.set(node.id, []);
    indegree.set(node.id, 0);
  }

  for (const edge of document.edges) {
    adjacency.get(edge.from)!.push(edge.to);
    indegree.set(edge.to, indegree.get(edge.to)! + 1);
  }

  const queue = document.nodes.filter((node) => indegree.get(node.id) === 0).map((node) => node.id);
  let visitedCount = 0;

  for (let index = 0; index < queue.length; index += 1) {
    const nodeId = queue[index]!;
    visitedCount += 1;

    for (const nextNodeId of adjacency.get(nodeId)!) {
      const nextIndegree = indegree.get(nextNodeId)! - 1;
      indegree.set(nextNodeId, nextIndegree);

      if (nextIndegree === 0) {
        queue.push(nextNodeId);
      }
    }
  }

  return visitedCount !== document.nodes.length;
}

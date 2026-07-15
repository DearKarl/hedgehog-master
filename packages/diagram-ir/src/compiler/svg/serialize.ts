import type { SvgAttribute, SvgElement, SvgNode } from "./ast.js";
import { escapeAttribute, escapeText } from "./escape.js";

const INDENT = "  ";

export function serializeSvg(root: SvgElement): string {
  return `${serializeElement(root, 0)}\n`;
}

function serializeNode(node: SvgNode, depth: number): string {
  if (node.kind === "text") {
    return `${INDENT.repeat(depth)}${escapeText(node.value)}`;
  }

  return serializeElement(node, depth);
}

function serializeElement(element: SvgElement, depth: number): string {
  const indent = INDENT.repeat(depth);
  const attributes = serializeAttributes(element.attributes);

  if (element.children.length === 0) {
    return `${indent}<${element.name}${attributes} />`;
  }

  if (element.children.length === 1 && element.children[0]?.kind === "text") {
    return `${indent}<${element.name}${attributes}>${escapeText(element.children[0].value)}</${element.name}>`;
  }

  const childLines = element.children.map((child) => serializeNode(child, depth + 1));
  return [
    `${indent}<${element.name}${attributes}>`,
    ...childLines,
    `${indent}</${element.name}>`
  ].join("\n");
}

function serializeAttributes(attributes: readonly SvgAttribute[]): string {
  if (attributes.length === 0) {
    return "";
  }

  return ` ${attributes
    .map((attribute) => `${attribute.name}="${escapeAttribute(attribute.value)}"`)
    .join(" ")}`;
}

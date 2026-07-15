import { describe, expect, it } from "vitest";

import type { SvgElement } from "../../../../src/compiler/svg/ast.js";
import { serializeSvg } from "../../../../src/compiler/svg/serialize.js";

describe("serializeSvg", () => {
  it("preserves attribute order", () => {
    const root: SvgElement = {
      kind: "element",
      name: "svg",
      attributes: [
        { name: "b", value: "2" },
        { name: "a", value: "1" }
      ],
      children: []
    };

    expect(serializeSvg(root)).toBe('<svg b="2" a="1" />\n');
  });

  it("escapes text nodes", () => {
    const root: SvgElement = {
      kind: "element",
      name: "svg",
      attributes: [],
      children: [{ kind: "text", value: "A & B < C > D" }]
    };

    expect(serializeSvg(root)).toBe("<svg>A &amp; B &lt; C &gt; D</svg>\n");
  });

  it("escapes attribute values", () => {
    const root: SvgElement = {
      kind: "element",
      name: "svg",
      attributes: [{ name: "aria-label", value: 'A & B < C > D "quoted"' }],
      children: []
    };

    expect(serializeSvg(root)).toBe(
      '<svg aria-label="A &amp; B &lt; C &gt; D &quot;quoted&quot;" />\n'
    );
  });

  it("ends with a final newline", () => {
    expect(serializeSvg({ kind: "element", name: "svg", attributes: [], children: [] })).toMatch(
      /\n$/u
    );
  });

  it("formats empty elements as stable self-closing tags", () => {
    expect(serializeSvg({ kind: "element", name: "path", attributes: [], children: [] })).toBe(
      "<path />\n"
    );
  });

  it("serializes the same AST identically", () => {
    const root: SvgElement = {
      kind: "element",
      name: "svg",
      attributes: [{ name: "width", value: "1600" }],
      children: [
        {
          kind: "element",
          name: "title",
          attributes: [],
          children: [{ kind: "text", value: "Stable" }]
        }
      ]
    };

    expect(serializeSvg(root)).toBe(serializeSvg(root));
  });
});

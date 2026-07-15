import { describe, expect, it } from "vitest";

import { escapeAttribute, escapeText } from "../../../../src/compiler/svg/escape.js";

describe("SVG escaping", () => {
  it("escapes text content", () => {
    expect(escapeText('A & B < C > D "quoted"')).toBe('A &amp; B &lt; C &gt; D "quoted"');
  });

  it("escapes attribute values", () => {
    expect(escapeAttribute('A & B < C > D "quoted"')).toBe(
      "A &amp; B &lt; C &gt; D &quot;quoted&quot;"
    );
  });
});

import { describe, expect, it } from "vitest";

import { formatNumber } from "../../../../src/compiler/svg/numeric.js";

describe("formatNumber", () => {
  it("formats integers without decimals", () => {
    expect(formatNumber(1600)).toBe("1600");
  });

  it("keeps at most three decimal places", () => {
    expect(formatNumber(12.34567)).toBe("12.346");
  });

  it("removes insignificant trailing zeros", () => {
    expect(formatNumber(12.3)).toBe("12.3");
    expect(formatNumber(12.34)).toBe("12.34");
    expect(formatNumber(12.0)).toBe("12");
  });

  it("formats negative zero as zero", () => {
    expect(formatNumber(-0)).toBe("0");
    expect(formatNumber(-0.0001)).toBe("0");
  });

  it("throws for non-finite values", () => {
    expect(() => formatNumber(Number.NaN)).toThrow("Cannot format non-finite SVG number");
    expect(() => formatNumber(Number.POSITIVE_INFINITY)).toThrow(
      "Cannot format non-finite SVG number"
    );
    expect(() => formatNumber(Number.NEGATIVE_INFINITY)).toThrow(
      "Cannot format non-finite SVG number"
    );
  });
});

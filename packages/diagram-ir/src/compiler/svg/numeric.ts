export function formatNumber(value: number): string {
  if (!Number.isFinite(value)) {
    throw new Error(`Cannot format non-finite SVG number: ${String(value)}.`);
  }

  const fixed = value.toFixed(3);

  if (/^-?0(?:\.0+)?$/u.test(fixed)) {
    return "0";
  }

  return fixed.replace(/\.?0+$/u, "");
}

export function pct(x?: number, digits = 0): string {
  if (x === undefined || x === null || Number.isNaN(x)) return "--";
  return `${(x * 100).toFixed(digits)}%`;
}

export function num(x?: number, digits = 2): string {
  if (x === undefined || x === null || Number.isNaN(x)) return "--";
  return x.toFixed(digits);
}

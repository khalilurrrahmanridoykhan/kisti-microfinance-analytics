/** Number formatting shared by every page. Amounts are taka unless stated otherwise. */

const grouped = new Intl.NumberFormat("en-US");

export function formatNumber(value: number, digits = 0): string {
  return value.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function formatInt(value: number): string {
  return grouped.format(Math.round(value));
}

export function formatPercent(value: number, digits = 1): string {
  return `${formatNumber(value, digits)}%`;
}

export function formatSignedPercentPoints(value: number, digits = 1): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, digits)} pp`;
}

/** A compact taka amount: million and above become "51.9M taka", "1.75B taka". */
export function formatCompactTaka(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1e9) return `${formatNumber(value / 1e9, 2)}B taka`;
  if (abs >= 1e6) return `${formatNumber(value / 1e6, 1)}M taka`;
  if (abs >= 1e3) return `${formatNumber(value / 1e3, 1)}K taka`;
  return `${formatInt(value)} taka`;
}

export function formatTaka(value: number): string {
  return `${formatInt(value)} taka`;
}

export function formatCompactCount(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1e6) return `${formatNumber(value / 1e6, 1)}M`;
  if (abs >= 1e3) return `${formatNumber(value / 1e3, 1)}K`;
  return formatInt(value);
}

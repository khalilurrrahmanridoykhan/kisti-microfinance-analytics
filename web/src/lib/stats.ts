/** Small client-side statistics used to derive a chart directly from mfis.json (median and
 * interquartile range by size band) where sector.json only carries the single figures already
 * quoted in RESULTS.md. Linear interpolation, matching pandas' default `quantile` method. */

export function quantile(sorted: number[], p: number): number {
  if (sorted.length === 0) return NaN;
  if (sorted.length === 1) return sorted[0];
  const position = p * (sorted.length - 1);
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return sorted[lower];
  const weight = position - lower;
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

export function median(values: number[]): number {
  return quantile([...values].sort((a, b) => a - b), 0.5);
}

export interface Range {
  n: number;
  p25: number;
  median: number;
  p75: number;
}

/** n, p25, median and p75 of the finite, non-null values in `values`. */
export function summariseRange(values: (number | null | undefined)[]): Range {
  const finite = values.filter((v): v is number => v !== null && v !== undefined && Number.isFinite(v));
  const sorted = [...finite].sort((a, b) => a - b);
  return { n: sorted.length, p25: quantile(sorted, 0.25), median: quantile(sorted, 0.5), p75: quantile(sorted, 0.75) };
}

export function groupBy<T, K extends string>(rows: T[], key: (row: T) => K): Map<K, T[]> {
  const groups = new Map<K, T[]>();
  for (const row of rows) {
    const k = key(row);
    const existing = groups.get(k);
    if (existing) existing.push(row);
    else groups.set(k, [row]);
  }
  return groups;
}

import { summariseRange, type Range } from "./stats";
import type { MfiRecord, SizeBandDef } from "./types";

export function bandOrder(sizeBands: SizeBandDef[]): string[] {
  return sizeBands.map((b) => b.label);
}

export interface BandRange extends Range {
  label: string;
}

/** Median and interquartile range of one MFI field, grouped by size band, in the band order
 * from methods.json — computed here (not in the Python pipeline) because it needs the raw
 * per-MFI values, which mfis.json already carries. */
export function rangeByBand(mfis: MfiRecord[], order: string[], value: (mfi: MfiRecord) => number | null): BandRange[] {
  return order
    .map((label) => {
      const inBand = mfis.filter((m) => m.size_band === label);
      const range = summariseRange(inBand.map(value));
      return { label, ...range };
    })
    .filter((row) => row.n > 0);
}

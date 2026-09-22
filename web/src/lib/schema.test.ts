import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { checkRecord, checkRecords, DISTRICT_RECORD, DIVISION_RECORD, META, MFI_RECORD } from "./schema";

// The other half of the data contract: tests/test_webdata.py checks these same JSON files
// against src/kisti/webdata/schema.py. If the two schema files drift apart, only one side —
// whichever is stricter — will catch a real mismatch, so keep their field lists in sync by hand.
// Resolved from the test runner's working directory (the web/ package root), not import.meta.url,
// since Vitest's module transform does not always give that a plain file: URL.
const DATA_DIR = path.resolve(process.cwd(), "public/data");

function load<T>(name: string): T {
  return JSON.parse(readFileSync(`${DATA_DIR}/${name}.json`, "utf-8")) as T;
}

describe("checkRecord / checkRecords", () => {
  const spec = { a: "int", b: "number|null" } as const;

  it("passes a matching record", () => {
    expect(checkRecord({ a: 1, b: 2.5 }, spec, "x")).toEqual([]);
    expect(checkRecord({ a: 1, b: null }, spec, "x")).toEqual([]);
  });

  it("reports missing and unexpected fields", () => {
    expect(checkRecord({ a: 1 }, spec, "x")).toEqual(['x: missing fields ["b"]']);
    expect(checkRecord({ a: 1, b: 2, c: 3 }, spec, "x")).toEqual(['x: unexpected fields ["c"]']);
  });

  it("rejects a non-integer for an int field and NaN for a number field", () => {
    expect(checkRecord({ a: 1.5, b: 1 }, spec, "x")[0]).toMatch(/a: expected int/);
    expect(checkRecord({ a: 1, b: NaN }, spec, "x")[0]).toMatch(/b: expected number\|null/);
  });

  it("indexes each row in checkRecords", () => {
    expect(checkRecords([{ a: 1, b: 1 }, {}], spec, "rows")).toEqual(['rows[1]: missing fields ["a","b"]']);
  });
});

describe("the committed dashboard data matches this schema", () => {
  it("meta.json", () => {
    expect(checkRecord(load("meta"), META, "meta")).toEqual([]);
  });

  it("mfis.json — every one of the 644 active MFIs", () => {
    const mfis = load<Record<string, unknown>[]>("mfis");
    expect(mfis.length).toBe(644);
    expect(checkRecords(mfis, MFI_RECORD, "mfis")).toEqual([]);
  });

  it("districts.json — all 64 districts", () => {
    const districts = load<Record<string, unknown>[]>("districts");
    expect(districts.length).toBe(64);
    expect(checkRecords(districts, DISTRICT_RECORD, "districts")).toEqual([]);
  });

  it("divisions.json — all 8 divisions", () => {
    const divisions = load<Record<string, unknown>[]>("divisions");
    expect(divisions.length).toBe(8);
    expect(checkRecords(divisions, DIVISION_RECORD, "divisions")).toEqual([]);
  });

  it("manifest.json lists exactly the files that exist", () => {
    const manifest = load<string[]>("manifest");
    expect(manifest.sort()).toEqual(["districts.json", "divisions.json", "meta.json", "methods.json", "mfis.json", "sector.json"]);
  });

  it("meta.json agrees with mfis.json and districts.json on the counts", () => {
    const meta = load<{ mfis_active: number; mfis_in_basic: number }>("meta");
    const mfis = load<unknown[]>("mfis");
    expect(meta.mfis_active).toBe(mfis.length);
    expect(meta.mfis_in_basic).toBe(693);
  });
});

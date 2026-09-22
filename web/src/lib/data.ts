import { checkRecord, checkRecords, DISTRICT_RECORD, META, MFI_RECORD } from "./schema";
import type { DistrictRecord, DivisionRecord, Meta, MethodsData, MfiRecord, SectorData } from "./types";

export interface AppData {
  meta: Meta;
  sector: SectorData;
  mfis: MfiRecord[];
  districts: DistrictRecord[];
  divisions: DivisionRecord[];
  methods: MethodsData;
}

function dataUrl(name: string): string {
  return `${import.meta.env.BASE_URL}data/${name}.json`;
}

async function loadJson<T>(name: string): Promise<T> {
  const response = await fetch(dataUrl(name));
  if (!response.ok) {
    throw new Error(`Could not load ${name}.json (HTTP ${response.status}). Try reloading the page.`);
  }
  return (await response.json()) as T;
}

/** Loads every dataset and checks the two that carry the dashboard's numeric contract. A
 * schema mismatch is a build-time bug in the export, not something a viewer can fix, so it
 * throws with the exact fields at fault rather than rendering with silently wrong data. */
export async function loadAppData(): Promise<AppData> {
  const [meta, sector, mfis, districts, divisions, methods] = await Promise.all([
    loadJson<Meta>("meta"),
    loadJson<SectorData>("sector"),
    loadJson<MfiRecord[]>("mfis"),
    loadJson<DistrictRecord[]>("districts"),
    loadJson<DivisionRecord[]>("divisions"),
    loadJson<MethodsData>("methods"),
  ]);

  const errors = [
    ...checkRecord(meta as unknown as Record<string, unknown>, META, "meta"),
    ...checkRecords(mfis as unknown as Record<string, unknown>[], MFI_RECORD, "mfis"),
    ...checkRecords(districts as unknown as Record<string, unknown>[], DISTRICT_RECORD, "districts"),
  ];
  if (errors.length > 0) {
    throw new Error(`Dashboard data does not match its schema:\n${errors.slice(0, 10).join("\n")}`);
  }
  if (mfis.length !== meta.mfis_active) {
    throw new Error(`meta.json says ${meta.mfis_active} active MFIs but mfis.json has ${mfis.length}.`);
  }

  return { meta, sector, mfis, districts, divisions, methods };
}

import { DistrictMap } from "../components/DistrictMap";
import { SectionCard } from "../components/SectionCard";
import { DataTable, type Column } from "../components/DataTable";
import type { AppData } from "../lib/data";
import { formatCompactTaka, formatInt } from "../lib/format";
import type { DistrictRecord, DivisionRecord } from "../lib/types";

const DISTRICT_COLUMNS: Column<DistrictRecord>[] = [
  { key: "district", header: "District", render: (r) => r.district, sortValue: (r) => r.district },
  { key: "division", header: "Division", render: (r) => r.division, sortValue: (r) => r.division },
  { key: "population", header: "Population", render: (r) => formatInt(r.population), align: "right", sortValue: (r) => r.population },
  { key: "borrowers", header: "MFI borrowers", render: (r) => formatInt(r.borrowers), align: "right", sortValue: (r) => r.borrowers },
  {
    key: "per1000",
    header: "Borrowers / 1,000",
    render: (r) => r.borrowers_per_1000.toFixed(0),
    align: "right",
    sortValue: (r) => r.borrowers_per_1000,
  },
  {
    key: "loans_per_person",
    header: "Loans per person",
    render: (r) => formatCompactTaka(r.loan_outstanding_per_person_bdt),
    align: "right",
    sortValue: (r) => r.loan_outstanding_per_person_bdt,
  },
  {
    key: "account",
    header: "Financial account %",
    render: (r) => `${r.financial_account_pct.toFixed(0)}%`,
    align: "right",
    sortValue: (r) => r.financial_account_pct,
  },
];

const DIVISION_COLUMNS: Column<DivisionRecord>[] = [
  { key: "division", header: "Division", render: (r) => r.division, sortValue: (r) => r.division },
  { key: "population", header: "Population", render: (r) => formatInt(r.population), align: "right", sortValue: (r) => r.population },
  { key: "borrowers", header: "MFI borrowers", render: (r) => formatInt(r.borrowers), align: "right", sortValue: (r) => r.borrowers },
  {
    key: "per1000",
    header: "Borrowers / 1,000",
    render: (r) => r.borrowers_per_1000.toFixed(0),
    align: "right",
    sortValue: (r) => r.borrowers_per_1000,
  },
];

export function Districts({ data }: { data: AppData }) {
  const { districts, divisions, sector } = data;

  return (
    <div>
      <SectionCard
        index={9}
        title="Geography"
        lead={
          <>
          MFI coverage by district, against Census 2022 population. Counts borrowers of MFIs, not distinct
          people; Grameen Bank, government schemes and banks are excluded. National average:{" "}
          {sector.geo_summary.national_borrowers_per_1000.toFixed(0)} per 1,000.
          </>
        }
      >
        <DistrictMap districts={districts} />
      </SectionCard>

      <SectionCard title="By division">
        <DataTable
          columns={DIVISION_COLUMNS}
          rows={divisions}
          getRowKey={(r) => r.division}
          caption="MFI coverage by division"
          initialSort={{ key: "per1000", direction: "desc" }}
          pageSize={10}
        />
      </SectionCard>

      <SectionCard title="All districts">
        <DataTable
          columns={DISTRICT_COLUMNS}
          rows={districts}
          getRowKey={(r) => r.district}
          caption="MFI coverage by district"
          searchPlaceholder="Search districts…"
          searchPredicate={(row, query) => row.district.toLowerCase().includes(query.toLowerCase())}
          initialSort={{ key: "per1000", direction: "desc" }}
          pageSize={20}
        />
      </SectionCard>
    </div>
  );
}

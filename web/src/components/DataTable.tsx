import { useMemo, useState } from "react";

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => React.ReactNode;
  sortValue?: (row: T) => number | string;
  align?: "left" | "right";
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  getRowKey: (row: T) => string | number;
  caption: string;
  searchPlaceholder?: string;
  searchPredicate?: (row: T, query: string) => boolean;
  initialSort?: { key: string; direction: "asc" | "desc" };
  pageSize?: number;
  extraControls?: React.ReactNode;
}

/** A sortable, searchable, paginated table. Column headers are buttons (keyboard-operable,
 * `aria-sort` announced), and this doubles as the plain "table view" of any chart it sits next
 * to, so nothing on the page depends on colour alone. */
export function DataTable<T>({
  columns,
  rows,
  getRowKey,
  caption,
  searchPlaceholder,
  searchPredicate,
  initialSort,
  pageSize = 25,
  extraControls,
}: DataTableProps<T>) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState(initialSort ?? { key: columns[0].key, direction: "desc" as const });
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    if (!query || !searchPredicate) return rows;
    return rows.filter((row) => searchPredicate(row, query));
  }, [rows, query, searchPredicate]);

  const sorted = useMemo(() => {
    const column = columns.find((c) => c.key === sort.key);
    if (!column?.sortValue) return filtered;
    const copy = [...filtered];
    copy.sort((a, b) => {
      const av = column.sortValue!(a);
      const bv = column.sortValue!(b);
      const cmp = typeof av === "number" && typeof bv === "number" ? av - bv : String(av).localeCompare(String(bv));
      return sort.direction === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [filtered, sort, columns]);

  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize));
  const clampedPage = Math.min(page, pageCount - 1);
  const visible = sorted.slice(clampedPage * pageSize, clampedPage * pageSize + pageSize);

  function toggleSort(key: string) {
    setPage(0);
    setSort((current) =>
      current.key === key ? { key, direction: current.direction === "asc" ? "desc" : "asc" } : { key, direction: "desc" },
    );
  }

  return (
    <div>
      <div className="control-row">
        {searchPredicate && (
          <input
            type="search"
            aria-label={searchPlaceholder ?? "Search"}
            placeholder={searchPlaceholder}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(0);
            }}
          />
        )}
        {extraControls}
        <span style={{ color: "var(--text-muted)", fontSize: 12 }}>
          {sorted.length.toLocaleString()} of {rows.length.toLocaleString()} rows
        </span>
      </div>
      <div className="table-scroll">
        <table>
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              {columns.map((column) => {
                const isSorted = sort.key === column.key;
                return (
                  <th
                    key={column.key}
                    scope="col"
                    aria-sort={isSorted ? (sort.direction === "asc" ? "ascending" : "descending") : "none"}
                    style={{ textAlign: column.align ?? "left" }}
                  >
                    {column.sortValue ? (
                      <button
                        type="button"
                        onClick={() => toggleSort(column.key)}
                        style={{ background: "none", border: "none", font: "inherit", color: "inherit", cursor: "pointer", padding: 0 }}
                      >
                        {column.header}
                        {isSorted ? (sort.direction === "asc" ? " ↑" : " ↓") : ""}
                      </button>
                    ) : (
                      column.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {visible.map((row) => (
              <tr key={getRowKey(row)}>
                {columns.map((column) => (
                  <td key={column.key} style={{ textAlign: column.align ?? "left" }}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td colSpan={columns.length} style={{ color: "var(--text-muted)" }}>
                  No rows match.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {pageCount > 1 && (
        <div className="control-row" style={{ marginTop: 8 }}>
          <button type="button" onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={clampedPage === 0}>
            Previous
          </button>
          <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
            Page {clampedPage + 1} of {pageCount}
          </span>
          <button type="button" onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))} disabled={clampedPage >= pageCount - 1}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}

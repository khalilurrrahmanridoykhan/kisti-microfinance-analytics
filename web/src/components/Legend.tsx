export interface LegendEntry {
  label: string;
  color: string;
}

/** Always shown for 2+ series — the dependable identity channel, per the dataviz skill. */
export function Legend({ entries }: { entries: LegendEntry[] }) {
  if (entries.length < 2) return null;
  return (
    <div className="legend" role="list" aria-label="Legend">
      {entries.map((entry) => (
        <span className="legend-item" role="listitem" key={entry.label}>
          <span className="legend-swatch" style={{ background: entry.color }} aria-hidden="true" />
          {entry.label}
        </span>
      ))}
    </div>
  );
}

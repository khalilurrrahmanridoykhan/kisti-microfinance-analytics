/** A small inline bar showing where a value sits (0-100) within its size band, used in the MFI
 * benchmark table. Always paired with the number as text, never colour alone. */
export function PercentileBar({ value }: { value: number | null }) {
  if (value === null) return <span style={{ color: "var(--text-muted)" }}>—</span>;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, minWidth: 92 }}>
      <span
        aria-hidden="true"
        style={{
          position: "relative",
          width: 56,
          height: 6,
          borderRadius: 3,
          background: "var(--surface-2)",
          overflow: "hidden",
        }}
      >
        <span
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            bottom: 0,
            width: `${Math.max(2, value)}%`,
            background: "var(--series-1)",
            borderRadius: 3,
          }}
        />
      </span>
      <span style={{ fontVariantNumeric: "tabular-nums", fontSize: 11.5, color: "var(--text-secondary)" }}>
        {Math.round(value)}
        <span className="sr-only"> percentile within its size band</span>
      </span>
    </span>
  );
}

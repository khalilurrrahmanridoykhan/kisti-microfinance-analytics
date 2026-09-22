export function KpiTile({ label, value, title }: { label: string; value: string; title?: string }) {
  return (
    <div className="kpi-tile" title={title}>
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  );
}

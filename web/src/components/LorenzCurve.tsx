import type { LorenzPoint } from "../lib/types";

export function LorenzCurve({ points, top4SharePct, gini }: { points: LorenzPoint[]; top4SharePct: number; gini: number }) {
  const width = 480;
  const height = 400;
  const padding = { left: 46, right: 12, top: 12, bottom: 34 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const x = (v: number) => padding.left + v * plotWidth;
  const y = (v: number) => padding.top + plotHeight - v * plotHeight;
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${x(p.institutions)} ${y(p.share)}`).join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ maxWidth: width, height: "auto", display: "block" }} role="img" aria-label="Lorenz curve of loan concentration">
      <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} stroke="var(--text-muted)" strokeWidth={1} />
      <text x={x(0.42)} y={y(0.5) - 6} fontSize={10} fill="var(--text-muted)" transform={`rotate(-42 ${x(0.42)} ${y(0.5)})`}>
        Equal shares
      </text>
      <path d={path} fill="none" stroke="var(--series-1)" strokeWidth={2} />
      <line x1={padding.left} x2={width - padding.right} y1={padding.top + plotHeight} y2={padding.top + plotHeight} stroke="var(--text-muted)" />
      <line x1={padding.left} x2={padding.left} y1={padding.top} y2={padding.top + plotHeight} stroke="var(--text-muted)" />
      <text x={width / 2} y={height - 6} fontSize={11} fill="var(--text-secondary)" textAnchor="middle">
        Cumulative share of MFIs, smallest first
      </text>
      <text x={-height / 2} y={12} fontSize={11} fill="var(--text-secondary)" textAnchor="middle" transform="rotate(-90)">
        Cumulative share of loan outstanding
      </text>
      <text x={padding.left + 8} y={padding.top + 16} fontSize={11.5} fill="var(--text-primary)">
        Largest 4 MFIs hold {top4SharePct.toFixed(0)}% of loans (Gini {gini.toFixed(2)})
      </text>
    </svg>
  );
}

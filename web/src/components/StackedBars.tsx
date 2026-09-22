import { useState } from "react";
import { Legend } from "./Legend";
import { ChartTooltip, type TooltipState } from "./ChartTooltip";

export interface StackedSeries {
  key: string;
  label: string;
  color: string;
}

export interface StackedRow {
  label: string;
  values: Record<string, number>;
}

/** A 100%-stacked horizontal bar per category, with a 2px surface gap between segments (the
 * "surface gap" spacer) so touching segments read as distinct without a border. */
export function StackedBars({ rows, series, minLabelWidth = 8 }: { rows: StackedRow[]; series: StackedSeries[]; minLabelWidth?: number }) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const labelWidth = 168;
  const chartWidth = 460;
  const rowHeight = 46;
  const gap = 2;
  const width = labelWidth + chartWidth + 12;
  const height = rows.length * rowHeight + 8;

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ maxWidth: width, height: "auto", display: "block" }} role="img" aria-label="Stacked bar chart">
        {rows.map((row, i) => {
          const y = i * rowHeight + 8;
          let cursor = 0;
          return (
            <g key={row.label}>
              <text x={labelWidth - 8} y={y + 21} fontSize={11.5} textAnchor="end" fill="var(--text-secondary)">
                {row.label}
              </text>
              {series.map((s) => {
                const value = row.values[s.key] ?? 0;
                const segmentWidth = Math.max((value / 100) * chartWidth - gap, 0);
                const x = labelWidth + (cursor / 100) * chartWidth;
                cursor += value;
                const showLabel = (value / 100) * chartWidth >= minLabelWidth * 2.2;
                return (
                  <g
                    key={s.key}
                    onMouseMove={(event) =>
                      setTooltip({ x: event.clientX, y: event.clientY, content: `${row.label} — ${s.label}: ${value.toFixed(1)}%` })
                    }
                    onMouseLeave={() => setTooltip(null)}
                  >
                    <rect x={x} y={y} width={segmentWidth} height={36} fill={s.color} rx={2} />
                    {showLabel && (
                      <text x={x + segmentWidth / 2} y={y + 22} fontSize={10.5} textAnchor="middle" fill="white">
                        {value.toFixed(0)}%
                      </text>
                    )}
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
      <Legend entries={series.map((s) => ({ label: s.label, color: s.color }))} />
      <ChartTooltip state={tooltip} />
    </div>
  );
}

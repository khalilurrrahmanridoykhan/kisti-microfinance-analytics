import { useState } from "react";
import { ChartTooltip, type TooltipState } from "./ChartTooltip";

export interface RangeRow {
  label: string;
  p25: number;
  median: number;
  p75: number;
  n: number;
}

/** A median dot with an interquartile-range line per category — the same form as the matching
 * static figure in RESULTS.md. Single hue: no legend needed. */
export function RangeDots({
  rows,
  domainMin,
  domainMax,
  color = "var(--series-1)",
  formatValue = (v: number) => v.toFixed(1),
  unit = "",
}: {
  rows: RangeRow[];
  domainMin: number;
  domainMax: number;
  color?: string;
  formatValue?: (value: number) => string;
  unit?: string;
}) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const labelWidth = 168;
  const chartWidth = 380;
  const rowHeight = 34;
  const width = labelWidth + chartWidth + 60;
  const height = rows.length * rowHeight + 8;
  const scale = (v: number) => ((v - domainMin) / (domainMax - domainMin)) * chartWidth;

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ maxWidth: width, height: "auto", display: "block" }} role="img" aria-label="Range chart">
        {rows.map((row, i) => {
          const y = i * rowHeight + rowHeight / 2;
          return (
            <g
              key={row.label}
              onMouseMove={(event) =>
                setTooltip({
                  x: event.clientX,
                  y: event.clientY,
                  content: `${row.label}: median ${formatValue(row.median)}${unit} (middle half ${formatValue(row.p25)}–${formatValue(row.p75)}${unit}, n=${row.n})`,
                })
              }
              onMouseLeave={() => setTooltip(null)}
            >
              <text x={labelWidth - 8} y={y + 4} fontSize={11.5} textAnchor="end" fill="var(--text-secondary)">
                {row.label}
              </text>
              <line
                x1={labelWidth + scale(row.p25)}
                x2={labelWidth + scale(row.p75)}
                y1={y}
                y2={y}
                stroke={color}
                strokeWidth={2}
                strokeLinecap="round"
              />
              <circle cx={labelWidth + scale(row.median)} cy={y} r={5} fill={color} stroke="var(--surface-raised)" strokeWidth={2} />
              <text x={labelWidth + scale(row.median)} y={y - 10} fontSize={10.5} textAnchor="middle" fill="var(--text-primary)">
                {formatValue(row.median)}
              </text>
            </g>
          );
        })}
      </svg>
      <ChartTooltip state={tooltip} />
    </div>
  );
}

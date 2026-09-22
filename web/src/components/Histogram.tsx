import { useMemo, useState } from "react";
import { roundedColumnPath } from "../lib/svg";
import { ChartTooltip, type TooltipState } from "./ChartTooltip";

export function Histogram({
  values,
  binWidth,
  domainMax,
  color = "var(--series-1)",
  reference,
  xLabel,
}: {
  values: number[];
  binWidth: number;
  domainMax: number;
  color?: string;
  reference?: { value: number; label: string };
  xLabel: string;
}) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const bins = useMemo(() => {
    const count = Math.ceil(domainMax / binWidth);
    const counts = new Array(count).fill(0);
    for (const value of values) {
      const clipped = Math.min(Math.max(value, 0), domainMax - 0.001);
      counts[Math.floor(clipped / binWidth)] += 1;
    }
    return counts;
  }, [values, binWidth, domainMax]);

  const width = 620;
  const height = 260;
  const padding = { left: 40, right: 12, top: 12, bottom: 34 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const maxCount = Math.max(...bins, 1);
  const barWidth = plotWidth / bins.length;
  const scaleX = (v: number) => padding.left + (v / domainMax) * plotWidth;

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ maxWidth: width, height: "auto", display: "block" }} role="img" aria-label="Histogram">
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <line
            key={t}
            x1={padding.left}
            x2={width - padding.right}
            y1={padding.top + plotHeight * (1 - t)}
            y2={padding.top + plotHeight * (1 - t)}
            stroke="var(--border)"
            strokeWidth={1}
          />
        ))}
        {bins.map((count, i) => {
          const x = padding.left + i * barWidth;
          const barHeight = (count / maxCount) * plotHeight;
          return (
            <path
              key={i}
              d={roundedColumnPath(x + 1, padding.top + plotHeight - barHeight, barWidth - 2, barHeight, 2)}
              fill={color}
              onMouseMove={(event) =>
                setTooltip({
                  x: event.clientX,
                  y: event.clientY,
                  content: `${(i * binWidth).toFixed(0)}–${((i + 1) * binWidth).toFixed(0)}${xLabel.includes("%") ? "%" : ""}: ${count} MFIs`,
                })
              }
              onMouseLeave={() => setTooltip(null)}
            />
          );
        })}
        {reference && (
          <g>
            <line
              x1={scaleX(reference.value)}
              x2={scaleX(reference.value)}
              y1={padding.top}
              y2={padding.top + plotHeight}
              stroke="var(--text-primary)"
              strokeWidth={1.4}
            />
            <text x={scaleX(reference.value) + 4} y={padding.top + 10} fontSize={10} fill="var(--text-primary)">
              {reference.label}
            </text>
          </g>
        )}
        <line x1={padding.left} x2={width - padding.right} y1={padding.top + plotHeight} y2={padding.top + plotHeight} stroke="var(--text-muted)" />
        <text x={padding.left} y={height - 6} fontSize={11} fill="var(--text-secondary)">
          {xLabel}
        </text>
        <text x={4} y={padding.top + 4} fontSize={11} fill="var(--text-secondary)">
          MFIs
        </text>
      </svg>
      <ChartTooltip state={tooltip} />
    </div>
  );
}

import { useState } from "react";
import { ChartTooltip, type TooltipState } from "./ChartTooltip";

export interface ScatterPoint {
  x: number;
  y: number;
  label: string;
}

/** One hue, so no legend (a single series needs none). Points carry a surface ring so they stay
 * legible where they overlap, and a per-point tooltip names the institution on hover only —
 * nothing here is a published list. */
export function ScatterPlot({
  points,
  xDomain,
  yDomain,
  color = "var(--series-1)",
  xLabel,
  yLabel,
  referenceY,
}: {
  points: ScatterPoint[];
  xDomain: [number, number];
  yDomain: [number, number];
  color?: string;
  xLabel: string;
  yLabel: string;
  referenceY?: { value: number; label: string };
}) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const width = 560;
  const height = 380;
  const padding = { left: 46, right: 12, top: 12, bottom: 34 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const scaleX = (v: number) => padding.left + ((v - xDomain[0]) / (xDomain[1] - xDomain[0])) * plotWidth;
  const scaleY = (v: number) => padding.top + plotHeight - ((v - yDomain[0]) / (yDomain[1] - yDomain[0])) * plotHeight;

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ maxWidth: width, height: "auto", display: "block" }} role="img" aria-label="Scatter plot">
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <line
            key={t}
            x1={padding.left}
            x2={width - padding.right}
            y1={padding.top + plotHeight * t}
            y2={padding.top + plotHeight * t}
            stroke="var(--border)"
            strokeWidth={1}
          />
        ))}
        {referenceY && (
          <g>
            <line
              x1={padding.left}
              x2={width - padding.right}
              y1={scaleY(referenceY.value)}
              y2={scaleY(referenceY.value)}
              stroke="var(--text-primary)"
              strokeWidth={1.2}
            />
            <text x={padding.left + 4} y={scaleY(referenceY.value) - 4} fontSize={10} fill="var(--text-primary)">
              {referenceY.label}
            </text>
          </g>
        )}
        {points.map((point, i) => (
          <circle
            key={i}
            cx={scaleX(point.x)}
            cy={scaleY(point.y)}
            r={4}
            fill={color}
            fillOpacity={0.55}
            stroke="var(--surface-raised)"
            strokeWidth={1}
            onMouseMove={(event) =>
              setTooltip({
                x: event.clientX,
                y: event.clientY,
                content: `${point.label}: yield ${point.x.toFixed(1)}%, OSS ${point.y.toFixed(1)}%`,
              })
            }
            onMouseLeave={() => setTooltip(null)}
          />
        ))}
        <line x1={padding.left} x2={width - padding.right} y1={padding.top + plotHeight} y2={padding.top + plotHeight} stroke="var(--text-muted)" />
        <line x1={padding.left} x2={padding.left} y1={padding.top} y2={padding.top + plotHeight} stroke="var(--text-muted)" />
        <text x={width / 2} y={height - 6} fontSize={11} fill="var(--text-secondary)" textAnchor="middle">
          {xLabel}
        </text>
        <text x={-height / 2} y={12} fontSize={11} fill="var(--text-secondary)" textAnchor="middle" transform="rotate(-90)">
          {yLabel}
        </text>
      </svg>
      <ChartTooltip state={tooltip} />
    </div>
  );
}

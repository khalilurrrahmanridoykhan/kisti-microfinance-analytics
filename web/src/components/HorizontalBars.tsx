import { useState } from "react";
import { roundedBarPath } from "../lib/svg";
import { ChartTooltip, type TooltipState } from "./ChartTooltip";

// Rough width of one character at the label font size (11.5px), used only to decide whether a
// label needs shortening — SVG text has no layout-time wrapping, so a label longer than its
// column would otherwise render past x=0 and be clipped by the svg's default overflow:hidden.
const CHAR_WIDTH_PX = 6.3;

function fitLabel(label: string, maxWidth: number): string {
  const budget = Math.max(1, Math.floor(maxWidth / CHAR_WIDTH_PX));
  if (label.length <= budget) return label;
  return `${label.slice(0, Math.max(1, budget - 1))}…`;
}

export interface BarRow {
  label: string;
  value: number;
  tooltip?: string;
  endLabel?: string;
  /** The full label for screen readers and the hover tooltip, when `label` is a shortened
   * version kept short so it fits the fixed label column without being clipped. */
  fullLabel?: string;
}

/** A single-series horizontal bar list: one hue, so no legend, per the dataviz skill (a single
 * series needs no legend box). Each bar is hoverable and the values live in a visually-hidden
 * table for screen readers and the colour-blind/no-JS case. */
export function HorizontalBars({
  rows,
  domainMax,
  color = "var(--series-1)",
  valueSuffix = "",
  height = 28,
  reference,
  formatValue = (v: number) => v.toFixed(1),
}: {
  rows: BarRow[];
  domainMax: number;
  color?: string;
  valueSuffix?: string;
  height?: number;
  reference?: { value: number; label: string };
  formatValue?: (value: number) => string;
}) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const labelWidth = 168;
  const chartWidth = 420;
  const gap = 10;
  const rowHeight = height + gap;
  const width = labelWidth + chartWidth + 70;
  const svgHeight = rows.length * rowHeight + 4;
  const scale = (v: number) => (v / domainMax) * chartWidth;

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${svgHeight}`} width="100%" style={{ maxWidth: width, height: "auto", display: "block" }} role="img" aria-label="Bar chart">
        {reference && (
          <g>
            <line
              x1={labelWidth + scale(reference.value)}
              x2={labelWidth + scale(reference.value)}
              y1={0}
              y2={svgHeight}
              stroke="var(--text-primary)"
              strokeWidth={1.2}
            />
            <text x={labelWidth + scale(reference.value) + 4} y={10} fontSize={10} fill="var(--text-primary)">
              {reference.label}
            </text>
          </g>
        )}
        {rows.map((row, i) => {
          const y = i * rowHeight + (reference ? 14 : 0);
          const barWidth = Math.max(scale(row.value), 0);
          return (
            <g
              key={row.label}
              onMouseMove={(event) =>
                setTooltip({
                  x: event.clientX,
                  y: event.clientY,
                  content: `${row.fullLabel ?? row.label}: ${formatValue(row.value)}${valueSuffix}${row.tooltip ? ` — ${row.tooltip}` : ""}`,
                })
              }
              onMouseLeave={() => setTooltip(null)}
            >
              <text x={labelWidth - 8} y={y + height / 2 + 4} fontSize={11.5} textAnchor="end" fill="var(--text-secondary)">
                {fitLabel(row.label, labelWidth - 8)}
                <title>{row.fullLabel ?? row.label}</title>
              </text>
              <path d={roundedBarPath(labelWidth, y, barWidth, height)} fill={color} />
              <text x={labelWidth + barWidth + 8} y={y + height / 2 + 4} fontSize={11.5} fill="var(--text-primary)">
                {row.endLabel ?? `${formatValue(row.value)}${valueSuffix}`}
              </text>
            </g>
          );
        })}
      </svg>
      {/* A <table> ignores a 1px width under auto layout (its min-content wins), so the
          sr-only clipping box has to be a plain div wrapped around it, not the table itself. */}
      <div className="sr-only">
        <table>
          <caption>Bar chart values</caption>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                <td>
                  {formatValue(row.value)}
                  {valueSuffix}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ChartTooltip state={tooltip} />
    </div>
  );
}

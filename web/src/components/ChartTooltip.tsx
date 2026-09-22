import type { ReactNode } from "react";

export interface TooltipState {
  x: number;
  y: number;
  content: ReactNode;
}

/** A fixed-position tooltip following the pointer. Chart components own a `TooltipState | null`
 * and render this next to their SVG; see interaction.md for why hover is not optional here. */
export function ChartTooltip({ state }: { state: TooltipState | null }) {
  if (!state) return null;
  return (
    <div className="tooltip" role="tooltip" style={{ left: state.x + 12, top: state.y + 12 }}>
      {state.content}
    </div>
  );
}

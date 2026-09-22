/** A horizontal bar path grown from `x` (the baseline), rounded only on the far end, per the
 * dataviz mark spec ("4px rounded data-end, square at the baseline"). `width` must be >= 0. */
export function roundedBarPath(x: number, y: number, width: number, height: number, radius = 4): string {
  const r = Math.min(radius, height / 2, Math.max(width, 0.01));
  const x1 = x + width;
  if (width <= 0) return `M ${x} ${y} h 0 v ${height} h 0 Z`;
  return [
    `M ${x} ${y}`,
    `H ${x1 - r}`,
    `Q ${x1} ${y} ${x1} ${y + r}`,
    `V ${y + height - r}`,
    `Q ${x1} ${y + height} ${x1 - r} ${y + height}`,
    `H ${x}`,
    "Z",
  ].join(" ");
}

/** Same, but growing vertically from a baseline at the bottom (`y + height`), rounded on top. */
export function roundedColumnPath(x: number, yTop: number, width: number, height: number, radius = 4): string {
  const r = Math.min(radius, width / 2, Math.max(height, 0.01));
  const yBase = yTop + height;
  if (height <= 0) return `M ${x} ${yBase} h ${width} v 0 h ${-width} Z`;
  return [
    `M ${x} ${yBase}`,
    `V ${yTop + r}`,
    `Q ${x} ${yTop} ${x + r} ${yTop}`,
    `H ${x + width - r}`,
    `Q ${x + width} ${yTop} ${x + width} ${yTop + r}`,
    `V ${yBase}`,
    "Z",
  ].join(" ");
}

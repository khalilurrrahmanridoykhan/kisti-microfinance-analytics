/** Zoom maths for the district map: fit a bounding box into the map's view box. */

export type BBox = [number, number, number, number]; // x0, y0, x1, y1 in view-box units

export interface ZoomTransform {
  scale: number;
  tx: number;
  ty: number;
}

export const IDENTITY: ZoomTransform = { scale: 1, tx: 0, ty: 0 };

/** The scale-then-translate that centres `box` in a `width` × `height` view, leaving `margin`
 * (a fraction of the view) free on each side. Never zooms out past the whole map (scale ≥ 1)
 * and caps at `maxScale` so a tiny district does not fill the frame with a few vertices. */
export function fitBox(box: BBox, width: number, height: number, margin = 0.08, maxScale = 6): ZoomTransform {
  const boxWidth = Math.max(box[2] - box[0], 1);
  const boxHeight = Math.max(box[3] - box[1], 1);
  const usable = 1 - 2 * margin;
  const scale = Math.min(Math.max(Math.min((width * usable) / boxWidth, (height * usable) / boxHeight), 1), maxScale);
  const cx = (box[0] + box[2]) / 2;
  const cy = (box[1] + box[3]) / 2;
  return { scale, tx: width / 2 - scale * cx, ty: height / 2 - scale * cy };
}

/** The part of the full map visible under `t`, as a bounding box in map units (for the locator). */
export function visibleBox(t: ZoomTransform, width: number, height: number): BBox {
  // `|| 0` turns the -0 an unzoomed transform produces into 0.
  return [-t.tx / t.scale || 0, -t.ty / t.scale || 0, (width - t.tx) / t.scale, (height - t.ty) / t.scale];
}

/** `box` grown by `factor` around its centre, to show a district with its neighbours. */
export function expandBox(box: BBox, factor: number): BBox {
  const cx = (box[0] + box[2]) / 2;
  const cy = (box[1] + box[3]) / 2;
  const hw = ((box[2] - box[0]) * factor) / 2;
  const hh = ((box[3] - box[1]) * factor) / 2;
  return [cx - hw, cy - hh, cx + hw, cy + hh];
}

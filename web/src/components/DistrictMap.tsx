import { useEffect, useMemo, useRef, useState } from "react";
import { CLASS_COUNT, MAP_METRICS, classOf, quantileClasses, type MapMetric } from "../lib/choropleth";
import { formatCompactTaka, formatInt } from "../lib/format";
import { IDENTITY, expandBox, fitBox, visibleBox, type BBox } from "../lib/mapzoom";
import type { DistrictRecord } from "../lib/types";
import { ChartTooltip, type TooltipState } from "./ChartTooltip";

interface GeoShape {
  path: string;
  label: [number, number];
  bbox: BBox;
}

interface GeoDistrict extends GeoShape {
  district: string;
  division: string;
}

interface GeoDivision extends GeoShape {
  division: string;
}

interface GeoData {
  source: string;
  license: string;
  viewBox: [number, number, number, number];
  districts: GeoDistrict[];
  divisions: GeoDivision[];
}

const GEO_URL = `${import.meta.env.BASE_URL}geo/bd-districts.json`;

/** How much wider than a district's own box the view is when zoomed to it, so its neighbours
 * stay in sight for context. */
const DISTRICT_ZOOM_CONTEXT = 2.2;

/** A choropleth of the 64 districts. Viewers can filter to a division (the map zooms there,
 * labels its districts and fades the rest) and on to a single district, with a locator inset
 * showing where the view sits in Bangladesh. Geometry is built by scripts/build_district_map.py
 * from the official BBS/OCHA boundaries; colours are a validated 5-step ordinal blue ramp
 * (--map-1..5) whose classes stay national at every zoom so a shade always means the same. */
export function DistrictMap({ districts }: { districts: DistrictRecord[] }) {
  const [geo, setGeo] = useState<GeoData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metricId, setMetricId] = useState(MAP_METRICS[0].id);
  const [division, setDivision] = useState<string | null>(null);
  const [zoomDistrict, setZoomDistrict] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  // Screen pixels per view-box unit, so labels keep a readable on-screen size on any width.
  const svgRef = useRef<SVGSVGElement>(null);
  const [pxPerUnit, setPxPerUnit] = useState(1);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      const viewWidth = svg.viewBox.baseVal?.width;
      if (viewWidth) setPxPerUnit(svg.getBoundingClientRect().width / viewWidth || 1);
    });
    observer.observe(svg);
    return () => observer.disconnect();
  }, [geo]);

  useEffect(() => {
    let cancelled = false;
    fetch(GEO_URL)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<GeoData>;
      })
      .then((data) => {
        if (!cancelled) setGeo(data);
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : String(reason));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const metric = MAP_METRICS.find((m) => m.id === metricId) ?? MAP_METRICS[0];
  const byName = useMemo(() => new Map(districts.map((d) => [d.district, d])), [districts]);
  const classes = useMemo(() => quantileClasses(districts.map(metric.value)), [districts, metric]);
  const national = useMemo(() => metric.national(districts), [districts, metric]);
  const ranked = useMemo(() => [...districts].sort((a, b) => metric.value(b) - metric.value(a)), [districts, metric]);
  const divisionNames = useMemo(() => [...new Set(districts.map((d) => d.division))].sort(), [districts]);
  const inDivision = useMemo(() => (division ? ranked.filter((d) => d.division === division) : []), [ranked, division]);

  const width = geo?.viewBox[2] ?? 600;
  const height = geo?.viewBox[3] ?? 841;
  const zoomBox: BBox | null = useMemo(() => {
    if (!geo) return null;
    if (zoomDistrict) {
      const shape = geo.districts.find((d) => d.district === zoomDistrict);
      return shape ? expandBox(shape.bbox, DISTRICT_ZOOM_CONTEXT) : null;
    }
    if (division) return geo.divisions.find((d) => d.division === division)?.bbox ?? null;
    return null;
  }, [geo, division, zoomDistrict]);
  const transform = zoomBox ? fitBox(zoomBox, width, height) : IDENTITY;

  const focusName = hovered ?? selected;
  const focus = focusName ? byName.get(focusName) : undefined;
  const focusShape = geo?.districts.find((g) => g.district === focusName);
  const selectedShape = geo?.districts.find((g) => g.district === selected);
  const max = metric.value(ranked[0]);

  function chooseDivision(name: string | null) {
    setDivision(name);
    setZoomDistrict(null);
    if (name && selected && byName.get(selected)?.division !== name) setSelected(null);
  }

  function chooseDistrict(name: string | null) {
    if (!name) {
      setZoomDistrict(null);
      return;
    }
    setDivision(byName.get(name)?.division ?? null);
    setZoomDistrict(name);
    setSelected(name);
  }

  function toggleSelected(name: string) {
    const row = byName.get(name);
    // A faded district outside the current division moves the view to its own division.
    if (division && row && row.division !== division) {
      chooseDivision(row.division);
      setSelected(name);
      return;
    }
    setSelected((current) => (current === name ? null : name));
  }

  const inView = (d: GeoDistrict) => !division || d.division === division;
  const labelled = geo ? geo.districts.filter((d) => (division ? d.division === division : d.district === selected)) : [];

  return (
    <div className="map-layout">
      <div className="map-main">
        <div className="map-toolbar">
          <div className="segmented" role="group" aria-label="Map metric">
            {MAP_METRICS.map((m) => (
              <button key={m.id} type="button" aria-pressed={m.id === metric.id} onClick={() => setMetricId(m.id)}>
                {m.short}
              </button>
            ))}
          </div>
        </div>

        <div className="area-filter" role="group" aria-label="Filter the map by area">
          <button type="button" className="chip" aria-pressed={division === null} onClick={() => chooseDivision(null)}>
            All Bangladesh
          </button>
          {divisionNames.map((name) => (
            <button key={name} type="button" className="chip" aria-pressed={division === name} onClick={() => chooseDivision(name)}>
              {name}
            </button>
          ))}
        </div>

        <div className="map-crumbs">
          <nav aria-label="Map area">
            <button type="button" onClick={() => chooseDivision(null)} aria-current={!division ? "location" : undefined}>
              Bangladesh
            </button>
            {division && (
              <>
                <span aria-hidden="true">›</span>
                <button type="button" onClick={() => chooseDivision(division)} aria-current={!zoomDistrict ? "location" : undefined}>
                  {division} division
                </button>
              </>
            )}
            {zoomDistrict && (
              <>
                <span aria-hidden="true">›</span>
                <span aria-current="location">{zoomDistrict}</span>
              </>
            )}
          </nav>
          {division && (
            <select
              aria-label="Zoom to a district"
              value={zoomDistrict ?? ""}
              onChange={(event) => chooseDistrict(event.target.value || null)}
            >
              <option value="">Zoom to a district…</option>
              {inDivision
                .map((d) => d.district)
                .sort()
                .map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
            </select>
          )}
        </div>

        <div className="map-canvas">
          {error && <p className="map-status">The district map could not be loaded ({error}). The table below has every value.</p>}
          {!geo && !error && <div className="map-skeleton" aria-label="Loading map" />}
          {geo && (
            <svg
              ref={svgRef}
              viewBox={geo.viewBox.join(" ")}
              className={`map-svg${division ? " is-zoomed" : ""}`}
              role="group"
              aria-label={`Map of ${division ? `${division} division` : "Bangladesh"} districts shaded by ${metric.label.toLowerCase()}`}
              onMouseLeave={() => {
                setHovered(null);
                setTooltip(null);
              }}
            >
              <g
                className="map-zoom"
                style={{ transform: `translate(${transform.tx}px, ${transform.ty}px) scale(${transform.scale})` }}
              >
                {geo.districts.map((shape) => {
                  const row = byName.get(shape.district);
                  if (!row) return null;
                  const value = metric.value(row);
                  const active = inView(shape);
                  return (
                    <path
                      key={shape.district}
                      d={shape.path}
                      className={`map-district${active ? "" : " is-faded"}`}
                      fill={`var(--map-${classOf(value, classes) + 1})`}
                      tabIndex={active ? 0 : -1}
                      role="button"
                      aria-pressed={selected === shape.district}
                      aria-label={`${shape.district}, ${row.division}: ${metric.format(value)}`}
                      onMouseMove={(event) => {
                        setHovered(shape.district);
                        setTooltip({
                          x: event.clientX,
                          y: event.clientY,
                          content: (
                            <>
                              <strong>{shape.district}</strong> <span className="tooltip-muted">{row.division}</span>
                              <br />
                              {metric.short}: <strong>{metric.format(value)}</strong>
                            </>
                          ),
                        });
                      }}
                      onClick={() => toggleSelected(shape.district)}
                      onFocus={() => setHovered(shape.district)}
                      onBlur={() => setHovered(null)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          toggleSelected(shape.district);
                        }
                      }}
                    />
                  );
                })}
                {geo.divisions.map((d) => (
                  <path key={d.division} d={d.path} className={`map-division${d.division === division ? " is-active" : ""}`} />
                ))}
                {/* Outlines drawn last so a highlighted border is never covered by a neighbour. */}
                {selectedShape && <path d={selectedShape.path} className="map-outline map-outline-selected" />}
                {focusShape && focusShape !== selectedShape && <path d={focusShape.path} className="map-outline" />}
                {labelled.map((shape) => {
                  const row = byName.get(shape.district);
                  return (
                    <text
                      key={shape.district}
                      x={shape.label[0]}
                      y={shape.label[1]}
                      className="map-label"
                      textAnchor="middle"
                      style={{
                        fontSize: `${11.5 / (transform.scale * pxPerUnit)}px`,
                        strokeWidth: `${3.5 / (transform.scale * pxPerUnit)}px`,
                      }}
                    >
                      {shape.district}
                      {division && row && (
                        <tspan x={shape.label[0]} dy="1.15em" className="map-label-value">
                          {metric.format(metric.value(row))}
                        </tspan>
                      )}
                    </text>
                  );
                })}
              </g>
            </svg>
          )}
          {geo && division && (
            <Locator geo={geo} division={division} view={visibleBox(transform, width, height)} onPick={chooseDivision} />
          )}
          {geo && division && (
            <button type="button" className="map-reset" onClick={() => chooseDivision(null)}>
              ⤢ Show all Bangladesh
            </button>
          )}
        </div>

        <div className="map-legend" aria-label={`${metric.label}, five classes of about 13 districts each`}>
          <div className="map-legend-title">{metric.label}</div>
          <div className="map-legend-scale">
            {classes.map((c, i) => (
              <div key={i} className="map-legend-step">
                <span className="map-legend-swatch" style={{ background: `var(--map-${i + 1})` }} />
                <span className="map-legend-range">
                  {metric.format(c.min)}–{metric.format(c.max)}
                </span>
              </div>
            ))}
          </div>
          <div className="map-legend-note">
            Each shade holds about one fifth of all 64 districts ({CLASS_COUNT} quantile classes), at every zoom level.
            Bangladesh: {metric.format(national)}.
          </div>
        </div>
        {geo && (
          <p className="card-caption">
            Boundaries: {geo.source}, {geo.license}. Pick a division to zoom in; hover a district for its value, click to
            pin it.
          </p>
        )}
      </div>

      <aside className="map-side">
        <div className="district-panel" aria-live="polite">
          {focus ? (
            <DistrictDetail
              row={focus}
              metric={metric}
              national={national}
              rank={ranked.findIndex((d) => d.district === focus.district) + 1}
              total={districts.length}
              divisionRank={ranked.filter((d) => d.division === focus.division).findIndex((d) => d.district === focus.district) + 1}
              divisionSize={ranked.filter((d) => d.division === focus.division).length}
              onZoom={zoomDistrict === focus.district ? undefined : () => chooseDistrict(focus.district)}
              onClear={selected ? () => setSelected(null) : undefined}
            />
          ) : division ? (
            <AreaSummary
              eyebrow={`${inDivision.length} districts`}
              name={`${division} division`}
              rows={inDivision}
              metric={metric}
              national={national}
            />
          ) : (
            <>
              <div className="district-panel-eyebrow">All 64 districts</div>
              <div className="district-panel-name">Bangladesh</div>
              <div className="district-panel-value">{metric.format(national)}</div>
              <div className="district-panel-metric">{metric.label}</div>
              <div className="district-panel-compare">
                Ranges from {metric.format(metric.value(ranked[ranked.length - 1]))} ({ranked[ranked.length - 1].district}) to{" "}
                {metric.format(max)} ({ranked[0].district}). Pick a division to zoom in.
              </div>
            </>
          )}
        </div>

        {division ? (
          <RankList title={`Districts in ${division}`} rows={inDivision} metric={metric} max={max} selected={selected} onSelect={toggleSelected} />
        ) : (
          <>
            <RankList title="Highest" rows={ranked.slice(0, 5)} metric={metric} max={max} selected={selected} onSelect={toggleSelected} />
            <RankList
              title="Lowest"
              rows={ranked.slice(-5).reverse()}
              metric={metric}
              max={max}
              selected={selected}
              onSelect={toggleSelected}
            />
          </>
        )}
      </aside>
      <ChartTooltip state={tooltip} />
    </div>
  );
}

/** A small whole-country map marking the division in view and the zoomed window. */
function Locator({ geo, division, view, onPick }: { geo: GeoData; division: string; view: BBox; onPick: (name: string) => void }) {
  return (
    <svg className="map-locator" viewBox={geo.viewBox.join(" ")} aria-hidden="true">
      {geo.divisions.map((d) => (
        <path
          key={d.division}
          d={d.path}
          className={`locator-division${d.division === division ? " is-active" : ""}`}
          onClick={() => onPick(d.division)}
        >
          <title>{d.division}</title>
        </path>
      ))}
      <rect x={view[0]} y={view[1]} width={view[2] - view[0]} height={view[3] - view[1]} className="locator-window" />
    </svg>
  );
}

function deltaText(value: number, national: number): string {
  const pct = (value / national - 1) * 100;
  return `${pct >= 0 ? "▲" : "▼"} ${Math.abs(pct).toFixed(0)}%`;
}

function DistrictDetail({
  row,
  metric,
  national,
  rank,
  total,
  divisionRank,
  divisionSize,
  onZoom,
  onClear,
}: {
  row: DistrictRecord;
  metric: MapMetric;
  national: number;
  rank: number;
  total: number;
  divisionRank: number;
  divisionSize: number;
  onZoom?: () => void;
  onClear?: () => void;
}) {
  const value = metric.value(row);
  return (
    <>
      <div className="district-panel-eyebrow">{row.division} division</div>
      <div className="district-panel-name">{row.district}</div>
      <div className="district-panel-value">{metric.format(value)}</div>
      <div className="district-panel-metric">{metric.label}</div>
      <div className="district-panel-compare">
        <span className="delta">{deltaText(value, national)}</span> vs Bangladesh · rank {rank} of {total}
        <br />
        {divisionRank} of {divisionSize} in {row.division}
      </div>
      <dl className="district-stats">
        <div>
          <dt>Population</dt>
          <dd>{formatInt(row.population)}</dd>
        </div>
        <div>
          <dt>MFI borrowers</dt>
          <dd>{formatInt(row.borrowers)}</dd>
        </div>
        <div>
          <dt>Branches</dt>
          <dd>{formatInt(row.branches)}</dd>
        </div>
        <div>
          <dt>Loan outstanding</dt>
          <dd>{formatCompactTaka(row.loan_outstanding_bdt)}</dd>
        </div>
      </dl>
      {(onZoom || onClear) && (
        <div className="district-actions">
          {onZoom && (
            <button type="button" className="btn" onClick={onZoom}>
              Zoom to {row.district}
            </button>
          )}
          {onClear && (
            <button type="button" className="btn btn-quiet" onClick={onClear}>
              Clear selection
            </button>
          )}
        </div>
      )}
    </>
  );
}

function AreaSummary({
  eyebrow,
  name,
  rows,
  metric,
  national,
}: {
  eyebrow: string;
  name: string;
  rows: DistrictRecord[];
  metric: MapMetric;
  national: number;
}) {
  const value = metric.national(rows);
  const total = (f: (d: DistrictRecord) => number) => rows.reduce((sum, d) => sum + f(d), 0);
  return (
    <>
      <div className="district-panel-eyebrow">{eyebrow}</div>
      <div className="district-panel-name">{name}</div>
      <div className="district-panel-value">{metric.format(value)}</div>
      <div className="district-panel-metric">{metric.label}</div>
      <div className="district-panel-compare">
        <span className="delta">{deltaText(value, national)}</span> vs Bangladesh
      </div>
      <dl className="district-stats">
        <div>
          <dt>Population</dt>
          <dd>{formatInt(total((d) => d.population))}</dd>
        </div>
        <div>
          <dt>MFI borrowers</dt>
          <dd>{formatInt(total((d) => d.borrowers))}</dd>
        </div>
        <div>
          <dt>Branches</dt>
          <dd>{formatInt(total((d) => d.branches))}</dd>
        </div>
        <div>
          <dt>Loan outstanding</dt>
          <dd>{formatCompactTaka(total((d) => d.loan_outstanding_bdt))}</dd>
        </div>
      </dl>
    </>
  );
}

function RankList({
  title,
  rows,
  metric,
  max,
  selected,
  onSelect,
}: {
  title: string;
  rows: DistrictRecord[];
  metric: MapMetric;
  max: number;
  selected: string | null;
  onSelect: (name: string) => void;
}) {
  return (
    <div className="rank-list">
      <div className="rank-list-title">{title}</div>
      <ol>
        {rows.map((d) => (
          <li key={d.district}>
            <button type="button" aria-pressed={selected === d.district} onClick={() => onSelect(d.district)}>
              <span className="rank-name">{d.district}</span>
              <span className="rank-bar" aria-hidden="true">
                <span style={{ width: `${(metric.value(d) / max) * 100}%` }} />
              </span>
              <span className="rank-value">{metric.format(metric.value(d))}</span>
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}

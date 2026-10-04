import { useEffect, useMemo, useState } from "react";
import { CLASS_COUNT, MAP_METRICS, classOf, quantileClasses } from "../lib/choropleth";
import { formatCompactTaka, formatInt } from "../lib/format";
import type { DistrictRecord } from "../lib/types";
import { ChartTooltip, type TooltipState } from "./ChartTooltip";

interface GeoDistrict {
  district: string;
  path: string;
  label: [number, number];
}

interface GeoData {
  source: string;
  license: string;
  viewBox: [number, number, number, number];
  districts: GeoDistrict[];
}

const GEO_URL = `${import.meta.env.BASE_URL}geo/bd-districts.json`;

/** A choropleth of the 64 districts with a metric switcher, hover tooltip, and a pinned
 * district panel. Geometry is built by scripts/build_district_map.py from the official
 * BBS/OCHA boundaries; colours are a validated 5-step ordinal blue ramp (--map-1..5). */
export function DistrictMap({ districts }: { districts: DistrictRecord[] }) {
  const [geo, setGeo] = useState<GeoData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metricId, setMetricId] = useState(MAP_METRICS[0].id);
  const [selected, setSelected] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

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
  const rankOf = (name: string) => ranked.findIndex((d) => d.district === name) + 1;

  const focusName = hovered ?? selected;
  const focus = focusName ? byName.get(focusName) : undefined;
  const focusShape = geo?.districts.find((g) => g.district === focusName);
  const selectedShape = geo?.districts.find((g) => g.district === selected);
  const max = metric.value(ranked[0]);

  function toggle(name: string) {
    setSelected((current) => (current === name ? null : name));
  }

  return (
    <div className="map-layout">
      <div className="map-main">
        <div className="segmented" role="group" aria-label="Map metric">
          {MAP_METRICS.map((m) => (
            <button key={m.id} type="button" aria-pressed={m.id === metric.id} onClick={() => setMetricId(m.id)}>
              {m.short}
            </button>
          ))}
        </div>

        <div className="map-canvas">
          {error && <p className="map-status">The district map could not be loaded ({error}). The table below has every value.</p>}
          {!geo && !error && <div className="map-skeleton" aria-label="Loading map" />}
          {geo && (
            <svg
              viewBox={geo.viewBox.join(" ")}
              className="map-svg"
              role="group"
              aria-label={`Map of Bangladesh districts shaded by ${metric.label.toLowerCase()}`}
              onMouseLeave={() => {
                setHovered(null);
                setTooltip(null);
              }}
            >
              {geo.districts.map((shape) => {
                const row = byName.get(shape.district);
                if (!row) return null;
                const value = metric.value(row);
                return (
                  <path
                    key={shape.district}
                    d={shape.path}
                    className="map-district"
                    fill={`var(--map-${classOf(value, classes) + 1})`}
                    tabIndex={0}
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
                    onClick={() => toggle(shape.district)}
                    onFocus={() => setHovered(shape.district)}
                    onBlur={() => setHovered(null)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        toggle(shape.district);
                      }
                    }}
                  />
                );
              })}
              {/* Outlines drawn last so a highlighted border is never covered by a neighbour. */}
              {selectedShape && <path d={selectedShape.path} className="map-outline map-outline-selected" />}
              {focusShape && focusShape !== selectedShape && <path d={focusShape.path} className="map-outline" />}
              {selectedShape && (
                <text x={selectedShape.label[0]} y={selectedShape.label[1]} className="map-label" textAnchor="middle">
                  {selectedShape.district}
                </text>
              )}
            </svg>
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
            Each shade holds about one fifth of districts ({CLASS_COUNT} quantile classes). Bangladesh: {metric.format(national)}.
          </div>
        </div>
        {geo && (
          <p className="card-caption">
            Boundaries: {geo.source}, {geo.license}. Hover a district for its value; click to pin it.
          </p>
        )}
      </div>

      <aside className="map-side">
        <div className="district-panel" aria-live="polite">
          {focus ? (
            <>
              <div className="district-panel-eyebrow">{focus.division} division</div>
              <div className="district-panel-name">{focus.district}</div>
              <div className="district-panel-value">{metric.format(metric.value(focus))}</div>
              <div className="district-panel-metric">{metric.label}</div>
              <div className="district-panel-compare">
                <span className="delta">
                  {metric.value(focus) >= national ? "▲" : "▼"} {Math.abs((metric.value(focus) / national - 1) * 100).toFixed(0)}%
                </span>{" "}
                vs Bangladesh · rank {rankOf(focus.district)} of {districts.length}
              </div>
              <dl className="district-stats">
                <div>
                  <dt>Population</dt>
                  <dd>{formatInt(focus.population)}</dd>
                </div>
                <div>
                  <dt>MFI borrowers</dt>
                  <dd>{formatInt(focus.borrowers)}</dd>
                </div>
                <div>
                  <dt>Branches</dt>
                  <dd>{formatInt(focus.branches)}</dd>
                </div>
                <div>
                  <dt>Loan outstanding</dt>
                  <dd>{formatCompactTaka(focus.loan_outstanding_bdt)}</dd>
                </div>
              </dl>
              {selected && (
                <button type="button" className="btn btn-quiet" onClick={() => setSelected(null)}>
                  Clear selection
                </button>
              )}
            </>
          ) : (
            <>
              <div className="district-panel-eyebrow">All 64 districts</div>
              <div className="district-panel-name">Bangladesh</div>
              <div className="district-panel-value">{metric.format(national)}</div>
              <div className="district-panel-metric">{metric.label}</div>
              <div className="district-panel-compare">
                Ranges from {metric.format(metric.value(ranked[ranked.length - 1]))} ({ranked[ranked.length - 1].district}) to{" "}
                {metric.format(max)} ({ranked[0].district}). Select a district on the map for its details.
              </div>
            </>
          )}
        </div>

        <RankList title="Highest" rows={ranked.slice(0, 5)} metric={metric} max={max} selected={selected} onSelect={toggle} />
        <RankList
          title="Lowest"
          rows={ranked.slice(-5).reverse()}
          metric={metric}
          max={max}
          selected={selected}
          onSelect={toggle}
        />
      </aside>
      <ChartTooltip state={tooltip} />
    </div>
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
  metric: (typeof MAP_METRICS)[number];
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

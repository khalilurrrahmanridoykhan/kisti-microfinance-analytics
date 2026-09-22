# Kisti dashboard

A static React + TypeScript app (Vite), deployed to GitHub Pages. It reads only the JSON files
in `public/data/`, written by `python -m kisti.webdata` (see `../Makefile`'s `webdata` target)
— it has no backend and makes no network calls beyond fetching those files.

## Develop

```sh
npm ci
npm run dev        # dev server with hot reload
npm run typecheck  # tsc --noEmit
npx eslint src
npm test           # vitest
npm run build      # production build to dist/, served at /kisti-microfinance-analytics/
npm run preview    # serve the production build locally
```

## Layout

```
src/
  lib/          data loading, the schema contract, formatting, small statistics helpers
  components/   chart primitives (HorizontalBars, RangeDots, StackedBars, Histogram,
                ScatterPlot, LorenzCurve), DataTable, Tabs, theme toggle
  pages/        SectorOverview, MfiBenchmark, Districts, Methods — one per dashboard tab
public/data/    generated JSON (do not hand-edit; regenerate with `make webdata` at the repo root)
```

Design decisions (palette validation, accessibility, what is precomputed vs. derived in the
browser) are written up in [`../docs/dashboard-design.md`](../docs/dashboard-design.md).

## The data contract

`src/lib/schema.ts` lists the same fields, by hand, as `../src/kisti/webdata/schema.py`. If you
add or rename a field on the Python side, update both, and both test suites
(`../tests/test_webdata.py` and `src/lib/schema.test.ts`) — each only checks its own language's
copy of the schema against the JSON, so a change on one side with no matching test update will
still be caught, but only by the side that changed.

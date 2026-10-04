import { useEffect, useState } from "react";
import { Banner } from "./components/Banner";
import { Tabs, TabPanel, type TabDef } from "./components/Tabs";
import { ThemeToggle } from "./components/ThemeToggle";
import { loadAppData, type AppData } from "./lib/data";
import { SectorOverview } from "./pages/SectorOverview";
import { MfiBenchmark } from "./pages/MfiBenchmark";
import { Districts } from "./pages/Districts";
import { Methods } from "./pages/Methods";

const TABS: TabDef[] = [
  { id: "sector", label: "Sector overview" },
  { id: "mfis", label: "MFI benchmark" },
  { id: "districts", label: "District coverage" },
  { id: "methods", label: "Methods & limits" },
];

type LoadState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; data: AppData };

export function App() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [tab, setTab] = useState(TABS[0].id);

  useEffect(() => {
    let cancelled = false;
    loadAppData()
      .then((data) => {
        if (!cancelled) setState({ status: "ready", data });
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ status: "error", message: error instanceof Error ? error.message : String(error) });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Optional chaining: App's own tests stub the loaded data as an empty object.
  const rawEdition = state.status === "ready" ? state.data.meta?.edition : undefined;
  const edition = rawEdition ? formatEdition(rawEdition) : null;

  return (
    <div className="app">
      <header className="masthead">
        <div className="masthead-inner">
          <div className="brand">
            <svg className="brand-mark" viewBox="0 0 32 32" aria-hidden="true">
              <rect width="32" height="32" rx="8" fill="currentColor" />
              <rect x="7" y="17" width="5" height="9" rx="1.5" fill="var(--masthead-bg)" />
              <rect x="14" y="11" width="5" height="15" rx="1.5" fill="var(--masthead-bg)" />
              <rect x="21" y="6" width="5" height="20" rx="1.5" fill="var(--masthead-bg)" />
            </svg>
            <div>
              <p className="brand-eyebrow">Bangladesh microfinance sector</p>
              <h1 className="app-title">Kisti: Microfinance Analytics Dashboard</h1>
              <p className="app-subtitle">
                Real data from the Microcredit Regulatory Authority (693 MFIs) and Census 2022 district populations. No
                synthetic data on this page.
              </p>
            </div>
          </div>
          <div className="masthead-meta">
            {edition && <span className="edition-badge">Edition: {edition}</span>}
            <ThemeToggle />
          </div>
        </div>
      </header>

      {state.status === "ready" && (
        <nav className="tabbar" aria-label="Dashboard">
          <div className="tabbar-inner">
            <Tabs tabs={TABS} active={tab} onChange={setTab} />
          </div>
        </nav>
      )}

      <main className="app-shell">
        {state.status === "loading" && <Banner kind="info">Loading the dashboard data…</Banner>}
        {state.status === "error" && (
          <Banner kind="error">
            <strong>Could not load the dashboard data.</strong> {state.message}
          </Banner>
        )}
        {state.status === "ready" && (
          <>
            <TabPanel id="sector" active={tab}>
              <SectorOverview data={state.data} />
            </TabPanel>
            <TabPanel id="mfis" active={tab}>
              <MfiBenchmark data={state.data} />
            </TabPanel>
            <TabPanel id="districts" active={tab}>
              <Districts data={state.data} />
            </TabPanel>
            <TabPanel id="methods" active={tab}>
              <Methods data={state.data} />
            </TabPanel>
          </>
        )}
      </main>

      <footer className="site-footer">
        <div className="site-footer-inner">
          <span>
            Analysis and demonstration only — not for credit, lending, supervisory or investment decisions.{" "}
            <a href="https://github.com/khalilurrrahmanridoykhan/kisti-microfinance-analytics">Source and methodology</a>.
          </span>
          <span className="site-footer-source">Sources: MRA Annual Statistics · BBS Census 2022</span>
        </div>
      </footer>
    </div>
  );
}

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

/** "2025-06" → "June 2025"; anything else is shown as published. */
function formatEdition(edition: string): string {
  const match = /^(\d{4})-(\d{2})$/.exec(edition);
  const month = match ? MONTHS[Number(match[2]) - 1] : undefined;
  return match && month ? `${month} ${match[1]}` : edition;
}

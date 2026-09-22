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

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1 className="app-title">Kisti: Microfinance Analytics Dashboard</h1>
          <p className="app-subtitle">
            Real data from the Microcredit Regulatory Authority (693 MFIs) and Census 2022 district populations. No
            synthetic data on this page.
          </p>
        </div>
        <ThemeToggle />
      </header>

      {state.status === "loading" && <Banner kind="info">Loading the dashboard data…</Banner>}
      {state.status === "error" && (
        <Banner kind="error">
          <strong>Could not load the dashboard data.</strong> {state.message}
        </Banner>
      )}
      {state.status === "ready" && (
        <>
          <Tabs tabs={TABS} active={tab} onChange={setTab} />
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

      <footer className="footer-note">
        Analysis and demonstration only — not for credit, lending, supervisory or investment decisions.{" "}
        <a href="https://github.com/khalilurrrahmanridoykhan/kisti-microfinance-analytics">Source and methodology</a>.
      </footer>
    </div>
  );
}

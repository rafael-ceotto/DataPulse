import React, { useEffect, useState } from "react";
import AIQuery from "./components/AIQuery";
import HospitalList from "./components/HospitalList";
import RatingChart from "./components/RatingChart";
import PhysicianAnalysis from "./components/PhysicianAnalysis";
import ScarceSpecialties from "./components/ScarceSpecialties";
import PipelineRuns from "./components/PipelineRuns";
import RatingTrend from "./components/RatingTrend";
import DataQuality from "./components/DataQuality";
import PipelineAnalytics from "./components/PipelineAnalytics";
import HospitalsNearMe from "./components/HospitalsNearMe";
import { theme } from "./theme";

const TABS = [
  { id: "hospitals", label: "Hospitals" },
  { id: "analytics", label: "Analytics" },
  { id: "pipeline", label: "Pipeline" },
  { id: "physicians", label: "Physicians" },
];

function useCIStatus() {
  const [status, setStatus] = useState(null);
  useEffect(() => {
    function fetch_() {
      fetch("https://api.github.com/repos/rafael-ceotto/DataPulse/actions/runs?per_page=1")
        .then((r) => r.json())
        .then((data) => {
          const run = data.workflow_runs?.[0];
          if (run) setStatus(run.conclusion);
        })
        .catch(() => {});
    }
    fetch_();
    const id = setInterval(fetch_, 60000);
    return () => clearInterval(id);
  }, []);
  return status;
}

function MetricCard({ label, value, accent }) {
  return (
    <div style={{
      background: "#16222a",
      border: `1px solid #1e2d35`,
      borderRadius: 12,
      padding: "16px 20px",
      flex: "1 1 160px",
    }}>
      <div style={{ fontFamily: theme.mono, fontSize: 10, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color: accent || "#dce5e9", letterSpacing: "-0.02em" }}>
        {value}
      </div>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState("hospitals");
  const ciStatus = useCIStatus();
  const ciColor = ciStatus === "success" ? theme.mint : ciStatus === "failure" ? "#ff6b6b" : "#6f8a95";
  const ciLabel = ciStatus === "success" ? "CI passing" : ciStatus === "failure" ? "CI failing" : "CI unknown";

  return (
    <div style={{ minHeight: "100vh", background: "#f4f6f8", color: theme.ink, fontFamily: theme.sans }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
        body { margin: 0; background: #f4f6f8; }
        * { box-sizing: border-box; }
        @keyframes dp-pulse { 0%,100% { opacity:.25; transform:scaleY(.5); } 50% { opacity:1; transform:scaleY(1); } }
        @keyframes pulse { 0% { opacity:1; } 50% { opacity:0.4; } 100% { opacity:1; } }
      `}</style>

      {/* Header */}
      <header style={{
        borderBottom: `1px solid #e6eaec`,
        padding: "16px 40px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "#ffffff",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 9,
            background: theme.accent,
            display: "flex", alignItems: "center", justifyContent: "center", gap: 3,
          }}>
            {[10, 18, 13].map((h, i) => (
              <span key={i} style={{
                display: "block", width: 3, height: h, borderRadius: 2,
                background: "#fff",
                animation: `dp-pulse 1.4s ease-in-out ${i * 0.2}s infinite`,
              }} />
            ))}
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em", color: theme.ink }}>DataPulse</div>
            <div style={{ fontSize: 11, color: theme.muted, fontFamily: theme.mono }}>CMS Hospital Quality Data</div>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1400, margin: "0 auto", padding: "32px 40px" }}>

        {/* AI Query */}
        <AIQuery />

        {/* Metric cards */}
        <div style={{ display: "flex", gap: 12, marginTop: 24, flexWrap: "wrap" }}>
          <MetricCard label="Facilities" value="5,419" accent={theme.mint} />
          <MetricCard label="Avg Rating" value="3.21 ★" accent="#f1c40f" />
          <MetricCard label="Completeness" value="58.6%" accent="#dce5e9" />
          <MetricCard label="CI Status" value={ciLabel} accent={ciColor} />
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 4, marginTop: 36, borderRadius: 12, padding: "4px", width: "fit-content",}}>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id ? "#0F6F8C" : "#85d6c6",
                border: "none",
                borderRadius: 9,
                color: activeTab === tab.id ? "#ffffff" : theme.ink,
                fontFamily: theme.sans,
                fontSize: 14,
                fontWeight: activeTab === tab.id ? 600 : 400,
                padding: "8px 20px",
                cursor: "pointer",
                transition: "all 0.15s",
                boxShadow: activeTab === tab.id ? "0 1px 4px rgba(0,0,0,.15)" : "none",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div style={{ marginTop: 24 }}>
          {activeTab === "hospitals" && (
            <>
              <HospitalsNearMe />
              <RatingChart />
              <DataQuality />
              <HospitalList />
            </>
          )}
          {activeTab === "analytics" && (
            <>
              <RatingTrend />
              <PipelineAnalytics />
            </>
          )}
          {activeTab === "pipeline" && <PipelineRuns />}
          {activeTab === "physicians" && (
            <>
              <PhysicianAnalysis />
              <ScarceSpecialties />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
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

const COUNTRIES = {
  US: {
    name: "United States",
    source: "CMS (Centers for Medicare & Medicaid Services)",
    description: "5,419 hospitals · Public health data · Updated annually",
    rating_info: "Rating: 1–5 stars based on 46 quality indicators. Higher = better quality care.",
  },
  BR: {
    name: "Brasil",
    source: "DATASUS / Ministério da Saúde",
    description: "7,680 hospitais · Sistema Único de Saúde (SUS)",
    rating_info: "Sem rating nacional único — dados estruturais: leitos, especialidades, equipamentos. Fonte: CNES.",
  },
};

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

function CountrySelector({ country, onChange }) {
  const current = COUNTRIES[country];
  return (
    <div style={{ marginBottom: 0 }}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        {Object.entries(COUNTRIES).map(([code, info]) => (
          <button
            key={code}
            onClick={() => onChange(code)}
            style={{
              background: country === code ? "#0F6F8C" : "#16222a",
              border: `1px solid ${country === code ? "#0F6F8C" : "#1e2d35"}`,
              borderRadius: 10,
              padding: "8px 16px",
              fontSize: 14,
              color: country === code ? "#fff" : "#6f8a95",
              cursor: "pointer",
              fontFamily: theme.sans,
              fontWeight: country === code ? 600 : 400,
              transition: "all 0.15s",
            }}
          >
            {info.name}
          </button>
        ))}
      </div>
      <div style={{
        background: "#16222a",
        border: `1px solid #1e2d35`,
        borderRadius: 12,
        padding: "14px 18px",
        display: "flex",
        flexDirection: "column",
        gap: 4,
        marginBottom: 24,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: "#dce5e9" }}>{current.name}</span>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95" }}>· {current.source}</span>
        </div>
        <div style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95" }}>{current.description}</div>
        <div style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint }}>{current.rating_info}</div>
      </div>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState("hospitals");
  const [country, setCountry] = useState("US");
  const ciStatus = useCIStatus();
  const ciColor = ciStatus === "success" ? theme.mint : ciStatus === "failure" ? "#ff6b6b" : "#6f8a95";
  const ciLabel = ciStatus === "success" ? "CI passing" : ciStatus === "failure" ? "CI failing" : "CI unknown";

  const TABS = [
  { id: "hospitals", label: country === "BR" ? "Hospitais" : "Hospitals" },
  { id: "analytics", label: "Analytics" },
  { id: "pipeline", label: "Pipeline" },
  { id: "physicians", label: country === "BR" ? "Médicos" : "Physicians" },
];

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
            <div style={{ fontSize: 11, color: theme.muted, fontFamily: theme.mono }}>Global Hospital Quality Data</div>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1400, margin: "0 auto", padding: "32px 40px" }}>

        {/* Country Selector */}
        <CountrySelector country={country} onChange={setCountry} />

        {/* AI Query */}
        <AIQuery country={country} />

        {/* Metric cards */}
        <div style={{ display: "flex", gap: 12, marginTop: 24, flexWrap: "wrap" }}>
          <MetricCard label="Facilities" value={country === "US" ? "5,419" : "7,680"} accent={theme.mint} />
          <MetricCard label="Avg Rating" value={country === "US" ? "3.21 ★" : "No rating"} accent="#f1c40f" />
          <MetricCard label="Completeness" value={country === "US" ? "58.6%" : "Structural data"} accent="#dce5e9" />
          <MetricCard label="CI Status" value={ciLabel} accent={ciColor} />
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 4, marginTop: 36, borderRadius: 12, padding: "4px", width: "fit-content" }}>
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
              <HospitalsNearMe country={country} />
              <RatingChart country={country} />
              <DataQuality country={country} />
              <HospitalList country={country} />
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
              <PhysicianAnalysis country={country}/>
              <ScarceSpecialties country={country}/>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
import React, { useEffect, useState } from "react";
import AIQuery from "./components/AIQuery";
import HospitalList from "./components/HospitalList";
import RatingChart from "./components/RatingChart";
import PhysicianAnalysis from "./components/PhysicianAnalysis";
import ScarceSpecialties from "./components/ScarceSpecialties";
import PipelineRuns from "./components/PipelineRuns";
import RatingTrend from "./components/RatingTrend";
import { theme } from "./theme";

function CIBadge() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    function fetchStatus() {
      fetch("https://api.github.com/repos/rafael-ceotto/DataPulse/actions/runs?per_page=1")
        .then((r) => r.json())
        .then((data) => {
          const run = data.workflow_runs?.[0];
          if (run) setStatus(run.conclusion);
        })
        .catch(() => setStatus(null));
    }

    fetchStatus();
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const color = status === "success" ? "#2f9e6f" : status === "failure" ? "#c0392b" : "#6f8a95";
  const label = status === "success" ? "CI passing" : status === "failure" ? "CI failing" : "CI unknown";

  return (
    <>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: color }} />
      <span>5,419 facilities · {label}</span>
    </>
  );
}

function Header() {
  return (
    <header style={{ background: theme.surface, borderBottom: `1px solid #e3e7ea` }}>
      <div
        style={{
          maxWidth: 1160,
          margin: "0 auto",
          padding: "22px 28px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 20,
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 11,
              background: theme.accent,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 3,
            }}
          >
            {[10, 18, 13].map((h, i) => (
              <span
                key={i}
                style={{
                  display: "block",
                  width: 3,
                  height: h,
                  borderRadius: 2,
                  background: "#fff",
                  animation: `dp-pulse 1.4s ease-in-out ${i * 0.2}s infinite`,
                }}
              />
            ))}
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", lineHeight: 1.1 }}>DataPulse</div>
            <div style={{ fontSize: 13, color: theme.muted, marginTop: 3 }}>CMS Hospital Quality Data</div>
          </div>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontFamily: theme.mono,
            fontSize: 11,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: theme.muted,
          }}
        >
          <CIBadge />
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div style={{ minHeight: "100vh", background: theme.bg, color: theme.ink, fontFamily: theme.sans, paddingBottom: 72 }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
        body { margin: 0; background: ${theme.bg}; }
        a { color: ${theme.accent}; text-decoration: none; }
        a:hover { color: #0b566c; text-decoration: underline; }
        input, button { font-family: inherit; }
        @keyframes dp-pulse { 0%,100% { opacity: .25; transform: scaleY(.5); } 50% { opacity: 1; transform: scaleY(1); } }
      `}</style>
      <Header />
      <main style={{ maxWidth: 1160, margin: "0 auto", padding: 28 }}>
        <AIQuery />
        <RatingChart />
        <RatingTrend />
        <PhysicianAnalysis />
        <ScarceSpecialties />
        <PipelineRuns />
        <HospitalList />
      </main>
    </div>
  );
}
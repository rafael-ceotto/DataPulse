import React, { useState, useEffect } from "react";
import { theme } from "../theme";

const US_STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
  "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
  "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
  "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
  "DC","PR","GU","VI"
];

function ScarcityBar({ ratio }) {
  const pct = Math.min(ratio * 100, 100);
  const color = ratio < 0.25 ? "#c0392b" : ratio < 0.4 ? "#e67e22" : "#f1c40f";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, background: "#1b272e", borderRadius: 4, height: 6, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4 }} />
      </div>
      <span style={{ fontFamily: theme.mono, fontSize: 11, color, minWidth: 36 }}>
        {(ratio * 100).toFixed(0)}%
      </span>
    </div>
  );
}

function StatusDot({ ready, loading, label }) {
  const color = loading ? "#f1c40f" : ready ? "#2f9e6f" : "#6f8a95";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, display: "block", flexShrink: 0 }} />
      <span style={{ fontSize: 13, color: "#dce5e9" }}>{label}</span>
    </div>
  );
}

export default function ScarceSpecialties() {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState("OH");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cacheReady, setCacheReady] = useState(null);
  const [warmingUp, setWarmingUp] = useState(false);
  const [stateCacheReady, setStateCacheReady] = useState(false);

  useEffect(() => {
    if (!open) return;
    fetch("/api/v1/physicians/cache-status")
      .then(r => r.json())
      .then(d => setCacheReady(d.national_specialty_cache === "ready"));
  }, [open]);

  // Poll cache status while warming up
  useEffect(() => {
    if (!warmingUp || cacheReady) return;
    const interval = setInterval(() => {
      fetch("/api/v1/physicians/cache-status")
        .then(r => r.json())
        .then(d => {
          if (d.national_specialty_cache === "ready") {
            setCacheReady(true);
            setWarmingUp(false);
            clearInterval(interval);
          }
        });
    }, 30000);
    return () => clearInterval(interval);
  }, [warmingUp, cacheReady]);

  useEffect(() => {
    setStateCacheReady(false);
    setData(null);
    setError(null);
  }, [state]);

  async function analyze() {
    setStateCacheReady(false);
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await fetch(`/api/v1/physicians/scarce-specialties/${state}`);

      // Cache not ready — backend started warm-up automatically
      if (res.status === 202) {
        setWarmingUp(true);
        setCacheReady(false);
        setError("Cache is being prepared automatically. This takes 2-5 minutes on first load. The page will update when ready — no action needed.");
        return;
      }

      if (!res.ok) {
        setError("Could not load analysis. Try again.");
        return;
      }

      const json = await res.json();
      setData(json);
      setStateCacheReady(true);
    } catch {
      setError("Could not load analysis. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section style={{ marginTop: 24 }}>
      <div
        onClick={() => setOpen((o) => !o)}
        style={{
          background: theme.dark,
          border: `1px solid #1e2d35`,
          borderRadius: open ? "14px 14px 0 0" : 14,
          padding: "18px 22px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          userSelect: "none",
          boxShadow: "0 18px 40px -24px rgba(16,26,32,.55)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <h2 style={{ margin: 0, fontSize: 17, fontWeight: 600, letterSpacing: "-0.01em", color: "#fff" }}>
            Scarce Specialties
          </h2>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Public health gaps
          </span>
        </div>
        <span style={{ fontSize: 20, color: "#6f8a95", transition: "transform .2s", transform: open ? "rotate(180deg)" : "rotate(0deg)" }}>
          ▾
        </span>
      </div>

      {open && (
        <div style={{
          background: theme.darkSurface,
          border: `1px solid #1e2d35`,
          borderTop: "none",
          borderRadius: "0 0 14px 14px",
          padding: "24px 22px",
          boxShadow: "0 4px 12px rgba(16,26,32,.3)",
        }}>
          {/* Cache status */}
          <div style={{ marginBottom: 20, padding: "14px 16px", background: "#101a20", borderRadius: 10, border: `1px solid #24323a` }}>
            <div style={{ marginBottom: 8 }}>
              <StatusDot
                ready={cacheReady}
                loading={warmingUp}
                label={
                  cacheReady === null ? "Checking national cache..." :
                  warmingUp ? "Preparing national cache (~2-5 min)..." :
                  cacheReady ? "National specialty cache ready" :
                  "National specialty cache not ready"
                }
              />
            </div>
            <StatusDot
              ready={stateCacheReady}
              loading={loading}
              label={
                loading ? `Fetching ${state} physician data from CMS...` :
                stateCacheReady ? `${state} analysis cached` :
                "State data not yet analyzed"
              }
            />
            {warmingUp && !cacheReady && (
              <div style={{ marginTop: 8, fontSize: 12, color: "#6f8a95" }}>
                Building in background. Page will update automatically when ready.
              </div>
            )}
          </div>

          {/* Controls */}
          <div style={{ display: "flex", gap: 10, marginBottom: 24, flexWrap: "wrap" }}>
            <select
              value={state}
              onChange={(e) => setState(e.target.value)}
              style={{
                background: "#1b272e",
                border: `1px solid #2c3b44`,
                borderRadius: 10,
                padding: "11px 14px",
                fontSize: 14,
                color: "#fff",
                outline: "none",
                cursor: "pointer",
              }}
            >
              {US_STATES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button
              onClick={analyze}
              disabled={loading || warmingUp}
              style={{
                background: !loading && !warmingUp ? theme.mint : "#1b272e",
                color: !loading && !warmingUp ? "#0c1418" : "#6f8a95",
                border: "none",
                borderRadius: 10,
                padding: "11px 24px",
                fontSize: 14,
                fontWeight: 600,
                cursor: loading || warmingUp ? "not-allowed" : "pointer",
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? "Analyzing..." : warmingUp ? "Warming up..." : "Analyze"}
            </button>
          </div>

          {error && (
            <div style={{ color: warmingUp ? "#f1c40f" : "#ff6b6b", fontSize: 14, marginBottom: 16, padding: "12px 16px", background: warmingUp ? "#1a1500" : "#1a1010", borderRadius: 10, border: `1px solid ${warmingUp ? "#3a3000" : "#3a1a1a"}` }}>
              {warmingUp ? "⏳" : "⚠"} {error}
            </div>
          )}

          {data && (
            <>
              <div style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 14 }}>
                Top 10 scarce specialties — {state} · scarcity ratio vs national average
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {data.map((item, i) => (
                  <div
                    key={i}
                    style={{
                      background: "#101a20",
                      border: `1px solid #24323a`,
                      borderRadius: 12,
                      padding: "16px 18px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 10 }}>
                      <div>
                        <div style={{ fontSize: 14.5, fontWeight: 600, color: "#fff", marginBottom: 4 }}>
                          {item.specialty}
                        </div>
                        <div style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95" }}>
                          {item.state_count.toLocaleString()} in {state} · {item.national_count.toLocaleString()} nationally
                        </div>
                      </div>
                      <div style={{ textAlign: "right", flexShrink: 0 }}>
                        <div style={{ fontFamily: theme.mono, fontSize: 13, color: "#c0392b", fontWeight: 600 }}>
                          +{item.gap.toLocaleString()} needed
                        </div>
                        <div style={{ fontFamily: theme.mono, fontSize: 10.5, color: "#6f8a95", marginTop: 2 }}>
                          {item.state_share_pct}% vs {item.expected_share_pct}% expected
                        </div>
                      </div>
                    </div>
                    <ScarcityBar ratio={item.scarcity_ratio} />
                  </div>
                ))}
              </div>
            </>
          )}

          {!data && !loading && !error && (
            <div style={{ textAlign: "center", color: "#6f8a95", fontSize: 14, padding: "32px 0" }}>
              Select a state and click Analyze.
            </div>
          )}
        </div>
      )}
    </section>
  );
}
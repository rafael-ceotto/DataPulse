import React, { useEffect, useState } from "react";
import { theme } from "../theme";
import { getToken } from "../services/api";

export default function DataQuality() {
  const [open, setOpen] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    getToken().then((token) => {
      fetch("/api/v1/hospitals/data-quality", {
        headers: { "Authorization": `Bearer ${token}` },
      })
        .then((r) => r.json())
        .then((data) => { setMetrics(data); setLoading(false); });
    });
  }, [open]);

  function MetricCard({ label, value, sub, color = "#dce5e9", alert = false }) {
    return (
      <div style={{
        background: alert ? "#1a0a0a" : theme.darkInput,
        border: `1px solid ${alert ? "#c0392b44" : "#1e2d35"}`,
        borderRadius: 12,
        padding: "18px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}>
        <div style={{ fontFamily: theme.mono, fontSize: 10.5, letterSpacing: "0.07em", textTransform: "uppercase", color: "#6f8a95" }}>
          {label}
        </div>
        <div style={{ fontSize: 28, fontWeight: 700, color: alert ? "#c0392b" : color, letterSpacing: "-0.02em" }}>
          {value ?? "—"}
        </div>
        {sub && (
          <div style={{ fontSize: 12, color: "#6f8a95" }}>{sub}</div>
        )}
      </div>
    );
  }

  function ProgressBar({ pct }) {
    return (
      <div style={{ marginTop: 4 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ fontFamily: theme.mono, fontSize: 10.5, letterSpacing: "0.07em", textTransform: "uppercase", color: "#6f8a95" }}>
            Data Completeness
          </span>
          <span style={{ fontFamily: theme.mono, fontSize: 12, color: pct >= 80 ? "#2f9e6f" : "#f0a500" }}>
            {pct}%
          </span>
        </div>
        <div style={{ background: "#1e2d35", borderRadius: 999, height: 6, overflow: "hidden" }}>
          <div style={{
            height: "100%",
            width: `${pct}%`,
            background: pct >= 80 ? "#2f9e6f" : "#f0a500",
            borderRadius: 999,
            transition: "width 0.6s ease",
          }} />
        </div>
      </div>
    );
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
            Data Quality
          </h2>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Health Metrics
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
          {loading ? (
            <div style={{ textAlign: "center", color: "#6f8a95", padding: 40 }}>Loading...</div>
          ) : metrics ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <ProgressBar pct={metrics.completeness_pct} />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 14 }}>
                <MetricCard
                  label="Total Hospitals"
                  value={metrics.total_hospitals?.toLocaleString() ?? "—"}
                  sub="CMS facilities in dataset"
                  color="#dce5e9"
                />
                <MetricCard
                  label="Rated Hospitals"
                  value={metrics.rated_hospitals?.toLocaleString() ?? "—"}
                  sub="Have an overall star rating"
                  color="#2f9e6f"
                />
                <MetricCard
                  label="Unrated Hospitals"
                  value={metrics.unrated_hospitals?.toLocaleString() ?? "—"}
                  sub="Missing overall rating"
                  color="#f0a500"
                  alert={metrics.unrated_hospitals > 500}
                />
                <MetricCard
                  label="Low Rated (≤2★)"
                  value={metrics.low_rated_hospitals?.toLocaleString() ?? "—"}
                  sub="Rated 1 or 2 stars"
                  color="#c0392b"
                  alert={metrics.low_rated_hospitals > 0}
                />
                <MetricCard
                  label="Missing Phone"
                  value={metrics.missing_phone?.toLocaleString() ?? "0"}
                  sub="No telephone number"
                  color="#6f8a95"
                />
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", color: "#6f8a95", padding: 40 }}>No data available.</div>
          )}
        </div>
      )}
    </section>
  );
}
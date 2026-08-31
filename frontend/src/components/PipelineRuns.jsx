import React, { useEffect, useState } from "react";
import { theme } from "../theme";

const STATUS_COLOR = {
  success: "#2f9e6f",
  failed: "#c0392b",
  running: theme.mint,
};

export default function PipelineRuns() {
  const [runs, setRuns] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    fetch("/api/v1/pipeline/runs?limit=20")
      .then((r) => r.json())
      .then((data) => { setRuns(data); setLoading(false); });
  }, [open]);

  function toggleInsight(id) {
    setExpandedId((prev) => (prev === id ? null : id));
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
            Pipeline Runs
          </h2>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Execution history
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
          ) : runs.length === 0 ? (
            <div style={{ textAlign: "center", color: "#6f8a95", padding: 40 }}>No pipeline runs found.</div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{
                    fontFamily: theme.mono,
                    fontSize: 10.5,
                    letterSpacing: "0.07em",
                    textTransform: "uppercase",
                    color: "#6f8a95",
                  }}>
                    <th style={{ padding: "10px 14px", textAlign: "left", borderBottom: `1px solid #1e2d35` }}>Started</th>
                    <th style={{ padding: "10px 14px", textAlign: "left", borderBottom: `1px solid #1e2d35` }}>Status</th>
                    <th style={{ padding: "10px 14px", textAlign: "right", borderBottom: `1px solid #1e2d35` }}>Received</th>
                    <th style={{ padding: "10px 14px", textAlign: "right", borderBottom: `1px solid #1e2d35` }}>Processed</th>
                    <th style={{ padding: "10px 14px", textAlign: "right", borderBottom: `1px solid #1e2d35` }}>Failed</th>
                    <th style={{ padding: "10px 14px", textAlign: "right", borderBottom: `1px solid #1e2d35` }}>Duration</th>
                    <th style={{ padding: "10px 14px", textAlign: "center", borderBottom: `1px solid #1e2d35` }}>Insight</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((r, i) => (
                    <React.Fragment key={r.id}>
                      <tr style={{ background: i % 2 === 0 ? "transparent" : "#111e24" }}>
                        <td style={{ padding: "12px 14px", color: "#dce5e9" }}>
                          {new Date(r.started_at).toLocaleString()}
                        </td>
                        <td style={{ padding: "12px 14px" }}>
                          <span style={{
                            fontFamily: theme.mono,
                            fontSize: 11,
                            letterSpacing: "0.06em",
                            textTransform: "uppercase",
                            color: STATUS_COLOR[r.status] ?? "#6f8a95",
                            border: `1px solid ${STATUS_COLOR[r.status] ?? "#6f8a95"}`,
                            borderRadius: 999,
                            padding: "3px 10px",
                          }}>
                            {r.status}
                          </span>
                        </td>
                        <td style={{ padding: "12px 14px", textAlign: "right", fontFamily: theme.mono, color: "#dce5e9" }}>
                          {r.records_received.toLocaleString()}
                        </td>
                        <td style={{ padding: "12px 14px", textAlign: "right", fontFamily: theme.mono, color: "#2f9e6f" }}>
                          {r.records_processed.toLocaleString()}
                        </td>
                        <td style={{ padding: "12px 14px", textAlign: "right", fontFamily: theme.mono, color: r.records_failed > 0 ? "#c0392b" : "#6f8a95" }}>
                          {r.records_failed.toLocaleString()}
                        </td>
                        <td style={{ padding: "12px 14px", textAlign: "right", fontFamily: theme.mono, color: "#a7b6bf" }}>
                          {r.duration_seconds != null ? `${r.duration_seconds}s` : "—"}
                        </td>
                        <td style={{ padding: "12px 14px", textAlign: "center" }}>
                          {r.insight ? (
                            <button
                              onClick={() => toggleInsight(r.id)}
                              style={{
                                background: "transparent",
                                border: `1px solid ${expandedId === r.id ? theme.mint : "#2c3b44"}`,
                                color: expandedId === r.id ? theme.mint : "#6f8a95",
                                borderRadius: 999,
                                padding: "3px 10px",
                                fontSize: 11,
                                fontFamily: theme.mono,
                                cursor: "pointer",
                                letterSpacing: "0.06em",
                                textTransform: "uppercase",
                              }}
                            >
                              {expandedId === r.id ? "hide" : "view"}
                            </button>
                          ) : (
                            <span style={{ color: "#2c3b44", fontFamily: theme.mono, fontSize: 11 }}>—</span>
                          )}
                        </td>
                      </tr>
                      {expandedId === r.id && r.insight && (
                        <tr style={{ background: "#0d1a20" }}>
                          <td colSpan={7} style={{ padding: "16px 20px" }}>
                            <div style={{
                              display: "flex",
                              alignItems: "flex-start",
                              gap: 12,
                            }}>
                              <span style={{
                                fontFamily: theme.mono,
                                fontSize: 10.5,
                                letterSpacing: "0.07em",
                                textTransform: "uppercase",
                                color: theme.mint,
                                whiteSpace: "nowrap",
                                marginTop: 2,
                              }}>
                                ✦ insight
                              </span>
                              <p style={{
                                margin: 0,
                                fontSize: 13.5,
                                lineHeight: 1.6,
                                color: "#dce5e9",
                              }}>
                                {r.insight}
                              </p>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
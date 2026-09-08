import React, { useEffect, useState } from "react";
import { theme } from "../theme";
import { getToken } from "../services/api";

export default function PipelineRuns() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState(null);
  const [runSuccess, setRunSuccess] = useState(null);
  const [open, setOpen] = useState(false);
  const [expandedInsight, setExpandedInsight] = useState(null);

  useEffect(() => {
    if (!open) return;
    fetchRuns();
  }, [open]);

  async function fetchRuns() {
    setLoading(true);
    try {
      const token = await getToken();
      const res = await fetch("/api/v1/pipeline/runs?limit=20", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setRuns(Array.isArray(data) ? data : []);
    } catch {
      setRuns([]);
    } finally {
      setLoading(false);
    }
  }

  async function runPipeline() {
    setRunning(true);
    setRunError(null);
    setRunSuccess(null);
    try {
      const token = await getToken();
      const res = await fetch("/api/v1/pipeline/run", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Pipeline failed");
      const data = await res.json();
      setRunSuccess(`Pipeline completed — ${data.processed?.toLocaleString()} records processed`);
      await fetchRuns();
    } catch {
      setRunError("Pipeline run failed. Try again.");
    } finally {
      setRunning(false);
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

          {/* Run Pipeline button */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
            <button
              onClick={(e) => { e.stopPropagation(); runPipeline(); }}
              disabled={running}
              style={{
                background: running ? "#1b272e" : theme.mint,
                color: running ? "#6f8a95" : "#0c1418",
                border: "none",
                borderRadius: 10,
                padding: "11px 24px",
                fontSize: 14,
                fontWeight: 600,
                cursor: running ? "not-allowed" : "pointer",
                opacity: running ? 0.7 : 1,
              }}
            >
              {running ? "Running..." : "▶ Run Pipeline"}
            </button>
            {runSuccess && (
              <span style={{ fontSize: 13, color: theme.mint }}>
                ✓ {runSuccess}
              </span>
            )}
            {runError && (
              <span style={{ fontSize: 13, color: "#ff6b6b" }}>
                ⚠ {runError}
              </span>
            )}
          </div>

          {/* Runs table */}
          {loading ? (
            <div style={{ color: "#6f8a95", fontSize: 14 }}>Loading...</div>
          ) : runs.length === 0 ? (
            <div style={{ color: "#6f8a95", fontSize: 14 }}>No pipeline runs yet.</div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid #1e2d35` }}>
                    {["Started", "Status", "Received", "Processed", "Failed", "Duration", "Insight"].map((h) => (
                      <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontFamily: theme.mono, fontSize: 10, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", fontWeight: 500 }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run) => (
                    <tr key={run.id} style={{ borderBottom: `1px solid #1a252c` }}>
                      <td style={{ padding: "10px 12px", color: "#dce5e9" }}>
                        {run.started_at ? new Date(run.started_at).toLocaleString() : "—"}
                      </td>
                      <td style={{ padding: "10px 12px" }}>
                        <span style={{
                          fontFamily: theme.mono,
                          fontSize: 11,
                          padding: "3px 8px",
                          borderRadius: 6,
                          background: run.status === "success" ? "#0f2a1a" : run.status === "running" ? "#1a1a0f" : "#2a0f0f",
                          color: run.status === "success" ? theme.mint : run.status === "running" ? "#f1c40f" : "#ff6b6b",
                          border: `1px solid ${run.status === "success" ? "#1a4a2a" : run.status === "running" ? "#3a3a1a" : "#4a1a1a"}`,
                        }}>
                          {run.status?.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: "#dce5e9" }}>
                        {run.records_received?.toLocaleString() ?? "—"}
                      </td>
                      <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: theme.mint }}>
                        {run.records_processed?.toLocaleString() ?? "—"}
                      </td>
                      <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: run.records_failed > 0 ? "#ff6b6b" : "#6f8a95" }}>
                        {run.records_failed ?? "—"}
                      </td>
                      <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: "#6f8a95" }}>
                        {run.duration_seconds ? `${run.duration_seconds}s` : "—"}
                      </td>
                      <td style={{ padding: "10px 12px" }}>
                        {run.insight ? (
                          <button
                            onClick={() => setExpandedInsight(expandedInsight === run.id ? null : run.id)}
                            style={{ background: "#1b272e", border: `1px solid #2c3b44`, borderRadius: 6, padding: "4px 10px", fontSize: 11, color: "#dce5e9", cursor: "pointer", fontFamily: theme.mono }}
                          >
                            {expandedInsight === run.id ? "HIDE" : "VIEW"}
                          </button>
                        ) : (
                          <span style={{ color: "#6f8a95", fontFamily: theme.mono, fontSize: 11 }}>—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {expandedInsight && (
                <div style={{ marginTop: 16, padding: "16px 18px", background: "#101a20", borderRadius: 10, border: `1px solid #24323a` }}>
                  <div style={{ fontFamily: theme.mono, fontSize: 10, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 8 }}>
                    AI Insight
                  </div>
                  <div style={{ fontSize: 13, color: "#dce5e9", lineHeight: 1.6 }}>
                    {runs.find((r) => r.id === expandedInsight)?.insight}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
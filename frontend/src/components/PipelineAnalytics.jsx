import React, { useEffect, useState } from "react";
import { theme } from "../theme";

export default function PipelineAnalytics() {
  const [open, setOpen] = useState(false);
  const [trend, setTrend] = useState(null);
  const [changes, setChanges] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    Promise.all([
      fetch("/api/v1/analytics/rating-trend").then((r) => r.json()),
      fetch("/api/v1/analytics/rating-changes").then((r) => r.json()),
    ]).then(([trendData, changesData]) => {
      setTrend(trendData);
      setChanges(changesData);
      setLoading(false);
    });
  }, [open]);

  function shortId(id) {
    return id ? id.split("-")[0] : "—";
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
            Pipeline Analytics
          </h2>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Data Lake Insights
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
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>

              {/* Rating Trend */}
              <div>
                <div style={{ fontFamily: theme.mono, fontSize: 10.5, letterSpacing: "0.07em", textTransform: "uppercase", color: "#6f8a95", marginBottom: 14 }}>
                  Average Rating per Pipeline Run
                </div>
                {trend && trend.length > 0 ? (
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                      <thead>
                        <tr style={{ borderBottom: `1px solid #1e2d35` }}>
                          {["Run ID", "Avg Rating", "Total Hospitals", "Rated"].map((h) => (
                            <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontFamily: theme.mono, fontSize: 10, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", fontWeight: 500 }}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {trend.map((row, i) => (
                          <tr key={i} style={{ borderBottom: `1px solid #1a252c` }}>
                            <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: "#6f8a95" }}>
                              {shortId(row.run_id)}...
                            </td>
                            <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 13, color: theme.mint, fontWeight: 600 }}>
                              {row.avg_rating}
                            </td>
                            <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: "#dce5e9" }}>
                              {row.total_hospitals?.toLocaleString()}
                            </td>
                            <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: "#dce5e9" }}>
                              {row.rated_hospitals?.toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ color: "#6f8a95", fontSize: 13 }}>No pipeline runs in S3 yet.</div>
                )}
              </div>

              {/* Rating Changes */}
              <div>
                <div style={{ fontFamily: theme.mono, fontSize: 10.5, letterSpacing: "0.07em", textTransform: "uppercase", color: "#6f8a95", marginBottom: 14 }}>
                  Rating Changes by State Across Runs
                </div>
                {changes && changes.length > 0 ? (
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                      <thead>
                        <tr style={{ borderBottom: `1px solid #1e2d35` }}>
                          {["State", "First Run", "Last Run", "Delta", "Runs"].map((h) => (
                            <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontFamily: theme.mono, fontSize: 10, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", fontWeight: 500 }}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {changes.map((row, i) => (
                          <tr key={i} style={{ borderBottom: `1px solid #1a252c` }}>
                            <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: "#dce5e9", fontWeight: 600 }}>
                              {row.state}
                            </td>
                            <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: "#dce5e9" }}>
                              {row.first_rating}
                            </td>
                            <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: "#dce5e9" }}>
                              {row.last_rating}
                            </td>
                            <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: row.delta > 0 ? theme.mint : row.delta < 0 ? "#c0392b" : "#6f8a95", fontWeight: 600 }}>
                              {row.delta > 0 ? `+${row.delta}` : row.delta}
                            </td>
                            <td style={{ padding: "10px 12px", fontFamily: theme.mono, fontSize: 12, color: "#6f8a95" }}>
                              {row.num_runs}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ color: "#6f8a95", fontSize: 13 }}>No changes detected across runs.</div>
                )}
              </div>

            </div>
          )}
        </div>
      )}
    </section>
  );
}
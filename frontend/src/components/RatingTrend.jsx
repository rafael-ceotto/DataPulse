import React, { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { theme } from "../theme";
import { getToken } from "../services/api";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export default function RatingTrend() {
  const [runs, setRuns] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    getToken().then((token) => {
      fetch("/api/v1/pipeline/runs?limit=50", {
        headers: { "Authorization": `Bearer ${token}` },
      })
        .then((r) => r.json())
        .then((data) => {
          const filtered = data
            .filter((r) => r.avg_rating != null && r.status === "success")
            .reverse();
          setRuns(filtered);
        });
    });
  }, [open]);

  const chartData = {
    labels: runs.map((r) =>
      new Date(r.started_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })
    ),
    datasets: [
      {
        label: "Avg Hospital Rating",
        data: runs.map((r) => r.avg_rating),
        borderColor: theme.mint,
        backgroundColor: "rgba(47, 158, 111, 0.08)",
        pointBackgroundColor: theme.mint,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2,
        tension: 0.3,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => `Avg Rating: ${ctx.raw}`,
          title: (items) => {
            const run = runs[items[0].dataIndex];
            return new Date(run.started_at).toLocaleString();
          },
        },
      },
    },
    scales: {
      y: {
        min: 1,
        max: 5,
        ticks: { color: "#6f8a95" },
        grid: { color: "#1e2d35" },
        title: {
          display: true,
          text: "Rating (1–5)",
          color: "#6f8a95",
          font: { size: 11 },
        },
      },
      x: {
        ticks: { color: "#6f8a95", font: { size: 11 } },
        grid: { display: false },
      },
    },
  };

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
            Rating Trend
          </h2>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Over time
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
          {runs.length === 0 ? (
            <div style={{ textAlign: "center", color: "#6f8a95", padding: 40 }}>
              No trend data yet — run the pipeline a few times to see the chart.
            </div>
          ) : (
            <div style={{ height: 340 }}>
              <Line data={chartData} options={options} />
            </div>
          )}
        </div>
      )}
    </section>
  );
}
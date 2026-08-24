import React, { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import { theme } from "../theme";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function RatingChart() {
  const [data, setData] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    fetch("/api/v1/hospitals/metrics/rating-distribution")
      .then((r) => r.json())
      .then(setData);
  }, [open]);

  const chartData = {
    labels: data.map((d) => d.state),
    datasets: [
      {
        label: "Average Rating",
        data: data.map((d) => d.avg_rating),
        backgroundColor: data.map((d) =>
          d.avg_rating >= 4
            ? "#2f9e6f"
            : d.avg_rating >= 3
            ? theme.accent
            : "#c0392b"
        ),
        borderRadius: 6,
        borderSkipped: false,
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
          label: (ctx) => {
            const d = data[ctx.dataIndex];
            return [`Avg Rating: ${ctx.raw}`, `Hospitals: ${d.total}`];
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
            Average Rating by State
          </h2>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Quality metrics
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
          <div style={{ display: "flex", gap: 20, marginBottom: 16, fontFamily: theme.mono, fontSize: 11, letterSpacing: "0.06em" }}>
            {[
              { color: "#2f9e6f", label: "≥ 4.0 Excellent" },
              { color: theme.accent, label: "≥ 3.0 Good" },
              { color: "#c0392b", label: "< 3.0 Below average" },
            ].map(({ color, label }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 6, color: "#6f8a95" }}>
                <span style={{ width: 10, height: 10, borderRadius: 3, background: color, display: "block" }} />
                {label}
              </div>
            ))}
          </div>

          {data.length > 0 ? (
            <div style={{ overflowX: "auto" }}>
              <div style={{ minWidth: data.length * 28, height: 400 }}>
                <Bar data={chartData} options={options} />
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", color: "#6f8a95", padding: 40 }}>Loading...</div>
          )}
        </div>
      )}
    </section>
  );
}
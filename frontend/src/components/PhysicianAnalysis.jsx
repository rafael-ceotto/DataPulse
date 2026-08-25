import React, { useState } from "react";
import { theme } from "../theme";

const US_STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
  "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
  "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
  "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
  "DC","PR","GU","VI"
];

export default function PhysicianAnalysis(){
    const [open, setOpen] = useState(false);
    const [state, setState] =  useState("OH");
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    async function analyze(){
        setLoading(true);
        setError(null);
        setData(null);
        try{
            const res = await fetch(`/api/v1/physicians/state-analysis/${state}`);
            if(!res.ok) throw new Error("Failed to fetch data");
            setData(await res.json());
        } catch(e){
            setError("Could not load analysis. Try again");
        } finally{
            setLoading(false);
        }
    }

    const metrics = data ? [
        { label: "State", value: data.state},
        { label: "Physicians", value: data.physician_count?.toLocaleString()},
        { label: "Hospitals", value: data.hospital_count?.toLocaleString()},
        { label: "Avg Hospital Rating", value: data.avg_hospital_rating ? `${data.avg_hospital_rating} / 5` : "—" },
        { label: "Physicians per Hospital", value: data.physicians_per_hospital?.toLocaleString() },
        
    ] : [];

    const ratingColor = (rating) => {
        if(!rating) return "#6f8a95";
        if(rating >= 4) return "#2f9e6f";
        if(rating >=3) return theme.accent;
        return "#c0392b";
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
            Physician & Hospital Analysis
          </h2>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            By state
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
              disabled={loading}
              style={{
                background: theme.mint,
                color: "#0c1418",
                border: "none",
                borderRadius: 10,
                padding: "11px 24px",
                fontSize: 14,
                fontWeight: 600,
                cursor: loading ? "wait" : "pointer",
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? "Loading..." : "Analyze"}
            </button>
          </div>

          {error && (
            <div style={{ color: "#ff6b6b", fontSize: 14, marginBottom: 16 }}>{error}</div>
          )}

          {data && (
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: 12,
            }}>
              {metrics.map(({ label, value }) => (
                <div
                  key={label}
                  style={{
                    background: "#101a20",
                    border: `1px solid #24323a`,
                    borderRadius: 12,
                    padding: "16px 18px",
                  }}
                >
                  <div style={{ fontFamily: theme.mono, fontSize: 10.5, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 8 }}>
                    {label}
                  </div>
                  <div style={{
                    fontSize: 20,
                    fontWeight: 700,
                    color: label === "Avg Hospital Rating"
                      ? ratingColor(data.avg_hospital_rating)
                      : "#fff",
                    fontFamily: label !== "State" ? theme.mono : theme.sans,
                  }}>
                    {value}
                  </div>
                </div>
              ))}
            </div>
          )}

          {!data && !loading && !error && (
            <div style={{ textAlign: "center", color: "#6f8a95", fontSize: 14, padding: "32px 0" }}>
              Select a state and click Analyze to see the physician-hospital correlation.
            </div>
          )}
        </div>
      )}
    </section>
  );    
    
}
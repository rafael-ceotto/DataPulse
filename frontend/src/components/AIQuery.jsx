import React, { useState } from "react";
import { theme } from "../theme";
import { askAI } from "../services/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const SUGGESTIONS = [
  "Which hospitals have a 5-star rating?",
  "Average rating by state",
  "Show me the lowest-rated facilities",
  "What states have the highest concentration of 5-star hospitals?",
];

const label = {
  fontFamily: theme.mono,
  fontSize: 11,
  letterSpacing: "0.07em",
  textTransform: "uppercase",
  color: "#6f8a95",
  marginBottom: 10,
};

const grid = { display: "grid", gridTemplateColumns: "2.4fr 1.4fr 0.8fr", gap: 12 };

export default function AIQuery() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function clear() {
    setAnswer(null);
    setQuery("");
    setError(null);
  }

  async function ask(text = query) {
    const q = text.trim();
    if (!q) return;
    setQuery(q);
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const data = await askAI(q);
      setAnswer(data);
    } catch (err) {
      setError("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section
      style={{
        background: theme.dark,
        borderRadius: 18,
        padding: 28,
        boxShadow: "0 18px 40px -24px rgba(16,26,32,.55)",
      }}
    >
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap", marginBottom: 18 }}>
        <h2 style={{ margin: 0, fontSize: 17, fontWeight: 600, color: "#fff", letterSpacing: "-0.01em" }}>
          Ask about the data
        </h2>
        <span
          style={{
            fontFamily: theme.mono,
            fontSize: 11,
            color: theme.mint,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
          }}
        >
          AI query
        </span>
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask()}
          placeholder="e.g. Which hospitals in Ohio have a 5-star rating?"
          style={{
            flex: "1 1 320px",
            minWidth: 0,
            background: theme.darkInput,
            border: `1px solid #2c3b44`,
            borderRadius: 11,
            padding: "14px 16px",
            fontSize: 15,
            color: "#fff",
            outline: "none",
          }}
        />
        <button
          onClick={() => ask()}
          disabled={loading || !query.trim()}
          style={{
            background: theme.mint,
            color: "#0c1418",
            border: "none",
            borderRadius: 11,
            padding: "14px 26px",
            fontSize: 15,
            fontWeight: 600,
            cursor: loading ? "wait" : "pointer",
            opacity: loading || !query.trim() ? 0.7 : 1,
          }}
        >
          {loading ? "Thinking…" : "Ask"}
        </button>
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 14, alignItems: "center" }}>
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => ask(s)}
            style={{
              background: "transparent",
              border: `1px solid #2c3b44`,
              color: s === "What states have the highest concentration of 5-star hospitals?"
                ? theme.mint
                : "#a7b6bf",
              borderRadius: 999,
              padding: "7px 14px",
              fontSize: 12.5,
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
          >
            {s === "What states have the highest concentration of 5-star hospitals?" ? "✦ " : ""}{s}
          </button>
        ))}
        {(answer || error) && !loading && (
          <button
            onClick={clear}
            style={{
              background: "transparent",
              border: `1px solid #3d5060`,
              color: "#6f8a95",
              borderRadius: 999,
              padding: "7px 14px",
              fontSize: 12.5,
              cursor: "pointer",
              whiteSpace: "nowrap",
              marginLeft: "auto",
            }}
          >
            ✕ Clear
          </button>
        )}
      </div>

      {error && (
        <div style={{ marginTop: 20, color: "#ff6b6b", fontSize: 14 }}>{error}</div>
      )}

      {answer && !loading && (
        <div style={{ marginTop: 24, borderTop: `1px solid ${theme.darkBorder}`, paddingTop: 22 }}>

          {/* Mode badge + tools used */}
          {answer.mode && (
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18, flexWrap: "wrap" }}>
              <span
                style={{
                  fontFamily: theme.mono,
                  fontSize: 10.5,
                  letterSpacing: "0.07em",
                  textTransform: "uppercase",
                  color: answer.mode === "agent" ? theme.mint : "#6f8a95",
                  border: `1px solid ${answer.mode === "agent" ? theme.mint : "#2c3b44"}`,
                  borderRadius: 999,
                  padding: "4px 10px",
                }}
              >
                {answer.mode === "agent" ? "✦ agent" : "sql"}
              </span>
              {answer.mode === "agent" && answer.tools_used?.length > 0 && (
                <span style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95" }}>
                  tools used:{" "}
                  {answer.tools_used.map((t, i) => (
                    <span key={t}>
                      <span style={{ color: "#a7b6bf" }}>{t}</span>
                      {i < answer.tools_used.length - 1 && ", "}
                    </span>
                  ))}
                </span>
              )}
            </div>
          )}

          <div style={{ ...label, textAlign: "center" }}>Explanation</div>
          
          <div
  style={{
    margin: "0 auto 22px",
    fontSize: 15.5,
    lineHeight: 1.6,
    color: "#dce5e9",
    maxWidth: "74ch",
    textAlign: "center",
  }}
>
  <style>{`
    .ai-explanation table {
      border-collapse: collapse;
      margin: 16px auto;
      font-size: 14px;
    }
    .ai-explanation th,
    .ai-explanation td {
      border: 1px solid #2c3b44;
      padding: 8px 16px;
      text-align: center;
    }
    .ai-explanation th {
      background: #1a2a32;
      color: #6f8a95;
      font-family: monospace;
      font-size: 11px;
      letter-spacing: 0.07em;
      text-transform: uppercase;
    }
    .ai-explanation td {
      color: #dce5e9;
    }
    .ai-explanation tr:nth-child(even) td {
      background: #111e24;
    }
    .ai-explanation h2,
    .ai-explanation h3 {
      margin-top: 24px;
      margin-bottom: 8px;
      color: #fff;
      font-size: 15px;
    }
    .ai-explanation ul {
      text-align: left;
      display: inline-block;
      padding-left: 20px;
    }
    .ai-explanation p {
      margin: 8px 0;
    }
  `}</style>
  <div className="ai-explanation">
    <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer.explanation}</ReactMarkdown>
  </div>
</div>

          {answer.results?.length > 0 && (
            <>
              <div style={{ ...label, textAlign: "center" }}>Results · {answer.results.length} records</div>
              <div
                style={{
                  background: theme.darkSurface,
                  border: `1px solid ${theme.darkBorder}`,
                  borderRadius: 12,
                  overflow: "hidden",
                  maxHeight: 400,
                  overflowY: "auto",
                }}
              >
                <div
                  style={{
                    ...grid,
                    padding: "12px 16px",
                    background: theme.darkInput,
                    fontFamily: theme.mono,
                    fontSize: 10.5,
                    letterSpacing: "0.07em",
                    textTransform: "uppercase",
                    color: "#6f8a95",
                    position: "sticky",
                    top: 0,
                    zIndex: 1,
                  }}
                >
                  <span>Facility</span>
                  <span>Location</span>
                  <span style={{ textAlign: "right" }}>Rating</span>
                </div>
                {answer.results.map((r, i) => (
                  <div
                    key={i}
                    style={{
                      ...grid,
                      padding: "13px 16px",
                      borderTop: `1px solid ${theme.darkBorder}`,
                      fontSize: 14,
                      color: "#dce5e9",
                      alignItems: "center",
                    }}
                  >
                    <span style={{ fontWeight: 500 }}>
                      {r.facility_name ?? r.state ?? Object.values(r)[0]}
                    </span>
                    <span style={{ color: "#a7b6bf" }}>
                      {r.city && r.state ? `${r.city}, ${r.state}` : r.state ? "Statewide" : "—"}
                    </span>
                    <span style={{ textAlign: "right", fontFamily: theme.mono, color: theme.mint }}>
                      {r.overall_rating ?? (r.avg_rating ? parseFloat(r.avg_rating).toFixed(2) : null) ?? (r.average_rating ? parseFloat(r.average_rating).toFixed(2) : null) ?? r.num_hospitals ?? "—"}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}
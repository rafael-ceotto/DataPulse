import React, { useState, useCallback } from "react";
import { theme } from "../theme";
import { askAI, saveToNotion } from "../services/api";
import { needsDeviceLocation, getDeviceLocation } from "../services/geolocation";
import { detectMentionedCountry, COUNTRY_LABELS } from "../services/countryDetection";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import TransparencyModal from "./TransparencyModal"

const PLACEHOLDERS = {
  US: "e.g. Which hospitals in Ohio have a 5-star rating?",
  BR: "ex: Quais hospitais em São Paulo têm atendimento de emergência?",
  CA: "e.g. Which hospitals in Ontario have emergency services?",
  GB: "e.g. Which hospitals in London are rated Outstanding?",
  FR: "ex : Quels hôpitaux à Paris ont des services d'urgence ?",
  BE: "ex : Quels hôpitaux à Bruxelles ont des services d'urgence ?",
  PT: "ex: Quais hospitais em Lisboa têm serviço de urgência?",
  ES: "ej: ¿Qué hospitales en Madrid tienen servicio de urgencias?",
  IT: "es: Quali ospedali a Roma hanno il pronto soccorso?",
  MT: "e.g. Which hospitals in Malta have emergency services?",
};

const SUGGESTIONS = {
  US: [
    { text: "Which hospitals have a 5-star rating?" },
    { text: "Average rating by state" },
    { text: "Show me the lowest-rated facilities" },
    { text: "What's the closest hospital near me?", highlight: true },
  ],
  BR: [
    { text: "Quais hospitais têm selo de acreditação?" },
    { text: "Hospitais com atendimento de emergência em São Paulo" },
    { text: "Mostre os hospitais com mais leitos" },
    { text: "Qual hospital mais próximo de mim?", highlight: true },
  ],
  CA: [
    { text: "Which hospitals are in Ontario?" },
    { text: "Show hospitals with emergency services" },
    { text: "List hospitals by type" },
    { text: "What's the nearest hospital to me?", highlight: true },
  ],
  GB: [
    { text: "Which hospitals are rated Outstanding by the CQC?" },
    { text: "Show hospitals rated Good in London" },
    { text: "List NHS hospitals with emergency services" },
    { text: "What's the closest hospital near me?", highlight: true },
  ],
  FR: [
    { text: "Quels hôpitaux ont une certification HAS ?" },
    { text: "Hôpitaux avec services d'urgence à Paris" },
    { text: "Liste des hôpitaux par région" },
    { text: "Quel est l'hôpital le plus proche de moi ?", highlight: true },
  ],
  BE: [
    { text: "Quels hôpitaux se trouvent à Bruxelles ?" },
    { text: "Liste des hôpitaux avec services d'urgence" },
    { text: "Hôpitaux par type d'établissement" },
    { text: "Quel est l'hôpital le plus proche de moi ?", highlight: true },
  ],
  PT: [
    { text: "Quais hospitais têm serviço de urgência?" },
    { text: "Hospitais do SNS em Lisboa" },
    { text: "Lista de hospitais por região" },
    { text: "Qual é o hospital mais próximo de mim?", highlight: true },
  ],
  ES: [
    { text: "¿Qué hospitales tienen servicio de urgencias?" },
    { text: "Hospitales del SNS en Madrid" },
    { text: "Lista de hospitales por comunidad autónoma" },
    { text: "¿Cuál es el hospital más cercano a mí?", highlight: true },
  ],
  IT: [
    { text: "Quali ospedali hanno il pronto soccorso?" },
    { text: "Ospedali del SSN a Roma" },
    { text: "Elenco degli ospedali per regione" },
    { text: "Qual è l'ospedale più vicino a me?", highlight: true },
  ],
  MT: [
    { text: "Which hospitals are in Malta?" },
    { text: "Show hospitals with emergency services" },
    { text: "List all hospitals" },
    { text: "What's the closest hospital near me?", highlight: true },
  ],
};

const label = {
  fontFamily: theme.mono,
  fontSize: 11,
  letterSpacing: "0.07em",
  textTransform: "uppercase",
  color: "#6f8a95",
  marginBottom: 10,
};

const grid = { display: "grid", gridTemplateColumns: "2.4fr 1.4fr 0.8fr", gap: 12 };

function generateConversationId() {
  return crypto.randomUUID();
}

export default function AIQuery({ country = "US", onCountryChange }) {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [conversationId, setConversationId] = useState(() => generateConversationId());
  const [pendingMismatch, setPendingMismatch] = useState(null);
  const [showTransparency, setShowTransparency] = useState(false);

  function clear() {
    setAnswer(null);
    setQuery("");
    setError(null);
    setSaved(false);
    setPendingMismatch(null);
  }

  function newConversation() {
    clear();
    setConversationId(generateConversationId());
  }

    async function ask(text = query) {
    const q = text.trim();
    if (!q) return;
    const mentioned = detectMentionedCountry(q, country);
    if (mentioned) {
      setQuery(q);
      setPendingMismatch({ code: mentioned, text: q });
      return;
    }
    await performAsk(q, country);
  }

  async function performAsk(text, useCountry) {
    const q = text.trim();
    if (!q) return;
    setQuery(q);
    setLoading(true);
    setError(null);
    setAnswer(null);
    setSaved(false);
    setPendingMismatch(null);
    try {
      let lat = null, lng = null;
      if (needsDeviceLocation(q)) {
        const loc = await getDeviceLocation();
        if (loc) { lat = loc.lat; lng = loc.lng; }
      }
      const data = await askAI(q, conversationId, useCountry, lat, lng);
      setAnswer(data);
    } catch (err) {
      console.error("AI query failed:", err);
      setError("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  function confirmSwitchCountry() {
    if (!pendingMismatch) return;
    const { code, text } = pendingMismatch;
    onCountryChange?.(code);
    performAsk(text, code);
  }

  function confirmSendAnyway() {
    if (!pendingMismatch) return;
    performAsk(pendingMismatch.text, country);
  }

  async function handleSaveToNotion() {
    setSaving(true);
    try {
      await saveToNotion(answer.question, answer.explanation, answer.tools_used ?? []);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error("Failed to save to Notion", err);
    } finally {
      setSaving(false);
    }
  }

  const suggestions = SUGGESTIONS[country] || SUGGESTIONS.US;

  return (
    <section
      style={{
        background: theme.dark,
        borderRadius: 18,
        padding: 28,
        boxShadow: "0 18px 40px -24px rgba(16,26,32,.55)",
        width: "100%",
        maxWidth: "100%",
        overflow: "hidden",
        boxSizing: "border-box",
      }}
    >
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap", marginBottom: 18 }}>
        <h2 style={{ margin: 0, fontSize: 17, fontWeight: 600, color: "#fff", letterSpacing: "-0.01em" }}>
          Ask AIDoc
        </h2>
        <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
          AI query
        </span>
        <button
          onClick={() => setShowTransparency(true)}
          style={{
            background: theme.mint, color: "#0c1418", border: "none",
            borderRadius: 999, padding: "6px 14px", fontSize: 12,
            fontWeight: 600, fontFamily: theme.sans, cursor: "pointer",
          }}
        >
          ℹ How our AI works
        </button>
        <button
          onClick={newConversation}
          style={{
            background: "transparent",
            border: `1px solid #2c3b44`,
            color: "#6f8a95",
            borderRadius: 999,
            padding: "4px 12px",
            fontSize: 11,
            fontFamily: theme.mono,
            cursor: "pointer",
            letterSpacing: "0.06em",
            marginLeft: "auto",
          }}
        >
          ↺ New conversation
        </button>
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask()}
          placeholder={PLACEHOLDERS[country] || PLACEHOLDERS.US}
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
        {suggestions.map((s) => (
          <button
            key={s.text}
            onClick={() => ask(s.text)}
            style={{
              background: "transparent",
              border: `1px solid #2c3b44`,
              color: s.highlight ? theme.mint : "#a7b6bf",
              borderRadius: 999,
              padding: "7px 14px",
              fontSize: 12.5,
              cursor: "pointer",
              whiteSpace: "normal",
            }}
          >
            {s.highlight ? "✦ " : ""}{s.text}
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
              whiteSpace: "normal",
              marginLeft: "auto",
            }}
          >
            ✕ Clear
          </button>
        )}
      </div>

      {pendingMismatch && (
        <div style={{
          marginTop: 14,
          padding: "12px 16px",
          background: "#2a2210",
          border: "1px solid #5a4a1a",
          borderRadius: 10,
          display: "flex",
          alignItems: "center",
          gap: 12,
          flexWrap: "wrap",
        }}>
          <span style={{ fontSize: 13.5, color: "#f1d78a", flex: "1 1 260px" }}>
            ⚠ Essa pergunta parece ser sobre <strong>{COUNTRY_LABELS[pendingMismatch.code]}</strong>, mas o país selecionado é <strong>{COUNTRY_LABELS[country]}</strong>.
          </span>
          <button
            onClick={confirmSwitchCountry}
            style={{
              background: theme.mint, color: "#0c1418", border: "none",
              borderRadius: 8, padding: "7px 14px", fontSize: 12.5, fontWeight: 600, cursor: "pointer",
            }}
          >
            Usar {COUNTRY_LABELS[pendingMismatch.code]}
          </button>
          <button
            onClick={confirmSendAnyway}
            style={{
              background: "transparent", color: "#f1d78a", border: "1px solid #5a4a1a",
              borderRadius: 8, padding: "7px 14px", fontSize: 12.5, cursor: "pointer",
            }}
          >
            Enviar mesmo assim
          </button>
        </div>
      )}

      {error && (
        <div style={{ marginTop: 20, color: "#ff6b6b", fontSize: 14 }}>{error}</div>
      )}

      {answer && !loading && (
        <div style={{ marginTop: 24, borderTop: `1px solid ${theme.darkBorder}`, paddingTop: 22 }}>

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

          {answer.explanation && (
            <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 18, flexWrap: "wrap" }}>
              <button
                onClick={handleSaveToNotion}
                disabled={saving || saved}
                style={{
                  background: "transparent",
                  border: `1px solid ${saved ? "#2f9e6f" : "#2c3b44"}`,
                  color: saved ? "#2f9e6f" : "#6f8a95",
                  borderRadius: 999,
                  padding: "5px 14px",
                  fontSize: 12,
                  fontFamily: theme.mono,
                  cursor: saving ? "wait" : "pointer",
                  letterSpacing: "0.06em",
                }}
              >
                {saved ? "✓ Saved to Notion" : saving ? "Saving..." : "↗ Save to Notion"}
              </button>
              {answer.tokens_used?.total > 0 && (
                <span style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95", letterSpacing: "0.04em" }}>
                  {answer.tokens_used.total.toLocaleString()} tokens
                  {answer.estimated_cost_usd > 0 && (
                    <span style={{ marginLeft: 8 }}>· ${answer.estimated_cost_usd.toFixed(6)}</span>
                  )}
                </span>
              )}
              {answer.data_as_of && (
                <span style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95", letterSpacing: "0.04em" }}>
                  📅 Data as of {answer.data_as_of}
                </span>
              )}
            </div>
          )}

          <div style={{ ...label, textAlign: "center" }}>Explanation</div>

          <div style={{ margin: "0 auto 22px", fontSize: 15.5, lineHeight: 1.6, color: "#dce5e9", maxWidth: "74ch", textAlign: "center", overflowX: "auto" }}>
            <style>{`
              .ai-explanation table { border-collapse: collapse; margin: 16px auto; font-size: 14px; max-width: 100; }
              .ai-explanation th, .ai-explanation td { border: 1px solid #2c3b44; padding: 8px 16px; text-align: center; }
              .ai-explanation th { background: #1a2a32; color: #6f8a95; font-family: monospace; font-size: 11px; letter-spacing: 0.07em; text-transform: uppercase; }
              .ai-explanation td { color: #dce5e9; }
              .ai-explanation tr:nth-child(even) td { background: #111e24; }
              .ai-explanation h2, .ai-explanation h3 { margin-top: 24px; margin-bottom: 8px; color: #fff; font-size: 15px; }
              .ai-explanation ul { text-align: left; display: inline-block; padding-left: 20px; }
              .ai-explanation p { margin: 8px 0; }
              .ai-explanation { overflow-x: auto; display: block;}

            `}</style>
            <div className="ai-explanation">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer.explanation}</ReactMarkdown>
            </div>
          </div>

          {answer.results?.length > 0 && (
            <>
              <div style={{ ...label, textAlign: "center" }}>Results · {answer.results.length} records</div>
              <div style={{ background: theme.darkSurface, border: `1px solid ${theme.darkBorder}`, borderRadius: 12, overflow: "hidden", maxHeight: 400, overflowY: "auto" }}>
                <div style={{ ...grid, padding: "12px 16px", background: theme.darkInput, fontFamily: theme.mono, fontSize: 10.5, letterSpacing: "0.07em", textTransform: "uppercase", color: "#6f8a95", position: "sticky", top: 0, zIndex: 1 }}>
                  <span>Facility</span>
                  <span>Location</span>
                  <span style={{ textAlign: "right" }}>Rating</span>
                </div>
                {answer.results.map((r, i) => (
                  <div key={i} style={{ ...grid, padding: "13px 16px", borderTop: `1px solid ${theme.darkBorder}`, fontSize: 14, color: "#dce5e9", alignItems: "center" }}>
                    <span style={{ fontWeight: 500 }}>{r.facility_name ?? r.state ?? Object.values(r)[0]}</span>
                    <span style={{ color: "#a7b6bf" }}>{r.city && r.state ? `${r.city}, ${r.state}` : r.state ? "Statewide" : "—"}</span>
                    <span style={{ textAlign: "right", fontFamily: theme.mono, color: theme.mint }}>
                      {r.overall_rating ?? (r.avg_rating ? parseFloat(r.avg_rating).toFixed(2) : null) ?? (r.average_rating ? parseFloat(r.average_rating).toFixed(2) : null) ?? r.hospital_count ?? r.count ?? r.five_star_hospitals ?? r.num_hospitals ?? "—"}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
      {showTransparency && <TransparencyModal onClose={() => setShowTransparency(false)} />}
    </section>
  );
}
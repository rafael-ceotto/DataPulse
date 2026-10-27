import React from "react";
import { theme } from "../theme";

const POINTS = [
  {
    title: "Where the data comes from",
    text: "Hospital data comes from each country's official public source where available: CMS Hospital Compare (US), DataSUS and ANS (Brazil), the NHS (UK), and FINESS (France). For Canada, Belgium, Italy, Spain, Portugal and Malta, hospital listings come from Wikidata, a community-maintained open database — details for these may be less complete or current than official registries. Every answer shows a 📅 \"Data as of\" date.",
  },
  {
    title: "Sources are cited, not invented",
    text: "When the AI references methodology or guidance documents (like how star ratings are calculated), it quotes the actual source document and page — it doesn't make up explanations.",
  },
  {
    title: "It stays on topic",
    text: "The assistant only answers questions about hospitals and healthcare data for the country you have selected. It will decline anything outside that scope rather than guess.",
  },
  {
    title: "Powered by AI, checked before you see it",
    text: "Answers are generated using large language models hosted via Groq. Every response passes through an automatic safety check that screens for sensitive personal information and inappropriate content before it's shown to you.",
  },
  {
    title: "Not medical advice",
    text: "This tool helps you explore public hospital quality data. It does not diagnose, treat, or give personalized medical recommendations — always consult a healthcare professional for medical decisions.",
  },
];

export default function TransparencyModal({ onClose }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, background: "rgba(8,14,18,.72)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 1000, padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: theme.dark, borderRadius: 18, padding: 28,
          maxWidth: 560, width: "100%", maxHeight: "85vh", overflowY: "auto",
          boxShadow: "0 24px 60px -24px rgba(0,0,0,.6)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
          <h2 style={{ margin: 0, fontSize: 17, fontWeight: 600, color: "#fff" }}>
            How our AI works
          </h2>
          <button
            onClick={onClose}
            style={{
              background: "transparent", border: "none", color: "#6f8a95",
              fontSize: 20, cursor: "pointer", lineHeight: 1,
            }}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {POINTS.map((p) => (
          <div key={p.title} style={{ marginBottom: 18 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: theme.mint, marginBottom: 4 }}>
              {p.title}
            </div>
            <div style={{ fontSize: 13.5, lineHeight: 1.6, color: "#a7b6bf" }}>
              {p.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
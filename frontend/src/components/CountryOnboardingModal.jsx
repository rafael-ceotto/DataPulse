import React, { useState, useEffect } from "react";
import { theme } from "../theme";

function Flag({ code, size = 20 }) {
  const h = size <= 15 ? 15 : size <= 30 ? 30 : 60;
  const w = h === 15 ? 20 : h === 30 ? 40 : 80;
  return (
    <img
      src={`https://flagcdn.com/${w}x${h}/${code.toLowerCase()}.png`}
      alt={code}
      style={{ width: size * 1.33, height: size, borderRadius: 2, display: "inline-block", verticalAlign: "middle", objectFit: "cover" }}
    />
  );
}

const CONTINENTS = {
  Americas: { label: "Americas", countries: ["US", "BR", "CA"] },
  Europe: { label: "Europe", countries: ["GB", "FR", "BE", "PT", "ES", "IT", "MT"] },
};

const COUNTRIES = {
  US: { name: "United States", description: "5,419 hospitals" },
  BR: { name: "Brasil", description: "7,680 hospitais" },
  CA: { name: "Canada", description: "432 hospitals" },
  GB: { name: "United Kingdom", description: "247 NHS Trusts" },
  FR: { name: "France", description: "3,360 hôpitaux" },
  BE: { name: "Belgium", description: "111 hôpitaux" },
  PT: { name: "Portugal", description: "131 hospitais" },
  ES: { name: "España", description: "861 hospitales" },
  IT: { name: "Italia", description: "343 ospedali" },
  MT: { name: "Malta", description: "11 hospitals" },
};

const SUPPORTED_COUNTRIES = Object.keys(COUNTRIES);

async function detectCountry() {
  try {
    const r = await fetch("https://freeipapi.com/api/json");
    const data = await r.json();
    const code = data.countryCode;
    return SUPPORTED_COUNTRIES.includes(code) ? code : "US";
  } catch {
    return "US";
  }
}

export default function CountryOnboardingModal({ onConfirm, initialCountry }) {
  const [detected, setDetected] = useState(null);
  const [selected, setSelected] = useState(null);
  const [activeContinent, setActiveContinent] = useState(null);
  const [visibleCountries, setVisibleCountries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (initialCountry) {
      setDetected(initialCountry);
      setSelected(initialCountry);
      setLoading(false);
      return;
    }
    detectCountry().then((code) => {
      setDetected(code);
      setSelected(code);
      setLoading(false);
    });
  }, []);

  function handleContinentClick(key) {
    if (activeContinent === key) {
      setActiveContinent(null);
      setTimeout(() => setVisibleCountries([]), 300);
      return;
    }
    setActiveContinent(null);
    setVisibleCountries([]);
    setTimeout(() => {
      setActiveContinent(key);
      setVisibleCountries(CONTINENTS[key].countries);
    }, 250);
  }

  function handleCountryClick(code) {
    setSelected(code);
  }

  const isOpen = activeContinent !== null && visibleCountries.length > 0;
  const current = selected ? COUNTRIES[selected] : null;

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      background: "rgba(8, 14, 18, 0.85)",
      backdropFilter: "blur(6px)",
      zIndex: 1000,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 24,
    }}>
      <div style={{
        background: "#101a20",
        border: "1px solid #1e2d35",
        borderRadius: 20,
        padding: "36px 32px",
        maxWidth: 480,
        width: "100%",
        boxShadow: "0 32px 64px -16px rgba(0,0,0,.6)",
        display: "flex",
        flexDirection: "column",
        gap: 24,
      }}>
        {/* Header */}
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🏥</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: "#dce5e9", letterSpacing: "-0.02em", marginBottom: 6 }}>
            Welcome to DataPulse
          </div>
          <div style={{ fontFamily: theme.mono, fontSize: 12, color: "#6f8a95" }}>
            Global Hospital Quality Data — select your country to get started
          </div>
        </div>

        {/* Detected country */}
        {loading ? (
          <div style={{ textAlign: "center", fontFamily: theme.mono, fontSize: 12, color: "#6f8a95" }}>
            Detecting your location...
          </div>
        ) : detected && (
          <div style={{
            background: "#16222a",
            border: "1px solid #1e2d35",
            borderRadius: 12,
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}>
            <Flag code={detected} size={24} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, color: "#6f8a95", fontFamily: theme.mono, marginBottom: 2 }}>
                Detected location
              </div>
              <div style={{ fontSize: 15, fontWeight: 600, color: "#dce5e9" }}>
                {COUNTRIES[detected]?.name}
              </div>
            </div>
            {selected === detected && (
              <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint }}>✓ selected</span>
            )}
          </div>
        )}

        {/* Continent selector */}
        <div>
          <div style={{ fontFamily: theme.mono, fontSize: 10.5, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 10 }}>
            Or choose another country
          </div>

          <div style={{ display: "flex", gap: 8, justifyContent: "center", marginBottom: 8 }}>
            {Object.entries(CONTINENTS).map(([key, val]) => (
              <button
                key={key}
                onClick={() => handleContinentClick(key)}
                style={{
                  background: activeContinent === key ? "#0F6F8C" : "#1e3a4a",
                  border: `1px solid ${activeContinent === key ? "#0F6F8C" : "#2a5a72"}`,
                  borderRadius: 10,
                  padding: "8px 20px",
                  fontSize: 13,
                  color: activeContinent === key ? "#fff" : "#a0c4d4",
                  cursor: "pointer",
                  fontFamily: theme.sans,
                  fontWeight: activeContinent === key ? 600 : 500,
                  transition: "all 0.2s ease",
                }}
              >
                {val.label}
              </button>
            ))}
          </div>

          <div style={{
            overflow: "hidden",
            maxHeight: isOpen ? "80px" : "0px",
            opacity: isOpen ? 1 : 0,
            transition: "max-height 0.3s ease, opacity 0.3s ease",
          }}>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center", paddingTop: 4 }}>
              {visibleCountries.map((code) => (
                <button
                  key={code}
                  onClick={() => handleCountryClick(code)}
                  style={{
                    background: selected === code ? "#1a3a4a" : "#16222a",
                    border: `1px solid ${selected === code ? "#2a7a9a" : "#2a4a5a"}`,
                    borderRadius: 10,
                    padding: "6px 14px",
                    fontSize: 13,
                    color: selected === code ? "#dce5e9" : "#7ab4c8",
                    cursor: "pointer",
                    fontFamily: theme.sans,
                    fontWeight: selected === code ? 600 : 400,
                    transition: "all 0.15s",
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <Flag code={code} size={14} />
                  {COUNTRIES[code]?.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Selected country preview */}
        {current && (
          <div style={{
            background: "#16222a",
            border: "1px solid #2a7a9a",
            borderRadius: 12,
            padding: "12px 16px",
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}>
            <Flag code={selected} size={24} />
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#dce5e9" }}>{current.name}</div>
              <div style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95" }}>{current.description}</div>
            </div>
          </div>
        )}

        {/* Confirm button */}
        <button
          onClick={() => selected && onConfirm(selected)}
          disabled={!selected}
          style={{
            background: selected ? theme.mint : "#1e2d35",
            color: selected ? "#0c1418" : "#6f8a95",
            border: "none",
            borderRadius: 12,
            padding: "14px",
            fontSize: 15,
            fontWeight: 700,
            cursor: selected ? "pointer" : "not-allowed",
            fontFamily: theme.sans,
            transition: "all 0.2s ease",
            letterSpacing: "-0.01em",
          }}
        >
          Continue with {current?.name || "..."}
        </button>
      </div>
    </div>
  );
}
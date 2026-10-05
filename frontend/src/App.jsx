import React, { useEffect, useState } from "react";
import AIQuery from "./components/AIQuery";
import HospitalList from "./components/HospitalList";
import RatingChart from "./components/RatingChart";
import PhysicianAnalysis from "./components/PhysicianAnalysis";
import ScarceSpecialties from "./components/ScarceSpecialties";
import PipelineRuns from "./components/PipelineRuns";
import RatingTrend from "./components/RatingTrend";
import DataQuality from "./components/DataQuality";
import PipelineAnalytics from "./components/PipelineAnalytics";
import HospitalsNearMe from "./components/HospitalsNearMe";
import CountryOnboardingModal from "./components/CountryOnboardingModal";
import { theme } from "./theme";

const CONTINENTS = {
  Americas: {
    label: "Americas",
    countries: ["US", "BR", "CA"],
  },
  Europe: {
    label: "Europe",
    countries: ["GB", "FR", "BE", "PT", "ES", "IT", "MT"],
  },
};

const COUNTRIES = {
  US: {
    name: "United States",
    source: "CMS (Centers for Medicare & Medicaid Services)",
    description: "5,419 hospitals · Public health data · Updated annually",
    rating_info: "Rating: 1–5 stars based on 46 quality indicators. Higher = better quality care.",
  },
  BR: {
    name: "Brasil",
    source: "DATASUS / Ministério da Saúde",
    description: "7,680 hospitais · Sistema Único de Saúde (SUS)",
    rating_info: "Sem rating nacional único — dados estruturais: leitos, especialidades, equipamentos. Fonte: CNES.",
  },
  CA: {
    name: "Canada",
    source: "Wikidata / CIHI",
    description: "432 hospitals · Canadian health system",
    rating_info: "No single national rating — structural data from Wikidata.",
  },
  GB: {
    name: "United Kingdom",
    source: "NHS / CQC (Care Quality Commission)",
    description: "247 NHS Trusts · National Health Service · England",
    rating_info: "Rating: Outstanding / Good / Requires Improvement / Inadequate. Assessed on: Safe · Effective · Caring · Responsive · Well-led.",
  },
  FR: {
    name: "France",
    source: "FINESS / Ministère de la Santé",
    description: "3,360 hôpitaux · Système de santé français",
    rating_info: "Certification HAS (Haute Autorité de Santé) — données structurelles FINESS.",
  },
  BE: {
    name: "Belgium",
    source: "Wikidata / SPF Santé publique",
    description: "111 hôpitaux · Royaume de Belgique",
    rating_info: "Agrément SPF Santé publique — données structurelles Wikidata.",
  },
  PT: {
    name: "Portugal",
    source: "Wikidata / SNS",
    description: "131 hospitais · Serviço Nacional de Saúde",
    rating_info: "Dados estruturais — sem rating nacional único. Fonte: Wikidata.",
  },
  ES: {
    name: "España",
    source: "Wikidata / SNS España",
    description: "861 hospitales · Sistema Nacional de Salud",
    rating_info: "Datos estructurales — sin rating nacional único. Fuente: Wikidata.",
  },
  IT: {
    name: "Italia",
    source: "Wikidata / SSN",
    description: "343 ospedali · Servizio Sanitario Nazionale",
    rating_info: "Dati strutturali — senza rating nazionale unico. Fonte: Wikidata.",
  },
  MT: {
    name: "Malta",
    source: "Wikidata / Malta Health",
    description: "11 hospitals · Maltese health system",
    rating_info: "Structural data only — Wikidata.",
  },
};

const FACILITIES_COUNT = { US: "5,419", BR: "7,680", CA: "432", GB: "247", FR: "3,360", BE: "111", PT: "131", ES: "861", IT: "343", MT: "11" };
const LAST_UPDATED = { US: "Oct 2026", BR: "Out 2026", CA: "Oct 2026", GB: "Oct 2026", FR: "Oct 2026", BE: "Oct 2026", PT: "Oct 2026", ES: "Oct 2026", IT: "Oct 2026", MT: "Oct 2026" };

function useCIStatus() {
  const [status, setStatus] = useState(null);
  useEffect(() => {
    function fetch_() {
      fetch("https://api.github.com/repos/rafael-ceotto/DataPulse/actions/runs?per_page=1")
        .then((r) => r.json())
        .then((data) => {
          const run = data.workflow_runs?.[0];
          if (run) setStatus(run.conclusion);
        })
        .catch(() => {});
    }
    fetch_();
    const id = setInterval(fetch_, 60000);
    return () => clearInterval(id);
  }, []);
  return status;
}

function useTotalGlobal() {
  const [total, setTotal] = useState("—");
  useEffect(() => {
    fetch("/api/v1/hospitals/stats/count")
      .then((r) => r.json())
      .then((data) => {
        
        setTotal(data.total.toLocaleString());
      })
      .catch((e) => console.error("total global error:", e));
  }, []);
  return total;
}

function MetricCard({ label, value, accent }) {
  return (
    <div style={{
      background: "#16222a",
      border: `1px solid #1e2d35`,
      borderRadius: 12,
      padding: "16px 20px",
      flex: "1 1 160px",
    }}>
      <div style={{ fontFamily: theme.mono, fontSize: 10, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color: accent || "#dce5e9", letterSpacing: "-0.02em" }}>
        {value}
      </div>
    </div>
  );
}

function CountrySelector({ country, onChange }) {
  const [activeContinent, setActiveContinent] = useState(null);
  const [visibleCountries, setVisibleCountries] = useState([]);

  const current = COUNTRIES[country];

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
      onChange(CONTINENTS[key].countries[0]);
    }, 250);
  }

  const isOpen = activeContinent !== null && visibleCountries.length > 0;

  return (
    <div style={{ marginBottom: 0 }}>
      <div style={{ display: "flex", gap: 10, justifyContent: "center", marginBottom: 8 }}>
        {Object.entries(CONTINENTS).map(([key, val]) => (
          <button
            key={key}
            onClick={() => handleContinentClick(key)}
            style={{
              background: activeContinent === key ? "#0F6F8C" : "#1e3a4a",
              border: `1px solid ${activeContinent === key ? "#0F6F8C" : "#2a5a72"}`,
              borderRadius: 10,
              padding: "9px 22px",
              fontSize: 13,
              color: activeContinent === key ? "#fff" : "#a0c4d4",
              cursor: "pointer",
              fontFamily: theme.sans,
              fontWeight: activeContinent === key ? 600 : 500,
              transition: "all 0.2s ease",
              letterSpacing: "0.02em",
            }}
          >
            {val.label}
          </button>
        ))}
      </div>

      <div style={{
        overflow: "hidden",
        maxHeight: isOpen ? "60px" : "0px",
        opacity: isOpen ? 1 : 0,
        transition: "max-height 0.3s ease, opacity 0.3s ease",
        marginBottom: isOpen ? 12 : 0,
      }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center", paddingTop: 4 }}>
          {visibleCountries.map((code) => (
            <button
              key={code}
              onClick={() => onChange(code)}
              style={{
                background: country === code ? "#1a3a4a" : "#16222a",
                border: `1px solid ${country === code ? "#2a7a9a" : "#2a4a5a"}`,
                borderRadius: 10,
                padding: "6px 16px",
                fontSize: 13,
                color: country === code ? "#dce5e9" : "#7ab4c8",
                cursor: "pointer",
                fontFamily: theme.sans,
                fontWeight: country === code ? 600 : 400,
                transition: "all 0.15s",
              }}
            >
              {COUNTRIES[code]?.name}
            </button>
          ))}
        </div>
      </div>

      <div style={{
        background: "#16222a",
        border: `1px solid #1e2d35`,
        borderRadius: 12,
        padding: "14px 18px",
        display: "flex",
        flexDirection: "column",
        gap: 4,
        marginBottom: 24,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: "#dce5e9" }}>{current.name}</span>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95" }}>· {current.source}</span>
        </div>
        <div style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95" }}>{current.description}</div>
        <div style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint }}>{current.rating_info}</div>
      </div>
    </div>
  );
}

export default function App() {
  const [showOnboarding, setShowOnboarding] = useState(true);
  const [activeTab, setActiveTab] = useState("hospitals");
  const [country, setCountry] = useState("US");
  const ciStatus = useCIStatus();
  const ciColor = ciStatus === "success" ? theme.mint : ciStatus === "failure" ? "#ff6b6b" : "#6f8a95";
  const totalGlobal = useTotalGlobal();
  const isUS = country === "US";
  const isBR = country === "BR";
  const isFR = country === "FR";
  const isBE = country === "BE";
  const isES = country === "ES";
  const isPT = country === "PT";
  const isIT = country === "IT";
  const isFrench = isFR || isBE;

  function handleOnboardingConfirm(code) {
    setCountry(code);
    setShowOnboarding(false);
  }

  const facilityLabel = isBR || isPT ? "Instalações"
    : isFrench ? "Établissements"
    : isES ? "Instalaciones"
    : isIT ? "Strutture"
    : "Facilities";

  const totalLabel = isBR || isPT ? "Total Global"
    : isFrench ? "Total mondial"
    : isES ? "Total mundial"
    : isIT ? "Totale mondiale"
    : "Total Global";

  const updatedLabel = isBR || isPT ? "Última atualização"
    : isFrench ? "Mise à jour"
    : isES ? "Última actualización"
    : isIT ? "Ultimo aggiornamento"
    : "Last Updated";

  useEffect(() => {
    if (!isUS) setActiveTab("hospitals");
  }, [country]);

  const TABS = isUS ? [
    { id: "hospitals", label: "Hospitals" },
    { id: "analytics", label: "Analytics" },
    { id: "pipeline", label: "Pipeline" },
    { id: "physicians", label: "Physicians" },
  ] : isBR || isPT ? [
    { id: "hospitals", label: "Hospitais" },
  ] : isFrench ? [
    { id: "hospitals", label: "Hôpitaux" },
  ] : isES ? [
    { id: "hospitals", label: "Hospitales" },
  ] : isIT ? [
    { id: "hospitals", label: "Ospedali" },
  ] : [
    { id: "hospitals", label: "Hospitals" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#f4f6f8", color: theme.ink, fontFamily: theme.sans }}>
      {showOnboarding && (
        <CountryOnboardingModal onConfirm={handleOnboardingConfirm} initialCountry={showOnboarding === "reopen" ? country : null} />
      )}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
        body { margin: 0; background: #f4f6f8; }
        * { box-sizing: border-box; }
        @keyframes dp-pulse { 0%,100% { opacity:.25; transform:scaleY(.5); } 50% { opacity:1; transform:scaleY(1); } }
        @keyframes pulse { 0% { opacity:1; } 50% { opacity:0.4; } 100% { opacity:1; } }
      `}</style>

      <header style={{
        borderBottom: `1px solid #e6eaec`,
        padding: "16px 40px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "#ffffff",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 9,
            background: theme.accent,
            display: "flex", alignItems: "center", justifyContent: "center", gap: 3,
          }}>
            {[10, 18, 13].map((h, i) => (
              <span key={i} style={{
                display: "block", width: 3, height: h, borderRadius: 2,
                background: "#fff",
                animation: `dp-pulse 1.4s ease-in-out ${i * 0.2}s infinite`,
              }} />
            ))}
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em", color: theme.ink }}>DataPulse</div>
            <div style={{ fontSize: 11, color: theme.muted, fontFamily: theme.mono }}>Global Hospital Quality Data</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>          
          <button
            onClick={() => setShowOnboarding("reopen")}
            style={{
              background: "#16222a",
              border: "1px solid #1e2d35",
              borderRadius: 8,
              padding: "6px 14px",
              fontSize: 12,
              color: "#a0c4d4",
              cursor: "pointer",
              fontFamily: theme.mono,
              letterSpacing: "0.04em",
              marginLeft: 12,
            }}
          >
            🌍 {COUNTRIES[country]?.name || "Change country"}
          </button>
        </div>
      </header>

      <main style={{ maxWidth: 1400, margin: "0 auto", padding: "32px 40px" }}>
        
        <AIQuery country={country} />

        <div style={{ display: "flex", gap: 12, marginTop: 24, flexWrap: "wrap" }}>
          <MetricCard label={facilityLabel} value={FACILITIES_COUNT[country] || "—"} accent={theme.mint} />
          {isUS ? (
            <>
              <MetricCard label="Avg Rating" value="3.21 ★" accent="#f1c40f" />
              <MetricCard label="Completeness" value="58.6%" accent="#dce5e9" />
            </>
          ) : (
            <MetricCard label={totalLabel} value={totalGlobal} accent="#dce5e9" />
          )}
          <MetricCard label={updatedLabel} value={LAST_UPDATED[country] || "—"} accent="#6f8a95" />
        </div>

        <div style={{ display: "flex", gap: 4, marginTop: 36, borderRadius: 12, padding: "4px", width: "fit-content" }}>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id ? "#0F6F8C" : "#85d6c6",
                border: "none",
                borderRadius: 9,
                color: activeTab === tab.id ? "#ffffff" : theme.ink,
                fontFamily: theme.sans,
                fontSize: 14,
                fontWeight: activeTab === tab.id ? 600 : 400,
                padding: "8px 20px",
                cursor: "pointer",
                transition: "all 0.15s",
                boxShadow: activeTab === tab.id ? "0 1px 4px rgba(0,0,0,.15)" : "none",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div style={{ marginTop: 24 }}>
          {activeTab === "hospitals" && (
            <>
              <HospitalsNearMe country={country} />
              {isUS && <RatingChart country={country} />}
              <DataQuality country={country} />
              <HospitalList country={country} />
            </>
          )}
          {activeTab === "analytics" && isUS && (
            <>
              <RatingTrend />
              <PipelineAnalytics />
            </>
          )}
          {activeTab === "pipeline" && isUS && <PipelineRuns />}
          {activeTab === "physicians" && (
            <>
              <PhysicianAnalysis country={country} />
              <ScarceSpecialties country={country} />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
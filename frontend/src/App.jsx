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
  Americas: { label: "Americas", countries: ["US", "BR", "CA"] },
  Europe: { label: "Europe", countries: ["GB", "FR", "BE", "PT", "ES", "IT", "MT"] },
};

const COUNTRY_FLAGS = {
  US: "🇺🇸", BR: "🇧🇷", CA: "🇨🇦", GB: "🇬🇧", FR: "🇫🇷",
  BE: "🇧🇪", PT: "🇵🇹", ES: "🇪🇸", IT: "🇮🇹", MT: "🇲🇹",
};

const COUNTRIES = {
  US: { name: "United States", source: "CMS (Centers for Medicare & Medicaid Services)", description: "5,419 hospitals · Public health data · Updated annually", rating_info: "Rating: 1–5 stars based on 46 quality indicators. Higher = better quality care." },
  BR: { name: "Brasil", source: "DATASUS / Ministério da Saúde", description: "7,680 hospitais · Sistema Único de Saúde (SUS)", rating_info: "Sem rating nacional único — dados estruturais: leitos, especialidades, equipamentos. Fonte: CNES." },
  CA: { name: "Canada", source: "Wikidata / CIHI", description: "432 hospitals · Canadian health system", rating_info: "No single national rating — structural data from Wikidata." },
  GB: { name: "United Kingdom", source: "NHS / CQC (Care Quality Commission)", description: "247 NHS Trusts · National Health Service · England", rating_info: "Rating: Outstanding / Good / Requires Improvement / Inadequate." },
  FR: { name: "France", source: "FINESS / Ministère de la Santé", description: "3,360 hôpitaux · Système de santé français", rating_info: "Certification HAS (Haute Autorité de Santé) — données structurelles FINESS." },
  BE: { name: "Belgium", source: "Wikidata / SPF Santé publique", description: "111 hôpitaux · Royaume de Belgique", rating_info: "Agrément SPF Santé publique — données structurelles Wikidata." },
  PT: { name: "Portugal", source: "Wikidata / SNS", description: "131 hospitais · Serviço Nacional de Saúde", rating_info: "Dados estruturais — sem rating nacional único. Fonte: Wikidata." },
  ES: { name: "España", source: "Wikidata / SNS España", description: "861 hospitales · Sistema Nacional de Salud", rating_info: "Datos estructurales — sin rating nacional único. Fuente: Wikidata." },
  IT: { name: "Italia", source: "Wikidata / SSN", description: "343 ospedali · Servizio Sanitario Nazionale", rating_info: "Dati strutturali — senza rating nazionale unico. Fonte: Wikidata." },
  MT: { name: "Malta", source: "Wikidata / Malta Health", description: "11 hospitals · Maltese health system", rating_info: "Structural data only — Wikidata." },
};

const LAST_UPDATED = { US: "Oct 2026", BR: "Oct 2026", CA: "Oct 2026", GB: "Oct 2026", FR: "Oct 2026", BE: "Oct 2026", PT: "Oct 2026", ES: "Oct 2026", IT: "Oct 2026", MT: "Oct 2026" };

function useCountryStats(country) {
  const [stats, setStats] = useState(null);
  useEffect(() => {
    setStats(null);
    fetch(`/api/v1/hospitals/stats/country?country=${country}`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, [country]);
  return stats;
}

function useCountrySummary(country) {
  const [summary, setSummary] = useState(null);
  useEffect(() => {
    setSummary(null);
    fetch(`/api/v1/ai/country-summary?country=${country}`)
      .then((r) => r.json())
      .then((data) => setSummary(data.summary))
      .catch(() => {});
  }, [country]);
  return summary;
}

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

function MetricCard({ icon, label, value, sub, accent }) {
  return (
    <div style={{
      background: "#1e3340",
      border: "1px solid #2a4555",
      borderRadius: 14,
      padding: "20px 24px",
      flex: "1 1 0",
      display: "flex",
      flexDirection: "column",
      gap: 8,
      maxWidth: "calc(25% - 11px)",
      minWidth: 160,      
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {icon && <span style={{ fontSize: 16 }}>{icon}</span>}
        <div style={{ fontFamily: theme.mono, fontSize: 10, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase" }}>
          {label}
        </div>
      </div>
      <div style={{ fontSize: 26, fontWeight: 700, color: accent || "#dce5e9", letterSpacing: "-0.02em" }}>
        {value ?? "—"}
      </div>
      {sub && <div style={{ fontFamily: theme.mono, fontSize: 10, color: "#6f8a95" }}>{sub}</div>}
    </div>
  );
}

function Sidebar({ country, onChange, activeSection, setActiveSection, isUS, isBR, isPT, isFrench, isES, isIT }) {
  const nearMeLabel = isBR || isPT ? "Hospitais Próximos" : isFrench ? "Hôpitaux à proximité" : isES ? "Hospitales Cercanos" : isIT ? "Ospedali Vicini" : "Hospitals Near Me";
  const dataQualityLabel = isBR || isPT ? "Qualidade dos Dados" : isFrench ? "Qualité des données" : isES ? "Calidad de los datos" : isIT ? "Qualità dei dati" : "Data Quality";
  const browseLabel = isBR || isPT ? "Explorar Hospitais" : isFrench ? "Explorer les hôpitaux" : isES ? "Explorar hospitales" : isIT ? "Esplora ospedali" : "Browse Hospitals";

  const navItems = [
    { id: "near-me", label: nearMeLabel, icon: "📍" },
    { id: "data-quality", label: dataQualityLabel, icon: "🛡" },
    { id: "browse", label: browseLabel, icon: "☰" },
    ...(isUS ? [
      { id: "analytics", label: "Analytics", icon: "📊", badge: "US only" },
      { id: "pipeline", label: "Pipeline", icon: "⚙️" },
      { id: "physicians", label: "Physicians", icon: "👨‍⚕️" },
    ] : []),
  ];

  return (
    <aside style={{
      width: 200,
      minWidth: 200,
      background: "#f4f6f8",
      borderRight: "1px solid #e0e5e8",
      display: "flex",
      flexDirection: "column",
      height: "100%",
      overflowY: "auto",
    }}>
      {/* Ask Doc button */}
      <div style={{ padding: "14px 12px 10px" }}>
        <button
          onClick={() => setActiveSection("ask-doc")}
          style={{
            width: "100%",
            background: activeSection === "ask-doc" ? "#0d5c73" : "#0F6F8C",
            border: "none",
            borderRadius: 10,
            padding: "10px 14px",
            fontSize: 14,
            fontWeight: 600,
            color: "#fff",
            cursor: "pointer",
            fontFamily: theme.sans,
            display: "flex",
            alignItems: "center",
            gap: 8,
            transition: "background 0.15s",
          }}
        >
          <span>✦</span>
          Ask Doc
        </button>
      </div>

      {/* Explore */}
      <div style={{ padding: "4px 10px 8px" }}>
        <div style={{ fontFamily: theme.mono, fontSize: 10, color: "#9baab3", letterSpacing: "0.08em", textTransform: "uppercase", padding: "6px 6px 6px" }}>
          Explore
        </div>
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveSection(item.id)}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: activeSection === item.id ? "#e2edf2" : "transparent",
              border: "none",
              borderRadius: 8,
              padding: "8px 10px",
              fontSize: 13,
              color: activeSection === item.id ? "#0F6F8C" : "#3d5566",
              cursor: "pointer",
              fontFamily: theme.sans,
              fontWeight: activeSection === item.id ? 600 : 400,
              transition: "all 0.12s",
              textAlign: "left",
              marginBottom: 2,
            }}
          >
            <span style={{ fontSize: 14, opacity: 0.8 }}>{item.icon}</span>
            <span style={{ flex: 1 }}>{item.label}</span>
            {item.badge && (
              <span style={{ fontFamily: theme.mono, fontSize: 9, color: "#0F6F8C", background: "#d4eef5", borderRadius: 4, padding: "2px 5px" }}>
                {item.badge}
              </span>
            )}
            {activeSection === item.id && (
              <span style={{ width: 3, height: 14, background: "#0F6F8C", borderRadius: 2 }} />
            )}
          </button>
        ))}
      </div>

      {/* Coverage */}
      <div style={{ padding: "8px 12px 16px", borderTop: "1px solid #e0e5e8", marginTop: 8 }}>
        <div style={{ fontFamily: theme.mono, fontSize: 10, color: "#9baab3", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 10 }}>
          Coverage · 10 countries
        </div>
        {Object.entries(CONTINENTS).map(([continent, val]) => (
          <div key={continent} style={{ marginBottom: 8 }}>
            <div style={{ fontFamily: theme.mono, fontSize: 9, color: "#b0bec7", marginBottom: 5, letterSpacing: "0.05em" }}>
              {continent}
            </div>
            <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
              {val.countries.map((code) => (
                <button
                  key={code}
                  onClick={() => onChange(code)}
                  title={COUNTRIES[code]?.name}
                  style={{
                    background: country === code ? "#0F6F8C" : "#e8eef1",
                    border: `1px solid ${country === code ? "#0F6F8C" : "#d0dce3"}`,
                    borderRadius: 5,
                    padding: "3px 6px",
                    fontSize: 10,
                    color: country === code ? "#fff" : "#4a6677",
                    cursor: "pointer",
                    fontFamily: theme.mono,
                    fontWeight: country === code ? 700 : 400,
                    transition: "all 0.12s",
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                  }}
                >
                  <Flag code={code} size={12} /> {code}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}

export default function App() {
  const [showOnboarding, setShowOnboarding] = useState(true);
  const [activeSection, setActiveSection] = useState("near-me");
  const [country, setCountry] = useState("US");
  const stats = useCountryStats(country);
  const summary = useCountrySummary(country);

  const isUS = country === "US";
  const isBR = country === "BR";
  const isFR = country === "FR";
  const isBE = country === "BE";
  const isES = country === "ES";
  const isPT = country === "PT";
  const isIT = country === "IT";
  const isFrench = isFR || isBE;

  const current = COUNTRIES[country];

  function handleOnboardingConfirm(code) {
    setCountry(code);
    setShowOnboarding(false);
  }

  function handleCountryChange(code) {
    setCountry(code);
    setActiveSection("ask-doc");
  }

  const metricCards = () => {
    if (!stats) return [];
    if (isUS) return [
      { icon: "🏥", label: "Facilities", value: stats.total?.toLocaleString(), accent: theme.mint },
      { icon: "🚨", label: "Emergency Services", value: stats.with_emergency?.toLocaleString(), accent: "#ff6b6b" },
      { icon: "📞", label: "With Phone", value: stats.with_phone?.toLocaleString(), accent: "#dce5e9" },
      { icon: "🏷️", label: "Hospital Types", value: stats.type_count, accent: "#a78bfa" },
    ];
    if (isBR) return [
      { icon: "🏥", label: "Instalações", value: stats.total?.toLocaleString(), accent: theme.mint },
      { icon: "🚨", label: "Com Emergência", value: stats.with_emergency?.toLocaleString(), accent: "#ff6b6b" },
      { icon: "📞", label: "Com Telefone", value: stats.with_phone?.toLocaleString(), accent: "#dce5e9" },
      { icon: "🏷️", label: "Tipos", value: stats.type_count, accent: "#a78bfa" },
    ];
    if (isFR || isES) return [
      { icon: "🏥", label: isFR ? "Établissements" : "Instalaciones", value: stats.total?.toLocaleString(), accent: theme.mint },
      { icon: "📞", label: isFR ? "Avec téléphone" : "Con teléfono", value: stats.with_phone?.toLocaleString(), accent: "#dce5e9" },
      { icon: "📍", label: isFR ? "Géolocalisés" : "Geolocalizados", value: stats.with_coords?.toLocaleString(), accent: "#f1c40f" },
      { icon: "🏷️", label: isFR ? "Types" : "Tipos", value: stats.type_count, accent: "#a78bfa" },
    ];
    return [
      { icon: "🏥", label: isIT ? "Strutture" : isPT ? "Instalações" : "Facilities", value: stats.total?.toLocaleString(), accent: theme.mint },
      { icon: "📍", label: "Geolocated", value: stats.with_coords?.toLocaleString(), accent: "#f1c40f" },
      { icon: "🗓️", label: "Last Updated", value: LAST_UPDATED[country], accent: "#6f8a95" },
      { icon: "🔗", label: "Source", value: current?.source?.split(" / ")[0], accent: "#dce5e9", sub: current?.source?.split(" / ")[1] },
    ];
  };

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", fontFamily: theme.sans, background: "#1a2f3a", overflow: "hidden" }}>
      {showOnboarding && (
        <CountryOnboardingModal
          onConfirm={handleOnboardingConfirm}
          initialCountry={showOnboarding === "reopen" ? country : null}
        />
      )}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
        html, body { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; background: #f4f6f8; }
        * { box-sizing: border-box; }
        @keyframes dp-pulse { 0%,100% { opacity:.25; transform:scaleY(.5); } 50% { opacity:1; transform:scaleY(1); } }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #c8d5dc; border-radius: 3px; }
      `}</style>

      {/* Header */}
      <header style={{
        height: 52,
        borderBottom: "1px solid #e0e5e8",
        background: "#ffffff",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
        flexShrink: 0,
        zIndex: 100,
        width: "100%",
        overflow: "hidden",
        boxSizing: "border-box",
      }}>
        <button
          onClick={() => setActiveSection("ask-doc")}
          style={{ display: "flex", alignItems: "center", gap: 10, background: "none", border: "none", cursor: "pointer", padding: 0 }}
        >
          <div style={{
            width: 28, height: 28, borderRadius: 7,
            background: theme.accent,
            display: "flex", alignItems: "center", justifyContent: "center", gap: 2,
          }}>
            {[7, 13, 9].map((h, i) => (
              <span key={i} style={{
                display: "block", width: 3, height: h, borderRadius: 2, background: "#fff",
                animation: `dp-pulse 1.4s ease-in-out ${i * 0.2}s infinite`,
              }} />
            ))}
          </div>
          <div style={{ textAlign: "left" }}>
            <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.02em", color: "#1a2f3a" }}>DataPulse</div>
            <div style={{ fontSize: 10, color: "#9baab3", fontFamily: theme.mono }}>Global Hospital Quality Data</div>
          </div>
        </button>

        <button
          onClick={() => setShowOnboarding("reopen")}
          style={{
            display: "flex", alignItems: "center", gap: 8,
            background: "#f4f6f8", border: "1px solid #e0e5e8",
            borderRadius: 8, padding: "6px 14px",
            fontSize: 13, color: "#3d5566",
            cursor: "pointer", fontFamily: theme.sans,
          }}
        >
          <Flag code={country} size={18} />
          <span style={{ fontWeight: 500 }}>{COUNTRIES[country]?.name}</span>
          <span style={{ color: "#9baab3", fontSize: 11 }}>▾</span>
        </button>
      </header>

      {/* Body */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden", width: "100%", minWidth: 0 }}>

        {/* Sidebar */}
        <Sidebar
          country={country}
          onChange={handleCountryChange}
          activeSection={activeSection}
          setActiveSection={setActiveSection}
          isUS={isUS}
          isBR={isBR}
          isPT={isPT}
          isFrench={isFrench}
          isES={isES}
          isIT={isIT}
        />

        {/* Main content */}
        <main style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          background: "#1a2f3a",
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
          minHeight: 0,
        }}>
          {/* Country hero */}
          <div style={{ padding: "28px 40px 20px", borderBottom: "1px solid #243d4d", flexShrink: 0  }}>
          <div style={{ fontSize: 26, fontWeight: 700, color: "#dce5e9", letterSpacing: "-0.02em", marginBottom: 4, display: "flex", alignItems: "center", gap: 10 }}>
          <Flag code={country} size={24} />
          {current?.name}
          </div>
          <div style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95", marginBottom: 20 }}>
            Hospital quality data, one view
          </div>
          <AIQuery country={country} />
          </div>

          {/* Metric cards */}
          <div style={{ padding: "20px 40px", display: "flex", gap: 14, flexWrap: "wrap", borderBottom: "1px solid #243d4d", overflow: "hidden", flexShrink: 0 }}>
            {metricCards().map((card, i) => (
              <MetricCard key={i} {...card} />
            ))}
          </div>

          {/* Country summary */}
          {summary && (
            <div style={{ padding: "20px 40px", borderBottom: "1px solid #243d4d", display: "flex", justifyContent: "center", flexShrink: 0 }}>
              <div style={{ maxWidth: 800, width: "100%" }}>
                <div style={{ fontFamily: theme.mono, fontSize: 10, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 10 }}>
                  Healthcare System Overview
                </div>
                <p style={{ fontSize: 14, lineHeight: 1.7, color: "#a0b8c4", margin: 0 }}>
                  {summary}
                </p>
              </div>
            </div>
          )}
          {!summary && (
            <div style={{ padding: "20px 40px", borderBottom: "1px solid #243d4d" }}>
              <div style={{ fontFamily: theme.mono, fontSize: 10, color: "#3a5a6a", letterSpacing: "0.07em", textTransform: "uppercase" }}>
                Loading overview...
              </div>
            </div>
          )}

          {/* Content */}
          <div style={{ padding: "24px 40px", flex: 1}}>
            {activeSection === "ask-doc" && null}
            {activeSection === "near-me" && <HospitalsNearMe country={country} />}
            {activeSection === "data-quality" && <DataQuality country={country} />}
            {activeSection === "browse" && <HospitalList country={country} />}
            {activeSection === "analytics" && isUS && (
              <>
                <RatingChart country={country} />
                <RatingTrend />
                <PipelineAnalytics />
              </>
            )}
            {activeSection === "pipeline" && isUS && <PipelineRuns />}
            {activeSection === "physicians" && isUS && (
              <>
                <PhysicianAnalysis country={country} />
                <ScarceSpecialties country={country} />
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
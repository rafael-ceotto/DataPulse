import React, { useEffect, useState } from "react";
import { theme } from "../theme";
import { getToken } from "../services/api";

export default function DataQuality({ country = "US" }) {
  const [open, setOpen] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  const isBR = country === "BR";
  const isGB = country === "GB";
  const isUS = country === "US";
  const isBE = country === "BE";
  const isFR = country === "FR";
  const isPT = country === "PT";
  const isES = country === "ES";
  const isCA = country === "CA";
  const isIT = country === "IT";
  const isMT = country === "MT";
  const isFrench = isFR || isBE;

  useEffect(() => {
    if (!open) return;
    setMetrics(null);
    setLoading(true);
    getToken().then((token) => {
      fetch(`/api/v1/hospitals/data-quality?country=${country}`, {
        headers: { "Authorization": `Bearer ${token}` },
      })
        .then((r) => r.json())
        .then((data) => { setMetrics(data); setLoading(false); });
    });
  }, [open, country]);

  function MetricCard({ label, value, sub, color = "#dce5e9", alert = false }) {
    return (
      <div style={{
        background: alert ? "#1a0a0a" : isUS ? theme.darkInput : "#1a2830",
        border: `1px solid ${alert ? "#c0392b44" : "#2c3b44"}`,
        borderRadius: 12,
        padding: "18px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}>
        <div style={{ fontFamily: theme.mono, fontSize: 10.5, letterSpacing: "0.07em", textTransform: "uppercase", color: "#6f8a95" }}>
          {label}
        </div>
        <div style={{ fontSize: 28, fontWeight: 700, color: alert ? "#c0392b" : color, letterSpacing: "-0.02em" }}>
          {value ?? "—"}
        </div>
        {sub && <div style={{ fontSize: 12, color: "#6f8a95" }}>{sub}</div>}
      </div>
    );
  }

  function ProgressBar({ pct }) {
    return (
      <div style={{ marginTop: 4 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ fontFamily: theme.mono, fontSize: 10.5, letterSpacing: "0.07em", textTransform: "uppercase", color: "#6f8a95" }}>
            Data Completeness
          </span>
          <span style={{ fontFamily: theme.mono, fontSize: 12, color: pct >= 80 ? "#2f9e6f" : "#f0a500" }}>
            {pct}%
          </span>
        </div>
        <div style={{ background: "#1e2d35", borderRadius: 999, height: 6, overflow: "hidden" }}>
          <div style={{
            height: "100%",
            width: `${pct}%`,
            background: pct >= 80 ? "#2f9e6f" : "#f0a500",
            borderRadius: 999,
            transition: "width 0.6s ease",
          }} />
        </div>
      </div>
    );
  }

  const totalHospitalsLabel = isBR || isPT ? "Total de Hospitais"
    : isFrench ? "Total des hôpitaux"
    : isES ? "Total de hospitales"
    : isIT ? "Totale ospedali"
    : "Total Hospitals";

  const totalHospitalsSub = isBR ? "Estabelecimentos CNES com leitos"
    : isGB ? "Active NHS Trusts in England"
    : isFR ? "Établissements FINESS — types 101, 106, 292, 355"
    : isBE ? "Hôpitaux Wikidata — Belgique"
    : isPT ? "Hospitais Wikidata — Portugal"
    : isES ? "Hospitales Wikidata — España"
    : isCA ? "Hospitals Wikidata — Canada"
    : isIT ? "Ospedali Wikidata — Italia"
    : isMT ? "Hospitals Wikidata — Malta"
    : "CMS facilities in dataset";

  const missingPhoneLabel = isBR || isPT ? "Telefone ausente"
    : isFrench ? "Téléphone manquant"
    : isES ? "Teléfono ausente"
    : isIT ? "Telefono mancante"
    : "Missing Phone";

  const missingPhoneSub = isBR || isPT ? "Sem número de telefone"
    : isFrench ? "Sans numéro de téléphone"
    : isES ? "Sin número de teléfono"
    : isIT ? "Senza numero di telefono"    
    : "No telephone number";

  const titleLabel = isBR || isPT ? "Qualidade dos Dados"
    : isFrench ? "Qualité des données"
    : isES ? "Calidad de los datos"
    : isIT ? "Qualità dei dati"
    : "Data Quality";

  const badgeLabel = isBR || isPT ? "Métricas de saúde"
    : isFrench ? "Métriques de santé"
    : isES ? "Métricas de salud"
    : isIT ? "Metriche sanitarie"
    : "Health Metrics";

  const loadingLabel = isFrench ? "Chargement..."
    : isPT ? "Carregando..."
    : isES ? "Cargando..."
    : isIT ? "Caricamento..."
    : "Loading...";

  const noDataLabel = isFrench ? "Aucune donnée disponible."
    : isPT ? "Sem dados disponíveis."
    : isES ? "No hay datos disponibles."
    : isIT ? "Nessun dato disponibile."
    : "No data available.";

  return (
    <section style={{ marginTop: 24 }}>
      <div
        onClick={() => setOpen((o) => !o)}
        style={{
          background: "#101a20",
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
            {titleLabel}
          </h2>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            {badgeLabel}
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
            <div style={{ textAlign: "center", color: "#6f8a95", padding: 40 }}>{loadingLabel}</div>
          ) : metrics ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              {isUS && <ProgressBar pct={metrics.completeness_pct} />}
              <div style={{
                display: "grid",
                gridTemplateColumns: isUS ? "repeat(auto-fill, minmax(200px, 1fr))" : "repeat(auto-fit, minmax(200px, max-content))",
                gap: 14,
                justifyContent: isUS ? "start" : "center",
              }}>
                <MetricCard
                  label={totalHospitalsLabel}
                  value={metrics.total_hospitals?.toLocaleString() ?? "—"}
                  sub={totalHospitalsSub}
                  color="#dce5e9"
                />
                {isUS && (
                  <>
                    <MetricCard label="Rated Hospitals" value={metrics.rated_hospitals?.toLocaleString() ?? "—"} sub="Have an overall star rating" color="#2f9e6f" />
                    <MetricCard label="Unrated Hospitals" value={metrics.unrated_hospitals?.toLocaleString() ?? "—"} sub="Missing overall rating" color="#f0a500" alert={metrics.unrated_hospitals > 500} />
                    <MetricCard label="Low Rated (≤2★)" value={metrics.low_rated_hospitals?.toLocaleString() ?? "—"} sub="Rated 1 or 2 stars" color="#c0392b" alert={metrics.low_rated_hospitals > 0} />
                  </>
                )}
                {isBR && (
                  <MetricCard label="Sistema de rating" value="N/A" sub="CNES não possui rating nacional único" color="#6f8a95" />
                )}
                {isGB && (
                  <MetricCard label="Rating system" value="CQC" sub="Care Quality Commission — no bulk data available without API key" color="#6f8a95" />
                )}
                {isFrench && (
                  <MetricCard
                    label="Système de notation"
                    value="N/A"
                    sub={isFR ? "HAS Certification — données structurelles uniquement" : "SPF Santé publique — données structurelles uniquement"}
                    color="#6f8a95"
                  />
                )}
                {isPT && (
                  <MetricCard label="Sistema de avaliação" value="N/A" sub="SNS — dados estruturais apenas (Wikidata)" color="#6f8a95" />
                )}
                {isES && (
                  <MetricCard label="Sistema de evaluación" value="N/A" sub="SNS España — datos estructurales únicamente (Wikidata)" color="#6f8a95" />
                )}
                {isCA && (
                  <MetricCard label="Rating system" value="N/A" sub="CIHI — structural data only (Wikidata)" color="#6f8a95" />
                )}
                {isIT && (
                  <MetricCard label="Sistema di valutazione" value="N/A" sub="SSN — dati strutturali solo (Wikidata)" color="#6f8a95" />
                )}
                {isMT && (
                  <MetricCard label="Rating system" value="N/A" sub="Malta Health — structural data only (Wikidata)" color="#6f8a95" />
                )}
                <MetricCard
                  label={missingPhoneLabel}
                  value={metrics.missing_phone?.toLocaleString() ?? "0"}
                  sub={missingPhoneSub}
                  color="#6f8a95"
                  alert={metrics.missing_phone > 0}
                />
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", color: "#6f8a95", padding: 40 }}>{noDataLabel}</div>
          )}
        </div>
      )}
    </section>
  );
}
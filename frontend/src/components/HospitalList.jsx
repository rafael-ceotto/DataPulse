import React, { useEffect, useState } from "react";
import { theme } from "../theme";
import { getHospitals, getHospitalInfections } from "../services/api";

function Stars({ rating }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 3 }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} style={{ fontSize: 15, lineHeight: 1, color: i <= rating ? theme.star : theme.starEmpty }}>
          ★
        </span>
      ))}
    </div>
  );
}

function exportCSV(hospitals, filename = "hospitals_selected.csv") {
  const headers = ["Facility ID", "Facility Name", "Address", "City", "State", "ZIP Code", "Type", "Ownership", "Emergency Services", "Overall Rating", "Phone", "HAI Worse", "HAI Better", "HAI Average"];
  const rows = hospitals.map((h) => [
    h.facility_id,
    h.facility_name,
    h.address,
    h.city,
    h.state,
    h.zip_code,
    h.hospital_type,
    h.hospital_ownership,
    h.emergency_services,
    h.overall_rating ?? "",
    h.telephone_number ?? "",
    h._infections?.worse ?? "",
    h._infections?.better ?? "",
    h._infections?.average ?? "",
  ]);
  const csv = [headers, ...rows].map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function HospitalCard({ hospital, expanded, onExpand, onClose, onInfectionsLoaded }) {
  const [infections, setInfections] = useState([]);
  const [loadingInfections, setLoadingInfections] = useState(false);

  useEffect(() => {
    if (!expanded) return;
    setLoadingInfections(true);
    getHospitalInfections(hospital.facility_id)
      .then((data) => {
        setInfections(data);
        const worse = data.filter(i => i.compared_to_national === "Worse than the National Benchmark").length;
        const better = data.filter(i => i.compared_to_national === "Better than the National Benchmark").length;
        const average = data.length - worse - better;
        onInfectionsLoaded({ worse, better, average });
      })
      .finally(() => setLoadingInfections(false));
  }, [expanded, hospital.facility_id]);

  const worse = infections.filter(i => i.compared_to_national === "Worse than the National Benchmark");
  const better = infections.filter(i => i.compared_to_national === "Better than the National Benchmark");
  const average = infections.length - worse.length - better.length;

  return (
    <article
      style={{
        background: theme.surface,
        border: `1px solid ${expanded ? theme.accent : theme.border}`,
        borderRadius: 14,
        padding: 20,
        boxShadow: expanded
          ? `0 0 0 2px ${theme.accent}22, 0 14px 28px -14px rgba(20,24,28,.26)`
          : "0 1px 2px rgba(20,24,28,.05), 0 8px 20px -14px rgba(20,24,28,.18)",
        display: "flex",
        flexDirection: "column",
        gap: 14,
        minHeight: 140,
        transition: "box-shadow .18s ease, border-color .18s ease",
        cursor: expanded ? "default" : "pointer",
      }}
      onClick={() => !expanded && onExpand()}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <div style={{ flex: 1 }}>
          <h3 style={{ margin: "0 0 6px", fontSize: 15.5, fontWeight: 600, lineHeight: 1.35, letterSpacing: "-0.01em" }}>
            {hospital.facility_name}
          </h3>
          <div style={{ fontSize: 13.5, color: theme.muted }}>
            {hospital.city}, {hospital.state}
          </div>
        </div>
        {expanded && (
          <button
            onClick={(e) => { e.stopPropagation(); onClose(); }}
            style={{
              background: "none",
              border: "none",
              fontSize: 18,
              color: theme.muted,
              cursor: "pointer",
              lineHeight: 1,
              padding: "0 2px",
            }}
          >
            ✕
          </button>
        )}
      </div>

      {expanded && (
        <>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, borderTop: `1px solid ${theme.border}`, paddingTop: 14 }}>
            {[
              { label: "Facility ID", value: hospital.facility_id },
              { label: "Address", value: hospital.address },
              { label: "ZIP Code", value: hospital.zip_code },
              { label: "Phone", value: hospital.telephone_number },
              { label: "Type", value: hospital.hospital_type },
              { label: "Ownership", value: hospital.hospital_ownership },
              { label: "Emergency Services", value: hospital.emergency_services },
            ].map(({ label, value }) => (
              <div key={label} style={{ display: "flex", gap: 10, fontSize: 13.5 }}>
                <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.faint, letterSpacing: "0.04em", minWidth: 130, paddingTop: 1 }}>
                  {label.toUpperCase()}
                </span>
                <span style={{ color: theme.ink, flex: 1 }}>{value ?? "—"}</span>
              </div>
            ))}
          </div>

          <div style={{ borderTop: `1px solid ${theme.border}`, paddingTop: 14 }}>
            <div style={{ fontFamily: theme.mono, fontSize: 10.5, color: theme.faint, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 10 }}>
              Healthcare-Associated Infections
            </div>

            {loadingInfections && (
              <div style={{ fontSize: 13, color: theme.muted }}>Loading...</div>
            )}

            {!loadingInfections && infections.length === 0 && (
              <div style={{ fontSize: 13, color: theme.muted }}>No infection data available.</div>
            )}

            {!loadingInfections && infections.length > 0 && (
              <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
                {[
                  { label: "▲ Worse", count: worse.length, color: "#c0392b" },
                  { label: "▼ Better", count: better.length, color: "#2f9e6f" },
                  { label: "— Average", count: average, color: "#6f8a95" },
                ].map(({ label, count, color }) => (
                  <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontFamily: theme.mono, fontSize: 16, fontWeight: 700, color }}>
                      {count}
                    </span>
                    <span style={{ fontFamily: theme.mono, fontSize: 10.5, color, letterSpacing: "0.04em" }}>
                      {label}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      <div style={{ marginTop: "auto", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, paddingTop: 14, borderTop: `1px solid #eef1f2` }}>
        <span style={{ fontFamily: theme.mono, fontSize: 12, color: theme.faint, letterSpacing: "0.04em" }}>
          ZIP {hospital.zip_code}
        </span>
        <Stars rating={hospital.overall_rating ?? 0} />
      </div>
    </article>
  );
}

const control = {
  background: "#1b272e",
  border: `1px solid #2c3b44`,
  borderRadius: 10,
  padding: "11px 14px",
  fontSize: 14,
  color: "#fff",
  outline: "none",
};

const pageBtn = (active) => ({
  background: active ? theme.accent : "#1b272e",
  border: `1px solid ${active ? theme.accent : "#2c3b44"}`,
  color: active ? "#fff" : "#a7b6bf",
  borderRadius: 9,
  padding: "9px 14px",
  fontSize: 13.5,
  fontFamily: theme.mono,
  cursor: "pointer",
});

export default function HospitalList() {
  const [open, setOpen] = useState(false);
  const [hospitals, setHospitals] = useState([]);
  const [stateFilter, setStateFilter] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState(null);
  const [selected, setSelected] = useState({});
  const [exportingState, setExportingState] = useState(false);
  const limit = 6;

  useEffect(() => {
    if (!open) return;
    getHospitals(page, limit, stateFilter, search).then(setHospitals);
  }, [page, stateFilter, search, open]);

  function handleExpand(hospital) {
    setExpandedId(hospital.facility_id);
    setSelected((prev) => ({
      ...prev,
      [hospital.facility_id]: { ...hospital },
    }));
  }

  function handleClose(facilityId) {
    setExpandedId(null);
    setSelected((prev) => {
      const next = { ...prev };
      delete next[facilityId];
      return next;
    });
  }

  function handleInfectionsLoaded(facilityId, infections) {
    setSelected((prev) => ({
      ...prev,
      [facilityId]: { ...prev[facilityId], _infections: infections },
    }));
  }

  function handleClear() {
    setStateFilter("");
    setSearch("");
    setPage(1);
    setSelected({});
    setExpandedId(null);
  }

  async function exportStateCSV() {
    if (!stateFilter) return;
    setExportingState(true);
    try {
      const response = await fetch(`/api/v1/hospitals/export?state=${stateFilter}`);
      const data = await response.json();
      exportCSV(data, `hospitals_${stateFilter}_all.csv`);
    } finally {
      setExportingState(false);
    }
  }

  const selectedList = Object.values(selected);

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
            Browse Hospitals
          </h2>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            5,419 facilities
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
          padding: "20px 22px",
          boxShadow: "0 4px 12px rgba(16,26,32,.3)",
        }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 20 }}>
            <input
              type="text"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search by hospital name..."
              style={{ ...control, flex: "1 1 220px" }}
            />
            <input
              type="text"
              value={stateFilter}
              onChange={(e) => { setStateFilter(e.target.value); setPage(1); }}
              placeholder="Filter by state (e.g. TX)"
              style={{ ...control, width: 180 }}
            />
            <button
              onClick={(e) => { e.stopPropagation(); handleClear(); }}
              style={{ ...control, cursor: "pointer", color: "#a7b6bf" }}
            >
              Clear
            </button>
            {hospitals.length > 0 && (
              <button
                onClick={(e) => { e.stopPropagation(); exportCSV(hospitals, `hospitals_${hospitals[0]?.state || "all"}_page.csv`); }}
                style={{ ...control, cursor: "pointer", color: theme.mint, borderColor: theme.mint }}
              >
                ↓ Export CSV
              </button>
            )}
            {stateFilter && hospitals.length > 0 && (
              <button
                onClick={(e) => { e.stopPropagation(); exportStateCSV(); }}
                disabled={exportingState}
                style={{ ...control, cursor: exportingState ? "wait" : "pointer", color: "#a78bfa", borderColor: "#a78bfa", opacity: exportingState ? 0.7 : 1 }}
              >
                {exportingState ? "Exporting..." : `↓ Export All ${stateFilter}`}
              </button>
            )}
            {selectedList.length > 0 && (
              <button
                onClick={(e) => { e.stopPropagation(); exportCSV(selectedList, "hospitals_selected.csv"); }}
                style={{ ...control, cursor: "pointer", color: "#f0a500", borderColor: "#f0a500" }}
              >
                ★ Export Selected ({selectedList.length})
              </button>
            )}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(288px, 1fr))", gap: 16, alignItems: "start" }}>
            {hospitals.map((h) => (
              <HospitalCard
                key={h.facility_id}
                hospital={h}
                expanded={expandedId === h.facility_id}
                onExpand={() => handleExpand(h)}
                onClose={() => handleClose(h.facility_id)}
                onInfectionsLoaded={(inf) => handleInfectionsLoaded(h.facility_id, inf)}
              />
            ))}
          </div>

          {hospitals.length === 0 && (
            <div style={{ background: theme.darkInput, border: `1px dashed #2c3b44`, borderRadius: 14, padding: "48px 24px", textAlign: "center", color: "#6f8a95", fontSize: 14.5 }}>
              No hospitals found.
            </div>
          )}

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginTop: 24 }}>
            <div style={{ fontFamily: theme.mono, fontSize: 12, color: "#6f8a95" }}>
              Page {page}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} style={{ ...control, borderRadius: 9, cursor: "pointer", fontSize: 13.5 }}>
                Prev
              </button>
              <button style={pageBtn(true)}>{page}</button>
              <button onClick={() => setPage((p) => p + 1)} disabled={hospitals.length < limit} style={{ ...control, borderRadius: 9, cursor: "pointer", fontSize: 13.5 }}>
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
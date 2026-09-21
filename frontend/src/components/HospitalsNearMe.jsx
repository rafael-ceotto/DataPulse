import React, { useState, useEffect } from "react";
import { theme } from "../theme";

const US_CITIES = [
  { label: "Alabama — Montgomery", lat: 32.3617, lng: -86.2792 },
  { label: "Alaska — Anchorage", lat: 61.2181, lng: -149.9003 },
  { label: "Arizona — Phoenix", lat: 33.4484, lng: -112.0740 },
  { label: "Arkansas — Little Rock", lat: 34.7465, lng: -92.2896 },
  { label: "California — Los Angeles", lat: 34.0522, lng: -118.2437 },
  { label: "Colorado — Denver", lat: 39.7392, lng: -104.9903 },
  { label: "Connecticut — Hartford", lat: 41.7658, lng: -72.6851 },
  { label: "Delaware — Wilmington", lat: 39.7447, lng: -75.5484 },
  { label: "Florida — Miami", lat: 25.7617, lng: -80.1918 },
  { label: "Georgia — Atlanta", lat: 33.7490, lng: -84.3880 },
  { label: "Hawaii — Honolulu", lat: 21.3069, lng: -157.8583 },
  { label: "Idaho — Boise", lat: 43.6150, lng: -116.2023 },
  { label: "Illinois — Chicago", lat: 41.8781, lng: -87.6298 },
  { label: "Indiana — Indianapolis", lat: 39.7684, lng: -86.1581 },
  { label: "Iowa — Des Moines", lat: 41.5868, lng: -93.6250 },
  { label: "Kansas — Wichita", lat: 37.6872, lng: -97.3301 },
  { label: "Kentucky — Louisville", lat: 38.2527, lng: -85.7585 },
  { label: "Louisiana — New Orleans", lat: 29.9511, lng: -90.0715 },
  { label: "Maine — Portland", lat: 43.6591, lng: -70.2568 },
  { label: "Maryland — Baltimore", lat: 39.2904, lng: -76.6122 },
  { label: "Massachusetts — Boston", lat: 42.3601, lng: -71.0589 },
  { label: "Michigan — Detroit", lat: 42.3314, lng: -83.0458 },
  { label: "Minnesota — Minneapolis", lat: 44.9778, lng: -93.2650 },
  { label: "Mississippi — Jackson", lat: 32.2988, lng: -90.1848 },
  { label: "Missouri — Kansas City", lat: 39.0997, lng: -94.5786 },
  { label: "Montana — Billings", lat: 45.7833, lng: -108.5007 },
  { label: "Nebraska — Omaha", lat: 41.2565, lng: -95.9345 },
  { label: "Nevada — Las Vegas", lat: 36.1699, lng: -115.1398 },
  { label: "New Hampshire — Manchester", lat: 42.9956, lng: -71.4548 },
  { label: "New Jersey — Newark", lat: 40.7357, lng: -74.1724 },
  { label: "New Mexico — Albuquerque", lat: 35.0844, lng: -106.6504 },
  { label: "New York — New York City", lat: 40.7128, lng: -74.0060 },
  { label: "North Carolina — Charlotte", lat: 35.2271, lng: -80.8431 },
  { label: "North Dakota — Fargo", lat: 46.8772, lng: -96.7898 },
  { label: "Ohio — Columbus", lat: 39.9612, lng: -82.9988 },
  { label: "Oklahoma — Oklahoma City", lat: 35.4676, lng: -97.5164 },
  { label: "Oregon — Portland", lat: 45.5051, lng: -122.6750 },
  { label: "Pennsylvania — Philadelphia", lat: 39.9526, lng: -75.1652 },
  { label: "Rhode Island — Providence", lat: 41.8240, lng: -71.4128 },
  { label: "South Carolina — Columbia", lat: 34.0007, lng: -81.0348 },
  { label: "South Dakota — Sioux Falls", lat: 43.5446, lng: -96.7311 },
  { label: "Tennessee — Nashville", lat: 36.1627, lng: -86.7816 },
  { label: "Texas — Houston", lat: 29.7604, lng: -95.3698 },
  { label: "Utah — Salt Lake City", lat: 40.7608, lng: -111.8910 },
  { label: "Vermont — Burlington", lat: 44.4759, lng: -73.2121 },
  { label: "Virginia — Virginia Beach", lat: 36.8529, lng: -75.9780 },
  { label: "Washington — Seattle", lat: 47.6062, lng: -122.3321 },
  { label: "Washington DC", lat: 38.9072, lng: -77.0369 },
  { label: "West Virginia — Charleston", lat: 38.3498, lng: -81.6326 },
  { label: "Wisconsin — Milwaukee", lat: 43.0389, lng: -87.9065 },
  { label: "Wyoming — Cheyenne", lat: 41.1400, lng: -104.8202 },
];

export default function HospitalsNearMe() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [hospitals, setHospitals] = useState([]);
  const [error, setError] = useState(null);
  const [radius, setRadius] = useState(25);
  const [minRating, setMinRating] = useState("");
  const [locationStatus, setLocationStatus] = useState(null);
  const [testCity, setTestCity] = useState("");
  const [currentCoords, setCurrentCoords] = useState(null);

  // Re-fetch when radius or minRating changes and we have coords
  useEffect(() => {
    if (!currentCoords) return;
    fetchHospitals(currentCoords.lat, currentCoords.lng, currentCoords.label, radius);
  }, [minRating, radius]);

  async function fetchHospitals(lat, lng, label, radiusOverride) {
    const activeRadius = radiusOverride ?? radius;
    setCurrentCoords({ lat, lng, label });
    setLoading(true);
    setError(null);
    setHospitals([]);
    setLocationStatus(`Searching near ${label}...`);

    try {
      const params = new URLSearchParams({ lat, lng, radius: activeRadius, limit: 50 });
      if (minRating) params.append("min_rating", minRating);
      const res = await fetch(`/api/v1/hospitals/nearby?${params}`);
      const data = await res.json();
      setHospitals(data);
      setLocationStatus(label);
    } catch (err) {
      setError("Failed to fetch nearby hospitals.");
    } finally {
      setLoading(false);
    }
  }

  async function findNearMe() {
    setLoading(true);
    setError(null);
    setHospitals([]);
    setLocationStatus("Getting your location...");

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        await fetchHospitals(latitude, longitude, `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`);
      },
      () => {
        setError("Could not get your location. Please allow location access or use a test city.");
        setLocationStatus(null);
        setLoading(false);
      }
    );
  }

  async function handleTestCity(e) {
    const value = e.target.value;
    setTestCity(value);
    if (!value) return;
    const city = US_CITIES.find(c => c.label === value);
    if (city) await fetchHospitals(city.lat, city.lng, city.label);
  }

  function ratingStars(rating) {
    if (!rating) return "—";
    return "★".repeat(rating) + "☆".repeat(5 - rating);
  }

  function ratingColor(rating) {
    if (!rating) return "#6f8a95";
    if (rating >= 4) return theme.mint;
    if (rating >= 3) return "#f1c40f";
    return "#ff6b6b";
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
            Hospitals Near Me
          </h2>
          <span style={{ fontFamily: theme.mono, fontSize: 11, color: theme.mint, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Geolocation
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

          {/* Controls */}
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 20 }}>
            <div>
              <div style={{ fontFamily: theme.mono, fontSize: 10.5, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 6 }}>
                Radius (miles)
              </div>
              <select
                value={radius}
                onChange={(e) => setRadius(Number(e.target.value))}
                style={{ background: theme.darkInput, border: `1px solid #2c3b44`, borderRadius: 8, padding: "10px 14px", color: "#fff", fontSize: 13, fontFamily: theme.mono, cursor: "pointer" }}
              >
                {[10, 25, 50, 100].map(r => <option key={r} value={r}>{r} miles</option>)}
              </select>
            </div>

            <div>
              <div style={{ fontFamily: theme.mono, fontSize: 10.5, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 6 }}>
                Min Rating
              </div>
              <select
                value={minRating}
                onChange={(e) => setMinRating(e.target.value)}
                style={{ background: theme.darkInput, border: `1px solid #2c3b44`, borderRadius: 8, padding: "10px 14px", color: "#fff", fontSize: 13, fontFamily: theme.mono, cursor: "pointer" }}
              >
                <option value="">Any rating</option>
                {[1, 2, 3, 4, 5].map(r => <option key={r} value={r}>{"★".repeat(r)} ({r}+)</option>)}
              </select>
            </div>

            <button
              onClick={findNearMe}
              disabled={loading}
              style={{
                background: loading ? "#1b272e" : theme.mint,
                color: loading ? "#6f8a95" : "#0c1418",
                border: "none",
                borderRadius: 10,
                padding: "11px 24px",
                fontSize: 14,
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? "Searching..." : "📍 Use my location"}
            </button>

            <div>
              <div style={{ fontFamily: theme.mono, fontSize: 10.5, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 6 }}>
                Or test with a US city
              </div>
              <select
                value={testCity}
                onChange={handleTestCity}
                disabled={loading}
                style={{ background: theme.darkInput, border: `1px solid #2c3b44`, borderRadius: 8, padding: "10px 14px", color: "#fff", fontSize: 13, fontFamily: theme.mono, cursor: "pointer", minWidth: 220 }}
              >
                <option value="">Select a city...</option>
                {US_CITIES.map(c => <option key={c.label} value={c.label}>{c.label}</option>)}
              </select>
            </div>
          </div>

          {locationStatus && !error && (
            <div style={{ fontFamily: theme.mono, fontSize: 11, color: "#6f8a95", marginBottom: 16 }}>
              📍 {locationStatus}
            </div>
          )}

          {error && (
            <div style={{ fontSize: 13, color: "#ff6b6b", marginBottom: 16 }}>{error}</div>
          )}

          {hospitals.length > 0 && (
            <>
              <div style={{ fontFamily: theme.mono, fontSize: 10.5, color: "#6f8a95", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 14 }}>
                {hospitals.length} hospitals found within {radius} miles
              </div>
              <div style={{ maxHeight: 500, overflowY: "auto", display: "flex", flexDirection: "column", gap: 10 }}>
                {hospitals.map((h) => (
                  <div
                    key={h.facility_id}
                    style={{
                      background: theme.dark,
                      border: `1px solid #1e2d35`,
                      borderRadius: 10,
                      padding: "14px 16px",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      flexWrap: "wrap",
                      gap: 8,
                    }}
                  >
                    <div style={{ flex: 1, minWidth: 200 }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: "#fff", marginBottom: 4 }}>
                        {h.facility_name}
                      </div>
                      <div style={{ fontSize: 12, color: "#6f8a95" }}>
                        {h.address}, {h.city}, {h.state} · {h.hospital_type}
                      </div>
                      {h.telephone_number && (
                        <div style={{ fontSize: 12, color: "#6f8a95", marginTop: 2 }}>
                          📞 {h.telephone_number}
                        </div>
                      )}
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                      <div style={{ fontFamily: theme.mono, fontSize: 13, fontWeight: 700, color: ratingColor(h.overall_rating) }}>
                        {ratingStars(h.overall_rating)}
                      </div>
                      <div style={{ fontFamily: theme.mono, fontSize: 11, color: "#a7b6bf" }}>
                        {h.distance_miles} mi away
                      </div>
                      {h.emergency_services === "Yes" && (
                        <div style={{ fontFamily: theme.mono, fontSize: 10, color: "#ff6b6b", letterSpacing: "0.06em", border: "1px solid #ff6b6b44", borderRadius: 4, padding: "2px 6px" }}>
                          ER
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {!loading && hospitals.length === 0 && !error && (
            <div style={{ color: "#6f8a95", fontSize: 13 }}>
              Use your location or select a US city to find nearby hospitals.
            </div>
          )}
        </div>
      )}
    </section>
  );
}
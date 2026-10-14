const NEAR_ME_PATTERNS = [
  /near me/i,
  /close to me/i,
  /nearest to me/i,
  /nearby me/i,
  /perto de mim/i,
  /pr[óo]ximo a mim/i,
  /pr[óo]xima a mim/i,
  /pr[óo]ximo de mim/i,
  /pr[óo]xima de mim/i,
  /na minha regi[ãa]o/i,
  /cerca de m[ií]/i,
];

// True only when the question is phrased about the device's own position
// ("near me" / "perto de mim"), not when it names a specific place
// ("perto de Copacabana") — those go through location_text/geocoding instead.
export function needsDeviceLocation(text) {
  return NEAR_ME_PATTERNS.some((re) => re.test(text));
}

export function getDeviceLocation(timeoutMs = 8000) {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(null), // denied, timed out, or unavailable — caller falls back
      { enableHighAccuracy: false, timeout: timeoutMs, maximumAge: 5 * 60 * 1000 }
    );
  });
}
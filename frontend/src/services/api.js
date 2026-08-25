const API_URL = "";

let cachedToken = null;
let tokenExpiry = null;

async function getToken() {
  if (cachedToken && tokenExpiry && Date.now() < tokenExpiry) {
    return cachedToken;
  }
  const response = await fetch("/api/v1/auth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: "username=admin&password=datapulse2024",
  });
  const data = await response.json();
  cachedToken = data.access_token;
  tokenExpiry = Date.now() + 55 * 60 * 1000; // 55 minutos
  return cachedToken;
}

export async function getHospitals(page = 1, limit = 20, state = "", search = "") {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
  });
  if (state) params.append("state", state);
  if (search) params.append("search", search);
  const response = await fetch(`${API_URL}/api/v1/hospitals?${params}`);
  return response.json();
}

export async function getHospitalById(facilityId) {
  const response = await fetch(`${API_URL}/api/v1/hospitals/${facilityId}`);
  return response.json();
}

export async function askAI(question) {
  const token = await getToken();
  const response = await fetch(`${API_URL}/api/v1/ai/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  });
  return response.json();
}
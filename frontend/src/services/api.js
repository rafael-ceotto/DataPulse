const API_URL = "";

let cachedToken = null;
let tokenExpiry = null;

export async function getToken() {
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
  tokenExpiry = Date.now() + 55 * 60 * 1000;
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

export async function askAI(question, conversationId = null) {
  const token = await getToken();

  const response = await fetch(`${API_URL}/api/v1/ai/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({ question, conversation_id: conversationId }),
  });

  const data = await response.json();

  if (data.explanation || data.sql) {
    return data;
  }

  const jobId = data.job_id;
  const maxAttempts = 60;
  const interval = 2000;

  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(resolve => setTimeout(resolve, interval));

    const pollResponse = await fetch(`${API_URL}/api/v1/ai/query/${jobId}`, {
      headers: { "Authorization": `Bearer ${token}` },
    });

    const pollData = await pollResponse.json();

    if (pollData.status === "done" || pollData.explanation || pollData.sql) {
      return pollData;
    }

    if (pollData.status === "failed") {
      throw new Error(pollData.error || "Query failed");
    }
  }

  throw new Error("Query timed out after 2 minutes");
}

export async function getHospitalInfections(facilityId) {
  const response = await fetch(`${API_URL}/api/v1/infections/${facilityId}`);
  if (!response.ok) return [];
  return response.json();
}

export async function saveToNotion(question, explanation, toolsUsed) {
  const token = await getToken();
  const response = await fetch("/api/v1/notion/save", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({
      question,
      explanation,
      tools_used: toolsUsed,
    }),
  });
  return response.json();
}
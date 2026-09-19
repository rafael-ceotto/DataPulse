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

import {supabase} from './supabase'

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

  // Cached result returned directly
  if (data.explanation || data.sql) {
    return data;
  }

  const jobId = data.job_id;

  // Wait for result via Supabase Realtime
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      channel.unsubscribe();
      reject(new Error("Query timed out after 2 minutes"));
    }, 120000);

    const channel = supabase
      .channel('ai-query-done')
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'events',
        filter: `type=eq.ai_query_done`,
      }, (payload) => {
        if (payload.new?.payload?.job_id === jobId) {
          clearTimeout(timeout);
          channel.unsubscribe();
          // Fetch the actual result
          fetch(`${API_URL}/api/v1/ai/query/${jobId}`, {
            headers: { "Authorization": `Bearer ${token}` },
          })
            .then(r => r.json())
            .then(result => resolve(result))
            .catch(reject);
        }
      })
      .subscribe();
  });
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
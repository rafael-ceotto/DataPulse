const API_URL = "";

let cachedToken = null;
let tokenExpiry = null;

export async function getToken() {
  if (cachedToken && tokenExpiry && Date.now() < tokenExpiry) {
    return cachedToken;
  }
  const apiUsername = import.meta.env.VITE_API_USERNAME;
  const apiPassword = import.meta.env.VITE_API_PASSWORD;
  if (!apiUsername || !apiPassword) {
    throw new Error(
      "VITE_API_USERNAME/VITE_API_PASSWORD are not set. Create frontend/.env.local (see .env.example)."
    );
  }
  const response = await fetch("/api/v1/auth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `username=${encodeURIComponent(apiUsername)}&password=${encodeURIComponent(apiPassword)}`,
  });
  const data = await response.json();
  cachedToken = data.access_token;
  tokenExpiry = Date.now() + 55 * 60 * 1000;
  return cachedToken;
}

export async function getHospitals(
  page = 1, limit = 20, state = "", search = "", country = "US",
  { acceptsMedicare = false, insuranceOperator = "", procedureCategory = "" } = {}
) {
  const params = new URLSearchParams({ page: page.toString(), limit: limit.toString(), country });
  if (state) params.append("state", state);
  if (search) params.append("search", search);
  if (acceptsMedicare) params.append("accepts_medicare", "true");
  if (insuranceOperator) params.append("insurance_operator", insuranceOperator);
  if (procedureCategory) params.append("procedure_category", procedureCategory);
  const response = await fetch(`${API_URL}/api/v1/hospitals?${params}`);
  return response.json();
}

export async function getHospitalById(facilityId) {
  const response = await fetch(`${API_URL}/api/v1/hospitals/${facilityId}`);
  return response.json();
}

import {supabase} from './supabase'

export async function askAI(question, conversationId = null, country = "US", userLat = null, userLng = null) {
  const token = await getToken();

  const response = await fetch(`${API_URL}/api/v1/ai/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({ question, conversation_id: conversationId, country, user_lat: userLat, user_lng: userLng }),
  });

    const data = await response.json();

  // Cached result returned directly
  if (data.explanation || data.sql) {
    return data;
  }

  const jobId = data.job_id;

  // Wait for result via Supabase Realtime, with a polling safety net.
  // Was 120000ms (2 min), but a compound comparison question (e.g. comparing
  // two states' rating + infections + CMS docs) can need 4-5 real Groq calls
  // in ask_agent(), and under the account's current rate limit each one can
  // carry a real Retry-After wait of up to 30s — a live test hit ~113s just
  // to gather tool results, before the final synthesis call even ran, so 2
  // minutes wasn't enough margin. Raised to 3 minutes. This is a band-aid for
  // the account's Groq TPM limit (see DataPulse_Pending_Items.md), not a fix
  // for it — if compound questions keep approaching this ceiling too, the
  // real fix is reducing Groq round-trips per question or a higher-TPM plan.
  //
  // The Realtime subscription below is set up AFTER the POST above already
  // returned job_id — subscribing takes a real WebSocket handshake, which
  // can take longer than a fast job (a guardrail refusal can finish in
  // ~1-2s). If the backend publishes "job done" before the subscription is
  // confirmed, Realtime does not replay it, and the UI used to sit waiting
  // for the full 3-minute timeout even though the answer was ready almost
  // instantly. The polling fallback below guarantees we notice within a few
  // seconds regardless of what Realtime does.
  return new Promise((resolve, reject) => {
    let settled = false;

    const finish = (fn, arg) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      clearInterval(pollInterval);
      channel.unsubscribe();
      fn(arg);
    };

    const fetchResult = () => {
      fetch(`${API_URL}/api/v1/ai/query/${jobId}`, {
        headers: { "Authorization": `Bearer ${token}` },
      })
        .then(r => r.json())
        .then(result => {
          if (!result || result.status === "queued" || result.status === "processing") return;
          if (result.status === "failed") finish(reject, new Error(result.error || "AI query failed on the server."));
          else finish(resolve, result);
        })
        .catch(() => {
          // transient poll error — ignore, Realtime or the next poll may still land
        });
    };

    const timeout = setTimeout(() => {
      finish(reject, new Error("Query timed out after 3 minutes"));
    }, 180000);

    const pollInterval = setInterval(fetchResult, 3000);

    const channel = supabase
      .channel(`ai-query-done-${jobId}`)
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'events',
        filter: `type=eq.ai_query_done`,
      }, (payload) => {
        if (payload.new?.payload?.job_id === jobId) {
          fetchResult();
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

export async function getHospitalEnrollment(facilityId){
  const response =  await fetch(`${API_URL}/api/v1/enrollments/${facilityId}`)
  if (!response.ok) return null;
  return response.json();
}

export async function getInsuranceNetwork(facilityId) {
  const response = await fetch(`${API_URL}/api/v1/insurance-network/${facilityId}`);
  if (!response.ok) return null;
  return response.json();
}
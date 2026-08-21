const API_URL = "";

export async function getHospitals(page = 1, limit = 20, state = "") {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
  });

  if (state) {
    params.append("state", state);
  }

  const response = await fetch(
    `${API_URL}/api/v1/hospitals?${params}`
  );

  return response.json();
}

export async function getHospitalById(facilityId) {
  const response = await fetch(
    `${API_URL}/api/v1/hospitals/${facilityId}`
  );

  return response.json();
}

export async function askAI(question) {
  const response = await fetch(`${API_URL}/api/v1/ai/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  return response.json();
}
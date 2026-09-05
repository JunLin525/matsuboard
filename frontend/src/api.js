const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }
  return res.json();
}

export function getFlights(date) {
  return getJSON(`/api/flights${date ? `?date=${date}` : ""}`);
}

export function getFerries(date) {
  return getJSON(`/api/ferries${date ? `?date=${date}` : ""}`);
}

export function getAdvisory(date) {
  return getJSON(`/api/advisory${date ? `?date=${date}` : ""}`);
}

export function getStats(days = 3) {
  return getJSON(`/api/stats?days=${days}`);
}

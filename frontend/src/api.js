// 去掉結尾斜線：VITE_API_BASE 若帶了結尾 "/"，跟下面 path 開頭的 "/" 疊在一起
// 會變成雙斜線，Vercel 對雙斜線路徑會回一個沒有 CORS header 的 308 redirect，
// 瀏覽器就會誤判成 CORS 被擋。
const API_BASE = (import.meta.env.VITE_API_BASE || "http://localhost:8000").replace(/\/+$/, "");

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

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function matchStudent(profile) {
  const res = await fetch(`${API_BASE}/match`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ? JSON.stringify(detail.detail) : `Request failed (${res.status})`);
  }

  return res.json();
}

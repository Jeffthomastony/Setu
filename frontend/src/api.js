const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/**
 * Parse a fetch Response into a human-readable error string.
 * Includes the HTTP status, URL, and any backend detail message.
 */
async function parseError(res, url) {
  let detail = null;
  try {
    const body = await res.json();
    // FastAPI validation errors come back as { detail: [...] }
    if (Array.isArray(body?.detail)) {
      detail = body.detail
        .map((e) => `${e.loc?.join(".")} — ${e.msg}`)
        .join("; ");
    } else if (typeof body?.detail === "string") {
      detail = body.detail;
    } else if (typeof body === "string") {
      detail = body;
    }
  } catch {
    // Body wasn't JSON — try raw text
    try {
      detail = await res.text();
    } catch {
      detail = null;
    }
  }

  const statusText = res.statusText || "Unknown error";
  const base = `${res.status} ${statusText} (${url})`;
  return detail ? `${base}: ${detail}` : base;
}

/**
 * Check connectivity to the backend and throw a clear error if it's down.
 */
async function guardedFetch(url, options = {}) {
  let res;
  try {
    res = await fetch(url, options);
  } catch (networkErr) {
    // Network-level failure — server is unreachable
    throw new Error(
      `Cannot reach the backend at ${API_BASE}. ` +
        `Is the server running? (Start it with: uvicorn app.main:app --reload --port 8000)\n` +
        `Network error: ${networkErr.message}`
    );
  }

  if (!res.ok) {
    const msg = await parseError(res, url);
    throw new Error(msg);
  }

  return res;
}

export async function matchStudent(profile) {
  const url = `${API_BASE}/match`;
  const res = await guardedFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  return res.json();
}

export async function matchSeniorCitizen(profile) {
  const url = `${API_BASE}/match/senior`;
  const res = await guardedFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  return res.json();
}

export async function searchSchemes(query) {
  const url = `${API_BASE}/search?q=${encodeURIComponent(query)}`;
  const res = await guardedFetch(url);
  return res.json();
}

export async function explainScheme(schemeId) {
  const url = `${API_BASE}/explain/${encodeURIComponent(schemeId)}`;
  const res = await guardedFetch(url);
  return res.json();
}

export async function askScheme(schemeId, question) {
  const url = `${API_BASE}/ask/${encodeURIComponent(schemeId)}?q=${encodeURIComponent(question)}`;
  const res = await guardedFetch(url);
  return res.json();
}

// Fetches the live scheme count/state count for the landing page trust stats,
// so those numbers stay accurate as the dataset grows instead of being hardcoded.
export async function getSchemeStats() {
  const url = `${API_BASE}/schemes`;
  const res = await guardedFetch(url);
  const schemes = await res.json();
  const states = new Set(
    schemes.map((s) => s.state).filter((s) => s && s.toLowerCase() !== "national")
  );
  return { totalSchemes: schemes.length, totalStates: states.size };
}

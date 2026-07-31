import { useState } from "react";
import { searchSchemes } from "../api";
import ResultCard from "./ResultCard";

// ── Quick-search chip suggestions ─────────────────────────────────────────────
const QUICK_CHIPS = [
  { label: "🎓 Post-matric", query: "post matric scholarship" },
  { label: "👧 Girls scholarship", query: "girls scholarship female" },
  { label: "🏷️ SC/ST merit", query: "SC ST merit scholarship" },
  { label: "♿ Disability", query: "disability scholarship persons with disability" },
  { label: "🕌 Minority", query: "minority scholarship Muslim Christian Sikh" },
  { label: "💰 Low income", query: "income below 1 lakh low income family" },
  { label: "🧡 Orphan support", query: "orphan single parent scholarship" },
  { label: "🔬 Research / PhD", query: "research fellowship doctoral PhD" },
  { label: "🌏 OBC backward class", query: "OBC backward class scholarship" },
  { label: "🌾 Rural student", query: "rural student agriculture scheme" },
];

function SkeletonCard() {
  return (
    <div className="skeleton-card" aria-hidden="true">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px" }}>
        <div className="skeleton-line w-60" />
        <div className="skeleton-line" style={{ width: "80px", flexShrink: 0 }} />
      </div>
      <div className="skeleton-line w-40" />
      <div className="skeleton-line w-80" />
      <div className="skeleton-line w-60" />
    </div>
  );
}

function EmptyState({ query }) {
  return (
    <div className="empty-state">
      <span className="empty-state-icon">🔍</span>
      <h3>No schemes found</h3>
      <p>
        No schemes matched <strong>"{query}"</strong>. Try a different keyword,
        a scheme name, or a category like "girls", "orphan", or "disability".
      </p>
    </div>
  );
}

export default function SearchPage({ onBack }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastQuery, setLastQuery] = useState("");

  async function handleSearch(e) {
    e?.preventDefault();
    const q = typeof e === "string" ? e : query.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    setLastQuery(q);
    try {
      const data = await searchSchemes(q);
      setResults(data);
    } catch (err) {
      setError(err.message || "Search failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  function handleChipClick(chipQuery) {
    setQuery(chipQuery);
    setLoading(true);
    setError(null);
    setLastQuery(chipQuery);
    searchSchemes(chipQuery)
      .then((data) => setResults(data))
      .catch((err) => setError(err.message || "Search failed."))
      .finally(() => setLoading(false));
  }

  return (
    <div className="page-content">
      <button className="back-link" onClick={onBack} aria-label="Back to home">
        ← Back
      </button>

      <div className="search-page">
        <h2>Search Schemes</h2>
        <p className="ask-hint">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
          </svg>
          Try searching by scheme name, category, or condition — or tap a chip below
        </p>

        <form className="search-form" onSubmit={handleSearch} role="search">
          <div className="search-input-wrapper">
            <span className="search-input-icon" aria-hidden="true">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
            </span>
            <input
              id="search-input"
              type="search"
              placeholder='e.g. "NMMS", "girls scholarship", "disability"…'
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoComplete="off"
            />
          </div>
          <button id="btn-search" type="submit" disabled={loading || !query.trim()}>
            {loading ? (
              <>
                <span className="spinner" style={{ borderColor: "rgba(255,255,255,0.4)", borderTopColor: "#fff" }} />
                Searching…
              </>
            ) : (
              "Search"
            )}
          </button>
        </form>

        {/* AI Smart Search Chips */}
        <div className="search-chips" role="group" aria-label="Quick search suggestions">
          <span className="search-chips-label">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            Quick picks
          </span>
          {QUICK_CHIPS.map((chip) => (
            <button
              key={chip.query}
              className={`search-chip ${lastQuery === chip.query ? "active" : ""}`}
              onClick={() => handleChipClick(chip.query)}
              type="button"
              disabled={loading}
            >
              {chip.label}
            </button>
          ))}
        </div>

        {error && (
          <p className="error-banner" role="alert">
            ⚠️ {error}
          </p>
        )}

        {/* Skeleton loading */}
        {loading && (
          <div className="results-list" aria-label="Loading results">
            {[0, 1, 2].map((i) => <SkeletonCard key={i} />)}
          </div>
        )}

        {/* Results */}
        {!loading && results !== null && (
          <>
            {results.length === 0 ? (
              <EmptyState query={lastQuery} />
            ) : (
              <>
                <div className="results-header">
                  <span className="results-title">Results for "{lastQuery}"</span>
                  <span className="results-count-badge">{results.length}</span>
                </div>
                <div className="results-list">
                  {results.map((r, i) => (
                    <ResultCard key={r.scheme_id} result={r} index={i} />
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

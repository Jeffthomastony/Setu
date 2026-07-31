import { useState } from "react";
import { searchSchemes } from "../api";

export default function SearchPage({ onBack }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await searchSchemes(query.trim());
      setResults(data);
    } catch (err) {
      setError(err.message || "Search failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="search-page">
      <button className="back-link" onClick={onBack}>
        &larr; Back
      </button>

      <h2>Search schemes</h2>

      <form className="search-form" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="e.g. NMMS, girls scholarship, orphan..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <p className="error-banner">{error}</p>}

      {results && (
        <div className="results-list">
          {results.length === 0 && <p>No schemes found for that search.</p>}
          {results.map((r) => (
            <article className="result-card" key={r.scheme_id}>
              <header>
                <h3>{r.scheme_name}</h3>
                <span className="score-badge">{r.relevance_score}% relevant</span>
              </header>

              {r.department && <p className="department">{r.department}</p>}
              <p>{r.description}</p>

              {r.required_documents?.length > 0 && (
                <details>
                  <summary>Documents you'll need</summary>
                  <ul>
                    {r.required_documents.map((doc) => (
                      <li key={doc}>{doc}</li>
                    ))}
                  </ul>
                </details>
              )}

              <div className="result-links">
                {r.official_website && (
                  <a href={r.official_website} target="_blank" rel="noreferrer">
                    Official website
                  </a>
                )}
                {r.application_portal && r.application_portal !== r.official_website && (
                  <a href={r.application_portal} target="_blank" rel="noreferrer">
                    Apply here
                  </a>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

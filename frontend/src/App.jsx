import { useState } from "react";
import StudentForm from "./components/StudentForm";
import ResultCard from "./components/ResultCard";
import { matchStudent } from "./api";
import "./App.css";

function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(profile) {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = await matchStudent(profile);
      setResults(data);
    } catch (err) {
      setError(err.message || "Something went wrong while matching. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Setu</h1>
        <p className="tagline">
          "Setu" means bridge — find the scholarships and government schemes you qualify for but never hear about.
        </p>
      </header>

      <main>
        <StudentForm onSubmit={handleSubmit} loading={loading} />

        {error && <p className="error-banner">{error}</p>}

        {results && (
          <section className="results-section">
            <h2>{results.length} scheme{results.length !== 1 ? "s" : ""} ranked for you</h2>
            <div className="results-list">
              {results.map((r) => (
                <ResultCard key={r.scheme_id} result={r} />
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;

import { useState } from "react";
import StudentForm from "./components/StudentForm";
import ResultCard from "./components/ResultCard";
import LandingPage from "./components/LandingPage";
import SearchPage from "./components/SearchPage";
import AskPage from "./components/AskPage";
import Logo from "./components/Logo";
import { matchStudent } from "./api";
import "./App.css";

function App() {
  const [view, setView] = useState("landing"); // 'landing' | 'search' | 'ask' | 'form'
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

  function goHome() {
    setView("landing");
    setResults(null);
    setError(null);
  }

  return (
    <div className="app-shell">
      {view !== "landing" && (
        <header className="app-header-bar">
          <button className="logo-button" onClick={goHome} aria-label="Back to home">
            <Logo size={32} />
          </button>
        </header>
      )}

      {view === "landing" && <LandingPage onSelect={setView} />}

      {view === "search" && <SearchPage onBack={goHome} />}

      {view === "ask" && <AskPage onBack={goHome} />}

      {view === "form" && (
        <main>
          <button className="back-link" onClick={goHome}>
            &larr; Back
          </button>

          <StudentForm onSubmit={handleSubmit} loading={loading} />

          {error && <p className="error-banner">{error}</p>}

          {results && (
            <section className="results-section">
              <h2>
                {results.length} scheme{results.length !== 1 ? "s" : ""} ranked for you
              </h2>
              <div className="results-list">
                {results.map((r) => (
                  <ResultCard key={r.scheme_id} result={r} />
                ))}
              </div>
            </section>
          )}
        </main>
      )}
    </div>
  );
}

export default App;

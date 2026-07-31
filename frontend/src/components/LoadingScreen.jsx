import { useEffect, useState } from "react";
import Logo from "./Logo";

/**
 * Full-page loading screen shown when the app initialises or during heavy
 * async operations. AMD-inspired dark design with animated logo and
 * progress bar. Used in App.jsx as the initial splash before mounting the
 * main UI.
 */
export default function LoadingScreen({ message = "Initialising…", progress = null }) {
  const [dots, setDots] = useState("");

  useEffect(() => {
    const id = setInterval(() => {
      setDots((d) => (d.length >= 3 ? "" : d + "."));
    }, 420);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="loading-screen" role="status" aria-live="polite" aria-label="Loading Setu">
      {/* Background grid */}
      <div className="loading-grid" aria-hidden="true" />

      {/* Animated scan line */}
      <div className="loading-scanline" aria-hidden="true" />

      {/* Center content */}
      <div className="loading-content">
        {/* Logo with pulse ring */}
        <div className="loading-logo-wrap">
          <div className="loading-logo-ring loading-logo-ring-1" aria-hidden="true" />
          <div className="loading-logo-ring loading-logo-ring-2" aria-hidden="true" />
          <Logo size={64} showText={false} white />
        </div>

        {/* Wordmark */}
        <div className="loading-wordmark">
          <span className="loading-wordmark-setu">SETU</span>
          <span className="loading-wordmark-sub">AI · Scholarship Discovery</span>
        </div>

        {/* Progress bar */}
        {progress !== null ? (
          <div className="loading-progress-track" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}>
            <div className="loading-progress-bar" style={{ width: `${progress}%` }} />
          </div>
        ) : (
          <div className="loading-progress-track">
            <div className="loading-progress-indeterminate" />
          </div>
        )}

        {/* Message */}
        <p className="loading-message">{message}{dots}</p>
      </div>

      {/* Corner accent marks — AMD style */}
      <div className="loading-corner loading-corner-tl" aria-hidden="true" />
      <div className="loading-corner loading-corner-tr" aria-hidden="true" />
      <div className="loading-corner loading-corner-bl" aria-hidden="true" />
      <div className="loading-corner loading-corner-br" aria-hidden="true" />
    </div>
  );
}

/**
 * Inline spinner — small loading indicator for button/inline use.
 */
export function InlineSpinner({ size = 20, color = "#fff" }) {
  return (
    <span
      className="setu-spinner"
      style={{ width: size, height: size, borderTopColor: color }}
      aria-hidden="true"
    />
  );
}

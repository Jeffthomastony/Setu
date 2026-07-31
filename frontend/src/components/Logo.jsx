/**
 * Setu Logo Component
 * AMD-inspired geometric bridge mark with sharp angles and gradient accent.
 * The bridge represents "Setu" (Sanskrit: bridge) — connecting students to
 * government schemes they qualify for but never hear about.
 */
export default function Logo({ size = 40, showText = true, white = false, mono = false }) {
  const accent1 = white || mono ? "#ffffff" : "#ED1C24";
  const accent2 = white || mono ? "rgba(255,255,255,0.7)" : "#FF6B35";
  const textColor = white ? "#ffffff" : mono ? "var(--clr-text-strong, #111)" : "var(--clr-text-strong, #0d0d14)";
  const strokeColor = white ? "#ffffff" : mono ? "var(--clr-text-strong, #111)" : "#0d0d14";

  return (
    <div className="logo" style={{ display: "inline-flex", alignItems: "center", gap: `${size * 0.25}px` }}>
      <svg
        width={size}
        height={size * 0.75}
        viewBox="0 0 64 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="setu-arch-grad" x1="0" y1="0" x2="64" y2="0" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor={accent1} />
            <stop offset="100%" stopColor={accent2} />
          </linearGradient>
          <filter id="setu-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Main arch — sharp angular geometry */}
        <path
          d="M2 44 L14 22 L32 10 L50 22 L62 44"
          stroke="url(#setu-arch-grad)"
          strokeWidth="4"
          strokeLinecap="square"
          strokeLinejoin="miter"
          fill="none"
          filter="url(#setu-glow)"
        />

        {/* Left pillar */}
        <line x1="2" y1="44" x2="2" y2="48" stroke={accent1} strokeWidth="4" strokeLinecap="square" />
        {/* Right pillar */}
        <line x1="62" y1="44" x2="62" y2="48" stroke={accent2} strokeWidth="4" strokeLinecap="square" />
        {/* Base road */}
        <line x1="2" y1="48" x2="62" y2="48" stroke={strokeColor === "#0d0d14" ? "var(--clr-border, #e8e4f0)" : strokeColor} strokeWidth="2.5" strokeLinecap="square" opacity="0.4" />

        {/* Vertical suspension cables */}
        <line x1="14" y1="22" x2="14" y2="44" stroke={strokeColor === "#0d0d14" ? "var(--clr-text-muted, #6b7280)" : "rgba(255,255,255,0.5)"} strokeWidth="1.5" strokeDasharray="2 2" />
        <line x1="32" y1="10" x2="32" y2="44" stroke={strokeColor === "#0d0d14" ? "var(--clr-text-muted, #6b7280)" : "rgba(255,255,255,0.5)"} strokeWidth="1.5" strokeDasharray="2 2" />
        <line x1="50" y1="22" x2="50" y2="44" stroke={strokeColor === "#0d0d14" ? "var(--clr-text-muted, #6b7280)" : "rgba(255,255,255,0.5)"} strokeWidth="1.5" strokeDasharray="2 2" />

        {/* Node dots at joints */}
        <circle cx="14" cy="22" r="3" fill={accent1} />
        <circle cx="50" cy="22" r="3" fill={accent2} />

        {/* Apex node — glowing accent */}
        <circle cx="32" cy="10" r="4.5" fill={accent1} filter="url(#setu-glow)" />
        <circle cx="32" cy="10" r="2.5" fill="#fff" opacity={white || mono ? "0.9" : "0.95"} />
      </svg>

      {showText && (
        <span
          className="logo-text"
          style={{
            color: textColor,
            fontSize: `${size * 0.42}px`,
            fontWeight: 900,
            letterSpacing: "-0.04em",
            fontFamily: "'Inter', 'Barlow', system-ui, sans-serif",
            lineHeight: 1,
            userSelect: "none",
          }}
        >
          SETU
        </span>
      )}
    </div>
  );
}

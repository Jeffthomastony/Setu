export default function Logo({ size = 40, showText = true }) {
  return (
    <div className="logo">
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <path
          d="M4 34C4 34 12 18 24 18C36 18 44 34 44 34"
          stroke="currentColor"
          strokeWidth="4"
          strokeLinecap="round"
        />
        <line x1="4" y1="34" x2="4" y2="42" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
        <line x1="44" y1="34" x2="44" y2="42" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
        <line x1="4" y1="42" x2="44" y2="42" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
        <line x1="14" y1="27" x2="14" y2="34" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        <line x1="24" y1="18" x2="24" y2="34" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        <line x1="34" y1="27" x2="34" y2="34" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
      {showText && <span className="logo-text">Setu</span>}
    </div>
  );
}

export function Bubble({ onClick, color }: { onClick: () => void; color: string }) {
  return (
    <button className="mc-bubble" style={{ background: color }} onClick={onClick} aria-label="Open chat">
      ?
    </button>
  );
}

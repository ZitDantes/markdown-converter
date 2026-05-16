type QueueDropOverlayProps = {
  visible: boolean;
};

export function QueueDropOverlay({ visible }: QueueDropOverlayProps) {
  if (!visible) {
    return null;
  }
  return (
    <div
      className="queue-drop-overlay"
      role="status"
      aria-live="polite"
      aria-label="Déposer pour ajouter à la file"
    >
      <span className="queue-drop-overlay__hint">Déposer pour ajouter à la file…</span>
    </div>
  );
}

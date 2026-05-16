type FooterBarProps = {
  batchPercent: number;
  itemCount: number;
  doneCount: number;
  canConvert: boolean;
  bridgeReady: boolean;
  onConvert: () => void;
};

export function FooterBar({
  batchPercent,
  itemCount,
  doneCount,
  canConvert,
  bridgeReady,
  onConvert,
}: FooterBarProps) {
  const pct = Math.round(batchPercent * 100);
  const queued = Math.max(0, itemCount - doneCount);
  const statusLabel =
    itemCount === 0
      ? "Ajoutez des fichiers pour commencer"
      : queued > 0
        ? `${queued} en attente`
        : doneCount > 0
          ? "Terminé"
          : "Prêt";

  return (
    <footer className="footer-bar">
      <div className="footer-bar__progress-block">
        <div className="footer-bar__meta">
          <span className="footer-bar__status">{statusLabel}</span>
          {itemCount > 0 && (
            <span className="footer-bar__counts">
              {doneCount}/{itemCount} convertis
            </span>
          )}
          {itemCount > 0 && (
            <span className="footer-bar__pct">{pct} %</span>
          )}
        </div>
        <div className="footer-bar__track" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
          <span className="footer-bar__fill" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <button
        type="button"
        className="btn btn--primary btn--lg"
        disabled={!bridgeReady || !canConvert}
        onClick={onConvert}
      >
        Convertir
      </button>
    </footer>
  );
}

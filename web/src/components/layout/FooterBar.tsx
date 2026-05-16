type FooterBarProps = {
  batchPercent: number;
  itemCount: number;
  doneCount: number;
  canConvert: boolean;
  bridgeReady: boolean;
  journalOpen: boolean;
  onToggleJournal: () => void;
  onConvert: () => void;
};

export function FooterBar({
  batchPercent,
  itemCount,
  doneCount,
  canConvert,
  bridgeReady,
  journalOpen,
  onToggleJournal,
  onConvert,
}: FooterBarProps) {
  const pct = Math.round(batchPercent * 100);
  const statusLabel =
    itemCount === 0
      ? "Ajoutez des fichiers pour commencer"
      : doneCount >= itemCount && itemCount > 0
        ? "Terminé"
        : pct > 0 && pct < 100
          ? "Conversion en cours…"
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
        className={`btn btn--sm btn--ghost footer-bar__journal${journalOpen ? " footer-bar__journal--active" : ""}`}
        aria-pressed={journalOpen}
        title="Afficher ou masquer le journal de conversion"
        onClick={onToggleJournal}
      >
        Journal
      </button>
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

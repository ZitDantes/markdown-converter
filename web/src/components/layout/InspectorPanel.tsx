type InspectorTab = "preview" | "output" | "details";

type InspectorPanelProps = {
  tab: InspectorTab;
  onTabChange: (tab: InspectorTab) => void;
  hasSelection: boolean;
};

const TABS: { id: InspectorTab; label: string }[] = [
  { id: "preview", label: "Aperçu" },
  { id: "output", label: "Sortie" },
  { id: "details", label: "Détails" },
];

export function InspectorPanel({ tab, onTabChange, hasSelection }: InspectorPanelProps) {
  return (
    <aside className="inspector" aria-label="Inspecteur">
      <div className="inspector__tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`inspector__tab${tab === t.id ? " inspector__tab--active" : ""}`}
            onClick={() => onTabChange(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="inspector__content" role="tabpanel">
        {!hasSelection ? (
          <p className="inspector__empty">Sélectionnez un fichier dans la file pour afficher l’inspecteur.</p>
        ) : (
          <p className="inspector__placeholder">
            Contenu « {TABS.find((t) => t.id === tab)?.label} » — parité fonctionnelle PLO-51+.
          </p>
        )}
      </div>
    </aside>
  );
}

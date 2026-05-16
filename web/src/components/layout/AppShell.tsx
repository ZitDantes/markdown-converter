import type { ReactNode } from "react";
import { TitleBar } from "./TitleBar";

type AppShellProps = {
  isDark: boolean;
  onToggleTheme: () => void;
  bridgeStatus: "loading" | "ready" | "error";
  bridgeError: string | null;
  main: ReactNode;
  inspector: ReactNode;
  footer: ReactNode;
  logDrawer: ReactNode;
};

export function AppShell({
  isDark,
  onToggleTheme,
  bridgeStatus,
  bridgeError,
  main,
  inspector,
  footer,
  logDrawer,
}: AppShellProps) {
  return (
    <div className="app-shell" data-bridge-status={bridgeStatus}>
      <TitleBar
        right={
          <>
            <span className="pill pill--pandoc" title="Statut Pandoc — PLO-50">
              Pandoc · local
            </span>
            <button type="button" className="btn btn--sm btn--ghost" onClick={onToggleTheme}>
              {isDark ? "Clair" : "Sombre"}
            </button>
          </>
        }
      />
      {bridgeStatus === "error" && (
        <p className="bridge-banner bridge-banner--error" role="alert">
          Pont indisponible : {bridgeError}
        </p>
      )}
      {bridgeStatus === "loading" && (
        <p className="bridge-banner">Connexion au pont Python…</p>
      )}
      <div className="app-shell__body">
        <div className="app-shell__main">{main}</div>
        {inspector}
      </div>
      {footer}
      {logDrawer}
    </div>
  );
}

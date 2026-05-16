import type { ReactNode } from "react";

type TitleBarProps = {
  right?: ReactNode;
};

/** Barre d’outils sous la titlebar native Qt (pas de feux ni titre dupliqués). */
export function TitleBar({ right }: TitleBarProps) {
  if (!right) return null;

  return (
    <header className="titlebar">
      <div className="titlebar__actions">{right}</div>
    </header>
  );
}

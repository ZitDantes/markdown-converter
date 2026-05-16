import { useCallback, useEffect, useState } from "react";

export type ThemeMode = "light" | "dark";

const STORAGE_KEY = "markdown-converter.theme";

function readStoredTheme(): ThemeMode {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v === "light" || v === "dark") return v;
  } catch {
    /* WebEngine / file: peut restreindre localStorage */
  }
  return "light";
}

export function useTheme() {
  const [theme, setThemeState] = useState<ThemeMode>(readStoredTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setThemeState((t) => (t === "light" ? "dark" : "light"));
  }, []);

  return { theme, isDark: theme === "dark", toggleTheme };
}

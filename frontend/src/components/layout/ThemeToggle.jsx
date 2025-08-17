import React from "react";
import { Sun, Moon } from "lucide-react";

export default function ThemeToggle() {
  const [dark, setDark] = React.useState(() =>
    document.documentElement.classList.contains("dark")
  );

  React.useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  React.useEffect(() => {
    const saved = localStorage.getItem("theme");
    if (saved) {
      document.documentElement.classList.toggle("dark", saved === "dark");
      setDark(saved === "dark");
    }
  }, []);

  return (
    <button
      className="inline-flex h-9 w-9 items-center justify-center rounded-md border bg-background text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
      onClick={() => setDark((v) => !v)}
      title="Toggle theme"
      aria-label="Toggle theme"
    >
      {dark ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
    </button>
  );
}

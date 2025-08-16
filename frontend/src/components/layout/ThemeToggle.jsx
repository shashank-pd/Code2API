import React from "react";

export default function ThemeToggle() {
  const [dark, setDark] = React.useState(() =>
    document.documentElement.classList.contains("dark")
  );

  React.useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <button
      className="inline-flex h-9 items-center justify-center rounded-md border px-3 text-sm hover:bg-accent hover:text-accent-foreground"
      onClick={() => setDark((v) => !v)}
      title="Toggle theme"
      aria-label="Toggle theme"
    >
      {dark ? "🌙" : "☀️"}
    </button>
  );
}

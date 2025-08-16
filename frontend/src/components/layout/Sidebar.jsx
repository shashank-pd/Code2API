import React from "react";
import { cn } from "../../lib/utils";

function Sidebar({ active, onChange }) {
  const items = [
    { key: "editor", label: "Editor", icon: "✏️" },
    { key: "results", label: "Results", icon: "📊" },
    { key: "swagger", label: "Docs", icon: "📜" },
  ];

  return (
    <aside className="hidden md:flex md:w-64 flex-col gap-2 border-r bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50">
      <div className="p-4 border-b">
        <div className="text-xl font-bold">Code2API</div>
        <div className="text-xs text-muted-foreground">Turn code into APIs</div>
      </div>
      <nav className="p-2">
        {items.map((item) => (
          <button
            key={item.key}
            onClick={() => onChange(item.key)}
            className={cn(
              "w-full flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
              active === item.key
                ? "bg-primary text-primary-foreground"
                : "hover:bg-accent hover:text-accent-foreground"
            )}
            aria-current={active === item.key ? "page" : undefined}
          >
            <span className="text-base" aria-hidden>
              {item.icon}
            </span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="mt-auto p-3 text-xs text-muted-foreground">v1.0.0</div>
    </aside>
  );
}

export default Sidebar;

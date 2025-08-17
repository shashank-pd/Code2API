import { cn } from "../../lib/utils";
import { FileCode2, BarChart3, BookText } from "lucide-react";

function Sidebar({ active, onChange }) {
  const items = [
    { key: "editor", label: "Editor", icon: FileCode2 },
    { key: "results", label: "Results", icon: BarChart3 },
    { key: "swagger", label: "Docs", icon: BookText },
  ];

  return (
    <aside className="hidden md:flex md:w-64 flex-col gap-2 border-r bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50">
      <div className="p-4 border-b">
        <div className="text-xl font-bold tracking-tight">Code2API</div>
        <div className="text-xs text-muted-foreground">Turn code into APIs</div>
      </div>
      <nav className="p-2">
        {items.map((item) => {
          const Icon = item.icon;
          return (
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
              <Icon className="h-4 w-4" aria-hidden />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
      <div className="mt-auto p-3 text-xs text-muted-foreground">v1.0.0</div>
    </aside>
  );
}

export default Sidebar;

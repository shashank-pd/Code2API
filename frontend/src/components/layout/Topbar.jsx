import React from "react";
import { Button } from "../ui/Button";
import ThemeToggle from "./ThemeToggle";

function Topbar({
  onUploadClick,
  onAnalyze,
  analyzing,
  inputMode,
  setInputMode,
}) {
  return (
    <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-2 px-4">
        <div className="md:hidden text-base font-semibold">Code2API</div>
        <div className="ml-auto flex items-center gap-2">
          <div className="hidden sm:flex rounded-md border p-1">
            <Button
              size="sm"
              variant={inputMode === "code" ? "default" : "ghost"}
              onClick={() => setInputMode("code")}
            >
              Code
            </Button>
            <Button
              size="sm"
              variant={inputMode === "repo" ? "default" : "ghost"}
              onClick={() => setInputMode("repo")}
            >
              Repo
            </Button>
          </div>
          <Button size="sm" variant="secondary" onClick={onUploadClick}>
            Upload
          </Button>
          <Button size="sm" onClick={onAnalyze} disabled={analyzing}>
            {analyzing ? "Analyzing..." : "Analyze"}
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

export default Topbar;

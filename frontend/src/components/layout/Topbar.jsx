import { Button } from "../ui/Button";
import ThemeToggle from "./ThemeToggle";
import { GitBranch, Code2, Upload, Play } from "lucide-react";

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
          <div className="hidden sm:flex rounded-md border p-1 bg-card">
            <Button
              size="sm"
              variant={inputMode === "code" ? "default" : "ghost"}
              onClick={() => setInputMode("code")}
            >
              <Code2 className="mr-1 h-4 w-4" /> Code
            </Button>
            <Button
              size="sm"
              variant={inputMode === "repo" ? "default" : "ghost"}
              onClick={() => setInputMode("repo")}
            >
              <GitBranch className="mr-1 h-4 w-4" /> Repo
            </Button>
          </div>
          <Button size="sm" variant="secondary" onClick={onUploadClick}>
            <Upload className="mr-1 h-4 w-4" /> Upload
          </Button>
          <Button size="sm" onClick={onAnalyze} disabled={analyzing}>
            <Play className="mr-1 h-4 w-4" />{" "}
            {analyzing ? "Analyzing..." : "Analyze"}
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

export default Topbar;

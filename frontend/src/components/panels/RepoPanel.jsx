import React from "react";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

export default function RepoPanel({
  repoUrl,
  setRepoUrl,
  branch,
  setBranch,
  analyzing,
  onAnalyze,
}) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">
            Repository URL
          </label>
          <Input
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repo or owner/repo"
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Branch</label>
          <Input
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="main"
          />
        </div>
      </div>
      <Button className="w-full" onClick={onAnalyze} disabled={analyzing}>
        {analyzing ? "Analyzing Repository..." : "Analyze Repository"}
      </Button>
      <div className="rounded-md border p-4">
        <h3 className="mb-2 text-sm font-semibold">Try examples</h3>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { name: "fastapi/fastapi", url: "fastapi/fastapi" },
            { name: "pallets/flask", url: "pallets/flask" },
            { name: "microsoft/vscode", url: "microsoft/vscode" },
            { name: "facebook/react", url: "facebook/react" },
          ].map((repo) => (
            <button
              key={repo.url}
              className="rounded-md border px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground"
              onClick={() => setRepoUrl(repo.url)}
            >
              {repo.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

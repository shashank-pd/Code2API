import MonacoEditor from "@monaco-editor/react";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Label } from "../ui/Label";
import { Upload, Play } from "lucide-react";

const SUPPORTED_LANGUAGES = {
  python: { label: "Python", extension: ".py", mode: "python" },
  javascript: { label: "JavaScript", extension: ".js", mode: "javascript" },
  java: { label: "Java", extension: ".java", mode: "java" },
};

export default function EditorPanel({
  language,
  setLanguage,
  filename,
  setFilename,
  fileInputRef,
  uploadFiles,
  analyzing,
  code,
  setCode,
  onAnalyze,
}) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="space-y-1">
          <Label htmlFor="language">Language</Label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="h-10 w-full rounded-md border bg-background px-3 text-sm"
          >
            {Object.entries(SUPPORTED_LANGUAGES).map(([key, lang]) => (
              <option key={key} value={key} className="text-foreground">
                {lang.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label htmlFor="filename">Filename</Label>
          <Input
            id="filename"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
          />
        </div>
        <div className="flex items-end gap-2">
          <input
            type="file"
            ref={fileInputRef}
            multiple
            accept=".py,.js,.jsx,.ts,.tsx,.java"
            onChange={uploadFiles}
            className="hidden"
          />
          <Button
            variant="secondary"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="mr-1 h-4 w-4" /> Upload Files
          </Button>
          <Button onClick={onAnalyze} disabled={analyzing}>
            <Play className="mr-1 h-4 w-4" />{" "}
            {analyzing ? "Analyzing..." : "Analyze Code"}
          </Button>
        </div>
      </div>
      <div className="rounded-lg border overflow-hidden">
        <MonacoEditor
          height="520px"
          language={SUPPORTED_LANGUAGES[language].mode}
          value={code}
          onChange={setCode}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: "on",
            roundedSelection: false,
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
}

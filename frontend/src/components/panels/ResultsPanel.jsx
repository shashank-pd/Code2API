import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { Download } from "lucide-react";

export default function ResultsPanel({ analysis, onDownload }) {
  if (!analysis) return null;

  const stats = analysis.analysis?.statistics;
  const repo = analysis.analysis?.repository_info;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Analysis Results</h2>
        {analysis.generated_api_path && (
          <Button onClick={onDownload}>
            <Download className="mr-1 h-4 w-4" /> Download Generated API
          </Button>
        )}
      </div>

      {repo && (
        <section className="rounded-lg border p-4">
          <h3 className="mb-4 text-sm font-semibold">Repository</h3>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <InfoTile label="Name" value={repo.name} />
            <InfoTile label="Language" value={repo.language || "Multiple"} />
            <InfoTile label="Stars" value={`⭐ ${repo.stars || 0}`} />
            <InfoTile label="Forks" value={`🍴 ${repo.forks || 0}`} />
            <InfoTile
              label="Files Analyzed"
              value={`📄 ${analysis.analysis.files_analyzed || 0}`}
            />
            <InfoTile
              label="Description"
              value={repo.description || "No description"}
              truncate
            />
          </div>
        </section>
      )}

      {stats && (
        <section className="rounded-lg border p-4">
          <h3 className="mb-4 text-sm font-semibold">Statistics</h3>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Kpi
              label="Total Files"
              value={stats.total_files}
              color="text-blue-500"
            />
            <Kpi
              label="Total Lines"
              value={stats.total_lines?.toLocaleString()}
              color="text-green-500"
            />
            <Kpi
              label="Languages"
              value={Object.keys(stats.languages || {}).length}
              color="text-purple-500"
            />
            <Kpi
              label="API Endpoints"
              value={analysis.analysis.api_endpoints?.length || 0}
              color="text-yellow-500"
            />
          </div>
          {stats.languages && (
            <div className="mt-4 space-y-2">
              {Object.entries(stats.languages).map(([lang, count]) => (
                <div
                  key={lang}
                  className="flex items-center justify-between rounded-md border p-2 text-sm"
                >
                  <span className="font-medium">{lang}</span>
                  <span className="text-muted-foreground">{count} files</span>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <section className="rounded-lg border p-4">
          <h3 className="mb-3 text-sm font-semibold">API Endpoints</h3>
          <div className="space-y-2">
            {analysis.analysis.api_endpoints?.map((endpoint, i) => (
              <EndpointCard key={i} endpoint={endpoint} />
            ))}
            {!analysis.analysis.api_endpoints?.length && (
              <div className="py-8 text-center text-sm text-muted-foreground">
                No API endpoints generated
              </div>
            )}
          </div>
        </section>

        <section className="rounded-lg border p-4">
          <h3 className="mb-3 text-sm font-semibold">
            Security Recommendations
          </h3>
          <ul className="space-y-2">
            {analysis.analysis.security_recommendations?.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-1 text-red-500">•</span>
                <span>{rec}</span>
              </li>
            ))}
            {!analysis.analysis.security_recommendations?.length && (
              <li className="py-8 text-center text-sm text-muted-foreground">
                No security issues detected
              </li>
            )}
          </ul>
        </section>

        <section className="rounded-lg border p-4">
          <h3 className="mb-3 text-sm font-semibold">
            Optimization Suggestions
          </h3>
          <ul className="space-y-2">
            {analysis.analysis.optimization_suggestions?.map((sug, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-1 text-green-500">•</span>
                <span>{sug}</span>
              </li>
            ))}
            {!analysis.analysis.optimization_suggestions?.length && (
              <li className="py-8 text-center text-sm text-muted-foreground">
                No optimization suggestions
              </li>
            )}
          </ul>
        </section>
      </div>
    </div>
  );
}

function InfoTile({ label, value, truncate }) {
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={truncate ? "truncate" : ""}>{value}</div>
    </div>
  );
}

function Kpi({ label, value, color }) {
  return (
    <div className="rounded-md border p-4 text-center">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function EndpointCard({ endpoint }) {
  const method = endpoint.http_method?.toLowerCase();
  const color =
    method === "get"
      ? "bg-green-500"
      : method === "post"
      ? "bg-blue-500"
      : method === "put"
      ? "bg-yellow-500"
      : method === "delete"
      ? "bg-red-500"
      : "bg-gray-500";

  return (
    <div className="space-y-1 rounded-md border p-3">
      <div className="flex items-center gap-2">
        <Badge className={`${color}`}>{endpoint.http_method}</Badge>
        <code className="text-sm font-mono text-blue-500">
          {endpoint.endpoint_path}
        </code>
      </div>
      <p className="text-sm text-muted-foreground">{endpoint.description}</p>
      <div className="flex gap-2">
        {endpoint.needs_auth && (
          <Badge variant="destructive">Auth Required</Badge>
        )}
        {endpoint.class_name && (
          <Badge className="bg-purple-500">{endpoint.class_name}</Badge>
        )}
      </div>
    </div>
  );
}

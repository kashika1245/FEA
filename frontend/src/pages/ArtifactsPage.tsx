import { useQuery } from "@tanstack/react-query";
import { artifactDownloadUrl, getAllArtifacts } from "../api/endpoints";
import { ErrorBanner } from "../components/ErrorBanner";
import { ExperimentPicker } from "../components/ExperimentPicker";
import { useExperimentId } from "../lib/experiment";
import { formatBytes, formatHash } from "../lib/format";

export function ArtifactsPage() {
  const [experimentId] = useExperimentId();
  const artifacts = useQuery({
    queryKey: ["artifacts", experimentId],
    queryFn: () => getAllArtifacts(experimentId),
  });
  return (
    <article>
      <p className="page-kicker">Provenance files</p>
      <h1 className="page-title">Artifact browser</h1>
      <p className="lede">
        Downloads use opaque artifact IDs from the API. Relative paths are experiment-local names,
        not host filesystem paths.
      </p>
      <ExperimentPicker />
      <ErrorBanner error={artifacts.error} />
      {artifacts.isLoading ? <div className="skeleton" style={{ height: 160, marginTop: 16 }} /> : null}
      {!artifacts.isLoading && !(artifacts.data?.length) ? <p>No artifacts are registered for this experiment.</p> : null}
      <div className="table-wrap" style={{ marginTop: 16 }}>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Size</th>
              <th>SHA-256</th>
              <th>Download</th>
            </tr>
          </thead>
          <tbody>
            {(artifacts.data ?? []).map((item) => (
              <tr key={item.artifact_id}>
                <td className="mono">{item.relative_path}</td>
                <td>{item.media_type}</td>
                <td>{formatBytes(item.size_bytes)}</td>
                <td className="mono">{formatHash(item.sha256)}</td>
                <td>
                  <a href={artifactDownloadUrl(item.artifact_id)}>Download</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

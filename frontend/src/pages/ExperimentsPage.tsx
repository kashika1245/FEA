import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getExperiments } from "../api/endpoints";
import { ErrorBanner } from "../components/ErrorBanner";
import { StatusBadge } from "../components/StatusBadge";
import { formatHash, formatNumber } from "../lib/format";
import { experimentKind } from "../lib/status";

export function ExperimentsPage() {
  const [q, setQ] = useState("");
  const [kind, setKind] = useState("all");
  const [sort, setSort] = useState("id");
  const experiments = useQuery({ queryKey: ["experiments"], queryFn: () => getExperiments(0, 100) });
  const rows = useMemo(() => {
    const list = (experiments.data ?? []).filter((item) => {
      const text = item.experiment_id.toLowerCase();
      if (q && !text.includes(q.toLowerCase())) return false;
      if (kind === "phase2" && !item.experiment_id.startsWith("paper-a.phase2.")) return false;
      if (kind === "phase3" && !item.experiment_id.startsWith("paper-a.phase3.")) return false;
      return true;
    });
    return list.sort((a, b) => {
      if (sort === "artifacts") return b.artifact_count - a.artifact_count;
      return a.experiment_id.localeCompare(b.experiment_id);
    });
  }, [experiments.data, q, kind, sort]);
  return (
    <article>
      <p className="page-kicker">Registry</p>
      <h1 className="page-title">Experiment explorer</h1>
      <p className="lede">
        Listing from GET /api/v1/experiments. The Paper A evidence experiment is{" "}
        <span className="mono">paper-a.phase2.v1</span>. Phase 2 pilots and{" "}
        <span className="mono">paper-a.phase3.tiny-*</span> jobs are integration artefacts, not the
        frozen paper result.
      </p>
      <div className="filters">
        <label className="field">
          Search
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="paper-a…" />
        </label>
        <label className="field">
          Type
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="all">All</option>
            <option value="phase2">Frozen Phase 2</option>
            <option value="phase3">Phase 3</option>
          </select>
        </label>
        <label className="field">
          Sort
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="id">Experiment ID</option>
            <option value="artifacts">Artifact count</option>
          </select>
        </label>
      </div>
      {experiments.isLoading ? <div className="skeleton" style={{ height: 160, marginTop: 16 }} /> : null}
      <ErrorBanner error={experiments.error} />
      {!experiments.isLoading && rows.length === 0 ? <p>No experiments match the current filters.</p> : null}
      <div className="table-wrap" style={{ marginTop: 16 }}>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Status</th>
              <th>Dataset</th>
              <th>Artifacts</th>
              <th>Immutable</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((item) => (
              <tr key={item.experiment_id}>
                <td>
                  <Link to={`/experiments/${item.experiment_id}`}>{item.experiment_id}</Link>
                </td>
                <td>{experimentKind(item.experiment_id)}</td>
                <td>
                  <StatusBadge status={item.status} />
                </td>
                <td className="mono">{formatHash(item.dataset_hash)}</td>
                <td>{formatNumber(item.artifact_count, 0)}</td>
                <td>{item.immutable ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

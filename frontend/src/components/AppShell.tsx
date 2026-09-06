import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet } from "react-router-dom";
import { getHealth, getReady } from "../api/endpoints";

const LINKS = [
  ["/", "Overview"],
  ["/experiments", "Experiments"],
  ["/profiles", "Profiles"],
  ["/thresholds", "Thresholds"],
  ["/asymmetry", "Asymmetry"],
  ["/combined", "Combined A3+F"],
  ["/interpolation", "Interpolation"],
  ["/jobs", "Jobs"],
  ["/artifacts", "Artifacts"],
  ["/methodology", "Methodology"],
] as const;

export function AppShell() {
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const ready = useQuery({ queryKey: ["ready"], queryFn: getReady });
  const apiState = health.isError
    ? "API unreachable"
    : ready.data && !ready.data.ready
      ? "API not ready"
      : health.data
        ? "API live"
        : "Checking API";
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand-kicker">Paper A observatory</div>
          <h1 className="brand-title">Structural surrogate trust</h1>
        </div>
        <nav aria-label="Primary">
          <ul className="nav-list">
            {LINKS.map(([to, label]) => (
              <li key={to}>
                <NavLink to={to} end={to === "/"}>
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <p className="provenance" style={{ color: "#d9d1c3" }}>
          {apiState}
          {ready.data?.ready ? " · Phase 1 dataset present" : ""}
        </p>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

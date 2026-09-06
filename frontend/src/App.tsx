import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ArtifactsPage } from "./pages/ArtifactsPage";
import { AsymmetryPage } from "./pages/AsymmetryPage";
import { CombinedPage } from "./pages/CombinedPage";
import { ExperimentDetailPage } from "./pages/ExperimentDetailPage";
import { ExperimentsPage } from "./pages/ExperimentsPage";
import { InterpolationPage } from "./pages/InterpolationPage";
import { JobsPage } from "./pages/JobsPage";
import { MethodologyPage } from "./pages/MethodologyPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ProfilesPage } from "./pages/ProfilesPage";
import { ThresholdsPage } from "./pages/ThresholdsPage";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/experiments" element={<ExperimentsPage />} />
        <Route path="/experiments/:id" element={<ExperimentDetailPage />} />
        <Route path="/profiles" element={<ProfilesPage />} />
        <Route path="/thresholds" element={<ThresholdsPage />} />
        <Route path="/asymmetry" element={<AsymmetryPage />} />
        <Route path="/combined" element={<CombinedPage />} />
        <Route path="/interpolation" element={<InterpolationPage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/artifacts" element={<ArtifactsPage />} />
        <Route path="/methodology" element={<MethodologyPage />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

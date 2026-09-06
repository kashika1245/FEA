import { useSearchParams } from "react-router-dom";

export const DEFAULT_EXPERIMENT = "paper-a.phase2.v1";

export function useExperimentId(): [string, (id: string) => void] {
  const [params, setParams] = useSearchParams();
  const id = params.get("experiment") ?? DEFAULT_EXPERIMENT;
  const setId = (next: string) => {
    const copy = new URLSearchParams(params);
    copy.set("experiment", next);
    setParams(copy, { replace: true });
  };
  return [id, setId];
}

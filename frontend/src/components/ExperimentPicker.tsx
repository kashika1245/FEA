import { useQuery } from "@tanstack/react-query";
import { getExperiments } from "../api/endpoints";
import { useExperimentId } from "../lib/experiment";

export function ExperimentPicker() {
  const [id, setId] = useExperimentId();
  const experiments = useQuery({ queryKey: ["experiments"], queryFn: () => getExperiments(0, 100) });
  return (
    <label className="field">
      Experiment
      <select value={id} onChange={(event) => setId(event.target.value)}>
        {!experiments.data?.some((item) => item.experiment_id === id) ? (
          <option value={id}>{id}</option>
        ) : null}
        {experiments.data?.map((item) => (
          <option key={item.experiment_id} value={item.experiment_id}>
            {item.experiment_id}
          </option>
        ))}
      </select>
    </label>
  );
}

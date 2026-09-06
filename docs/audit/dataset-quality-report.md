# Dataset Quality Report

Generated programmatically by `scripts/audit_dataset.py`. Values are read from the artefact, not invented.

| Field | Value |
|-------|-------|
| dataset_id | `paper-a.phase1.v1-n10000-seed20260905` |
| sample_count | 10000 |
| requested_sample_count | 10000 |
| column_count | 17 |
| missing_value_count | 0 |
| nan_count | 0 |
| inf_count | 0 |
| duplicate_id_count | 0 |
| duplicate_input_count | 0 |
| out_of_domain_count | 0 |
| nonfinite_output_count | 0 |
| failed_fea_count | 0 |
| random_seed | 20260905 |
| geometry_version | `tenbar.cantilever.v1` |
| solver_version | `planar-truss-direct-stiffness.v1` |
| software_version | `0.1.0` |
| git_commit | `None` |
| dataset_hash | `a78de261b1686363ed6d830cd370b763800da657bce0991047fe43fb9504e99e` |
| dataset_hash_recomputed | `a78de261b1686363ed6d830cd370b763800da657bce0991047fe43fb9504e99e` |
| configuration_hash | `449e9b7cfd50bcce39c9293bb5f12b63724d49ae44cc0cd427290b3e998e4752` |
| quality_ok | True |

## Input and output ranges

```json
{
  "max": {
    "A1": 99.99744280843014,
    "A10": 99.99636604069023,
    "A2": 99.97380860478502,
    "A3": 99.99861225150453,
    "A4": 99.9997410632562,
    "A5": 99.98647909996187,
    "A6": 99.99443723274543,
    "A7": 99.99791741188254,
    "A8": 99.98594095575514,
    "A9": 99.99843512614706,
    "C": 633784.3802453048,
    "E": 219.9969360645969,
    "F": 9.999225902163108,
    "sigma_max": 293.66481987560815,
    "u_max": 67.68168550599431
  },
  "min": {
    "A1": 50.0058652166824,
    "A10": 50.00175013181867,
    "A2": 50.00332369574679,
    "A3": 50.00686533628831,
    "A4": 50.00298626347166,
    "A5": 50.00047222592337,
    "A6": 50.00139794237487,
    "A7": 50.0005850281686,
    "A8": 50.002222700277954,
    "A9": 50.01430144545254,
    "C": 4394.770265459596,
    "E": 180.0091423287201,
    "F": 1.0011738350491899,
    "sigma_max": 16.171339100654226,
    "u_max": 4.319919645766519
  }
}
```

## Notes

- none

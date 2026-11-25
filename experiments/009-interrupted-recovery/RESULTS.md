# Experiment 009 — observed results

Run: https://github.com/EdwinJdevops/recourse-lab-/actions/runs/45603408829

Tested head: `0286d187c02659b7c7b893577023b093e78c27dd`.

Both experiments passed on 2026-11-25. The raw job log reports:

```text
PASS: dry-run did not persist; stale update rejected; partial workflow state observed
PASS: interruption persisted; stale compensation rejected; operator change preserved; incomplete recovery detected
```

All job steps, including cluster deletion and artifact upload, succeeded. Artifact 15015777928 has SHA-256 `d40d073977e2d6d335e1b5da5034e0371250e942ba25a4dbcee01743d8261c70` in both API metadata and job logs. Archive bytes and internal checksums have not been independently verified.

## Interpretation

A committed mutation survives recovery worker termination. A stale compensation is rejected after an intervening mutation. A subsequent update to another resource does not establish overall recovery completion. These are observations in a ConfigMap proxy, not a production recovery guarantee or novel Kubernetes primitive.

## Limitations and next gate

The intervening actor is sequential, not concurrent. The completion predicate reads resources separately, and the no-write check covers only one operation. Next test: coordinate competing processes to mutate the first resource between the verifier's two reads, and compare the reported completion with final observed state. This tests a specific observation race, not global snapshot semantics. Standalone product remains no-go absent actionable differentiation.

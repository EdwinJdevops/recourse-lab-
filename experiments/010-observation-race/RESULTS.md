# Experiment 010 — observed results

Verified run: https://github.com/EdwinJdevops/recourse-lab-/actions/runs/45604023075

Tested head: `aa5bd77da62b841f6087ee73604ecec754ec6b09`.

On 2026-11-25 all three integration experiments passed. Raw log: `PASS: separate reads falsely report completion; collection read rejects completion`.

Artifact 15016433408 digest `sha256:0978b0986bf70140a44cbc32ca84f34b07d570896a61fa1a40c09d8b616b365b` matches API metadata and upload log. Archive bytes and internal checksums have not been independently verified. Cluster deletion succeeded.

The controlled sequence changes A from recovered to initial before changing B from initial to recovered. Separate reads return recovered for both; the final collection read rejects the aggregate predicate. This is a deterministic fractured observation counterexample, not evidence of a defect in Kubernetes or an existing controller. The collection comparison is limited to same-kind objects in one namespace, and is not a guarantee of future state.

## Decision gate

Stop adding synthetic variants until a real recovery controller or runbook is identified with an applicable completion predicate and a reproducible failure. Inspect source and existing tests, identify exact version and semantics, and attempt to falsify the suspected defect. If existing mechanisms already cover the case, publish the baseline as a case study rather than claim a new product. Standalone product remains no-go.

# Experiment 011 — Results

Run: https://github.com/EdwinJdevops/recourse-lab-/actions/runs/45605371054

Head: `454c80bf4527694c7a39919f954205ed82a48f3a`.

Observed log on 2026-11-25:

```text
clean phase=Completed state=healthy
default phase=Completed state=incompatible
update phase=Completed state=healthy
PASS: real Velero restore policy comparison
```

All integration steps and cluster deletion succeeded. Uploaded archive digest reported by log: `a25800d3ffc237f84636caf3cd8af84dea81d9eef79dc698be87b6da1bc90c1e`. Archive bytes not independently verified.

Decision: reject a standalone tool addressing this specific configuration divergence; native update policy resolves the tested case. No upstream defect established. ConfigMap state is a proxy, not application health. Image tags were resolved at runtime, not locked across runs.

Next gate: inspect native hook semantics and existing recovery validation mechanisms before testing evidence invalidation between successful application validation and traffic admission. A documented point-in-time guarantee is not a defect merely because later state changes. Require an actual consumer contract violation and compare native readiness/admission mechanisms before proposing a product.

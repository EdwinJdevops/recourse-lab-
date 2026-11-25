# Experiment 008

Run only against a disposable Kubernetes cluster with kubectl configured for that cluster. The script creates and deletes its own randomly named namespace. It does not access Secrets or production data. Requires Python 3 and kubectl.

Run `python3 experiments/008-kubernetes-recovery/lab.py` from the repository root.

Acceptance: server dry-run does not persist B; A commits; a subsequent independent change to B makes the stale replacement fail with Conflict; final A and B show partial workflow completion. Raw evidence is written to evidence-008.json. This is a ConfigMap proxy for a recovery workflow, not actual workload restoration. No novelty or production guarantee is claimed. Execution pending.

Reference: https://kubernetes.io/docs/reference/using-api/api-concepts/

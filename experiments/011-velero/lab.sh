#!/usr/bin/env bash
set -euo pipefail
test "$(kubectl config current-context)" = kind-recourse
mkdir -p evidence
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
archive=velero-v1.19.0-linux-amd64.tar.gz
curl -fsSL --retry 3 "https://github.com/velero-io/velero/releases/download/v1.19.0/$archive" -o "$work/$archive"
(cd "$work"; echo "048d6965f152e9fe3e39e290caa3e8297009eaaa071946ff414417de20281ffe  $archive" | sha256sum -c -; tar -xzf "$archive")
v="$work/velero-v1.19.0-linux-amd64/velero"
# Resolve image tags to immutable registry references before deployment.
for image in bitnamilegacy/minio:latest bitnamilegacy/minio-client:latest velero/velero:v1.19.0 velero/velero-plugin-for-aws:v1.15.0; do
  docker pull "$image" >&2
  digest=$(docker image inspect --format '{{index .RepoDigests 0}}' "$image")
  [[ "$digest" == *@sha256:* ]]
  printf '%s %s\n' "$image" "$digest" >> evidence/011-images.txt
  case "$image" in
    bitnamilegacy/minio:latest) storage="$digest";;
    bitnamilegacy/minio-client:latest) client="$digest";;
    velero/velero:*) server="$digest";;
    velero/velero-plugin-for-aws:*) plugin="$digest";;
  esac
done
sed -e "s|bitnamilegacy/minio:latest|$storage|" -e "s|bitnamilegacy/minio-client:latest|$client|" experiments/011-velero/minio.yaml | kubectl apply -f -
kubectl -n velero rollout status deployment/minio --timeout=180s
kubectl -n velero wait --for=condition=complete job/minio-setup --timeout=180s
umask 077
printf '[default]\naws_access_key_id = minio\naws_secret_access_key = minio123\n' > "$work/credentials"
"$v" install --provider aws --plugins "$plugin" --image "$server" --bucket velero --secret-file "$work/credentials" --use-volume-snapshots=false --backup-location-config region=minio,s3ForcePathStyle=true,s3Url=http://minio.velero.svc:9000 --wait
kubectl -n velero wait --for=jsonpath='{.status.phase}'=Available backupstoragelocation/default --timeout=180s
kubectl create namespace recourse-011
kubectl -n recourse-011 create configmap dependency --from-literal=state=healthy
"$v" backup create recourse-011 --include-namespaces recourse-011 --include-resources configmaps --wait
kubectl -n velero get backup recourse-011 -o json > evidence/011-backup.json
test "$(kubectl -n velero get backup recourse-011 -o jsonpath='{.status.phase}')" = Completed
kubectl -n recourse-011 delete configmap dependency
for scenario in clean default update; do
  if [[ "$scenario" != clean ]]; then
    kubectl -n recourse-011 patch configmap dependency --type=merge -p '{"data":{"state":"incompatible"}}'
  fi
  args=()
  if [[ "$scenario" == update ]]; then args+=(--existing-resource-policy=update); fi
  "$v" restore create "recourse-011-$scenario" --from-backup recourse-011 --wait "${args[@]}"
  kubectl -n velero get restore "recourse-011-$scenario" -o json > "evidence/011-$scenario-restore.json"
  kubectl -n recourse-011 get configmap dependency -o json > "evidence/011-$scenario-state.json"
  phase=$(kubectl -n velero get restore "recourse-011-$scenario" -o jsonpath='{.status.phase}')
  state=$(kubectl -n recourse-011 get configmap dependency -o jsonpath='{.data.state}')
  printf '%s phase=%s state=%s\n' "$scenario" "$phase" "$state" | tee -a evidence/011-outcomes.txt
  test "$phase" = Completed
  if [[ "$scenario" == default ]]; then test "$state" = incompatible; else test "$state" = healthy; fi
done
echo 'PASS: real Velero restore policy comparison'

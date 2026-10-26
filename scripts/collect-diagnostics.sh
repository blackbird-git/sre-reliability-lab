#!/usr/bin/env bash
set -euo pipefail

run_check() {
    local title="$1"
    shift

    printf '\n=== %s ===\n' "$title"

    if "$@"; then
        return 0
    else
        local exit_code=$?
        printf 'WARNING: check failed with exit code %s\n' "$exit_code" >&2
        return 0
    fi
}
run_check "Kubernetes context" \
    kubectl config current-context

run_check "Application Pods" \
    kubectl get pods -l app=lab-api -o wide --show-labels

run_check "Application Service" \
    kubectl describe service lab-api

run_check "Service endpoints" \
    kubectl get endpointslices \
    -l kubernetes.io/service-name=lab-api -o yaml

run_check "Application Pod details and events" \
    kubectl describe pods -l app=lab-api

run_check "Recent application logs" \
    kubectl logs -l app=lab-api \
    --all-containers=true --prefix=true \
    --tail=50 --since=15m
#!/usr/bin/env bash
# Installs ArgoCD on a Kubernetes cluster and retrieves the initial admin password.

set -e

# Funcs.
die() { echo "$1" >&2; exit "${2:-1}"; }

# Check deps.
deps=(kubectl)
missing=()
for dep in "${deps[@]}"; do hash "$dep" 2>/dev/null || missing+=("$dep"); done
if [[ ${#missing[@]} -ne 0 ]]; then
    [[ "${#missing[@]}" -gt 1 ]] && s="s"
    die "Missing dep${s}: ${missing[*]}."
fi

# Vars.
namespace="argocd"
manifestUrl="https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"

# Create namespace.
kubectl create namespace "$namespace" 2>/dev/null || true

# Install ArgoCD.
kubectl apply -n "$namespace" -f "$manifestUrl" \
    || die "Failed to install ArgoCD from $manifestUrl"

# Wait for pods to be ready.
echo "Waiting for ArgoCD pods to be ready..."
kubectl wait --for=condition=Ready pods --all -n "$namespace" --timeout=300s \
    || die "ArgoCD pods failed to become ready within 5 minutes."

# Retrieve initial admin password.
adminPassword=$(kubectl -n "$namespace" get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" 2>/dev/null | base64 -d) \
    || die "Failed to retrieve ArgoCD admin password."

[[ -z "$adminPassword" ]] && \
    die "Admin password is empty; Check ArgoCD installation."

echo "ArgoCD installed successfully!"
echo "Namespace: $namespace"
echo "Username: admin"
echo "Password: $adminPassword"
echo ""
echo "Access ArgoCD:"
echo "  kubectl port-forward svc/argocd-server -n $namespace 8080:443"
echo "  Then navigate to: https://localhost:8080"

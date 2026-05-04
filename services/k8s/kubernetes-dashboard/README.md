# Kubernetes Dashboard is deployed via Helm in deploy-dashboard.yml.
# The manifests in this directory are legacy reference only — do NOT apply
# them directly as they will conflict with the Helm-managed installation.
#
# If you need to manage the Dashboard via ArgoCD after initial Helm install,
# use the Helm chart via an ArgoCD Application pointing at the Helm repo,
# NOT these raw manifests.

---
roles: [admin]
---

# IT Security — Internal (Admin only)

## Privileged access

Production Kubernetes kubeconfig access is limited to the platform on-call rotation. Contractors and general staff must not receive cluster-admin credentials.

## Secrets

API keys for payment processors are stored only in the corporate vault. Rotation cadence is **90 days**. Sharing vault tokens in Slack is a P1 incident.

# Implementation-only infrastructure closure

The repository now contains separate Terraform roots for sandbox, staging, and
production under `infra/terraform/environments/`, backed by the shared
`peti-platform` module.

The module defines private uniform-access media storage, Firestore, bounded
Cloud Tasks, Secret Manager references, separate API and worker Cloud Run
services, environment-specific service accounts, bounded scaling, and
least-privilege runtime IAM bindings. Terraform state and variable values are
operator-managed and excluded from source control.

This records infrastructure configuration implementation only. Applying the
roots, supplying secrets, and external cloud certification remain operator
activities and are intentionally not performed by the implementation pass.

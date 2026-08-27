# PETi environment infrastructure

Each environment root is intentionally separate so project IDs, buckets, queues,
service accounts, secrets, and Cloud Run services cannot be shared accidentally.

```powershell
terraform -chdir=infra/terraform/environments/sandbox init
terraform -chdir=infra/terraform/environments/sandbox plan -var-file=variables.tfvars
```

Initialize each root with an organization-managed, environment-specific state
bucket and prefix, for example:

```powershell
terraform -chdir=infra/terraform/environments/sandbox init `
  -backend-config="bucket=peti-sandbox-tfstate" `
  -backend-config="prefix=peti/sandbox"
```

Supply `billing_account_id` through an untracked tfvars file when budget
alerts are enabled. The module enables Firebase Identity Platform and creates
the Google OAuth provider when `google_oauth_client_id` and
`google_oauth_client_secret` are supplied through a secure, untracked variable
source. The module enables Firebase Identity Platform and creates
an API-to-private-worker invoker relationship; the API must create Cloud Tasks
with an OIDC token whose service account is the dedicated API runtime identity
and whose audience is the worker URL.

The generated environment outputs are the only supported source for API and
worker URLs. Do not copy them into Android source; pass them through the
environment-specific Gradle/Firebase build configuration.

The module provisions private uniform-access media storage, Firestore, an
authenticated Cloud Tasks queue, separate API/worker service accounts, private
worker and public API Cloud Run services, Secret Manager references, bounded
Cloud Run scaling, and least-privilege task/storage/Firestore bindings.

Terraform state must be configured in an organization-approved remote backend;
credentials and `*.tfvars` files are intentionally excluded from source control.

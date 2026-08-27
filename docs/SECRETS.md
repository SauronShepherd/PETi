# Secrets

Production secrets belong in Google Secret Manager or secure deployment configuration. Never commit API keys, service-account JSON, Firebase private credentials, ad verification secrets, Play purchase credentials, tokens, or signed URLs. `.env.example` contains names only.
# Secrets and environment boundaries

- Android contains no backend credentials, provider verification secrets, or authoritative prices.
- Local development uses explicit local-test identity and fake rewarded advertising only.
- DEV/STAGING/PRODUCTION require Firebase authentication and environment-specific backend configuration.
- Provider callback verification belongs exclusively in the backend advertising boundary.

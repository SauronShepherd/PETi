# Observability Taxonomy

Events use stable names and low-cardinality labels: `domain`, `operation_type`, `status`, `error_code`, `environment`, `schema_version`, `provider`, and `correlation_id`. Never use pet names, free-text queries, source excerpts, media bytes, tokens or raw model output as metric labels. Cost-bearing operations always carry an operation identity.

class ContextBroker:
    """Materializes least-context bundles from caller-owned typed sources."""
    def __init__(self, sources=None): self.sources = sources or {}

    def register(self, source_type, provider): self.sources[source_type] = provider

    def materialize(self, owner, pet_id, requested_types, limit=50):
        bundle = []
        for source_type in requested_types:
            provider = self.sources.get(source_type)
            if not provider: continue
            for item in provider(owner, pet_id)[:limit - len(bundle)]:
                if item.get("owner_user_id", owner) != owner or item.get("pet_id", pet_id) != pet_id: continue
                bundle.append({"source_type": source_type, "id": item.get("id"), "summary": item.get("summary", item.get("title", "")), "source_version": item.get("source_version", "1.0.0")})
        return {"owner_user_id": owner, "pet_id": pet_id, "items": bundle, "context_policy_version": "1.0.0"}

from copy import deepcopy

from .config.context_policies_v1 import CONTEXT_POLICIES_BY_CAPABILITY


class ContextBroker:
    """Policy-bound materialization of least-context, immutable bundles."""
    def __init__(self, sources=None, policies=None):
        self.sources, self.policies, self._bundles = sources or {}, policies or CONTEXT_POLICIES_BY_CAPABILITY, {}
    def register(self, source_type, provider): self.sources[source_type] = provider
    def materialize(self, owner, pet_id, requested_types, *, capability_id=None, limit=None):
        policy = self.policies.get(capability_id)
        if policy is None: raise ValueError("CONTEXT_POLICY_REQUIRED")
        requested = list(dict.fromkeys(requested_types))
        if any(not policy.permits(x) for x in requested): raise ValueError("CONTEXT_CATEGORY_FORBIDDEN")
        items, excluded, maximum = [], [], min(limit or policy.max_items, policy.max_items)
        for category in requested:
            provider = self.sources.get(category)
            if not provider: excluded.append(category); continue
            rows = provider.load(owner, pet_id) if hasattr(provider, "load") else provider(owner, pet_id)
            for raw in rows[: maximum - len(items)]:
                if raw.get("owner_user_id") != owner or raw.get("pet_id") != pet_id: continue
                item = {"source_type": category, "id": raw.get("id"), "source_version": raw.get("source_version", "1.0.0")}
                if category == "CURRENT_MEDIA": item.update({"media_asset_id": raw.get("media_asset_id", raw.get("id")), "checksum": raw.get("checksum"), "storage_generation": raw.get("storage_generation")})
                else: item["summary"] = raw.get("summary", raw.get("title", ""))
                items.append(item)
        bundle = {"owner_user_id": owner, "pet_id": pet_id, "items": items, "included_categories": sorted({x["source_type"] for x in items}), "excluded_categories": excluded, "context_policy_version": "1.0.0"}
        bundle["id"] = f"ctx-{len(self._bundles) + 1}"; self._bundles[bundle["id"]] = deepcopy(bundle)
        return deepcopy(bundle)
    def get(self, bundle_id): return deepcopy(self._bundles[bundle_id])

import hashlib
import re


class SearchService:
    def __init__(self, source_provider): self.source_provider = source_provider

    @staticmethod
    def normalize(query): return re.sub(r"\s+", " ", str(query).strip().lower())[:200]

    def search(self, owner, query, pet_id=None, entity_type=None, source=None, limit=50):
        q = self.normalize(query)
        if not q: return []
        try:
            if isinstance(limit, (bool, float)):
                raise TypeError("search limit must be an integer")
            bounded_limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            bounded_limit = 50
        try:
            rows = self.source_provider(owner, pet_id) or []
        except Exception:  # noqa: BLE001 - search is a non-authoritative read projection
            rows = []
        result = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            if entity_type and row.get("type") != entity_type: continue
            if source and row.get("source") != source: continue
            text = self.normalize(" ".join(str(row.get(k, "")) for k in ("title", "summary", "content", "measurement_type")))
            if q in text:
                result.append({"id": row.get("id"), "type": row.get("type", "UNKNOWN"), "pet_id": row.get("pet_id"), "title": row.get("title", "PETi record"), "source": row.get("source", "CANONICAL"), "query_hash": hashlib.sha256(q.encode()).hexdigest()})
        return result[:bounded_limit]

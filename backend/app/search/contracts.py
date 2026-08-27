from dataclasses import dataclass, field


@dataclass
class SearchDocument:
    id: str
    user_scope: str
    pet_id: str
    entity_type: str
    title: str
    text: str
    source_id: str
    source_version: str = "1.0.0"


class SearchBackend:
    def __init__(self): self.documents: dict[str, SearchDocument] = {}
    def upsert(self, document): self.documents[document.id] = document
    def delete(self, document_id): self.documents.pop(document_id, None)
    def query(self, user_scope, text, pet_ids=None): return [x for x in self.documents.values() if x.user_scope == user_scope and (not pet_ids or x.pet_id in pet_ids) and text.lower() in (x.title + " " + x.text).lower()]


@dataclass
class SearchQuery:
    text: str
    animal_ids: list[str] = field(default_factory=list)
    entity_type: str | None = None
    source: str | None = None


@dataclass
class SavedSearch:
    user_id: str
    name: str
    query: SearchQuery
    id: str = ""


@dataclass
class TopicCollection:
    owner_user_id: str
    name: str
    item_ids: list[str] = field(default_factory=list)
    id: str = ""

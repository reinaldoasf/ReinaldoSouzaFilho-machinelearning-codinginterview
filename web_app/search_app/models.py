import mongoengine as db


class Article(db.Document):
    text = db.StringField(required=True)

    @classmethod
    def search(cls, query, top_k=10):
        """Legacy keyword search (kept for reference/fallback only - the
        `/search` endpoint now uses vector_search.semantic_search instead)."""
        return [a.text for a in cls.objects(text__icontains=query).limit(top_k)]

    @classmethod
    def get_by_ids(cls, ids):
        """Fetch articles by Mongo id, preserving the given order (the order
        in which the vector search ranked them)."""
        by_id = {str(a.id): a.text for a in cls.objects(id__in=ids)}
        return [by_id[_id] for _id in ids if _id in by_id]

    meta = {
        "indexes": ["text"]
    }

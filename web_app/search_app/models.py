import mongoengine as db


class Article(db.Document):
    text = db.StringField(required=True)

    @classmethod
    def search(cls, query, top_k=10):
        return [a.text for a in cls.objects(text__icontains=query).limit(top_k)]
    meta = {
        "indexes": ["text"]
    }
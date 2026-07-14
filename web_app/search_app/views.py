from flask import Blueprint
from flask import request, render_template

from vector_search import semantic_search
from translation import translate_es_to_en, translate_batch_en_to_es

search_app = Blueprint("search_app", __name__)


@search_app.route("/search", methods=("GET", "POST"))
def init():
    results = []
    query = ""
    language = "en"

    if request.method == "POST":
        query = (request.form.get("query") or "").strip()
        language = request.form.get("language", "en")

        if query:
            # Only one vector index exists (English). For Spanish searches we
            # translate the query into English, search, then translate the
            # matched article texts back into Spanish for display.
            search_query = (
                translate_es_to_en(query) if language == "es" else query
            )

            matches = semantic_search(search_query)
            texts = [match["text"] for match in matches]

            if language == "es":
                texts = translate_batch_en_to_es(texts)

            results = texts

    return render_template(
        "index.html", results=results, query=query, language=language
    )

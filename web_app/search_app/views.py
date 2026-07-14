from flask import Blueprint
from flask import request, render_template

from search_app.models import Article

search_app = Blueprint("search_app", __name__)


@search_app.route("/search", methods=("GET", 'POST'))
def init():
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            results = Article.search(query, top_k=10)
        else:
            results = []
    else:
        results = []
    return render_template('index.html', results=results)

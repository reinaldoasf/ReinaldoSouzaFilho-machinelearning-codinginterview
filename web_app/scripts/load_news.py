import os

import click
import pandas as pd
from flask.cli import with_appcontext
from mongoengine import connect
from search_app.models import Article

from vector_search import index_articles, reset_collection

BATCH_SIZE = 256


@click.command("load-news")
@with_appcontext
def load_news():
    connect(
        host=os.environ["MONGODB_HOST"],
        db=os.environ["MONGODB_DB"],
    )
    print("starting load")

    # Start from a clean vector index every run, so re-running `load-news`
    # (e.g. after changing the embedding model) never leaves stale/duplicate
    # vectors behind. Mongo storage keeps its existing upsert-by-text
    # behaviour, so re-runs against the same dataset stay cheap there.
    reset_collection()

    splits = {
        "train": "data/train-00000-of-00001.parquet",
        "test": "data/test-00000-of-00001.parquet",
    }
    df = pd.read_parquet("hf://datasets/fancyzhx/ag_news/" + splits["test"])

    articles = 0
    batch_ids, batch_texts = [], []

    for article in df.itertuples():
        # `.modify(upsert=True, new=True, ...)` is an atomic find-and-modify
        # that returns the persisted document (including its _id), which
        # `update_one` does not. We need that id to use as the vector id.
        doc = Article.objects(text=article.text).modify(
            upsert=True, new=True, set__text=article.text
        )
        articles += 1
        batch_ids.append(str(doc.id))
        batch_texts.append(doc.text)

        if len(batch_ids) >= BATCH_SIZE:
            index_articles(batch_ids, batch_texts)
            batch_ids, batch_texts = [], []

    if batch_ids:
        index_articles(batch_ids, batch_texts)

    print(f"Loaded {articles} articles!")

"""
Lightweight Spanish <-> English translation, used so users can search in
Spanish against an English-only article index and read results back in
Spanish.

Design choices, and why:
  - We use Helsinki-NLP/opus-mt-{es-en,en-es}: small MarianMT models
    (~300MB each) rather than a large multilingual LLM-style translator.
    They're fast on CPU and good enough for search queries and short article
    snippets, matching the "lightweight and efficient" requirement.
  - We translate the QUERY into English and search the existing English
    index, rather than maintaining a second Spanish vector index. This keeps
    exactly one index to build/update/keep in sync.
  - Models are loaded lazily and cached (functools.lru_cache) so the (slow)
    weight loading happens once per process, not once per request.
"""

import functools

from transformers import pipeline

ES_EN_MODEL = "Helsinki-NLP/opus-mt-es-en"
EN_ES_MODEL = "Helsinki-NLP/opus-mt-en-es"


@functools.lru_cache(maxsize=1)
def _es_to_en_pipeline():
    return pipeline("translation", model=ES_EN_MODEL)


@functools.lru_cache(maxsize=1)
def _en_to_es_pipeline():
    return pipeline("translation", model=EN_ES_MODEL)


def translate_es_to_en(text):
    """Translate a single string from Spanish to English."""
    if not text or not text.strip():
        return text
    return _es_to_en_pipeline()(text)[0]["translation_text"]


def translate_en_to_es(text):
    """Translate a single string from English to Spanish."""
    if not text or not text.strip():
        return text
    return _en_to_es_pipeline()(text)[0]["translation_text"]


def translate_batch_en_to_es(texts):
    """Translate a list of English strings to Spanish in one batched call,
    which is considerably faster than translating one at a time when we have
    a page of results to render."""
    if not texts:
        return []
    outputs = _en_to_es_pipeline()(texts)
    return [word["translation_text"] for word in outputs]

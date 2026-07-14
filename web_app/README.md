## AI Engineer Coding Exercise

This application is a web app that performs **semantic (vector) search** over
a news article dataset, in English or Spanish.

##### Starting the app
```
docker compose up --build
```
This brings up three containers: `web-app` (Flask), `mongodb` (article
storage), and `chromadb` (vector index).

##### Initializing data
```
docker compose run --rm web-app flask load-news
```
This loads the AG News dataset into MongoDB and, for each article, computes a
sentence embedding (Hugging Face `sentence-transformers/all-MiniLM-L6-v2`)
and stores it in ChromaDB for semantic search.

##### UI interface
```
http://localhost:5004/search
```
Pick "English" or "Español" before searching - Spanish queries are
translated to English for the search, and results are translated back to
Spanish for display.

### Requirements
- Docker compose
- Linux, Windows or MacOS

## AI Engineer Coding Exercise

This application is a simple web app that allows to perform text search over elements in a dataset.

##### Starting the app
```
docker compose up --build
```
##### Initializing data
```
docker compose run --rm web-app flask load-news
```
##### UI interface
```
http://localhost:5004/search
```
### Requirements
- Docker compose
- Linux or iOS, this has not been tested in Windows
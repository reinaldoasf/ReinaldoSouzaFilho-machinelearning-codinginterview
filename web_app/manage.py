import os

from mongoengine import connect

from application import create_app


app = create_app()
connect(
    host=os.environ["MONGODB_HOST"],
    db=os.environ["MONGODB_DB"],
)

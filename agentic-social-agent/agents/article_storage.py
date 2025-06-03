import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGODB_URI"))
db = client.get_default_database()
articles_collection = db["articles"]

def store_articles(articles: list):
    for article in articles:
        if not articles_collection.find_one({"url": article["url"]}):
            articles_collection.insert_one(article)
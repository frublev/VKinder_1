from pymongo import MongoClient


class MongoDB:
    def __init__(self, name, client=MongoClient()):
        self.db = client['VKinder']
        self.collection = self.db[name]

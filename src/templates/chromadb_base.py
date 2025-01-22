from src.templates.singleton import Singleton


# ChromaDB
class ChromaDBBase(Singleton):
    def connect(self):
        raise NotImplementedError

    def insert(self):
        raise NotImplementedError

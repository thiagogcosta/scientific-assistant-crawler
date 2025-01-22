from src.templates.singleton import Singleton


# WebScrapper
class WebScrapperBase(Singleton):
    def config(self):
        raise NotImplementedError

    def conectar(self):
        raise NotImplementedError

    def captar(self):
        raise NotImplementedError

    def persistir(self):
        raise NotImplementedError

    def execute(self):
        self.config()
        self.conectar()
        self.captar()
        self.persistir()

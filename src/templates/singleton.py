# REF: https://www.geeksforgeeks.org/singleton-pattern-in-python-a-complete-guide/
class Singleton(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Singleton, cls).__new__(cls)
        return cls.instance

"""Base Agent Class"""

class BaseAgent:
    def __init__(self, name: str):
        self.name = name
    
    def process(self, message: str):
        raise NotImplementedError

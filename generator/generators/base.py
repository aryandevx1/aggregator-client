from abc import ABC, abstractmethod
from generator.model import Object

class Generator(ABC): 

    @abstractmethod
    def generate(
        self, 
        objects: list[Object]
    ) -> dict[str, str]:
        pass  
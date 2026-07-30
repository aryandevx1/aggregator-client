import pytest
from generator.generators.base import Generator
from generator.model import Object

class IncompleteGenerator(Generator): 
    pass

class FakeGenerator(Generator): 
    def generate(
        self, 
        objects: list[Object]
    ) -> dict[str, str]:
        return {}

def test_generator_cannot_be_instantiated(): 
    with pytest.raises(
        TypeError
    ): 
        Generator()

def test_incomplete_child_class_cannot_be_instantiated(): 
    with pytest.raises(
        TypeError
    ): 
        IncompleteGenerator()

def test_complete_child_class_canbe_instantiated(): 
    generator = FakeGenerator()

    assert isinstance(generator, Generator)
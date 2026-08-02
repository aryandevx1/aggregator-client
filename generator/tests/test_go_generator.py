from generator.generators.base import Generator
from generator.generators.go import GoGenerator

def test_go_generator_is_instance_of_generator(): 
    assert isinstance(GoGenerator(), Generator)
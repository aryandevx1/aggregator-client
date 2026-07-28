from model import Object

class Validator: 
    def validateObjectKind(objectKind: str) -> None: 
        final_string: str = objectKind.lower().strip()
        if final_string not in {"entity", "composite"}:
            raise ValueError(f"invalid value for the kind field, {final_string}")
            
    def validate(self, objects: list[Object]) -> None:
        for obj in objects: 
            self.validateObjectKind(obj.kind)


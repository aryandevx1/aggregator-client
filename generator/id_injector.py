from .model import Object, Field

class EntityIdInjector: 
    _ID_FIELD_NAME = "id" 
    def _has_id_field(self, field_list: list[Field]) -> bool: 
        for field in field_list: 
            if field.name == self._ID_FIELD_NAME :
                return True

        return False

    def _create_id_field(self) -> Field: 
        return Field(
            name=self._ID_FIELD_NAME,
            type="string",
            required=True, 
            ref=None, 
            values=[],
            sensitive=False
        )

    def inject(self, objects: list[Object]) -> None : 
        for obj in objects: 
            if obj.kind != "entity": 
                continue

            if self._has_id_field(obj.fields): 
                continue

            obj.fields.append(self._create_id_field())

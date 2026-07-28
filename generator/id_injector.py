from .model import Object, Field

class EntityIdInjector(): 
    _ID_FIELD_NAME = "id" 
    def _has_id_field(self, field_list: list[Field]) -> bool: 
        return any(field.name == self._ID_FIELD_NAME for field in field_list)

    def _get_id_field(self) -> Field: 
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

            obj.fields.append(self._get_id_field())

from .test_helpers import make_object, make_field
from generator.id_injector import EntityIdInjector
from generator.model import Field

def test_id_injection_for_object_kind_entity(): 
    objects = [
        make_object(
            name="Job", 
            kind="entity", 
            fields=[
                make_field()
            ]
        )
    ]

    injector = EntityIdInjector()
    injector.inject(objects)

    assert len(objects) == 1
    assert len(objects[0].fields) == 2 

def test_id_injection_for_object_kind_composite(): 
    objects = [
        make_object(
            name="Job", 
            kind="composite", 
            fields=[
                make_field()
            ]
        )
    ]

    injector = EntityIdInjector()
    injector.inject(objects)

    assert len(objects) == 1
    assert len(objects[0].fields) == 1

def test_id_injection_idempotency(): 
    objects = [
        make_object(
            name="Job", 
            kind="entity", 
            fields=[
                make_field()
            ]
        )
    ]

    injector = EntityIdInjector()
    injector.inject(objects)

    assert len(objects) == 1
    assert len(objects[0].fields) == 2 

    injector.inject(objects)
    assert len(objects) == 1
    assert len(objects[0].fields) == 2 

def test_all_entities_receive_id_fields() -> None:
    objects = [
        make_object(name="Job", kind="entity"),
        make_object(name="Company", kind="entity"),
        make_object(name="User", kind="entity"),
    ]

    EntityIdInjector().inject(objects)

    for obj in objects:
        id_fields = [
            field
            for field in obj.fields
            if field.name == "id"
        ]

        assert len(id_fields) == 1

def test_existing_id_field_is_not_duplicated() -> None:
    existing_id = Field(
        name="id",
        type="string",
        required=True,
        ref=None,
        values=[],
        sensitive=False,
    )

    objects = [
        make_object(
            name="Job",
            kind="entity",
            fields=[existing_id],
        ),
    ]

    EntityIdInjector().inject(objects)

    id_fields = [
        field
        for field in objects[0].fields
        if field.name == "id"
    ]

    assert len(id_fields) == 1
    assert id_fields[0] is existing_id
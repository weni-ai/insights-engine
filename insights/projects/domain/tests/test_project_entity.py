import pytest
import uuid

from ..entities import Project


def test_guarantee_project_fields():
    assert Project.__slots__ == (
        "created_at",
        "updated_at",
        "uuid",
        "name",
        "timezone",
        "config",
    )


def test_instance_with_not_listed_field():
    with pytest.raises(TypeError):
        Project(non_implemented_field="Won't work")


def test_throw_error_when_not_giving_name():
    with pytest.raises(TypeError):
        Project(name="Project Name")


def test_throw_error_when_not_giving_timezone():
    with pytest.raises(TypeError):
        Project(timezone="America/Maceio")


def test_instance_with_required_fields_only():
    project = Project(name="Test", timezone="America/Maceio")
    assert type(project.uuid) is uuid.UUID
    assert project.config == {}


def test_instance_with_all_fields():
    project = Project(name="Test", timezone="America/Maceio", config={"key": "value"})
    assert project.config == {"key": "value"}

import pytest

from ..usecases import CreateProject, CreateProjectUseCase


class TestCreateProjectDTO:
    """
    Fields:
        uuid: uuid, mandatory
        name: str, mandatory
        timezone: str, mandatory

    """

    def test_required_fields():
        test_data = [(None, "Weni", "")]

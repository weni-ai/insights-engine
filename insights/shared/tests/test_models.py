import pytest

from insights.shared.models import (
    BaseModel,
    ConfigurableModel,
    DateTimeModel,
    SoftDeleteModel,
    UUIDModel,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model", [UUIDModel, DateTimeModel, SoftDeleteModel, ConfigurableModel, BaseModel]
)
def test_abstract_models(model):
    with pytest.raises(AttributeError):
        model.objects.create()

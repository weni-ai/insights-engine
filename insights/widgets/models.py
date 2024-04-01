from django.db import models  # noqa

from insights.shared.models import BaseModel, ConfigurableModel


class Widget(BaseModel, ConfigurableModel): ...  # noqa

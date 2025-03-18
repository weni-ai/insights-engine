from typing import TYPE_CHECKING

from django.utils import translation

if TYPE_CHECKING:
    from insights.users.models import User


class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        user: "User" = getattr(request, "user", None)

        language = user.language if user else "en"

        with translation.override(language):
            response = self.get_response(request)

        return response

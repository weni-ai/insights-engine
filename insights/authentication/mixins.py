from insights.authentication.authentication import JWTAuthentication


class AllowJWTInternalAuthMixin:
    @property
    def authentication_classes(self):
        classes = super().authentication_classes
        get_method = getattr(self, "get", None)
        flag_as_internal_jwt_enabled = (
            getattr(get_method, "_flag_as_internal_jwt_enabled", False)
            if get_method
            else False
        )

        if flag_as_internal_jwt_enabled:
            classes.append(JWTAuthentication)

        return classes

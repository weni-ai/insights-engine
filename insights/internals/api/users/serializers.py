from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from insights.users.models import User


class ChangeUserLanguageSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    language = serializers.CharField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("User does not exist"), code="does_not_exist"
            )

        return value

    class Meta:
        model = User
        fields = ["email", "language"]

    def save(self):
        User.objects.filter(email=self.validated_data["email"]).update(
            language=self.validated_data["language"]
        )

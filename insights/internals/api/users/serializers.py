from rest_framework import serializers

from insights.users.models import User


class ChangeUserLanguageSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    language = serializers.ChoiceField(
        required=True, choices=User.language.field.choices
    )

    class Meta:
        model = User
        fields = ["email", "language"]

    def save(self):
        user = User.objects.get(email=self.validated_data["email"])
        user.language = self.validated_data["language"]
        return user.save()

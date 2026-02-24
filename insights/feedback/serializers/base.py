from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class Score1To5AnswerSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["SCORE_1_5"])
    answer = serializers.CharField()

    def validate_answer(self, value: str):
        error_msg = _("Invalid answer. Must be a string number between 1 and 5.")

        try:
            converted_value = int(value)
        except ValueError:
            raise serializers.ValidationError(error_msg, code="invalid_answer")

        if converted_value < 1 or converted_value > 5:
            raise serializers.ValidationError(error_msg, code="invalid_answer")

        return converted_value


class TextAnswerSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["TEXT"])
    answer = serializers.CharField()

    def validate_answer(self, value: str):
        max_length = 1000

        if len(value) > max_length:
            raise serializers.ValidationError(
                _(
                    "Invalid answer. Must be a string less than {max_length} characters."
                ).format(max_length=max_length),
                code="invalid_answer",
            )

        return value

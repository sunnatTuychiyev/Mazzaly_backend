from rest_framework import serializers


class FlexibleCharField(serializers.CharField):
    """CharField that accepts lists/tuples and coerces them to a string."""

    def to_internal_value(self, data):
        if isinstance(data, (list, tuple)):
            data = " ".join(str(v) for v in data)
        return super().to_internal_value(str(data))


class ChatMessageSerializer(serializers.Serializer):
    """Validate an incoming chat message."""

    message = FlexibleCharField()

    def validate_message(self, value):
        """Ensure the message is a plain string."""
        return str(value)


class ChatResponseSerializer(serializers.Serializer):
    response = serializers.CharField()


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()


class ImageResponseSerializer(serializers.Serializer):
    food_name = serializers.CharField()
    calories = serializers.FloatField()

from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class ChatImageSerializer(serializers.Serializer):
    image = serializers.ImageField()

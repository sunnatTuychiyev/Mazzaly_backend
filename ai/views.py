from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import openai

from recipes.models import Recipe

class ChatView(APIView):
    """Simple ChatGPT proxy that only answers food related questions."""

    @swagger_auto_schema(
        operation_description="Chat with AI about food and recipes.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['message'],
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='User question')
            }
        ),
        responses={200: openapi.Response('AI response', openapi.Schema(type=openapi.TYPE_OBJECT, properties={'reply': openapi.Schema(type=openapi.TYPE_STRING)}))}
    )
    def post(self, request):
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            return Response({'detail': 'OpenAI API key not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        message = request.data.get('message')
        if not message:
            return Response({'detail': 'message field required'}, status=status.HTTP_400_BAD_REQUEST)

        openai.api_key = api_key
        recipes = Recipe.objects.all().values_list('name', flat=True)
        system_prompt = (
            "You are a helpful assistant that answers ONLY food related questions. "
            "You know these recipes: " + ', '.join(recipes) + ". "
            "If asked how to cook a recipe, provide instructions if available."
        )

        try:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': message}
                ]
            )
            reply = response.choices[0].message['content'].strip()
        except Exception as e:
            return Response({'detail': f'Error communicating with OpenAI: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'reply': reply})

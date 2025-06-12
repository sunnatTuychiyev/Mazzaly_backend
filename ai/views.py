from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
import os
import openai

from recipes.models import Recipe

class ChatView(APIView):
    """Interact with ChatGPT for food-related questions."""

    permission_classes = [AllowAny]

    def post(self, request):
        user_message = request.data.get('message', '')
        if not user_message:
            return Response({'error': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)

        openai.api_key = os.getenv('OPENAI_API_KEY')
        recipes = Recipe.objects.all().values_list('name', flat=True)
        recipe_list = ', '.join(recipes)
        system_prompt = (
            "You are a cooking assistant. Answer only food-related questions. "
            "If the user asks something unrelated, politely refuse. "
            f"These recipes are available: {recipe_list}. Use them when relevant."
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            answer = response.choices[0].message['content']
            return Response({'answer': answer})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

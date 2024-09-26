import requests
from django.conf import settings


class ChatCompletionClient:
    base_url = settings.GROQ_OPEN_AI_URL

    @property
    def headers(self):
        return {
            "Content-Type": "application/json; charset: utf-8",
            "Authorization": f"Bearer {settings.GROQ_CHATGPT_TOKEN}",
        }

    def chat_completion(self, filters: dict):
        prompt = filters.get("prompt")
        if prompt is None:
            return {}
        url = f"{self.base_url}chat/completions"
        response = requests.post(
            url=url,
            headers=self.headers,
            json={
                "model": settings.GROQ_OPEN_AI_GPT_VERSION,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            },
        )
        return response.json()

import os
import httpx
from typing import List
from app.config import settings


class BhashiniTranslationService:
    """Service for translating text using Bhashini API."""

    def __init__(self):
        self.api_key = os.getenv("MEITY_API_KEY_VALUE") or settings.meity_api_key_value
        self.base_url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    async def translate_texts(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
    ) -> List[str]:
        """Translate a list of texts using the Bhashini API."""
        if not self.api_key:
            raise ValueError("Translation API key not configured")
        if not texts:
            return []

        headers = {
            "Accept": "/",
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        data = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang,
                        },
                        "serviceId": "bhashini/ai4b/bhili-nmt",
                    },
                }
            ],
            "inputData": {
                "input": [{"source": text} for text in texts],
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            pipeline_response = result.get("pipelineResponse", [])
            if pipeline_response and "output" in pipeline_response[0]:
                return [item.get("target", "") for item in pipeline_response[0]["output"]]

            raise ValueError("Unexpected response format from translation API")

    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate a single text using the Bhashini API."""
        if source_lang == target_lang:
            return text
        results = await self.translate_texts([text], source_lang, target_lang)
        return results[0] if results else text


translation_service = BhashiniTranslationService()

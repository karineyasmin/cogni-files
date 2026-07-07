from __future__ import annotations
import httpx
from typing import Any
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class LLMProviderService:
    """
    Orchestrates LLM generation requests, routing exclusively to
    the local Ollama instance for offline privacy and zero-cost inference.
    """

    def __init__(self) -> None:
        self.http_client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=settings.LOCAL_LLM_URL, timeout=180.0
        )

    async def generate_local_response(
        self, prompt: str, system_instruction: str = ""
    ) -> str:
        """
        Queries the configured local LLM via a generic completions protocol.
        """
        logger.info(f"Querying local model '{settings.LOCAL_MODEL_NAME}'...")
        try:
            payload: dict[str, Any] = {
                "model": settings.LOCAL_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            }
            response: httpx.Response = await self.http_client.post(
                "/v1/chat/completions", json=payload
            )
            response.raise_for_status()
            response_data: dict[str, Any] = response.json()
            answer: str = str(response_data["choices"][0]["message"]["content"])

            logger.info("Local response generated successfully.")
            return answer

        except Exception as e:
            logger.error(f"Local LLM generation failed: {str(e)}")
            raise e

    async def close(self) -> None:
        """Closes the active HTTP client connection pool gracefully."""
        await self.http_client.aclose()

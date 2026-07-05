from __future__ import annotations
from typing import Any, List, cast
from fastapi import APIRouter, HTTPException, status
from app.schemas.chat_schema import QueryRequest, QueryResponse
from app.services.llm_provider import LLMProviderService
from app.services.vector_storage import VectorStorageService
from app.core.logger import get_logger

logger = get_logger(__name__)

router: APIRouter = APIRouter()

llm_service: LLMProviderService = LLMProviderService()
vector_service: VectorStorageService = VectorStorageService()


router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question about processed documents using context-driven RAG.",
)


async def query_knowledge_base(payload: QueryRequest) -> Any:
    """
    Queries the vector database for relevant document context and orchestrates
    the generation of an answer using Gemini with an automated local Ollama fallback.
    """
    logger.info(f"Received query request for collection: '{payload.collection_name}'")

    try:
        raw_contexts: Any = cast(Any, vector_service).get_relevant_chunks(
            collection_name=payload.collection_name, query=payload.prompt, limit=4
        )
        retrieved_chunks: list[str] = cast(List[str], raw_contexts)

        if not retrieved_chunks:
            logger.warning(
                f"No semantic context found in collection '{payload.collection_name}' for this query."
            )
            return QueryResponse(
                answer="Não encontrei nenhuma informação relevante nos documentos enviados para responder a essa pergunta.",
                provider_used="none",
                retrieved_contexts=[],
            )

        context_block: str = "\n---\n".join(retrieved_chunks)

        system_instruction: str = (
            "Você é um tutor acadêmico especialista. Use estritamente os trechos de documentos fornecidos "
            "no 'CONTEÚDO DE SUPORTE' para responder à dúvida do aluno de forma didática e detalhada.\n"
            "Se o conteúdo fornecido não contiver a resposta, diga honestamente que não sabe com base nos documentos.\n\n"
            f"CONTEÚDO DE SUPORTE EXTRAÍDO DO BANCO VETORIAL:\n{context_block}"
        )

        history_context: str = ""
        if payload.history:
            history_context = "HISTÓRICO DA CONVERSA ATUAL:\n"
            for msg in payload.history:
                history_context += f"- {msg.role.upper()}: {msg.content}\n"
            history_context += "\n"

        final_prompt: str = f"{history_context}DÚVIDA ATUAL DO ALUNO: {payload.prompt}"

        provider_used: str = "gemini"

        try:
            logger.info("Attempting response generation via Gemini Cloud...")
            answer: str = await llm_service.generate_local_response(
                prompt=final_prompt, system_instruction=system_instruction
            )

        except Exception as cloud_err:
            logger.warning(
                f"Gemini cloud provider unavailable ({str(cloud_err)}). Initiating Ollama local fallback..."
            )
            provider_used = "ollama-fallback"

            # Estratégia de Fallback: Geração local via Llama 3.2 na CPU
            answer = await llm_service.generate_local_response(
                prompt=final_prompt, system_instruction=system_instruction
            )

        return QueryResponse(
            answer=answer,
            provider_used=provider_used,
            retrieved_contexts=retrieved_chunks,
        )

    except Exception as e:
        logger.error(f"Fatal error during RAG chat orchestration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat query: {str(e)}",
        )

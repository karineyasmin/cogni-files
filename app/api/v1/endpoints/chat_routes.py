from __future__ import annotations
from typing import Any, cast
from fastapi import APIRouter, HTTPException, status
from app.schemas.chat_schema import QueryRequest, QueryResponse
from app.services.llm_provider import LLMProviderService
from app.services.vector_storage import VectorStorageService
from app.core.logger import get_logger
import re
import unicodedata


logger = get_logger(__name__)

router: APIRouter = APIRouter()

# Inicialização das dependências de execução puramente local
llm_service: LLMProviderService = LLMProviderService()
vector_service: VectorStorageService = VectorStorageService()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question about processed documents using 100% local context-driven RAG.",
)
async def query_knowledge_base(payload: QueryRequest) -> Any:
    """
    Queries the local vector database for relevant document context and orchestrates
    the generation of an answer using the local Ollama instance.
    """
    logger.info(
        f"Received local query request for collection: '{payload.collection_name}'"
    )
    normalized = (
        unicodedata.normalize("NFKD", payload.collection_name)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )
    sanitized_collection = re.sub(r"[^a-zA-Z0-9._-]", "", normalized.replace(" ", "_"))

    try:
        # 1. Busca semântica de trechos relevantes no ChromaDB local usando o método real
        raw_contexts: Any = cast(Any, vector_service).query_similar_chunks(
            collection_name=sanitized_collection,
            query_text=payload.prompt,
            n_results=4,
        )
        retrieved_chunks: list[str] = cast(list[str], raw_contexts)

        # 2. Tratamento de contingência para coleções sem dados mapeados
        if not retrieved_chunks:
            logger.warning(
                f"No semantic context found in collection '{payload.collection_name}' for this query."
            )
            return QueryResponse(
                answer="Não encontrei nenhuma informação relevante nos documentos enviados para responder a essa pergunta.",
                provider_used="none",
                retrieved_contexts=[],
            )

        # 3. Consolidação dos fragmentos textuais extraídos
        context_block: str = "\n---\n".join(retrieved_chunks)

        # 4. Construção da instrução de contexto do sistema acadêmico
        system_instruction: str = (
            "Você é um tutor acadêmico especialista. Use estritamente os trechos de documentos fornecidos "
            "no 'CONTEÚDO DE SUPORTE' para responder à dúvida do aluno de forma didática e detalhada.\n"
            "Se o conteúdo fornecido não contiver a resposta, diga honestamente que não sabe com base nos documentos.\n\n"
            f"CONTEÚDO DE SUPORTE EXTRAÍDO DO BANCO VETORIAL:\n{context_block}"
        )

        # 5. Formatação do histórico linear de mensagens do estudante
        history_context: str = ""
        if payload.history:
            history_context = "HISTÓRICO DA CONVERSA ATUAL:\n"
            for msg in payload.history:
                history_context += f"- {msg.role.upper()}: {msg.content}\n"
            history_context += "\n"

        final_prompt: str = f"{history_context}DÚVIDA ATUAL DO ALUNO: {payload.prompt}"

        # 6. Geração de resposta direta via Ollama (Sem dependência de nuvem)
        logger.info("Generating academic response via local Ollama engine...")
        provider_used: str = "ollama-local"

        answer: str = await llm_service.generate_local_response(
            prompt=final_prompt, system_instruction=system_instruction
        )

        # 7. Resposta formatada retornada com sucesso
        return QueryResponse(
            answer=answer,
            provider_used=provider_used,
            retrieved_contexts=retrieved_chunks,
        )

    except Exception as e:
        logger.error(f"Fatal error during local RAG chat orchestration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat query: {str(e)}",
        )

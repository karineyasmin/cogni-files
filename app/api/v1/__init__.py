"""
API Version 1 Router Deployment Module.

Combines individual endpoint routers (documents, chat) into a unified
namespace prefixed under the v1 protocol specification.
"""

from fastapi import APIRouter
from app.api.v1.endpoints.document_routes import router as document_router
from app.api.v1.endpoints.chat_routes import router as chat_router

api_router: APIRouter = APIRouter()

api_router.include_router(
    document_router, prefix="/documents", tags=["Documents Ingestion"]
)
api_router.include_router(chat_router, prefix="/chat", tags=["Academic Chat Engine"])

__all__: list[str] = ["api_router"]

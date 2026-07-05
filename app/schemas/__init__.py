"""
Data Validation and Serialization Schemas Module.

This module unifies and exposes all Pydantic v2 schemas used across the
CogniFiles ecosystem to enforce strict type validation, sanitize payload inputs,
and serialize database structures into client-facing API responses.
"""

from app.schemas.document_schema import (
    DocumentChunkSchema,
    DocumentCreate,
    DocumentResponse,
)
from app.schemas.chat_schema import ChatMessageSchema, QueryRequest, QueryResponse

__all__: list[str] = [
    "DocumentChunkSchema",
    "DocumentCreate",
    "DocumentResponse",
    "ChatMessageSchema",
    "QueryRequest",
    "QueryResponse",
]

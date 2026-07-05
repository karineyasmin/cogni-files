"""
Data Persistence Layer - Repository Pattern Module.

This module encapsulates all asynchronous database CRUD interactions using the
Motor driver for MongoDB. By isolating data access queries into dedicated repository
classes, it decouples database schemas from the service layer, enhancing testing flexibility.
"""

from app.repositories.document_repository import DocumentRepository

__all__: list[str] = [
    "DocumentRepository",
]

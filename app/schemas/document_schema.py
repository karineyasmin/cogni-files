from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DocumentChunkSchema(BaseModel):
    """Defines the strucutre of a text chunk stored inside the database metadata"""

    chunk_id: str = Field(
        ..., description="Unique sequential ID generated for the cevtor store."
    )
    page_index: int = Field(
        ..., description="The physical page number where this chunk was extracted."
    )
    char_count: int = Field(
        ..., description="Total character length pf this text slice."
    )


class DocumentCreate(BaseModel):
    """Payload template required to register a document meeta-struct ure in MongoDB."""

    filename: str = Field(
        ..., min_length=1, max_length=255, description="Original uploaded PDF name."
    )
    content_type: str = Field(
        "application/pdf", description="MIME type of the uploaded asset."
    )
    file_size_bytes: int = Field(
        ..., gt=0, description="Total size of the file in bytes."
    )
    collection_name: str = Field(
        ..., min_length=3, description="The targeted isolated ChromaDB vector table."
    )


class DocumentResponse(BaseModel):
    """The strict typed interface returned by the API to the client applications."""

    id: str = Field(
        ..., validation_alias="_id", description="The stringified MongoDB ObjectId."
    )
    filename: str
    content_type: str
    file_size_bytes: int
    collection_name: str
    total_chunks: int = Field(
        0, description="Total count of text chunks sent to ChromaDB"
    )
    processed_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp of parsing execution."
    )

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    requirement_text: str = Field(
        ...,
        min_length=10,
        description="Requerimiento en texto libre",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Número de historias similares a recuperar del knowledge base",
    )

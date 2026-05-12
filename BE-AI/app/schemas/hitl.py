from typing import Literal
from pydantic import BaseModel


class AmbiguityItem(BaseModel):
    word: str
    category: str
    ieee_830_violation: str
    iso_25010_category: str
    suggestion: str
    context: str
    severity: Literal["alta", "media", "baja"]


class HitlStartResponse(BaseModel):
    session_id: str
    requirement_preview: str
    ambiguity_count: int
    ambiguities: list[AmbiguityItem]
    requires_review: bool


class AnalystResolution(BaseModel):
    word: str
    category: str
    analyst_resolution: str = ""
    status: Literal["resolved", "dismissed"]


class HitlResolveRequest(BaseModel):
    session_id: str
    resolutions: list[AnalystResolution]

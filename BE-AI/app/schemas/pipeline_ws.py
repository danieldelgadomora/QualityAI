from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class StartPipelineMsg(BaseModel):
    type: Literal["start_pipeline"]
    requirement_text: str = Field(min_length=10)
    top_k: int = Field(default=3, ge=1, le=10)
    interactive_m1: bool = True


class AnalystResolutionItem(BaseModel):
    word: str
    category: str
    analyst_resolution: str = ""
    status: Literal["resolved", "dismissed"]


class ResolveAmbiguitiesMsg(BaseModel):
    type: Literal["resolve_ambiguities"]
    resolutions: list[AnalystResolutionItem]


class ReviewerIdMsg(BaseModel):
    type: Literal["reviewer_id"]
    reviewer: str = Field(min_length=1)


class ScenarioActionMsg(BaseModel):
    type: Literal["scenario_action"]
    scenario_index: int
    action: Literal["accept", "reclassify", "comment", "skip"]
    new_quality_characteristic: str | None = None
    note: str | None = None


class GlobalDecisionMsg(BaseModel):
    type: Literal["global_decision"]
    decision: Literal["approve", "reject", "request_changes"]
    feedback: str | None = None


InboundMessage = Annotated[
    Union[
        StartPipelineMsg,
        ResolveAmbiguitiesMsg,
        ReviewerIdMsg,
        ScenarioActionMsg,
        GlobalDecisionMsg,
    ],
    Field(discriminator="type"),
]

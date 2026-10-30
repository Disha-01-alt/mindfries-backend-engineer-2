"""Request/response models for the API (pydantic v2)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..core.metrics import MetricKind


class EnrollRequest(BaseModel):
    member_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    chronological_age: float = Field(gt=0, lt=130)
    coach_id: str | None = None


class DeviceRequest(BaseModel):
    device_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    kind: str = Field(min_length=1)


class ReadingRequest(BaseModel):
    member_id: str
    device_id: str
    metric: MetricKind
    event_time: float
    value: float
    unit: str
    seq: int
    source: str


class ContributionOut(BaseModel):
    metric: str
    aggregate: float
    sample_count: int
    risk: float
    weight: float
    note: str


class ScoreOut(BaseModel):
    member_id: str
    as_of: float
    overall: float
    band: str
    sample_count: int
    contributions: list[ContributionOut]


class AgingOut(BaseModel):
    member_id: str
    as_of: float
    chronological_age: float
    biological_age: float
    delta_years: float


class CohortRequest(BaseModel):
    member_ids: list[str]


class CohortOut(BaseModel):
    size: int
    scored: int
    average_overall: float
    band_distribution: dict[str, int]
    high_risk_members: list[str]

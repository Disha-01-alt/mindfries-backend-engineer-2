"""HTTP routes for ALIVE O.S."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..core.aging import AgingAssessment
from ..core.score import RiskScore
from ..engine import Engine
from .deps import get_engine
from .schemas import (
    AgingOut,
    CohortOut,
    CohortRequest,
    ContributionOut,
    DeviceRequest,
    EnrollRequest,
    ReadingRequest,
    ScoreOut,
)

router = APIRouter()


def _score_out(score: RiskScore) -> ScoreOut:
    return ScoreOut(
        member_id=score.member_id,
        as_of=score.as_of,
        overall=score.overall,
        band=score.band.value,
        sample_count=score.sample_count,
        contributions=[
            ContributionOut(
                metric=c.metric.value, aggregate=c.aggregate, sample_count=c.sample_count,
                risk=c.risk, weight=c.weight, note=c.note,
            )
            for c in score.contributions
        ],
    )


def _aging_out(a: AgingAssessment) -> AgingOut:
    return AgingOut(
        member_id=a.member_id, as_of=a.as_of, chronological_age=a.chronological_age,
        biological_age=a.biological_age, delta_years=a.delta_years,
    )


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/members", status_code=201)
def enroll(req: EnrollRequest, engine: Engine = Depends(get_engine)) -> dict[str, str]:
    m = engine.enroll(req.member_id, req.name, req.chronological_age, req.coach_id)
    return {"member_id": m.member_id, "coach_id": m.coach_id or ""}


@router.post("/members/{member_id}/devices", status_code=201)
def register_device(member_id: str, req: DeviceRequest, engine: Engine = Depends(get_engine)) -> dict[str, str]:
    d = engine.register_device(req.device_id, member_id, req.source, req.kind)
    return {"device_id": d.device_id, "member_id": d.member_id}


@router.post("/ingest")
def ingest(req: ReadingRequest, engine: Engine = Depends(get_engine)) -> ScoreOut | dict[str, str]:
    score = engine.submit(
        member_id=req.member_id, device_id=req.device_id, metric=req.metric, event_time=req.event_time,
        value=req.value, unit=req.unit, seq=req.seq, source=req.source,
    )
    return _score_out(score) if score else {"status": "ingested", "score": "pending"}


@router.get("/members/{member_id}/score")
def get_score(member_id: str, engine: Engine = Depends(get_engine)) -> ScoreOut:
    score = engine.score_of(member_id)
    if score is None:
        raise HTTPException(status_code=404, detail="no score yet for this member")
    return _score_out(score)


@router.get("/members/{member_id}/aging")
def get_aging(member_id: str, engine: Engine = Depends(get_engine)) -> AgingOut:
    a = engine.aging_of(member_id)
    if a is None:
        raise HTTPException(status_code=404, detail="no aging assessment yet for this member")
    return _aging_out(a)


@router.post("/cohorts/summary")
def cohort_summary(req: CohortRequest, engine: Engine = Depends(get_engine)) -> CohortOut:
    s = engine.cohort_summary(req.member_ids)
    return CohortOut(
        size=s.size, scored=s.scored, average_overall=s.average_overall,
        band_distribution=s.band_distribution, high_risk_members=list(s.high_risk_members),
    )

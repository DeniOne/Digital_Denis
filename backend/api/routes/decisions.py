"""
Digital Denis — Decision Analysis API Routes
═══════════════════════════════════════════════════════════════════════════

REST API endpoints for decision analysis.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from analytics.logic import decision_analysis_service
from core.auth import get_current_user_optional
from memory.models import User


router = APIRouter(tags=["Decision Analysis"])


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class ArgumentSchema(BaseModel):
    content: str
    strength: str
    evidence: Optional[str] = None


class AssumptionSchema(BaseModel):
    content: str
    verified: bool
    risk_if_wrong: str


class LogicIssueSchema(BaseModel):
    issue_type: str
    severity: str
    description: str


class RiskSchema(BaseModel):
    risk_type: str
    impact: str
    likelihood: str
    description: str
    mitigation: Optional[str] = None


class DecisionStructureSchema(BaseModel):
    hypothesis: str
    arguments: List[ArgumentSchema]
    counterarguments: List[ArgumentSchema]
    assumptions: List[AssumptionSchema]
    confidence: float
    urgency: str
    reversibility: str


class DecisionAnalysisResponse(BaseModel):
    decision_id: UUID
    structure: DecisionStructureSchema
    strong_points: List[str]
    weak_points: List[LogicIssueSchema]
    risks: List[RiskSchema]
    overall_score: float
    clarity_score: float
    completeness_score: float
    risk_level: str
    recommendation: str
    analyzed_at: str


class AnalysisSummaryResponse(BaseModel):
    decision_id: UUID
    overall_score: float
    risk_level: str
    strong_points_count: int
    weak_points_count: int
    risks_count: int
    analyzed_at: str


class StatsResponse(BaseModel):
    total_analyses: int
    average_score: float
    by_risk_level: dict


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/{decision_id}/analyze", response_model=DecisionAnalysisResponse)
async def analyze_decision(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Analyze a decision's logic quality.
    Creates a new analysis for the specified decision.
    """
    result = await decision_analysis_service.analyze_decision(db, decision_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    await db.commit()
    
    return DecisionAnalysisResponse(
        decision_id=result.decision_id,
        structure=DecisionStructureSchema(
            hypothesis=result.structure.hypothesis,
            arguments=[
                ArgumentSchema(
                    content=a.content,
                    strength=a.strength,
                    evidence=a.evidence,
                )
                for a in result.structure.arguments
            ],
            counterarguments=[
                ArgumentSchema(
                    content=a.content,
                    strength=a.strength,
                    evidence=a.evidence,
                )
                for a in result.structure.counterarguments
            ],
            assumptions=[
                AssumptionSchema(
                    content=a.content,
                    verified=a.verified,
                    risk_if_wrong=a.risk_if_wrong,
                )
                for a in result.structure.assumptions
            ],
            confidence=result.structure.confidence,
            urgency=result.structure.urgency,
            reversibility=result.structure.reversibility,
        ),
        strong_points=result.strong_points,
        weak_points=[
            LogicIssueSchema(
                issue_type=i.issue_type,
                severity=i.severity,
                description=i.description,
            )
            for i in result.weak_points
        ],
        risks=[
            RiskSchema(
                risk_type=r.risk_type,
                impact=r.impact,
                likelihood=r.likelihood,
                description=r.description,
                mitigation=r.mitigation,
            )
            for r in result.risks
        ],
        overall_score=result.overall_score,
        clarity_score=result.clarity_score,
        completeness_score=result.completeness_score,
        risk_level=result.risk_level,
        recommendation=result.recommendation,
        analyzed_at=result.analyzed_at.isoformat(),
    )


@router.get("/{decision_id}/analysis")
async def get_decision_analysis(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get existing analysis for a decision."""
    analysis = await decision_analysis_service.get_analysis(db, decision_id)
    
    if not analysis:
        raise HTTPException(
            status_code=404, 
            detail="Analysis not found. Use POST to create one."
        )
    
    return {
        "decision_id": str(analysis.decision_id),
        "overall_score": analysis.overall_score,
        "clarity_score": analysis.clarity_score,
        "completeness_score": analysis.completeness_score,
        "risk_level": analysis.risk_level,
        "strong_points": analysis.strong_points,
        "weak_points": analysis.weak_points,
        "risks": analysis.risks,
        "analyzed_at": analysis.analyzed_at.isoformat(),
    }


@router.get("/", response_model=List[AnalysisSummaryResponse])
async def list_analyses(
    limit: int = Query(20, ge=1, le=100),
    min_score: Optional[float] = Query(None, ge=0, le=1),
    max_score: Optional[float] = Query(None, ge=0, le=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """List all decision analyses with optional filtering."""
    analyses = await decision_analysis_service.get_all_analyses(
        db,
        user_id=current_user.id,
        limit=limit,
        min_score=min_score,
        max_score=max_score,
    )
    
    return [
        AnalysisSummaryResponse(
            decision_id=a.decision_id,
            overall_score=a.overall_score or 0,
            risk_level=a.risk_level or "unknown",
            strong_points_count=len(a.strong_points) if a.strong_points else 0,
            weak_points_count=len(a.weak_points) if a.weak_points else 0,
            risks_count=len(a.risks) if a.risks else 0,
            analyzed_at=a.analyzed_at.isoformat() if a.analyzed_at else "",
        )
        for a in analyses
    ]


@router.get("/stats", response_model=StatsResponse)
async def get_analysis_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get decision analysis statistics."""
    stats = await decision_analysis_service.get_stats(db, user_id=current_user.id)
    return StatsResponse(**stats)


@router.get("/risk-levels")
async def get_risk_level_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get distribution of risk levels across all decisions."""
    from analytics.cal_models import CALDecisionAnalysis
    from sqlalchemy import select, func
    
    result = await db.execute(
        select(
            CALDecisionAnalysis.risk_level,
            func.count(CALDecisionAnalysis.id).label("count"),
            func.avg(CALDecisionAnalysis.overall_score).label("avg_score")
        ).where(CALDecisionAnalysis.user_id == current_user.id).group_by(CALDecisionAnalysis.risk_level)
    )
    
    return [
        {
            "risk_level": row.risk_level,
            "count": row.count,
            "average_score": round(row.avg_score, 2) if row.avg_score else 0,
        }
        for row in result.fetchall()
    ]

"""
Digital Den — Logic Analysis Pipeline
═══════════════════════════════════════════════════════════════════════════

Decision quality analysis: structure extraction, logic validation, risk assessment.
"""

import json
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.cal_models import CALDecisionAnalysis
from memory.models import MemoryItem
from llm.groq import groq


# ═══════════════════════════════════════════════════════════════════════════
# Enums and Constants
# ═══════════════════════════════════════════════════════════════════════════

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LogicIssueType(str, Enum):
    LOGICAL_HOLE = "logical_hole"
    UNVERIFIED_ASSUMPTION = "unverified_assumption"
    IGNORED_COUNTERARGUMENT = "ignored_counterargument"
    CIRCULAR_REASONING = "circular_reasoning"
    FALSE_DICHOTOMY = "false_dichotomy"
    CONFIRMATION_BIAS = "confirmation_bias"
    SUNK_COST_FALLACY = "sunk_cost_fallacy"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    WEAK_ARGUMENT = "weak_argument"
    MISSING_EVIDENCE = "missing_evidence"


class RiskType(str, Enum):
    ASSUMPTION_FAILURE = "assumption_failure"
    EXECUTION_RISK = "execution_risk"
    MARKET_RISK = "market_risk"
    RESOURCE_RISK = "resource_risk"
    TIMING_RISK = "timing_risk"
    UNKNOWN_UNKNOWNS = "unknown_unknowns"


# ═══════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Argument:
    """Supporting or opposing argument."""
    content: str
    strength: str = "moderate"  # weak, moderate, strong
    evidence: Optional[str] = None


@dataclass
class Assumption:
    """Underlying assumption."""
    content: str
    verified: bool = False
    risk_if_wrong: str = "medium"  # low, medium, high


@dataclass
class LogicIssue:
    """Detected logic issue."""
    issue_type: str
    severity: str
    description: str
    location: Optional[str] = None


@dataclass
class Risk:
    """Identified risk."""
    risk_type: str
    impact: str  # low, medium, high
    likelihood: str  # low, medium, high
    description: str
    mitigation: Optional[str] = None


@dataclass
class DecisionStructure:
    """Structured representation of a decision."""
    hypothesis: str
    arguments: List[Argument] = field(default_factory=list)
    counterarguments: List[Argument] = field(default_factory=list)
    assumptions: List[Assumption] = field(default_factory=list)
    confidence: float = 0.5
    urgency: str = "medium"  # low, medium, high
    reversibility: str = "moderate"  # easy, moderate, hard
    context: Optional[str] = None


@dataclass
class DecisionAnalysisResult:
    """Complete analysis result."""
    decision_id: UUID
    structure: DecisionStructure
    strong_points: List[str]
    weak_points: List[LogicIssue]
    risks: List[Risk]
    overall_score: float
    clarity_score: float
    completeness_score: float
    risk_level: str
    recommendation: str
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════
# Logic Analyzer
# ═══════════════════════════════════════════════════════════════════════════

class LogicAnalyzer:
    """
    Decision logic analysis pipeline.
    
    1. Extract structure (hypothesis, arguments, assumptions)
    2. Validate logic (find fallacies and gaps)
    3. Assess risks
    4. Generate report
    """
    
    async def analyze(
        self,
        db: AsyncSession,
        decision: MemoryItem,
    ) -> DecisionAnalysisResult:
        """Run full analysis pipeline on a decision."""
        
        # 1. Extract structure
        structure = await self._extract_structure(decision)
        
        # 2. Validate logic
        logic_issues = await self._validate_logic(structure)
        
        # 3. Assess risks
        risks = await self._assess_risks(structure, logic_issues)
        
        # 4. Find strong points
        strong_points = self._find_strong_points(structure)
        
        # 5. Calculate scores
        overall_score = self._calculate_score(structure, logic_issues, risks)
        clarity_score = self._calculate_clarity(structure)
        completeness_score = self._calculate_completeness(structure)
        risk_level = self._determine_risk_level(risks)
        recommendation = self._generate_recommendation(overall_score, risk_level)
        
        result = DecisionAnalysisResult(
            decision_id=decision.id,
            structure=structure,
            strong_points=strong_points,
            weak_points=logic_issues,
            risks=risks,
            overall_score=overall_score,
            clarity_score=clarity_score,
            completeness_score=completeness_score,
            risk_level=risk_level,
            recommendation=recommendation,
        )
        
        # Save to database
        await self._save_analysis(db, result)
        
        return result
    
    async def _extract_structure(
        self,
        decision: MemoryItem
    ) -> DecisionStructure:
        """Use LLM to extract decision structure."""
        
        prompt = f"""Проанализируй это решение и извлеки его логическую структуру.

Решение:
{decision.content}

{f"Контекст: {decision.structured_data}" if decision.structured_data else ""}

Верни JSON:
{{
    "hypothesis": "главное утверждение/решение",
    "arguments": [
        {{"content": "аргумент за", "strength": "weak|moderate|strong", "evidence": "доказательство или null"}}
    ],
    "counterarguments": [
        {{"content": "аргумент против", "strength": "weak|moderate|strong"}}
    ],
    "assumptions": [
        {{"content": "предположение", "verified": true/false, "risk_if_wrong": "low|medium|high"}}
    ],
    "confidence": 0.0-1.0,
    "urgency": "low|medium|high",
    "reversibility": "easy|moderate|hard"
}}

JSON:"""
        
        try:
            result = await groq.complete_simple(prompt)
            data = self._parse_json(result)
            
            return DecisionStructure(
                hypothesis=data.get("hypothesis", decision.content[:100]),
                arguments=[
                    Argument(
                        content=a.get("content", ""),
                        strength=a.get("strength", "moderate"),
                        evidence=a.get("evidence"),
                    )
                    for a in data.get("arguments", [])
                ],
                counterarguments=[
                    Argument(
                        content=a.get("content", ""),
                        strength=a.get("strength", "moderate"),
                    )
                    for a in data.get("counterarguments", [])
                ],
                assumptions=[
                    Assumption(
                        content=a.get("content", ""),
                        verified=a.get("verified", False),
                        risk_if_wrong=a.get("risk_if_wrong", "medium"),
                    )
                    for a in data.get("assumptions", [])
                ],
                confidence=data.get("confidence", 0.5),
                urgency=data.get("urgency", "medium"),
                reversibility=data.get("reversibility", "moderate"),
            )
            
        except Exception as e:
            print(f"Error extracting structure: {e}")
            return DecisionStructure(
                hypothesis=decision.content[:100],
                confidence=0.5,
            )
    
    async def _validate_logic(
        self,
        structure: DecisionStructure
    ) -> List[LogicIssue]:
        """Check for logical fallacies and gaps."""
        issues = []
        
        # Check for missing counterarguments
        if len(structure.counterarguments) == 0:
            issues.append(LogicIssue(
                issue_type=LogicIssueType.IGNORED_COUNTERARGUMENT.value,
                severity=Severity.MEDIUM.value,
                description="Не рассмотрены контраргументы — возможна confirmation bias",
            ))
        
        # Check for unverified high-risk assumptions
        for assumption in structure.assumptions:
            if not assumption.verified and assumption.risk_if_wrong in ["high", "critical"]:
                issues.append(LogicIssue(
                    issue_type=LogicIssueType.UNVERIFIED_ASSUMPTION.value,
                    severity=Severity.HIGH.value,
                    description=f"Непроверенное важное допущение: {assumption.content}",
                ))
        
        # Check for weak arguments
        weak_args = [a for a in structure.arguments if a.strength == "weak"]
        if len(weak_args) > len(structure.arguments) / 2 and len(structure.arguments) > 0:
            issues.append(LogicIssue(
                issue_type=LogicIssueType.WEAK_ARGUMENT.value,
                severity=Severity.MEDIUM.value,
                description="Большинство аргументов слабые",
            ))
        
        # Check for missing evidence
        no_evidence = [a for a in structure.arguments if not a.evidence]
        if len(no_evidence) == len(structure.arguments) and len(structure.arguments) > 0:
            issues.append(LogicIssue(
                issue_type=LogicIssueType.MISSING_EVIDENCE.value,
                severity=Severity.MEDIUM.value,
                description="Аргументы не подкреплены доказательствами",
            ))
        
        # LLM-based deeper analysis
        llm_issues = await self._llm_logic_check(structure)
        issues.extend(llm_issues)
        
        return issues
    
    async def _llm_logic_check(
        self,
        structure: DecisionStructure
    ) -> List[LogicIssue]:
        """Use LLM for deeper logic analysis."""
        
        prompt = f"""Проверь логику этого решения на наличие ошибок:

Гипотеза: {structure.hypothesis}
Аргументы: {[a.content for a in structure.arguments]}
Контраргументы: {[a.content for a in structure.counterarguments]}
Допущения: {[a.content for a in structure.assumptions]}

Проверь на:
1. Логические дыры (вывод не следует из аргументов)
2. Circular reasoning (аргумент = переформулировка вывода)
3. False dichotomy (только 2 варианта из многих)
4. Sunk cost fallacy ("уже вложили много")
5. Appeal to authority (без собственных рассуждений)

Верни JSON массив найденных проблем:
[{{"issue_type": "тип", "severity": "low|medium|high", "description": "описание"}}]

Если проблем нет — верни [].
JSON:"""
        
        try:
            result = await groq.complete_simple(prompt)
            data = self._parse_json(result)
            
            if isinstance(data, list):
                return [
                    LogicIssue(
                        issue_type=item.get("issue_type", "unknown"),
                        severity=item.get("severity", "medium"),
                        description=item.get("description", ""),
                    )
                    for item in data
                ]
            return []
            
        except Exception:
            return []
    
    async def _assess_risks(
        self,
        structure: DecisionStructure,
        logic_issues: List[LogicIssue]
    ) -> List[Risk]:
        """Assess risks based on structure and logic issues."""
        risks = []
        
        # Risk from unverified assumptions
        for assumption in structure.assumptions:
            if not assumption.verified:
                risks.append(Risk(
                    risk_type=RiskType.ASSUMPTION_FAILURE.value,
                    impact=assumption.risk_if_wrong,
                    likelihood="medium" if not assumption.verified else "low",
                    description=f"Если '{assumption.content}' окажется неверным",
                    mitigation=f"Проверить допущение: {assumption.content}",
                ))
        
        # Risk from low reversibility + high-severity issues
        severe_issues = [i for i in logic_issues if i.severity == "high"]
        if structure.reversibility == "hard" and severe_issues:
            risks.append(Risk(
                risk_type=RiskType.EXECUTION_RISK.value,
                impact="high",
                likelihood="medium",
                description="Решение трудно отменить, но есть серьёзные логические проблемы",
                mitigation="Рекомендуется дополнительный анализ перед выполнением",
            ))
        
        # Risk from low confidence + high urgency
        if structure.confidence < 0.5 and structure.urgency == "high":
            risks.append(Risk(
                risk_type=RiskType.TIMING_RISK.value,
                impact="medium",
                likelihood="high",
                description="Срочное решение с низкой уверенностью",
                mitigation="По возможности выделить время на дополнительный анализ",
            ))
        
        return risks
    
    def _find_strong_points(
        self,
        structure: DecisionStructure
    ) -> List[str]:
        """Identify strong points of the decision."""
        points = []
        
        # Clear hypothesis
        if len(structure.hypothesis) > 10:
            points.append("Чёткая формулировка решения")
        
        # Multiple arguments
        if len(structure.arguments) >= 2:
            points.append(f"Поддержано {len(structure.arguments)} аргументами")
        
        # Strong arguments
        strong_args = [a for a in structure.arguments if a.strength == "strong"]
        if strong_args:
            points.append(f"{len(strong_args)} сильных аргументов")
        
        # Evidence provided
        with_evidence = [a for a in structure.arguments if a.evidence]
        if with_evidence:
            points.append("Аргументы подкреплены доказательствами")
        
        # Counterarguments considered
        if structure.counterarguments:
            points.append("Рассмотрены контраргументы")
        
        # High confidence
        if structure.confidence >= 0.8:
            points.append("Высокая уверенность в решении")
        
        # Easy reversibility
        if structure.reversibility == "easy":
            points.append("Решение легко отменить при необходимости")
        
        return points
    
    def _calculate_score(
        self,
        structure: DecisionStructure,
        issues: List[LogicIssue],
        risks: List[Risk]
    ) -> float:
        """Calculate overall decision quality score (0-1)."""
        score = 0.5  # Base
        
        # Bonus for arguments
        score += min(0.15, len(structure.arguments) * 0.05)
        
        # Bonus for counterarguments
        score += min(0.1, len(structure.counterarguments) * 0.05)
        
        # Bonus for evidence
        with_evidence = [a for a in structure.arguments if a.evidence]
        score += min(0.1, len(with_evidence) * 0.05)
        
        # Penalty for issues
        for issue in issues:
            if issue.severity == "high":
                score -= 0.15
            elif issue.severity == "medium":
                score -= 0.08
            else:
                score -= 0.03
        
        # Penalty for high risks
        high_risks = [r for r in risks if r.impact == "high"]
        score -= len(high_risks) * 0.1
        
        # Factor in confidence
        score = score * 0.7 + structure.confidence * 0.3
        
        return max(0.0, min(1.0, score))
    
    def _calculate_clarity(self, structure: DecisionStructure) -> float:
        """Calculate clarity score."""
        score = 0.5
        
        if len(structure.hypothesis) > 20:
            score += 0.2
        if structure.arguments:
            score += 0.15
        if structure.assumptions:
            score += 0.15
        
        return min(1.0, score)
    
    def _calculate_completeness(self, structure: DecisionStructure) -> float:
        """Calculate completeness score."""
        score = 0.0
        
        # Has hypothesis
        if structure.hypothesis:
            score += 0.2
        
        # Has arguments
        if structure.arguments:
            score += 0.2
        
        # Has counterarguments
        if structure.counterarguments:
            score += 0.2
        
        # Has assumptions
        if structure.assumptions:
            score += 0.2
        
        # Has verified assumptions
        verified = [a for a in structure.assumptions if a.verified]
        if verified:
            score += 0.2
        
        return score
    
    def _determine_risk_level(self, risks: List[Risk]) -> str:
        """Determine overall risk level."""
        high_impact = [r for r in risks if r.impact == "high"]
        medium_impact = [r for r in risks if r.impact == "medium"]
        
        if len(high_impact) >= 2:
            return "high"
        elif high_impact or len(medium_impact) >= 3:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendation(self, score: float, risk_level: str) -> str:
        """Generate recommendation based on analysis."""
        if score >= 0.8 and risk_level == "low":
            return "Рекомендуется к выполнению"
        elif score >= 0.6 and risk_level != "high":
            return "Можно выполнять с учётом замечаний"
        elif score >= 0.4:
            return "Рекомендуется доработать перед выполнением"
        else:
            return "Требуется существенная доработка"
    
    async def _save_analysis(
        self,
        db: AsyncSession,
        result: DecisionAnalysisResult
    ) -> None:
        """Save analysis to database."""
        analysis = CALDecisionAnalysis(
            id=uuid4(),
            decision_id=result.decision_id,
            strong_points=result.strong_points,
            weak_points=[
                {"type": i.issue_type, "severity": i.severity, "description": i.description}
                for i in result.weak_points
            ],
            risks=[
                {"type": r.risk_type, "impact": r.impact, "description": r.description, "mitigation": r.mitigation}
                for r in result.risks
            ],
            overall_score=result.overall_score,
            clarity_score=result.clarity_score,
            completeness_score=result.completeness_score,
            risk_level=result.risk_level,
            recommendations=result.strong_points,  # Store strong points as recommendations too
        )
        db.add(analysis)
    
    def _parse_json(self, text: str) -> Any:
        """Parse JSON from LLM response."""
        text = text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        # Find JSON
        start = text.find("{") if "{" in text else text.find("[")
        end = max(text.rfind("}"), text.rfind("]")) + 1
        
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# Decision Analysis Service
# ═══════════════════════════════════════════════════════════════════════════

class DecisionAnalysisService:
    """Service for decision analysis operations."""
    
    def __init__(self):
        self.analyzer = LogicAnalyzer()
    
    async def analyze_decision(
        self,
        db: AsyncSession,
        decision_id: UUID
    ) -> Optional[DecisionAnalysisResult]:
        """Analyze a decision by ID."""
        result = await db.execute(
            select(MemoryItem).where(
                and_(
                    MemoryItem.id == decision_id,
                    MemoryItem.item_type == "decision"
                )
            )
        )
        decision = result.scalar_one_or_none()
        
        if not decision:
            return None
        
        return await self.analyzer.analyze(db, decision)
    
    async def get_analysis(
        self,
        db: AsyncSession,
        decision_id: UUID
    ) -> Optional[CALDecisionAnalysis]:
        """Get existing analysis for a decision."""
        result = await db.execute(
            select(CALDecisionAnalysis)
            .where(CALDecisionAnalysis.decision_id == decision_id)
            .order_by(CALDecisionAnalysis.analyzed_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_all_analyses(
        self,
        db: AsyncSession,
        limit: int = 20,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
    ) -> List[CALDecisionAnalysis]:
        """Get all analyses with optional filtering."""
        query = select(CALDecisionAnalysis)
        
        if min_score is not None:
            query = query.where(CALDecisionAnalysis.overall_score >= min_score)
        if max_score is not None:
            query = query.where(CALDecisionAnalysis.overall_score <= max_score)
        
        query = query.order_by(CALDecisionAnalysis.analyzed_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_stats(
        self,
        db: AsyncSession
    ) -> Dict:
        """Get decision analysis statistics."""
        from sqlalchemy import func
        
        # Count by risk level
        risk_result = await db.execute(
            select(
                CALDecisionAnalysis.risk_level,
                func.count(CALDecisionAnalysis.id).label("count")
            ).group_by(CALDecisionAnalysis.risk_level)
        )
        risk_counts = {row.risk_level: row.count for row in risk_result.fetchall()}
        
        # Average score
        score_result = await db.execute(
            select(func.avg(CALDecisionAnalysis.overall_score))
        )
        avg_score = score_result.scalar() or 0
        
        # Total count
        count_result = await db.execute(
            select(func.count(CALDecisionAnalysis.id))
        )
        total = count_result.scalar() or 0
        
        return {
            "total_analyses": total,
            "average_score": round(avg_score, 2),
            "by_risk_level": risk_counts,
        }


# Global instances
logic_analyzer = LogicAnalyzer()
decision_analysis_service = DecisionAnalysisService()

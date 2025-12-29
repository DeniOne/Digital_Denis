# ⚖️ TASK 3.3 — Logic Analysis Pipeline

**Проект:** Digital Denis  
**Статус:** ✅ Завершено  
**Приоритет:** Средний  
**Зависимости:** TASK 3.1

---

## 📋 Чеклист реализации (v1.0)

- [x] Создать backend/analytics/logic.py
- [x] Реализовать LogicAnalyzer
- [x] Реализовать extract_structure() с LLM
- [x] Реализовать validate_logic()
- [x] Создать таблицу cal_decision_analysis
- [x] API endpoint /analytics/decisions/{id}
- [x] Написать unit-тесты

---

## 🎯 Цель

Спроектировать пайплайн логического анализа решений: входы, выходы, типовые риски.

---

## 📦 Артефакты

### 1. Decision Schema

```python
@dataclass
class DecisionStructure:
    """Structured representation of a decision"""
    
    # Core content
    hypothesis: str  # What is being decided
    
    # Supporting elements
    arguments: List[Argument]  # Pro arguments
    counterarguments: List[Argument]  # Against
    assumptions: List[Assumption]  # Underlying beliefs
    
    # Metadata
    confidence: float  # 0.0 - 1.0
    urgency: str  # low, medium, high
    reversibility: str  # easy, moderate, hard
    
    # Outcome (filled later)
    outcome: Optional[Outcome] = None

@dataclass
class Argument:
    content: str
    strength: str  # weak, moderate, strong
    evidence: Optional[str]
    
@dataclass
class Assumption:
    content: str
    verified: bool
    risk_if_wrong: str  # low, medium, high
```

---

### 2. Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LOGIC ANALYSIS PIPELINE                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Decision   │ => │  Structure  │ => │   Logic     │ => │   Risk      │
│   Input     │    │  Extraction │    │  Validation │    │ Assessment  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                  │                  │
                          ▼                  ▼                  ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │ Hypothesis  │    │ Logic Gaps  │    │ Risk Flags  │
                   │ Arguments   │    │ Fallacies   │    │ Warnings    │
                   │ Assumptions │    │ Weaknesses  │    │ Score       │
                   └─────────────┘    └─────────────┘    └─────────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │  FINAL REPORT   │
                                   │  ─────────────  │
                                   │  🟢 Strong pts  │
                                   │  🟡 Weak pts    │
                                   │  🔴 Risks       │
                                   │  📊 Score       │
                                   └─────────────────┘
```

---

### 3. Типовые логические риски

| Риск | Описание | Индикатор | Severity |
|------|----------|-----------|----------|
| **Logical hole** | Вывод не следует из аргументов | Gap in reasoning | 🔴 High |
| **Unverified assumption** | Допущение без проверки | "Assuming that..." | 🟡 Medium |
| **Ignored counterargument** | Не рассмотрены возражения | No cons listed | 🟡 Medium |
| **Circular reasoning** | Аргумент = переформулировка вывода | Self-reference | 🔴 High |
| **False dichotomy** | Только 2 варианта из многих | "Either X or Y" | 🟡 Medium |
| **Confirmation bias** | Только поддерживающие факты | No contra evidence | 🟡 Medium |
| **Sunk cost fallacy** | "Уже вложили много" | Past investment | 🟠 Medium-High |
| **Appeal to authority** | "X сказал, значит верно" | No own reasoning | 🟡 Medium |

---

### 4. Logic Analyzer Implementation

```python
class LogicAnalyzer:
    async def analyze(self, decision: MemoryItem) -> DecisionAnalysis:
        # 1. Extract structure
        structure = await self._extract_structure(decision)
        
        # 2. Validate logic
        logic_issues = await self._validate_logic(structure)
        
        # 3. Assess risks
        risks = await self._assess_risks(structure, logic_issues)
        
        # 4. Generate report
        return DecisionAnalysis(
            decision_id=decision.id,
            structure=structure,
            strong_points=self._find_strong_points(structure),
            weak_points=logic_issues,
            risks=risks,
            overall_score=self._calculate_score(structure, logic_issues, risks)
        )
    
    async def _extract_structure(self, decision: MemoryItem) -> DecisionStructure:
        """Use LLM to extract decision structure"""
        prompt = f"""
        Analyze this decision and extract its logical structure:
        
        Decision: {decision.content}
        
        Return JSON with:
        - hypothesis: main claim/decision
        - arguments: list of supporting arguments with strength
        - counterarguments: list of opposing points
        - assumptions: underlying beliefs (mark if verified)
        - confidence: estimated confidence 0.0-1.0
        """
        result = await self.llm.complete(prompt)
        return DecisionStructure.from_json(result)
    
    async def _validate_logic(self, structure: DecisionStructure) -> List[LogicIssue]:
        """Check for logical fallacies and gaps"""
        issues = []
        
        # Check for missing counterarguments
        if len(structure.counterarguments) == 0:
            issues.append(LogicIssue(
                type="ignored_counterargument",
                severity="medium",
                description="No counterarguments considered"
            ))
        
        # Check for unverified assumptions
        unverified = [a for a in structure.assumptions if not a.verified]
        for assumption in unverified:
            if assumption.risk_if_wrong in ["high", "critical"]:
                issues.append(LogicIssue(
                    type="unverified_assumption",
                    severity="high",
                    description=f"Unverified: {assumption.content}"
                ))
        
        # Use LLM for deeper analysis
        llm_issues = await self._llm_logic_check(structure)
        issues.extend(llm_issues)
        
        return issues
```

---

### 5. Output Format

```json
{
  "decision_id": "uuid",
  "analyzed_at": "2024-01-15T10:30:00Z",
  
  "structure": {
    "hypothesis": "Increase marketing budget by 20%",
    "arguments": [
      {"content": "ROI is positive", "strength": "strong"},
      {"content": "Competitors increased spend", "strength": "moderate"}
    ],
    "counterarguments": [
      {"content": "Market saturation risk", "strength": "moderate"}
    ],
    "assumptions": [
      {"content": "Market conditions stable", "verified": false, "risk": "high"}
    ]
  },
  
  "strong_points": [
    "Clear hypothesis with measurable outcome",
    "Multiple supporting arguments"
  ],
  
  "weak_points": [
    {"type": "unverified_assumption", "severity": "high", 
     "description": "Market stability not verified"}
  ],
  
  "risks": [
    {"type": "assumption_failure", "impact": "high", 
     "mitigation": "Validate market research"}
  ],
  
  "overall_score": 0.72,
  "recommendation": "Consider before proceeding"
}
```

---

## ✅ Критерии завершения

- [x] Структура решения формализована
- [x] Пайплайн описан
- [x] Типовые риски каталогизированы
- [x] Выходной формат готов для UI

---

## 📎 Связанные документы

- [TASK 3.1 — CAL Architecture](./TASK_3.1_CAL_Architecture.md)
- [TASK 5.2 — UI Wireframes](../phase-5/TASK_5.2_UI_Wireframes.md)

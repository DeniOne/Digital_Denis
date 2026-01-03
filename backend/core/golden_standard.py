"""
Digital Den — Golden Standard Loader
═══════════════════════════════════════════════════════════════════════════

Loads and parses the Golden Standard Denis document.

The Golden Standard defines:
- What constitutes quality thinking
- Which patterns indicate development
- Which deviations require attention (not evaluation)

Based on: docs/golden_standard_denis.md
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class GoldenPattern:
    """An ideal pattern of thinking/behavior."""
    name: str
    description: str
    indicators: List[str] = field(default_factory=list)


@dataclass
class DeviationPattern:
    """A deviation pattern (signal, not error)."""
    name: str
    description: str
    signs: List[str] = field(default_factory=list)
    status: str = "observation"  # observation, neutral, stabilization_signal


@dataclass
class GoldenStandard:
    """Parsed Golden Standard Denis configuration."""
    
    # Core principles
    principles: Dict[str, str] = field(default_factory=dict)
    
    # Ideal patterns (what constitutes growth)
    ideal_patterns: List[GoldenPattern] = field(default_factory=list)
    
    # Deviation patterns (signals, not problems)
    deviations: List[DeviationPattern] = field(default_factory=list)
    
    # Key formula
    key_formula: List[str] = field(default_factory=list)
    
    # AI behavior constraints
    ai_obligations: List[str] = field(default_factory=list)
    ai_forbidden: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Golden Standard Loader
# ═══════════════════════════════════════════════════════════════════════════

class GoldenStandardLoader:
    """
    Loads and parses the Golden Standard Denis document.
    
    The document is a living document and can be updated.
    """
    
    def __init__(self, docs_path: Optional[str] = None):
        if docs_path:
            self.docs_path = Path(docs_path)
        else:
            # Default: look for docs/ relative to backend/
            backend_dir = Path(__file__).parent.parent
            self.docs_path = backend_dir.parent / "docs"
        
        self.golden_standard_file = self.docs_path / "golden_standard_denis.md"
        self._cached_standard: Optional[GoldenStandard] = None
        self._cache_time: float = 0
    
    def load(self, force_reload: bool = False) -> GoldenStandard:
        """
        Load and parse the Golden Standard document.
        
        Uses caching to avoid re-parsing on every call.
        """
        if not force_reload and self._cached_standard:
            # Check if file was modified
            if self.golden_standard_file.exists():
                mtime = self.golden_standard_file.stat().st_mtime
                if mtime <= self._cache_time:
                    return self._cached_standard
        
        if not self.golden_standard_file.exists():
            logger.warning(
                "golden_standard_not_found",
                path=str(self.golden_standard_file),
            )
            return self._get_default_standard()
        
        try:
            content = self.golden_standard_file.read_text(encoding="utf-8")
            standard = self._parse_markdown(content)
            
            self._cached_standard = standard
            self._cache_time = self.golden_standard_file.stat().st_mtime
            
            logger.info(
                "golden_standard_loaded",
                patterns=len(standard.ideal_patterns),
                deviations=len(standard.deviations),
            )
            
            return standard
            
        except Exception as e:
            logger.error(
                "golden_standard_parse_error",
                error=str(e),
            )
            return self._get_default_standard()
    
    def _parse_markdown(self, content: str) -> GoldenStandard:
        """Parse the markdown content into structured data."""
        standard = GoldenStandard()
        
        # Parse principles
        principles_match = re.search(
            r"## 2\. ПРИНЦИПЫ СТАНДАРТА(.*?)(?=## 3\.|$)",
            content, re.DOTALL
        )
        if principles_match:
            principles_text = principles_match.group(1)
            
            # Extract each principle
            principle_blocks = re.findall(
                r"### ([\d.]+) ([^\n]+)\n(.*?)(?=### |\Z)",
                principles_text, re.DOTALL
            )
            for _, name, description in principle_blocks:
                # Clean up and store
                clean_desc = self._clean_text(description)
                standard.principles[name] = clean_desc
        
        # Parse ideal patterns
        patterns_match = re.search(
            r"## 3\. ЭТАЛОННЫЕ ПАТТЕРНЫ(.*?)(?=## 4\.|$)",
            content, re.DOTALL
        )
        if patterns_match:
            patterns_text = patterns_match.group(1)
            
            pattern_blocks = re.findall(
                r"### [\d.]+ ([^\n]+)\n(.*?)(?=### |\Z)",
                patterns_text, re.DOTALL
            )
            for name, description in pattern_blocks:
                indicators = self._extract_list_items(description)
                standard.ideal_patterns.append(GoldenPattern(
                    name=self._clean_text(name),
                    description=self._clean_text(description),
                    indicators=indicators,
                ))
        
        # Parse deviations
        deviations_match = re.search(
            r"## 4\. ПАТТЕРНЫ ОТКЛОНЕНИЙ(.*?)(?=## 5\.|$)",
            content, re.DOTALL
        )
        if deviations_match:
            deviations_text = deviations_match.group(1)
            
            deviation_blocks = re.findall(
                r"### [\d.]+ ([^\n]+)\n(.*?)(?=### |\Z)",
                deviations_text, re.DOTALL
            )
            for name, description in deviation_blocks:
                signs = self._extract_list_items(description)
                
                # Try to extract status
                status = "observation"
                if "нейтральный" in description.lower():
                    status = "neutral"
                elif "стабилизац" in description.lower():
                    status = "stabilization_signal"
                
                standard.deviations.append(DeviationPattern(
                    name=self._clean_text(name),
                    description=self._clean_text(description),
                    signs=signs,
                    status=status,
                ))
        
        # Parse AI behavior
        ai_match = re.search(
            r"## 5\. РОЛЬ ИИ(.*?)(?=## 6\.|$)",
            content, re.DOTALL
        )
        if ai_match:
            ai_text = ai_match.group(1)
            
            # Obligations
            if "ИИ обязан:" in ai_text:
                obligations_section = ai_text.split("ИИ обязан:")[1]
                obligations_section = obligations_section.split("ИИ запрещено:")[0] if "ИИ запрещено:" in obligations_section else obligations_section
                standard.ai_obligations = self._extract_list_items(obligations_section)
            
            # Forbidden
            if "ИИ запрещено:" in ai_text:
                forbidden_section = ai_text.split("ИИ запрещено:")[1]
                standard.ai_forbidden = self._extract_list_items(forbidden_section)
        
        # Parse key formula
        formula_match = re.search(
            r"## 8\. КЛЮЧЕВАЯ ФОРМУЛА(.*?)(?=## 9\.|$)",
            content, re.DOTALL
        )
        if formula_match:
            formula_text = formula_match.group(1)
            # Extract lines like "Осознанность > Скорость"
            formulas = re.findall(r"(\w+)\s*>\s*(\w+)", formula_text)
            standard.key_formula = [f"{a} > {b}" for a, b in formulas]
        
        return standard
    
    def _extract_list_items(self, text: str) -> List[str]:
        """Extract bullet points or numbered items from text."""
        items = []
        
        # Match "- item" or "• item"
        for match in re.finditer(r"[-•]\s*(.+?)(?=\n[-•]|\n\n|\Z)", text, re.DOTALL):
            item = self._clean_text(match.group(1))
            if item:
                items.append(item)
        
        return items
    
    def _clean_text(self, text: str) -> str:
        """Clean up markdown text."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove markdown formatting
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        # Trim
        return text.strip()
    
    def _get_default_standard(self) -> GoldenStandard:
        """Return default standard if file not found."""
        return GoldenStandard(
            principles={
                "Сравнение только с собой": "Единственная точка отсчёта: Денис сегодня ↔ Денис вчера",
                "Рост важнее скорости": "Развитие = осознанное усложнение + стабилизация",
                "Системность выше эмоций": "Решения зрелые только после структурирования",
            },
            ideal_patterns=[
                GoldenPattern(
                    name="Эталон ясности",
                    description="Формулировки короче и точнее",
                    indicators=["снижение противоречий", "вопросы ведут к модели"],
                ),
                GoldenPattern(
                    name="Эталон системности",
                    description="Мысли связываются, появляется иерархия",
                    indicators=["цель → подцель → действие"],
                ),
            ],
            key_formula=["Осознанность > Скорость", "Системность > Эмоция", "Динамика > Оценка"],
            ai_obligations=[
                "ориентироваться на стандарт",
                "подстраивать стиль под состояние",
                "отражать динамику без оценок",
            ],
            ai_forbidden=[
                "навязывать цели",
                "интерпретировать отклонения как неудачу",
                "подменять рефлексию мотивацией",
            ],
        )
    
    def get_ai_prompt_addition(self) -> str:
        """
        Get prompt addition based on Golden Standard.
        
        Used to remind AI of core principles.
        """
        standard = self.load()
        
        prompt = """
## 🏆 Золотой стандарт Дениса

### Ключевой принцип
Сравнение только с собой: пользователь(T) ↔ пользователь(T-1)

### Формула
"""
        for formula in standard.key_formula:
            prompt += f"- {formula}\n"
        
        prompt += """
### ИИ обязан
"""
        for obligation in standard.ai_obligations:
            prompt += f"✅ {obligation}\n"
        
        prompt += """
### ИИ запрещено
"""
        for forbidden in standard.ai_forbidden:
            prompt += f"❌ {forbidden}\n"
        
        return prompt


# ═══════════════════════════════════════════════════════════════════════════
# Global Instance
# ═══════════════════════════════════════════════════════════════════════════

golden_standard_loader = GoldenStandardLoader()


def get_golden_standard() -> GoldenStandard:
    """Get the current Golden Standard."""
    return golden_standard_loader.load()

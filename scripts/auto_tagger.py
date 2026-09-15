# scripts/auto_tagger.py
"""Automatic tagging system for listings based on title and metadata keywords."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TagResult:
    """Result of auto-tagging analysis."""
    tag_name: str
    icon: str
    display: str  # e.g. "✨ A급"
    matched_keyword: str


# 8 core tagging rules aligned with used-market-notifier
DEFAULT_TAG_RULES: list[dict[str, Any]] = [
    {
        "tag_name": "A급",
        "icon": "✨",
        "keywords": ["A급", "에이급", "상태좋음", "매우깨끗", "최상", "S급", "민트급"],
    },
    {
        "tag_name": "풀박스",
        "icon": "📦",
        "keywords": ["풀박스", "풀박", "미개봉", "새제품", "미사용", "원박스"],
    },
    {
        "tag_name": "급처",
        "icon": "🔥",
        "keywords": ["급처", "급매", "급급", "빨리", "오늘만", "처분"],
    },
    {
        "tag_name": "네고가능",
        "icon": "💬",
        "keywords": ["네고가능", "네고", "협의가능", "가격협의", "흥정", "절충가능"],
    },
    {
        "tag_name": "택포",
        "icon": "📮",
        "keywords": ["택포", "택배포함", "배송비포함", "무배", "택배비포함"],
    },
    {
        "tag_name": "직거래",
        "icon": "🤝",
        "keywords": ["직거래", "직거래만", "직거래전용", "직거래희망", "대면거래"],
    },
    {
        "tag_name": "정품",
        "icon": "✅",
        "keywords": ["정품", "정품확인", "구매영수증", "보증서", "국내정품"],
    },
    {
        "tag_name": "구성품포함",
        "icon": "🎁",
        "keywords": ["구성품", "풀구성", "박스포함", "악세사리포함", "케이스포함", "충전기포함"],
    },
]


class AutoTagger:
    """Analyzes listing titles/locations and attaches semantic tags with icons."""

    def __init__(self, rules: list[dict[str, Any]] | None = None):
        self.rules = rules or DEFAULT_TAG_RULES

    def analyze_detailed(self, text: str) -> list[TagResult]:
        if not text:
            return []
        text_lower = text.lower()
        results: list[TagResult] = []
        for rule in self.rules:
            tag_name = rule["tag_name"]
            icon = rule.get("icon", "🏷️")
            for kw in rule.get("keywords", []):
                if kw.lower() in text_lower:
                    results.append(
                        TagResult(
                            tag_name=tag_name,
                            icon=icon,
                            display=f"{icon} {tag_name}",
                            matched_keyword=kw,
                        )
                    )
                    break
        return results

    def analyze(self, text: str) -> list[str]:
        """Returns formatted display strings like ['✨ A급', '📦 풀박스']."""
        return [res.display for res in self.analyze_detailed(text)]

    def analyze_names(self, text: str) -> list[str]:
        """Returns bare tag names like ['A급', '풀박스']."""
        return [res.tag_name for res in self.analyze_detailed(text)]


_default_tagger = AutoTagger()


def auto_tag(text: str) -> list[str]:
    """Convenience function returning formatted tag display strings."""
    return _default_tagger.analyze(text)


def auto_tag_names(text: str) -> list[str]:
    """Convenience function returning bare tag names."""
    return _default_tagger.analyze_names(text)

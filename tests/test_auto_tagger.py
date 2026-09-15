from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from auto_tagger import auto_tag, auto_tag_names, AutoTagger


def test_auto_tag_basic():
    title = "아이폰 15 프로 128G A급 풀박스 급처 네고가능"
    tags = auto_tag(title)
    names = auto_tag_names(title)
    
    assert "✨ A급" in tags
    assert "📦 풀박스" in tags
    assert "🔥 급처" in tags
    assert "💬 네고가능" in tags
    
    assert "A급" in names
    assert "풀박스" in names
    assert "급처" in names
    assert "네고가능" in names


def test_auto_tag_all_categories():
    tagger = AutoTagger()
    samples = {
        "A급": "상태좋음 매우깨끗",
        "풀박스": "미개봉 새제품",
        "급처": "오늘만 급매 처분",
        "네고가능": "가격협의 흥정 가능",
        "택포": "택배포함 무배",
        "직거래": "직거래만 희망 대면거래",
        "정품": "구매영수증 보증서 포함 정품",
        "구성품포함": "충전기포함 케이스포함",
    }
    for expected_name, sample_text in samples.items():
        matched = tagger.analyze_names(sample_text)
        assert expected_name in matched, f"Expected {expected_name} in {matched} for '{sample_text}'"


def test_auto_tag_empty():
    assert auto_tag("") == []
    assert auto_tag(None) == []

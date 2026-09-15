from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from message_templates import MessageTemplateManager, get_template_manager, render_seller_message


def test_template_list():
    mgr = get_template_manager()
    templates = mgr.list_templates()
    assert len(templates) >= 7
    ids = [t.id for t in templates]
    assert "default" in ids
    assert "nego" in ids
    assert "direct" in ids
    assert "danggeun" in ids
    assert "bunjang" in ids


def test_template_render_basic():
    msg = render_seller_message("default", {
        "title": "맥북 에어 M2",
        "price": "100만원",
    })
    assert "맥북 에어 M2" in msg
    assert "아직 판매중인가요?" in msg


def test_template_render_nego():
    msg = render_seller_message("nego", {
        "title": "아이폰 15 프로",
        "price": "110만원",
    })
    assert "아이폰 15 프로" in msg
    assert "110만원" in msg
    assert "네고 가능할까요?" in msg


def test_template_render_location_direct():
    msg = render_seller_message("direct", {
        "title": "플스 5",
        "location": "잠실역",
    })
    assert "플스 5" in msg
    assert "잠실역" in msg
    assert "직거래 가능하신가요?" in msg


def test_platform_specific_filter():
    mgr = get_template_manager()
    danggeun_templates = mgr.list_templates("danggeun")
    ids = [t.id for t in danggeun_templates]
    assert "danggeun" in ids
    assert "bunjang" not in ids

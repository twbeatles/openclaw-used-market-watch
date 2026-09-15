# scripts/message_templates.py
"""Message template system for quick seller communication, adapted for OpenClaw."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping, Sequence


@dataclass
class MessageTemplate:
    """Template for seller communication with variable substitution."""
    id: str
    name: str
    content: str
    market: str = "all"  # "all", "danggeun", "bunjang", "joonggonara"
    description: str = ""

    def render(self, context: Mapping[str, object]) -> str:
        """Render template replacing {title}, {price}, {location}, {seller}, {target_price}, {market}."""
        result = self.content
        for key, value in context.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value) if value is not None else "")
        # Remove any leftover unknown placeholders
        result = re.sub(r"\{[^}]+\}", "", result)
        # Collapse multiple blank lines
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()


DEFAULT_TEMPLATES: list[MessageTemplate] = [
    MessageTemplate(
        id="default",
        name="기본 문의",
        content="안녕하세요! {title} 상품 문의드립니다.\n아직 판매중인가요?",
        market="all",
        description="판매 여부를 묻는 가장 기본적이고 정중한 문의",
    ),
    MessageTemplate(
        id="nego",
        name="가격 네고 문의",
        content="안녕하세요! {title} 보고 연락드립니다.\n현재 {price}에 판매중이신데, 혹시 조금 네고 가능할까요? 빠른 쿨거래 약속드립니다!",
        market="all",
        description="정중하게 가격 조율(네고)을 제안하는 문의",
    ),
    MessageTemplate(
        id="direct",
        name="직거래 문의",
        content="안녕하세요! {title} 구매 희망합니다.\n{location} 부근에서 직거래 가능하신가요? 편하신 시간 말씀해주시면 맞추겠습니다.",
        market="all",
        description="직거래 장소 및 일정을 조율하기 위한 문의",
    ),
    MessageTemplate(
        id="condition",
        name="상태 및 사용기간 문의",
        content="안녕하세요! {title} 관심 있어 문의드립니다.\n상세한 외관 상태나 찍힘, 사용 기간 및 배터리 효율이 어떻게 되나요?",
        market="all",
        description="외관 상태와 사용 내역을 상세히 묻는 문의",
    ),
    MessageTemplate(
        id="package",
        name="구성품 확인 문의",
        content="안녕하세요! {title} 문의드립니다.\n본품 외에 박스, 충전기 등 기본 구성품이 모두 포함되어 있는지 궁금합니다.",
        market="all",
        description="풀박스/액세서리 구성품 포함 여부를 확인하는 문의",
    ),
    MessageTemplate(
        id="danggeun",
        name="당근마켓 이웃 문의",
        content="안녕하세요, {location} 이웃 주민입니다! 😊\n올려주신 {title} 아직 거래 가능한가요? 가까우면 바로 찾아뵐 수 있습니다.",
        market="danggeun",
        description="당근마켓 특유의 친근한 이웃 인사말 템플릿",
    ),
    MessageTemplate(
        id="bunjang",
        name="번개장터 빠른거래 문의",
        content="⚡ 안녕하세요!\n{title} 바로 번개페이 또는 안전결제로 구매 가능할까요?",
        market="bunjang",
        description="번개장터 번개페이/즉시구매 전용 문의",
    ),
]


class MessageTemplateManager:
    """Manages and renders communication templates."""

    def __init__(self, templates: Sequence[MessageTemplate] | None = None):
        self.templates = list(templates) if templates else DEFAULT_TEMPLATES.copy()

    def list_templates(self, market: str | None = None) -> list[MessageTemplate]:
        if not market or market == "all":
            return self.templates
        return [t for t in self.templates if t.market in ("all", market)]

    def get(self, template_id_or_name: str) -> MessageTemplate | None:
        target = template_id_or_name.strip().lower()
        for t in self.templates:
            if t.id.lower() == target or t.name.lower() == target:
                return t
        return None

    def render(self, template_id_or_name: str, context: Mapping[str, object]) -> str:
        tpl = self.get(template_id_or_name)
        if not tpl:
            tpl = self.get("default") or self.templates[0]
        return tpl.render(context)


_default_manager = MessageTemplateManager()


def get_template_manager() -> MessageTemplateManager:
    return _default_manager


def render_seller_message(template_id_or_name: str, context: Mapping[str, object]) -> str:
    """Convenience function to render a seller message."""
    return _default_manager.render(template_id_or_name, context)

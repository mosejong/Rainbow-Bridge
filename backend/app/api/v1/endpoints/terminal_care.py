from fastapi import APIRouter
from ai.llm.terminal_care import get_terminal_care_info

router = APIRouter()


@router.get("/terminal-care", summary="시한부 케어 안내")
def terminal_care():
    """시한부 판정 반려동물 보호자를 위한 고정 케어 안내를 반환합니다."""
    return get_terminal_care_info()

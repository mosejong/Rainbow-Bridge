"""레인보우 브릿지 HHHHHMM 삶의 질(QoL) 척도 모듈 (ai/hhhhhmm).

1단계(아플 때) 보호자에게 반려동물 삶의 질 참고 지표를 제공합니다.

⚠️ 보조 지표일 뿐 — 안락사 등 결정은 AI가 내리지 않으며, 결과엔 항상
수의사 상담 안내를 답니다. 윤리 경계는 CLAUDE.md 참고.
선택(가산점) 기능 — 팀+강사 합의 전까지 백엔드·프론트에 배선하지 않습니다.
"""

from .qol import QOL_CRITERIA, score_qol

__all__ = ["QOL_CRITERIA", "score_qol"]

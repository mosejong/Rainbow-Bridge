"""레인보우 브릿지 평가 패키지 (ai/evaluation) — MVP ⑧ 평가 리포트.

서비스 사용 데이터를 집계해 보호자/팀에게 보여줄 리포트를 만듭니다.
(모델 성능 후기는 여기 아님 → ../llm/MODEL_NOTES.md)
"""

from .logs import LLMLog, save_log
from .report import build_report

__all__ = ["LLMLog", "save_log", "build_report"]

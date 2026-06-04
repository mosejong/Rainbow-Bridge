"""레인보우 브릿지 TTS 패키지 (ai/tts) — MVP ④ 음성 톤 선택 + 낭독.

추모 메시지(③)를 보호자에게 음성으로 들려줍니다.

⚠️ 윤리 경계 (../CLAUDE.md, ../tts/CLAUDE.md §5):
   음성도 **보호자 대상 위로 낭독**입니다. 반려동물 목소리 흉내 ❌.
"""

from .tts import TtsTone, synthesize

__all__ = ["TtsTone", "synthesize"]

"""ai/ 패키지를 백엔드에서 직접 import할 수 있도록 프로젝트 루트를 sys.path에 추가.

나중에 AI 추론 서버 분리 시 이 모듈만 수정하고 HTTP 호출로 교체 (선행결정 B).
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

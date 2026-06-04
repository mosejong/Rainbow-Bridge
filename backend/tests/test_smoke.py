"""백엔드 스모크 테스트 — import 가능 여부만 확인합니다."""


def test_app_importable():
    from app.main import app

    assert app is not None


def test_schemas_importable():
    from app.schemas.emotion import EmotionCreate, EmotionResponse
    from app.schemas.mission import MissionResponse
    from app.schemas.pet import PetCreate, PetResponse

    assert all(
        [PetCreate, PetResponse, EmotionCreate, EmotionResponse, MissionResponse]
    )

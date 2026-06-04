import os
from datetime import datetime, timezone

from bson import ObjectId
from openai import APIError, OpenAI

from app.db.mongodb import mongodb
from app.schemas.message import MessageCreate, MessageResponse

CRISIS_HOTLINE = "1393"

_CRISIS_NOTICE = (
    f"많이 힘드시군요. 혼자 감당하기 어려울 때는 "
    f"자살예방상담전화 {CRISIS_HOTLINE}로 연락해 주세요. 24시간 운영합니다."
)

# 위기 키워드 (반소람님 L2+ 기준)
_CRISIS_KEYWORDS = ["죽고싶", "따라가고싶", "없어지고싶", "살기싫", "유서", "뛰어내리"]

_TONE_GUIDE = {
    "warm": "따뜻하고 다정하게, 보호자의 슬픔을 부드럽게 감싸 안듯이.",
    "calm": "담담하고 차분하게, 과장 없이 곁에 머무르듯이.",
    "hopeful": "잔잔한 희망을 담아, 일상으로 천천히 돌아오도록 북돋우듯이.",
}

_SYSTEM_PROMPT = """\
당신은 반려동물을 떠나보낸 보호자를 위로하는 따뜻한 글벗입니다.
보호자가 들려준 기억을 바탕으로, 짧고 진심 어린 추모의 글을 씁니다.

[반드시 지킬 것]
- 글은 언제나 '보호자'를 향합니다.
- 3~4문장, 한국어. 군더더기 없이 담백하게.

[절대 금지]
- 반려동물을 다시 살아나게 하거나, 돌아온다고 말하지 마세요.
- 반려동물이 '나'라고 말하는 1인칭 화법 금지.
- 종교적 단정이나 근거 없는 위로를 강요하지 마세요.
"""


def _collection():
    return mongodb.db["messages"]


def _is_crisis(note: str | None) -> bool:
    note_str = note or ""
    return any(kw in note_str for kw in _CRISIS_KEYWORDS)


def _build_prompt(pet: dict, tone: str, score: int, note: str) -> str:
    memories = pet.get("memories") or []
    memories_block = ""
    if memories:
        bullets = "\n".join(f"  - {m}" for m in memories)
        memories_block = f"- 함께한 추억:\n{bullets}\n"

    tone_guide = _TONE_GUIDE.get(tone, _TONE_GUIDE["warm"])
    return (
        f"[반려동물]\n"
        f"- 이름: {pet.get('name', '')}\n"
        f"- 종: {pet.get('species', '')}\n"
        f"- 함께한 기간: {pet.get('period', '')}\n"
        f"{memories_block}"
        f"[보호자 감정]\n"
        f"- 감정 점수: {score}/10 (1=많이 힘듦 · 10=평온)\n"
        f"- 메모: {note or '(없음)'}\n\n"
        f"[요청] 위 기억을 바탕으로 {tone_guide} 3~4문장으로 써 주세요."
    )


def _llm_generate(prompt: str) -> str | None:
    """Gemini OpenAI 호환 엔드포인트 호출. 키 없으면 None 반환."""
    api_key = os.getenv("LLM_API_KEY", "")
    if not api_key:
        return None

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv(
            "LLM_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        ),
    )
    try:
        resp = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "512")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none") or None,
        )
        return (resp.choices[0].message.content or "").strip()
    except APIError:
        return None


_FALLBACK = {
    "warm": "함께한 시간들이 당신 마음 깊은 곳에서 언제나 따뜻하게 빛나고 있을 거예요. 그 소중한 기억들이 당신 곁에 늘 있습니다.",
    "calm": "소중한 인연은 시간이 지나도 마음속에 조용히 머뭅니다. 함께한 모든 순간이 당신의 일부로 남아 있어요.",
    "hopeful": "사랑했던 기억은 사라지지 않아요. 그 기억이 당신이 다시 일어설 수 있는 힘이 되어줄 거예요.",
}


async def create_message(data: MessageCreate) -> MessageResponse:
    if _is_crisis(data.note):
        doc = {
            "pet_id": data.pet_id,
            "content": _CRISIS_NOTICE,
            "tone": data.tone,
            "source": "safety",
            "risk_level": 2,
            "created_at": datetime.now(timezone.utc),
        }
        result = await _collection().insert_one(doc)
        doc["id"] = str(result.inserted_id)
        response = MessageResponse(**doc)
        response.crisis_message = _CRISIS_NOTICE
        return response

    # 반려동물 정보 조회
    pet_doc = await mongodb.db["pets"].find_one({"_id": ObjectId(data.pet_id)})
    pet = pet_doc or {}

    tone = data.tone if data.tone in _TONE_GUIDE else "warm"
    prompt = _build_prompt(pet, tone, data.emotion_score or 5, data.note or "")

    content = _llm_generate(prompt)
    source = "local"
    if content is None:
        content = _FALLBACK[tone]
        source = "fallback"

    doc = {
        "pet_id": data.pet_id,
        "content": content,
        "tone": tone,
        "source": source,
        "risk_level": 0,
        "created_at": datetime.now(timezone.utc),
    }
    result = await _collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)

    await mongodb.db["pets"].update_one(
        {"_id": ObjectId(data.pet_id)},
        {"$push": {"timeline_refs": {"type": "message", "ref_id": doc["id"]}}},
    )
    return MessageResponse(**doc)

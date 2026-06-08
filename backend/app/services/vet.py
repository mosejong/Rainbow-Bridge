from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vet import Vet
from app.schemas.vet import VetRegisterRequest, VetResponse, VetTokenResponse
from app.services.auth import _create_token, _hash_password, _verify_password


async def register_vet(db: AsyncSession, data: VetRegisterRequest) -> VetResponse:
    existing = await db.scalar(select(Vet).where(Vet.email == data.email))
    if existing:
        raise ValueError("이미 사용 중인 이메일입니다.")

    existing_license = await db.scalar(
        select(Vet).where(Vet.license_number == data.license_number)
    )
    if existing_license:
        raise ValueError("이미 등록된 면허번호입니다.")

    vet = Vet(
        email=data.email,
        password_hash=_hash_password(data.password),
        name=data.name,
        hospital_name=data.hospital_name,
        license_number=data.license_number,
    )
    db.add(vet)
    await db.commit()
    await db.refresh(vet)
    return VetResponse.model_validate(vet)


async def login_vet(db: AsyncSession, email: str, password: str) -> VetTokenResponse:
    vet = await db.scalar(select(Vet).where(Vet.email == email))
    if not vet or not vet.is_active:
        raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다.")

    try:
        verified = _verify_password(password, vet.password_hash)
    except Exception:
        verified = False

    if not verified:
        raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다.")

    token = _create_token(vet.id, vet.email)
    return VetTokenResponse(access_token=token)

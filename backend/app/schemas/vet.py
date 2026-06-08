from pydantic import BaseModel, EmailStr, Field


class VetRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="이메일")
    password: str = Field(..., min_length=6, description="비밀번호 (6자 이상)")
    name: str = Field(..., min_length=1, max_length=50, description="수의사 이름")
    hospital_name: str = Field(..., min_length=1, max_length=100, description="병원명")
    license_number: str = Field(
        ..., min_length=1, max_length=50, description="면허번호"
    )


class VetLoginRequest(BaseModel):
    email: EmailStr
    password: str


class VetResponse(BaseModel):
    id: int
    email: str
    name: str
    hospital_name: str
    license_number: str
    is_verified: bool
    is_active: bool

    model_config = {"from_attributes": True}


class VetTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

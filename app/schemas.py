from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PlannerRequest(BaseModel):
    plan_type: str = Field(
        pattern="^(home|party|jewelry)$"
    )
    budget: int = Field(gt=0, le=100_000_000)
    currency: str = Field(default="INR", pattern="^INR$")
    occasion: str = Field(default="", max_length=120)
    style: str = Field(default="", max_length=120)
    people: int = Field(default=10, ge=1, le=10000)
    rooms: int = Field(default=1, ge=1, le=100)
    requirements: str = Field(default="", max_length=2000)


class PlanResponse(BaseModel):
    id: int
    plan_type: str
    title: str
    budget: int
    request_data: dict
    result: dict
    ai_provider: str
    created_at: str
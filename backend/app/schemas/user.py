import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.user import UserRole

class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    department: str | None = None
    is_active: bool
    created_at: datetime

class DepartmentUpdate(BaseModel):
    department: str | None = Field(default=None, max_length=120)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

from typing import List, Optional

from pydantic import BaseModel, EmailStr


class Email(BaseModel):
    email: List[EmailStr]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[EmailStr] = None

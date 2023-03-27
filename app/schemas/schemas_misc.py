from typing import List, Optional

from pydantic import BaseModel, EmailStr


class Email(BaseModel):
    email: List[EmailStr]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None

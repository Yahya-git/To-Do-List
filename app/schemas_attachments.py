from typing import Optional

from pydantic import BaseModel


class AttachmentBase(BaseModel):
    id: int
    file_attachment: Optional[bytes] = None


class AttachmentCreate(AttachmentBase):
    task_id: int


class Attachment(AttachmentBase):
    task_id: int

    class Config:
        orm_mode = True

from typing import Optional

from fastapi import UploadFile
from pydantic import BaseModel


class AttachmentBase(BaseModel):
    file_name: Optional[str] = None
    file_attachment: Optional[UploadFile] = None


class AttachmentCreate(AttachmentBase):
    task_id: int


class Attachment(AttachmentBase):
    id: int
    task_id: int

    class Config:
        orm_mode = True

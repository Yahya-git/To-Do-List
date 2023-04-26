from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, EmailStr
from pydantic.generics import GenericModel

M = TypeVar("M", bound=BaseModel)


class BaseGenericResponse(GenericModel):
    status: str


class UserSingleObject(GenericModel, Generic[M]):
    user: M

    class Config:
        orm_mode = True


class UserSingleResponse(BaseGenericResponse, Generic[M]):
    data: UserSingleObject[M]

    class Config:
        orm_mode = True


class TaskSingleObject(GenericModel, Generic[M]):
    task: M

    class Config:
        orm_mode = True


class TaskMultipleObjects(GenericModel, Generic[M]):
    tasks: List[M]

    class Config:
        orm_mode = True


class TaskSingleResponse(BaseGenericResponse, Generic[M]):
    data: TaskSingleObject[M]

    class Config:
        orm_mode = True


class TaskMultipleResponse(BaseGenericResponse, Generic[M]):
    data: TaskMultipleObjects[M]

    class Config:
        orm_mode = True


class ReportSingleObject(GenericModel, Generic[M]):
    report: M

    class Config:
        orm_mode = True


class ReportMultipleObjects(GenericModel, Generic[M]):
    reports: List[M]

    class Config:
        orm_mode = True


class ReportSingleResponse(BaseGenericResponse, Generic[M]):
    data: ReportSingleObject[M]

    class Config:
        orm_mode = True


class ReportMultipleResponse(BaseGenericResponse, Generic[M]):
    data: ReportMultipleObjects[M]

    class Config:
        orm_mode = True


class EmailList(BaseModel):
    email: List[EmailStr]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    id: Optional[int] = None

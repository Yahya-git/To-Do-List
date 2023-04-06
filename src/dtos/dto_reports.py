from pydantic import BaseModel


class CountReportResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    incomplete_tasks: int

    class Config:
        orm_mode = True

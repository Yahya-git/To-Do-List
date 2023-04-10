from datetime import date

from pydantic import BaseModel


class CountReportResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    incomplete_tasks: int

    class Config:
        orm_mode = True


class AverageReportResponse(BaseModel):
    average_tasks_completed_per_day: int

    class Config:
        orm_mode = True


class OverdueReportResponse(BaseModel):
    overdue_tasks: int

    class Config:
        orm_mode = True


class DateMaxReportResponse(BaseModel):
    date: date
    completed_tasks: int

    class Config:
        orm_mode = True


class DayTasksReportResponse(BaseModel):
    day_of_week: str
    created_tasks: int

    class Config:
        orm_mode = True

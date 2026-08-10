"""Analytics schemas."""

from datetime import date

from pydantic import BaseModel


class TimeSeriesPoint(BaseModel):
    date: date
    count: int


class NamedCount(BaseModel):
    name: str
    count: int


class AnalyticsOut(BaseModel):
    date_from: date
    date_to: date
    consultations_by_status: dict[str, int]
    consultations_per_day: list[TimeSeriesPoint]
    appointments_by_status: dict[str, int]
    new_patients_per_day: list[TimeSeriesPoint]
    ai_processing_outcomes: dict[str, int]
    consultations_by_doctor: list[NamedCount]
    consultations_by_department: list[NamedCount]
    reports_generated: int
    missed_appointment_rate: float

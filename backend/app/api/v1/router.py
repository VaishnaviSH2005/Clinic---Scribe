"""Aggregates all v1 routers (PRD Ch4.5 api/). Business routers (patients,
consultations, auth, etc.) are registered here as each module is implemented.
"""

from fastapi import APIRouter

from app.api.v1.ai import router as ai_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.appointments import router as appointments_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.consultations import router as consultations_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.departments import router as departments_router
from app.api.v1.doctors import router as doctors_router
from app.api.v1.health import router as health_router
from app.api.v1.hospitals import router as hospitals_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.patients import router as patients_router
from app.api.v1.receptionists import router as receptionists_router
from app.api.v1.reports import router as reports_router
from app.api.v1.search import router as search_router
from app.api.v1.settings import router as settings_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(hospitals_router)
api_router.include_router(departments_router)
api_router.include_router(doctors_router)
api_router.include_router(receptionists_router)
api_router.include_router(users_router)
api_router.include_router(patients_router)
api_router.include_router(appointments_router)
api_router.include_router(consultations_router)
api_router.include_router(ai_router)
api_router.include_router(reports_router)
api_router.include_router(notifications_router)
api_router.include_router(dashboard_router)
api_router.include_router(analytics_router)
api_router.include_router(settings_router)
api_router.include_router(search_router)
api_router.include_router(subscriptions_router)
api_router.include_router(audit_logs_router)

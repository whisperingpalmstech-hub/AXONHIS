from fastapi import APIRouter

from .messages.routes import router as message_router
from .channels.routes import router as channel_router
from .alerts.routes import router as alert_router
from .notifications.routes import router as notification_router
from .escalations.routes import router as escalation_router
from .patient_threads.routes import router as thread_router

communication_router = APIRouter(prefix="/communication")

communication_router.include_router(message_router)
communication_router.include_router(channel_router)
communication_router.include_router(alert_router)
communication_router.include_router(notification_router)
communication_router.include_router(escalation_router)
communication_router.include_router(thread_router)

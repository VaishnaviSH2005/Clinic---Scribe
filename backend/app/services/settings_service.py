"""User-scoped settings — notification preferences and application
preferences (PRD Ch15.9.3). Backed by the generic key-value `settings`
table already defined in the schema; nothing new to migrate.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SettingsScope
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings_schema import ApplicationPreferences, NotificationPreferences, UserSettingsOut

NOTIFICATION_PREFERENCES_KEY = "notification_preferences"
APPLICATION_PREFERENCES_KEY = "application_preferences"


async def get_user_settings(db: AsyncSession, *, user_id: uuid.UUID) -> UserSettingsOut:
    repo = SettingsRepository(db)
    notif_row = await repo.get(
        scope=SettingsScope.user, user_id=user_id, hospital_id=None, key=NOTIFICATION_PREFERENCES_KEY
    )
    app_row = await repo.get(
        scope=SettingsScope.user, user_id=user_id, hospital_id=None, key=APPLICATION_PREFERENCES_KEY
    )

    return UserSettingsOut(
        notification_preferences=NotificationPreferences(**(notif_row.value if notif_row else {})),
        application_preferences=ApplicationPreferences(**(app_row.value if app_row else {})),
    )


async def update_notification_preferences(
    db: AsyncSession, *, user_id: uuid.UUID, data: NotificationPreferences
) -> NotificationPreferences:
    await SettingsRepository(db).upsert(
        scope=SettingsScope.user,
        user_id=user_id,
        hospital_id=None,
        key=NOTIFICATION_PREFERENCES_KEY,
        value=data.model_dump(),
        updated_at=datetime.now(timezone.utc),
    )
    return data


async def update_application_preferences(
    db: AsyncSession, *, user_id: uuid.UUID, data: ApplicationPreferences
) -> ApplicationPreferences:
    await SettingsRepository(db).upsert(
        scope=SettingsScope.user,
        user_id=user_id,
        hospital_id=None,
        key=APPLICATION_PREFERENCES_KEY,
        value=data.model_dump(),
        updated_at=datetime.now(timezone.utc),
    )
    return data

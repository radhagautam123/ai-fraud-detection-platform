from datetime import datetime
from sqlalchemy import select

from src.common.database import async_session
from src.common.models import AuditLog, User


async def create_audit_log(
    user: User | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Create an audit log entry asynchronously."""
    entry = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=details,
        ip_address=ip_address,
        created_at=datetime.utcnow(),
    )
    async with async_session() as session:
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
    return entry

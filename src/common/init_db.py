import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import inspect, text
from src.common.database import init_db, engine, async_session
from src.common.models import Base, User
from src.backend.auth import hash_password


async def migrate():
    """Add columns that may not exist on existing tables (safe migration)."""
    async with engine.begin() as conn:
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))

        # Check alerts table for new columns
        alerts_columns = [c["name"] for c in inspector.get_columns("alerts")]

        migrations = [
            ("alerts", "investigation_status", "VARCHAR(20) DEFAULT 'NEW'"),
            ("alerts", "assigned_to", "INTEGER REFERENCES users(id)"),
            ("alerts", "case_notes", "TEXT"),
            ("alerts", "resolution", "VARCHAR(50)"),
            ("alerts", "resolved_at", "TIMESTAMP"),
        ]

        for table, column, col_type in migrations:
            if column not in alerts_columns:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                print(f"  + Added column {table}.{column}")

        # Check audit_logs table (new model — created by metadata)
        tables = inspector.get_table_names()
        if "audit_logs" not in tables:
            print("  - audit_logs table will be created by metadata")

    print("Migrations complete.")


async def seed_admin():
    """Create default admin user if not exists."""
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                email="admin@fraud-detection.local",
                hashed_password=hash_password("admin123"),
                role="ADMIN",
            )
            session.add(admin)
            await session.commit()
            print("  + Created admin user (admin / admin123)")
        else:
            print("  - Admin user already exists")


async def main():
    print("Initializing database tables...")
    await init_db()

    print("Running migrations...")
    await migrate()

    print("Seeding default data...")
    await seed_admin()

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

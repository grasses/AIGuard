"""AI Firewall — Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import init_db, close_db
from app.logging_config import setup_logging

# Import all API routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.assets import router as assets_router
from app.api.guardrails import router as guardrails_router
from app.api.traffic import router as traffic_router
from app.api.logs import router as logs_router
from app.api.dashboard import router as dashboard_router
from app.api.alerts import router as alerts_router
from app.api.billing import router as billing_router
from app.api.settings import router as settings_router
from app.gateway.proxy import router as proxy_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    setup_logging()
    await init_db()
    # Create default super admin if not exists
    await seed_default_admin()
    yield
    await close_db()


async def seed_default_admin():
    """Create default super admin account if none exists."""
    from app.database import async_session_factory
    from app.models import User, UserRole, UserStatus
    from app.utils import hash_password
    from sqlalchemy import select

    async with async_session_factory() as db:
        result = await db.execute(
            select(User).where(User.role == UserRole.super_admin)
        )
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                email="admin@aifirewall.local",
                hashed_password=hash_password("Admin@123"),
                role=UserRole.super_admin,
                status=UserStatus.active,
                balance=999999,
            )
            db.add(admin)
            await db.commit()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": f"内部服务器错误: {str(exc)}"},
    )


# ─── Register Routers ───

# Auth (no middleware)
app.include_router(auth_router)

# User/Admin API (JWT middleware applied in routes)
app.include_router(users_router)
app.include_router(assets_router)
app.include_router(guardrails_router)
app.include_router(traffic_router)
app.include_router(logs_router)
app.include_router(dashboard_router)
app.include_router(alerts_router)
app.include_router(billing_router)
app.include_router(settings_router)

# Proxy gateway (API Key middleware applied in route)
app.include_router(proxy_router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)

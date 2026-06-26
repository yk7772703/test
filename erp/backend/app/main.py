import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine, get_db
from app.routers import auth, finance, hr, crm, compliance
from app.services.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    # Start background scheduler
    start_scheduler(get_db)
    logger.info("Scheduler started")

    yield

    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Enterprise ERP with Compliance — US, UK, Canada. "
        "Features: Finance, HR/Payroll, CRM, Sanctions Screening, KYC/AML, "
        "Regulatory Updates (OFAC, UKSL, UN, EU, SEMA)."
    ),
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api")
app.include_router(finance.router, prefix="/api")
app.include_router(hr.router, prefix="/api")
app.include_router(crm.router, prefix="/api")
app.include_router(compliance.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/api")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "jurisdictions": settings.SUPPORTED_JURISDICTIONS,
        "docs": "/api/docs",
    }

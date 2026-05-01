from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, NoResultFound
import src.models  # noqa: F401 - ensures all models are registered with Base
from src.db import Base, engine
from src.routers import auth, batches, sessions, attendance, institutions, programme, monitoring

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkillBridge API", version="1.0.0")

app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(institutions.router)
app.include_router(programme.router)
app.include_router(monitoring.router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "Database integrity error — possible duplicate or invalid reference"},
    )


@app.get("/health")
def health():
    return {"status": "ok"}

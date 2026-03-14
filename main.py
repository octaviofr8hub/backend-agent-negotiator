"""
Backend Agent Negotiator — FastAPI entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from model.config import settings
from routes.negotiation import router as negotiation_router
from routes.negotiations import router as negotiations_router
from routes.transcript import router as transcript_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Backend Agent Negotiator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(negotiation_router)
app.include_router(negotiations_router)
app.include_router(transcript_router)


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok"}

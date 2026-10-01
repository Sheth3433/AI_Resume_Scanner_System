from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.resume import router as resume_router
from app.api.routes.jobs import router as jobs_router
from app.config import CORS_ORIGINS
from app.models.database import Base, engine
from app.models.user import UserRecord
from sqlalchemy import inspect, text


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    columns = {column["name"] for column in inspect(engine).get_columns("analyses")}
    if "owner_user_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE analyses ADD COLUMN owner_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_analyses_owner_user_id ON analyses (owner_user_id)"))
    yield


app = FastAPI(title="AI Resume Scanner & Job Matcher", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(resume_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")

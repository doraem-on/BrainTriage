import os

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from app.database import engine, init_db
from app.models import Patient
from app.routers import patients, queue, meta, report, locations, assistant, auth
from app.ml.train import train_all, MODEL_DIR

load_dotenv()

# When the frontend has been built into the backend's own container (see
# Dockerfile), it lands here; FastAPI serves it directly so the whole app is
# one deployable service with no cross-origin URL to configure. In local dev
# this directory doesn't exist — the frontend runs on its own via `npm run
# dev` instead — so everything below is skipped gracefully.
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend_dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if not os.path.exists(os.path.join(MODEL_DIR, "metrics.json")):
        train_all()
    with Session(engine) as session:
        if session.exec(select(Patient)).first() is None:
            import seed_demo
            seed_demo.main()
    yield


app = FastAPI(title="BrainTriage API", lifespan=lifespan)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(queue.router)
app.include_router(meta.router)
app.include_router(report.router)
app.include_router(locations.router)
app.include_router(assistant.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

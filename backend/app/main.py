import os

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import patients, queue, meta, report
from app.ml.train import train_all, MODEL_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if not os.path.exists(os.path.join(MODEL_DIR, "metrics.json")):
        train_all()
    yield


app = FastAPI(title="BrainTriage API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router)
app.include_router(queue.router)
app.include_router(meta.router)
app.include_router(report.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

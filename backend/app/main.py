from fastapi import FastAPI

from app.api.hospital_router import router
from app.api.ai_router import router as ai_router

app = FastAPI()

app.include_router(router)
app.include_router(ai_router)

@app.get("/")
def root():
    return {"message": "DataPulse API"}

@app.get("/health")
def healt():
    return {"status": "ok"}


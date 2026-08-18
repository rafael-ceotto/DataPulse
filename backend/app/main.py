from fastapi import FastAPI

from app.api.hospital_router import router

app = FastAPI()

app.include_router(router)

@app.get("/")
def root():
    return {"message": "DataPulse API"}

@app.get("/health")
def healt():
    return {"status": "ok"}
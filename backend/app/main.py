from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Helllo World!"}

@app.get("/health")
def healt():
    return {"status": "ok"}
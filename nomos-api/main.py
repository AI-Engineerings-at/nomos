"""NomOS Fleet API."""
from fastapi import FastAPI

app = FastAPI(title="NomOS API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "nomos-api", "version": "0.1.0"}

@app.get("/api/fleet")
def fleet():
    return {"agents": [], "total": 0}

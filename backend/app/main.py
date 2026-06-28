from fastapi import FastAPI

from app.routers import coordinator, crisis

app = FastAPI(title="Vigil", version="0.1.0")

app.include_router(crisis.router)
app.include_router(coordinator.router)

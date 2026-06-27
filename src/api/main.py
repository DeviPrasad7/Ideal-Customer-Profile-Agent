from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import config, prospects, hitl, triggers

app = FastAPI(title="ICP Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router)
app.include_router(prospects.router)
app.include_router(hitl.router)
app.include_router(triggers.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

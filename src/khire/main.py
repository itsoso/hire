from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from khire.routers.analyze import router as analyze_router
from khire.routers.developer import router as developer_router
from khire.routers.search import router as search_router

app = FastAPI(title="KHire", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)
app.include_router(search_router)
app.include_router(developer_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

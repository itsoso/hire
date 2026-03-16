from fastapi import FastAPI

from khire.routers.analyze import router as analyze_router

app = FastAPI(title="KHire", version="0.1.0")
app.include_router(analyze_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

from fastapi import FastAPI, BackgroundTasks
from src.config import settings
from src.db.session import init_db
from src.gateway.routes import router as gateway_router
from src.intelligence.insights import insight_layer
from loguru import logger

app = FastAPI(title=settings.app_name, debug=settings.debug)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing Database...")
    init_db()

# Include the Gateway routes
app.include_router(gateway_router)

@app.get("/")
async def root():
    return {"message": "LLM Router Gateway is running", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/system/analyze")
async def trigger_analysis(background_tasks: BackgroundTasks):
    """Trigger system analysis and insight generation."""
    background_tasks.add_task(insight_layer.generate_system_insights)
    return {"message": "System analysis triggered"}

@app.get("/system/insights")
async def get_insights():
    return {"insights": await insight_layer.get_latest_insights()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)

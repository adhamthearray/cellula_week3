from fastapi import FastAPI

from routers.chat import router
from routers.data_analysis import router as data_analysis_router

app = FastAPI(title="AI Code Assistant", version="1.0.0")
app.include_router(router)
app.include_router(data_analysis_router)

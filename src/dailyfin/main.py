from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dailyfin.frontend.frontend_routes import router as frontend_router
from dailyfin.api.news_api import router as news_router
import pathlib

app = FastAPI()

# 路徑設定
BASE_DIR = pathlib.Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "frontend" / "static"

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 掛載路由
app.include_router(frontend_router)             
app.include_router(news_router)
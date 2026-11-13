from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.handlers import register_exception_handlers
from app.common.response import SuccessResponse, success_response
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="App Backend",
    description="FastAPI backend (vibe-harness template)",
    version="0.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 예외 핸들러 (envelope 강제)
register_exception_handlers(app)

# 도메인 라우터 등록 — 새 도메인을 만들면 여기에 app.include_router(...) 추가


@app.get("/api/health")
async def health_check() -> SuccessResponse[dict]:
    """헬스 체크"""
    return success_response({"status": "ok"})


@app.get("/")
async def root() -> SuccessResponse[dict]:
    """루트 엔드포인트"""
    return success_response({"message": "App Backend API"})

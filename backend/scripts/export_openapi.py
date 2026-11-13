"""FastAPI 앱의 OpenAPI 스펙을 frontend/public/openapi.json으로 내보낸다"""

import json
from pathlib import Path

from app.main import app

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "frontend" / "public" / "openapi.json"


def export_openapi() -> None:
    """구현 코드 기준 OpenAPI 스펙을 생성해 프론트 정적 경로에 저장"""
    spec = app.openapi()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK - {len(spec.get('paths', {}))} paths -> {OUTPUT_PATH}")


if __name__ == "__main__":
    export_openapi()

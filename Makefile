# 비개발자는 이 파일을 직접 쓸 필요가 없다 — Claude가 하네스 안에서 호출한다.
SHELL := /bin/bash
BACKEND := backend
FRONTEND := frontend
ENV_FILE ?= $(BACKEND)/.env

.PHONY: doctor setup db db-port dev dev-backend dev-frontend check check-backend check-frontend e2e gc worktree-setup

doctor: ## 필수 도구 설치 여부 확인
	@bash scripts/doctor.sh

setup: doctor ## 최초 1회: env 생성, DB 기동, 의존성 설치, 마이그레이션
	git config core.hooksPath .githooks  # 커밋 직전 민감 파일·비밀값 검사 (scripts/check_secrets.py)
	@git show-ref -q --verify refs/heads/main || git branch main $$(git rev-parse -q --verify origin/main >/dev/null && echo origin/main || echo HEAD)  # 브랜치: main(배포) · dev(개발 기준) — 작업 브랜치는 dev 에서 판다
	@git show-ref -q --verify refs/heads/dev || git branch dev $$(git rev-parse -q --verify origin/dev >/dev/null && echo origin/dev || echo main)
	@[ "$$(git branch --show-current)" != main ] || git switch -q dev
	@test -f $(BACKEND)/.env || cp $(BACKEND)/.env.example $(BACKEND)/.env
	@test -f $(FRONTEND)/.env.local || cp $(FRONTEND)/.env.example $(FRONTEND)/.env.local
	cd $(BACKEND) && uv venv --allow-existing -q && uv pip install -q -e ".[dev]"
	$(MAKE) db
	cd $(BACKEND) && .venv/bin/alembic upgrade head
	cd $(FRONTEND) && pnpm install --silent
	cd $(FRONTEND) && pnpm exec playwright install chromium
	npx -y @playwright/mcp@0.0.83 install-browser chrome-for-testing  # AI 실검증(MCP)용 브라우저 — 버전은 .mcp.json 과 맞춘다
	@echo "✅ setup 완료"

db: ## DB 컨테이너 기동 (healthy 될 때까지 대기)
	cd $(BACKEND) && docker compose up -d --wait

db-port: ## DB 포트 변경 (5432 충돌 시) — 예: make db-port PORT=5433. backend/.env 내용을 출력하지 않고 두 값만 바꾼다
	@echo "$(PORT)" | grep -Eq '^[0-9]{2,5}$$' || { echo "PORT 를 숫자로 지정하세요 (예: make db-port PORT=5433)"; exit 1; }
	@sed -i.bak -E 's/^POSTGRES_PORT=.*/POSTGRES_PORT=$(PORT)/; s#^(DATABASE_URL=.*@[^:/]+:)[0-9]+/#\1$(PORT)/#' $(ENV_FILE) && rm -f $(ENV_FILE).bak
	@echo "✅ DB 포트를 $(PORT) 로 바꿨습니다 ($(ENV_FILE)). 'make db' 로 다시 켜세요."

dev: db ## 백엔드 + 프론트 동시 실행 (Ctrl+C로 둘 다 종료)
	@trap 'kill 0' EXIT; \
	(cd $(BACKEND) && .venv/bin/uvicorn app.main:app --reload --port 8000) & \
	(cd $(FRONTEND) && pnpm dev) & \
	wait

dev-backend:
	cd $(BACKEND) && .venv/bin/uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd $(FRONTEND) && pnpm dev

check: check-backend check-frontend ## 정적 검증 전체

check-backend: db ## lint + 포맷 + 테스트(경계·스키마 테스트 포함) + 모델↔마이그레이션 일치
	cd $(BACKEND) && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest -q && .venv/bin/alembic check

check-frontend: ## lint(계층 import 규칙 포함) + 타입 + 테스트 + 빌드
	cd $(FRONTEND) && pnpm lint && pnpm type-check && pnpm test && pnpm build

e2e: ## Playwright 실브라우저 검증 — 예: make e2e SPEC=e2e/notice.spec.ts HARNESS_RUN_DIR=.harness/runs/x (지정 시 콘솔 에러 기록)
	cd $(FRONTEND) && HARNESS_RUN_DIR="$(HARNESS_RUN_DIR)" pnpm test:e2e $(SPEC)

gc: ## 주간 엔트로피 점검 (보고 전용)
	@bash scripts/gc/check.sh

worktree-setup: ## (워크트리 안에서) env·가상환경·의존성 준비 — 개발 서브에이전트용
	@bash scripts/worktree-setup.sh

.PHONY: up down logs ps rebuild migrate shell check test smoke clean

# 啟動全棧（含 healthcheck 等待）
up:
	docker compose -f docker/docker-compose.yml up -d --wait

# 停止全棧
down:
	docker compose -f docker/docker-compose.yml down

# 跟隨日誌（最後 100 行）
logs:
	docker compose -f docker/docker-compose.yml logs -f --tail=100

# 服務狀態
ps:
	docker compose -f docker/docker-compose.yml ps

# 重建後端 image 並重啟
rebuild:
	docker compose -f docker/docker-compose.yml build django celery_worker celery_beat && make up

# 只有在你真的懷疑人生、裝了新套件卻讀不到時，才用的終極重灌大招
rebuild-clean:
	docker compose -f docker/docker-compose.yml build --no-cache django celery_worker celery_beat && make up
# 跑 migration
migrate:
	docker compose -f docker/docker-compose.yml exec -T django python manage.py migrate

# Django shell
shell:
	docker compose -f docker/docker-compose.yml exec django python manage.py shell

# Django system check
check:
	docker compose -f docker/docker-compose.yml exec -T django python manage.py check

# 跑測試
test:
	docker compose -f docker/docker-compose.yml exec -T django python manage.py test

# Smoke test — 驗證 API 可達
smoke:
	curl -fsS http://127.0.0.1:8000/api/openapi.json | jq -e '.info.title'

# 清除 volume（⚠️ 破壞性 — 會刪除所有資料）
clean:
	docker compose -f docker/docker-compose.yml down -v

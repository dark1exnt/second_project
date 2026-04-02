# ===============================
# Настройки проекта
# ===============================
# Каталоги с кодом/тестами
PY_SRCS=src
# Порог для Radon:
# - запрещаем функции со сложностью CC уровней E/F
# - минимальный Maintainability Index (MI)
RADON_MIN_MI=65
# ===============================
# Служебные цели
# ===============================

.PHONY: help lint fmt type security cc mi hal raw check migrate makemigrations up down init bucket

help:
	@echo "Доступные цели:"
	@echo " lint - ruff check (с автофиксом)"
	@echo " fmt - ruff format"
	@echo " type - mypy (проверка типов)"
	@echo " security - bandit (скан безопасности)"
	@echo " cc - radon cc (цикломатическая сложность) + quality gate"
	@echo " mi - radon mi (индекс поддерживаемости) + quality gate"
	@echo " hal - radon hal (метрика халстеда)"
	@echo " raw - radon raw (SLOC, LLOC, комментарии, число функций/классов)"
	@echo " check - быстрый локальный quality gate (ruff+mypy+bandit+radon)"


# ===============================
# Ruff: линт и форматирование
# ===============================
lint:
	poetry run ruff check $(PY_SRCS) --fix

fmt:
	poetry run ruff format $(PY_SRCS)

# ===============================
# Mypy: проверка типов
# (если есть mypy.ini / pyproject.toml, он подхватится автоматически)
# ===============================

type:
	poetry run mypy $(PY_SRCS)

# ===============================
# Bandit: анализ безопасности
# ===============================
security:
# -r: рекурсивно, -lll: максимум строгости вывода,
# -x: исключения (подправьте под проект)
	poetry run bandit -r src -lll -x .venv,venv,build,dist,migrations

# ===============================
# Radon: метрики
# ===============================
# Цикломатическая сложность: подробный вывод (-s), среднее (-a)
cc:
	poetry run radon cc -s -a $(PY_SRCS)
	@# QUALITY GATE: проваливаем, если есть элементы со сложностью E/F
	@if poetry run radon cc -s $(PY_SRCS) | grep -E ' - [EF]$ '; then \
		echo "❌ Radon CC: обнаружены функции со сложностью E/F"; \
		exit 1; \
	else \
		echo "✅ Radon CC: нет функций с E/F"; \
	fi

# Индекс поддерживаемости
mi:
	@poetry run radon mi $(PY_SRCS)
	@# QUALITY GATE: проваливаем, если есть MI < $(RADON_MIN_MI)
	@if poetry run radon mi $(PY_SRCS) \
		| grep -oE '\([0-9]+\.[0-9]+\)' \
		| tr -d '()' \
		| awk '$$1+0 < $(RADON_MIN_MI) {exit 1}'; then \
		echo "✅ Radon MI: все файлы с MI >= $(RADON_MIN_MI)"; \
	else \
		echo "❌ Radon MI: найден MI < $(RADON_MIN_MI)"; \
		exit 1; \
	fi

# Метрика халстеда
hal:
	poetry run radon hal $(PY_SRCS)
# Метрика Raw
raw:
	poetry run radon raw $(PY_SRCS)

# ===============================
# Комплексные цели
# ===============================
# Локальный быстрый прогон с автофиксом Ruff
check: lint fmt type security cc mi hal raw

migrate:
	docker compose exec api sh -c "alembic upgrade head"

makemigrations:
	docker compose exec api sh -c 'alembic revision --autogenerate -m "$(msg)"'

test:
	PYTHONPATH=src POSTGRES_HOST=localhost poetry run pytest tests/ -v

up:
	docker compose up -d --build

down:
	docker compose down

bucket:
	docker compose exec api python -c "import boto3; from botocore.client import Config; from app.config import settings; s3 = boto3.client('s3', endpoint_url=settings.s3_endpoint_url, aws_access_key_id=settings.s3_access_key, aws_secret_access_key=settings.s3_secret_key, region_name=settings.s3_region, config=Config(signature_version='s3v4')); bucket = settings.s3_bucket_name; existing = [b['Name'] for b in s3.list_buckets().get('Buckets', [])]; print(f'Bucket {bucket} already exists' if bucket in existing else f'Bucket {bucket} created'); None if bucket in existing else s3.create_bucket(Bucket=bucket)"

init: up 
	$(MAKE) migrate 
	$(MAKE) bucket
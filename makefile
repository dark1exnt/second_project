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

.PHONY: help install lint fmt type security cc mi hal raw check

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
	@if poetry run radon cc -s $(PY_SRCS) | grep -E ' [EF] '; then \
		echo "❌ Radon CC: обнаружены функции со сложностью E/F"; \
		exit 1; \
	else \
		echo "✅ Radon CC: нет функций с E/F"; \
	fi

# Индекс поддерживаемости
mi:
	@poetry run radon mi $(PY_SRCS)
	@# QUALITY GATE: проваливаем, если есть MI < $(RADON_MIN_MI)
	@MI_BAD=$$(radon mi $(PY_SRCS) | awk '{print $$NF}' | awk -F: '{print $$NF}' | awk '$$1+0<$(RADON_MIN_MI){print}'); \
	if [ -n "$$MI_BAD" ]; then \
		echo "❌ Radon MI: найден MI < $(RADON_MIN_MI)"; \
		exit 1; \
	else \
		echo "✅ Radon MI: все файлы с MI >= $(RADON_MIN_MI)"; \
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
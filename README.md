# Blog Marketplace API

Бэкенд API для блог-маркетплейса с аутентификацией, управлением статьями, категориями, загрузкой изображений и асинхронной отправкой email.

---

## Стек технологий

- Python 3.12
- FastAPI
- SQLAlchemy (async)
- PostgreSQL 17
- Alembic
- Celery + RabbitMQ
- MinIO (S3-совместимое хранилище)
- Docker, Docker Compose
- Poetry
- Ruff, mypy, Bandit, Radon
- pytest

---

## Архитектура

Проект реализован в многослойной архитектуре:

```
src/app/
├── api/           # роуты и зависимости
├── core/          # конфиг, безопасность, middleware, exceptions
├── db/            # подключение к БД
├── models/        # SQLAlchemy модели
├── repositories/  # доступ к данным
├── schemas/       # Pydantic схемы
├── services/      # бизнес-логика
└── tasks/         # celery задачи
```

---

## Быстрый старт

### 1. Клонировать проект

```
git clone https://github.com/dark1exnt/second_project.git
cd second_project
cp .env.example .env
```

---

### 2. Полная инициализация проекта

```
make init
```

Команда:
- поднимает контейнеры
- применяет миграции
- создает bucket в MinIO

---

### 3. Доступные сервисы

| Сервис | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |
| RabbitMQ | http://localhost:15672 |

---

## Альтернативный запуск (по шагам)

```
make up
make migrate
make bucket
```

---

## Переменные окружения

Скопировать `.env.example` в `.env`.

### PostgreSQL

| Переменная | Пример |
|---|---|
| POSTGRES_HOST | postgres |
| POSTGRES_PORT | 5432 |
| POSTGRES_USER | postgres |
| POSTGRES_PASSWORD | postgres |
| POSTGRES_DB | blog_marketplace |

### JWT

| Переменная | Пример |
|---|---|
| SECRET_KEY | secret-key |
| ALGORITHM | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30 |

### S3 / MinIO

| Переменная | Пример |
|---|---|
| S3_ENDPOINT_URL | http://minio:9000 |
| S3_ACCESS_KEY | minioadmin |
| S3_SECRET_KEY | minioadmin |
| S3_BUCKET_NAME | blog-images |
| S3_REGION | eu-west-1 |

### RabbitMQ

| Переменная | Пример |
|---|---|
| RABBITMQ_HOST | rabbitmq |
| RABBITMQ_USER | guest |
| RABBITMQ_PASSWORD | guest |

### Email

| Переменная | Пример |
|---|---|
| SMTP_USER | your@email.com |
| SMTP_PASSWORD | your-password |

---

## Команды Makefile

```
make help
make up
make down
make logs
make init
make migrate
make makemigrations msg="message"
make bucket
make test
make check
```

---

## Миграции

```
make migrate
```

Создать:

```
make makemigrations msg="add new field"
```

---

## Тесты

```
make test
```

---

## Проверка качества кода

```
make check
```

Включает:
- Ruff (lint + format)
- mypy
- Bandit
- Radon

---

## API

Swagger:
http://localhost:8000/docs

### Основные эндпоинты

```
Auth
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout

Categories
GET /api/v1/categories/
POST /api/v1/categories/
GET /api/v1/categories/{id}
PATCH /api/v1/categories/{id}
DELETE /api/v1/categories/{id}

Articles
GET /api/v1/articles/
POST /api/v1/articles/
GET /api/v1/articles/{id}
PATCH /api/v1/articles/{id}
DELETE /api/v1/articles/{id}
POST /api/v1/articles/{id}/image
```

---

## Healthcheck

```
GET /health
```


# Blog Marketplace API

Бэкенд API для блог-маркетплейса с аутентификацией, управлением статьями, категориями, загрузкой изображений и асинхронной отправкой email через очередь сообщений.

---

## Быстрый старт

```bash
git clone https://github.com/dark1exnt/second_project.git
cd second_project
cp .env.example .env
docker compose up --build
```

API будет доступно по адресу: [http://localhost:8000](http://localhost:8000)  
Swagger документация: [http://localhost:8000/docs](http://localhost:8000/docs)

После запуска применить миграции:

```bash
docker compose exec api sh -c "alembic upgrade head"
```

Создать bucket в MinIO (один раз):  
Открыть [http://localhost:9001](http://localhost:9001) → войти → создать bucket `blog-images`.

---

## Переменные окружения

Скопировать `.env.example` в `.env` и заполнить значения:

| Переменная | Описание | Пример |
|---|---|---|
| `POSTGRES_HOST` | Хост PostgreSQL | `postgres` |
| `POSTGRES_PORT` | Порт PostgreSQL | `5432` |
| `POSTGRES_USER` | Пользователь БД | `postgres` |
| `POSTGRES_PASSWORD` | Пароль БД | `postgres` |
| `POSTGRES_DB` | Название БД | `blog_marketplace` |
| `SECRET_KEY` | Секрет для JWT | `your-secret-key` |
| `ALGORITHM` | Алгоритм JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена | `30` |
| `S3_ENDPOINT_URL` | URL MinIO/S3 | `http://minio:9000` |
| `S3_ACCESS_KEY` | Access key S3 | `minioadmin` |
| `S3_SECRET_KEY` | Secret key S3 | `minioadmin` |
| `S3_BUCKET_NAME` | Название bucket | `blog-images` |
| `RABBITMQ_HOST` | Хост RabbitMQ | `rabbitmq` |
| `RABBITMQ_USER` | Пользователь RabbitMQ | `guest` |
| `RABBITMQ_PASSWORD` | Пароль RabbitMQ | `guest` |
| `SMTP_USER` | Email для отправки | `your@email.com` |
| `SMTP_PASSWORD` | Пароль SMTP | `your-password` |

---

## Тесты

```bash
make test
```

> Перед запуском тестов должен быть запущен PostgreSQL: `docker compose up -d postgres`

---

## Стек технологий

| Компонент | Технология |
|---|---|
| Язык | Python 3.12 |
| Фреймворк | FastAPI |
| База данных | PostgreSQL 17 |
| ORM | SQLAlchemy (async) |
| Миграции | Alembic |
| Очередь задач | Celery + RabbitMQ |
| Хранилище файлов | MinIO (S3-совместимое) |
| Аутентификация | JWT (cookie) |
| Контейнеризация | Docker, Docker Compose |
| Зависимости | Poetry |
| Линтер | Ruff |
| Тесты | pytest + httpx |

---

## API

Полная документация доступна в Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

### Основные эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Регистрация |
| `POST` | `/api/v1/auth/login` | Вход |
| `POST` | `/api/v1/auth/logout` | Выход |
| `GET` | `/api/v1/categories/` | Список категорий |
| `POST` | `/api/v1/categories/` | Создать категорию |
| `GET` | `/api/v1/categories/{id}` | Получить категорию |
| `PATCH` | `/api/v1/categories/{id}` | Обновить категорию |
| `DELETE` | `/api/v1/categories/{id}` | Удалить категорию |
| `GET` | `/api/v1/articles/` | Список статей (пагинация, поиск, фильтр) |
| `POST` | `/api/v1/articles/` | Создать статью |
| `GET` | `/api/v1/articles/{id}` | Получить статью |
| `PATCH` | `/api/v1/articles/{id}` | Обновить статью |
| `DELETE` | `/api/v1/articles/{id}` | Удалить статью (soft delete) |
| `POST` | `/api/v1/articles/{id}/image` | Загрузить изображение |

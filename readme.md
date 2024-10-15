# Python WEB course project by Pynctual Adventurers
The task (in Ukrainian):
https://docs.google.com/document/d/11mdaddCwhgKPPWgTnQgJNolNUV_DwiZkjj7vC5En3vw/edit

## Getting started

This guide will take you through the steps to set up and run the project on your device.

### Installation

Steps to install the project in a standart way:

1. Clone the repository: https://github.com/shulika-w/python-web-course-project

2. Go to the project directory: `cd python-web-course-project`

3. Run `poetry shell` and `poetry install`

4. Create, fill with settings and put in `app` folder file `.env` with following format:

```
API_NAME=PhotoShare API
API_PROTOCOL=http
API_HOST=127.0.0.1
API_PORT=8000

SECRET_KEY_LENGTH=64
ALGORITHM=HS512

DATABASE=postgresql
DRIVER_SYNC=psycopg2
DRIVER_ASYNC=asyncpg
POSTGRES_DB=...
POSTGRES_USER=${POSTGRES_DB}
POSTGRES_PASSWORD=...
POSTGRES_HOST=${API_HOST}
POSTGRES_PORT=5432
SQLALCHEMY_DATABASE_URL_SYNC=${DATABASE}+${DRIVER_SYNC}://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
SQLALCHEMY_DATABASE_URL_ASYNC=${DATABASE}+${DRIVER_ASYNC}://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

REDIS_PROTOCOL=redis
REDIS_HOST=${API_HOST}
REDIS_PORT=6379
REDIS_USER=...
REDIS_PASSWORD=...
REDIS_URL=${REDIS_PROTOCOL}://${REDIS_USER}:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}
REDIS_EXPIRE=3600
REDIS_DB_FOR_RATE_LIMITER=0
REDIS_DB_FOR_OBJECTS=1

RATE_LIMITER_TIMES=2
RATE_LIMITER_SECONDS=5

MAIL_SERVER=...
MAIL_PORT=465
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_FROM=test@test.com
MAIL_FROM_NAME=${API_NAME}

CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

TEST=False
```

5. If you want to run the project locally and you already have running instances of Postgres DB and Redis DB then go to next point. Otherwise, you can run Postgres DB and Redis DB with Docker by `docker-compose --env-file app/.env up -d`

6. Go to app folder `cd app` and run `alembic upgrade head`

7. Run `python main.py` and open http://127.0.0.1:8000 or http://127.0.0.1:8000/docs to open the project's Swagger documentation (The API protocol, host and port you can change with .env)

### The authors

Pynctual Adventurers team
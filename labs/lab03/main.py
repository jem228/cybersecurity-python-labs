"""Точка входу FastAPI-застосунку лабораторної роботи № 3."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab03.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску, не заповнюючи їх даними."""
    initialize_database()
    yield


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(records.router)


@app.get(
    "/ping",
    tags=["Службові маршрути"],
    summary="Перевірити доступність API",
    description="Повертає статус ok, якщо API відповідає на запит.",
)
def ping() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/student",
    tags=["Службові маршрути"],
    summary="Отримати дані студента",
    description="Повертає ім'я, академічну групу та номер варіанта з shared/student.py.",
)
def get_student() -> dict[str, str | int]:
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }

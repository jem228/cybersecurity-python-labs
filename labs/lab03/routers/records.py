import sqlite3
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from labs.lab03 import repository
from labs.lab03.config import VALUE_MAX, VALUE_MIN
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter(prefix="/records", tags=["Записи аудиту"])


def _handle_database_error() -> HTTPException:
    return HTTPException(status_code=500, detail="Помилка бази даних.")


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Отримати список записів",
    description=(
        "Повертає записи з необов'язковими фільтрами. Усі задані фільтри "
        "об'єднуються умовою AND. Сортування за ID за зростанням."
    ),
)
def list_records(
    category_id: int | None = Query(default=None, gt=0, description="Фільтр за додатним ID категорії."),
    record_status: str | None = Query(default=None, alias="status", pattern="^(new|in_progress|done)$", description="Фільтр за статусом: new, in_progress або done."),
    min_value: float | None = Query(default=None, ge=VALUE_MIN, le=VALUE_MAX, description="Мінімальне значення ризику (0–10)."),
    q: str | None = Query(default=None, min_length=1, max_length=120, description="Буквальний регістрозалежний підрядок у назві."),
    limit: int = Query(default=20, ge=1, le=100, description="Кількість результатів (1–100)."),
    offset: int = Query(default=0, ge=0, description="Кількість записів, які потрібно пропустити."),
) -> list[dict]:
    try:
        return repository.get_records(category_id, record_status, min_value, q, limit, offset)
    except sqlite3.Error:
        raise _handle_database_error() from None


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис за ID",
    responses={404: {"description": "Запис не знайдено."}},
)
def get_record(record_id: int = Path(gt=0, description="Додатний ID запису.")) -> dict:
    try:
        record = repository.get_record_by_id(record_id)
    except sqlite3.Error:
        raise _handle_database_error() from None
    if record is None:
        raise HTTPException(status_code=404, detail="Запис не знайдено.")
    return record


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запис аудиту",
    responses={
        404: {"description": "Вказану категорію не знайдено."},
        409: {"description": "Код запису вже використовується."},
    },
)
def create_record(payload: RecordCreate) -> dict:
    try:
        record_id = repository.add_record(payload.model_dump())
        record = repository.get_record_by_id(record_id)
        assert record is not None
        return record
    except repository.CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="Категорію не знайдено.") from None
    except repository.DuplicateResourceError:
        raise HTTPException(status_code=409, detail="Запис із таким кодом уже існує.") from None
    except sqlite3.Error:
        raise _handle_database_error() from None


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити запис",
    description="Усі змінювані поля потрібно передати в запиті. ID змінити неможливо.",
    responses={
        404: {"description": "Запис або вказану категорію не знайдено."},
        409: {"description": "Код запису вже використовується іншим записом."},
    },
)
def replace_record(
    payload: RecordReplace,
    record_id: int = Path(gt=0, description="Додатний ID запису."),
) -> dict:
    try:
        record = repository.update_record(record_id, payload.model_dump())
        if record is None:
            raise HTTPException(status_code=404, detail="Запис не знайдено.")
        return record
    except repository.CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="Категорію не знайдено.") from None
    except repository.DuplicateResourceError:
        raise HTTPException(status_code=409, detail="Запис із таким кодом уже існує.") from None
    except sqlite3.Error:
        raise _handle_database_error() from None


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    responses={404: {"description": "Запис не знайдено."}},
)
def remove_record(record_id: int = Path(gt=0, description="Додатний ID запису.")) -> None:
    try:
        deleted = repository.delete_record(record_id)
    except sqlite3.Error:
        raise _handle_database_error() from None
    if not deleted:
        raise HTTPException(status_code=404, detail="Запис не знайдено.")


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Масово створити записи",
    description="Атомарно додає від 1 до 100 записів. Якщо хоча б один запис некоректний, не зберігається жоден.",
    responses={
        404: {"description": "Одна або декілька категорій не існують."},
        409: {"description": "Один або декілька кодів уже використовуються або повторюються в масиві."},
    },
)
def bulk_create_records(
    payload: Annotated[
        list[RecordCreate],
        Body(
            min_length=1,
            max_length=100,
            description="Масив із 1–100 записів для атомарного додавання.",
            ),
    ],
) -> list[dict]:
    try:
        created_ids = repository.bulk_insert_records(
            [item.model_dump() for item in payload]
        )
        return [
            record
            for record_id in created_ids
            if (record := repository.get_record_by_id(record_id)) is not None
        ]
    except repository.CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="Одну або декілька категорій не знайдено.") from None
    except repository.DuplicateResourceError:
        raise HTTPException(status_code=409, detail="Код одного із записів уже існує або повторюється в масиві.") from None
    except sqlite3.Error:
        raise _handle_database_error() from None

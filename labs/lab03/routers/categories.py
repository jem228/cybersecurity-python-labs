"""Маршрути роботи з категоріями."""

import sqlite3

from fastapi import APIRouter, HTTPException, Path, Response, status

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Категорії"])


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Отримати список категорій",
    description="Повертає всі категорії, відсортовані за зростанням ID.",
)
def list_categories() -> list[dict]:
    return repository.get_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити категорію",
    responses={409: {"description": "Категорія з такою назвою вже існує."}},
)
def create_category(payload: CategoryCreate) -> dict:
    try:
        category_id = repository.create_category(payload.name)
        return {"id": category_id, "name": payload.name}
    except repository.DuplicateResourceError:
        raise HTTPException(status_code=409, detail="Категорія з такою назвою вже існує.") from None
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Помилка бази даних.") from None


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити категорію",
    description="Категорію можна видалити лише тоді, коли вона не містить записів.",
    responses={
        404: {"description": "Категорію не знайдено."},
        409: {"description": "Категорія містить записи."},
    },
)
def remove_category(
    category_id: int = Path(gt=0, description="Додатний ID категорії."),
) -> Response:
    try:
        repository.delete_category(category_id)
    except repository.CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="Категорію не знайдено.") from None
    except repository.CategoryNotEmptyError:
        raise HTTPException(status_code=409, detail="Неможливо видалити категорію, яка містить записи.") from None
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Помилка бази даних.") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)

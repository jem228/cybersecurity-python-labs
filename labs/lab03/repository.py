"""Рівень доступу до SQLite."""

import sqlite3
from contextlib import closing
from typing import Any

from labs.lab03.database import get_connection


class CategoryNotFoundError(Exception):
    """Категорію не знайдено."""


class RecordNotFoundError(Exception):
    """Запис не знайдено."""


class CategoryNotEmptyError(Exception):
    """Категорія містить записи."""


class DuplicateResourceError(Exception):
    """Порушено унікальність коду або назви."""


def _get_connection() -> sqlite3.Connection:
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def _is_unique_error(error: sqlite3.IntegrityError) -> bool:
    message = str(error).lower()
    return "unique constraint failed" in message or "is not unique" in message


def create_category(name: str) -> int:
    with closing(_get_connection()) as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO categories (name) VALUES (?)", (name,)
            )
            connection.commit()
            return int(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            connection.rollback()
            if _is_unique_error(error):
                raise DuplicateResourceError from error
            raise
        except sqlite3.Error:
            connection.rollback()
            raise


def get_categories() -> list[dict[str, Any]]:
    with closing(_get_connection()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id ASC"
        ).fetchall()
        return [dict(row) for row in rows]


def delete_category(category_id: int) -> None:
    with closing(_get_connection()) as connection:
        try:
            exists = connection.execute(
                "SELECT 1 FROM categories WHERE id = ?", (category_id,)
            ).fetchone()
            if exists is None:
                raise CategoryNotFoundError

            has_records = connection.execute(
                "SELECT 1 FROM records WHERE category_id = ? LIMIT 1",
                (category_id,),
            ).fetchone()
            if has_records is not None:
                raise CategoryNotEmptyError

            connection.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            connection.commit()
        except (CategoryNotFoundError, CategoryNotEmptyError):
            connection.rollback()
            raise
        except sqlite3.Error:
            connection.rollback()
            raise


def _record_select() -> str:
    return """
        SELECT records.id, records.code, records.title,
               records.category_id, categories.name AS category_name,
               records.value, records.status
        FROM records
        JOIN categories ON records.category_id = categories.id
    """


def get_record_by_id(record_id: int) -> dict[str, Any] | None:
    with closing(_get_connection()) as connection:
        row = connection.execute(
            _record_select() + " WHERE records.id = ?", (record_id,)
        ).fetchone()
        return dict(row) if row is not None else None


def get_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    query = _record_select() + " WHERE 1 = 1"
    parameters: list[Any] = []

    if category_id is not None:
        query += " AND records.category_id = ?"
        parameters.append(category_id)
    if status is not None:
        query += " AND records.status = ?"
        parameters.append(status)
    if min_value is not None:
        query += " AND records.value >= ?"
        parameters.append(min_value)
    if q is not None:
        # instr виконує буквальний пошук: символи % та _ не є шаблонами.
        query += " AND instr(records.title, ?) > 0"
        parameters.append(q)

    query += " ORDER BY records.id ASC LIMIT ? OFFSET ?"
    parameters.extend((limit, offset))

    with closing(_get_connection()) as connection:
        rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]


def _validate_category(connection: sqlite3.Connection, category_id: int) -> None:
    exists = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    if exists is None:
        raise CategoryNotFoundError


def add_record(record: dict[str, Any]) -> int:
    with closing(_get_connection()) as connection:
        try:
            _validate_category(connection, record["category_id"])
            cursor = connection.execute(
                """INSERT INTO records (code, title, category_id, value, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (record["code"], record["title"], record["category_id"],
                 record["value"], record["status"]),
            )
            connection.commit()
            return int(cursor.lastrowid)
        except CategoryNotFoundError:
            connection.rollback()
            raise
        except sqlite3.IntegrityError as error:
            connection.rollback()
            if _is_unique_error(error):
                raise DuplicateResourceError from error
            raise
        except sqlite3.Error:
            connection.rollback()
            raise


def update_record(record_id: int, record: dict[str, Any]) -> dict[str, Any] | None:
    with closing(_get_connection()) as connection:
        try:
            exists = connection.execute(
                "SELECT 1 FROM records WHERE id = ?", (record_id,)
            ).fetchone()
            if exists is None:
                return None
            _validate_category(connection, record["category_id"])
            connection.execute(
                """UPDATE records SET code = ?, title = ?, category_id = ?,
                   value = ?, status = ? WHERE id = ?""",
                (record["code"], record["title"], record["category_id"],
                 record["value"], record["status"], record_id),
            )
            connection.commit()
            row = connection.execute(
                _record_select() + " WHERE records.id = ?", (record_id,)
            ).fetchone()
            return dict(row) if row is not None else None
        except CategoryNotFoundError:
            connection.rollback()
            raise
        except sqlite3.IntegrityError as error:
            connection.rollback()
            if _is_unique_error(error):
                raise DuplicateResourceError from error
            raise
        except sqlite3.Error:
            connection.rollback()
            raise


def delete_record(record_id: int) -> bool:
    with closing(_get_connection()) as connection:
        try:
            cursor = connection.execute(
                "DELETE FROM records WHERE id = ?", (record_id,)
            )
            if cursor.rowcount == 0:
                connection.rollback()
                return False
            connection.commit()
            return True
        except sqlite3.Error:
            connection.rollback()
            raise


def bulk_insert_records(records: list[dict[str, Any]]) -> list[int]:
    """Атомарно додає весь масив і повертає ID створених записів."""
    if not records:
        return []

    with closing(_get_connection()) as connection:
        try:
            connection.execute("BEGIN")

            category_ids = {record["category_id"] for record in records}
            placeholders = ",".join("?" for _ in category_ids)
            found = {
                row[0] for row in connection.execute(
                    f"SELECT id FROM categories WHERE id IN ({placeholders})",
                    tuple(category_ids),
                ).fetchall()
            }
            missing = category_ids - found
            if missing:
                raise CategoryNotFoundError

            codes = [record["code"] for record in records]
            if len(codes) != len(set(codes)):
                raise DuplicateResourceError
            placeholders = ",".join("?" for _ in codes)
            duplicate = connection.execute(
                f"SELECT 1 FROM records WHERE code IN ({placeholders}) LIMIT 1",
                tuple(codes),
            ).fetchone()
            if duplicate is not None:
                raise DuplicateResourceError

            created_ids: list[int] = []
            for record in records:
                cursor = connection.execute(
                    """INSERT INTO records (code, title, category_id, value, status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (record["code"], record["title"], record["category_id"],
                     record["value"], record["status"]),
                )
                created_ids.append(int(cursor.lastrowid))

            connection.commit()
            return created_ids
        except (CategoryNotFoundError, DuplicateResourceError):
            connection.rollback()
            raise
        except sqlite3.IntegrityError as error:
            connection.rollback()
            if _is_unique_error(error):
                raise DuplicateResourceError from error
            raise
        except sqlite3.Error:
            connection.rollback()
            raise

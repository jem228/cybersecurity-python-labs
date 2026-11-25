import json
import math
import sqlite3
from contextlib import closing
from pathlib import Path

from labs.lab03.database import get_connection

BASE_DIR = Path(__file__).resolve().parent
SEED_PATH = BASE_DIR / "data" / "seed.json"

ALLOWED_STATUSES = {"new", "in_progress", "done"}


def read_seed_data() -> dict:
    """Прочитати початкові дані з JSON-файлу."""
    try:
        with SEED_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as error:
        raise ValueError("Файл data/seed.json не знайдено.") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Помилка формату JSON: рядок {error.lineno}, "
            f"стовпець {error.colno}."
        ) from error

    return data


def validate_seed_data(data: dict) -> None:
    """Перевірити структуру та значення початкових даних."""
    if not isinstance(data, dict):
        raise TypeError("Початкові дані повинні бути JSON-об'єктом.")

    if set(data) != {"categories", "records"}:
        raise ValueError(
            "JSON повинен містити тільки масиви categories і records."
        )

    categories = data["categories"]
    records = data["records"]

    if not isinstance(categories, list) or len(categories) != 3:
        raise ValueError("Потрібно вказати рівно три категорії.")

    if not isinstance(records, list) or len(records) != 8:
        raise ValueError("Потрібно вказати рівно вісім записів.")

    category_ids = set()
    category_names = set()

    for category in categories:
        if not isinstance(category, dict):
            raise TypeError("Кожна категорія повинна бути об'єктом.")

        if set(category) != {"id", "name"}:
            raise ValueError("Категорія повинна містити id та name.")

        category_id = category["id"]
        name = category["name"]

        if (
            not isinstance(category_id, int)
            or isinstance(category_id, bool)
            or category_id <= 0
        ):
            raise ValueError("ID категорії повинен бути додатним цілим числом.")

        if not isinstance(name, str) or not 2 <= len(name.strip()) <= 40:
            raise ValueError("Назва категорії повинна містити 2–40 символів.")

        if category_id in category_ids:
            raise ValueError(f"Повторюється ID категорії: {category_id}.")

        if name.strip() in category_names:
            raise ValueError(f"Повторюється назва категорії: {name}.")

        category_ids.add(category_id)
        category_names.add(name.strip())

    record_codes = set()

    for record in records:
        if not isinstance(record, dict):
            raise TypeError("Кожен запис повинен бути об'єктом.")

        required_fields = {
            "code",
            "title",
            "category_id",
            "value",
            "status",
        }

        if set(record) != required_fields:
            raise ValueError(
                "Запис повинен містити code, title, category_id, value і status."
            )

        code = record["code"]
        title = record["title"]
        category_id = record["category_id"]
        value = record["value"]
        status = record["status"]

        if not isinstance(code, str) or not 3 <= len(code.strip()) <= 40:
            raise ValueError("Код запису повинен містити 3–40 символів.")

        if not isinstance(title, str) or not 3 <= len(title.strip()) <= 120:
            raise ValueError("Назва запису повинна містити 3–120 символів.")

        if code in record_codes:
            raise ValueError(f"Повторюється код запису: {code}.")

        if (
            not isinstance(category_id, int)
            or isinstance(category_id, bool)
            or category_id not in category_ids
        ):
            raise ValueError(
                f"Запис {code} посилається на невідому категорію."
            )
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or not 0 <= value <= 10
        ):
            raise ValueError(
                f"Значення value у записі {code} повинно бути від 0 до 10."
            )

        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Недозволений статус у записі {code}.")

        record_codes.add(code)


def seed_database() -> None:
    """Додати початкові категорії та записи в одну транзакцію."""
    data = read_seed_data()
    validate_seed_data(data)

    with closing(get_connection()) as connection:
        try:
            connection.execute("BEGIN")

            category_count = connection.execute(
                "SELECT COUNT(*) FROM categories"
            ).fetchone()[0]

            record_count = connection.execute(
                "SELECT COUNT(*) FROM records"
            ).fetchone()[0]

            if category_count > 0 or record_count > 0:
                connection.rollback()
                print(
                    "База даних уже містить дані. "
                    "Початкове заповнення не виконано."
                )
                return

            for category in data["categories"]:
                connection.execute(
                    """
                    INSERT INTO categories (id, name)
                    VALUES (?, ?)
                    """,
                    (category["id"], category["name"]),
                )

            for record in data["records"]:
                connection.execute(
                    """
                    INSERT INTO records (
                        code,
                        title,
                        category_id,
                        value,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        record["code"],
                        record["title"],
                        record["category_id"],
                        record["value"],
                        record["status"],
                    ),
                )

            connection.commit()

        except (sqlite3.Error, ValueError):
            connection.rollback()
            raise

    print("Початкові дані успішно додано до бази даних.")
    print("Додано категорій: 3.")
    print("Додано записів: 8.")


if __name__ == "__main__":
    try:
        seed_database()
    except (ValueError, sqlite3.Error) as error:
        print(f"Помилка початкового заповнення: {error}")



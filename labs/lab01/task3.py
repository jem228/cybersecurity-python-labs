import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from functools import wraps

from shared.student import (
    GROUP_NAME,
    STUDENT_NAME,
    VARIANT_NUMBER,
)

SALT = str(VARIANT_NUMBER).zfill(5)
MIN_LENGTH = 9

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_FOLDER, "users.csv")
JSON_PATH = os.path.join(DATA_FOLDER, "log.json")


class ValidationError(Exception):
    pass


def log_event(func):
    @wraps(func)
    def wrapper(username, password, *args, **kwargs):
        os.makedirs(DATA_FOLDER, exist_ok=True)

        status = "failure"

        try:
            result = func(username, password, *args, **kwargs)
            status = "success" if result else "failure"
            return result

        except Exception as error:
            status = f"failure ({type(error).__name__})"
            raise

        finally:
            log_data = {
                "event": "login",
                "user": username,
                "result": status,
                "timestamp": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "args": list(args),
                "kwargs": kwargs,
            }

            all_logs = []

            if os.path.exists(JSON_PATH):
                try:
                    with open(JSON_PATH, "r", encoding="utf-8") as file:
                        all_logs = json.load(file)
                except (OSError, json.JSONDecodeError):
                    all_logs = []

            all_logs.append(log_data)

            try:
                with open(JSON_PATH, "w", encoding="utf-8") as file:
                    json.dump(
                        all_logs,
                        file,
                        indent=4,
                        ensure_ascii=False
                    )
            except OSError:
                print("Помилка запису журналу")

    return wrapper


def generate_hash(password: str, salt: str | None = None) -> str:
    try:
        if password is None or salt is None:
            raise ValueError("Пароль або сіль не можуть бути None")

        if password == "" or salt == "":
            raise ValueError("Пароль або сіль порожні")

        if len(password) < MIN_LENGTH:
            raise ValidationError(
                f"Пароль коротший за мінімальну довжину ({MIN_LENGTH})"
            )

        combined_string = password + salt
        sha1_hash = hashlib.sha1(
            combined_string.encode("utf-8")
        )

        return sha1_hash.hexdigest()

    except (ValueError, ValidationError) as error:
        print(f"Помилка генерації хешу: {error}")
        raise


def create_user(username, password):
    try:
        if not username:
            raise ValueError("Логін порожній")

        hash_value = generate_hash(password, salt=SALT)
        return username, hash_value

    except (ValueError, ValidationError) as error:
        print(f"Помилка створення користувача: {error}")
        raise


def create_users(users_list):
    os.makedirs(DATA_FOLDER, exist_ok=True)

    try:
        with open(
            CSV_PATH,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            for username, password in users_list:
                try:
                    user_record = create_user(username, password)
                    writer.writerow(user_record)

                except (ValueError, ValidationError) as error:
                    print(
                        f"Помилка реєстрації "
                        f"користувача [{username}]: {error}"
                    )

    except OSError as error:
        print(f"Помилка роботи з CSV-файлом: {error}")
        raise


def read_users_db():
    users_db = []

    if not os.path.exists(CSV_PATH):
        return users_db

    try:
        with open(
            CSV_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.reader(file)

            for row in reader:
                if row:
                    users_db.append(row)

    except (OSError, csv.Error) as error:
        print(f"Помилка читання бази користувачів: {error}")
        raise

    return users_db


@log_event
def login(username: str, password: str) -> bool:

    try:
        if not username or not password:
            raise ValueError(
                "Логін або пароль порожні"
            )

        users_db = read_users_db()

        try:
            current_hash = generate_hash(
                password,
                salt=SALT
            )

        except ValidationError:
            return False

        for row in users_db:

            if len(row) != 2:
                continue

            db_username, db_hash = row

            if (
                db_username == username
                and db_hash == current_hash
            ):
                return True

        return False

    except (ValueError, OSError) as error:
        print(f"Помилка авторизації: {error}")
        raise


def main():

    print(f"Студент: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}")
    print(f"Сіль: {SALT}")

    users_to_register = (
        ("admin1", "SecretPassword123"),
        ("admin2", "CryptoDev2026"),
        ("admin3", "Secret"),
        ("admin4", ""),
        ("admin5", "AdminNetSecure"),
        ("admin6", "ShieldPass2026"),
        ("admin7", "SecretPassword456"),
        ("admin8", "CryptoDev2027"),
        ("admin9", "SystemBackup99"),
        ("admin10", "AuditingPass#1"),
    )

    print("\n" + "-" * 100)
    print("ПРОЦЕС РЕЄСТРАЦІЇ КОРИСТУВАЧІВ")
    print("-" * 100)

    try:

        create_users(users_to_register)

        users_db = read_users_db()

        print("\n" + "-" * 100)
        print("БАЗА ДАНИХ КОРИСТУВАЧІВ (З CSV-ФАЙЛУ)")
        print("-" * 100)

        print(
            f"{'Користувач':<25}"
            f"{'Хеш пароля (SHA-1)':<55}"
        )

        print("-" * 100)

        for username, pwd_hash in users_db:
            print(
                f"{username:<25}"
                f"{pwd_hash:<55}"
            )

        print("-" * 100)

        print("\n" + "-" * 100)
        print("ТЕСТУВАННЯ АВТЕНТИФІКАЦІЇ ТА ЛОГУВАННЯ")
        print("-" * 100)

        print(
            f"Вхід (admin1 / правильний): "
            f"{login('admin1', 'SecretPassword123')}"
        )

        print(
            f"Вхід (admin2 / неправильний): "
            f"{login('admin2', 'CryptoDev2025')}"
        )

        print(
            f"Вхід (hacker / немає в базі): "
            f"{login('hacker', 'HackDev123')}"
        )

        print("\nПеревірка винятку при порожньому вході:")

        login("", "some_password")

    except FileNotFoundError:
        print("Файл не знайдено")

    except PermissionError:
        print("Немає прав доступу до файлу")

    except OSError:
        print("Проблема з читанням файлу на диск")

    except ValueError as error:
        print(f"ValueError: {error}")

    except ValidationError as error:
        print(f"ValidationError: {error}")


if __name__ == "__main__":
    main()
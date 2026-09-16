import csv
import hashlib
import json
import os
from datetime import datetime, timezone  # Додали timezone
from functools import wraps

from shared.student import (
    GROUP_NAME,
    STUDENT_NAME,
    VARIANT_NUMBER,
)

SALT = "00015"
MIN_LENGTH = 9

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_FOLDER, "users.csv")
JSON_PATH = os.path.join(DATA_FOLDER, "log.json")


class ValidationError(Exception):
    """Власний виняток для помилок валідації пароля."""


def log_event(func):
    """Декоратор для автоматичного запису спроб входу в JSON-журнал."""
    @wraps(func)
    def wrapper(username, password, *args, **kwargs):
        os.makedirs(DATA_FOLDER, exist_ok=True)
        
        try:
            result = func(username, password, *args, **kwargs)
            status = "success" if result else "failure"
            return result
        except Exception as error:
            status = f"failure ({type(error).__name__})"
            raise  # ВИПРАВЛЕНО: тепер просто raise замість raise error
        finally:
            # ВИПРАВЛЕНО: додано datetime.now(timezone.utc) для відповідності правилу DTZ005
            log_data = {
                "event": "login",
                "user": username,
                "result": status,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
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
            
            with open(JSON_PATH, "w", encoding="utf-8") as file:
                json.dump(all_logs, file, indent=4, ensure_ascii=False)
                
    return wrapper


def generate_hash(password: str, salt: str = "00000") -> str:
    """Генерує шістнадцятковий хеш SHA-1 від пароля із сіллю."""
    if password is None or salt is None or password == "" or salt == "":
        raise ValueError("Пароль або сіль порожні!")

    if len(password) < MIN_LENGTH:
        raise ValidationError(
            f"Пароль коротший за мінімальну довжину ({MIN_LENGTH} симв.)"
        )

    combined_string = password + salt
    sha1_hash = hashlib.sha1(combined_string.encode("utf-8"))
    return sha1_hash.hexdigest()


def create_user(username, password):
    """Створює пару (користувач, хеш)."""
    hash_value = generate_hash(password, salt=SALT)
    return username, hash_value


def create_users(users_list):
    """Записує базу користувачів у файл CSV."""
    os.makedirs(DATA_FOLDER, exist_ok=True)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for username, password in users_list:
            try:
                user_record = create_user(username, password)
                writer.writerow(user_record)
            except (ValueError, ValidationError) as error:
                print(f"Помилка реєстрації користувача [{username}]: {error}")


def read_users_db():
    """Зчитує дані з файлу CSV."""
    users_db = []
    if not os.path.exists(CSV_PATH):
        return users_db

    with open(CSV_PATH, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if row:
                users_db.append(row)
    return users_db


@log_event
def login(username: str, password: str) -> bool:
    """Автентифікує користувача за базою даних."""
    if not username or not password:
        raise ValueError("Логін або пароль порожні!")

    users_db = read_users_db()
    
    try:
        current_hash = generate_hash(password, salt=SALT)
    except ValidationError:
        return False

    for db_username, db_hash in users_db:
        if db_username == username and db_hash == current_hash:
            return True
            
    return False


def main():
    """Основна функція програми."""
    print(f"Студент: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}")

    # Нові користувачі від admin1 до admin10
    users_to_register = (
        ("admin1", "SecretPassword123"),
        ("admin2", "CryptoDev2026"),
        ("admin3", "short"),             # Менше 9 символів -> ValidationError
        ("admin4", ""),                  # Порожній -> ValueError
        ("admin5", "AdminNetSecure"),
        ("admin6", "ShieldPass2026"),
        ("admin7", "AnalysisData!"),
        ("admin8", "GuestPass789"),
        ("admin9", "SystemBackup99"),
        ("admin10", "AuditingPass#1"),
    )

    print("\n" + "=" * 80)
    print("ПРОЦЕС РЕЄСТРАЦІЇ КОРИСТУВАЧІВ")
    print("=" * 80)
    
    try:
        create_users(users_to_register)

        users_db = read_users_db()

        print("\n" + "=" * 80)
        print("БАЗА ДАНИХ КОРИСТУВАЧІВ (З CSV-ФАЙЛУ)")
        print("=" * 80)
        print(f"{'Користувач':<25}{'Хеш пароля (SHA-1)':<55}")
        print("-" * 80)
        for username, pwd_hash in users_db:
            print(f"{username:<25}{pwd_hash:<55}")
        print("-" * 80)

        print("\n" + "=" * 80)
        print("ТЕСТУВАННЯ АВТЕНТИФІКАЦІЇ ТА ЛОГУВАННЯ")
        print("=" * 80)

        # Тест-кейси для перевірки входу (адаптовані під нові логіни)
        print(f"Вхід (admin1 / правильний): {login('admin1', 'SecretPassword123')}")
        print(f"Вхід (admin2 / неправильний): {login('admin2', 'WrongPass!')}")
        print(f"Вхід (hacker / немає в базі): {login('hacker', 'AnyPass123')}")
        
        print("\nПеревірка винятку при порожньому вході:")
        login("", "some_password")

    except FileNotFoundError:
        print("Помилка: Файл не знайдено!")
    except PermissionError:
        print("Помилка: Немає прав доступу до файлу!")
    except OSError:
        print("Помилка: Проблема з читанням/записом файлу на диск!")
    except ValueError as error:
        print(f"Перехоплено ValueError: {error}")
    except ValidationError as error:
        print(f"Перехоплено ValidationError: {error}")



if __name__ == "__main__":
    main()
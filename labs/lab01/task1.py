import random
import string

from shared.student import (
    GROUP_NAME,
    STUDENT_NAME,
    VARIANT_NUMBER,
)

passwords = [
    "IoT@S3curity",
    "standard",
    "Blockchain@Pr0tect",
    "typical123",
    "AI@Cybersec",
    "normal",
    "Quantum@Crypt0",
    "general123",
    "Edge@S3curity",
    "common",
]

criteria = {
    "min_length": 8,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {
    "standard",
    "typical123",
    "normal",
    "general123",
    "common",
    "guest",
}


def check_password(password, all_passwords):

    min_length = criteria["min_length"]

    has_digit = any(char in string.digits for char in password)
    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)
    has_special = any(
        char in string.punctuation for char in password
    )

    if password in forbidden_passwords or len(password) < min_length:
        return "Заборонений"

    checks = [
        has_digit,
        has_upper,
        has_special,
        has_lower,
    ]

    passed_checks = sum(checks)

    if passed_checks == 1:
        return "Слабкий"

    if passed_checks < 4:
        return "Середній"

    if len(password) < min_length + 4:
        return "Сильний"

    if all_passwords.count(password) == 1:
        return "Дуже сильний"

    return "Сильний"


def add_duplicate_passwords(password_list):

    indexes = random.sample(range(len(password_list)), 3)

    for index in indexes:
        password_list.append(password_list[index])


def print_results(results):

    print("АНАЛІЗАТОР НАДІЙНОСТІ ПАРОЛІВ")
    print("-" * 100)

    print(f"Студент: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}")

    print("-" * 100)
    print(
        f"{'№':<4}"
        f"{'Пароль':<25}"
        f"{'Довжина':<10}"
        f"{'Результат':<20}"
    )
    print("-" * 100)

    for number, result in enumerate(results, start=1):
        password, level = result

        print(
            f"{number:<4}"
            f"{password:<25}"
            f"{len(password):<10}"
            f"{level:<20}"
        )

    print("-" * 75)


def main():

    all_passwords = passwords.copy()

    add_duplicate_passwords(all_passwords)

    results = []

    for password in all_passwords:
        level = check_password(password, all_passwords)
        results.append((password, level))

    print_results(results)


if __name__ == "__main__":
    main()
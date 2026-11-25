"""Налаштування API для лабораторної роботи № 3."""

APP_TITLE = "Реєстр ризиків налаштування робочих станцій"
APP_DESCRIPTION = (
    "API для ведення реєстру результатів аудиту налаштувань робочих станцій. "
    "Числове значення ризику вимірюється за шкалою від 0 до 10 балів."
)
APP_VERSION = "1.0.0"

VALUE_MIN = 0.0
VALUE_MAX = 10.0
ALLOWED_STATUSES = ("new", "in_progress", "done")

CATEGORY_NAME_MIN_LENGTH = 2
CATEGORY_NAME_MAX_LENGTH = 40
CODE_MIN_LENGTH = 3
CODE_MAX_LENGTH = 40
TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 120

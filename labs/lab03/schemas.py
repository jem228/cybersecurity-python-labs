"""Pydantic-моделі запитів і відповідей API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from labs.lab03.config import (
    CATEGORY_NAME_MAX_LENGTH,
    CATEGORY_NAME_MIN_LENGTH,
    CODE_MAX_LENGTH,
    CODE_MIN_LENGTH,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    VALUE_MAX,
    VALUE_MIN,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CategoryCreate(StrictModel):
    name: str = Field(
        min_length=CATEGORY_NAME_MIN_LENGTH,
        max_length=CATEGORY_NAME_MAX_LENGTH,
        description="Унікальна назва категорії (2–40 символів).",
        examples=["updates"],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not CATEGORY_NAME_MIN_LENGTH <= len(value) <= CATEGORY_NAME_MAX_LENGTH:
            raise ValueError("Назва категорії повинна містити 2–40 символів.")
        return value


class CategoryRead(StrictModel):
    id: int = Field(gt=0, description="Унікальний додатний ID категорії.")
    name: str = Field(description="Назва категорії.")


class RecordFields(StrictModel):
    code: str = Field(
        min_length=CODE_MIN_LENGTH,
        max_length=CODE_MAX_LENGTH,
        description="Унікальний код запису (3–40 символів).",
        examples=["V15-09"],
    )
    title: str = Field(
        min_length=TITLE_MIN_LENGTH,
        max_length=TITLE_MAX_LENGTH,
        description="Назва знахідки аудиту (3–120 символів).",
        examples=["Знахідка аудиту станції"],
    )
    category_id: int = Field(
        gt=0,
        strict=True,
        description="ID наявної категорії.",
        examples=[1],
    )
    value: float = Field(
        ge=VALUE_MIN,
        le=VALUE_MAX,
        strict=True,
        description="Числове значення ризику від 0 до 10 балів.",
        examples=[8.5],
    )
    status: Literal["new", "in_progress", "done"] = Field(
        description="Статус: new, in_progress або done.",
        examples=["new"],
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        value = value.strip()
        if not CODE_MIN_LENGTH <= len(value) <= CODE_MAX_LENGTH:
            raise ValueError("Код повинен містити 3–40 символів.")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not TITLE_MIN_LENGTH <= len(value) <= TITLE_MAX_LENGTH:
            raise ValueError("Назва повинна містити 3–120 символів.")
        return value


class RecordCreate(RecordFields):
    """Модель створення запису; ID призначає база даних."""


class RecordReplace(RecordFields):
    """Повна заміна всіх змінюваних полів запису."""


class RecordRead(StrictModel):
    id: int = Field(gt=0, description="Унікальний ID запису.")
    code: str
    title: str
    category_id: int
    category_name: str = Field(description="Назва пов'язаної категорії.")
    value: float
    status: Literal["new", "in_progress", "done"]


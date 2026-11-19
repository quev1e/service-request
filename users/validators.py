"""Валидаторы для пользователя"""
import re
from string import digits

from django.core.exceptions import ValidationError


def phone_number_validator(value: str):
    """Проверяет, что номер телефона содержит 11 цифр, 
    допускается ведущий знак +."""

    only_digits = value.removeprefix('+')

    if not (
        len(only_digits) == 11 and all(i in digits for i in only_digits)
    ):
        raise ValidationError("Неверно введён номер телефона!")


def contract_number_validator(value: str):
    """Проверяет соответствие номера договора 
    установленному формату."""

    if not re.fullmatch(r'\d{3}/\d{2}/\d{4}-[А-Я]', value):
        raise ValidationError(
            'Неверно введён номер договора!'
        )


def room_number_validator(value: str):
    """Проверяет соответствие номера комнаты 
    одному из допустимых форматов."""

    if not (
        re.fullmatch(r'\d{2}-\d{2}', value) \
            or re.fullmatch(r'\d{4}', value)
    ):
        raise ValidationError(
            'Неверно введён номер комнаты!'
        )

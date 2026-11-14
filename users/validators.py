from string import digits
import re
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


def phone_number_validator(value: str):

    only_digits = value[1:] if value.startswith('+') else value

    if not (
        len(only_digits) == 11 and all(i in digits for i in only_digits)
    ):
        raise ValidationError("Неверно введён номер телефона!")
    

def contract_number_validator(value: str):

    if not re.fullmatch(r'\d{3}/\d{2}/\d{4}-[А-Я]', value):
        raise ValidationError(
            'Неверно введён номер договора!'
        )


def room_number_validator(value: str):
    
    if not (re.fullmatch(r'\d{2}-d{2}', value) or re.fullmatch(r'\d{4}', value)):
        raise ValidationError(
            'Неверно введён номер комнаты!'
        )
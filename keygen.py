#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генерация ключей — лабораторная работа №3, вариант 10.

Правило варианта (по примеру из задания: «726911» -> 276DL-191GO-0467):

* ключ имеет формат ``XXXXX-XXXXX XXXX``;
* 1-й блок — три первые цифры введённого числа в случайном порядке + 2 буквы;
* 2-й блок — три последние цифры в случайном порядке + 2 буквы;
* 3-й блок — сумма чисел, получившихся в 1-м и 2-м блоках (дополняется нулями
  слева до 4 цифр): 276 + 191 = 467 -> 0467.

Модуль не зависит от tkinter, поэтому логику можно тестировать отдельно.
"""

from __future__ import annotations

import random           # перемешивание цифр и выбор случайных букв
import string           # готовый набор латинских букв A-Z
from dataclasses import dataclass   # удобная структура результата

ALPHABET = string.ascii_uppercase   # буквы, из которых состоит «остальное» в блоке
DIGITS_LENGTH = 6                   # вводная часть — ровно 6 цифр
LETTERS_IN_BLOCK = 2                # по две буквы в первом и втором блоке


class KeyFormatError(ValueError):
    """Введённая вводная часть ключа не является 6-значным DEC-числом."""


@dataclass(frozen=True)
class GeneratedKey:
    """Результат генерации: сам ключ и числа, из которых он собран.

    frozen=True — объект нельзя случайно изменить после создания.
    """

    key: str        # готовый ключ, например «276DL-191GO-0467»
    first: int      # число из цифр первого блока (276)
    second: int     # число из цифр второго блока (191)
    total: int      # их сумма (467) — она же третий блок с ведущими нулями

    @property
    def blocks(self) -> tuple[str, str, str]:
        """Разбивает ключ на три блока — удобно для тестов."""
        return tuple(self.key.replace("-", " ").split())  # type: ignore[return-value]


def validate_digits(raw: str) -> str:
    """Проверяет ввод: ровно 6 десятичных цифр.

    Возвращает очищенную строку, а при ошибке выбрасывает KeyFormatError
    с понятным текстом — его и показывает интерфейс.
    """
    value = (raw or "").strip()             # убираем пробелы по краям
    if not value:                           # пустая строка
        raise KeyFormatError("Введите 6-значное DEC-число, например 726911.")
    if not value.isdigit() or not value.isascii():   # не цифры (или не ASCII-цифры)
        raise KeyFormatError("Ввод должен состоять только из цифр 0-9.")
    if len(value) != DIGITS_LENGTH:         # цифр не шесть
        raise KeyFormatError(f"Нужно ровно {DIGITS_LENGTH} цифр, а введено {len(value)}.")
    return value                            # ввод корректен


def _random_letters(rng: random.Random, count: int = LETTERS_IN_BLOCK) -> str:
    """Возвращает count случайных заглавных латинских букв."""
    return "".join(rng.choice(ALPHABET) for _ in range(count))


def _shuffled_digits(rng: random.Random, digits: str) -> list[str]:
    """Перемешивает строку из трёх цифр и возвращает список символов."""
    shuffled = list(digits)                 # строка -> список символов
    rng.shuffle(shuffled)                   # перемешиваем на месте
    return shuffled


def generate_key(raw_digits: str, rng: random.Random | None = None) -> GeneratedKey:
    """Собирает ключ варианта 10 из введённого 6-значного числа.

    rng передаётся только в тестах: с фиксированным seed результат
    становится воспроизводимым, и это легко проверить.
    """
    digits = validate_digits(raw_digits)    # проверяем ввод (или получим исключение)
    rng = rng or random.Random()            # свой генератор случайных чисел

    # 1-й блок: первые три цифры в случайном порядке
    first_digits = _shuffled_digits(rng, digits[:3])
    # 2-й блок: последние три цифры тоже в случайном порядке
    second_digits = _shuffled_digits(rng, digits[3:])

    # к цифрам каждого блока добавляем по две случайные буквы
    block1 = "".join(first_digits) + _random_letters(rng)
    block2 = "".join(second_digits) + _random_letters(rng)

    # числа, записанные цифрами блоков (порядок цифр уже перемешан)
    first = int("".join(first_digits))
    second = int("".join(second_digits))

    # 3-й блок: сумма, дополненная нулями слева до четырёх цифр
    total = first + second
    block3 = f"{total:04d}"

    # собираем ключ в формате XXXXX-XXXXX XXXX
    return GeneratedKey(
        key=f"{block1}-{block2} {block3}",
        first=first,
        second=second,
        total=total,
    )


if __name__ == "__main__":
    import sys

    # запуск без GUI для быстрой проверки: python keygen.py 726911
    sample = sys.argv[1] if len(sys.argv) > 1 else "726911"
    result = generate_key(sample)
    print(f"Ввод: {sample}")
    print(f"Ключ: {result.key}")
    print(f"Проверка: {result.first} + {result.second} = {result.total}")

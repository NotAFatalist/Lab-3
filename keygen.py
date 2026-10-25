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

import random
import string
from dataclasses import dataclass

ALPHABET = string.ascii_uppercase
DIGITS_LENGTH = 6
LETTERS_IN_BLOCK = 2


class KeyFormatError(ValueError):
    """Введённая вводная часть ключа не является 6-значным DEC-числом."""


@dataclass(frozen=True)
class GeneratedKey:
    """Результат генерации: сам ключ и числа, из которых он собран."""

    key: str
    first: int
    second: int
    total: int

    @property
    def blocks(self) -> tuple[str, str, str]:
        return tuple(self.key.replace("-", " ").split())  # type: ignore[return-value]


def validate_digits(raw: str) -> str:
    """Проверяет ввод: ровно 6 десятичных цифр."""
    value = (raw or "").strip()
    if not value:
        raise KeyFormatError("Введите 6-значное DEC-число, например 726911.")
    if not value.isdigit() or not value.isascii():
        raise KeyFormatError("Ввод должен состоять только из цифр 0-9.")
    if len(value) != DIGITS_LENGTH:
        raise KeyFormatError(f"Нужно ровно {DIGITS_LENGTH} цифр, а введено {len(value)}.")
    return value


def _random_letters(rng: random.Random, count: int = LETTERS_IN_BLOCK) -> str:
    return "".join(rng.choice(ALPHABET) for _ in range(count))


def _shuffled_digits(rng: random.Random, digits: str) -> list[str]:
    shuffled = list(digits)
    rng.shuffle(shuffled)
    return shuffled


def generate_key(raw_digits: str, rng: random.Random | None = None) -> GeneratedKey:
    """Собирает ключ варианта 10 из введённого 6-значного числа."""
    digits = validate_digits(raw_digits)
    rng = rng or random.Random()

    first_digits = _shuffled_digits(rng, digits[:3])
    second_digits = _shuffled_digits(rng, digits[3:])

    block1 = "".join(first_digits) + _random_letters(rng)
    block2 = "".join(second_digits) + _random_letters(rng)

    first = int("".join(first_digits))
    second = int("".join(second_digits))
    total = first + second
    block3 = f"{total:04d}"

    return GeneratedKey(
        key=f"{block1}-{block2} {block3}",
        first=first,
        second=second,
        total=total,
    )


if __name__ == "__main__":
    import sys

    sample = sys.argv[1] if len(sys.argv) > 1 else "726911"
    result = generate_key(sample)
    print(f"Ввод: {sample}")
    print(f"Ключ: {result.key}")
    print(f"Проверка: {result.first} + {result.second} = {result.total}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты генератора ключей (вариант 10). Запуск: python -m unittest discover tests"""

from __future__ import annotations

import os
import random
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keygen import KeyFormatError, generate_key  # noqa: E402

KEY_PATTERN = re.compile(r"^([A-Z0-9]{5})-([A-Z0-9]{5}) ([0-9]{4})$")


class KeyFormatTests(unittest.TestCase):
    def test_key_matches_variant_format(self) -> None:
        for sample in ("726911", "000000", "999999", "123456"):
            key = generate_key(sample, random.Random(1)).key
            self.assertRegex(key, KEY_PATTERN, f"неверный формат для {sample}")

    def test_blocks_contain_input_digits(self) -> None:
        result = generate_key("726911", random.Random(2))
        block1, block2, block3 = result.blocks

        self.assertEqual(sorted(block1[:3]), sorted("726"))
        self.assertEqual(sorted(block2[:3]), sorted("911"))

    def test_letters_follow_digits(self) -> None:
        block1, block2, _ = generate_key("726911", random.Random(3)).blocks
        self.assertTrue(block1[3:].isalpha() and block1[3:].isupper())
        self.assertTrue(block2[3:].isalpha() and block2[3:].isupper())

    def test_third_block_is_sum(self) -> None:
        for seed in range(20):
            result = generate_key("726911", random.Random(seed))
            block1, block2, block3 = result.blocks
            self.assertEqual(int(block3), int(block1[:3]) + int(block2[:3]))
            self.assertEqual(f"{result.first + result.second:04d}", block3)

    def test_example_from_task(self) -> None:
        # «726911» -> 276 + 191 = 467 -> XXXX-XXXXX 0467
        result = generate_key("726911", random.Random(0))
        self.assertEqual(result.total, result.first + result.second)
        self.assertEqual(len(result.blocks[2]), 4)

    def test_leading_zeros(self) -> None:
        result = generate_key("012345", random.Random(4))
        self.assertEqual(len(result.blocks[2]), 4)
        self.assertRegex(result.key, KEY_PATTERN)

    def test_same_seed_gives_same_key(self) -> None:
        first = generate_key("726911", random.Random(42)).key
        second = generate_key("726911", random.Random(42)).key
        self.assertEqual(first, second)


class KeyValidationTests(unittest.TestCase):
    def test_rejects_wrong_length(self) -> None:
        for value in ("", "  ", "12345", "1234567"):
            with self.assertRaises(KeyFormatError):
                generate_key(value)

    def test_rejects_non_digits(self) -> None:
        for value in ("12a456", "72 911", "-72691"):
            with self.assertRaises(KeyFormatError):
                generate_key(value)

    def test_accepts_surrounding_spaces(self) -> None:
        self.assertRegex(generate_key("  726911  ").key, KEY_PATTERN)


if __name__ == "__main__":
    unittest.main()

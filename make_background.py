#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Подготовка фона для keygen'а (лабораторная №3).

Берёт исходный арт из assets/ (new-bg.webp, new-bg.png или new-bg.jpg),
приводит его к размеру окна 960×540 и мягко затемняет центральную область —
под панель с интерфейсом. Без этого панель и фон одинаковы по яркости
и интерфейс визуально сливается с картинкой.

Запуск::

    python make_background.py

Результат: assets/background.png (его и загружает main.py).
Запасной фон, нарисованный программно, лежит отдельно —
assets/background_generated.png, его пересобирает make_assets.py.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 960, 540
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
TARGET = os.path.join(ASSETS, "background.png")

# кандидаты исходника: свой арт пользователя
SOURCES = ("new-bg.webp", "new-bg.png", "new-bg.jpg")

# Затемнение центра (эллипс под панелью интерфейса).
# По умолчанию выключено: панель непрозрачная и центр арта всё равно не виден,
# а затемнение только гасит те края картинки, которые видны вокруг панели.
# Если арт окажется слишком ярким и мешает читать текст — поставьте 0.3…0.5.
DIM_STRENGTH = 0.0
DIM_RADII = (WIDTH // 2 - 20, HEIGHT // 2 - 15)
DIM_BLUR = 110


def cover_resize(image: Image.Image, width: int, height: int) -> Image.Image:
    """Масштабирует картинку «по покрытию» окна и обрезает лишнее по центру."""
    source_ratio = image.width / image.height
    target_ratio = width / height
    if source_ratio > target_ratio:          # исходник шире окна — режем по бокам
        new_height = height
        new_width = round(height * source_ratio)
    else:                                    # исходник выше — режем сверху и снизу
        new_width = width
        new_height = round(width / source_ratio)
    resized = image.resize((new_width, new_height), Image.LANCZOS)
    left = (new_width - width) // 2
    top = (new_height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def add_dim(image: Image.Image) -> Image.Image:
    """Мягко затемняет центральную область (если DIM_STRENGTH > 0)."""
    if DIM_STRENGTH <= 0:
        return image
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    cx, cy = WIDTH // 2, HEIGHT // 2
    rx, ry = DIM_RADII
    ImageDraw.Draw(mask).ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                                 fill=round(DIM_STRENGTH * 255))
    mask = mask.filter(ImageFilter.GaussianBlur(DIM_BLUR))

    dark = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    return Image.composite(dark, image, mask)


def find_source() -> str | None:
    for name in SOURCES:
        path = os.path.join(ASSETS, name)
        if os.path.exists(path):
            return path
    return None


def main() -> int:
    source = find_source()
    if not source:
        print("не найден исходный арт в assets/: нужен new-bg.webp (или .png/.jpg)")
        return 1

    image = Image.open(source).convert("RGB")
    print(f"исходник: {os.path.basename(source)} {image.size}")

    prepared = add_dim(cover_resize(image, WIDTH, HEIGHT))
    prepared.save(TARGET, "PNG", optimize=True)
    print(f"готово: {TARGET} ({WIDTH}×{HEIGHT}, "
          f"{os.path.getsize(TARGET) // 1024} КБ)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка запасных ресурсов для keygen'а: фон и 8-битная музыка.

Основные файлы в assets/ — свои: background.png (арт) и theme.wav (трек Silksong
«Bilewater», mp3 перекодирован в WAV, потому что winsound умеет только WAV).
Этот скрипт рисует/синтезирует ЗАПАСНЫЕ файлы, если основных почему-то нет::

    python make_assets.py           # создаст только отсутствующие fallback-файлы
    python make_assets.py --force   # перезаписать fallback-файлы

Создаёт:
    assets/background_generated.png  — нарисованный программно фон 960×540;
    assets/theme_generated.wav       — зацикленная 8-битная мелодия.

Пользовательские background.png и theme.wav скрипт никогда не перезаписывает.
Для работы нужен Pillow; сам keygen (main.py) обходится стандартной библиотекой.
"""

from __future__ import annotations

import math
import os
import random
import sys
import wave
from array import array

from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 960, 540
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

TEAL = (126, 224, 208)
CRIMSON = (224, 64, 95)
GOLD = (242, 193, 78)
PALE = (196, 186, 226)


def vertical_gradient() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    top, bottom = (16, 18, 38), (4, 5, 11)
    for y in range(HEIGHT):
        ratio = y / (HEIGHT - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (WIDTH, y)], fill=color)
    return image


def add_glow(image: Image.Image, center: tuple[int, int], radius: int,
             color: tuple[int, int, int], strength: int = 190) -> Image.Image:
    """Мягкое радиальное свечение поверх изображения."""
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    cx, cy = center
    ImageDraw.Draw(mask).ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius], fill=strength
    )
    mask = mask.filter(ImageFilter.GaussianBlur(radius / 2.4))
    layer = Image.new("RGB", (WIDTH, HEIGHT), color)
    return Image.composite(layer, image, mask)


def spire(draw: ImageDraw.ImageDraw, x: float, width: float, height: float,
          color: tuple[int, int, int]) -> None:
    """Один шпиль: вытянутый силуэт с изломом по центру."""
    base = HEIGHT
    top = base - height
    points = [
        (x - width / 2, base),
        (x - width * 0.16, top + height * 0.18),
        (x, top),
        (x + width * 0.16, top + height * 0.18),
        (x + width / 2, base),
    ]
    draw.polygon(points, fill=color)


def bezier(points: list[tuple[float, float]], steps: int = 90) -> list[tuple[float, float]]:
    """Гладкая кривая по опорным точкам (квадратичная/кубическая)."""
    result = []
    for index in range(steps + 1):
        t = index / steps
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = points
        u = 1 - t
        x = u ** 3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3
        y = u ** 3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3
        result.append((x, y))
    return result


def build_background() -> Image.Image:
    random.seed(10)
    image = vertical_gradient()

    image = add_glow(image, (700, 140), 250, CRIMSON, 150)
    image = add_glow(image, (170, HEIGHT - 60), 260, TEAL, 90)

    # дальний план — частокол шпилей
    draw = ImageDraw.Draw(image)
    for x in range(-40, WIDTH + 60, 46):
        height = random.randint(120, 230)
        spire(draw, x + random.randint(-12, 12), 30, height, (10, 12, 24))

    # ближний план — крупные шпили с подсветкой по грани
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for x, width, height in ((120, 90, 300), (330, 120, 380), (560, 80, 260),
                             (760, 130, 330), (880, 70, 210)):
        spire(overlay_draw, x, width, height, (7, 8, 18, 255))
        overlay_draw.line(
            [(x - width * 0.16, HEIGHT - height * 0.82), (x - width / 2, HEIGHT)],
            fill=(*TEAL, 40), width=3,
        )
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")

    # нити шёлка
    silk = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    silk_draw = ImageDraw.Draw(silk)
    for _ in range(9):
        start = (random.randint(-60, WIDTH), random.randint(-20, 120))
        end = (random.randint(0, WIDTH + 60), random.randint(HEIGHT - 160, HEIGHT + 40))
        curve = bezier([
            start,
            (random.randint(0, WIDTH), random.randint(0, HEIGHT)),
            (random.randint(0, WIDTH), random.randint(0, HEIGHT)),
            end,
        ])
        silk_draw.line(curve, fill=(*PALE, 34), width=2)
    silk = silk.filter(ImageFilter.GaussianBlur(0.6))
    image = Image.alpha_composite(image.convert("RGBA"), silk).convert("RGB")

    # звёзды
    draw = ImageDraw.Draw(image, "RGBA")
    for _ in range(220):
        x, y = random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)
        radius = random.choice((1, 1, 1, 2))
        alpha = random.randint(40, 190)
        draw.ellipse([x, y, x + radius, y + radius], fill=(220, 210, 255, alpha))

    # виньетка
    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    ImageDraw.Draw(vignette).ellipse([-160, -160, WIDTH + 160, HEIGHT + 160], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(120))
    black = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    image = Image.composite(image, black, vignette)

    # тонкая золотая рамка
    frame = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle(
        [14, 14, WIDTH - 15, HEIGHT - 15], radius=18, outline=(*GOLD, 70), width=2
    )
    image = Image.alpha_composite(image.convert("RGBA"), frame).convert("RGB")
    return image


# --- музыка ---------------------------------------------------------------------
SAMPLE_RATE = 22050
BPM = 148
BEAT = 60 / BPM

NOTES = {
    "A2": 110.00, "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00,
    "A3": 220.00, "B3": 246.94,
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00,
    "B4": 493.88, "C5": 523.25, "D5": 587.33, "E5": 659.25, "G5": 783.99, "A5": 880.00,
}

MELODY = [
    ("A4", .5), ("C5", .5), ("E5", .5), ("A5", 1.), ("G5", .5), ("E5", .5), ("C5", .5),
    ("E5", 1.), ("D5", .5), ("C5", .5), ("B4", .5), ("A4", 1.), (None, .5),
    ("F4", .5), ("A4", .5), ("C5", .5), ("F4", 1.), ("E5", .5), ("C5", .5), ("A4", .5),
    ("C5", 1.), ("B4", .5), ("A4", .5), ("G4", .5), ("A4", 1.), (None, .5),
    ("E4", .5), ("G4", .5), ("B4", .5), ("E5", 1.), ("D5", .5), ("B4", .5), ("G4", .5),
    ("B4", 1.), ("C5", .5), ("B4", .5), ("A4", .5), ("G4", 1.), (None, .5),
    ("A4", .5), ("B4", .5), ("C5", .5), ("D5", 1.), ("E5", .5), ("D5", .5), ("C5", .5),
    ("B4", 1.5), ("A4", 1.5), (None, 1.),
]

BASS = [
    ("A2", 2.), ("A2", 2.), ("F3", 2.), ("F3", 2.),
    ("C3", 2.), ("C3", 2.), ("G3", 2.), ("G3", 2.),
    ("A2", 2.), ("A2", 2.), ("F3", 2.), ("F3", 2.),
]


def render(sequence, volume: float) -> list[float]:
    """Прямоугольная волна (8-бит) с короткими атакой и затуханием."""
    total = int(sum(duration for _, duration in sequence) * BEAT * SAMPLE_RATE) + 1
    buffer = [0.0] * total
    position = 0
    for note, beats in sequence:
        length = int(beats * BEAT * SAMPLE_RATE)
        if note:
            frequency = NOTES[note]
            attack = max(1, int(0.006 * SAMPLE_RATE))
            release = max(1, int(0.05 * SAMPLE_RATE))
            for index in range(length):
                envelope = min(1.0, index / attack, (length - index) / release)
                phase = (index * frequency / SAMPLE_RATE) % 1.0
                buffer[position + index] += (1.0 if phase < 0.5 else -1.0) * volume * envelope
        position += length
    return buffer


def write_music(path: str) -> None:
    melody = render(MELODY, 0.24)
    bass = render(BASS, 0.16)
    size = max(len(melody), len(bass))
    samples = array("h")
    for index in range(size):
        value = (melody[index] if index < len(melody) else 0.0) + \
                (bass[index] if index < len(bass) else 0.0)
        value = max(-1.0, min(1.0, value))
        samples.append(int(value * 32000))

    with wave.open(path, "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(SAMPLE_RATE)
        file.writeframes(samples.tobytes())


def main() -> int:
    force = "--force" in sys.argv[1:]
    os.makedirs(ASSETS, exist_ok=True)

    background = os.path.join(ASSETS, "background_generated.png")
    music = os.path.join(ASSETS, "theme_generated.wav")

    if force or not os.path.exists(background):
        build_background().save(background, "PNG", optimize=True)
        print("создан", background, os.path.getsize(background), "байт")
    else:
        print("уже есть, пропускаю:", background)

    if force or not os.path.exists(music):
        write_music(music)
        print("создан", music, os.path.getsize(music), "байт")
    else:
        print("уже есть, пропускаю:", music)

    print("основные assets/background.png и assets/theme.wav скрипт не трогает")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

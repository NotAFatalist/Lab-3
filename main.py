#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Keygen по мотивам Hollow Knight: Silksong — лабораторная работа №3, вариант 10.

Интерфейс (tkinter):
  * фоновая картинка-арт (assets/background.png);
  * поле ввода 6-значного DEC-числа (вводная часть ключа);
  * поле сгенерированного ключа формата XXXXX-XXXXX XXXX;
  * кнопки «Сгенерировать», «Копировать», включение музыки и выход.

Допзадание: 8-битная музыка (assets/theme.wav, воспроизводится через winsound)
и анимация — летящие искры, бегущая развёртка, пульсирующая рамка ключа
и «печать» ключа по символам.

Логика генерации вынесена в keygen.py, оформление собирается make_assets.py.
"""

from __future__ import annotations

import math
import os
import random
import tkinter as tk
from tkinter import messagebox

from keygen import KeyFormatError, GeneratedKey, generate_key

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
BACKGROUND = os.path.join(ASSETS, "background.png")
MUSIC = os.path.join(ASSETS, "theme.wav")

WIDTH, HEIGHT = 900, 560

DARK = "#070910"
PANEL = "#0b101c"
FIELD = "#131a2a"
TEXT = "#cfd6e6"
MUTED = "#7c86a3"
GOLD = "#f2c14e"
CRIMSON = "#e0405f"
TEAL = "#7ee0d0"

GLOW_FROM = (26, 32, 54)
GLOW_TO = (70, 26, 44)
GLOW_DARK = "#1b2338"
GLOW_BRIGHT = "#461a2c"

FONT_TITLE = ("Georgia", 30, "bold")
FONT_SUB = ("Consolas", 10)
FONT_INPUT = ("Consolas", 22)
FONT_KEY = ("Consolas", 25, "bold")
FONT_BUTTON = ("Consolas", 11, "bold")
FONT_STATUS = ("Consolas", 10)


def mix(first: tuple[int, int, int], second: tuple[int, int, int], ratio: float) -> str:
    """Смешивает два цвета (0.0 — первый, 1.0 — второй) в строку #rrggbb."""
    ratio = min(1.0, max(0.0, ratio))
    return "#%02x%02x%02x" % tuple(
        int(first[i] + (second[i] - first[i]) * ratio) for i in range(3)
    )


class KeygenApp:
    """Окно генератора ключей."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Silksong Keygen — лабораторная №3, вариант 10")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=DARK)

        self.full_key = ""
        self.revealed = 0
        self.phase = 0.0
        self.scan_y = 0.0
        self.music_on = False
        self.particles: list[list] = []

        self._build_canvas()
        self._build_panel()
        self._build_particles()
        self._bind_events()
        self._animate()

    # --- оформление ------------------------------------------------------------
    def _build_canvas(self) -> None:
        self.canvas = tk.Canvas(
            self.root, width=WIDTH, height=HEIGHT, bg=DARK, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        if os.path.exists(BACKGROUND):
            self.background = tk.PhotoImage(file=BACKGROUND)
            self.canvas.create_image(0, 0, image=self.background, anchor="nw")
        else:
            self.background = None
            messagebox.showwarning(
                "Нет фона",
                "Файл assets/background.png не найден.\nЗапустите: python make_assets.py",
            )

        self.scanline = self.canvas.create_line(
            0, 0, WIDTH, 0, fill="#3c4a70", width=1, stipple="gray12"
        )

    def _build_panel(self) -> None:
        self.panel = tk.Frame(
            self.canvas, bg=PANEL, bd=0,
            highlightthickness=1, highlightbackground="#233049",
        )
        self.canvas.create_window(
            WIDTH // 2, HEIGHT // 2, window=self.panel, width=660, height=430
        )

        title = tk.Label(self.panel, text="SILKSONG", font=FONT_TITLE,
                         bg=PANEL, fg=CRIMSON)
        title.pack(pady=(18, 0))

        subtitle = tk.Label(
            self.panel, text="K E Y G E N   ·   вариант 10", font=("Consolas", 11, "bold"),
            bg=PANEL, fg=MUTED,
        )
        subtitle.pack(pady=(2, 14))

        hint = tk.Label(
            self.panel,
            text="Вводная часть: 6-значное DEC-число",
            font=FONT_SUB, bg=PANEL, fg=TEXT,
        )
        hint.pack()

        self.digits_var = tk.StringVar(value="726911")
        self.entry = tk.Entry(
            self.panel, textvariable=self.digits_var, font=FONT_INPUT,
            justify="center", width=8, bg=FIELD, fg=GOLD, insertbackground=GOLD,
            relief="flat", highlightthickness=2,
            highlightbackground="#2a3350", highlightcolor=GLOW_BRIGHT,
        )
        self.entry.pack(pady=(6, 14))

        self.key_frame = tk.Frame(
            self.panel, bg=FIELD, highlightthickness=2,
            highlightbackground=GLOW_DARK, highlightcolor=GLOW_DARK,
        )
        self.key_frame.pack(padx=40, fill="x")

        self.key_var = tk.StringVar(value="— — —")
        self.key_label = tk.Label(
            self.key_frame, textvariable=self.key_var, font=FONT_KEY,
            bg=FIELD, fg=GOLD, pady=12,
        )
        self.key_label.pack(fill="x")

        self.status_var = tk.StringVar(
            value="Введите 6 цифр и нажмите «Сгенерировать»"
        )
        self.status = tk.Label(
            self.panel, textvariable=self.status_var, font=FONT_STATUS,
            bg=PANEL, fg=MUTED, height=2, wraplength=600,
        )
        self.status.pack(pady=(10, 0))

        buttons = tk.Frame(self.panel, bg=PANEL)
        buttons.pack(pady=(6, 16))

        self.generate_button = self._button(buttons, "СГЕНЕРИРОВАТЬ", self.generate,
                                            fg=GOLD)
        self.generate_button.grid(row=0, column=0, padx=6)

        self._button(buttons, "КОПИРОВАТЬ", self.copy_key).grid(row=0, column=1, padx=6)

        self.music_button = self._button(buttons, "♪ ВКЛ", self.toggle_music)
        self.music_button.grid(row=0, column=2, padx=6)

        self._button(buttons, "ВЫХОД", self.root.destroy, fg=MUTED).grid(
            row=0, column=3, padx=6
        )

    def _button(self, parent: tk.Misc, text: str, command, fg: str = TEXT) -> tk.Button:
        button = tk.Button(
            parent, text=text, command=command, font=FONT_BUTTON,
            bg="#1b2236", fg=fg, activebackground=CRIMSON, activeforeground="#ffffff",
            relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
        )
        button.bind("<Enter>", lambda _event: button.configure(bg="#26304a"))
        button.bind("<Leave>", lambda _event: button.configure(bg="#1b2236"))
        return button

    def _build_particles(self) -> None:
        random.seed(10)
        palette = (TEAL, GOLD, "#9a8cc0", "#ffffff")
        for _ in range(70):
            x = random.uniform(0, WIDTH)
            y = random.uniform(0, HEIGHT)
            radius = random.choice((1, 1, 2))
            item = self.canvas.create_oval(
                x, y, x + radius, y + radius,
                fill=random.choice(palette), outline="",
            )
            self.particles.append([item, random.uniform(-0.9, -0.25)])

    def _bind_events(self) -> None:
        self.digits_var.trace_add("write", self._filter_input)
        self.entry.bind("<Return>", lambda _event: self.generate())
        self.root.bind("<Escape>", lambda _event: self.root.destroy())

    # --- действия --------------------------------------------------------------
    def _filter_input(self, *_args) -> None:
        value = self.digits_var.get()
        cleaned = "".join(symbol for symbol in value if symbol.isdigit())[:6]
        if cleaned != value:
            self.digits_var.set(cleaned)

    def generate(self) -> None:
        try:
            result: GeneratedKey = generate_key(self.digits_var.get())
        except KeyFormatError as error:
            self.status.configure(fg=CRIMSON)
            self.status_var.set(str(error))
            return

        self.status.configure(fg=MUTED)
        self.status_var.set(
            f"Проверка: {result.first} + {result.second} = {result.total} "
            f"→ {result.key.split()[-1]}"
        )
        self._reveal(result.key)

    def _reveal(self, key: str) -> None:
        self.full_key = key
        self.revealed = 0
        self.key_var.set("")

        def step() -> None:
            if self.revealed < len(self.full_key):
                self.revealed += 1
                tail = "▌" if self.revealed < len(self.full_key) else ""
                self.key_var.set(self.full_key[: self.revealed] + tail)
                self.root.after(45, step)
            else:
                self.key_var.set(self.full_key)

        step()

    def copy_key(self) -> None:
        if not self.full_key:
            self.status.configure(fg=CRIMSON)
            self.status_var.set("Сначала сгенерируйте ключ.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.full_key)
        self.status.configure(fg=TEAL)
        self.status_var.set(f"Ключ скопирован: {self.full_key}")

    def toggle_music(self) -> None:
        try:
            import winsound
        except ImportError:
            self.status.configure(fg=CRIMSON)
            self.status_var.set("winsound доступен только в Windows.")
            return

        if not os.path.exists(MUSIC):
            self.status.configure(fg=CRIMSON)
            self.status_var.set("Нет файла assets/theme.wav — запустите make_assets.py")
            return

        if self.music_on:
            winsound.PlaySound(None, winsound.SND_PURGE)
            self.music_on = False
            self.music_button.configure(text="♪ ВКЛ")
        else:
            winsound.PlaySound(
                MUSIC,
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP,
            )
            self.music_on = True
            self.music_button.configure(text="♪ ВЫКЛ")

    # --- анимация --------------------------------------------------------------
    def _animate(self) -> None:
        self.phase += 0.08

        for particle in self.particles:
            item, speed = particle
            self.canvas.move(item, 0, speed)
            x1, y1, _, _ = self.canvas.coords(item)
            if y1 < -4:
                self.canvas.coords(item, random.uniform(0, WIDTH), HEIGHT + 4,
                                   random.uniform(0, WIDTH) + 2, HEIGHT + 5)

        glow = (math.sin(self.phase) + 1) / 2
        self.key_frame.configure(highlightbackground=mix(GLOW_FROM, GLOW_TO, glow))

        self.scan_y = (self.scan_y + 2.4) % HEIGHT
        self.canvas.coords(self.scanline, 0, self.scan_y, WIDTH, self.scan_y)

        self.root.after(33, self._animate)


def main() -> int:
    root = tk.Tk()
    KeygenApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

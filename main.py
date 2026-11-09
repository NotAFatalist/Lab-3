#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Keygen по мотивам Hollow Knight: Silksong — лабораторная работа №3, вариант 10.

Интерфейс (tkinter), окно 960×540:
  * фоновая картинка-арт (assets/background.png, 16:9);
  * поле ввода 6-значного DEC-числа (вводная часть ключа);
  * поле сгенерированного ключа формата XXXXX-XXXXX XXXX;
  * кнопки «Сгенерировать», «Копировать», включение музыки и выход.

Допзадание: музыка Silksong OST «Bilewater» (assets/theme.wav — mp3 сконвертирован
в WAV, потому что winsound умеет только WAV) и анимация — «печать» ключа по символам.
Оформление минимальное: на фоне только арт из assets/background.png, без искр,
бегущих линий и прочего декора.

Логика генерации вынесена в keygen.py; если картинки или музыки не окажется,
make_assets.py нарисует и синтезирует запасные.
"""

from __future__ import annotations

import os                       # склейка путей к папке assets
import tkinter as tk            # сама графика: окно, виджеты, canvas
from tkinter import messagebox  # предупреждение, если не найден фон

from keygen import KeyFormatError, GeneratedKey, generate_key   # чистая логика ключа

HERE = os.path.dirname(os.path.abspath(__file__))   # папка, где лежит main.py
ASSETS = os.path.join(HERE, "assets")               # папка с картинкой и музыкой

BACKGROUND = os.path.join(ASSETS, "background.png")  # фон окна (960×540)
MUSIC = os.path.join(ASSETS, "theme.wav")            # музыка (только WAV)

WIDTH, HEIGHT = 960, 540        # размер окна (тот же, что у фона)


# --- палитра интерфейса --------------------------------------------------------
DARK = "#070910"        # самый тёмный фон (края окна)
PANEL = "#0b101c"       # фон панели с элементами управления
FIELD = "#131a2a"       # фон полей ввода и поля ключа
TEXT = "#cfd6e6"        # основной цвет текста
MUTED = "#7c86a3"       # приглушённый текст (подписи, статус)
GOLD = "#f2c14e"        # золотой акцент (ключ, кнопка генерации)
CRIMSON = "#e0405f"     # красный акцент (логотип, ошибки)
TEAL = "#7ee0d0"        # бирюзовый (успешные сообщения)

GLOW_DARK = "#1b2338"       # обычный цвет рамки поля ключа
GLOW_BRIGHT = "#461a2c"     # цвет рамки поля ввода при фокусе

FONT_TITLE = ("Georgia", 30, "bold")     # логотип SILKSONG
FONT_SUB = ("Consolas", 10)              # поясняющие подписи
FONT_INPUT = ("Consolas", 22)            # поле ввода числа
FONT_KEY = ("Consolas", 25, "bold")      # поле сгенерированного ключа
FONT_BUTTON = ("Consolas", 11, "bold")   # кнопки
FONT_STATUS = ("Consolas", 10)           # строка состояния


class KeygenApp:
    """Окно генератора ключей: собирает интерфейс и обрабатывает нажатия."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root                                        # главное окно Tk
        self.root.title("Silksong Keygen — лабораторная №3, вариант 10")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")                 # размер 960×540
        self.root.resizable(False, False)                       # тянуть окно нельзя
        self.root.configure(bg=DARK)                            # цвет окна

        # --- состояние приложения ---
        self.full_key = ""                  # готовый ключ целиком
        self.revealed = 0                   # сколько символов уже «напечатано»
        self.music_on = False               # играет ли музыка сейчас

        # --- сборка интерфейса (порядок важен: canvas ниже, панель выше) ---
        self._build_canvas()                # только фон-картинка
        self._build_panel()                 # панель с полями и кнопками
        self._bind_events()                 # горячие клавиши и фильтр ввода

    # --- оформление ------------------------------------------------------------
    def _build_canvas(self) -> None:
        """Создаёт Canvas на всё окно и рисует на нём фон."""
        self.canvas = tk.Canvas(
            self.root, width=WIDTH, height=HEIGHT, bg=DARK, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)      # растягиваем на всё окно

        # фон окна — арт из assets/background.png
        if os.path.exists(BACKGROUND):
            # ссылку на PhotoImage храним в self, иначе сборщик мусора её удалит
            self.background = tk.PhotoImage(file=BACKGROUND)
            self.canvas.create_image(0, 0, image=self.background, anchor="nw")
        else:
            self.background = None                      # картинки нет — работаем без неё
            messagebox.showwarning(
                "Нет фона",
                "Файл assets/background.png не найден.\n"
                "Запустите: python make_assets.py",
            )

    def _build_panel(self) -> None:
        """Создаёт панель с заголовком, полями ввода и кнопками."""
        # рамка в тон арту: панель тёмная, фон за ней — тёмно-бордовый арт,
        # поэтому край панели отделяем линией (иначе интерфейс «сливается» с фоном)
        self.panel = tk.Frame(
            self.canvas, bg=PANEL, bd=0,
            highlightthickness=2, highlightbackground="#6b5426",
        )
        # панель кладём по центру окна фиксированного размера
        self.canvas.create_window(
            WIDTH // 2, HEIGHT // 2, window=self.panel, width=660, height=430
        )

        # логотип игры
        title = tk.Label(self.panel, text="SILKSONG", font=FONT_TITLE,
                         bg=PANEL, fg=CRIMSON)
        title.pack(pady=(18, 0))                        # отступ сверху

        # подпись «keygen · вариант 10»
        subtitle = tk.Label(
            self.panel, text="K E Y G E N   ·   вариант 10", font=("Consolas", 11, "bold"),
            bg=PANEL, fg=MUTED,
        )
        subtitle.pack(pady=(2, 14))

        # пояснение, что именно вводить
        hint = tk.Label(
            self.panel,
            text="Вводная часть: 6-значное DEC-число",
            font=FONT_SUB, bg=PANEL, fg=TEXT,
        )
        hint.pack()

        # --- поле ввода числа ---
        # StringVar связана с Entry: любое изменение текста видно в переменной,
        # а trace_add позволяет фильтровать ввод на лету
        self.digits_var = tk.StringVar(value="726911")
        self.entry = tk.Entry(
            self.panel, textvariable=self.digits_var, font=FONT_INPUT,
            justify="center", width=8, bg=FIELD, fg=GOLD, insertbackground=GOLD,
            relief="flat", highlightthickness=2,
            highlightbackground="#2a3350", highlightcolor=GLOW_BRIGHT,
        )
        self.entry.pack(pady=(6, 14))

        # --- поле сгенерированного ключа ---
        # отдельный Frame нужен ради рамки, которую анимация перекрашивает
        self.key_frame = tk.Frame(
            self.panel, bg=FIELD, highlightthickness=2,
            highlightbackground=GLOW_DARK, highlightcolor=GLOW_DARK,
        )
        self.key_frame.pack(padx=40, fill="x")

        self.key_var = tk.StringVar(value="— — —")      # пока ключа нет
        self.key_label = tk.Label(
            self.key_frame, textvariable=self.key_var, font=FONT_KEY,
            bg=FIELD, fg=GOLD, pady=12,
        )
        self.key_label.pack(fill="x")

        # --- строка состояния (ошибки, подсказки, сообщения об успехе) ---
        self.status_var = tk.StringVar(
            value="Введите 6 цифр и нажмите «Сгенерировать»"
        )
        self.status = tk.Label(
            self.panel, textvariable=self.status_var, font=FONT_STATUS,
            bg=PANEL, fg=MUTED, height=2, wraplength=600,
        )
        self.status.pack(pady=(10, 0))

        # --- кнопки в один ряд ---
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
        """Создаёт кнопку в едином стиле и вешает эффект наведения мышью."""
        button = tk.Button(
            parent, text=text, command=command, font=FONT_BUTTON,
            bg="#1b2236", fg=fg, activebackground=CRIMSON, activeforeground="#ffffff",
            relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
        )
        # подсветка при наведении: меняем фон и возвращаем обратно
        button.bind("<Enter>", lambda _event: button.configure(bg="#26304a"))
        button.bind("<Leave>", lambda _event: button.configure(bg="#1b2236"))
        return button

    def _bind_events(self) -> None:
        """Подключает фильтр ввода и горячие клавиши."""
        self.digits_var.trace_add("write", self._filter_input)      # фильтр цифр
        self.entry.bind("<Return>", lambda _event: self.generate())  # Enter — генерация
        self.root.bind("<Escape>", lambda _event: self.root.destroy())  # Esc — выход

    # --- действия --------------------------------------------------------------
    def _filter_input(self, *_args) -> None:
        """Оставляет в поле ввода только цифры и не больше шести.

        Вызывается при каждом изменении StringVar: если после чистки строка
        отличается от введённой, записываем очищенный вариант обратно.
        """
        value = self.digits_var.get()                                   # что ввели
        cleaned = "".join(symbol for symbol in value if symbol.isdigit())[:6]
        if cleaned != value:                                            # были лишние символы
            self.digits_var.set(cleaned)                                # исправляем поле

    def generate(self) -> None:
        """Обработчик кнопки «Сгенерировать»: проверяет ввод и показывает ключ."""
        try:
            result: GeneratedKey = generate_key(self.digits_var.get())
        except KeyFormatError as error:             # ввод не 6-значное число
            self.status.configure(fg=CRIMSON)       # сообщение красным
            self.status_var.set(str(error))
            return                                  # ключ не меняем

        # всё хорошо: показываем проверку «a + b = c → третий блок»
        self.status.configure(fg=MUTED)
        self.status_var.set(
            f"Проверка: {result.first} + {result.second} = {result.total} "
            f"→ {result.key.split()[-1]}"
        )
        self._reveal(result.key)                   # и печатаем ключ по символам

    def _reveal(self, key: str) -> None:
        """Печатает ключ по одному символу — эффект «набора» текста."""
        self.full_key = key                         # запоминаем ключ целиком
        self.revealed = 0                           # начинаем с пустой строки
        self.key_var.set("")

        def step() -> None:
            """Один шаг: добавить символ и запланировать следующий через 45 мс."""
            if self.revealed < len(self.full_key):
                self.revealed += 1
                # пока ключ не допечатан, в конце мигает курсор «▌»
                tail = "▌" if self.revealed < len(self.full_key) else ""
                self.key_var.set(self.full_key[: self.revealed] + tail)
                self.root.after(45, step)           # планируем следующий шаг
            else:
                self.key_var.set(self.full_key)     # готово — показываем целиком

        step()                                      # запускаем печать

    def copy_key(self) -> None:
        """Кладёт готовый ключ в буфер обмена."""
        if not self.full_key:                       # ключа ещё нет
            self.status.configure(fg=CRIMSON)
            self.status_var.set("Сначала сгенерируйте ключ.")
            return
        self.root.clipboard_clear()                 # очищаем буфер обмена
        self.root.clipboard_append(self.full_key)   # и кладём туда ключ
        self.status.configure(fg=TEAL)              # подтверждение бирюзовым
        self.status_var.set(f"Ключ скопирован: {self.full_key}")

    def toggle_music(self) -> None:
        """Включает и выключает фоновую музыку (допзадание)."""
        try:
            import winsound                         # модуль есть только в Windows
        except ImportError:
            self.status.configure(fg=CRIMSON)
            self.status_var.set("winsound доступен только в Windows.")
            return

        if not os.path.exists(MUSIC):               # файла нет — подсказываем, что делать
            self.status.configure(fg=CRIMSON)
            self.status_var.set("Нет файла assets/theme.wav — запустите make_assets.py")
            return

        if self.music_on:                           # музыка играет — выключаем
            winsound.PlaySound(None, winsound.SND_PURGE)    # остановить и освободить
            self.music_on = False
            self.music_button.configure(text="♪ ВКЛ")
            self.status.configure(fg=MUTED)
            self.status_var.set("Музыка выключена")
        else:                                       # музыки нет — включаем
            winsound.PlaySound(
                MUSIC,
                # SND_ASYNC — не блокировать программу, SND_LOOP — повторять трек
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP,
            )
            self.music_on = True
            self.music_button.configure(text="♪ ВЫКЛ")
            self.status.configure(fg=TEAL)
            self.status_var.set("♪ Silksong — Bilewater (зациклено)")


def main() -> int:
    """Точка входа: создаёт окно и запускает цикл событий."""
    root = tk.Tk()              # главное окно Tk
    KeygenApp(root)             # собираем интерфейс
    root.mainloop()             # цикл событий: ждём кликов и таймеров
    return 0


if __name__ == "__main__":
    raise SystemExit(main())    # запуск только при прямом вызове файла

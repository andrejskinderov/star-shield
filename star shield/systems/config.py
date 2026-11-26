"""Константы, пути и настройки игры."""
import json
import os
import sys

VERSION = "2.0.0"
TITLE = "Star Shield"
WIDTH, HEIGHT, FPS = 600, 800, 60

WHITE = (240, 240, 240)
BLACK = (8, 8, 20)
RED = (230, 70, 70)
ORANGE = (240, 160, 50)
GREEN = (80, 220, 120)
BLUE = (80, 160, 255)
YELLOW = (250, 220, 70)
GRAY = (130, 130, 150)
PURPLE = (190, 100, 240)
CYAN = (70, 220, 230)

# Параметры сложности: жизни, бомбы в начале, множитель скорости врагов,
# множитель задержки появления врагов
DIFFICULTIES = {
    "easy": {"lives": 5, "bombs": 3, "speed": 0.8, "spawn": 1.3},
    "normal": {"lives": 3, "bombs": 2, "speed": 1.0, "spawn": 1.0},
    "hard": {"lives": 2, "bombs": 1, "speed": 1.25, "spawn": 0.75},
}
DEFAULT_SETTINGS = {
    "music": 0.5,
    "sfx": 0.7,
    "difficulty": "normal",
    "language": "ru",
    "fullscreen": False,
    "shake": True,
}


def resource_path(*parts):
    """Путь к ресурсам игры. Работает и из исходников, и из собранного PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, *parts)


def user_dir():
    """Папка для сохранений. Не в папке игры: у Steam она может быть только для чтения."""
    if sys.platform.startswith("win"):
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        root = os.path.expanduser("~/Library/Application Support")
    else:
        root = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    folder = os.path.join(root, "StarShield")
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        folder = os.path.expanduser("~")
    return folder


def load_json(file, default):
    """Читает JSON-файл. При ошибке возвращает копию значений по умолчанию."""
    result = dict(default)
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            result.update(data)
    except (OSError, ValueError):
        pass
    return result


def save_json(file, data):
    """Безопасная запись: сначала во временный файл, потом замена (файл не испортится)."""
    tmp = file + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, file)
    except OSError:
        pass


def _sanitize(s):
    """Исправляет некорректные значения в файле настроек."""
    if s.get("difficulty") not in DIFFICULTIES:
        s["difficulty"] = "normal"
    if s.get("language") not in ("ru", "en"):
        s["language"] = "ru"
    for key in ("music", "sfx"):
        try:
            s[key] = round(max(0.0, min(1.0, float(s[key]))), 1)
        except (TypeError, ValueError):
            s[key] = DEFAULT_SETTINGS[key]
    s["fullscreen"] = bool(s.get("fullscreen"))
    s["shake"] = bool(s.get("shake"))
    return s


SETTINGS_FILE = os.path.join(user_dir(), "settings.json")
settings = _sanitize(load_json(SETTINGS_FILE, DEFAULT_SETTINGS))


def save_settings():
    save_json(SETTINGS_FILE, settings)


def difficulty_key():
    return settings["difficulty"]


def get_difficulty():
    return DIFFICULTIES[settings["difficulty"]]

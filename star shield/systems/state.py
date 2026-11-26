"""Сохранение прогресса: таблица рекордов, статистика, достижения (save.json)."""
import os
import time

from systems import config

SAVE_FILE = os.path.join(config.user_dir(), "save.json")
DEFAULT_SAVE = {
    "highscores": [],
    "games_played": 0,
    "enemies_killed": 0,
    "bosses_killed": 0,
    "playtime": 0,
    "achievements": {},
}


def _clean(raw):
    """Проверяет данные из файла, чтобы испорченное сохранение не ломало игру."""
    data = dict(DEFAULT_SAVE)
    data.update(raw)
    for key in ("games_played", "enemies_killed", "bosses_killed", "playtime"):
        if not isinstance(data[key], (int, float)) or data[key] < 0:
            data[key] = 0
    if not isinstance(data["achievements"], dict):
        data["achievements"] = {}
    scores = []
    if isinstance(data["highscores"], list):
        for e in data["highscores"]:
            if isinstance(e, dict) and isinstance(e.get("score"), int):
                scores.append(e)
    scores.sort(key=lambda e: e["score"], reverse=True)
    data["highscores"] = scores[:10]
    return data


data = _clean(config.load_json(SAVE_FILE, DEFAULT_SAVE))


def save():
    config.save_json(SAVE_FILE, data)


def best():
    """Лучший результат за всё время."""
    return max((e["score"] for e in data["highscores"]), default=0)


def register_game(session, difficulty):
    """Записывает итоги партии. Возвращает (место в таблице или None, побит ли рекорд)."""
    new_best = session.score > best()
    data["games_played"] += 1
    data["enemies_killed"] += session.kills
    data["bosses_killed"] += session.bosses
    data["playtime"] += int(session.time_s)
    rank = None
    if session.score > 0:
        entry = {"score": session.score, "level": session.level, "difficulty": difficulty,
                 "date": time.strftime("%d.%m.%Y")}
        table = data["highscores"]
        table.append(entry)
        table.sort(key=lambda e: e["score"], reverse=True)
        del table[10:]
        for i, e in enumerate(table):
            if e is entry:
                rank = i + 1
    save()
    return rank, new_best


def unlock(achievement_id):
    """Открывает достижение. Возвращает True, если оно получено впервые."""
    if achievement_id in data["achievements"]:
        return False
    data["achievements"][achievement_id] = time.strftime("%d.%m.%Y")
    save()
    return True

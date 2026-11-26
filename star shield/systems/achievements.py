"""Достижения. check() вызывается во время игры и по её окончании."""
from systems import state, steam

IDS = ["first_blood", "hunter", "score_1000", "score_5000", "combo_x5",
       "boss_slayer", "untouchable", "bomber", "collector", "survivor"]


def check(session):
    """Проверяет условия по данным партии. Возвращает список только что открытых достижений."""
    newly = []

    def grant(ach_id, condition):
        if condition and state.unlock(ach_id):
            newly.append(ach_id)

    total_kills = state.data["enemies_killed"] + session.kills
    grant("first_blood", session.kills >= 1)
    grant("hunter", total_kills >= 200)
    grant("score_1000", session.score >= 1000)
    grant("score_5000", session.score >= 5000)
    grant("combo_x5", session.max_mult >= 5)
    grant("boss_slayer", session.bosses >= 1)
    grant("untouchable", session.level >= 4 and session.damage_taken == 0)
    grant("bomber", session.bombs_used >= 1)
    grant("collector", session.bonuses >= 10)
    grant("survivor", session.time_s >= 180)
    for ach_id in newly:
        steam.unlock(ach_id)
    return newly

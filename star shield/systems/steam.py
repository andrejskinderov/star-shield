"""Необязательная интеграция со Steam (достижения).

Работает через библиотеку SteamworksPy (https://github.com/philippj/SteamworksPy).
Если библиотеки или клиента Steam нет, все функции просто ничего не делают,
поэтому игра запускается и без Steam.
"""
_api = None


def init():
    global _api
    try:
        from steamworks import STEAMWORKS  # noqa
        api = STEAMWORKS()
        api.initialize()
        _api = api
    except Exception:  # нет библиотеки, нет Steam, нет steam_appid.txt - не страшно
        _api = None


def available():
    return _api is not None


def unlock(achievement_id):
    """Открывает достижение в Steam. ID в Steamworks: ACH_<ИМЯ> (например ACH_FIRST_BLOOD)."""
    if _api is None:
        return
    try:
        _api.UserStats.SetAchievement(("ACH_" + achievement_id.upper()).encode())
        _api.UserStats.StoreStats()
    except Exception:
        pass


def run_callbacks():
    if _api is None:
        return
    try:
        _api.run_callbacks()
    except Exception:
        pass


def shutdown():
    global _api
    _api = None

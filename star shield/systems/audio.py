"""Звук. Эффекты и музыка создаются программно (никаких внешних файлов не нужно).

Если положить свои файлы menu_music.ogg/.mp3 и game_music.ogg/.mp3 в assets/audio/,
игра будет использовать их вместо сгенерированной музыки.
Если звукового устройства нет, все функции безопасно ничего не делают.
"""
import array
import math
import os
import random

import pygame

from systems import config

_enabled = False
_rate = 44100
_channels = 1
_sounds = {}
_music_cache = {}
_music_sound = None
_current_music = None
_file_music = False

# Частоты нот для музыки (аккорды Am - F - C - G): бас и арпеджио
CHORDS = [
    (110.00, (220.00, 261.63, 329.63)),
    (87.31, (174.61, 220.00, 261.63)),
    (130.81, (261.63, 329.63, 392.00)),
    (98.00, (196.00, 246.94, 293.66)),
]
ARP_ORDER = (0, 1, 2, 1, 0, 1, 2, 1)


def _wave(kind, phase):
    frac = phase % 1.0
    if kind == "square":
        return 1.0 if frac < 0.5 else -1.0
    if kind == "saw":
        return 2.0 * frac - 1.0
    if kind == "tri":
        return 4.0 * abs(frac - 0.5) - 1.0
    if kind == "noise":
        return random.uniform(-1.0, 1.0)
    return math.sin(2 * math.pi * phase)


def _tone(f_start, f_end, duration, volume=0.4, kind="square", power=1.0):
    """Один звук: частота плавно меняется от f_start до f_end, громкость затухает."""
    count = max(1, int(_rate * duration))
    buf = array.array("h")
    phase = 0.0
    for i in range(count):
        p = i / count
        phase += (f_start + (f_end - f_start) * p) / _rate
        envelope = (1.0 - p) ** power
        buf.append(int(_wave(kind, phase) * envelope * volume * 32767))
    return buf


def _mix(a, b):
    n = min(len(a), len(b))
    return array.array("h", (a[i] + b[i] for i in range(n)))


def _to_sound(buf):
    """Превращает массив отсчётов в pygame.mixer.Sound (учитывает моно/стерео)."""
    if _channels == 2:
        stereo = array.array("h")
        for sample in buf:
            stereo.append(sample)
            stereo.append(sample)
        buf = stereo
    return pygame.mixer.Sound(buffer=buf.tobytes())


def _build_sounds():
    explosion = array.array("h")
    for i in range(int(_rate * 0.35)):
        p = i / (_rate * 0.35)
        explosion.append(int(random.uniform(-1, 1) * (1 - p) ** 2 * 0.55 * 32767))
    bomb = array.array("h")
    for i in range(int(_rate * 0.9)):
        p = i / (_rate * 0.9)
        low = math.sin(2 * math.pi * (70 - 40 * p) * i / _rate)
        bomb.append(int((random.uniform(-1, 1) * 0.6 + low * 0.5) * (1 - p) ** 1.5 * 0.6 * 32767))
    sounds = {
        "shoot": _tone(1000, 350, 0.07, 0.18, "square"),
        "explosion": explosion,
        "hit": _tone(260, 60, 0.3, 0.45, "saw"),
        "pickup": _tone(600, 900, 0.07, 0.3, "square", 0.5) + _tone(900, 1300, 0.1, 0.3, "square"),
        "bomb": bomb,
        "boss": _tone(120, 90, 0.35, 0.5, "saw", 0.4) + _tone(120, 90, 0.35, 0.5, "saw", 0.4),
        "levelup": _tone(500, 500, 0.08, 0.3) + _tone(700, 700, 0.08, 0.3) + _tone(1000, 1000, 0.16, 0.3),
        "achievement": _tone(800, 800, 0.08, 0.3, "tri") + _tone(1200, 1200, 0.2, 0.3, "tri"),
        "gameover": _tone(500, 120, 0.9, 0.4, "saw", 0.6),
        "click": _tone(700, 700, 0.03, 0.25, "square"),
    }
    for name, buf in sounds.items():
        _sounds[name] = _to_sound(buf)
    set_sfx_volume(config.settings["sfx"])


def _note(freq, duration, volume, kind):
    return _tone(freq, freq, duration, volume, kind, 0.7)


def _build_music(name):
    """Собирает зацикленную мелодию. 'menu' - спокойная, 'game' - динамичная с басом."""
    step = 0.32 if name == "menu" else 0.19
    kind = "tri" if name == "menu" else "square"
    arp_volume = 0.16 if name == "menu" else 0.10
    track = array.array("h")
    for bass, arp in CHORDS:
        for i in range(8):
            note = _note(arp[ARP_ORDER[i]], step, arp_volume, kind)
            if name == "game":
                note = _mix(note, _note(bass, step, 0.16, "tri"))
            track.extend(note)
    return track


def initialize():
    global _enabled, _rate, _channels
    try:
        pygame.mixer.quit()
        pygame.mixer.init(44100, -16, 1, 512)
        pygame.mixer.set_num_channels(16)
        info = pygame.mixer.get_init()
        if not info or info[1] != -16:
            _enabled = False
            return
        _rate, _channels = info[0], info[2]
        _build_sounds()
        _enabled = True
    except (pygame.error, Exception):
        _enabled = False


def set_sfx_volume(value):
    config.settings["sfx"] = round(max(0.0, min(1.0, value)), 1)
    for sound in _sounds.values():
        sound.set_volume(config.settings["sfx"])


def set_music_volume(value):
    config.settings["music"] = round(max(0.0, min(1.0, value)), 1)
    if not _enabled:
        return
    if _file_music:
        pygame.mixer.music.set_volume(config.settings["music"])
    elif _music_sound is not None:
        _music_sound.set_volume(config.settings["music"])


def play(name):
    """Проигрывает звуковой эффект по имени."""
    if _enabled and name in _sounds:
        _sounds[name].play()


def _find_music_file(name):
    for ext in (".ogg", ".mp3", ".wav"):
        file = config.resource_path("assets", "audio", name + "_music" + ext)
        if os.path.exists(file):
            return file
    return None


def stop_music():
    global _music_sound, _current_music, _file_music
    if _enabled:
        pygame.mixer.music.stop()
        if _music_sound is not None:
            _music_sound.stop()
    _music_sound = None
    _current_music = None
    _file_music = False


def play_music(name):
    """Включает музыку 'menu' или 'game' (если уже играет - ничего не меняет)."""
    global _music_sound, _current_music, _file_music
    if not _enabled or name == _current_music:
        return
    stop_music()
    try:
        file = _find_music_file(name)
        if file:
            pygame.mixer.music.load(file)
            pygame.mixer.music.set_volume(config.settings["music"])
            pygame.mixer.music.play(-1)
            _file_music = True
        else:
            if name not in _music_cache:
                _music_cache[name] = _to_sound(_build_music(name))
            _music_sound = _music_cache[name]
            _music_sound.set_volume(config.settings["music"])
            _music_sound.play(loops=-1)
        _current_music = name
    except pygame.error:
        _current_music = None

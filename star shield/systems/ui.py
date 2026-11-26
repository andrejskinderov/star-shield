"""Общие элементы интерфейса: шрифты, текст, кнопки, полоски, базовый класс экрана."""
import os

import pygame

from systems import config as cfg

FONT_NAMES = "arial,dejavusans,liberationsans,notosans"
_fonts = {}


def get_font(size, bold=False):
    """Шрифт из assets/fonts/game_font.ttf, если он есть, иначе системный."""
    key = (size, bold)
    if key not in _fonts:
        font = None
        file = cfg.resource_path("assets", "fonts", "game_font.ttf")
        if os.path.exists(file):
            try:
                font = pygame.font.Font(file, size)
            except (OSError, pygame.error):
                font = None
        if font is None:
            font = pygame.font.SysFont(FONT_NAMES, size, bold=bold)
        _fonts[key] = font
    return _fonts[key]


def draw_text(surface, text, size, color, center=None, topleft=None, topright=None, bold=False):
    surf = get_font(size, bold).render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = center
    elif topright:
        rect.topright = topright
    elif topleft:
        rect.topleft = topleft
    surface.blit(surf, rect)
    return rect


def draw_bar(surface, rect, ratio, color):
    """Полоска прогресса (здоровье босса, таймеры бонусов)."""
    pygame.draw.rect(surface, (30, 34, 60), rect, border_radius=4)
    fill = rect.copy()
    fill.width = int(rect.width * max(0.0, min(1.0, ratio)))
    if fill.width > 0:
        pygame.draw.rect(surface, color, fill, border_radius=4)
    pygame.draw.rect(surface, cfg.GRAY, rect, 1, border_radius=4)


def draw_ship_icon(surface, center, size, color):
    """Маленький значок корабля (для отображения жизней)."""
    cx, cy = center
    h = size / 2
    points = [(cx, cy - h), (cx + h, cy + h * 0.9), (cx, cy + h * 0.5), (cx - h, cy + h * 0.9)]
    pygame.draw.polygon(surface, color, points)


class Button:
    def __init__(self, label, center, size=(300, 48)):
        self.label = label
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center

    def draw(self, surface, selected):
        color = cfg.GREEN if selected else cfg.GRAY
        pygame.draw.rect(surface, (20, 24, 48), self.rect, border_radius=10)
        pygame.draw.rect(surface, color, self.rect, 3, border_radius=10)
        draw_text(surface, self.label, 24, cfg.WHITE if selected else cfg.GRAY,
                  center=self.rect.center, bold=True)


class Screen:
    """Базовый класс экрана. Чтобы перейти на другой экран, нужно записать
    его имя в self.next ("menu", "game", "settings", "help", "scores",
    "achievements", "credits" или "quit")."""

    def __init__(self, app):
        self.app = app
        self.next = None

    def on_enter(self):
        self.next = None

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass

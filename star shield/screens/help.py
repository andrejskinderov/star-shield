"""Экран «Как играть»."""
import pygame

from systems import config as cfg
from systems.i18n import t
from systems.ui import Screen, draw_text


class HelpScreen(Screen):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.next = "menu"
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.next = "menu"

    def draw(self, surface):
        draw_text(surface, t("help_title"), 42, cfg.BLUE, center=(cfg.WIDTH // 2, 70), bold=True)
        y = 130
        for line in t("help_lines"):
            if line.startswith("#"):
                draw_text(surface, line[1:], 21, cfg.YELLOW, topleft=(40, y), bold=True)
            elif line:
                draw_text(surface, line, 19, cfg.WHITE, topleft=(40, y))
            y += 30
        draw_text(surface, t("esc_back"), 18, cfg.GRAY, center=(cfg.WIDTH // 2, 765))

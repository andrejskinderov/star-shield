"""Титры."""
import pygame

from systems import config as cfg
from systems.i18n import t
from systems.ui import Screen, draw_text


class CreditsScreen(Screen):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.next = "menu"
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.next = "menu"

    def draw(self, surface):
        draw_text(surface, t("credits_title"), 42, cfg.BLUE, center=(cfg.WIDTH // 2, 100), bold=True)
        for i, line in enumerate(t("credits_lines")):
            size = 36 if i == 0 else 22
            color = cfg.YELLOW if i == 0 else cfg.WHITE
            draw_text(surface, line.replace("{v}", cfg.VERSION), size, color,
                      center=(cfg.WIDTH // 2, 220 + i * 46), bold=(i == 0))
        draw_text(surface, t("esc_back"), 18, cfg.GRAY, center=(cfg.WIDTH // 2, 765))

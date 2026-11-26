"""Экран достижений."""
import pygame

from systems import achievements, state
from systems import config as cfg
from systems.i18n import t
from systems.ui import Screen, draw_text


class AchievementsScreen(Screen):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.next = "menu"
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.next = "menu"

    def draw(self, surface):
        got = state.data["achievements"]
        draw_text(surface, t("ach_title"), 42, cfg.BLUE, center=(cfg.WIDTH // 2, 60), bold=True)
        draw_text(surface, f"{len(got)} / {len(achievements.IDS)}", 20, cfg.YELLOW,
                  center=(cfg.WIDTH // 2, 100))
        for i, ach_id in enumerate(achievements.IDS):
            y = 135 + i * 62
            unlocked = ach_id in got
            pygame.draw.rect(surface, (20, 24, 48), (30, y, cfg.WIDTH - 60, 54), border_radius=8)
            pygame.draw.rect(surface, cfg.GREEN if unlocked else (60, 60, 80),
                             (30, y, cfg.WIDTH - 60, 54), 2, border_radius=8)
            draw_text(surface, t("ach_" + ach_id), 22, cfg.WHITE if unlocked else cfg.GRAY,
                      topleft=(48, y + 6), bold=True)
            draw_text(surface, t("ach_" + ach_id + "_d"), 16, cfg.GRAY, topleft=(48, y + 32))
            if unlocked:
                draw_text(surface, got[ach_id], 16, cfg.GREEN, topright=(cfg.WIDTH - 48, y + 8))
        draw_text(surface, t("esc_back"), 18, cfg.GRAY, center=(cfg.WIDTH // 2, 775))

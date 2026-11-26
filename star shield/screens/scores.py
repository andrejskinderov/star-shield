"""Таблица рекордов и общая статистика."""
import pygame

from systems import config as cfg
from systems import state
from systems.i18n import t
from systems.ui import Screen, draw_text


class ScoresScreen(Screen):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.next = "menu"
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.next = "menu"

    def draw(self, surface):
        draw_text(surface, t("scores_title"), 42, cfg.BLUE, center=(cfg.WIDTH // 2, 70), bold=True)
        table = state.data["highscores"]
        if not table:
            draw_text(surface, t("no_scores"), 22, cfg.GRAY, center=(cfg.WIDTH // 2, 300))
        for i, entry in enumerate(table):
            y = 140 + i * 46
            color = cfg.YELLOW if i == 0 else cfg.WHITE
            draw_text(surface, f"{i + 1}.", 26, color, topleft=(50, y), bold=True)
            draw_text(surface, str(entry["score"]), 26, color, topleft=(110, y), bold=True)
            info = f"{t('level')} {entry.get('level', 1)}  {t(entry.get('difficulty', 'normal'))}"
            draw_text(surface, info, 16, cfg.GRAY, topleft=(260, y + 4))
            draw_text(surface, str(entry.get("date", "")), 16, cfg.GRAY, topright=(cfg.WIDTH - 40, y + 4))
        d = state.data
        draw_text(surface, t("stats", games=d["games_played"], kills=d["enemies_killed"],
                             bosses=d["bosses_killed"]), 18, cfg.WHITE,
                  center=(cfg.WIDTH // 2, 680))
        draw_text(surface, t("playtime", minutes=int(d["playtime"] // 60)), 18, cfg.WHITE,
                  center=(cfg.WIDTH // 2, 710))
        draw_text(surface, t("esc_back"), 18, cfg.GRAY, center=(cfg.WIDTH // 2, 765))

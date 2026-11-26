"""Настройки: сложность, язык, громкость, полный экран, тряска. Хранятся в settings.json."""
import pygame

from systems import audio
from systems import config as cfg
from systems.i18n import t
from systems.ui import Screen, draw_text

ROWS = ["difficulty", "language", "music", "sfx", "fullscreen", "shake", "back"]
LANGS = ["ru", "en"]


class SettingsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.selected = 0

    def change(self, direction):
        """direction: -1 (влево) или +1 (вправо)."""
        row = ROWS[self.selected]
        s = cfg.settings
        if row == "difficulty":
            keys = list(cfg.DIFFICULTIES.keys())
            s["difficulty"] = keys[(keys.index(s["difficulty"]) + direction) % len(keys)]
        elif row == "language":
            s["language"] = LANGS[(LANGS.index(s["language"]) + direction) % len(LANGS)]
        elif row == "music":
            audio.set_music_volume(s["music"] + 0.1 * direction)
        elif row == "sfx":
            audio.set_sfx_volume(s["sfx"] + 0.1 * direction)
            audio.play("shoot")
        elif row == "fullscreen":
            self.app.toggle_fullscreen()
        elif row == "shake":
            s["shake"] = not s["shake"]

    def leave(self):
        cfg.save_settings()
        self.next = "menu"

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.leave()
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(ROWS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(ROWS)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.change(-1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.change(1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if ROWS[self.selected] == "back":
                self.leave()
            else:
                self.change(1)

    def value_text(self, row):
        s = cfg.settings
        if row == "difficulty":
            return t(s["difficulty"])
        if row == "language":
            return t("lang_name")
        if row == "music":
            return f"{int(round(s['music'] * 100))}%"
        if row == "sfx":
            return f"{int(round(s['sfx'] * 100))}%"
        if row == "fullscreen":
            return t("on") if s["fullscreen"] else t("off")
        if row == "shake":
            return t("on") if s["shake"] else t("off")
        return ""

    def draw(self, surface):
        draw_text(surface, t("settings_title"), 42, cfg.BLUE, center=(cfg.WIDTH // 2, 110), bold=True)
        for i, row in enumerate(ROWS):
            y = 230 + i * 66
            color = cfg.GREEN if i == self.selected else cfg.WHITE
            label = t("back") if row == "back" else t(row)
            if row == "back":
                draw_text(surface, label, 26, color, center=(cfg.WIDTH // 2, y), bold=True)
                continue
            draw_text(surface, label, 24, color, topleft=(60, y - 14), bold=True)
            draw_text(surface, f"<  {self.value_text(row)}  >", 24, color,
                      center=(cfg.WIDTH - 170, y))
        draw_text(surface, t("settings_hint"), 17, cfg.GRAY, center=(cfg.WIDTH // 2, 750))

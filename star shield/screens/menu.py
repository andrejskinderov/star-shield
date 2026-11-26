"""Главное меню."""
import math

import pygame

from systems import audio, sprites, state
from systems import config as cfg
from systems.i18n import t
from systems.ui import Button, Screen, draw_text

ITEMS = [("menu_play", "game"), ("menu_scores", "scores"), ("menu_ach", "achievements"),
         ("menu_settings", "settings"), ("menu_help", "help"), ("menu_credits", "credits"),
         ("menu_quit", "quit")]


class Menu(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.selected = 0
        self.tick = 0

    def on_enter(self):
        super().on_enter()
        audio.play_music("menu")

    def buttons(self):
        return [Button(t(key), (cfg.WIDTH // 2, 310 + i * 60)) for i, (key, _) in enumerate(ITEMS)]

    def choose(self, index):
        audio.play("click")
        self.next = ITEMS[index][1]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(ITEMS)
                audio.play("click")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(ITEMS)
                audio.play("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.choose(self.selected)
        elif event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons()):
                if button.rect.collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.buttons()):
                if button.rect.collidepoint(event.pos):
                    self.choose(i)

    def update(self):
        self.tick += 1

    def draw_showcase(self, surface):
        """Корабль и пришельцы, плавно покачивающиеся в меню."""
        bob = math.sin(self.tick / 30)
        frame = (self.tick // 18) % 2
        ship = sprites.player()
        surface.blit(ship, ship.get_rect(center=(cfg.WIDTH // 2, 60 + int(4 * bob))))
        decor = (("grunt", 62, 160, 1), ("shooter", cfg.WIDTH - 62, 160, -1),
                 ("zigzag", 62, 740, -1), ("tough", cfg.WIDTH - 62, 735, 1))
        for kind, x, y, sign in decor:
            image = sprites.enemy_frames(kind)[frame]
            surface.blit(image, image.get_rect(center=(x, y + int(6 * bob * sign))))

    def draw(self, surface):
        self.draw_showcase(surface)
        pulse = int(25 * math.sin(self.tick / 25))
        color = (80 + pulse, 160 + pulse, 255)
        draw_text(surface, "STAR SHIELD", 62, color, center=(cfg.WIDTH // 2, 150), bold=True)
        draw_text(surface, t("tagline"), 22, cfg.WHITE, center=(cfg.WIDTH // 2, 215))
        for i, button in enumerate(self.buttons()):
            button.draw(surface, i == self.selected)
        draw_text(surface, f"{t('best')}: {state.best()}", 22, cfg.YELLOW,
                  center=(cfg.WIDTH // 2, 745))
        draw_text(surface, "v" + cfg.VERSION, 16, cfg.GRAY, topleft=(8, cfg.HEIGHT - 24))

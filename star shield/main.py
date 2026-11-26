"""
Star Shield - 2D аркада на PyGame.

Запуск:
    pip install pygame
    python main.py
"""
import os
import sys
import traceback

import pygame

from screens.achievements import AchievementsScreen
from screens.credits import CreditsScreen
from screens.game import GameScreen
from screens.help import HelpScreen
from screens.menu import Menu
from screens.scores import ScoresScreen
from screens.settings import SettingsScreen
from systems import audio, sprites, steam
from systems import config as cfg
from systems.controls import Controls, joy_event_to_key
from systems.entities import Star


def make_icon():
    """Иконка окна: корабль игрока."""
    return pygame.transform.smoothscale(sprites.player(), (32, 38))


class App:
    """Главный класс: окно, фон, переключение экранов, игровой цикл."""

    def __init__(self):
        pygame.init()
        steam.init()
        flags = pygame.SCALED | pygame.RESIZABLE
        if cfg.settings["fullscreen"]:
            flags |= pygame.FULLSCREEN
        self.surface = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT), flags)
        pygame.display.set_caption(cfg.TITLE)
        sprites.preload()
        pygame.display.set_icon(make_icon())
        audio.initialize()
        self.controls = Controls()
        self.clock = pygame.time.Clock()
        self.stars = [Star() for _ in range(80)]
        self.screens = {
            "menu": Menu(self),
            "game": GameScreen(self),
            "settings": SettingsScreen(self),
            "help": HelpScreen(self),
            "scores": ScoresScreen(self),
            "achievements": AchievementsScreen(self),
            "credits": CreditsScreen(self),
        }
        self.current = self.screens["menu"]
        self.current.on_enter()

    def toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()
        cfg.settings["fullscreen"] = not cfg.settings["fullscreen"]

    def switch(self, name):
        if name == "quit":
            self.quit()
        self.current = self.screens[name]
        self.current.on_enter()

    def quit(self):
        cfg.save_settings()
        steam.shutdown()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            elif event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self.controls.refresh()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
            elif event.type in (pygame.JOYHATMOTION, pygame.JOYBUTTONDOWN):
                key = joy_event_to_key(event)
                if key is not None:
                    self.current.handle_event(
                        pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0))
            else:
                self.current.handle_event(event)

    def run(self):
        while True:
            self.clock.tick(cfg.FPS)
            self.handle_events()
            steam.run_callbacks()
            self.current.update()

            self.surface.fill(cfg.BLACK)
            for star in self.stars:
                star.update()
                star.draw(self.surface)
            self.current.draw(self.surface)
            pygame.display.flip()

            if self.current.next:
                self.switch(self.current.next)


def main():
    try:
        App().run()
    except SystemExit:
        raise
    except Exception:
        # при сбое пишем отчёт в папку сохранений, чтобы игрок мог его прислать
        try:
            with open(os.path.join(cfg.user_dir(), "crash.log"), "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except OSError:
            pass
        raise


if __name__ == "__main__":
    main()

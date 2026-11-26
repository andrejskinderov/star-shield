"""Визуальные эффекты: частицы взрывов и всплывающий текст."""
import math
import random

import pygame

from systems.ui import draw_text


class Particles:
    """Набор частиц. Каждая частица: x, y, vx, vy, жизнь, макс. жизнь, цвет, размер."""

    def __init__(self):
        self.items = []

    def burst(self, x, y, color, count=14, speed=4.0, size=4):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            v = random.uniform(0.4, 1.0) * speed
            life = random.randint(20, 40)
            self.items.append([x, y, math.cos(angle) * v, math.sin(angle) * v,
                               life, life, color, size])

    def update(self):
        for p in self.items:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.96
            p[3] *= 0.96
            p[4] -= 1
        self.items = [p for p in self.items if p[4] > 0]

    def draw(self, surface):
        for x, y, _, _, life, max_life, color, size in self.items:
            radius = max(1, int(size * life / max_life))
            pygame.draw.circle(surface, color, (int(x), int(y)), radius)


class FloatingText:
    """Текст, который поднимается вверх и исчезает (очки, названия бонусов)."""

    def __init__(self, text, x, y, color, life=45, size=18):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life = life
        self.size = size

    @property
    def alive(self):
        return self.life > 0

    def update(self):
        self.y -= 0.8
        self.life -= 1

    def draw(self, surface):
        draw_text(surface, self.text, self.size, self.color,
                  center=(int(self.x), int(self.y)), bold=True)

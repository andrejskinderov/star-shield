"""Игровые объекты: звезда фона, игрок, пуля, враги, босс, бонусы."""
import math
import random

import pygame

from systems import config as cfg
from systems import sprites


class Star:
    """Звезда для движущегося фона (чем быстрее, тем ближе и крупнее)."""

    def __init__(self):
        self.x = random.randint(0, cfg.WIDTH)
        self.y = random.randint(0, cfg.HEIGHT)
        self.speed = random.uniform(0.5, 3)
        self.size = 1 if self.speed < 1.8 else 2

    def update(self):
        self.y += self.speed
        if self.y > cfg.HEIGHT:
            self.y = 0
            self.x = random.randint(0, cfg.WIDTH)

    def draw(self, surface):
        pygame.draw.circle(surface, cfg.GRAY, (int(self.x), int(self.y)), self.size)


class Bullet(pygame.sprite.Sprite):
    """Пуля: своя (плазменный снаряд) или вражеская (красный шар)."""

    def __init__(self, x, y, vx, vy, enemy=False):
        super().__init__()
        image = sprites.bullet(enemy)
        if not enemy and vx:
            # косые пули повёрнуты по направлению полёта
            angle = math.degrees(math.atan2(vx, -vy))
            image = pygame.transform.rotate(image, -angle)
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.fx, self.fy = float(x), float(y)
        self.vx, self.vy = vx, vy

    def update(self, now=0):
        self.fx += self.vx
        self.fy += self.vy
        self.rect.center = (int(self.fx), int(self.fy))
        if (self.rect.bottom < -20 or self.rect.top > cfg.HEIGHT + 20
                or self.rect.right < -20 or self.rect.left > cfg.WIDTH + 20):
            self.kill()


class Player(pygame.sprite.Sprite):
    """Корабль игрока: оружие 1-3 уровня, бомбы, щит, скорострельность."""

    def __init__(self, lives, bombs):
        super().__init__()
        self.image = sprites.player()
        self.rect = self.image.get_rect(midbottom=(cfg.WIDTH // 2, cfg.HEIGHT - 20))
        self.speed = 6
        self.lives = lives
        self.max_lives = max(5, lives)
        self.bombs = bombs
        self.weapon = 1
        self.last_shot = -1000
        self.shield_until = 0
        self.rapid_until = 0
        self.invuln_until = 0

    def shield_active(self, now):
        return now < self.shield_until

    def update(self, move):
        self.rect.x += int(move * self.speed)
        self.rect.clamp_ip(pygame.Rect(0, 0, cfg.WIDTH, cfg.HEIGHT))

    def shoot(self, now, bullets):
        """Стреляет, если прошла пауза. Возвращает True при выстреле."""
        delay = 130 if now < self.rapid_until else 280
        if now - self.last_shot < delay:
            return False
        self.last_shot = now
        cx, top = self.rect.centerx, self.rect.top
        if self.weapon == 1:
            bullets.add(Bullet(cx, top, 0, -11))
        elif self.weapon == 2:
            bullets.add(Bullet(cx - 16, top + 14, 0, -11), Bullet(cx + 16, top + 14, 0, -11))
        else:
            bullets.add(Bullet(cx, top, 0, -11),
                        Bullet(cx - 20, top + 24, -2.2, -10.5),
                        Bullet(cx + 20, top + 24, 2.2, -10.5))
        return True


def _flash_copy(image):
    """Светлая копия картинки: показывается на миг при попадании."""
    flash = image.copy()
    flash.fill((110, 110, 110, 0), special_flags=pygame.BLEND_RGB_ADD)
    return flash


_flash_cache = {}


def _flash_frames(key, frames):
    """Кадры вспышки считаем один раз на вид врага."""
    if key not in _flash_cache:
        _flash_cache[key] = [_flash_copy(f) for f in frames]
    return _flash_cache[key]


class Enemy(pygame.sprite.Sprite):
    """Враг. Виды: grunt (обычный), zigzag (быстрый), tough (прочный), shooter (стреляет)."""

    KINDS = {
        "grunt": {"hp": 1, "points": 10, "color": cfg.RED, "speed": 1.0, "sway": 30,
                  "rate": 40, "shoots": False, "drop": 0.10},
        "zigzag": {"hp": 1, "points": 15, "color": cfg.PURPLE, "speed": 1.4, "sway": 90,
                   "rate": 30, "shoots": False, "drop": 0.10},
        "tough": {"hp": 3, "points": 25, "color": cfg.ORANGE, "speed": 0.8, "sway": 20,
                  "rate": 50, "shoots": False, "drop": 0.25},
        "shooter": {"hp": 2, "points": 30, "color": cfg.CYAN, "speed": 0.7, "sway": 40,
                    "rate": 45, "shoots": True, "drop": 0.25},
    }

    def __init__(self, kind, level, speed_mul, now):
        super().__init__()
        spec = self.KINDS[kind]
        self.kind = kind
        self.hp = spec["hp"]
        self.points = spec["points"]
        self.color = spec["color"]
        self.shoots = spec["shoots"]
        self.drop_chance = spec["drop"]
        self.sway = spec["sway"]
        self.sway_rate = spec["rate"]
        self.frames = sprites.enemy_frames(kind)
        self.flash_frames = _flash_frames(("enemy", kind), self.frames)
        self.anim_offset = random.random() * 2
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=(random.randint(40, cfg.WIDTH - 40), 0))
        self.speed = (1.4 + min(level, 12) * 0.25) * spec["speed"] * speed_mul
        self.base_x = self.rect.centerx
        self.phase = random.uniform(0, 6.28)
        self.y_float = float(self.rect.y)
        self.flash_until = 0
        self.next_shot = now + random.randint(800, 1800)

    def hit(self, now):
        self.flash_until = now + 90

    def ready_to_shoot(self, now):
        """True, если пришло время выстрела (и враг уже виден, но ещё высоко)."""
        if not self.shoots or now < self.next_shot:
            return False
        if self.rect.bottom < 0 or self.rect.top > cfg.HEIGHT * 0.6:
            return False
        self.next_shot = now + random.randint(1400, 2600)
        return True

    def update(self, now=0):
        self.y_float += self.speed
        self.rect.y = int(self.y_float)
        x = self.base_x + self.sway * math.sin(self.y_float / self.sway_rate + self.phase)
        self.rect.centerx = int(max(25, min(cfg.WIDTH - 25, x)))
        index = int(now / 140 + self.anim_offset) % len(self.frames)
        frames = self.flash_frames if now < self.flash_until else self.frames
        self.image = frames[index]


class Boss(pygame.sprite.Sprite):
    """Босс: выезжает сверху, качается из стороны в сторону, стреляет веером и прицельно."""

    def __init__(self, level, now):
        super().__init__()
        self.max_hp = 30 + level * 6
        self.hp = self.max_hp
        self.frames = sprites.boss_frames()
        self.flash_frames = _flash_frames("boss", self.frames)
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=(cfg.WIDTH // 2, 0))
        self.flash_until = 0
        self.next_spread = now + 1800
        self.next_aim = now + 2600

    def hit(self, now):
        self.flash_until = now + 80

    def update(self, now=0):
        if self.rect.centery < 120:
            self.rect.centery += 2
        else:
            self.rect.centerx = cfg.WIDTH // 2 + int(170 * math.sin(now / 1100))
        index = int(now / 400) % len(self.frames)
        frames = self.flash_frames if now < self.flash_until else self.frames
        self.image = frames[index]

    def attack(self, now, target):
        """Возвращает список выстрелов (x, y, vx, vy). До выезда на позицию не стреляет."""
        shots = []
        if self.rect.centery < 120:
            return shots
        x, y = self.rect.centerx, self.rect.bottom - 10
        enraged = self.hp <= self.max_hp / 2
        if now >= self.next_spread:
            self.next_spread = now + (1100 if enraged else 1600)
            for i in range(-2, 3):
                shots.append((x, y, i * 1.3, 4.0))
        if enraged and now >= self.next_aim:
            self.next_aim = now + 900
            dx, dy = target[0] - x, target[1] - y
            dist = math.hypot(dx, dy) or 1.0
            shots.append((x, y, dx / dist * 5.0, dy / dist * 5.0))
        return shots


class Bonus(pygame.sprite.Sprite):
    """Бонус: S - щит, R - скорострельность, + - жизнь, W - оружие, B - бомба."""

    COLORS = sprites.BONUS_COLORS
    WEIGHTS = {"shield": 25, "rapid": 25, "weapon": 20, "bomb": 15, "life": 15}

    def __init__(self, center, kind, font):
        super().__init__()
        self.kind = kind
        self.image = sprites.bonus(kind, font)
        self.rect = self.image.get_rect(center=center)

    def update(self, now=0):
        self.rect.y += 3
        if self.rect.top > cfg.HEIGHT:
            self.kill()

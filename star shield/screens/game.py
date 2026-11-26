"""Игровой экран: волны врагов, боссы, бонусы, комбо, бомбы, эффекты."""
import math
import random

import pygame

from systems import achievements, audio, sprites, state
from systems import config as cfg
from systems.effects import FloatingText, Particles
from systems.entities import Bonus, Boss, Bullet, Enemy, Player
from systems.i18n import t
from systems.ui import Button, Screen, draw_bar, draw_ship_icon, draw_text, get_font

PLAY, PAUSE, OVER = "play", "pause", "over"
FRAME_MS = 1000 / cfg.FPS   # игровое время идёт кадрами, поэтому пауза замораживает всё
LEVEL_STEP = 250            # очков на уровень
BOSS_EVERY = 5              # босс каждые 5 уровней
MAX_BOMBS = 5
HITBOX = pygame.sprite.collide_rect_ratio(0.65)   # попадания считаются по уменьшенному контуру


class Session:
    """Статистика одной партии (для достижений и таблицы рекордов)."""

    def __init__(self):
        self.score = 0
        self.level = 1
        self.kills = 0
        self.bosses = 0
        self.max_mult = 1
        self.damage_taken = 0
        self.bombs_used = 0
        self.bonuses = 0
        self.time_s = 0.0


class GameScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.canvas = pygame.Surface((cfg.WIDTH, cfg.HEIGHT), pygame.SRCALPHA)
        self.flash_surface = pygame.Surface((cfg.WIDTH, cfg.HEIGHT))
        self.flash_surface.fill(cfg.WHITE)
        self.dim = pygame.Surface((cfg.WIDTH, cfg.HEIGHT))
        self.dim.set_alpha(150)
        self.reset()

    def reset(self):
        """Начинает новую партию с учётом выбранной сложности."""
        self.diff_key = cfg.difficulty_key()
        self.diff = cfg.DIFFICULTIES[self.diff_key]
        self.session = Session()
        self.player = Player(self.diff["lives"], self.diff["bombs"])
        self.player.invuln_until = 1500
        self.players = pygame.sprite.GroupSingle(self.player)
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bosses = pygame.sprite.Group()
        self.bonuses = pygame.sprite.Group()
        self.particles = Particles()
        self.texts = []
        self.toasts = []
        self.now = 0.0
        self.frame = 0
        self.last_spawn = 0.0
        self.combo = 0
        self.combo_until = 0.0
        self.mult = 1
        self.shake = 0.0
        self.flash = 0
        self.mode = PLAY
        self.pause_sel = 0
        self.rank = None
        self.new_best = False
        self.registered = False
        self.boss_level_done = 0
        self.last_level = 1

    def on_enter(self):
        super().on_enter()
        self.reset()
        audio.play_music("game")

    # -------------------------------------------------------------- события
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        key = event.key
        if self.mode == PLAY:
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.mode = PAUSE
                self.pause_sel = 0
            elif key in (pygame.K_b, pygame.K_x):
                self.use_bomb()
        elif self.mode == PAUSE:
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.mode = PLAY
            elif key in (pygame.K_UP, pygame.K_w):
                self.pause_sel = (self.pause_sel - 1) % 2
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.pause_sel = (self.pause_sel + 1) % 2
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.pause_sel == 0:
                    self.mode = PLAY
                else:
                    self.end_game()
                    self.next = "menu"
        elif self.mode == OVER:
            if key == pygame.K_RETURN:
                self.reset()
                audio.play("click")
            elif key == pygame.K_ESCAPE:
                self.next = "menu"

    # --------------------------------------------------------------- логика
    def update(self):
        if self.mode == OVER:
            self.particles.update()
            self.shake *= 0.88
            return
        if self.mode != PLAY:
            return

        self.now += FRAME_MS
        self.frame += 1
        now = self.now
        s = self.session
        s.time_s = now / 1000
        s.level = 1 + s.score // LEVEL_STEP

        keys = pygame.key.get_pressed()
        controls = self.app.controls
        self.player.update(controls.move(keys))
        if controls.shooting(keys) and self.player.shoot(now, self.bullets):
            audio.play("shoot")

        self.bullets.update(now)
        self.enemy_bullets.update(now)
        self.enemies.update(now)
        self.bosses.update(now)
        self.bonuses.update(now)

        self.spawn_enemies(now)
        self.handle_boss(now)
        self.enemy_fire(now)
        self.check_collisions(now)

        self.particles.update()
        for text in self.texts:
            text.update()
        self.texts = [x for x in self.texts if x.alive]
        self.toasts = [x for x in self.toasts if now < x["until"]]
        if now > self.combo_until:
            self.combo = 0
            self.mult = 1
        self.shake *= 0.88
        self.flash = max(0, self.flash - 1)

        s.level = 1 + s.score // LEVEL_STEP
        if s.level > self.last_level:
            self.last_level = s.level
            self.add_toast(t("level_up", n=s.level), cfg.GREEN, 1500, 34)
            audio.play("levelup")
        if self.frame % 30 == 0:
            self.check_achievements()

        if self.player.lives <= 0:
            self.player_destroyed()

    def spawn_enemies(self, now):
        level = self.session.level
        delay = max(260, int((1050 - level * 60) * self.diff["spawn"]))
        if len(self.bosses) > 0:
            delay *= 3
        if now - self.last_spawn <= delay:
            return
        self.last_spawn = now
        kinds, weights = ["grunt"], [10]
        if level >= 2:
            kinds.append("zigzag")
            weights.append(4)
        if level >= 3:
            kinds.append("tough")
            weights.append(3)
        if level >= 4:
            kinds.append("shooter")
            weights.append(3)
        kind = random.choices(kinds, weights)[0]
        self.enemies.add(Enemy(kind, level, self.diff["speed"], now))

    def handle_boss(self, now):
        level = self.session.level
        if level % BOSS_EVERY == 0 and level != self.boss_level_done and len(self.bosses) == 0:
            self.boss_level_done = level
            self.bosses.add(Boss(level, now))
            self.add_toast(t("boss_warning"), cfg.RED, 2500, 40)
            audio.play("boss")

    def enemy_fire(self, now):
        px, py = self.player.rect.center
        for enemy in self.enemies:
            if enemy.ready_to_shoot(now):
                x, y = enemy.rect.centerx, enemy.rect.bottom
                dx, dy = px - x, py - y
                dist = math.hypot(dx, dy) or 1.0
                self.enemy_bullets.add(Bullet(x, y, dx / dist * 4.2, dy / dist * 4.2, enemy=True))
        for boss in self.bosses:
            for x, y, vx, vy in boss.attack(now, (px, py)):
                self.enemy_bullets.add(Bullet(x, y, vx, vy, enemy=True))

    def check_collisions(self, now):
        # 1) наши пули попадают во врагов
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, False, True)
        for enemy, bullet_list in hits.items():
            enemy.hp -= len(bullet_list)
            enemy.hit(now)
            if enemy.hp <= 0:
                self.register_kill(enemy, now)

        # 2) наши пули попадают в босса
        hits = pygame.sprite.groupcollide(self.bosses, self.bullets, False, True)
        for boss, bullet_list in hits.items():
            self.hit_boss(boss, len(bullet_list), now)

        # 3) вражеские пули попадают в игрока
        if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, HITBOX):
            self.damage_player(now)

        # 4) враг врезался в корабль
        for enemy in pygame.sprite.spritecollide(self.player, self.enemies, True, HITBOX):
            self.particles.burst(enemy.rect.centerx, enemy.rect.centery, enemy.color)
            audio.play("explosion")
            self.damage_player(now)
        if pygame.sprite.spritecollide(self.player, self.bosses, False, HITBOX):
            self.damage_player(now)

        # 5) враг прорвался к нижнему краю (щит от этого не спасает)
        for enemy in list(self.enemies):
            if enemy.rect.top > cfg.HEIGHT:
                enemy.kill()
                self.damage_player(now, breach=True)

        # 6) подбор бонусов
        for bonus in pygame.sprite.spritecollide(self.player, self.bonuses, True):
            self.apply_bonus(bonus, now)

    def register_kill(self, enemy, now):
        """Уничтожение врага: комбо, очки, эффекты, шанс бонуса."""
        s = self.session
        self.combo = self.combo + 1 if now < self.combo_until else 1
        self.combo_until = now + 2000
        self.mult = 1 + min(self.combo // 5, 4)
        s.max_mult = max(s.max_mult, self.mult)
        gain = enemy.points * self.mult
        s.score += gain
        s.kills += 1
        x, y = enemy.rect.center
        self.texts.append(FloatingText(f"+{gain}", x, y, enemy.color))
        self.particles.burst(x, y, enemy.color)
        audio.play("explosion")
        if random.random() < enemy.drop_chance:
            self.drop_bonus((x, y))
        enemy.kill()

    def hit_boss(self, boss, damage, now):
        boss.hp -= damage
        boss.hit(now)
        if boss.hp > 0:
            return
        s = self.session
        s.score += 500
        s.bosses += 1
        x, y = boss.rect.center
        for _ in range(6):
            self.particles.burst(x + random.randint(-60, 60), y + random.randint(-30, 30),
                                 random.choice([cfg.PURPLE, cfg.ORANGE, cfg.YELLOW]), 20, 6, 6)
        self.texts.append(FloatingText("+500", x, y, cfg.YELLOW, 70, 30))
        self.add_toast(t("boss_defeated"), cfg.YELLOW, 2500, 36)
        self.shake = max(self.shake, 20)
        self.flash = 18
        self.enemy_bullets.empty()
        self.drop_bonus((x - 30, y), "weapon")
        self.drop_bonus((x + 30, y), "bomb")
        audio.play("bomb")
        boss.kill()

    def drop_bonus(self, center, kind=None):
        if kind is None:
            kind = random.choices(list(Bonus.WEIGHTS), list(Bonus.WEIGHTS.values()))[0]
        self.bonuses.add(Bonus(center, kind, get_font(18, True)))

    def apply_bonus(self, bonus, now):
        p = self.player
        self.session.bonuses += 1
        audio.play("pickup")
        if bonus.kind == "shield":
            p.shield_until = now + 5000
        elif bonus.kind == "rapid":
            p.rapid_until = now + 6000
        elif bonus.kind == "life":
            p.lives = min(p.max_lives, p.lives + 1)
        elif bonus.kind == "weapon":
            p.weapon = min(3, p.weapon + 1)
        elif bonus.kind == "bomb":
            p.bombs = min(MAX_BOMBS, p.bombs + 1)
        self.texts.append(FloatingText(t("bonus_" + bonus.kind), p.rect.centerx,
                                       p.rect.top - 10, Bonus.COLORS[bonus.kind], 50, 20))

    def damage_player(self, now, breach=False):
        p = self.player
        if now < p.invuln_until:
            return
        if p.shield_active(now) and not breach:
            self.particles.burst(p.rect.centerx, p.rect.centery, cfg.GREEN, 10, 3)
            return
        p.lives -= 1
        p.weapon = max(1, p.weapon - 1)
        p.invuln_until = now + 2000
        self.session.damage_taken += 1
        self.combo = 0
        self.mult = 1
        self.shake = max(self.shake, 10)
        self.particles.burst(p.rect.centerx, p.rect.centery, cfg.BLUE, 16, 4)
        audio.play("hit")

    def use_bomb(self):
        p = self.player
        if self.mode != PLAY or p.bombs <= 0:
            return
        p.bombs -= 1
        self.session.bombs_used += 1
        self.flash = 14
        self.shake = max(self.shake, 14)
        audio.play("bomb")
        self.enemy_bullets.empty()
        for enemy in list(self.enemies):
            self.register_kill(enemy, self.now)
        for boss in list(self.bosses):
            self.hit_boss(boss, 12, self.now)

    def player_destroyed(self):
        p = self.player
        for _ in range(4):
            self.particles.burst(p.rect.centerx, p.rect.centery,
                                 random.choice([cfg.BLUE, cfg.WHITE, cfg.ORANGE]), 24, 6, 6)
        self.shake = 18
        audio.play("explosion")
        audio.play("gameover")
        self.end_game()
        self.mode = OVER

    def end_game(self):
        """Один раз записывает итоги партии (рекорды, статистика, достижения)."""
        if self.registered:
            return
        self.registered = True
        self.check_achievements()
        self.rank, self.new_best = state.register_game(self.session, self.diff_key)

    def check_achievements(self):
        for ach_id in achievements.check(self.session):
            self.add_toast(f"{t('ach_unlocked')}: {t('ach_' + ach_id)}", cfg.YELLOW, 3500, 22)
            audio.play("achievement")

    def add_toast(self, text, color, duration=2000, size=28):
        self.toasts.append({"text": text, "color": color, "until": self.now + duration,
                            "size": size})

    # ----------------------------------------------------------- отрисовка
    def draw(self, surface):
        now = self.now
        canvas = self.canvas
        canvas.fill((0, 0, 0, 0))
        self.bonuses.draw(canvas)
        self.enemies.draw(canvas)
        self.bosses.draw(canvas)
        self.bullets.draw(canvas)
        self.enemy_bullets.draw(canvas)
        if self.mode != OVER:
            self.draw_player(canvas, now)
        self.particles.draw(canvas)

        ox = oy = 0
        if cfg.settings["shake"] and self.shake > 0.5:
            amount = int(self.shake)
            ox, oy = random.randint(-amount, amount), random.randint(-amount, amount)
        surface.blit(canvas, (ox, oy))

        for text in self.texts:
            text.draw(surface)
        if self.flash > 0:
            self.flash_surface.set_alpha(min(200, self.flash * 14))
            surface.blit(self.flash_surface, (0, 0))
        self.draw_hud(surface, now)
        for i, toast in enumerate(self.toasts):
            draw_text(surface, toast["text"], toast["size"], toast["color"],
                      center=(cfg.WIDTH // 2, 190 + i * 44), bold=True)

        if self.mode == PAUSE:
            surface.blit(self.dim, (0, 0))
            draw_text(surface, t("paused"), 56, cfg.WHITE, center=(cfg.WIDTH // 2, 280), bold=True)
            for i, key in enumerate(("resume", "to_menu")):
                Button(t(key), (cfg.WIDTH // 2, 380 + i * 70)).draw(surface, i == self.pause_sel)
        elif self.mode == OVER:
            surface.blit(self.dim, (0, 0))
            self.draw_game_over(surface)

    def draw_player(self, canvas, now):
        p = self.player
        if now < p.invuln_until and int(now / 100) % 2 == 0:
            return
        flame = sprites.flame(int(now / 50))
        for dx in (-10, 10):                       # пламя двигателей (за кораблём)
            canvas.blit(flame, (p.rect.centerx + dx - flame.get_width() // 2, p.rect.bottom - 8))
        self.players.draw(canvas)
        if p.shield_active(now):
            bubble = sprites.shield()
            bubble.set_alpha(190 + int(50 * math.sin(now / 90)))
            canvas.blit(bubble, bubble.get_rect(center=p.rect.center))

    def draw_hud(self, surface, now):
        s, p = self.session, self.player
        draw_text(surface, f"{t('score')}: {s.score}", 26, cfg.WHITE, topleft=(10, 8), bold=True)
        draw_text(surface, f"{t('level')}: {s.level}", 20, cfg.GRAY, topleft=(10, 40))
        draw_text(surface, f"{t('best')}: {max(state.best(), s.score)}", 20, cfg.YELLOW,
                  topright=(cfg.WIDTH - 10, 8))
        for i in range(p.lives):
            draw_ship_icon(surface, (cfg.WIDTH - 22 - i * 26, 50), 20, cfg.BLUE)
        for i in range(p.bombs):
            pygame.draw.circle(surface, cfg.ORANGE, (cfg.WIDTH - 22 - i * 26, 78), 8)
            pygame.draw.circle(surface, cfg.WHITE, (cfg.WIDTH - 22 - i * 26, 78), 8, 1)
        draw_text(surface, f"{t('weapon')} {p.weapon}", 18, cfg.BLUE, topleft=(10, cfg.HEIGHT - 28))
        if self.combo >= 2:
            draw_text(surface, f"{t('combo')} x{self.mult}  ({self.combo})", 22, cfg.ORANGE,
                      center=(cfg.WIDTH // 2, 36), bold=True)
            draw_bar(surface, pygame.Rect(cfg.WIDTH // 2 - 60, 54, 120, 6),
                     (self.combo_until - now) / 2000, cfg.ORANGE)
        if p.shield_active(now):
            draw_bar(surface, pygame.Rect(cfg.WIDTH - 130, cfg.HEIGHT - 40, 120, 8),
                     (p.shield_until - now) / 5000, cfg.GREEN)
        if now < p.rapid_until:
            draw_bar(surface, pygame.Rect(cfg.WIDTH - 130, cfg.HEIGHT - 24, 120, 8),
                     (p.rapid_until - now) / 6000, cfg.YELLOW)
        for boss in self.bosses:
            draw_bar(surface, pygame.Rect(cfg.WIDTH // 2 - 180, 96, 360, 12),
                     boss.hp / boss.max_hp, cfg.RED)

    def draw_game_over(self, surface):
        c = cfg.WIDTH // 2
        draw_text(surface, t("game_over"), 60, cfg.RED, center=(c, 270), bold=True)
        draw_text(surface, t("your_score", score=self.session.score), 30, cfg.WHITE, center=(c, 350))
        draw_text(surface, t("kills", kills=self.session.kills), 22, cfg.GRAY, center=(c, 395))
        if self.new_best:
            draw_text(surface, t("new_record"), 32, cfg.YELLOW, center=(c, 450), bold=True)
        elif self.rank:
            draw_text(surface, t("rank", rank=self.rank), 24, cfg.YELLOW, center=(c, 450))
        draw_text(surface, t("retry_hint"), 24, cfg.GREEN, center=(c, 530))

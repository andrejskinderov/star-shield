"""Графика игры: корабль, пришельцы, босс, бонусы, пули, пламя, щит.

Всё рисуется кодом. Для гладких краёв каждая модель рисуется в 3-4 раза крупнее
и уменьшается (сглаживание). Заливки - с градиентами, плюс свечение и блики.
Готовые картинки кэшируются: preload() создаёт их заранее при запуске.
"""
import math

import pygame

_cache = {}


def _rgba(c):
    return tuple(c) + ((255,) if len(c) == 3 else ())


def _gradient(size, top, bottom):
    """Вертикальный градиент (поддерживает прозрачность в цвете)."""
    w, h = size
    top, bottom = _rgba(top), _rgba(bottom)
    g = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(h):
        t = y / max(1, h - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(4))
        pygame.draw.line(g, color, (0, y), (w, y))
    return g


def mir(points, cx):
    """Отражает точки относительно вертикали x = cx."""
    return [(2 * cx - x, y) for x, y in points]


def sym(right, cx):
    """Правая половина контура (от оси до оси) -> полный симметричный контур."""
    return right + list(reversed(mir(right, cx)))


class Canvas:
    """Холст для рисования модели в крупном масштабе с последующим уменьшением."""

    def __init__(self, w, h, scale=4):
        self.w, self.h, self.s = w, h, scale
        self.surf = pygame.Surface((w * scale, h * scale), pygame.SRCALPHA)

    def _pts(self, pts):
        return [(int(x * self.s), int(y * self.s)) for x, y in pts]

    def _masked(self, box, mask_draw, top, bottom):
        x0, y0, x1, y1 = box
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(self.surf.get_width(), x1), min(self.surf.get_height(), y1)
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0:
            return
        layer = _gradient((w, h), top, bottom or top)
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        mask_draw(mask, x0, y0)
        layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.surf.blit(layer, (x0, y0))

    def poly(self, pts, top, bottom=None, outline=None, width=1.2):
        """Многоугольник с градиентом сверху вниз и тёмной обводкой."""
        p = self._pts(pts)
        xs, ys = [q[0] for q in p], [q[1] for q in p]

        def mask_draw(mask, x0, y0):
            pygame.draw.polygon(mask, (255, 255, 255, 255), [(x - x0, y - y0) for x, y in p])

        self._masked((min(xs), min(ys), max(xs) + 1, max(ys) + 1), mask_draw, top, bottom)
        if outline:
            pygame.draw.polygon(self.surf, _rgba(outline), p, max(1, int(width * self.s)))

    def ellipse(self, rect, top, bottom=None, outline=None, width=1.0):
        x, y, w, h = [int(v * self.s) for v in rect]

        def mask_draw(mask, x0, y0):
            pygame.draw.ellipse(mask, (255, 255, 255, 255), (x - x0, y - y0, w, h))

        self._masked((x, y, x + w + 1, y + h + 1), mask_draw, top, bottom)
        if outline:
            pygame.draw.ellipse(self.surf, _rgba(outline), (x, y, w, h),
                                max(1, int(width * self.s)))

    def glow(self, center, radius, color, strength=0.6):
        """Мягкое светящееся пятно."""
        r = int(radius * self.s)
        tmp = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        steps = 16
        for i in range(steps):
            rr = max(1, int(r * (1 - i / steps)))
            alpha = int(255 * strength * ((i + 1) / steps) ** 2)
            pygame.draw.circle(tmp, tuple(color[:3]) + (alpha,), (r, r), rr)
        self.surf.blit(tmp, (int(center[0] * self.s) - r, int(center[1] * self.s) - r))

    def line(self, a, b, color, width=1.0):
        pygame.draw.line(self.surf, _rgba(color), self._pts([a])[0], self._pts([b])[0],
                         max(1, int(width * self.s)))

    def done(self):
        out = pygame.transform.smoothscale(self.surf, (self.w, self.h))
        return out.convert_alpha()


# ------------------------------------------------------------------ корабль
def _build_player():
    cv = Canvas(64, 76)
    for x in (22, 42):                                    # двигатели
        cv.ellipse((x - 5, 54, 10, 20), (150, 160, 180), (45, 50, 75), (15, 20, 40))
        cv.glow((x, 72), 8, (90, 210, 255), 0.8)
    wing = [(32, 22), (40, 28), (61, 52), (63, 66), (52, 64), (40, 58), (32, 60)]
    cv.poly(sym(wing, 32), (120, 180, 255), (25, 55, 150), (12, 20, 55), 1.3)
    stripe = [(42, 35), (58, 55), (58, 60), (42, 43)]    # красные полосы на крыльях
    for pts in (stripe, mir(stripe, 32)):
        cv.poly(pts, (255, 130, 95), (205, 45, 55))
    for pts in ([(44, 46), (52, 58)], [(20, 46), (12, 58)]):
        cv.line(pts[0], pts[1], (20, 35, 90), 0.8)       # линии обшивки
    for x in (8, 56):                                     # пушки на крыльях
        cv.poly([(x - 2, 38), (x + 2, 38), (x + 2, 58), (x - 2, 58)], (170, 175, 190),
                (50, 55, 75), (15, 20, 40), 0.8)
        cv.glow((x, 38), 4, (255, 230, 120), 0.7)
    body = [(32, 1), (36, 12), (38, 32), (37, 54), (34, 66), (32, 68)]
    cv.poly(sym(body, 32), (240, 247, 255), (85, 125, 200), (15, 25, 60), 1.3)
    cv.line((32, 12), (32, 62), (70, 100, 160), 0.7)
    cv.ellipse((27, 18, 10, 22), (205, 255, 255), (30, 115, 205), (10, 30, 70), 0.9)  # кабина
    cv.ellipse((29, 20, 3.5, 9), (255, 255, 255), (210, 240, 255))
    cv.glow((32, 4), 6, (255, 255, 255), 0.5)
    return cv.done()


def _build_flame(frame):
    length = (22, 29, 25, 31)[frame % 4]
    cv = Canvas(14, 34)
    outer = [(7, 0), (12, 4), (11, 10), (9, length - 4), (7, length), (5, length - 4),
             (3, 10), (2, 4)]
    cv.poly(outer, (255, 215, 120, 255), (255, 80, 30, 0))
    middle = [(7, 0), (10, 5), (9, 11), (7, length - 7), (5, 11), (4, 5)]
    cv.poly(middle, (255, 255, 220, 255), (255, 200, 90, 0))
    inner = [(7, 0), (9, 5), (7, length - 12), (5, 5)]
    cv.poly(inner, (255, 255, 255, 255), (190, 240, 255, 0))
    return cv.done()


def _build_shield():
    size = 104
    cv = Canvas(size, size, 3)
    cx = cy = size * 3 // 2
    for i in range(16):                    # заливка: прозрачная в центре, плотнее к краю
        r = int((50 - i * 2.2) * 3)
        pygame.draw.circle(cv.surf, (90, 255, 170, max(4, 52 - i * 3)), (cx, cy), max(1, r))
    pygame.draw.circle(cv.surf, (150, 255, 205, 235), (cx, cy), 150, 6)
    pygame.draw.circle(cv.surf, (200, 255, 225, 120), (cx, cy), 142, 3)
    return cv.done()


# ---------------------------------------------------------------- пришельцы
def _build_grunt(flap):
    """Красный дрон: глаз-щель, крылья-клешни машут."""
    cv = Canvas(48, 48)
    dy = -3 if flap else 3
    wing = [(30, 12), (46, 8 + dy), (47, 24 + dy), (40, 36), (33, 30)]
    for pts in (wing, mir(wing, 24)):
        cv.poly(pts, (230, 70, 80), (105, 20, 40), (50, 8, 22), 1.1)
    cv.poly(sym([(24, 2), (28, 12), (24, 17)], 24), (255, 205, 125), (200, 60, 50))
    cv.ellipse((7, 6, 34, 36), (255, 145, 130), (135, 22, 42), (55, 8, 22), 1.2)
    cv.ellipse((12, 11, 5, 4), (150, 30, 50), (150, 30, 50))
    cv.ellipse((31, 11, 5, 4), (150, 30, 50), (150, 30, 50))
    cv.glow((24, 30), 11, (255, 210, 60), 0.6)
    cv.ellipse((16, 23, 16, 14), (255, 255, 215), (255, 185, 50), (90, 30, 10), 0.9)
    cv.ellipse((22.2, 24.5, 3.6, 11), (70, 0, 10), (130, 0, 20))
    cv.ellipse((18.5, 25, 3, 2.5), (255, 255, 255), (255, 255, 255))
    return cv.done()


def _build_zigzag(flap):
    """Фиолетовая оса: быстрые прозрачные крылья, жало."""
    cv = Canvas(54, 52)
    dy = -6 if flap else 4
    wing = [(28, 14), (52, 6 + dy), (53, 17 + dy), (46, 25), (30, 31)]
    for pts in (wing, mir(wing, 27)):
        cv.poly(pts, (225, 175, 255, 235), (110, 50, 185, 200), (45, 12, 85), 1.0)
    for sign in (1, -1):
        cv.line((27 + sign * 2, 18), (27 + sign * 23, 11 + dy), (120, 60, 190), 0.6)
        cv.line((27 + sign * 2, 22), (27 + sign * 19, 20 + dy // 2), (120, 60, 190), 0.6)
    cv.poly(sym([(27, 2), (32, 14), (31, 38), (27, 50)], 27), (200, 125, 245), (75, 25, 145),
            (40, 10, 80), 1.1)
    for y in (22, 28, 34):
        cv.line((23, y), (31, y), (60, 20, 110), 0.8)
    cv.poly([(25, 44), (29, 44), (27, 51)], (255, 180, 255), (170, 60, 200))
    for x in (24, 30):
        cv.glow((x, 14), 4, (130, 255, 150), 0.9)
        cv.ellipse((x - 1.8, 12.2, 3.6, 3.6), (230, 255, 230), (80, 230, 110))
    return cv.done()


def _build_tough(open_):
    """Оранжевый жук: броня, клешни, светящееся ядро."""
    cv = Canvas(66, 64)
    o = 0 if open_ else -4
    claw = [(36, 50), (46, 50), (55, 58 + o), (53, 64), (44, 58), (36, 56)]
    for pts in (claw, mir(claw, 33)):
        cv.poly(pts, (230, 210, 170), (120, 85, 50), (50, 30, 10), 1.0)
    for pts in ([(58, 14), (66, 5), (63, 23)],):
        for q in (pts, mir(pts, 33)):
            cv.poly(q, (255, 235, 170), (205, 110, 40), (70, 30, 5), 0.9)
    shell = [(33, 2), (48, 6), (61, 18), (63, 36), (54, 50), (40, 56), (33, 57)]
    cv.poly(sym(shell, 33), (255, 205, 105), (140, 60, 15), (60, 25, 5), 1.3)
    for pts in ([(33, 6), (33, 54)], [(20, 12), (14, 46)], [(46, 12), (52, 46)],
                [(8, 28), (24, 30)], [(58, 28), (42, 30)]):
        cv.line(pts[0], pts[1], (115, 50, 15), 0.9)
    cv.glow((33, 24), 13, (255, 90, 30), 0.7)
    cv.ellipse((28, 16, 10, 16), (255, 235, 130), (255, 70, 20), (110, 30, 5), 0.9)
    for x in (27, 39):
        cv.glow((x, 46), 4, (255, 240, 120), 0.8)
        cv.ellipse((x - 1.6, 44.4, 3.2, 3.2), (255, 255, 200), (255, 220, 60))
    return cv.done()


def _build_shooter(pulse):
    """Голубой глаз-стрелок с пушкой."""
    cv = Canvas(56, 66)
    spike = [(12, 10), (18, 2), (23, 14)]
    for pts in (spike, mir(spike, 28), [(5, 24), (0, 14), (12, 18)], mir([(5, 24), (0, 14), (12, 18)], 28)):
        cv.poly(pts, (150, 235, 245), (30, 120, 150), (10, 50, 70), 0.9)
    cv.poly([(22, 46), (34, 46), (35, 62), (21, 62)], (150, 160, 180), (40, 45, 62),
            (15, 20, 35), 1.0)
    cv.glow((28, 63), 6, (90, 255, 230), 0.7 if pulse else 0.4)
    cv.ellipse((4, 4, 48, 48), (240, 255, 255), (75, 180, 200), (15, 55, 70), 1.4)
    for pts in ([(10, 14), (18, 22)], [(46, 14), (38, 22)], [(8, 36), (16, 32)],
                [(48, 36), (40, 32)], [(28, 7), (28, 13)]):
        cv.line(pts[0], pts[1], (230, 110, 130), 0.7)
    cv.glow((28, 28), 17, (80, 255, 220), 0.5 if pulse else 0.25)
    cv.ellipse((13, 13, 30, 30), (130, 255, 205), (0, 150, 175), (0, 70, 85), 1.0)
    cv.ellipse((22, 18, 12, 20), (10, 15, 30), (0, 40, 60))
    cv.ellipse((17, 16, 7, 5), (255, 255, 255), (255, 255, 255))
    return cv.done()


def _build_boss(pulse):
    """Босс - корабль-матка с огромным глазом и двумя пушками."""
    cv = Canvas(220, 124, 3)
    for x in (53, 167):                                   # пушки
        cv.poly([(x - 7, 70), (x + 7, 70), (x + 6, 112), (x - 6, 112)], (150, 155, 175),
                (35, 38, 58), (15, 15, 30), 1.2)
        cv.glow((x, 114), 9, (255, 70, 70), 0.9 if pulse else 0.5)
    spike = [(150, 12), (158, 0), (168, 18)]
    for pts in (spike, mir(spike, 110), [(184, 28), (200, 16), (200, 36)],
                mir([(184, 28), (200, 16), (200, 36)], 110)):
        cv.poly(pts, (230, 190, 255), (110, 60, 180), (30, 10, 60), 1.1)
    hull = [(110, 6), (150, 10), (196, 26), (216, 50), (208, 76), (176, 86), (146, 92),
            (126, 112), (110, 118)]
    cv.poly(sym(hull, 110), (175, 115, 235), (50, 22, 105), (25, 10, 55), 2.0)
    plate = [(110, 16), (144, 20), (180, 34), (196, 52), (180, 66), (140, 64), (110, 72)]
    cv.poly(sym(plate, 110), (140, 80, 205), (70, 30, 140), (30, 12, 70), 1.4)
    for pts in ([(110, 16), (110, 72)], [(144, 20), (140, 64)], [(180, 34), (170, 62)],
                [(76, 20), (80, 64)], [(40, 34), (50, 62)]):
        cv.line(pts[0], pts[1], (45, 20, 95), 1.0)
    for x, c in ((70, (90, 230, 255)), (150, (90, 230, 255)), (30, (255, 120, 190)),
                 (190, (255, 120, 190))):
        cv.glow((x, 46), 8, c, 0.8)
        cv.ellipse((x - 2.5, 43.5, 5, 5), (255, 255, 255), c)
    cv.ellipse((80, 32, 60, 60), (95, 60, 140), (30, 14, 62), (15, 6, 36), 2.0)   # глазница
    cv.glow((110, 62), 40, (255, 90, 40), 0.55 if pulse else 0.35)
    cv.ellipse((87, 39, 46, 46), (255, 255, 205), (255, 110, 40), (90, 25, 10), 1.5)
    cv.ellipse((103, 44, 14, 36), (35, 0, 10), (110, 0, 15))
    cv.ellipse((94, 45, 12, 8), (255, 255, 255), (255, 255, 255))
    return cv.done()


# ------------------------------------------------------------ бонусы и пули
BONUS_COLORS = {"shield": (80, 220, 120), "rapid": (250, 220, 70), "life": (240, 80, 90),
                "weapon": (90, 170, 255), "bomb": (245, 150, 50)}


def _build_bonus(kind):
    color = BONUS_COLORS[kind]
    light = tuple(min(255, c + 90) for c in color)
    dark = tuple(int(c * 0.6) for c in color)
    cv = Canvas(40, 40)
    cv.glow((20, 20), 19, color, 0.6)
    cv.ellipse((5, 5, 30, 30), light, dark, (255, 255, 255), 1.0)
    cv.ellipse((9, 7, 16, 10), (255, 255, 255, 190), (255, 255, 255, 0))
    return cv.done()


def _build_bullet(enemy):
    if enemy:
        cv = Canvas(16, 16)
        cv.glow((8, 8), 8, (255, 60, 40), 0.9)
        cv.ellipse((3.5, 3.5, 9, 9), (255, 255, 220), (255, 140, 60), (255, 70, 40), 0.7)
    else:
        cv = Canvas(12, 30)
        cv.glow((6, 9), 8, (70, 220, 255), 0.7)
        cv.glow((6, 21), 8, (70, 220, 255), 0.7)
        cv.ellipse((3.8, 2, 4.4, 26), (255, 255, 255), (110, 225, 255), (70, 200, 255), 0.6)
    return cv.done()


# ------------------------------------------------------------ публичный API
def _get(key, factory):
    if key not in _cache:
        _cache[key] = factory()
    return _cache[key]


def player():
    return _get("player", _build_player)


def flame(frame):
    return _get(("flame", frame % 4), lambda: _build_flame(frame))


def shield():
    return _get("shield", _build_shield)


def enemy_frames(kind):
    """Кадры анимации врага: 'grunt', 'zigzag', 'tough' или 'shooter'."""
    builders = {"grunt": _build_grunt, "zigzag": _build_zigzag, "tough": _build_tough,
                "shooter": _build_shooter}
    return _get(("enemy", kind), lambda: [builders[kind](0), builders[kind](1)])


def boss_frames():
    return _get("boss", lambda: [_build_boss(0), _build_boss(1)])


def bonus(kind, font):
    """Бонус с буквой (S, R, +, W, B) на светящемся шаре."""
    img = _get(("bonus", kind), lambda: _build_bonus(kind)).copy()
    letter = {"shield": "S", "rapid": "R", "life": "+", "weapon": "W", "bomb": "B"}[kind]
    text = font.render(letter, True, (10, 10, 25))
    img.blit(text, text.get_rect(center=(20, 20)))
    return img


def bullet(enemy=False):
    return _get(("bullet", enemy), lambda: _build_bullet(enemy))


def preload():
    """Создаёт все картинки заранее, чтобы в игре не было подвисаний."""
    player()
    shield()
    for i in range(4):
        flame(i)
    for kind in ("grunt", "zigzag", "tough", "shooter"):
        enemy_frames(kind)
    boss_frames()
    for kind in BONUS_COLORS:
        _get(("bonus", kind), lambda k=kind: _build_bonus(k))
    bullet(True)
    bullet(False)

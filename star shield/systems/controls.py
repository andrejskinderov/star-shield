"""Единое управление: клавиатура и геймпад."""
import pygame


class Controls:
    def __init__(self):
        self.joy = None
        self.refresh()

    def refresh(self):
        """Подключает первый доступный геймпад (вызывается при подключении/отключении)."""
        self.joy = None
        try:
            if pygame.joystick.get_count() > 0:
                self.joy = pygame.joystick.Joystick(0)
                self.joy.init()
        except pygame.error:
            self.joy = None

    def move(self, keys):
        """Возвращает число от -1 (влево) до 1 (вправо)."""
        x = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            x -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            x += 1.0
        if self.joy:
            try:
                axis = self.joy.get_axis(0)
                if abs(axis) > 0.25:
                    x += axis
                if self.joy.get_numhats() > 0:
                    x += self.joy.get_hat(0)[0]
            except pygame.error:
                pass
        return max(-1.0, min(1.0, x))

    def shooting(self, keys):
        if keys[pygame.K_SPACE]:
            return True
        if self.joy:
            try:
                return bool(self.joy.get_button(0))
            except pygame.error:
                return False
        return False


def joy_event_to_key(event):
    """Превращает событие геймпада в нажатие клавиши (чтобы меню работали с геймпадом)."""
    if event.type == pygame.JOYHATMOTION:
        x, y = event.value
        if y == 1:
            return pygame.K_UP
        if y == -1:
            return pygame.K_DOWN
        if x == -1:
            return pygame.K_LEFT
        if x == 1:
            return pygame.K_RIGHT
    elif event.type == pygame.JOYBUTTONDOWN:
        return {0: pygame.K_RETURN, 1: pygame.K_ESCAPE, 2: pygame.K_b,
                7: pygame.K_ESCAPE}.get(event.button)
    return None

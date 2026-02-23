import random
import pygame
from config import (
    GAME_CONFIG, SKEL_FRAME_W, SKEL_FRAME_H,
    SKEL_COL_X_OFFSET, SKEL_COL_Y_OFFSET, SKEL_COL_W, SKEL_COL_H,
    SKEL_FRAME_DELAYS,
    SKEL_WHITE_HP, SKEL_WHITE_SPEED, SKEL_WHITE_DAMAGE,
    SKEL_WHITE_ATTACK_RANGE, SKEL_WHITE_ATTACK_COOLDOWN,
    SKEL_YELLOW_HP, SKEL_YELLOW_SPEED, SKEL_YELLOW_DAMAGE,
    SKEL_YELLOW_ATTACK_RANGE, SKEL_YELLOW_ATTACK_COOLDOWN,
)
from entities.base import Entity


class Enemy(Entity):
    """Animated enemy with frame-dict animation system."""

    def __init__(self, x, y, frame_dict, health=2, speed=2.0, damage=8,
                 attack_range=45, attack_cooldown=75):
        super().__init__(x, y)
        self.states = frame_dict
        self.state = 'IDLE'
        self.current_frames = self.states['IDLE']
        self.current_frame_idx = 0
        self.animation_timer = 0
        self.frame_delay = SKEL_FRAME_DELAYS.get('IDLE', 100)

        self.rect = pygame.Rect(x, y, SKEL_FRAME_W, SKEL_FRAME_H)
        self.image = self.current_frames[0]

        # Collision box
        self._col_x_offset = SKEL_COL_X_OFFSET
        self._col_y_offset = SKEL_COL_Y_OFFSET
        self._col_width = SKEL_COL_W
        self._col_height = SKEL_COL_H

        self.facing_right = True
        self.alive = True
        self.vel_y = 0
        self.on_ground = False

        self.health = health
        self.max_health = health
        self.speed = speed
        self.damage = damage
        self.attack_range = attack_range
        self.attack_cooldown = attack_cooldown
        self.attack_timer = 0
        self.attacking = False
        self.state_locked = False

        self.death_anim_done = False
        self.hit_stun = 0

    def set_state(self, new_state):
        if new_state not in self.states or self.state == new_state:
            return
        self.state = new_state
        self.current_frames = self.states[new_state]
        self.current_frame_idx = 0
        self.animation_timer = 0
        self.frame_delay = SKEL_FRAME_DELAYS.get(new_state, 100)
        self.state_locked = new_state in ('ATTACK1', 'ATTACK2', 'HURT', 'DIE')

    def take_damage(self, amount):
        if not self.alive:
            return
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.set_state('DIE')
        else:
            self.set_state('HURT')
            self.hit_stun = 20

    def move_towards(self, target_rect, layout):
        if not self.alive or self.state_locked or self.hit_stun > 0:
            return

        col = self._col_rect()
        target_col_cx = target_rect.centerx
        distance = abs(col.centerx - target_col_cx)

        dx = 0
        if col.centerx < target_col_cx - 10:
            dx = self.speed
            self.facing_right = True
        elif col.centerx > target_col_cx + 10:
            dx = -self.speed
            self.facing_right = False

        if dx != 0:
            if self.state != 'WALK':
                self.set_state('WALK')
            if not self.check_collision(dx, 0, layout):
                new_x = self.rect.x + dx
                if 0 <= new_x <= GAME_CONFIG['WIDTH'] - self.rect.width:
                    self.rect.x = new_x
        else:
            if self.state == 'WALK':
                self.set_state('IDLE')

        if distance < self.attack_range and self.attack_timer <= 0:
            self.do_attack()

    def do_attack(self):
        if self.state_locked or not self.alive:
            return
        self.attacking = True
        self.attack_timer = self.attack_cooldown
        attack_choice = random.choice(['ATTACK1', 'ATTACK2'])
        self.set_state(attack_choice)

    def get_attack_hitbox(self):
        """Return hitbox rect during active attack frames, or None."""
        if not self.attacking or self.state not in ('ATTACK1', 'ATTACK2'):
            return None
        # Active on middle frames of attack animation
        total = len(self.current_frames)
        start = total // 3
        end = (total * 2) // 3
        if not (start <= self.current_frame_idx <= end):
            return None

        hitbox_w = 35
        hitbox_h = 35
        col = self._col_rect()
        if self.facing_right:
            return pygame.Rect(col.right, col.centery - hitbox_h // 2, hitbox_w, hitbox_h)
        else:
            return pygame.Rect(col.left - hitbox_w, col.centery - hitbox_h // 2, hitbox_w, hitbox_h)

    def _on_animation_end(self):
        state = self.state

        if state == 'DIE':
            self.current_frame_idx = len(self.current_frames) - 1
            self.death_anim_done = True
            return

        if state == 'HURT':
            self.hit_stun = 0
            self.set_state('IDLE')
            return

        if state in ('ATTACK1', 'ATTACK2'):
            self.attacking = False
            self.set_state('IDLE')
            return

        # Default: loop
        self.current_frame_idx = 0

    def update_animation(self, dt):
        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.hit_stun > 0:
            self.hit_stun -= 1

        self.animation_timer += dt
        if self.animation_timer >= self.frame_delay:
            self.animation_timer = 0
            self.current_frame_idx += 1

            if self.current_frame_idx >= len(self.current_frames):
                self._on_animation_end()

            if self.current_frame_idx >= len(self.current_frames):
                self.current_frame_idx = len(self.current_frames) - 1

            self.image = self.current_frames[self.current_frame_idx]

    def draw(self, screen):
        if self.facing_right:
            screen.blit(self.image, self.rect)
        else:
            flipped = pygame.transform.flip(self.image, True, False)
            screen.blit(flipped, self.rect)


class Skeleton(Enemy):
    """White skeleton — weaker, faster."""
    def __init__(self, x, y, frame_dict):
        super().__init__(x, y, frame_dict,
                         health=SKEL_WHITE_HP,
                         speed=SKEL_WHITE_SPEED,
                         damage=SKEL_WHITE_DAMAGE,
                         attack_range=SKEL_WHITE_ATTACK_RANGE,
                         attack_cooldown=SKEL_WHITE_ATTACK_COOLDOWN)


class YellowSkeleton(Enemy):
    """Yellow skeleton — stronger, slower. Replaces Orc."""
    def __init__(self, x, y, frame_dict):
        super().__init__(x, y, frame_dict,
                         health=SKEL_YELLOW_HP,
                         speed=SKEL_YELLOW_SPEED,
                         damage=SKEL_YELLOW_DAMAGE,
                         attack_range=SKEL_YELLOW_ATTACK_RANGE,
                         attack_cooldown=SKEL_YELLOW_ATTACK_COOLDOWN)

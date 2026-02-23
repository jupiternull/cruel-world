import pygame
from config import (
    GAME_CONFIG, KNIGHT_FRAME_W, KNIGHT_FRAME_H,
    KNIGHT_COL_X_OFFSET, KNIGHT_COL_Y_OFFSET, KNIGHT_COL_W, KNIGHT_COL_H,
    KNIGHT_FRAME_DELAYS, DASH_SPEED, DASH_COOLDOWN,
    ROLL_SPEED, ROLL_COOLDOWN, ROLL_INVULN_FRAMES,
    SLIDE_SPEED, SLIDE_FRICTION, COMBO_WINDOW,
    ATTACK1_DAMAGE, ATTACK2_DAMAGE, COMBO_DAMAGE,
)
from entities.base import Entity

# States that lock out player input until the animation finishes
_LOCKED_STATES = {
    'ATTACK', 'ATTACK2', 'ATTACK_COMBO', 'CROUCH_ATTACK',
    'DASH', 'ROLL', 'SLIDE_FULL', 'SLIDE', 'SLIDE_TRANSITION_END',
    'HIT', 'DEATH', 'TURN_AROUND', 'CROUCH_FULL',
}


class Knight(Entity):
    def __init__(self, x, y, frame_dict):
        super().__init__(x, y)
        self.states = frame_dict
        self.state = 'IDLE'
        self.current_frames = self.states[self.state]
        self.current_frame_idx = 0
        self.animation_timer = 0
        self.frame_delay = KNIGHT_FRAME_DELAYS.get('IDLE', 100)

        # Set rect to frame size
        self.rect = pygame.Rect(x, y, KNIGHT_FRAME_W, KNIGHT_FRAME_H)
        self.image = self.current_frames[0]

        # Collision box offsets
        self._col_x_offset = KNIGHT_COL_X_OFFSET
        self._col_y_offset = KNIGHT_COL_Y_OFFSET
        self._col_width = KNIGHT_COL_W
        self._col_height = KNIGHT_COL_H

        self.vel_y = 0
        self.on_ground = True
        self.facing_right = True

        # Health
        self.health = GAME_CONFIG['PLAYER_MAX_HEALTH']
        self.max_health = GAME_CONFIG['PLAYER_MAX_HEALTH']
        self.alive = True
        self.invulnerable = 0
        self.hit_flash = 0

        # Combat
        self.attacking = False
        self.attack_hitbox = None
        self.current_damage = 0
        self.combo_stage = 0        # 0=none, 1=ATTACK, 2=ATTACK2, 3=ATTACK_COMBO
        self.combo_buffer = False    # buffered next attack press
        self.combo_timer = 0        # frames remaining in combo window

        # Abilities
        self.dash_cooldown = 0
        self.roll_cooldown = 0
        self.slide_vel = 0
        self.crouching = False

        # State lock
        self.state_locked = False

    def set_state(self, new_state):
        if new_state not in self.states or self.state == new_state:
            return
        self.state = new_state
        self.current_frames = self.states[new_state]
        self.current_frame_idx = 0
        self.animation_timer = 0
        self.frame_delay = KNIGHT_FRAME_DELAYS.get(new_state, 100)
        self.state_locked = new_state in _LOCKED_STATES

    def take_damage(self, damage):
        if self.invulnerable > 0 or not self.alive:
            return
        self.health -= damage
        self.invulnerable = 60
        self.hit_flash = 10
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.set_state('DEATH')
        else:
            self.set_state('HIT')

    def heal(self, amount):
        self.health = min(self.health + amount, self.max_health)

    # --- Input handling ---

    def handle_input(self, keys, layout):
        """Process movement keys each frame. Replaces old move()."""
        if not self.alive or self.state == 'DEATH':
            return

        # Tick cooldowns
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.roll_cooldown > 0:
            self.roll_cooldown -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1

        # During locked states, only handle movement for dash/roll/slide
        if self.state_locked:
            if self.state in ('SLIDE_FULL', 'SLIDE'):
                self._apply_slide(layout)
            if self.state == 'DASH':
                speed = DASH_SPEED if self.facing_right else -DASH_SPEED
                if not self.check_collision(speed, 0, layout):
                    new_x = self.rect.x + speed
                    if 0 <= new_x <= GAME_CONFIG['WIDTH'] - self.rect.width:
                        self.rect.x = new_x
            if self.state == 'ROLL':
                speed = ROLL_SPEED if self.facing_right else -ROLL_SPEED
                if not self.check_collision(speed, 0, layout):
                    new_x = self.rect.x + speed
                    if 0 <= new_x <= GAME_CONFIG['WIDTH'] - self.rect.width:
                        self.rect.x = new_x
            return

        # Crouching
        crouch_held = keys[pygame.K_s] or keys[pygame.K_DOWN]
        if crouch_held and self.on_ground:
            if not self.crouching:
                self.crouching = True
                self.set_state('CROUCH_FULL')
                return
            # Already crouching — move or hold
            dx = 0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx = -GAME_CONFIG['PLAYER_SPEED'] // 2
                self.facing_right = False
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx = GAME_CONFIG['PLAYER_SPEED'] // 2
                self.facing_right = True

            if dx != 0:
                if self.state != 'CROUCH_WALK':
                    self.set_state('CROUCH_WALK')
                if not self.check_collision(dx, 0, layout):
                    new_x = self.rect.x + dx
                    if 0 <= new_x <= GAME_CONFIG['WIDTH'] - self.rect.width:
                        self.rect.x = new_x
            else:
                if self.state not in ('CROUCH', 'CROUCH_FULL'):
                    self.set_state('CROUCH')
            return

        if self.crouching:
            self.crouching = False
            self.set_state('IDLE')

        # Normal movement
        dx = 0
        moving = False
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -GAME_CONFIG['PLAYER_SPEED']
            if self.facing_right and self.on_ground and self.state == 'RUN':
                self.facing_right = False
                self.set_state('TURN_AROUND')
                return
            self.facing_right = False
            moving = True
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = GAME_CONFIG['PLAYER_SPEED']
            if not self.facing_right and self.on_ground and self.state == 'RUN':
                self.facing_right = True
                self.set_state('TURN_AROUND')
                return
            self.facing_right = True
            moving = True

        # Jump
        if (keys[pygame.K_SPACE] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = GAME_CONFIG['JUMP_VELOCITY']
            self.on_ground = False

        # Airborne state detection
        if not self.on_ground:
            if self.vel_y < -2:
                if self.state != 'JUMP':
                    self.set_state('JUMP')
            elif self.vel_y > 2:
                if self.state != 'FALL':
                    self.set_state('FALL')
            else:
                if self.state == 'JUMP':
                    self.set_state('JUMP_FALL_BETWEEN')
        else:
            # Ground state
            if moving:
                if self.state != 'RUN':
                    self.set_state('RUN')
            else:
                if self.state not in ('IDLE',):
                    self.set_state('IDLE')

        # Apply horizontal movement
        if dx != 0 and not self.check_collision(dx, 0, layout):
            new_x = self.rect.x + dx
            if 0 <= new_x <= GAME_CONFIG['WIDTH'] - self.rect.width:
                self.rect.x = new_x

    def attack(self):
        """Called on F key press."""
        if not self.alive:
            return

        # Crouch attack
        if self.crouching and self.on_ground:
            self.set_state('CROUCH_ATTACK')
            self.attacking = True
            self.current_damage = ATTACK1_DAMAGE
            self._update_attack_hitbox()
            return

        # Combo chaining — buffer press during active attack
        if self.state_locked and self.state in ('ATTACK', 'ATTACK2'):
            self.combo_buffer = True
            return

        # Combo window — chain next hit after previous attack ended
        if self.combo_timer > 0:
            if self.combo_stage == 1:
                self.set_state('ATTACK2')
                self.attacking = True
                self.combo_stage = 2
                self.current_damage = ATTACK2_DAMAGE
                self.combo_timer = 0
                self._update_attack_hitbox()
                return
            elif self.combo_stage == 2:
                self.set_state('ATTACK_COMBO')
                self.attacking = True
                self.combo_stage = 3
                self.current_damage = COMBO_DAMAGE
                self.combo_timer = 0
                self._update_attack_hitbox()
                return

        if not self.state_locked:
            self.set_state('ATTACK')
            self.attacking = True
            self.combo_stage = 1
            self.current_damage = ATTACK1_DAMAGE
            self._update_attack_hitbox()

    def dash(self):
        """Called on Left Shift press."""
        if not self.alive or self.state_locked or self.dash_cooldown > 0:
            return
        self.set_state('DASH')
        self.dash_cooldown = DASH_COOLDOWN

    def roll(self):
        """Called on Q press."""
        if not self.alive or self.state_locked or self.roll_cooldown > 0 or not self.on_ground:
            return
        self.set_state('ROLL')
        self.roll_cooldown = ROLL_COOLDOWN
        self.invulnerable = ROLL_INVULN_FRAMES

    def slide(self):
        """Called on E press. Only works while running."""
        if not self.alive or self.state_locked or not self.on_ground:
            return
        if self.state != 'RUN':
            return
        self.set_state('SLIDE_FULL')
        self.slide_vel = SLIDE_SPEED if self.facing_right else -SLIDE_SPEED

    def _apply_slide(self, layout):
        """Decelerate slide each frame."""
        self.slide_vel *= SLIDE_FRICTION
        int_vel = int(self.slide_vel)
        if abs(int_vel) < 1:
            self.slide_vel = 0
            return
        if not self.check_collision(int_vel, 0, layout):
            new_x = self.rect.x + int_vel
            if 0 <= new_x <= GAME_CONFIG['WIDTH'] - self.rect.width:
                self.rect.x = new_x

    def _update_attack_hitbox(self):
        hitbox_width = 45
        hitbox_height = 40
        col = self._col_rect()
        if self.facing_right:
            self.attack_hitbox = pygame.Rect(
                col.right, col.centery - hitbox_height // 2,
                hitbox_width, hitbox_height)
        else:
            self.attack_hitbox = pygame.Rect(
                col.left - hitbox_width, col.centery - hitbox_height // 2,
                hitbox_width, hitbox_height)

    def _on_animation_end(self):
        """Called when the current animation reaches its last frame."""
        state = self.state

        if state == 'DEATH':
            self.current_frame_idx = len(self.current_frames) - 1
            return

        if state == 'HIT':
            self.set_state('IDLE')
            return

        if state in ('ATTACK', 'ATTACK2', 'ATTACK_COMBO', 'CROUCH_ATTACK'):
            self.attacking = False
            self.attack_hitbox = None
            # Check combo buffer
            if self.combo_buffer and state in ('ATTACK', 'ATTACK2'):
                self.combo_buffer = False
                self.attack()
                return
            # Open combo window for chaining
            if state in ('ATTACK', 'ATTACK2') and self.combo_stage < 3:
                self.combo_timer = COMBO_WINDOW
            else:
                self.combo_stage = 0
                self.combo_timer = 0
            if self.crouching:
                self.set_state('CROUCH')
            else:
                self.set_state('IDLE')
            return

        if state == 'CROUCH_FULL':
            self.set_state('CROUCH')
            return

        if state == 'TURN_AROUND':
            self.set_state('RUN')
            return

        if state == 'DASH':
            self.set_state('IDLE')
            return

        if state == 'ROLL':
            self.invulnerable = 0
            self.set_state('IDLE')
            return

        if state == 'SLIDE_FULL':
            self.set_state('SLIDE')
            return

        if state == 'SLIDE':
            if abs(self.slide_vel) < 1:
                self.set_state('SLIDE_TRANSITION_END')
            return

        if state == 'SLIDE_TRANSITION_END':
            self.slide_vel = 0
            self.set_state('IDLE')
            return

        # Default: loop
        self.current_frame_idx = 0

    def update_animation(self, dt):
        if self.invulnerable > 0:
            self.invulnerable -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

        self.animation_timer += dt
        if self.animation_timer >= self.frame_delay:
            self.animation_timer = 0
            self.current_frame_idx += 1

            if self.current_frame_idx >= len(self.current_frames):
                self._on_animation_end()
            else:
                if self.attacking:
                    self._update_attack_hitbox()

            # Clamp index
            if self.current_frame_idx >= len(self.current_frames):
                self.current_frame_idx = len(self.current_frames) - 1

            self.image = self.current_frames[self.current_frame_idx]

    def draw(self, screen):
        image_to_draw = self.image
        if self.hit_flash > 0 and self.hit_flash % 4 < 2:
            image_to_draw = self.image.copy()
            image_to_draw.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_ADD)

        if self.invulnerable > 0 and self.invulnerable % 10 < 5:
            return

        if self.facing_right:
            screen.blit(image_to_draw, self.rect)
        else:
            flipped_image = pygame.transform.flip(image_to_draw, True, False)
            screen.blit(flipped_image, self.rect)

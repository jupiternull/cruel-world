import pygame
from progression import effect
from entities.base import Entity
from projectile import DamageSource


CLASSES = {
    'warrior': {'name': 'Knight', 'health': 150, 'speed': 4, 'damage': 22,
                'secondary': 'Shield rush', 'cooldown': 180, 'color': (227, 166, 86),
                'description': '150 HP / heavy melee / three-hit combo',
                'hint': 'F: combo   E: shield rush   Shift/Q: dodge'},
    'ranger': {'name': 'Archer', 'health': 100, 'speed': 6, 'damage': 18,
                 'secondary': 'Piercing volley', 'cooldown': 210, 'color': (129, 212, 142),
                 'description': '100 HP / fast bow / piercing spread',
                 'hint': 'F: arrow   E: piercing volley   Shift/Q: evade'},
    'wizard': {'name': 'Wizard', 'health': 85, 'speed': 4, 'damage': 26,
               'secondary': 'Arcane wave', 'cooldown': 300, 'color': (177, 142, 239),
               'description': '85 HP / fireball / wide arcane wave',
               'hint': 'F: fireball   E: arcane wave   Shift/Q: blink'},
}


def held(keys, key):
    try:
        return keys[key]
    except (KeyError, IndexError):
        return False


class Hero(Entity):
    def __init__(self, x, y, frames, class_id='warrior'):
        super().__init__(x, y)
        from zerie_runtime import canonical_class
        class_id = canonical_class(class_id)
        self.class_id = class_id
        self.stats = CLASSES[class_id]
        self.rect = pygame.Rect(x, y, 32, 64)
        self.frames = frames
        self.states = frames
        self.anchor = getattr(frames, 'anchor', frames['Idle'][0].get_bounding_rect())
        self.health = self.max_health = self.stats['health']
        self.state = 'Idle'
        self.current_frames = frames['Idle']
        self.current_frame_idx = 0
        self.animation_timer = 0
        self.image = self.current_frames[0]
        self.invulnerable = 0
        self.hit_flash = 0
        self.secondary_cooldown = 0
        self.dash_cooldown = 0
        self.roll_cooldown = 0
        self.mobility_timer = 0
        self.rushing = False
        self.combo_stage = 0
        self.combo_timer = 0
        self.combo_buffer = False
        self.pending_attack = None
        self.attack_elapsed = 0
        self.attacking = False
        self.attack_hitbox = None
        self.current_damage = 0
        self.hit_targets = set()
        self.climbing = None
        self.drop_timer = 0
        self.jump_held = False
        self.footstep_timer = 0
        self.events = []
        self.sources = []
        self.aim = pygame.Vector2(1, 0)
        self.on_ground = True

    @property
    def state_locked(self):
        return self.pending_attack is not None or self.mobility_timer > 0 or self.state in ('Hit', 'Take hit', 'Death')

    def set_state(self, name, restart=False):
        if name not in self.frames or (name == self.state and not restart):
            return
        self.state = name
        self.current_frames = self.frames[name]
        self.current_frame_idx = 0
        self.animation_timer = 0
        self.image = self.current_frames[0]

    def take_damage(self, damage, source=None):
        if not self.alive or self.invulnerable:
            return
        self.health = max(0, self.health - damage)
        self.invulnerable = 48
        self.hit_flash = 12
        self.pending_attack = None
        self.attacking = False
        self.combo_buffer = False
        self.attack_hitbox = None
        self.events.append('hit')
        self.alive = self.health > 0
        self.set_state(('Hit' if 'Hit' in self.frames else 'Take hit') if self.alive else 'Death', True)

    def heal(self, amount, upgrade=False):
        self.health = min(self.max_health, self.health + amount + (effect(self, 'healing') if upgrade and amount > 0 else 0))

    def attack(self):
        if not self.alive:
            return False
        if self.pending_attack and self.class_id == 'warrior':
            self.combo_buffer = True
            return False
        if self.state_locked:
            return False
        self.combo_stage = self.combo_stage % 3 + 1 if self.combo_timer else 1
        self.pending_attack = 'primary'
        self.attacking = True
        self.attack_elapsed = 0
        self.set_state(f'Attack{self.combo_stage}' if self.class_id == 'warrior' else 'Attack1', True)
        self.events.append({'warrior': 'sword_attack', 'ranger': 'bow_attack', 'wizard': 'fireball'}[self.class_id])
        return True

    def secondary(self):
        if not self.alive or self.state_locked or self.secondary_cooldown:
            return False
        self.secondary_cooldown = self.stats['cooldown'] - effect(self, 'recovery')
        if self.class_id == 'warrior':
            self.rushing = True
            self.mobility_timer = 24
            self.invulnerable = 30
            self.set_state('Block')
            self.events.append('sword_block')
            col = self.rect
            self.sources.append(DamageSource(col.inflate(64, 12), 35, 'hero', 24, owner=self, kind='rush'))
        else:
            self.pending_attack = 'secondary'
            self.attacking = True
            self.attack_elapsed = 0
            self.set_state('Attack3' if self.class_id == 'ranger' else 'Attack2', True)
            self.events.append('bow_attack' if self.class_id == 'ranger' else 'arcane_wave')
        return True

    def dash(self, direction=None):
        if not self.alive or self.dash_cooldown or self.mobility_timer or self.state in ('Hit', 'Take hit', 'Death'):
            return False
        if self.pending_attack:
            if self.class_id == 'warrior':
                return False
            self.pending_attack = None
            self.attacking = False
            self.attack_hitbox = None
        if direction:
            self.facing_right = direction > 0
        self.dash_cooldown = 90 if self.class_id != 'wizard' else 150
        self.dash_cooldown -= effect(self, 'mobility')
        self.roll_cooldown = self.dash_cooldown
        self.mobility_timer = 14
        self.invulnerable = max(self.invulnerable, 18)
        self.set_state('Roll' if self.class_id == 'warrior' else 'Run')
        self.climbing = None
        return True

    def roll(self, direction=None):
        return self.dash(direction)

    def slide(self):
        return self.secondary()

    def detach(self, jump=False):
        self.climbing = None
        if jump:
            self.vel_y = -14
            self.on_ground = False

    def drop_through(self, world):
        if self.on_ground and self.rect.bottom < world.ground.top:
            self.drop_timer = 18
            self.rect.y += 2
            self.on_ground = False
            self.vel_y = 2
            self.climbing = None
            return True
        return False

    def handle_input(self, keys, world):
        if not self.alive:
            return
        for name in ('secondary_cooldown', 'dash_cooldown', 'roll_cooldown', 'combo_timer', 'drop_timer'):
            setattr(self, name, max(0, getattr(self, name) - 1))
        jump = held(keys, pygame.K_SPACE)
        jump_press = jump and not self.jump_held
        self.jump_held = jump
        up = held(keys, pygame.K_w) or held(keys, pygame.K_UP)
        down = held(keys, pygame.K_s) or held(keys, pygame.K_DOWN)
        dx = int(held(keys, pygame.K_d) or held(keys, pygame.K_RIGHT)) - int(held(keys, pygame.K_a) or held(keys, pygame.K_LEFT))
        if self.mobility_timer:
            world.move(self, (12 if self.class_id != 'wizard' else 18) * (1 if self.facing_right else -1))
            self.mobility_timer -= 1
            if not self.mobility_timer:
                self.rushing = False
            return
        if self.state_locked:
            if self.pending_attack and self.class_id != 'warrior':
                if dx:
                    world.move(self, dx * max(2, self.stats['speed'] // 2))
                if jump_press and self.on_ground:
                    self.vel_y = -15
                    self.on_ground = False
                    self.events.append('jump')
            return
        if down and jump_press and self.drop_through(world):
            return
        if self.climbing is None and (up or down) and not self.drop_timer:
            self.climbing = next((r for r in world.climbables if self.rect.colliderect(r.inflate(10, 8))), None)
        if self.climbing is not None:
            zone = self.climbing
            self.rect.centerx = zone.centerx
            self.vel_y = 0
            self.on_ground = False
            if jump_press or dx:
                self.detach(jump_press)
            else:
                self.rect.y += (int(down) - int(up)) * 3
                if self.rect.bottom <= zone.top + 3:
                    self.rect.bottom = zone.top
                    self.detach()
                    self.on_ground = True
                elif self.rect.bottom >= zone.bottom and down:
                    self.rect.bottom = zone.bottom
                    self.detach()
                    self.on_ground = True
                self.set_state(('WallSlide' if up or down else 'LedgeGrab') if self.class_id == 'warrior' else ('Run' if up or down else 'Idle'))
                return
        if dx:
            self.facing_right = dx > 0
            world.move(self, dx * self.stats['speed'])
        if (jump_press or up) and self.on_ground:
            self.vel_y = -15
            self.on_ground = False
            self.events.append('jump')
        self.set_state('Run' if dx else 'Idle')
        if not self.on_ground:
            self.set_state('Jump' if self.vel_y < 0 else 'Fall')

    def emit_attack(self):
        direction = 1 if self.facing_right else -1
        x = self.rect.centerx
        y = self.rect.centery
        secondary = self.pending_attack == 'secondary'
        if self.class_id == 'warrior':
            damage = (22, 30, 42)[self.combo_stage - 1]
            self.current_damage = damage
            self.attack_hitbox = pygame.Rect(x if direction > 0 else x - 82, y - 38, 82, 76)
            source = DamageSource(self.attack_hitbox, damage, 'hero', 10, owner=self)
            self.hit_targets = source.hit_targets
            self.sources.append(source)
        elif self.class_id == 'ranger':
            for vy in (-2, 0, 2) if secondary else (0,):
                self.sources.append(DamageSource((x, y - 4, 30, 8), 24 if secondary else 18,
                                                'hero', 75 + effect(self, 'reach'), (direction * 12, vy) if secondary else (self.aim.x * 12, self.aim.y * 12),
                                                'volley' if secondary else 'arrow', self, secondary))
        else:
            self.sources.append(DamageSource((x - 16, y - (65 if secondary else 12), 48 if secondary else 28,
                                              130 if secondary else 24), 50 if secondary else 26, 'hero',
                                             55 if secondary else 85, (direction * 7, 0) if secondary else (self.aim.x * 9, self.aim.y * 9),
                                             'wave' if secondary else 'fireball', self, secondary))

    def update_animation(self, dt):
        self.invulnerable = max(0, self.invulnerable - 1)
        self.hit_flash = max(0, self.hit_flash - 1)
        if self.pending_attack:
            self.attack_elapsed += 1
            if self.attack_elapsed == 9:
                self.emit_attack()
        if self.class_id == 'warrior' and self.pending_attack:
            strike = (2, 1, 3)[self.combo_stage - 1]
            # Put the forward sweep on the deterministic damage tick, then recover.
            self.current_frame_idx = (self.attack_elapsed * strike // 9 if self.attack_elapsed <= 9
                                      else strike + (self.attack_elapsed - 9) * (len(self.current_frames) - 1 - strike) // 8)
            self.current_frame_idx = min(len(self.current_frames) - 1, self.current_frame_idx)
            self.image = self.current_frames[self.current_frame_idx]
            if self.attack_elapsed >= 17:
                self.pending_attack = None
                self.attacking = False
                self.attack_hitbox = None
                self.combo_timer = 28
                self.set_state('Idle')
                if self.combo_buffer:
                    self.combo_buffer = False
                    self.attack()
            return
        self.animation_timer += dt
        delay = 80 if self.class_id == 'warrior' and self.state == 'Death' else 50 if self.class_id == 'wizard' and self.pending_attack == 'primary' else 70 if self.state.startswith('Attack') else 90
        if self.animation_timer >= delay:
            self.animation_timer -= delay
            self.current_frame_idx += 1
            if self.current_frame_idx >= len(self.current_frames):
                if self.state == 'Death':
                    self.current_frame_idx = len(self.current_frames) - 1
                elif self.pending_attack:
                    self.pending_attack = None
                    self.attacking = False
                    self.attack_hitbox = None
                    self.combo_timer = 28
                    self.set_state('Idle')
                    if self.combo_buffer and self.class_id == 'warrior':
                        self.combo_buffer = False
                        self.attack()
                elif self.state in ('Hit', 'Take hit'):
                    self.set_state('Idle')
                else:
                    self.current_frame_idx = 0
            self.image = self.current_frames[self.current_frame_idx]

    def draw(self, screen, camera):
        image = self.image
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
        if self.hit_flash % 4 >= 2:
            image = image.copy()
            image.fill((100, 100, 100, 0), special_flags=pygame.BLEND_RGBA_ADD)
        anchor_x = self.anchor.centerx if self.facing_right else image.get_width() - self.anchor.centerx
        screen.blit(image, (self.rect.centerx - anchor_x - camera.x, self.rect.bottom - self.anchor.bottom))
        if self.invulnerable:
            pygame.draw.arc(screen, self.stats['color'], camera.rect(self.rect.inflate(12, 8)), 0, 6.28, 2)

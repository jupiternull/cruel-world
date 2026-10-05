import pygame
from entities.base import Entity
from projectile import DamageSource


class Monster(Entity):
    def __init__(self, x, y, frames, species, boss=False, environment=0):
        super().__init__(x, y)
        self.species = species
        self.boss = boss
        self.environment = environment
        self.frames = frames
        self.scale = 2 if boss else 1
        self.rect = pygame.Rect(x, y, 64 if boss else 36, 84 if boss else 56)
        self.flying = species == 'Flying eye'
        self.armored = species == 'Skeleton' or (boss and species == 'Goblin')
        self.health = self.max_health = (240 + environment * 70 if boss else {'Goblin': 44, 'Mushroom': 60, 'Skeleton': 70, 'Flying eye': 36}[species])
        self.speed = 2 if species != 'Flying eye' else 3
        self.damage = 18 if boss else 8
        self.state = 'Flight' if self.flying else 'Idle'
        self.current_frames = frames[self.state]
        self.anchor = self.current_frames[0].get_bounding_rect()
        self.current_frame_idx = 0
        self.animation_timer = 0
        self.image = self.current_frames[0]
        self.attack_timer = 60
        self.windup = 0
        self.recovery = 0
        self.attack_count = 0
        self.age = 0
        self.death_anim_done = False
        self.rewarded = False
        self.telegraph = None
        self.sources = []
        self.events = []
        self.attacking = False
        self.hit_stun = 0

    def set_state(self, name):
        if name not in self.frames or self.state == name:
            return
        self.state = name
        self.current_frames = self.frames[name]
        self.current_frame_idx = 0
        self.animation_timer = 0
        self.image = self.current_frames[0]

    def take_damage(self, amount, source=None):
        if not self.alive:
            return
        frontal = source and ((source.rect.centerx > self.rect.centerx) == self.facing_right)
        if self.armored and not self.windup and not self.recovery and frontal and source.kind != 'wave':
            amount = max(1, amount // 3)
            self.set_state('Shield' if 'Shield' in self.frames else 'Idle')
        self.health = max(0, self.health - amount)
        if not self.health:
            self.alive = False
            self.attacking = False
            self.windup = 0
            self.telegraph = None
            self.set_state('Death')
        elif not self.boss:
            self.hit_stun = 10
            self.set_state('Take Hit')

    def do_attack(self, target=None):
        if not self.alive or self.windup or self.recovery:
            return
        self.attacking = True
        self.windup = 60 if self.boss else 32
        self.attack_timer = 150 if self.boss else 90
        self.attack_count += 1
        self.set_state('Idle' if self.boss and not self.flying else 'Flight' if self.boss else 'Attack')
        if self.boss:
            self.events.append('sword_attack' if self.species == 'Goblin' else 'arcane_wave')
        direction = 1 if self.facing_right else -1
        width = 180 if self.boss else 65
        self.telegraph = pygame.Rect(self.rect.centerx if direction > 0 else self.rect.centerx - width,
                                     self.rect.bottom - 64, width, 64)
        if self.boss and self.species == 'Flying eye' and target is not None:
            self.telegraph = pygame.Rect(target.centerx - 42, 128, 84, 432)
        elif self.boss and self.species == 'Mushroom':
            self.telegraph = self.rect.inflate(280, 64)
            self.telegraph.bottom = self.rect.bottom

    def release_attack(self, world):
        direction = 1 if self.facing_right else -1
        if self.boss and self.species == 'Mushroom':
            self.sources.append(DamageSource(self.telegraph, 20, 'enemy', 12, kind='spore', owner=self))
            if self.attack_count % 2 == 0:
                for sign in (-1, 1):
                    self.sources.append(DamageSource((self.rect.centerx, self.rect.bottom - 26, 26, 24), 14, 'enemy', 100, (sign * 5, 0), 'spore', self, False))
        elif self.boss and self.species == 'Goblin':
            self.sources.append(DamageSource(self.telegraph, 22, 'enemy', 12, owner=self))
            self.sources.append(DamageSource((self.rect.centerx, self.rect.bottom - 24, 38, 24), 16, 'enemy', 100, (direction * 8, 0), 'shock', self, False))
            world.move(self, direction * 100)
        elif self.boss and self.species == 'Flying eye':
            self.sources.append(DamageSource((self.telegraph.x, 128, self.telegraph.width, 30), 24, 'enemy', 80, (0, 7), 'moon', self, False))
            if self.attack_count % 2 == 0:
                for sign in (-1, 1):
                    self.sources.append(DamageSource((self.rect.centerx, self.rect.centery, 24, 24), 15, 'enemy', 100, (sign * 5, 2), 'moon', self, False))
        else:
            self.sources.append(DamageSource(self.telegraph, self.damage, 'enemy', 10, owner=self))
        self.telegraph = None
        self.recovery = 42 if self.boss else 20
        self.attacking = False

    def update(self, target, world):
        self.age += 1
        if self.alive:
            self.attack_timer = max(0, self.attack_timer - 1)
            self.hit_stun = max(0, self.hit_stun - 1)
            if self.windup:
                self.windup -= 1
                if self.boss and self.windup == 24:
                    self.set_state('Attack')
                if not self.windup:
                    self.release_attack(world)
            elif self.recovery:
                self.recovery -= 1
            elif not self.hit_stun and target.alive:
                dx = target.rect.centerx - self.rect.centerx
                self.facing_right = dx > 0
                distance = abs(dx)
                if self.flying:
                    desired_y = target.rect.y - (80 if self.boss else 12)
                    self.rect.y += max(-2, min(2, desired_y - self.rect.y))
                    self.rect.y = max(128, min(490, self.rect.y))
                elif self.on_ground and target.rect.bottom < self.rect.bottom - 48:
                    self.vel_y = -15
                    self.on_ground = False
                attack_range = 400 if self.boss and self.flying else 120 if self.boss else 62
                if distance > (180 if self.boss and self.flying else 38):
                    world.move(self, self.speed if dx > 0 else -self.speed)
                    self.set_state('Flight' if self.flying else 'Walk' if 'Walk' in self.frames else 'Run')
                else:
                    self.set_state('Flight' if self.flying else 'Idle')
                if distance < attack_range and (self.boss and self.flying or abs(target.rect.centery - self.rect.centery) < 70) and not self.attack_timer:
                    self.do_attack(target.rect)
            if not self.flying:
                world.gravity(self)
        self.update_animation(1000 / 60)

    def update_animation(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 100:
            self.animation_timer -= 100
            self.current_frame_idx += 1
            if self.current_frame_idx >= len(self.current_frames):
                if not self.alive:
                    self.current_frame_idx = len(self.current_frames) - 1
                    self.death_anim_done = True
                else:
                    self.current_frame_idx = 0
            self.image = self.current_frames[self.current_frame_idx]

    def draw(self, screen, camera):
        if self.telegraph is not None:
            rect = camera.rect(self.telegraph)
            surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            surface.fill((240, 68, 70, 55 if self.windup > 15 else 115))
            screen.blit(surface, rect)
            pygame.draw.rect(screen, (248, 124, 84), rect, 2)
        image = self.image
        if self.boss:
            image = pygame.transform.scale(image, (image.get_width() * 2, image.get_height() * 2))
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
        anchor_x = self.anchor.centerx * self.scale
        if not self.facing_right:
            anchor_x = image.get_width() - anchor_x
        screen.blit(image, (self.rect.centerx - anchor_x - camera.x, self.rect.bottom - self.anchor.bottom * self.scale))
        if self.alive and not self.boss and self.health < self.max_health:
            rect = camera.rect((self.rect.x - 4, self.rect.y - 8, 44, 4))
            pygame.draw.rect(screen, (42, 25, 35), rect)
            pygame.draw.rect(screen, (232, 103, 89), (rect.x, rect.y, int(44 * self.health / self.max_health), 4))
        if self.windup:
            pygame.draw.circle(screen, (255, 185, 95), camera.point(self.rect.centerx, self.rect.y - 12), 6)

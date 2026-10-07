import pygame
from entities.monster import Monster
from projectile import DamageSource


class Infernal(Monster):
    def __init__(self, x, y, frames, role):
        flying = frames.action_sources['Idle'] == 'Flying'
        species = 'Flying eye' if flying else 'Goblin'
        super().__init__(x, y, frames, species, role in ('boss', 'miniboss'), 3)
        self.role = role
        self.armored = role == 'elite' and frames.actor == 'Black Knight_B'
        self.health = self.max_health = {'melee': 30, 'flying': 24, 'caster': 28,
                                        'elite': 45, 'miniboss': 150, 'boss': 300}[role]
        self.rect.bottom = 560
        self.damage = {'melee': 4, 'flying': 4, 'caster': 5, 'elite': 4,
                       'miniboss': 7, 'boss': 10}[role]
        if flying:
            self.rect.y = 420
        self.speed = 1 if self.boss else 2

    def do_attack(self, target=None):
        super().do_attack(target)
        attacks = ['Attack'] + [s for s in ('Attack02', 'Attack03') if s in self.frames]
        self.set_state(attacks[(self.attack_count - 1) % len(attacks)])
        if self.role in ('caster', 'boss') and target is not None:
            direction = 1 if self.facing_right else -1
            self.telegraph = pygame.Rect(self.rect.centerx if direction > 0 else self.rect.centerx - 420,
                                         self.rect.centery - 16, 420, 32)
            self.windup = 65 if self.boss else 48
            self.set_state('Attack')

    def release_attack(self, world):
        if self.role == 'miniboss':
            direction = 1 if self.facing_right else -1
            self.sources.append(DamageSource(self.telegraph, self.damage, 'enemy', 10, owner=self))
            world.move(self, direction * 45)
            self.telegraph = None
            self.recovery = 90
            self.attacking = False
        elif self.role in ('caster', 'boss'):
            direction = 1 if self.facing_right else -1
            source = DamageSource((self.rect.centerx, self.rect.centery - 12, 30, 24),
                                  self.damage, 'enemy', 95, (direction * 5, 0), 'fireball', self, False)
            source.frames = self.frames.projectile
            self.sources.append(source)
            self.telegraph = None
            self.recovery = 65 if self.boss else 40
            self.attacking = False
        else:
            super().release_attack(world)

    def update(self, target, world):
        # Casters hold a readable firing lane; other roles retain campaign pursuit.
        if self.alive and target.alive and self.role in ('caster', 'boss') and not self.windup and not self.recovery:
            dx = target.rect.centerx - self.rect.centerx
            if 100 < abs(dx) < 420 and abs(target.rect.centery - self.rect.centery) < 90:
                self.facing_right = dx > 0
                if not self.attack_timer:
                    self.do_attack(target.rect)
                self.speed = 0
            else:
                self.speed = 1 if self.boss else 2
        super().update(target, world)

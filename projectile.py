import pygame


class DamageSource:
    def __init__(self, rect, damage, team, lifetime, velocity=(0, 0), kind='melee', owner=None,
                 pierce=True, frames=None):
        self.rect = pygame.Rect(rect)
        self.damage = damage
        self.team = team
        self.lifetime = lifetime
        self.velocity = velocity
        self.kind = kind
        self.owner = owner
        self.pierce = pierce
        self.hit_targets = set()
        self.frames = frames
        self.age = 0
        self.alive = True
        self.position = list(self.rect.topleft)

    def update(self, world):
        self.age += 1
        self.lifetime -= 1
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.rect.topleft = self.position
        self.alive = self.alive and self.lifetime > 0 and self.rect.right >= 0 and self.rect.left <= world.width and self.rect.bottom >= 0 and self.rect.top <= world.ground.bottom
        if self.kind != 'wave' and self.velocity != (0, 0) and self.rect.colliderect(world.ground):
            self.alive = False

    def hit(self, target):
        if not self.alive or not target.alive or target in self.hit_targets or not self.rect.colliderect(target._col_rect()):
            return False
        self.hit_targets.add(target)
        target.take_damage(self.damage, self)
        if not self.pierce:
            self.alive = False
        return True

    def draw(self, screen, camera):
        rect = camera.rect(self.rect)
        if self.kind in ('melee', 'rush'):
            return
        if self.frames:
            image = self.frames[(self.age // 5) % len(self.frames)]
            if self.velocity[0] < 0:
                image = pygame.transform.flip(image, True, False)
            screen.blit(image, image.get_rect(center=rect.center))
        elif self.kind in ('arrow', 'volley'):
            direction = pygame.Vector2(self.velocity).normalize()
            normal = pygame.Vector2(-direction.y, direction.x)
            center = pygame.Vector2(rect.center)
            pygame.draw.line(screen, (226, 196, 128), center - direction * 16, center + direction * 16, 2)
            pygame.draw.polygon(screen, (220, 231, 221), [center + direction * 18,
                                 center + direction * 10 - normal * 4, center + direction * 10 + normal * 4])
        else:
            color = (254, 134, 51) if self.kind == 'fireball' else (150, 112, 246)
            pygame.draw.ellipse(screen, (53, 40, 76), rect.inflate(8, 8), 3)
            pygame.draw.ellipse(screen, color, rect, 3 if self.kind == 'wave' else 0)
            pygame.draw.ellipse(screen, (255, 227, 166), rect.inflate(-8, -8), 2)

import pygame


class Scenery:
    def __init__(self, world, assets):
        self.world = world
        self.assets = assets
        self.kind = world.data['id']
        self.forest_background = pygame.transform.scale_by(assets['forest_bg'], 2)
        self.tiles = {}
        if self.kind == 'underworld':
            from underworld import SCENES, scene_path
            sheet = pygame.image.load(str(scene_path(*SCENES[1]))).convert()
            self.top = self.crop(sheet, (0, 132, 16, 8), 2)
            self.fill = self.crop(sheet, (16, 132, 16, 12), 2)
            self.platform = self.top
            self.prop = None
        elif self.kind == 'graveyard':
            sheet = assets['moon_tiles']
            self.top = self.crop(sheet, (144, 32, 16, 16), 2)
            self.fill = self.crop(sheet, (32, 64, 16, 16), 2)
            self.platform = self.crop(sheet, (80, 240, 16, 16), 2)
            self.prop = self.crop(sheet, (256, 32, 32, 64), 2)
        else:
            sheet = assets['forest_tiles']
            self.top = self.crop(sheet, (16, 16, 16, 16), 2)
            self.fill = self.crop(sheet, (16, 48, 16, 16), 2)
            self.platform = self.crop(assets['interior'], (0, 144, 16, 8), 2)
            self.prop = self.crop(assets['rocks'], (0, 80, 64, 80), 2)
            if self.kind == 'cave':
                self.top = self.crop(sheet, (16, 96, 16, 16), 2)
                self.fill = self.crop(sheet, (48, 112, 16, 16), 2)
                self.prop = self.crop(assets['rocks'], (0, 0, 64, 80), 2)
        self.wood = self.crop(assets['interior'], (96, 32, 8, 16), 1)
        self.rung = self.crop(assets['interior'], (96, 16, 16, 4), 1)
        self.door = self.crop(assets['interior'], (128, 4, 48, 64), 2)
        self.ruin = self.crop(assets['buildings'], (272, 240, 112, 112), 2)
        self.wall = self.crop(assets['buildings'], (352, 64, 32, 32), 2)
        self.cache = pygame.Surface((world.width, 600), pygame.SRCALPHA)
        for x in range(0, world.width, 32):
            self.cache.blit(self.top, (x, 560))
            self.cache.blit(self.fill, (x, 592))
        for rect in world.platforms:
            for x in range(rect.left, rect.right, 32):
                tile = self.top if self.kind != 'cave' else self.platform
                # Raised ledges match their 16 px collision height.
                self.cache.blit(tile, (x, rect.top), (0, 0, min(32, rect.right - x), 16))
        for zone in world.climbables:
            pygame.draw.rect(self.cache, (24, 27, 30, 220), zone.inflate(6, 0))
            for y in range(zone.top, zone.bottom, 16):
                self.cache.blit(self.wood, (zone.left, y))
                self.cache.blit(self.wood, (zone.right - 8, y))
                self.cache.blit(self.rung, (zone.left + 4, y + 7))
        for index, x in enumerate(range(384, world.width - 200, 560) if self.prop is not None else []):
            prop = pygame.transform.flip(self.prop, bool(index % 2), False)
            prop = prop.copy()
            prop.set_alpha(150)
            self.cache.blit(prop, (x + (index % 3) * 24, 560 - prop.get_height()))
        if self.kind == 'forest':
            for x in (880, 1808):
                self.cache.blit(self.ruin, (x, 336))
        for hazard in ([] if self.kind == 'underworld' else world.hazards):
            for x in range(hazard.x, hazard.right, 16):
                if self.kind == 'forest':
                    self.cache.blit(self.crop(assets['forest_tiles'], (256, 256, 16, 16), 1), (x, hazard.y))
                pygame.draw.polygon(self.cache, (177, 204, 155) if self.kind == 'forest' else (169, 170, 190),
                                    [(x, hazard.bottom), (x + 8, hazard.top), (x + 16, hazard.bottom)])

    def crop(self, sheet, rect, scale):
        image = sheet.subsurface(rect).copy()
        return pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale))

    def repeat(self, screen, image, camera, factor, y=0):
        start = -int(camera.x * factor) % image.get_width() - image.get_width()
        for x in range(start, 800, image.get_width()):
            screen.blit(image, (x, y))

    def draw(self, screen, camera, campaign):
        screen.fill(self.world.data['color'])
        if self.kind == 'underworld':
            pass
        elif self.kind == 'forest':
            self.repeat(screen, self.forest_background, camera, 0.15)
            tree = self.assets['forest_trees']
            for index, x in enumerate(range(-224, self.world.width, 208)):
                image = pygame.transform.flip(tree, bool(index % 2), False).copy()
                image.set_alpha(130 if index % 3 else 190)
                screen.blit(image, (x + (index % 3) * 32 - int(camera.x * 0.4), 168 + (index % 4) * 16))
        elif self.kind == 'graveyard':
            self.repeat(screen, self.assets['moon_bg'], camera, 0.15)
            self.repeat(screen, self.assets['moon_buildings'], camera, 0.35, 144)
        else:
            for x in range(-int(camera.x * 0.25) % 64 - 64, 800, 64):
                for y in range(80, 560, 64):
                    screen.blit(self.wall, (x, y))
            for x in range(-int(camera.x * 0.25) % 256 - 256, 800, 256):
                pygame.draw.rect(screen, (43, 39, 46), (x, 80, 22, 480))
                pygame.draw.line(screen, (74, 67, 65), (x + 3, 80), (x + 3, 560), 3)
            shade = pygame.Surface((800, 600), pygame.SRCALPHA)
            shade.fill((15, 12, 33, 145))
            screen.blit(shade, (0, 0))
            for x in range(224, self.world.width, 384):
                sx = x - camera.x
                pygame.draw.rect(screen, (29, 26, 38), (sx - 8, 264, 16, 30))
                pygame.draw.circle(screen, (88, 60, 39), (sx, 280), 14)
                pygame.draw.circle(screen, (255, 179, 79), (sx, 280), 6)
        features = getattr(self.world, 'features', None)
        if features:
            features.draw_background(screen, camera)
        screen.blit(self.cache, (-camera.x, 0))
        for point in self.world.data['checkpoints']:
            color = (135, 228, 177) if point <= campaign.checkpoint else (102, 119, 125)
            x = point - camera.x
            pygame.draw.line(screen, color, (x, 510), (x, 560), 3)
            pygame.draw.polygon(screen, color, [(x, 510), (x + 26, 518), (x, 531)])
        rect = camera.rect(self.world.exit)
        screen.blit(self.door, (rect.x - 8, rect.bottom - self.door.get_height()))
        pygame.draw.rect(screen, (115, 236, 189) if campaign.exit_open else (196, 133, 85), rect, 3)
        if not campaign.exit_open:
            pygame.draw.line(screen, (196, 133, 85), rect.midleft, rect.midright, 4)

from config import GAME_CONFIG


class GameState:
    def __init__(self):
        self.score = 0
        self.wave = 1
        self.game_over = False
        self.paused = False
        self.phase = 'ready'
        self.transition_timer = 150
        self.spawn_timer = 0
        self.spawned = 0
        self.completed = 0

    @property
    def boss_wave(self):
        return self.wave % 5 == 0

    @property
    def wave_size(self):
        return 1 if self.boss_wave else min(18, 4 + self.wave * 2)

    @property
    def spawn_rate(self):
        return max(GAME_CONFIG['MIN_SPAWN_RATE'], GAME_CONFIG['INITIAL_SPAWN_RATE'] - (self.wave - 1) * 8)

    @property
    def enemy_limit(self):
        return min(6, 3 + self.wave // 3)

    def update_wave(self, alive_count=0):
        """Return a spawn request or a completed-wave event per fixed tick."""
        if self.game_over or self.paused:
            return None
        if self.phase != 'combat':
            self.transition_timer -= 1
            if self.transition_timer <= 0:
                if self.phase == 'clear':
                    self.wave += 1
                self.phase = 'combat'
                self.spawned = 0
                self.spawn_timer = self.spawn_rate
            return None
        if self.spawned == self.wave_size and alive_count == 0:
            self.completed = self.wave
            self.phase = 'clear'
            self.transition_timer = 180
            self.add_score(250 * self.wave)
            return 'clear'
        self.spawn_timer += 1
        if self.spawned < self.wave_size and alive_count < self.enemy_limit and self.spawn_timer >= self.spawn_rate:
            self.spawn_timer = 0
            self.spawned += 1
            return 'boss' if self.boss_wave else 'spawn'
        return None

    def add_score(self, points):
        self.score += max(0, points)


class CampaignState(GameState):
    @property
    def boss_wave(self):
        return self.wave == getattr(self, 'realm_waves', 3)

    @property
    def wave_size(self):
        if getattr(self, 'realm_waves', 3) == 8:
            from underworld import ENCOUNTERS
            return len(ENCOUNTERS[self.wave - 1])
        return 1 if self.boss_wave else 4 + self.wave

    @property
    def spawn_rate(self):
        return 85

    def update_wave(self, alive_count=0):
        if self.phase in ('travel', 'exit', 'victory'):
            return None
        return super().update_wave(alive_count)

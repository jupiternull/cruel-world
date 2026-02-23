from config import GAME_CONFIG


class GameState:
    def __init__(self):
        self.score = 0
        self.wave = 1
        self.wave_timer = 0
        self.spawn_rate = GAME_CONFIG['INITIAL_SPAWN_RATE']
        self.enemies_per_spawn = 1
        self.game_over = False
        self.paused = False

    def update_wave(self):
        self.wave_timer += 1
        if self.wave_timer >= GAME_CONFIG['WAVE_DURATION']:
            self.wave += 1
            self.wave_timer = 0
            self.spawn_rate = max(GAME_CONFIG['MIN_SPAWN_RATE'], self.spawn_rate - 10)
            if self.wave % 3 == 0:
                self.enemies_per_spawn += 1

    def add_score(self, points):
        self.score += points

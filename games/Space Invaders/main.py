import pygame
import random
import sys
import os
import json
import webbrowser
from datetime import datetime

pygame.init()

BASE_WIDTH, BASE_HEIGHT = 800, 700
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
DISPLAY_SCALE = max(0.65, min(WIDTH / BASE_WIDTH, HEIGHT / BASE_HEIGHT))
FPS = 60

def scale_value(value):
    if value == 0:
        return 0
    scaled = max(1, round(abs(value) * DISPLAY_SCALE))
    return scaled if value > 0 else -scaled

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (20, 220, 240)
GREEN = (50, 235, 50)
YELLOW = (235, 235, 50)
RED = (235, 50, 50)
PINK_BUNKER = (235, 120, 140)
PURPLE_UFO = (200, 50, 200)
BLUE_SHIELD = (50, 150, 255)

pygame.display.set_caption("Space Invaders")

RESOURCE_DIR = getattr(
    sys,
    "_MEIPASS",
    os.path.dirname(os.path.abspath(__file__))
)
DATA_DIR = os.path.join(RESOURCE_DIR, "data")
if getattr(sys, "frozen", False):
    IMAGE_DIR = os.path.join(RESOURCE_DIR, "img")
else:
    IMAGE_DIR = os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "docs", "img"
    ))
pygame.display.set_icon(
    pygame.image.load(os.path.join(IMAGE_DIR, "space invaders - favicon.png"))
)
BUNDLED_RECORDS_PATH = os.path.join(DATA_DIR, "records.json")
RECORDS_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "SpaceInvaders",
    "records.json"
)

class RetroFont:
    def __init__(self, name, size, scale=2):
        self.scale = scale
        self.font = pygame.font.SysFont(name, max(1, size // scale), bold=True)

    def render(self, text, _antialias, color, background=None):
        text_surface = self.font.render(text, False, color, background)
        scaled_size = (
            text_surface.get_width() * self.scale,
            text_surface.get_height() * self.scale
        )
        return pygame.transform.scale(text_surface, scaled_size)

font_ui = RetroFont("Courier", scale_value(24))
font_large = RetroFont("Courier", scale_value(52))
font_menu = RetroFont("Courier", scale_value(30))
font_powerup = RetroFont("Courier", scale_value(16))

def load_records():
    has_shared_records = os.path.exists(RECORDS_PATH)
    records_path = RECORDS_PATH if has_shared_records else BUNDLED_RECORDS_PATH

    if os.path.exists(records_path):
        with open(records_path, "r", encoding="utf-8") as records_file:
            records = json.load(records_file)
    else:
        records = {
            "high_score": 0,
            "high_score_date": None,
            "max_wave": 0,
            "max_wave_date": None
        }

    if not isinstance(records, dict):
        raise ValueError("El archivo records.json debe contener un objeto JSON.")

    for key in ("high_score", "max_wave"):
        if type(records.get(key)) is not int or records[key] < 0:
            raise ValueError(f"El valor '{key}' de records.json no es válido.")

    for key in ("high_score_date", "max_wave_date"):
        if records.get(key) is not None and not isinstance(records[key], str):
            raise ValueError(f"La fecha '{key}' de records.json no es válida.")

    if not has_shared_records:
        save_records(records)

    return records

def save_records(records):
    os.makedirs(os.path.dirname(RECORDS_PATH), exist_ok=True)
    with open(RECORDS_PATH, "w", encoding="utf-8") as records_file:
        json.dump(records, records_file, ensure_ascii=False, indent=4)

GAME_MUSIC_END = pygame.USEREVENT + 1

DIFFICULTY_SETTINGS = {
    "Fácil": (45, 0.010),
    "Normal": (37, 0.017),
    "Difícil": (29, 0.025)
}

MAP_LAYOUTS = {
    "Clásico": [0.1125, 0.33125, 0.55, 0.76875],
    "Abierto": [0.1625, 0.725]
}

ALIEN_GREEN = [
    ["...11...", "..1111..", ".111111.", "11.11.11", "11111111", "..1..1..", ".1.11.1.", "1......1"],
    ["...11...", "..1111..", ".111111.", "11.11.11", "11111111", "...11...", "..1..1..", ".1....1."]
]

ALIEN_YELLOW = [
    ["..1.....1..", "...1...1...", "..1111111..", ".11.111.11.", "11111111111", "1.1111111.1", "1.1.....1.1", "...11.11..."],
    ["..1.....1..", "1..1...1..1", "1.1111111.1", "111.111.111", "11111111111", ".111111111.", "..1.....1..", ".1.......1."]
]

ALIEN_RED = [
    ["....1111....", ".1111111111.", "111111111111", "111..11..111", "111111111111", "...11..11...", "..11.11.11..", "11........11"],
    ["....1111....", ".1111111111.", "111111111111", "111..11..111", "111111111111", "..11....11..", ".11......11.", "..11....11.."]
]

UFO_PATTERN = [
    "....111111....", "..1111111111..", ".111111111111.", ".11.11.11.11..", 
    "11111111111111", "...111..111...", ".....1..1....."
]

PLAYER_PATTERN = [
    ".....1.....", "....111....", "....111....", ".111111111.", 
    "11111111111", "11111111111", "11111111111"
]

BUNKER_PATTERN = [
    "....11111111111111....", "...1111111111111111...", "..111111111111111111..",
    ".11111111111111111111.", "1111111111111111111111", "1111111111111111111111",
    "1111111111111111111111", "1111111111111111111111", "111111....11....111111",
    "11111......1......1111", "1111.......1.......111", "111........1........11",
    "11.........1.........1"
]

def build_sprite(pattern_list, color, scale=3):
    scale = scale_value(scale)
    width, height = len(pattern_list[0]), len(pattern_list)
    surface = pygame.Surface((width * scale, height * scale), pygame.SRCALPHA)
    for y, row in enumerate(pattern_list):
        for x, char in enumerate(row):
            if char == '1':
                pygame.draw.rect(surface, color, (x * scale, y * scale, scale, scale))
    return surface

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = build_sprite(PLAYER_PATTERN, CYAN, scale=4)
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - scale_value(50)))
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = scale_value(5)
        self.shoot_cooldown = 0
        self.lives = 3
        
        self.shield_active = False
        self.triple_shot_timer = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.rect.left > scale_value(10):
            self.rect.x -= self.speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.rect.right < WIDTH - scale_value(10):
            self.rect.x += self.speed
            
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if self.triple_shot_timer > 0:
            self.triple_shot_timer -= 1

    def shoot(self, bullets_group):
        if self.shoot_cooldown == 0:
            if self.triple_shot_timer > 0:
                bullets_group.add(Bullet(self.rect.centerx, self.rect.top, -10, WHITE))
                bullets_group.add(Bullet(self.rect.centerx - scale_value(15), self.rect.top + scale_value(5), -10, WHITE))
                bullets_group.add(Bullet(self.rect.centerx + scale_value(15), self.rect.top + scale_value(5), -10, WHITE))
            else:
                bullets_group.add(Bullet(self.rect.centerx, self.rect.top, -10, WHITE))
            
            self.shoot_cooldown = 15  # Cadencia mucho mas rapida
            return True

        return False

    def draw_shield(self, surface):
        if self.shield_active:
            pygame.draw.circle(surface, BLUE_SHIELD, self.rect.center, scale_value(35), scale_value(3))

class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, frames_patterns, color, score_value):
        super().__init__()
        self.color = color
        self.frames = [build_sprite(frames_patterns[0], color, scale=3), 
                       build_sprite(frames_patterns[1], color, scale=3)]
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.score_value = score_value

    def move_step(self, x_move, y_move):
        self.rect.x += x_move
        self.rect.y += y_move
        self.current_frame = (self.current_frame + 1) % 2
        self.image = self.frames[self.current_frame]

class BossUFO(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = build_sprite(UFO_PATTERN, PURPLE_UFO, scale=3)
        self.mask = pygame.mask.from_surface(self.image)
        self.direction = random.choice([-1, 1])
        start_x = -scale_value(60) if self.direction == 1 else WIDTH + scale_value(60)
        self.rect = self.image.get_rect(topleft=(start_x, scale_value(70)))
        self.speed = scale_value(3)
        self.score_value = random.choice([50, 100, 150, 300])

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.right < -scale_value(150) or self.rect.left > WIDTH + scale_value(150):
            self.kill()

class AlienBoss(pygame.sprite.Sprite):
    def __init__(self, wave):
        super().__init__()
        patterns, self.color = random.choice([
            (ALIEN_GREEN, GREEN),
            (ALIEN_YELLOW, YELLOW),
            (ALIEN_RED, RED)
        ])
        self.frames = [
            build_sprite(pattern, self.color, scale=7)
            for pattern in patterns
        ]
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(midtop=(WIDTH // 2, scale_value(110)))
        self.mask = pygame.mask.from_surface(self.image)

        boss_number = wave // 5
        self.max_health = 5 + (boss_number - 1) * 2
        self.health = self.max_health
        self.speed = scale_value(2 + boss_number)
        self.direction = random.choice([-1, 1])
        self.animation_timer = 0
        self.shoot_timer = 60
        self.bullet_speed = 6 + boss_number
        self.score_value = 500 + (boss_number - 1) * 250

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.left <= scale_value(20):
            self.rect.left = scale_value(20)
            self.direction = 1
        elif self.rect.right >= WIDTH - scale_value(20):
            self.rect.right = WIDTH - scale_value(20)
            self.direction = -1

        self.animation_timer += 1
        if self.animation_timer >= 20:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]

    def shoot(self, bullets_group):
        for offset, speed_x in ((-scale_value(24), -2), (0, 0), (scale_value(24), 2)):
            bullets_group.add(
                Bullet(
                    self.rect.centerx + offset,
                    self.rect.bottom,
                    self.bullet_speed,
                    WHITE,
                    speed_x
                )
            )
        self.shoot_timer = max(35, 75 - self.bullet_speed * 2)

class Bunker(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = build_sprite(BUNKER_PATTERN, PINK_BUNKER, scale=4)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

    def take_damage(self, bullet_rect):
        hit_x, hit_y = bullet_rect.centerx - self.rect.x, bullet_rect.centery - self.rect.y
        pygame.draw.circle(self.image, (0, 0, 0, 0), (hit_x, hit_y), scale_value(12))
        self.mask = pygame.mask.from_surface(self.image)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed_y, color, speed_x=0):
        super().__init__()
        self.image = pygame.Surface((scale_value(4), scale_value(16)))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = scale_value(speed_y)
        self.speed_x = scale_value(speed_x) if speed_x else 0

    def update(self):
        self.rect.y += self.speed_y
        self.rect.x += self.speed_x
        if self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, type_code):
        super().__init__()
        self.type_code = type_code
        size = scale_value(24)
        self.image = pygame.Surface((size, size))
        
        # Mapeo de tipos y colores
        # V = Vida, E = Escudo, T = Triple, B = Bunkers
        color_map = {'V': GREEN, 'E': BLUE_SHIELD, 'T': YELLOW, 'B': PINK_BUNKER}
        color = color_map.get(type_code, WHITE)
        
        self.image.fill(color)
        pygame.draw.rect(self.image, WHITE, self.image.get_rect(), scale_value(2))
        
        text = font_powerup.render(type_code, True, BLACK)
        text_rect = text.get_rect(center=self.image.get_rect().center)
        self.image.blit(text, text_rect)
        
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.y += scale_value(3)
        if self.rect.top > HEIGHT:
            self.kill()

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((
            scale_value(random.randint(3, 5)),
            scale_value(random.randint(3, 5))
        ))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x = random.uniform(-4, 4) * DISPLAY_SCALE
        self.vel_y = random.uniform(-4, 4) * DISPLAY_SCALE
        self.lifetime = random.randint(15, 35)

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

class Star:
    def __init__(self):
        self.x = random.randrange(WIDTH)
        self.y = random.randrange(HEIGHT)
        self.speed = random.uniform(0.5, 2) * DISPLAY_SCALE
        self.size = scale_value(random.choice((1, 2, 3)))
        self.color = random.choice(((100, 100, 130), (170, 170, 200), WHITE))

    def update(self, speed_multiplier):
        self.y += self.speed * speed_multiplier
        if self.y >= HEIGHT:
            self.x = random.randrange(WIDTH)
            self.y = 0

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)

class StarField:
    def __init__(self, count=None):
        if count is None:
            count = scale_value(100)
        self.stars = [Star() for _ in range(count)]
        self.speed_multiplier = 1

    def update(self):
        for star in self.stars:
            star.update(self.speed_multiplier)

    def set_wave(self, wave):
        self.speed_multiplier = 1 + (wave - 1) * 0.2

    def draw(self, surface):
        for star in self.stars:
            star.draw(surface)

def show_intro():
    intro_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "audio",
        "Intro.mp3"
    )
    logo_path = os.path.join(IMAGE_DIR, "space invaders - logo.png")
    logo = pygame.image.load(logo_path).convert_alpha()
    logo_scale = min(
        (WIDTH - scale_value(80)) / logo.get_width(),
        scale_value(250) / logo.get_height()
    )
    logo_size = (
        int(logo.get_width() * logo_scale),
        int(logo.get_height() * logo_scale)
    )
    logo = pygame.transform.smoothscale(logo, logo_size)

    pygame.mixer.music.load(intro_path)
    pygame.mixer.music.play()

    starfield = StarField()
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()

    while pygame.time.get_ticks() - start_time < 5000:
        elapsed = pygame.time.get_ticks() - start_time
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                return False

        screen.fill(BLACK)
        starfield.update()
        starfield.draw(screen)

        progress = min(elapsed / 1400, 1)
        eased_progress = 1 - (1 - progress) ** 3
        logo_factor = 0.04 + 0.96 * eased_progress
        current_size = (
            max(1, int(logo_size[0] * logo_factor)),
            max(1, int(logo_size[1] * logo_factor))
        )
        current_logo = pygame.transform.smoothscale(logo, current_size)
        screen.blit(
            current_logo,
            current_logo.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.43)))
        )

        title = font_large.render("Made By", True, CYAN)
        creator = font_large.render("1oza16", True, WHITE)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.70))))
        screen.blit(creator, creator.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.81))))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.mixer.music.stop()
    return True

class GameMusic:
    def __init__(self):
        if getattr(sys, "frozen", False):
            # PyInstaller extrae los recursos incluidos en la carpeta temporal.
            music_dir = os.path.join(sys._MEIPASS, "audio", "music")
        else:
            # Ruta utilizada al ejecutar el proyecto desde el código fuente.
            music_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "docs", "sound", "Space Invaders"
            ))
        self.tracks = [
            os.path.join(music_dir, filename)
            for filename in os.listdir(music_dir)
            if filename.lower().endswith((".mp3", ".ogg", ".wav"))
        ]
        if not self.tracks:
            raise FileNotFoundError(f"No hay canciones compatibles en {music_dir}")

        self.remaining_tracks = []
        self.last_track = None

    def start(self):
        pygame.mixer.music.set_endevent(GAME_MUSIC_END)
        self.play_next()

    def play_next(self):
        if not self.remaining_tracks:
            self.remaining_tracks = self.tracks.copy()
            random.shuffle(self.remaining_tracks)
            if len(self.remaining_tracks) > 1 and self.remaining_tracks[-1] == self.last_track:
                self.remaining_tracks[0], self.remaining_tracks[-1] = (
                    self.remaining_tracks[-1],
                    self.remaining_tracks[0]
                )

        self.last_track = self.remaining_tracks.pop()
        pygame.mixer.music.load(self.last_track)
        pygame.mixer.music.play()

    def stop(self):
        pygame.mixer.music.set_endevent()
        pygame.mixer.music.stop()

class GameSounds:
    def __init__(self):
        sound_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "audio",
            "game"
        )
        self.effects = {
            "shoot": pygame.mixer.Sound(os.path.join(sound_dir, "Gun Shot.mp3")),
            "boss": pygame.mixer.Sound(os.path.join(sound_dir, "Boss.mp3")),
            "game_over": pygame.mixer.Sound(os.path.join(sound_dir, "Game Over.mp3")),
            "damage": pygame.mixer.Sound(os.path.join(sound_dir, "Player Damage.mp3")),
            "ufo": pygame.mixer.Sound(os.path.join(sound_dir, "Ufo.mp3"))
        }
        for effect in self.effects.values():
            effect.set_volume(0.5)

    def play(self, effect_name):
        self.effects[effect_name].play()

def show_menu():
    difficulty_options = list(DIFFICULTY_SETTINGS)
    map_options = list(MAP_LAYOUTS)
    difficulty_index = 1
    map_index = 0
    selected_option = 0
    option_count = 4
    web_status = ""
    starfield = StarField()
    records = load_records()
    logo_path = os.path.join(IMAGE_DIR, "space invaders - logo.png")
    logo = pygame.image.load(logo_path).convert_alpha()
    logo_scale = min(
        scale_value(540) / logo.get_width(),
        scale_value(180) / logo.get_height()
    )
    logo_size = (
        int(logo.get_width() * logo_scale),
        int(logo.get_height() * logo_scale)
    )
    logo = pygame.transform.smoothscale(logo, logo_size)

    pygame.mixer.music.set_endevent()
    music_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "audio",
        "Main Menu - Space Invaders Soundtrack.mp3"
    )
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.play(-1)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    direction = -1 if event.key == pygame.K_UP else 1
                    selected_option = (selected_option + direction) % option_count
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    direction = 1 if event.key == pygame.K_RIGHT else -1
                    if selected_option == 0:
                        difficulty_index = (difficulty_index + direction) % len(difficulty_options)
                    elif selected_option == 1:
                        map_index = (map_index + direction) % len(map_options)
                elif event.key == pygame.K_RETURN:
                    if selected_option == 2:
                        try:
                            if not webbrowser.open(
                                "https://1oza16.github.io/games/index.html#space-invaders-view",
                                new=2
                            ):
                                web_status = "No se pudo abrir el navegador."
                            else:
                                web_status = ""
                        except (webbrowser.Error, OSError) as error:
                            web_status = f"No se pudo abrir el enlace: {error}"
                    elif selected_option == 3:
                        return None
                    else:
                        return difficulty_options[difficulty_index], map_options[map_index]

        screen.fill(BLACK)
        starfield.update()
        starfield.draw(screen)

        screen.blit(logo, logo.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.26))))

        difficulty_color = YELLOW if selected_option == 0 else WHITE
        map_color = YELLOW if selected_option == 1 else WHITE
        web_color = YELLOW if selected_option == 2 else WHITE
        difficulty_text = font_menu.render(
            f"Dificultad: {difficulty_options[difficulty_index]}",
            True,
            difficulty_color
        )
        map_text = font_menu.render(
            f"Mapa: {map_options[map_index]}",
            True,
            map_color
        )
        web_option = font_menu.render("Web", True, web_color)
        exit_color = YELLOW if selected_option == 3 else WHITE
        exit_option = font_menu.render("Salir", True, exit_color)
        screen.blit(difficulty_text, difficulty_text.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.44))))
        screen.blit(map_text, map_text.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.505))))
        screen.blit(web_option, web_option.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.57))))
        screen.blit(exit_option, exit_option.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.635))))
        if web_status:
            status_text = font_powerup.render(web_status, True, RED)
            screen.blit(status_text, status_text.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.69))))

        score_date = records["high_score_date"] or "--"
        wave_date = records["max_wave_date"] or "--"
        score_record = font_powerup.render(
            f"RECORD PUNTOS: {records['high_score']:06d}  FECHA: {score_date}",
            True,
            WHITE
        )
        wave_record = font_powerup.render(
            f"OLEADA MAXIMA: {records['max_wave']:02d}  FECHA: {wave_date}",
            True,
            WHITE
        )
        screen.blit(score_record, score_record.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.77))))
        screen.blit(wave_record, wave_record.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.82))))

        pygame.display.flip()
        clock.tick(FPS)

class GameManager:
    def __init__(self, difficulty="Normal", map_name="Clásico"):
        self.difficulty = difficulty
        self.map_name = map_name
        self.alien_move_base, self.alien_shoot_chance = DIFFICULTY_SETTINGS[difficulty]
        self.records = load_records()
        self.sounds = GameSounds()
        self.game_over_played = False

        self.player = Player()
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.starfield = StarField()
        self.aliens = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.alien_bullets = pygame.sprite.Group()
        self.bunkers = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.boss_group = pygame.sprite.GroupSingle()
        self.ufo_group = pygame.sprite.GroupSingle()
        
        self.score = 0
        self.wave = 1
        
        self.alien_direction = 1
        self.alien_step_x = scale_value(15)
        self.alien_step_y = scale_value(20)
        self.move_timer = 0 
        self.ufo_timer = random.randint(800, 1500)

        self.create_bunkers()
        self.start_wave()

    def create_bunkers(self):
        self.bunkers.empty()
        for x_ratio in MAP_LAYOUTS[self.map_name]:
            x_pos = int(WIDTH * x_ratio)
            y_pos = HEIGHT - scale_value(180)
            self.bunkers.add(Bunker(x_pos, y_pos))

    def create_aliens(self):
        self.aliens.empty()
        rows_data = [
            (ALIEN_GREEN, GREEN, 30),
            (ALIEN_YELLOW, YELLOW, 20),
            (ALIEN_YELLOW, YELLOW, 20),
            (ALIEN_RED, RED, 10),
            (ALIEN_RED, RED, 10)
        ]
        alien_gap = scale_value(45)
        formation_width = scale_value(36) + 10 * alien_gap
        start_x = (WIDTH - formation_width) // 2
        for row_idx, data in enumerate(rows_data):
            pattern, color, pts = data
            for col in range(11):
                x = start_x + col * alien_gap
                y = scale_value(120) + row_idx * scale_value(40)
                self.aliens.add(Alien(x, y, pattern, color, pts))

    def start_wave(self):
        self.starfield.set_wave(self.wave)
        self.move_timer = 0
        self.player_bullets.empty()
        self.alien_bullets.empty()
        self.powerups.empty()
        self.aliens.empty()
        self.boss_group.empty()
        self.ufo_group.empty()

        if self.wave % 5 == 0:
            self.boss_group.add(AlienBoss(self.wave))
            self.sounds.play("boss")
        else:
            self.ufo_timer = random.randint(800, 1500)
            self.create_aliens()

    def spawn_particles(self, x, y, color, count=20):
        for _ in range(count):
            self.particles.add(Particle(x, y, color))

    def update_records(self):
        updated = False
        record_date = datetime.now().strftime("%d/%m/%Y %H:%M")

        if self.score > self.records["high_score"]:
            self.records["high_score"] = self.score
            self.records["high_score_date"] = record_date
            updated = True

        if self.wave > self.records["max_wave"]:
            self.records["max_wave"] = self.wave
            self.records["max_wave_date"] = record_date
            updated = True

        if updated:
            save_records(self.records)

    def move_aliens_logic(self):
        if len(self.aliens) == 0:
            return

        self.move_timer -= 1
        if self.move_timer <= 0:
            move_down = False
            for alien in self.aliens.sprites():
                if alien.rect.right >= WIDTH - scale_value(20) and self.alien_direction == 1:
                    move_down = True
                    break
                elif alien.rect.left <= scale_value(20) and self.alien_direction == -1:
                    move_down = True
                    break

            if move_down:
                self.alien_direction *= -1
                for alien in self.aliens.sprites():
                    alien.move_step(0, self.alien_step_y)
            else:
                for alien in self.aliens.sprites():
                    alien.move_step(self.alien_step_x * self.alien_direction, 0)
            
            self.move_timer = max(8, self.alien_move_base - (self.wave - 1) * 2)

    def enemy_shooting_logic(self):
        shoot_chance = min(0.05, self.alien_shoot_chance + (self.wave - 1) * 0.002)
        if self.aliens.sprites() and random.random() < shoot_chance:
            random_alien = random.choice(self.aliens.sprites())
            bullet = Bullet(random_alien.rect.centerx, random_alien.rect.bottom, 6, WHITE)
            self.alien_bullets.add(bullet)

    def handle_collisions(self):
        hits = pygame.sprite.groupcollide(self.aliens, self.player_bullets, True, True)
        for alien in hits:
            self.score += alien.score_value
            self.spawn_particles(alien.rect.centerx, alien.rect.centery, alien.color)
            
            if random.random() < 0.08: # 8% de probabilidad de tirar una habilidad
                p_type = random.choice(['V', 'E', 'T', 'B'])
                self.powerups.add(PowerUp(alien.rect.centerx, alien.rect.centery, p_type))

        boss_hits = pygame.sprite.groupcollide(self.boss_group, self.player_bullets, False, True)
        for boss, bullets in boss_hits.items():
            boss.health -= len(bullets)
            if boss.health <= 0:
                self.score += boss.score_value
                self.spawn_particles(boss.rect.centerx, boss.rect.centery, boss.color, 40)
                boss.kill()

        ufo_hits = pygame.sprite.groupcollide(self.ufo_group, self.player_bullets, True, True)
        for ufo in ufo_hits:
            self.score += ufo.score_value
            self.spawn_particles(ufo.rect.centerx, ufo.rect.centery, PURPLE_UFO, 40)

        for bullet in self.player_bullets.sprites() + self.alien_bullets.sprites():
            for bunker in self.bunkers.sprites():
                offset_x = bullet.rect.x - bunker.rect.x
                offset_y = bullet.rect.y - bunker.rect.y
                bullet_mask = pygame.mask.Mask(bullet.rect.size, fill=True)
                
                if bunker.mask.overlap(bullet_mask, (offset_x, offset_y)):
                    bunker.take_damage(bullet.rect)
                    bullet.kill()
                    break

        powerup_hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for p in powerup_hits:
            if p.type_code == 'V' and self.player.lives < 3:
                self.player.lives += 1
            elif p.type_code == 'E':
                self.player.shield_active = True
            elif p.type_code == 'T':
                self.player.triple_shot_timer = 400 
            elif p.type_code == 'B':
                self.create_bunkers()

        if pygame.sprite.spritecollide(self.player, self.alien_bullets, True, pygame.sprite.collide_mask):
            if self.player.shield_active:
                self.player.shield_active = False
                self.spawn_particles(self.player.rect.centerx, self.player.rect.centery, BLUE_SHIELD, 20)
            else:
                self.player.lives -= 1
                self.sounds.play("damage")
                self.spawn_particles(self.player.rect.centerx, self.player.rect.centery, CYAN, 30)
                self.player.triple_shot_timer = 0 # Pierde disparo triple si lo matan

        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.player.rect.top:
                self.player.lives = 0

    def manage_waves_and_boss(self):
        if self.wave % 5 == 0:
            if len(self.boss_group) == 0:
                self.wave += 1
                self.start_wave()
            return

        if len(self.aliens) == 0:
            self.wave += 1
            self.start_wave()
            return

        self.ufo_timer -= 1
        if self.ufo_timer <= 0:
            if len(self.ufo_group) == 0:
                self.ufo_group.add(BossUFO())
                self.sounds.play("ufo")
            self.ufo_timer = random.randint(1000, 2000)

    def draw_ui(self, screen):
        score_surf = font_ui.render("PUNTOS <1>", True, CYAN)
        score_val = font_ui.render(f"{self.score:06d}", True, WHITE)
        pause_text = font_ui.render("P: PAUSA", True, CYAN)
        wave_surf = font_ui.render("OLEADA", True, CYAN)
        wave_val = font_ui.render(f"{self.wave:02d}", True, WHITE)
        
        screen.blit(score_surf, (scale_value(40), scale_value(15)))
        screen.blit(score_val, (scale_value(60), scale_value(45)))
        screen.blit(pause_text, pause_text.get_rect(center=(WIDTH // 2, scale_value(25))))
        screen.blit(wave_surf, (WIDTH - scale_value(40) - wave_surf.get_width(), scale_value(15)))
        screen.blit(wave_val, (WIDTH - scale_value(40) - wave_val.get_width(), scale_value(45)))

        boss = self.boss_group.sprite
        if boss is not None:
            boss_label = font_powerup.render("JEFE", True, CYAN)
            bar_width = scale_value(300)
            bar_rect = pygame.Rect(
                WIDTH // 2 - bar_width // 2,
                scale_value(84),
                bar_width,
                scale_value(14)
            )
            health_width = int(bar_width * boss.health / boss.max_health)
            screen.blit(
                boss_label,
                boss_label.get_rect(center=(WIDTH // 2, scale_value(75)))
            )
            pygame.draw.rect(screen, RED, bar_rect)
            pygame.draw.rect(screen, GREEN, (bar_rect.x, bar_rect.y, health_width, bar_rect.height))
            pygame.draw.rect(screen, WHITE, bar_rect, scale_value(2))

        pygame.draw.line(
            screen,
            RED,
            (0, HEIGHT - scale_value(30)),
            (WIDTH, HEIGHT - scale_value(30)),
            scale_value(3)
        )
        
        lives_text = font_ui.render(str(self.player.lives), True, WHITE)
        screen.blit(lives_text, (scale_value(20), HEIGHT - scale_value(25)))
        
        for i in range(self.player.lives - 1):
            x_pos = scale_value(60) + i * scale_value(50)
            pygame.draw.rect(
                screen,
                CYAN,
                (x_pos, HEIGHT - scale_value(15), scale_value(25), scale_value(10))
            )
            pygame.draw.rect(
                screen,
                CYAN,
                (x_pos + scale_value(10), HEIGHT - scale_value(20), scale_value(5), scale_value(5))
            )

    def run(self):
        clock = pygame.time.Clock()
        game_music = GameMusic()
        game_music.start()
        running = True
        paused = False
        pause_selection = 0
        confirm_return = False
        confirm_selection = 1

        while running:
            screen.fill(BLACK)
            if not paused:
                self.starfield.update()
            self.starfield.draw(screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == GAME_MUSIC_END:
                    game_music.play_next()
                
                if event.type == pygame.KEYDOWN:
                    if paused:
                        if confirm_return:
                            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                                confirm_selection = 1 - confirm_selection
                            elif event.key == pygame.K_RETURN:
                                if confirm_selection == 0:
                                    game_music.stop()
                                    return True
                                confirm_return = False
                            elif event.key in (pygame.K_ESCAPE, pygame.K_p):
                                confirm_return = False
                        elif event.key == pygame.K_p:
                            paused = False
                        elif event.key in (pygame.K_UP, pygame.K_DOWN):
                            pause_selection = 1 - pause_selection
                        elif event.key == pygame.K_RETURN:
                            if pause_selection == 0:
                                paused = False
                            else:
                                confirm_return = True
                        continue

                    if event.key == pygame.K_p and self.player.lives > 0:
                        paused = True
                    elif event.key == pygame.K_SPACE and self.player.lives > 0:
                        if self.player.shoot(self.player_bullets):
                            self.sounds.play("shoot")
                    elif event.key == pygame.K_r and self.player.lives <= 0:
                        self.__init__(self.difficulty, self.map_name)

                if event.type == pygame.MOUSEBUTTONDOWN and not paused:
                    if event.button == 3 and self.player.lives > 0:
                        if self.player.shoot(self.player_bullets):
                            self.sounds.play("shoot")

            if not running:
                break

            if self.player.lives > 0:
                if not paused:
                    self.player_group.update()
                    self.move_aliens_logic()
                    self.enemy_shooting_logic()
                    self.boss_group.update()
                    boss = self.boss_group.sprite
                    if boss is not None:
                        boss.shoot_timer -= 1
                        if boss.shoot_timer <= 0:
                            boss.shoot(self.alien_bullets)
                    self.ufo_group.update()
                    self.player_bullets.update()
                    self.alien_bullets.update()
                    self.powerups.update()
                    self.particles.update()
                    
                    self.handle_collisions()
                    self.manage_waves_and_boss()
                    self.update_records()

                if self.player.lives <= 0 and not self.game_over_played:
                    self.sounds.play("game_over")
                    self.game_over_played = True
                
                self.player_group.draw(screen)
                self.player.draw_shield(screen)
                self.aliens.draw(screen)
                self.boss_group.draw(screen)
                self.ufo_group.draw(screen)
                self.bunkers.draw(screen)
                self.powerups.draw(screen)
                self.player_bullets.draw(screen)
                self.alien_bullets.draw(screen)
                self.particles.draw(screen)
            else:
                game_over_surf = font_large.render("GAME OVER", True, RED)
                restart_surf = font_ui.render("Pulsa 'R' para reiniciar", True, WHITE)
                screen.blit(
                    game_over_surf,
                    game_over_surf.get_rect(
                        center=(WIDTH // 2, HEIGHT // 2 - scale_value(50))
                    )
                )
                screen.blit(
                    restart_surf,
                    restart_surf.get_rect(
                        center=(WIDTH // 2, HEIGHT // 2 + scale_value(20))
                    )
                )

            self.draw_ui(screen)
            if paused:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))

                if confirm_return:
                    title = font_large.render("¿Volver al menú?", True, CYAN)
                    yes_color = YELLOW if confirm_selection == 0 else WHITE
                    no_color = YELLOW if confirm_selection == 1 else WHITE
                    yes_text = font_menu.render("Sí", True, yes_color)
                    no_text = font_menu.render("No", True, no_color)
                    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
                    screen.blit(yes_text, yes_text.get_rect(center=(WIDTH // 2 - 70, HEIGHT // 2 + 10)))
                    screen.blit(no_text, no_text.get_rect(center=(WIDTH // 2 + 70, HEIGHT // 2 + 10)))
                else:
                    title = font_large.render("PAUSA", True, CYAN)
                    continue_color = YELLOW if pause_selection == 0 else WHITE
                    menu_color = YELLOW if pause_selection == 1 else WHITE
                    continue_text = font_menu.render("Continuar", True, continue_color)
                    menu_text = font_menu.render("Volver al menú", True, menu_color)
                    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))
                    screen.blit(continue_text, continue_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
                    screen.blit(menu_text, menu_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55)))
                    pause_help = font_ui.render("P: continuar   FLECHAS: elegir   ENTER: confirmar", True, WHITE)
                    screen.blit(pause_help, pause_help.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 115)))
                if confirm_return:
                    confirm_help = font_ui.render("IZQ./DER.: elegir   ENTER: confirmar", True, WHITE)
                    screen.blit(confirm_help, confirm_help.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 65)))

            pygame.display.flip()
            clock.tick(FPS)

        game_music.stop()
        return False

if __name__ == "__main__":
    if show_intro():
        while True:
            menu_selection = show_menu()
            if menu_selection is None:
                break
            difficulty, map_name = menu_selection
            pygame.mixer.music.stop()
            game = GameManager(difficulty, map_name)
            if not game.run():
                break

    pygame.quit()
    sys.exit()

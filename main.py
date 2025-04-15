import pygame
import sys
import random
import math
import os

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19) # For bandits
GRAY = (128, 128, 128) # For civilians
YELLOW = (255, 255, 0) # For cash text
DARK_RED = (139, 0, 0) # For dead bandits
SKY_BLUE = (135, 206, 235)
SANDY_BROWN = (244, 164, 96)
BUILDING_BROWN = (160, 82, 45)

# Scale Factor
SCALE_FACTOR = 1.5

# Character settings
CHARACTER_WIDTH = int(50 * SCALE_FACTOR) # Base width 50
CHARACTER_HEIGHT = int(80 * SCALE_FACTOR) # Base height 80
BANDIT_SPAWN_RATE = 1.5 # Lower means faster spawns (seconds)
CIVILIAN_SPAWN_RATE = 3.0
MAX_CHARACTERS_ON_SCREEN = 5 # Limit total bandits + civilians
DEAD_BANDIT_DESPAWN_TIME = 5000 # milliseconds (5 seconds)
AMMO_PER_COLLECT = 2
CIVILIAN_SPEED = 2
MAX_BANDITS_ON_SCREEN = 4 # Specific limit for bandits

# Difficulty Scaling
KILLS_PER_LEVEL = 5
SPAWN_RATE_DECREASE_PER_LEVEL = 0.1 # seconds
MIN_BANDIT_SPAWN_RATE = 0.5 # seconds

# Player settings
MAX_PLAYER_HEALTH = 3
MAX_TOTAL_HEALTH = 5 # Maximum possible health

# Bandit settings
BANDIT_MIN_SHOOT_DELAY = 2000 # ms (2 seconds)
BANDIT_MAX_SHOOT_DELAY = 5000 # ms (5 seconds)

# Item settings
HEALTH_PACK_DROP_CHANCE = 0.20 # 20% chance
HEALTH_PACK_SIZE = int(20 * SCALE_FACTOR) # Base size 20
HEALTH_PACK_DESPAWN_TIME = 7000 # ms (7 seconds)

# Visuals
SHOT_LINE_DURATION = 100 # ms (0.1 seconds)
PLAYER_SHOT_COLOR = YELLOW
BANDIT_SHOT_COLOR = RED

# Game states
PLAYING = 0
GAME_OVER = 1
START_SCREEN = 2

# --- Asset Loading Helper ---
def load_image(filename, use_alpha=True):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    try:
        image = pygame.image.load(filepath)
        if use_alpha:
            image = image.convert_alpha() # Optimize for transparency
        else:
            image = image.convert() # Optimize for opaque images
        print(f"Successfully loaded image: {filename}")
        return image
    except pygame.error as e:
        print(f"Cannot load image: {filename} - {e}")
        return None
    except FileNotFoundError:
        print(f"Image file not found: {filename}")
        return None

# --- Game Setup ---
pygame.init()
pygame.mixer.init() # Initialize the mixer
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Western Shooter")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36) # Default font

# --- Load Optional Assets (after display init) ---
background_img = load_image("background.png", use_alpha=False)
building_img = load_image("building.png")
bandit_img = load_image("bandit.png")
civilian_img = load_image("civilian.png")
dead_bandit_img = load_image("dead_bandit.png") # Optional: If needed later
# health_pack_img = load_image("health_pack.png") # Optional: If needed later
start_background_img = load_image("start_background.png", use_alpha=False)

# --- Load and Play Optional Background Music ---
try:
    music_path = os.path.join(os.path.dirname(__file__), "background.mp3")
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.play(loops=-1) # Play indefinitely
    print("Successfully loaded and playing background.mp3")
except FileNotFoundError:
    print("Background music file 'background.mp3' not found. Skipping music.")
except pygame.error as e:
    print(f"Cannot load background music 'background.mp3': {e}. Skipping music.")

# Hide the default mouse cursor
pygame.mouse.set_visible(False)

# --- Character Classes ---
class Character:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.spawn_time = pygame.time.get_ticks()
        self.visible_duration = random.uniform(2000, 5000) # Visible for 2-5 seconds (ms)
        self.image = None # Placeholder for optional image

    def draw(self, surface):
        if self.image:
            # Scale image to fit the character's rect and blit it
            scaled_image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
            surface.blit(scaled_image, self.rect.topleft)
        else:
            pygame.draw.rect(surface, self.color, self.rect)

    def is_expired(self):
        return pygame.time.get_ticks() - self.spawn_time > self.visible_duration

class Bandit(Character):
    def __init__(self, x, y):
        super().__init__(x, y, CHARACTER_WIDTH, CHARACTER_HEIGHT, BROWN)
        self.cash_value = 100
        self.time_until_shoot = random.randint(BANDIT_MIN_SHOOT_DELAY, BANDIT_MAX_SHOOT_DELAY)
        self.last_update_time = pygame.time.get_ticks()
        self.image = bandit_img # Assign loaded image (or None)

        # Flip image if spawning on the right half and image exists
        if x > SCREEN_WIDTH / 2 and self.image:
             self.image = pygame.transform.flip(self.image, True, False) # Flip horizontally

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        time_elapsed = current_time - self.last_update_time
        self.last_update_time = current_time

        self.time_until_shoot -= time_elapsed
        if self.time_until_shoot <= 0:
            return True # Indicates bandit wants to shoot
        return False

    def reset_shoot_timer(self):
        self.time_until_shoot = random.randint(BANDIT_MIN_SHOOT_DELAY, BANDIT_MAX_SHOOT_DELAY)
        self.last_update_time = pygame.time.get_ticks() # Reset update timer too

class Civilian(Character):
    def __init__(self):
        self.direction = random.choice([-1, 1]) # -1 for left, 1 for right
        spawn_y = random.randint(SCREEN_HEIGHT // 2 + 10, SCREEN_HEIGHT - CHARACTER_HEIGHT - 10) # Spawn on the ground

        if self.direction == 1: # Moving right
            spawn_x = -CHARACTER_WIDTH # Start just off-screen left
        else: # Moving left
            spawn_x = SCREEN_WIDTH # Start just off-screen right

        # Call super().__init__ *after* determining position
        super().__init__(spawn_x, spawn_y, CHARACTER_WIDTH, CHARACTER_HEIGHT, GRAY)
        # Civilians don't expire based on time, but on leaving screen
        self.visible_duration = float('inf')
        self.image = civilian_img # Assign loaded image (or None)

        # Flip image if moving left and image exists
        if self.direction == -1 and self.image:
            self.image = pygame.transform.flip(self.image, True, False) # Flip horizontally

    def update(self):
        self.rect.x += self.direction * CIVILIAN_SPEED

    def is_offscreen(self):
        if self.direction == 1: # Moving right
            return self.rect.left > SCREEN_WIDTH
        else: # Moving left
            return self.rect.right < 0

    def is_despawned(self):
        # Civilians despawn by going offscreen
        return self.is_offscreen()

class DeadBandit:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, CHARACTER_WIDTH, CHARACTER_HEIGHT // 2) # Shorter when dead
        self.color = DARK_RED
        self.death_time = pygame.time.get_ticks()
        self.image = dead_bandit_img # Assign loaded image (or None)

    def draw(self, surface):
        if self.image:
            scaled_image = pygame.transform.scale(self.image, self.rect.size)
            surface.blit(scaled_image, self.rect.topleft)
        else:
            pygame.draw.rect(surface, self.color, self.rect) # Fallback

    def is_despawned(self):
        return pygame.time.get_ticks() - self.death_time > DEAD_BANDIT_DESPAWN_TIME

# --- Item Classes ---
class HealthPack:
    def __init__(self, x, y):
        # Center the pack where the bandit died
        center_x = x + CHARACTER_WIDTH / 2
        center_y = y + (CHARACTER_HEIGHT // 2) / 2
        self.rect = pygame.Rect(center_x - HEALTH_PACK_SIZE // 2,
                               center_y - HEALTH_PACK_SIZE // 2,
                               HEALTH_PACK_SIZE, HEALTH_PACK_SIZE)
        self.color = WHITE
        self.spawn_time = pygame.time.get_ticks()

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        # Simple '+' sign
        pygame.draw.line(surface, RED, (self.rect.centerx - 5, self.rect.centery), (self.rect.centerx + 5, self.rect.centery), 3)
        pygame.draw.line(surface, RED, (self.rect.centerx, self.rect.centery - 5), (self.rect.centerx, self.rect.centery + 5), 3)

    def is_despawned(self):
        return pygame.time.get_ticks() - self.spawn_time > HEALTH_PACK_DESPAWN_TIME

# --- Effects Classes ---
class ShotEffect:
    def __init__(self, start_pos, end_pos, color):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.creation_time = pygame.time.get_ticks()

    def is_expired(self):
        return pygame.time.get_ticks() - self.creation_time > SHOT_LINE_DURATION

    def draw(self, surface):
        pygame.draw.line(surface, self.color, self.start_pos, self.end_pos, 2)

# --- Game Variables ---
game_state = START_SCREEN # Start with the start screen
score = 0
ammo = 6 # Revolver capacity
player_health = MAX_PLAYER_HEALTH
bandits = []
civilians = []
dead_bandits = []
last_bandit_spawn_time = 0
last_civilian_spawn_time = 0
player_shot_effects = []
bandit_shot_effects = []
bandits_killed = 0
health_packs = []

def reset_game():
    global score, ammo, game_state, bandits, civilians, dead_bandits, last_bandit_spawn_time, last_civilian_spawn_time, player_health, player_shot_effects, bandit_shot_effects, bandits_killed, health_packs
    score = 0
    ammo = 6
    player_health = MAX_PLAYER_HEALTH
    bandits = []
    civilians = []
    dead_bandits = []
    last_bandit_spawn_time = pygame.time.get_ticks() # Reset spawn timers
    last_civilian_spawn_time = pygame.time.get_ticks()
    player_shot_effects = []
    bandit_shot_effects = []
    bandits_killed = 0
    health_packs = []
    game_state = PLAYING
    pygame.mouse.set_visible(False)

# --- Game Loop ---
running = True
while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif game_state == START_SCREEN:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                reset_game() # This sets state to PLAYING
        elif game_state == PLAYING:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if event.button == 1: # Left click - Shoot / Collect Health Pack / Collect Ammo
                    collected_pack = False
                    collected_ammo = False

                    # 1. Check for Health Pack Collection First
                    for i in range(len(health_packs) - 1, -1, -1):
                        pack = health_packs[i]
                        if pack.rect.collidepoint(mouse_pos):
                            if player_health < MAX_TOTAL_HEALTH:
                                player_health += 1
                                print(f"Collected Health Pack! Health: {player_health}")
                                # TODO: Play health pack sound
                            else:
                                print("Already at max health!")
                                # TODO: Play different sound? (optional)
                            health_packs.pop(i)
                            collected_pack = True
                            break # Collected one pack

                    # 2. If no pack, check for Dead Bandit Ammo Collection
                    if not collected_pack:
                        for i in range(len(dead_bandits) - 1, -1, -1):
                            dead_bandit = dead_bandits[i]
                            if dead_bandit.rect.collidepoint(mouse_pos):
                                ammo += AMMO_PER_COLLECT
                                print(f"Collected Ammo! Ammo: {ammo}")
                                # TODO: Play ammo collect sound
                                dead_bandits.pop(i)
                                collected_ammo = True
                                break # Collected ammo from one

                    # 3. If nothing collected, proceed with shooting logic
                    if not collected_pack and not collected_ammo:
                        if ammo > 0:
                            ammo -= 1
                            shot_fired = True # Flag to ensure only one hit per shot

                            # Add player shot effect
                            player_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 10)
                            player_shot_effects.append(ShotEffect(player_pos, mouse_pos, PLAYER_SHOT_COLOR))

                            # Check hit on Bandits (reverse order so top ones are hit first)
                            for i in range(len(bandits) - 1, -1, -1):
                                bandit = bandits[i]
                                if bandit.rect.collidepoint(mouse_pos):
                                    score += bandit.cash_value
                                    bandits_killed += 1
                                    bandit_death_pos_x = bandit.rect.x
                                    bandit_death_pos_y = bandit.rect.bottom - CHARACTER_HEIGHT // 2
                                    dead_bandits.append(DeadBandit(bandit_death_pos_x, bandit_death_pos_y))

                                    # Chance to drop health pack
                                    if random.random() < HEALTH_PACK_DROP_CHANCE:
                                        health_packs.append(HealthPack(bandit_death_pos_x, bandit_death_pos_y))
                                        print("Bandit dropped a health pack!")

                                    bandits.pop(i)
                                    shot_fired = False # Hit consumed
                                    # TODO: Play hit sound
                                    break # Stop checking after hitting one

                            # Check hit on Civilians only if no bandit was hit
                            if shot_fired:
                                for i in range(len(civilians) - 1, -1, -1):
                                    civilian = civilians[i]
                                    if civilian.rect.collidepoint(mouse_pos):
                                        print("Hit a civilian! Game Over.")
                                        game_state = GAME_OVER
                                        # TODO: Play game over sound
                                        break # Stop checking
                        else:
                            print("Click! Out of ammo.")
                            # TODO: Play empty click sound?
            elif game_state == GAME_OVER:
                if event.button == 1: # Left click to restart
                    reset_game()

    # --- Game Logic ---
    if game_state == PLAYING:
        current_time = pygame.time.get_ticks()
        dt = clock.tick(FPS) # Get time since last frame in ms

        # --- Spawning Logic ---
        total_characters = len(bandits) + len(civilians)

        # Calculate current level and spawn rate
        current_level = bandits_killed // KILLS_PER_LEVEL
        spawn_rate_reduction = current_level * SPAWN_RATE_DECREASE_PER_LEVEL
        actual_bandit_spawn_rate_seconds = max(MIN_BANDIT_SPAWN_RATE, BANDIT_SPAWN_RATE - spawn_rate_reduction)
        actual_bandit_spawn_rate_ms = actual_bandit_spawn_rate_seconds * 1000

        # Spawn Bandits
        if len(bandits) < MAX_BANDITS_ON_SCREEN and current_time - last_bandit_spawn_time > actual_bandit_spawn_rate_ms:
            spawn_x = random.randint(0, SCREEN_WIDTH - CHARACTER_WIDTH)
            # Spawn near the middle vertically for a street feel
            spawn_y = random.randint(SCREEN_HEIGHT // 3, SCREEN_HEIGHT - CHARACTER_HEIGHT - 50)
            bandits.append(Bandit(spawn_x, spawn_y))
            last_bandit_spawn_time = current_time

        # Spawn Civilians
        if total_characters < MAX_CHARACTERS_ON_SCREEN and current_time - last_civilian_spawn_time > CIVILIAN_SPAWN_RATE * 1000:
            civilians.append(Civilian())
            last_civilian_spawn_time = current_time

        # --- Update Characters (Remove expired ones) ---
        bandits[:] = [b for b in bandits if not b.is_expired()]
        # civilians[:] = [c for c in civilians if not c.is_expired()]
        # Civilians are removed when they go offscreen
        civilians[:] = [c for c in civilians if not c.is_offscreen()]

        # --- Update Bandits (Shooting) ---
        for bandit in bandits:
            if bandit.update(dt):
                player_health -= 1
                print(f"Ouch! Player health: {player_health}")

                # Add bandit shot effect
                bandit_pos = bandit.rect.center
                player_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 10)
                bandit_shot_effects.append(ShotEffect(bandit_pos, player_pos, BANDIT_SHOT_COLOR))

                # TODO: Play player hit sound
                # TODO: Add visual indicator of being shot (screen flash?)
                bandit.reset_shoot_timer()
                if player_health <= 0:
                    print("Player died! Game Over.")
                    game_state = GAME_OVER
                    break # Stop processing further bandit shots this frame

        # Update Dead Bandits (Remove despawned ones)
        dead_bandits = [db for db in dead_bandits if not db.is_despawned()]

        # Update health packs (remove despawned)
        health_packs[:] = [pack for pack in health_packs if not pack.is_despawned()]

        # Update shot effects (remove expired)
        player_shot_effects[:] = [effect for effect in player_shot_effects if not effect.is_expired()]
        bandit_shot_effects[:] = [effect for effect in bandit_shot_effects if not effect.is_expired()]

        # Check if ammo is zero and no way to get more (no dead bandits)
        if ammo <= 0 and not dead_bandits and not bandits: # Also check bandits to prevent immediate loss if one is about to die
            print("Out of ammo and targets! Game Over.")
            game_state = GAME_OVER

        # --- Update Civilian Positions ---
        for civilian in civilians:
            civilian.update()

    # --- Drawing ---
    screen.fill(BLACK) # Default background if no image

    if game_state == START_SCREEN:
        pygame.mouse.set_visible(True)
        if start_background_img:
            scaled_start_bg = pygame.transform.scale(start_background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(scaled_start_bg, (0,0))
        else:
            screen.fill(BLACK) # Fallback background

        title_font = pygame.font.Font(None, 72)
        start_font = pygame.font.Font(None, 48)
        title_text = title_font.render("Western Shooter", True, YELLOW)
        start_text = start_font.render("Click to Start", True, WHITE)

        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 3 - title_text.get_height() // 2))
        screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, SCREEN_HEIGHT // 2))

    elif game_state == PLAYING:
        # Draw Background
        if background_img:
            scaled_bg = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(scaled_bg, (0, 0))
        else:
            # Fallback to colored rectangles
            # Sky
            pygame.draw.rect(screen, SKY_BLUE, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            # Ground
            pygame.draw.rect(screen, SANDY_BROWN, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))

        # Simple Buildings (drawn before characters)
        building_rects = [
            pygame.Rect(50, SCREEN_HEIGHT // 2 - 150, 100 * 2, 150 * 2),
            pygame.Rect(200, SCREEN_HEIGHT // 2 - 120, 120 * 2, 120 * 2),
            pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT // 2 - 170, 100 * 2, 170 * 2)
        ]
        if building_img:
            for rect in building_rects:
                scaled_building = pygame.transform.scale(building_img, rect.size)
                screen.blit(scaled_building, rect.topleft)
        else:
            # Fallback to colored rectangles
            for rect in building_rects:
                pygame.draw.rect(screen, BUILDING_BROWN, rect)

        # Draw Bandits
        for bandit in bandits:
            bandit.draw(screen)

        # Draw Civilians
        for civilian in civilians:
            civilian.draw(screen)

        # Draw Dead Bandits
        for dead_bandit in dead_bandits:
            dead_bandit.draw(screen)

        # Draw Health Packs
        for pack in health_packs:
            pack.draw(screen)

        # Draw Shot Effects
        for effect in player_shot_effects:
            effect.draw(screen)
        for effect in bandit_shot_effects:
            effect.draw(screen)

        # Draw UI
        score_text = font.render(f"Cash: ${score}", True, YELLOW)
        ammo_text = font.render(f"Ammo: {ammo}", True, WHITE)
        health_text = font.render(f"Health: {player_health}", True, RED)
        screen.blit(score_text, (10, 10))
        screen.blit(ammo_text, (SCREEN_WIDTH - ammo_text.get_width() - 10, 10))
        screen.blit(health_text, (SCREEN_WIDTH // 2 - health_text.get_width() // 2, 10))

        # Draw Level Info
        level_text = font.render(f"Level: {current_level + 1}", True, WHITE)
        kills_text = font.render(f"Kills: {bandits_killed}", True, WHITE)
        screen.blit(level_text, (10, 40))
        screen.blit(kills_text, (10, 70))

        # Draw Crosshair
        mouse_x, mouse_y = pygame.mouse.get_pos()
        crosshair_color = WHITE
        pygame.draw.line(screen, crosshair_color, (mouse_x - 15, mouse_y), (mouse_x + 15, mouse_y), 2)
        pygame.draw.line(screen, crosshair_color, (mouse_x, mouse_y - 15), (mouse_x, mouse_y + 15), 2)
        pygame.draw.circle(screen, crosshair_color, (mouse_x, mouse_y), 10, 1)

    elif game_state == GAME_OVER:
        pygame.mouse.set_visible(True) # Ensure mouse is visible on game over
        # TODO: Draw Game Over screen
        game_over_text = font.render("GAME OVER", True, RED)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        final_score_text = font.render(f"Final Cash: ${score}", True, YELLOW)
        screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2))
        reason_text = ""
        if player_health <= 0:
            reason_text = font.render("You were shot!", True, WHITE)
        elif ammo <= 0 and not dead_bandits and not bandits:
             reason_text = font.render("Out of ammo!", True, WHITE)
        else: # Must have shot a civilian
             reason_text = font.render("You shot a civilian!", True, WHITE)

        screen.blit(reason_text, (SCREEN_WIDTH // 2 - reason_text.get_width() // 2, SCREEN_HEIGHT // 2 + 25))

        restart_text = font.render("Click to Restart", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 75))

    # --- Update Display ---
    pygame.display.flip()

    # --- Frame Rate Control ---
    clock.tick(FPS)

# --- Cleanup ---
pygame.mixer.music.stop() # Stop music before quitting
pygame.quit()
sys.exit() 
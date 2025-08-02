import pygame
import random
import math
import sys

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Screen dimensions and frame rate
WIDTH = 1200
HEIGHT = 800
FPS = 60

# Enhanced color palette with better contrast and visual appeal
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (64, 128, 255)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
PURPLE = (155, 89, 182)
ORANGE = (230, 126, 34)
YELLOW = (241, 196, 15)

# Background gradient colors
DARK_BLUE = (15, 32, 60)
LIGHT_BLUE = (52, 152, 219)
MIDNIGHT_BLUE = (8, 20, 40)

# Platform colors
BROWN = (101, 67, 33)
DARK_GREEN = (39, 174, 96)
PLATFORM_GRAY = (108, 122, 137)
PLATFORM_HIGHLIGHT = (149, 165, 180)

# UI colors
UI_BACKGROUND = (44, 62, 80)
UI_TEXT = (236, 240, 241)
WARNING_RED = (192, 57, 43)
SUCCESS_GREEN = (39, 174, 96)

class Player:
    def __init__(self, x, y, color=BLUE):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 40
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 8
        self.jump_power = -15
        self.gravity = 0.8
        self.on_ground = False
        self.color = color
        self.is_dead = False
        self.death_timer = 0
        self.death_animation_duration = 60
        self.is_stunned = False
        self.stun_timer = 0
        self.stun_duration = 120  # 2 seconds at 60 FPS
        self.tag_cooldown = 0
        self.tag_cooldown_duration = 30  # 0.5 second cooldown
        self.punch_cooldown = 0
        self.punch_cooldown_duration = 20  # 0.33 second cooldown
        self.throw_cooldown = 0
        self.throw_cooldown_duration = 60  # 1 second cooldown

    def update(self, terrain, controls, other_players):
        if self.is_dead:
            self.death_timer += 1
            self.vel_y += self.gravity * 0.5
            self.y += self.vel_y
            return self.death_timer >= self.death_animation_duration

        # Update stun timer
        if self.is_stunned:
            self.stun_timer += 1
            if self.stun_timer >= self.stun_duration:
                self.is_stunned = False
                self.stun_timer = 0

        # Update tag cooldown
        if self.tag_cooldown > 0:
            self.tag_cooldown -= 1

        # Update punch cooldown
        if self.punch_cooldown > 0:
            self.punch_cooldown -= 1

        # Update throw cooldown
        if self.throw_cooldown > 0:
            self.throw_cooldown -= 1

        # Don't allow movement during terrain morphing or when stunned
        if not terrain.is_morphing and not self.is_stunned:
            keys = pygame.key.get_pressed()

            # Check for tag input
            if keys[controls['tag']] and self.tag_cooldown == 0:
                for other_player in other_players:
                    if other_player != self:
                        self.try_tag(other_player)

            # Check for punch input
            if keys[controls['punch']] and self.punch_cooldown == 0:
                for other_player in other_players:
                    if other_player != self:
                        self.try_punch(other_player)

            # Check for throw input
            if keys[controls['throw']] and self.throw_cooldown == 0:
                for other_player in other_players:
                    if other_player != self:
                        self.try_throw(other_player)

            if keys[controls['left']]:
                self.vel_x = -self.speed
            elif keys[controls['right']]:
                self.vel_x = self.speed
            else:
                self.vel_x *= 0.8

            if keys[controls['jump']] and self.on_ground:
                self.vel_y = self.jump_power
                self.on_ground = False
        else:
            # During morphing or stunned, apply friction but no input
            self.vel_x *= 0.9

        self.vel_y += self.gravity

        self.x += self.vel_x
        self.y += self.vel_y

        if self.x < 0:
            self.x = 0
        elif self.x > WIDTH - self.width:
            self.x = WIDTH - self.width

        return self.check_terrain_collision(terrain)

    def die(self):
        self.is_dead = True
        self.death_timer = 0
        self.vel_x = random.randint(-5, 5)
        self.vel_y = -8

    def try_tag(self, other_player):
        # Check if players are close enough to tag
        distance = ((self.x - other_player.x) ** 2 + (self.y - other_player.y) ** 2) ** 0.5
        tag_range = 60  # pixels

        if distance <= tag_range and not other_player.is_dead and not other_player.is_stunned:
            other_player.is_stunned = True
            other_player.stun_timer = 0
            self.tag_cooldown = self.tag_cooldown_duration

    def try_punch(self, other_player):
        # Check if players are close enough to punch
        distance = ((self.x - other_player.x) ** 2 + (self.y - other_player.y) ** 2) ** 0.5
        punch_range = 50  # pixels

        if distance <= punch_range and not other_player.is_dead:
            # Calculate knockback direction
            dx = other_player.x - self.x
            dy = other_player.y - self.y

            # Normalize direction
            if distance > 0:
                dx /= distance
                dy /= distance

            # Apply knockback
            knockback_force = 12
            other_player.vel_x += dx * knockback_force
            other_player.vel_y += dy * knockback_force - 3  # Slight upward component

            self.punch_cooldown = self.punch_cooldown_duration

    def try_throw(self, other_player):
        # Check if players are close enough to throw
        distance = ((self.x - other_player.x) ** 2 + (self.y - other_player.y) ** 2) ** 0.5
        throw_range = 45  # pixels

        if distance <= throw_range and not other_player.is_dead:
            # Calculate direction towards center of stage
            stage_center_x = WIDTH // 2
            stage_center_y = HEIGHT // 2
            
            # Calculate direction from thrown player to stage center
            dx = stage_center_x - other_player.x
            dy = stage_center_y - other_player.y
            
            # Normalize direction
            center_distance = (dx ** 2 + dy ** 2) ** 0.5
            if center_distance > 0:
                dx /= center_distance
                dy /= center_distance
            
            # Apply throw force towards center
            throw_force_x = 15
            throw_force_y = -12  # Always have upward component for arc
            
            other_player.vel_x = dx * throw_force_x
            other_player.vel_y = dy * throw_force_x + throw_force_y  # Combine center direction with upward arc
            other_player.on_ground = False

            self.throw_cooldown = self.throw_cooldown_duration

    def check_terrain_collision(self, terrain):
        self.on_ground = False
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # Check collision with holes (player falls through)
        for hole in terrain.holes:
            if player_rect.colliderect(hole) and self.y + self.height >= hole.y:
                if not self.is_dead:
                    self.die()
                return False

        for platform in terrain.platforms:
            if player_rect.colliderect(platform):
                # Check if platform is cut by a hole
                platform_cut = False
                for hole in terrain.holes:
                    if (hole.x < platform.x + platform.width and 
                        hole.x + hole.width > platform.x and
                        hole.y == platform.y):
                        # Platform is cut by hole, check if player is in the hole area
                        if (self.x + self.width > hole.x and 
                            self.x < hole.x + hole.width):
                            platform_cut = True
                            break

                if not platform_cut:
                    if self.vel_y > 0:
                        self.y = platform.top - self.height
                        self.vel_y = 0
                        self.on_ground = True
                    elif self.vel_y < 0:
                        self.y = platform.bottom
                        self.vel_y = 0

        if self.y > HEIGHT:
            if not self.is_dead:
                self.die()
            return False
        return False

    def draw(self, screen):
        if self.is_dead:
            # Enhanced death animation with particles
            rotation_angle = (self.death_timer * 10) % 360
            death_color = RED if self.death_timer % 10 < 5 else ORANGE

            # Draw death particles around player
            for i in range(8):
                particle_angle = (rotation_angle + i * 45) % 360
                particle_x = self.x + 15 + 20 * math.cos(math.radians(particle_angle))
                particle_y = self.y + 20 + 15 * math.sin(math.radians(particle_angle))
                particle_size = 3 - (self.death_timer % 20) // 7
                if particle_size > 0:
                    pygame.draw.circle(screen, ORANGE, (int(particle_x), int(particle_y)), particle_size)

            # Draw spinning death effect with gradient
            death_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            pygame.draw.rect(screen, death_color, death_rect)

            # Add inner glow effect
            inner_color = (255, 200, 200) if self.death_timer % 10 < 5 else (255, 220, 180)
            inner_rect = pygame.Rect(self.x + 3, self.y + 3, self.width - 6, self.height - 6)
            pygame.draw.rect(screen, inner_color, inner_rect)

            # Draw X eyes for death
            eye_color = BLACK
            pygame.draw.line(screen, eye_color, (self.x + 6, self.y + 8), (self.x + 10, self.y + 12), 3)
            pygame.draw.line(screen, eye_color, (self.x + 10, self.y + 8), (self.x + 6, self.y + 12), 3)
            pygame.draw.line(screen, eye_color, (self.x + 20, self.y + 8), (self.x + 24, self.y + 12), 3)
            pygame.draw.line(screen, eye_color, (self.x + 24, self.y + 8), (self.x + 20, self.y + 12), 3)

            # Add glowing outline
            pygame.draw.rect(screen, WHITE, death_rect, 1)
            pygame.draw.rect(screen, BLACK, death_rect, 3)
        else:
            # Enhanced player drawing with shadows and effects
            player_color = self.color
            shadow_color = (max(0, self.color[0] - 60), max(0, self.color[1] - 60), max(0, self.color[2] - 60))

            if self.is_stunned:
                # Pulsing effect when stunned
                pulse = abs(math.sin(self.stun_timer * 0.2)) * 0.5 + 0.5
                player_color = tuple(int(c * pulse + 128 * (1 - pulse)) for c in self.color)

            # Draw shadow
            shadow_rect = pygame.Rect(self.x + 2, self.y + 2, self.width, self.height)
            pygame.draw.rect(screen, shadow_color, shadow_rect)

            # Draw main body with gradient effect
            main_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            pygame.draw.rect(screen, player_color, main_rect)

            # Add highlight on top half
            highlight_color = tuple(min(255, c + 40) for c in player_color)
            highlight_rect = pygame.Rect(self.x + 2, self.y + 2, self.width - 4, self.height // 2 - 2)
            pygame.draw.rect(screen, highlight_color, highlight_rect)

            # Enhanced eyes
            if self.is_stunned:
                # Swirling spiral eyes
                pygame.draw.circle(screen, WHITE, (int(self.x + 8), int(self.y + 10)), 5)
                pygame.draw.circle(screen, WHITE, (int(self.x + 22), int(self.y + 10)), 5)

                angle = (self.stun_timer * 15) % 360
                for i in range(3):
                    spiral_radius = 2 + i
                    spiral_angle = angle + i * 120
                    spiral_x1 = int(self.x + 8 + spiral_radius * math.cos(math.radians(spiral_angle)))
                    spiral_y1 = int(self.y + 10 + spiral_radius * math.sin(math.radians(spiral_angle)))
                    spiral_x2 = int(self.x + 22 + spiral_radius * math.cos(math.radians(spiral_angle)))
                    spiral_y2 = int(self.y + 10 + spiral_radius * math.sin(math.radians(spiral_angle)))
                    pygame.draw.circle(screen, BLACK, (spiral_x1, spiral_y1), 1)
                    pygame.draw.circle(screen, BLACK, (spiral_x2, spiral_y2), 1)
            else:
                # Normal eyes with shine
                pygame.draw.circle(screen, WHITE, (int(self.x + 8), int(self.y + 10)), 5)
                pygame.draw.circle(screen, WHITE, (int(self.x + 22), int(self.y + 10)), 5)
                pygame.draw.circle(screen, BLACK, (int(self.x + 8), int(self.y + 10)), 3)
                pygame.draw.circle(screen, BLACK, (int(self.x + 22), int(self.y + 10)), 3)
                # Eye shine
                pygame.draw.circle(screen, WHITE, (int(self.x + 9), int(self.y + 9)), 1)
                pygame.draw.circle(screen, WHITE, (int(self.x + 23), int(self.y + 9)), 1)

            # Enhanced legs with shoes
            leg_color = tuple(max(0, c - 30) for c in player_color)
            pygame.draw.rect(screen, leg_color, (self.x + 8, self.y + self.height, 6, 8))
            pygame.draw.rect(screen, leg_color, (self.x + 16, self.y + self.height, 6, 8))
            # Shoes
            pygame.draw.rect(screen, BLACK, (self.x + 6, self.y + self.height + 6, 10, 4))
            pygame.draw.rect(screen, BLACK, (self.x + 14, self.y + self.height + 6, 10, 4))

            # Enhanced outline with glow effect
            outline_width = 3 if self.is_stunned else 2
            if self.is_stunned:
                # Glowing outline when stunned
                glow_color = YELLOW
                for i in range(3):
                    pygame.draw.rect(screen, glow_color, main_rect, outline_width + i)

            pygame.draw.rect(screen, BLACK, main_rect, outline_width)

            # Floating stun indicator
            if self.is_stunned:
                remaining_time = (self.stun_duration - self.stun_timer) // 60 + 1
                # Background for text
                text_bg = pygame.Rect(self.x + 5, self.y - 25, 20, 15)
                pygame.draw.rect(screen, UI_BACKGROUND, text_bg)
                pygame.draw.rect(screen, WARNING_RED, text_bg, 2)

                stun_text = pygame.font.Font(None, 20).render(str(remaining_time), True, WHITE)
                screen.blit(stun_text, (self.x + 10, self.y - 23))

class TerrainSystem:
    def __init__(self, num_players=2):
        self.platforms = []
        self.holes = []
        self.morph_timer = 0
        self.base_morph_interval = 180
        self.morph_interval = self.base_morph_interval
        self.is_morphing = False
        self.morph_duration = 30
        self.morph_progress = 0
        self.num_players = num_players
        self.generate_initial_terrain()

    def generate_initial_terrain(self):
        self.platforms = [pygame.Rect(0, HEIGHT - 60, WIDTH, 60)]
        self.holes = []

        # Player starting positions based on number of players
        if self.num_players == 2:
            player_positions = [WIDTH // 3, 2 * WIDTH // 3]
        else:
            player_positions = [WIDTH // 4, WIDTH // 2, 3 * WIDTH // 4]

        safe_zone = 80  # Safe zone around each player

        # Create holes in the ground
        for _ in range(2):
            attempts = 0
            while attempts < 50:  # Prevent infinite loop
                hole_x = random.randint(100, WIDTH - 200)
                hole_width = random.randint(60, 120)

                # Check if hole would overlap with any player safe zones
                hole_overlaps_any_player = False
                for player_x in player_positions:
                    if (hole_x < player_x + safe_zone and 
                        hole_x + hole_width > player_x - safe_zone):
                        hole_overlaps_any_player = True
                        break

                if not hole_overlaps_any_player:
                    self.holes.append(pygame.Rect(hole_x, HEIGHT - 60, hole_width, 60))
                    break

                attempts += 1

        for _ in range(6):
            x = random.randint(100, WIDTH - 200)
            y = random.randint(200, HEIGHT - 150)
            width = random.randint(80, 200)
            height = 20
            self.platforms.append(pygame.Rect(x, y, width, height))

    def update(self, score):
        if self.is_morphing:
            self.morph_progress += 1
            if self.morph_progress >= self.morph_duration:
                self.is_morphing = False
                self.morph_progress = 0
        else:
            self.morph_timer += 1

            # Calculate faster interval based on score
            difficulty_factor = min(score // 500, 10)  # Every 50 points (500/10), increase difficulty
            self.morph_interval = max(self.base_morph_interval - (difficulty_factor * 20), 60)  # Minimum 1 second

            if self.morph_timer >= self.morph_interval:
                self.start_morph()
                self.morph_timer = 0

    def start_morph(self):
        self.is_morphing = True
        self.morph_progress = 0
        self.morph_terrain()

    def morph_terrain(self):
        ground = self.platforms[0]
        self.platforms = [ground]
        self.holes = []

        # Create new holes in the ground
        num_holes = random.randint(2, 5)
        for _ in range(num_holes):
            hole_x = random.randint(100, WIDTH - 200)
            hole_width = random.randint(60, 150)
            self.holes.append(pygame.Rect(hole_x, HEIGHT - 60, hole_width, 60))

        num_platforms = random.randint(4, 8)
        for _ in range(num_platforms):
            x = random.randint(0, WIDTH - 150)
            y = random.randint(150, HEIGHT - 150)
            width = random.randint(60, 250)
            height = random.randint(15, 25)

            if random.random() < 0.2:
                continue

            self.platforms.append(pygame.Rect(x, y, width, height))

        for platform in self.platforms[1:]:
            if random.random() < 0.1:
                platform.width = max(platform.width - random.randint(10, 30), 30)

    def draw(self, screen):
        time_to_morph = self.morph_interval - self.morph_timer
        shake_intensity = max(0, 30 - time_to_morph) * 0.5

        # Draw platforms with enhanced visuals
        for i, platform in enumerate(self.platforms):
            if shake_intensity > 0:
                shake_x = random.randint(-int(shake_intensity), int(shake_intensity))
                shake_y = random.randint(-int(shake_intensity//2), int(shake_intensity//2))
                draw_rect = pygame.Rect(platform.x + shake_x, platform.y + shake_y, 
                                      platform.width, platform.height)
            else:
                draw_rect = platform

            if i == 0:  # Ground platform
                # Draw ground with gradient
                base_color = DARK_GREEN
                top_color = GREEN

                # Draw gradient effect
                for y_offset in range(draw_rect.height):
                    ratio = y_offset / draw_rect.height
                    r = int(top_color[0] * (1 - ratio) + base_color[0] * ratio)
                    g = int(top_color[1] * (1 - ratio) + base_color[1] * ratio)
                    b = int(top_color[2] * (1 - ratio) + base_color[2] * ratio)
                    line_rect = pygame.Rect(draw_rect.x, draw_rect.y + y_offset, draw_rect.width, 1)
                    pygame.draw.rect(screen, (r, g, b), line_rect)

                # Add grass texture
                for x in range(draw_rect.x, draw_rect.x + draw_rect.width, 4):
                    grass_height = random.randint(3, 6)
                    grass_color = tuple(min(255, c + random.randint(-20, 20)) for c in GREEN)
                    pygame.draw.line(screen, grass_color, (x, draw_rect.y), (x, draw_rect.y - grass_height), 2)

                # Add some flowers
                if random.randint(1, 20) == 1:
                    flower_x = random.randint(draw_rect.x, draw_rect.x + draw_rect.width - 5)
                    flower_colors = [RED, YELLOW, PURPLE]
                    flower_color = random.choice(flower_colors)
                    pygame.draw.circle(screen, flower_color, (flower_x, draw_rect.y - 2), 2)
            else:  # Regular platforms
                # Draw platform with 3D effect
                main_color = PLATFORM_GRAY
                highlight_color = PLATFORM_HIGHLIGHT
                shadow_color = tuple(max(0, c - 40) for c in main_color)

                # Shadow
                shadow_rect = pygame.Rect(draw_rect.x + 2, draw_rect.y + 2, draw_rect.width, draw_rect.height)
                pygame.draw.rect(screen, shadow_color, shadow_rect)

                # Main platform
                pygame.draw.rect(screen, main_color, draw_rect)

                # Highlight on top
                highlight_rect = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, 4)
                pygame.draw.rect(screen, highlight_color, highlight_rect)

                # Add texture lines
                for y in range(draw_rect.y + 5, draw_rect.y + draw_rect.height - 2, 3):
                    pygame.draw.line(screen, shadow_color, (draw_rect.x + 2, y), (draw_rect.x + draw_rect.width - 2, y))

            # Enhanced outline
            pygame.draw.rect(screen, BLACK, draw_rect, 2)

        # Draw holes with enhanced danger effects
        for hole in self.holes:
            if shake_intensity > 0:
                shake_x = random.randint(-int(shake_intensity), int(shake_intensity))
                shake_y = random.randint(-int(shake_intensity//2), int(shake_intensity//2))
                draw_hole = pygame.Rect(hole.x + shake_x, hole.y + shake_y, 
                                      hole.width, hole.height)
            else:
                draw_hole = hole

            # Draw hole with glowing red edges
            pygame.draw.rect(screen, BLACK, draw_hole)

            # Pulsing red glow effect
            glow_intensity = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 100 + 100
            glow_color = (int(glow_intensity), 0, 0)

            # Multiple glow layers
            for i in range(4):
                glow_rect = pygame.Rect(draw_hole.x - i, draw_hole.y - i, draw_hole.width + 2*i, draw_hole.height + 2*i)
                pygame.draw.rect(screen, glow_color, glow_rect, 2)
                glow_color = tuple(max(0, c - 25) for c in glow_color)

            # Add danger particles
            for i in range(3):
                particle_x = hole.x + random.randint(0, hole.width)
                particle_y = hole.y + random.randint(0, hole.height // 2)
                particle_size = random.randint(1, 3)
                particle_color = (255, random.randint(100, 200), 0)
                pygame.draw.circle(screen, particle_color, (particle_x, particle_y), particle_size)

class StartScreen:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.large_font = pygame.font.Font(None, 72)
        self.medium_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        self.selected_option = 0
        self.options = ["2 Players", "3 Players"]

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.options)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.selected_option + 2
        return None

    def draw(self):
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            top_color = MIDNIGHT_BLUE
            bottom_color = LIGHT_BLUE
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))

        title_text = self.large_font.render("DREAM RUNNER", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        self.screen.blit(title_text, title_rect)

        subtitle_text = self.medium_font.render("Choose Player Mode", True, YELLOW)
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        self.screen.blit(subtitle_text, subtitle_rect)

        for i, option in enumerate(self.options):
            y_pos = HEIGHT // 2 + i * 80
            color = YELLOW if i == self.selected_option else WHITE

            if i == self.selected_option:
                option_bg = pygame.Rect(WIDTH // 2 - 100, y_pos - 25, 200, 50)
                pygame.draw.rect(self.screen, UI_BACKGROUND, option_bg)
                pygame.draw.rect(self.screen, YELLOW, option_bg, 3)

            option_text = self.medium_font.render(option, True, color)
            option_rect = option_text.get_rect(center=(WIDTH // 2, y_pos))
            self.screen.blit(option_text, option_rect)

        controls_text = self.small_font.render("Use UP/DOWN arrows and ENTER to select", True, WHITE)
        controls_rect = controls_text.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        self.screen.blit(controls_text, controls_rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Dream Runner")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.start_screen = StartScreen(self.screen, self.font)
        self.in_start_screen = True
        self.num_players = 2

        self.players = []
        self.terrain = None
        self.score = 0
        self.game_over = False
        self.winner = None
        self.player_scores = []
        self.round_end_timer = 0
        self.round_end_duration = 180  # 3 seconds at 60 FPS

        self.controls1 = {'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w, 'tag': pygame.K_q, 'punch': pygame.K_e, 'throw': pygame.K_s}
        self.controls2 = {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'jump': pygame.K_UP, 'tag': pygame.K_RSHIFT, 'punch': pygame.K_SLASH, 'throw': pygame.K_DOWN}
        self.controls3 = {'left': pygame.K_g, 'right': pygame.K_j, 'jump': pygame.K_y, 'tag': pygame.K_t, 'punch': pygame.K_u, 'throw': pygame.K_h}
        
        # Initialize music
        self.music_playing = False
        self.load_music()

    def load_music(self):
        """Load and start background music with error handling"""
        try:
            # Try to load common music file formats that might exist
            music_files = [
                "background_music.mp3",
                "music.mp3", 
                "bgm.mp3",
                "background_music.ogg",
                "music.ogg",
                "bgm.ogg",
                "background_music.wav",
                "music.wav",
                "bgm.wav"
            ]
            
            music_loaded = False
            for music_file in music_files:
                try:
                    pygame.mixer.music.load(music_file)
                    pygame.mixer.music.set_volume(0.3)  # Set volume to 30%
                    pygame.mixer.music.play(-1)  # Loop indefinitely
                    print(f"Loaded music: {music_file}")
                    self.music_playing = True
                    music_loaded = True
                    break
                except pygame.error:
                    continue
            
            if not music_loaded:
                print("No music files found. Running without background music.")
                print("To add music, place a file named 'background_music.mp3' in the game directory.")
                
        except Exception as e:
            print(f"Error initializing music: {e}")

    def toggle_music(self):
        """Toggle background music on/off"""
        try:
            if self.music_playing:
                pygame.mixer.music.pause()
                self.music_playing = False
                print("Music paused")
            else:
                pygame.mixer.music.unpause()
                self.music_playing = True
                print("Music resumed")
        except Exception as e:
            print(f"Error toggling music: {e}")

    def init_game(self, num_players, reset_scores=False):
        self.num_players = num_players
        self.players = []

        # Only reset scores if explicitly requested or if number of players changed
        if reset_scores or len(self.player_scores) != num_players:
            self.player_scores = [0] * num_players

        colors = [BLUE, RED, GREEN]
        if num_players == 2:
            positions = [WIDTH // 3, 2 * WIDTH // 3]
        else:
            positions = [WIDTH // 4, WIDTH // 2, 3 * WIDTH // 4]

        for i in range(num_players):
            self.players.append(Player(positions[i], HEIGHT - 150, colors[i]))

        self.terrain = TerrainSystem(num_players)
        self.score = 0
        self.game_over = False
        self.winner = None

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.in_start_screen:
                        result = self.start_screen.handle_input(event)
                        if result:
                            self.init_game(result, reset_scores=True)
                            self.in_start_screen = False
                    elif self.game_over and event.key == pygame.K_r:
                        self.restart(reset_scores=False)
                    elif self.game_over and event.key == pygame.K_ESCAPE:
                        self.in_start_screen = True
                        self.game_over = False
                    elif event.key == pygame.K_m:
                        self.toggle_music()

            if self.in_start_screen:
                self.start_screen.draw()
            else:
                if not self.game_over:
                    self.update()
                else:
                    # Handle round end timer
                    self.round_end_timer += 1
                    if self.round_end_timer >= self.round_end_duration:
                        self.next_round()
                self.draw()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def update(self):
        self.terrain.update(self.score)

        controls_list = [self.controls1, self.controls2, self.controls3][:self.num_players]
        players_dead = []

        for i, player in enumerate(self.players):
            player_dead = player.update(self.terrain, controls_list[i], self.players)
            players_dead.append(player_dead)

        # Check game over conditions
        alive_players = [i for i, player in enumerate(self.players) if not player.is_dead]
        dead_players = [i for i, (player, dead) in enumerate(zip(self.players, players_dead)) if player.is_dead and dead]

        # If only one player alive or all dead, end round
        if len(alive_players) <= 1 and not self.game_over:
            if len(alive_players) == 1:
                self.winner = f"Player {alive_players[0] + 1}"
                self.player_scores[alive_players[0]] += 1
            else:
                self.winner = "Tie"
            self.game_over = True
            self.round_end_timer = 0
        elif dead_players:
            # Award points to surviving players
            for player_idx in dead_players:
                for alive_idx in alive_players:
                    if alive_idx != player_idx:
                        pass  # Could add partial scoring here

        # Increment score if any player is alive
        if alive_players:
            self.score += 1

    def restart(self, reset_scores=False):
        self.init_game(self.num_players, reset_scores=reset_scores)

    def next_round(self):
        # Start next round without resetting scores
        self.init_game(self.num_players, reset_scores=False)

    def draw(self):
        # Enhanced gradient sky background with time-based color shifting
        time_factor = math.sin(pygame.time.get_ticks() * 0.0005) * 0.3 + 0.7

        for y in range(HEIGHT):
            ratio = y / HEIGHT
            # Create more complex gradient
            top_color = (int(MIDNIGHT_BLUE[0] * time_factor), 
                        int(MIDNIGHT_BLUE[1] * time_factor), 
                        int(MIDNIGHT_BLUE[2] * time_factor))
            bottom_color = (int(LIGHT_BLUE[0] * time_factor), 
                           int(LIGHT_BLUE[1] * time_factor), 
                           int(LIGHT_BLUE[2] * time_factor))

            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))

        # Enhanced stars with twinkling effect
        random.seed(42)
        for i in range(80):
            star_x = random.randint(0, WIDTH)
            star_y = random.randint(0, HEIGHT // 2)

            # Twinkling effect
            twinkle = abs(math.sin((pygame.time.get_ticks() + i * 100) * 0.01)) * 0.5 + 0.5
            base_brightness = random.randint(150, 255)
            brightness = int(base_brightness * twinkle)

            size = random.randint(1, 3)
            star_color = (brightness, brightness, brightness)
            pygame.draw.circle(self.screen, star_color, (star_x, star_y), size)

            # Add star glow for larger stars
            if size > 2:
                glow_color = (brightness // 3, brightness // 3, brightness // 3)
                pygame.draw.circle(self.screen, glow_color, (star_x, star_y), size + 2)
        random.seed()

        self.terrain.draw(self.screen)
        for player in self.players:
            player.draw(self.screen)

        # Enhanced UI with backgrounds and better styling
        # Time display with background
        time_bg = pygame.Rect(5, 5, 150, 35)
        pygame.draw.rect(self.screen, UI_BACKGROUND, time_bg)
        pygame.draw.rect(self.screen, SUCCESS_GREEN, time_bg, 2)
        score_text = self.font.render(f"Time: {self.score // 10}", True, UI_TEXT)
        self.screen.blit(score_text, (10, 12))


        # Level display with background
        level_bg = pygame.Rect(5, 45, 120, 35)
        pygame.draw.rect(self.screen, UI_BACKGROUND, level_bg)
        pygame.draw.rect(self.screen, PURPLE, level_bg, 2)
        difficulty_level = min(self.score // 500, 10) + 1
        difficulty_text = self.font.render(f"Level: {difficulty_level}", True, UI_TEXT)
        self.screen.blit(difficulty_text, (10, 52))

        # Player score counters
        colors = [BLUE, RED, GREEN]
        for i in range(self.num_players):
            score_bg = pygame.Rect(5, 85 + i * 40, 130, 35)
            pygame.draw.rect(self.screen, UI_BACKGROUND, score_bg)
            pygame.draw.rect(self.screen, colors[i], score_bg, 2)

            score_text = self.font.render(f"P{i+1}: {self.player_scores[i]}", True, UI_TEXT)
            self.screen.blit(score_text, (10, 92 + i * 40))

        # Music status indicator
        music_bg = pygame.Rect(WIDTH - 160, 80, 150, 25)
        pygame.draw.rect(self.screen, UI_BACKGROUND, music_bg)
        music_color = SUCCESS_GREEN if self.music_playing else WARNING_RED
        pygame.draw.rect(self.screen, music_color, music_bg, 2)
        music_status = "♪ Music: ON" if self.music_playing else "♪ Music: OFF"
        music_text = pygame.font.Font(None, 24).render(music_status, True, UI_TEXT)
        self.screen.blit(music_text, (WIDTH - 155, 85))
        
        # Music controls hint
        music_hint = pygame.font.Font(None, 18).render("Press M to toggle", True, UI_TEXT)
        self.screen.blit(music_hint, (WIDTH - 140, 105))

        # Enhanced controls display - moved to top middle
        small_font = pygame.font.Font(None, 20)
        controls_text = [
            "P1: WASD + Q(tag) E(punch) S(throw)",
            "P2: Arrows + rshift(tag) /(punch) Down Arrow(throw)",
            "P3: YGJ + T(tag) U(punch) H(throw)"
        ]

        # Calculate total width needed for controls
        max_text_width = max(small_font.size(text)[0] for text in controls_text[:self.num_players])
        controls_width = max_text_width + 20  # Add padding
        
        for i in range(self.num_players):
            # Position at top middle
            controls_x = (WIDTH - controls_width) // 2
            controls_y = 85 + i * 25
            
            controls_bg = pygame.Rect(controls_x, controls_y, controls_width, 25)
            pygame.draw.rect(self.screen, UI_BACKGROUND, controls_bg)
            pygame.draw.rect(self.screen, colors[i], controls_bg, 2)

            text = small_font.render(controls_text[i], True, UI_TEXT)
            # Center the text within the background
            text_x = controls_x + (controls_width - text.get_width()) // 2
            self.screen.blit(text, (text_x, controls_y + 3))

        # Enhanced morph timer with better styling
        morph_progress = (self.terrain.morph_interval - self.terrain.morph_timer) / self.terrain.morph_interval
        bar_width = 220
        bar_height = 15
        bar_x = WIDTH - bar_width - 15
        bar_y = 15

        # Timer background and border
        timer_bg = pygame.Rect(bar_x - 5, bar_y - 5, bar_width + 10, bar_height + 10)
        pygame.draw.rect(self.screen, UI_BACKGROUND, timer_bg)
        pygame.draw.rect(self.screen, WARNING_RED, timer_bg, 2)

        # Timer bar background
        pygame.draw.rect(self.screen, BLACK, (bar_x, bar_y, bar_width, bar_height))

        # Timer progress with gradient effect
        progress_width = int(bar_width * morph_progress)
        if morph_progress > 0.7:
            bar_color = SUCCESS_GREEN
        elif morph_progress > 0.3:
            bar_color = YELLOW
        else:
            bar_color = WARNING_RED

        pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, progress_width, bar_height))

        # Timer label
        timer_label = small_font.render("Next Shift", True, UI_TEXT)
        self.screen.blit(timer_label, (bar_x, bar_y - 20))

        # Score counter display below terrain timer
        score_bg = pygame.Rect(WIDTH - 160, 40, 150, 35)
        pygame.draw.rect(self.screen, UI_BACKGROUND, score_bg)
        pygame.draw.rect(self.screen, ORANGE, score_bg, 2)
        score_counter_text = self.font.render(f"Score: {self.score}", True, UI_TEXT)
        self.screen.blit(score_counter_text, (WIDTH - 155, 47))

        # Enhanced terrain shift warning
        if self.terrain.morph_timer > self.terrain.morph_interval - 60:
            # Flashing warning with background
            flash = (pygame.time.get_ticks() // 200) % 2
            if flash:
                warning_bg = pygame.Rect(WIDTH // 2 - 100, 40, 200, 40)
                pygame.draw.rect(self.screen, WARNING_RED, warning_bg)
                pygame.draw.rect(self.screen, WHITE, warning_bg, 3)

                warning_font = pygame.font.Font(None, 32)
                warning_text = warning_font.render("TERRAIN SHIFT!", True, WHITE)
                text_rect = warning_text.get_rect(center=(WIDTH // 2, 60))
                self.screen.blit(warning_text, text_rect)

        # Enhanced game over screen
        if self.game_over:
            # Semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))

            # Game over box
            game_over_box = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 150, 400, 300)
            pygame.draw.rect(self.screen, UI_BACKGROUND, game_over_box)
            pygame.draw.rect(self.screen, WARNING_RED, game_over_box, 4)

            # Game over text with glow
            large_font = pygame.font.Font(None, 48)
            medium_font = pygame.font.Font(None, 36)
            small_font = pygame.font.Font(None, 24)

            game_over_text = large_font.render("GAME OVER", True, WARNING_RED)
            game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

            # Add glow effect
            for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
                glow_text = large_font.render("GAME OVER", True, (100, 0, 0))
                self.screen.blit(glow_text, (game_over_rect.x + offset[0], game_over_rect.y + offset[1]))

            self.screen.blit(game_over_text, game_over_rect)

            if self.winner:
                winner_color = SUCCESS_GREEN if self.winner != "Tie" else YELLOW
                if self.winner == "Tie":
                    winner_text = medium_font.render("It's a Tie!", True, winner_color)
                else:
                    winner_text = medium_font.render(f"{self.winner} Wins!", True, winner_color)

                winner_rect = winner_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
                self.screen.blit(winner_text, winner_rect)

            final_score_text = medium_font.render(f"Final Time: {self.score // 10}", True, UI_TEXT)
            score_rect = final_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(final_score_text, score_rect)

            # Display player scores
            for i in range(self.num_players):
                score_text = medium_font.render(f"Player {i+1}: {self.player_scores[i]} wins", True, colors[i])
                score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30 + i * 25))
                self.screen.blit(score_text, score_rect)

            # Show countdown and instructions
            seconds_left = (self.round_end_duration - self.round_end_timer) // 60 + 1
            countdown_text = medium_font.render(f"Next round in {seconds_left} seconds...", True, YELLOW)
            countdown_rect = countdown_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60 + self.num_players * 15))
            self.screen.blit(countdown_text, countdown_rect)

            restart_text = small_font.render("Press R for Next Round or ESC for Menu", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90 + self.num_players * 15))
            self.screen.blit(restart_text, restart_rect)

if __name__ == "__main__":
    game = Game()
    game.run()

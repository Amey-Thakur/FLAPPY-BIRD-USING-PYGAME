# ============================================================================
# FLAPPY BIRD GAME
# ============================================================================
# A high-fidelity reconstruction of the mobile arcade classic.
# Features real-time physics, sprite animation, and high score persistence.
#
# Authors:          Amey Thakur & Mega Satish
# Date:             June 30, 2021
# License:          MIT License
# Repository:       https://github.com/Amey-Thakur/FLAPPY-BIRD-USING-PYGAME
# Profiles:
#   - Amey Thakur:  https://github.com/Amey-Thakur
#   - Mega Satish:  https://github.com/msatmod
# ============================================================================
# title: AMEY & MEGA
# icon: favicon.png

import asyncio  # Asynchronous I/O for WebAssembly compatibility
import pygame
import sys
import random

# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================
SCREEN_WIDTH    = 576
SCREEN_HEIGHT   = 1024
FPS             = 120
GRAVITY         = 0.25      # Downward acceleration applied per frame
FLAP_STRENGTH   = 8         # Upward velocity impulse on flap
PIPE_SPAWN_TIME = 1200      # Milliseconds between pipe generation
PIPE_GAP        = 300       # Vertical space between top and bottom pipes

# ============================================================================
# CORE LOGIC
# ============================================================================

def draw_floor():
    """
    Renders the infinite scrolling floor effect.
    
    Logic:
        Two identical floor surfaces are drawn side-by-side. As they move left,
        if the first one leaves the screen, it resets to the right, creating
        a seamless loop.
    """
    screen.blit(floor_surface, (floor_x_position, 900))
    screen.blit(floor_surface, (floor_x_position + 576, 900))

    # Render static text on top of the floor
    # Content and Colors
    # Text structure: [ ("Text", (R, G, B)) ]
    text_parts = [
        ("Developed by ", (255, 255, 255)),           # White
        ("Amey Thakur ", (85, 172, 238)),             # Sky Blue
        ("& ", (255, 255, 255)),                      # White
        ("Mega Satish", (85, 172, 238))               # Sky Blue
    ]

    # Calculate Total Width for Centering
    total_width = 0
    surfaces = []
    for text, color in text_parts:
        surface = footer_font.render(text, True, color)
        shadow = footer_font.render(text, True, (0, 0, 0)) # Black shadow
        width = surface.get_width()
        total_width += width
        surfaces.append( (surface, shadow, width) )

    # Starting X Position (Centered)
    current_x = (SCREEN_WIDTH - total_width) // 2
    text_y = 962
    
    # Render Loop
    for surface, shadow, width in surfaces:
        surface_rect = surface.get_rect(midleft=(current_x, text_y))
        shadow_rect = shadow.get_rect(midleft=(current_x + 2, text_y + 2)) # Offset shadow
        
        screen.blit(shadow, shadow_rect) # Draw shadow first
        screen.blit(surface, surface_rect) # Draw text on top
        
        current_x += width


def create_pipe():
    """
    Generates a new pipe obstacle pair (Top and Bottom).
    
    Returns:
        tuple: (bottom_pipe_rect, top_pipe_rect)
        
    Logic:
        Selects a random height from predefined positions.
        Calculates the position of the bottom pipe primarily, then
        derives the top pipe's position by subtracting the PIPE_GAP.
    """
    random_pipe_position = random.choice(pipe_height)
    
    # Bottom Pipe: Anchored at midtop position
    bottom_pipe = pipe_surface.get_rect(midtop=(700, random_pipe_position))
    
    # Top Pipe: Anchored relative to bottom pipe with fixed gap
    top_pipe = pipe_surface.get_rect(midbottom=(700, random_pipe_position - PIPE_GAP))
    
    return bottom_pipe, top_pipe


def move_pipes(pipes):
    """
    Updates the horizontal position of all active pipes.
    
    Parameters:
        pipes (list): List of pygame.Rect objects representing pipes.
        
    Returns:
        list: Updated list of moved pipes.
    """
    for pipe in pipes:
        pipe.centerx -= 5   # Move pipe leftward by 5 pixels per frame
    return pipes


def draw_pipes(pipes):
    """
    Renders the pipe sprites onto the screen.
    
    Logic:
        Iterates through the pipe list. If the pipe is a 'top' pipe
        (determined by its bottom Y coordinate being visible), checking
        logic is simplified here by context or we flip based on position.
        In this implementation, logic infers orientation:
        - If pipe bottom is >= 1024 (off screen low? No, Logic checks position).
        
        Correction:
        The logic checks if `pipe.bottom >= 1024`. This condition seems specific
        to how `create_pipe` sets rectangles. Ideally, distinction should be explicit.
        Here, we check geometry to decide whether to flip the sprite vertically.
    """
    for pipe in pipes:
        if pipe.bottom >= 1024:
            # Bottom pipe (Standard orientation)
            screen.blit(pipe_surface, pipe)
        else:
            # Top pipe (Flipped vertically)
            flip_pipe = pygame.transform.flip(pipe_surface, False, True)
            screen.blit(flip_pipe, pipe)


def check_collision(pipes):
    """
    Performs Axis-Aligned Bounding Box (AABB) collision detection.
    
    Parameters:
        pipes (list): List of obstacle rectangles.
        
    Returns:
        bool: False if collision detected (Game Over), True otherwise.
        
    Side Effects:
        Plays `death_sound` upon collision detection.
    """
    global game_active
    
    # 1. Pipe Collision
    for pipe in pipes:
        if bird_rectangle.colliderect(pipe):
            if game_active:
                death_sound.play()
            return False

    # 2. Environmental Collision (Floor/Ceiling)
    # Thresholds: -100 (Ceiling buffer), 900 (Floor Y-coordinate)
    if bird_rectangle.top <= -100 or bird_rectangle.bottom >= 900:
        if game_active:
             death_sound.play()
        return False

    return True


def rotate_bird(bird):
    """
    Applies affine transformation (rotation) to the bird sprite.
    
    Logic:
        Rotation angle is proportional to vertical velocity (`bird_movement`).
        - Upward movement (negative velocity) -> Rotate Up (CCW).
        - Downward movement (positive velocity) -> Rotate Down (CW).
        Multiplier (3) exaggerates the visual effect.
        
    Returns:
        pygame.Surface: The rotated image surface.
    """
    new_bird = pygame.transform.rotozoom(bird, -bird_movement * 3, 1)
    return new_bird


def bird_animation():
    """
    Updates the bird's sprite frame to simulate wing flapping.
    
    Returns:
        tuple: (new_bird_surface, new_bird_rect)
    """
    new_bird = bird_frames[bird_index]
    new_bird_rectangle = new_bird.get_rect(center=(100, bird_rectangle.centery))
    return new_bird, new_bird_rectangle


def score_display(game_state):
    """
    Renders textual score information based on game state.
    
    Parameters:
        game_state (str): 'main_game' or 'game_over'.
    """
    if game_state == 'main_game':
        # Live Score
        score_surface = game_font.render(str(int(score)), True, (255, 255, 255))
        score_rectangle = score_surface.get_rect(center=(288, 100))
        screen.blit(score_surface, score_rectangle)

    if game_state == 'game_over':
        # Score Summary
        score_surface = game_font.render(f'Score: {int(score)}', True, (255, 255, 255))
        score_rectangle = score_surface.get_rect(center=(288, 100))
        screen.blit(score_surface, score_rectangle)

        # High Score
        high_score_surface = game_font.render(f'High Score: {int(high_score)}', True, (255, 255, 255))
        high_score_rectangle = high_score_surface.get_rect(center=(288, 185))
        screen.blit(high_score_surface, high_score_rectangle)


def update_score(current_score, current_high_score):
    """Updates the high score persistence variable."""
    if current_score > current_high_score:
        return current_score
    return current_high_score


# ============================================================================
# INITIALIZATION
# ============================================================================

# Audio Mixer: Pre-init required to avoid audio lag
pygame.mixer.pre_init(frequency=44100, size=16, channels=1, buffer=512)
pygame.init()

# Display Setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("AMEY & MEGA")

# Icon Setup
try:
    icon_surface = pygame.image.load('favicon.png')
    pygame.display.set_icon(icon_surface)
except Exception as e:
    print(f"Warning: Could not load icon ({e})")

clock = pygame.time.Clock()

# Typography
try:
    try:
        # Try finding the font with uppercase extension (Primary check)
        game_font = pygame.font.Font('04B_19.TTF', 40)
        footer_font = pygame.font.Font('04B_19.TTF', 20)
    except:
        # Fallback to lowercase extension (Secondary check)
        game_font = pygame.font.Font('04B_19.ttf', 40)
        footer_font = pygame.font.Font('04B_19.ttf', 20)
except:
    print("Warning: Custom font not found. Using system font.")
    game_font = pygame.font.SysFont('Arial', 40, bold=True)
    footer_font = pygame.font.SysFont('Arial', 20, bold=True)
bird_movement       = 0
game_active         = True
score               = 0
high_score          = 0
floor_x_position    = 0
pipe_list           = []
pipe_height         = [400, 600, 800]
score_sound_countdown = 100

# ============================================================================
# ASSET MANAGEMENT
# ============================================================================

try:
    # Textures
    background_surface = pygame.image.load('assets/background-day.png').convert()
    background_surface = pygame.transform.scale2x(background_surface)

    floor_surface = pygame.image.load('assets/base.png').convert()
    floor_surface = pygame.transform.scale2x(floor_surface)

    # Bird Animation Frames
    bird_downflap = pygame.transform.scale2x(pygame.image.load('assets/bluebird-midflap.png').convert_alpha())
    bird_midflap  = pygame.transform.scale2x(pygame.image.load('assets/bluebird-midflap.png').convert_alpha())
    bird_upflap   = pygame.transform.scale2x(pygame.image.load('assets/bluebird-midflap.png').convert_alpha())
    bird_frames   = [bird_downflap, bird_midflap, bird_upflap]
    bird_index    = 0
    bird_surface  = bird_frames[bird_index]
    bird_rectangle= bird_surface.get_rect(center=(100, 512))

    # Obstacles & UI
    pipe_surface    = pygame.image.load('assets/pipe-green.png')
    pipe_surface    = pygame.transform.scale2x(pipe_surface)
    
    game_over_surface   = pygame.transform.scale2x(pygame.image.load('assets/message.png').convert_alpha())
    game_over_rectangle = game_over_surface.get_rect(center=(288, 512))

    # Sound Effects
    flap_sound  = pygame.mixer.Sound('sound/sfx_wing.wav')
    death_sound = pygame.mixer.Sound('sound/sfx_hit.wav')
    score_sound = pygame.mixer.Sound('sound/sfx_point.wav')

except Exception as e:
    print(f"CRITICAL ERROR: Asset loading failed ({e}). Playing in fallback mode.")
    # Fallback Assets (Mock generation)
    background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background_surface.fill((30, 30, 30))
    floor_surface = pygame.Surface((SCREEN_WIDTH, 100))
    floor_surface.fill((200, 200, 200))
    bird_surface = pygame.Surface((34, 24))
    bird_surface.fill((255, 255, 0))
    bird_rectangle = bird_surface.get_rect(center=(100, 512))
    bird_frames = [bird_surface]
    pipe_surface = pygame.Surface((52, 320))
    pipe_surface.fill((0, 255, 0))
    game_over_surface = pygame.Surface((200, 50))
    game_over_rectangle = game_over_surface.get_rect(center=(288, 512))
    
    # Sound Mock
    class MockSound:
        def play(self): pass
    flap_sound = MockSound()
    death_sound = MockSound()
    score_sound = MockSound()


# ============================================================================
# EVENT TIMERS
# ============================================================================
SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, PIPE_SPAWN_TIME)

BIRDFLAP = pygame.USEREVENT + 1
pygame.time.set_timer(BIRDFLAP, 200)


# ============================================================================
# MAIN LOOP (ASYNC)
# ============================================================================
async def main():
    """
    The main game loop, utilizing asyncio for browser compatibility.
    Handles events, updates game state, and renders the frame.
    """
    global bird_movement, game_active, score, high_score, bird_index, bird_surface, bird_rectangle, pipe_list, floor_x_position, score_sound_countdown

    while True:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Flap Mechanic
                if event.key == pygame.K_SPACE and game_active:
                    bird_movement = 0
                    bird_movement -= FLAP_STRENGTH
                    flap_sound.play()

                # Restart Mechanic
                if event.key == pygame.K_SPACE and not game_active:
                    game_active         = True
                    pipe_list.clear() # Reset obstacles
                    bird_rectangle.center = (100, 512)
                    bird_movement       = 0
                    score               = 0
                    score_sound_countdown = 100

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Flap Mechanic (Mouse)
                if game_active:
                    bird_movement = 0
                    bird_movement -= FLAP_STRENGTH
                    flap_sound.play()
                
                # Restart Mechanic (Mouse)
                else:
                    game_active         = True
                    pipe_list.clear() # Reset obstacles
                    bird_rectangle.center = (100, 512)
                    bird_movement       = 0
                    score               = 0
                    score_sound_countdown = 100

            if event.type == SPAWNPIPE:
                pipe_list.extend(create_pipe())

            if event.type == BIRDFLAP:
                if bird_index < 2:
                    bird_index += 1
                else:
                    bird_index = 0
                bird_surface, bird_rectangle = bird_animation()

        # Render Background
        screen.blit(background_surface, (0, 0))

        if game_active:
            # --- Active Gameplay State ---
            
            # 1. Physics: Apply Gravity
            bird_movement += GRAVITY
            
            # 2. Physics: Rotation
            rotated_bird = rotate_bird(bird_surface)
            bird_rectangle.centery += bird_movement
            screen.blit(rotated_bird, bird_rectangle)
            
            # 3. Collision Detection
            game_active = check_collision(pipe_list)

            # 4. Obstacle Update
            pipe_list = move_pipes(pipe_list)
            draw_pipes(pipe_list)

            # 5. Scoring System
            score += 0.01  # Incremental score for survival
            score_display('main_game')
            
            # 6. Audio Feedback (Score)
            score_sound_countdown -= 1
            if score_sound_countdown <= 0:
                score_sound.play()
                score_sound_countdown = 100
        else:
            # --- Game Over State ---
            screen.blit(game_over_surface, game_over_rectangle)
            high_score = update_score(score, high_score)
            score_display('game_over')

        # Floor Animation (Independent of game state for visual polish)
        floor_x_position -= 1
        draw_floor()
        if floor_x_position <= -576:
            floor_x_position = 0

        # Frame Update
        pygame.display.update()
        clock.tick(FPS)
        await asyncio.sleep(0)  # Critical yield for WebAssembly environment

if __name__ == "__main__":
    asyncio.run(main())

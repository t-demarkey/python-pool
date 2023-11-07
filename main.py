import pygame
import pymunk
import pymunk.pygame_util
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 678
BOTTOM_PANEL = 50

# Create the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT + BOTTOM_PANEL))
pygame.display.set_caption("Pocket Billiards")

# Create a Pymunk space
space = pymunk.Space()
static_body = space.static_body
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Initialize the clock
clock = pygame.time.Clock()
FPS = 120

# Game variables
lives = 3
ball_radius = 36
pocket_radius = 66
shot_force = 0
max_shot_force = 10000
shot_direction = 1
game_active = True
cue_ball_potted = False
taking_shot = True
powering_up = False
potted_balls = []

# Define colors
BG_COLOR = (50, 50, 50)
BALL_COLOR = (255, 0, 0)
WHITE_COLOR = (255, 255, 255)

# Define fonts
font = pygame.font.SysFont("Arial", 30)
large_font = pygame.font.SysFont("Arial", 60)

# Load images
table_image = pygame.image.load("assets/images/table.png").convert_alpha()
ball_images = []
for i in range(1, 17):
    ball_image = pygame.image.load(f"assets/images/ball_{i}.png").convert_alpha()
    ball_images.append(ball_image)

# Store the mouse dragging state
dragging_cue = False

# Function for rendering text on the screen
def render_text(text, font, text_color, x, y):
    text_image = font.render(text, True, text_color)
    screen.blit(text_image, (x, y))

# Create balls
def create_ball(radius, position):
    body = pymunk.Body()
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.mass = 5
    shape.elasticity = 0.8

    pivot_joint = pymunk.PivotJoint(static_body, body, (0, 0), (0, 0))
    pivot_joint.max_bias = 0
    pivot_joint.max_force = 1000

    space.add(body, shape, pivot_joint)
    return shape

# Set up game balls
balls = []
rows = 5

for col in range(5):
    for row in range(rows):
        position = (250 + (col * (ball_radius + 1)), 267 + (row * (ball_radius + 1)) + (col * ball_radius / 2))
        new_ball = create_ball(ball_radius / 2, position)
        balls.append(new_ball)
    rows -= 1

cue_ball_position = (888, SCREEN_HEIGHT / 2)
cue_ball = create_ball(ball_radius / 2, cue_ball_position)
balls.append(cue_ball)

# Create pockets
pockets = [
    (55, 63),
    (592, 48),
    (1134, 64),
    (55, 616),
    (592, 629),
    (1134, 616)
]

# Create pool table cushions
cushions = [
    [(88, 56), (109, 77), (555, 77), (564, 56)],
    [(621, 56), (630, 77), (1081, 77), (1102, 56)],
    [(89, 621), (110, 600), (556, 600), (564, 621)],
    [(622, 621), (630, 600), (1081, 600), (1102, 621)],
    [(56, 96), (77, 117), (77, 560), (56, 581)],
    [(1143, 96), (1122, 117), (1122, 560), (1143, 581)]
]

# Create cushions
def create_cushion(poly_dims):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = ((0, 0))
    shape = pymunk.Poly(body, poly_dims)
    shape.elasticity = 0.8

    space.add(body, shape)

for c in cushions:
    create_cushion(c)

# Create power bars
power_bar = pygame.Surface((10, 20))
power_bar.fill(BALL_COLOR)

# Game loop
game_running = True
while game_running:
    clock.tick(FPS)
    space.step(1 / FPS)

    screen.fill(BG_COLOR)

    screen.blit(table_image, (0, 0))

    for i, ball in enumerate(balls):
        for pocket in pockets:
            ball_x_dist = abs(ball.body.position[0] - pocket[0])
            ball_y_dist = abs(ball.body.position[1] - pocket[1])
            ball_dist = math.sqrt((ball_x_dist ** 2) + (ball_y_dist ** 2))
            if ball_dist <= pocket_radius / 2:
                if i == len(balls) - 1:
                    lives -= 1
                    cue_ball_potted = True
                    ball.body.position = (-100, -100)
                    ball.body.velocity = (0.0, 0.0)
                else:
                    space.remove(ball.body)
                    balls.remove(ball)
                    potted_balls.append(ball_images[i])
                    ball_images.pop(i)

    for i, ball in enumerate(balls):
        screen.blit(ball_images[i], (ball.body.position[0] - ball.radius, ball.body.position[1] - ball.radius))

    taking_shot = True
    for ball in balls:
        if int(ball.body.velocity[0]) != 0 or int(ball.body.velocity[1]) != 0:
            taking_shot = False

    if taking_shot and game_active:
        if cue_ball_potted:
            balls[-1].body.position = (888, SCREEN_HEIGHT / 2)
            cue_ball_potted = False

        if not dragging_cue:
            mouse_pos = pygame.mouse.get_pos()
            cue_start = balls[-1].body.position
            cue_drag_vector = (cue_start[0] - mouse_pos[0], cue_start[1] - mouse_pos[1])
            cue_drag_length = math.sqrt(cue_drag_vector[0] ** 2 + cue_drag_vector[1] ** 2)

            if cue_drag_length > 0:
                x_dist = cue_start[0] - mouse_pos[0]
                y_dist = -(cue_start[1] - mouse_pos[1])
                cue_angle = math.degrees(math.atan2(y_dist, x_dist))

    if powering_up and game_active:
        shot_force += 100 * shot_direction
        if shot_force >= max_shot_force or shot_force <= 0:
            shot_direction *= -1

        for b in range(math.ceil(shot_force / 2000)):
            screen.blit(power_bar,
                        (balls[-1].body.position[0] - 30 + (b * 15),
                         balls[-1].body.position[1] + 30))
    elif not powering_up and taking_shot:
        x_impulse = math.cos(math.radians(cue_angle))
        y_impulse = math.sin(math.radians(cue_angle))
        balls[-1].body.apply_impulse_at_local_point((shot_force * -x_impulse, shot_force * y_impulse), (0, 0))
        shot_force = 0
        shot_direction = 1

    pygame.draw.rect(screen, BG_COLOR, (0, SCREEN_HEIGHT, SCREEN_WIDTH, BOTTOM_PANEL))
    render_text("LIVES: " + str(lives), font, WHITE_COLOR, SCREEN_WIDTH - 200, SCREEN_HEIGHT + 10)

    for i, ball in enumerate(potted_balls):
        screen.blit(ball, (10 + (i * 50), SCREEN_HEIGHT + 10))

    if lives <= 0:
        render_text("GAME OVER", large_font, WHITE_COLOR, SCREEN_WIDTH / 2 - 160, SCREEN_HEIGHT / 2 - 100)
        game_active = False

    if len(balls) == 1:
        render_text("YOU WIN!", large_font, WHITE_COLOR, SCREEN_WIDTH / 2 - 160, SCREEN_HEIGHT / 2 - 100)
        game_active = False

    pygame.display.update()

pygame.quit()

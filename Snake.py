import pygame, random, sys, math, os, time
pygame.init()

#Setting
CELL = 32  # large cells
GRID_W, GRID_H = 28, 20  # Increased grid size
W, H = GRID_W * CELL, GRID_H * CELL
SCREEN = pygame.display.set_mode((W, H))
pygame.display.set_caption("ABS Snake Duo")
CLOCK = pygame.time.Clock()

FONT = pygame.font.SysFont(None, 28)  # big font
BIG = pygame.font.SysFont(None, 60)

# speeds & dash
NORMAL_SPEED = 6
DASH_SPEED = 12
DASH_MAX = 100
DRAIN_PER_SEC = 70
RECOVER_PER_SEC = 45

# gradient + glass
def make_background():
    # gradient glass background surface
    surf = pygame.Surface((W, H))
    # Gradient colors
    for y in range(H):
        r = int(25 + (y / H) * 70)
        g = int(60 + (y / H) * 90)
        b = int(100 + (y / H) * 120)
        pygame.draw.line(surf, (r, g, b), (0, y), (W, y))
    # Glass overlay
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((255,255,255,28))
    surf.blit(overlay, (0,0))
    return surf

BACKGROUND = make_background()

# utils
def rand_color():
    # Snake body colour
    return (random.randint(80,255), random.randint(80,255), random.randint(80,255))

def text(s, f=FONT, col=(255,255,255)):
    # text render
    return f.render(s, True, col)

# particles
class Particle:
    # creating particles
    def __init__(self, pos, color):
        self.x, self.y = pos
        ang = random.uniform(0, math.pi*2)
        sp = random.uniform(60, 160)
        self.vx = math.cos(ang) * sp
        self.vy = math.sin(ang) * sp
        self.life = random.uniform(0.4, 0.9)
        self.age = 0.0
        self.color = color
        self.size = random.randint(3,6)
    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 120 * dt # Gravity effect
    def draw(self, surf):
        alpha = max(0, 255 * (1 - self.age / self.life))
        if alpha <= 0: return
        # smooth fading
        col = (*self.color[:3], int(alpha))
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, col, (self.size, self.size), self.size)
        surf.blit(s, (self.x - self.size, self.y - self.size))
    def alive(self): return self.age < self.life

    # game state
def reset_game():
    # initilization 1. snake 2. positions 3. directions 4. colors
    # Player 1 setup (Left side, moving Right, White Head)
    sx = GRID_W // 3
    sy = GRID_H // 2
    snake1 = [(sx, sy), (sx-1, sy), (sx-2, sy)]
    colors1 = {snake1[0]:(255,255,255)}
    for seg in snake1[1:]:
        colors1[seg] = rand_color()
    dir1 = (1,0)

    # Player 2 setup (Right side, moving Left, Yellow/Gold Head)
    sx2 = GRID_W * 2 // 3
    sy2 = GRID_H // 2
    snake2 = [(sx2, sy2), (sx2+1, sy2), (sx2+2, sy2)]
    colors2 = {snake2[0]:(240,240,50)} # P2 Head color
    for seg in snake2[1:]:
        colors2[seg] = rand_color()
    dir2 = (-1,0)

    return snake1, colors1, dir1, snake2, colors2, dir2

    # Initialize state
snake1, colors1, dir1, snake2, colors2, dir2 = reset_game()

    # Food
foods = []
def spawn_foods():
    #place food on empty grid spots
    global foods
    foods = []  # Clear existing foods

    # Get all available spots
    spots = [(x,y) for x in range(GRID_W) for y in range(GRID_H)
             if (x,y) not in snake1 and (x,y) not in snake2]

    if spots:
        # Spawn between 3 and 6 foods, but not more than available spots
        num_foods = random.randint(3, 6)
        num_foods = min(num_foods, len(spots))  # Don't exceed available spots

        # Randomly choose food positions
        foods = random.sample(spots, num_foods)
    else:
        foods = []  # No space left

spawn_foods()

# Dash (P1 and P2)
dash_energy1 = DASH_MAX
dash_energy2 = DASH_MAX

# Scores and particles
score1 = 0  # Player 1 Score
score2 = 0  # Player 2 Score
particles = []

# Menu and screens
STATE = "menu"  # "menu", "playing", "gameover"
menu_selected = 0
menu_items = ["Play (1v1)", "Quit"]
winner_text = ""

# drawing helpers
def draw_head_triangle(surf, center, direction_vec, color):
    # triangle snake head
    cx, cy = center
    dx, dy = direction_vec
    size = CELL * 0.9
    h = size
    w = size * 0.6
    # calculate angle from direction vector
    ang = math.atan2(dy, dx)
    # Base points for a triangle pointing right (0 angle)
    pts = [ (w/2, 0), (-w/2, -h/2), (-w/2, h/2) ]
    # Rotate points
    rot = []
    for px, py in pts:
        rx = px * math.cos(ang) - py * math.sin(ang)
        ry = px * math.sin(ang) + py * math.cos(ang)
        rot.append((cx + rx, cy + ry))
    pygame.draw.polygon(surf, color, rot)
    # Draw eye/detail
    ex = cx + math.cos(ang) * (w*0.15)
    ey = cy + math.sin(ang) * (w*0.15)
    pygame.draw.circle(surf, (40,40,40), (int(ex), int(ey)), max(2, CELL//8))

def draw_dash_bar(surf, x, y, w=180, h=14, val=1.0, name="Dash", color=(20,180,240)):
    # dash bar
    # Draw background
    pygame.draw.rect(surf, (40,40,40), (x, y, w, h), border_radius=8)

    # Draw fill
    fill_width = int(val * (w-4))
    if fill_width > 0:
        pygame.draw.rect(surf, color, (x+2, y+2, fill_width, h-4), border_radius=8)

    # Draw label
    label = text(name, FONT, color)
    surf.blit(label, (x - label.get_width() - 10, y - 1))

def draw_scoreboard(surf):
    # score
    # P1: White color (Top Left)
    p1_text = text(f"P1: {score1}", FONT, (255,255,255))
    surf.blit(p1_text, (10,10))

    # P2: Yellow (Top Right)
    p2_text = text(f"P2: {score2}", FONT, (240,240,50))
    surf.blit(p2_text, (W - p2_text.get_width() - 10, 10))

    # Menu & Gameover render
def render_menu(surface, sel):
    # main menu
    wcard = W * 0.5
    hcard = H * 0.5
    x = (W - wcard)/2
    y = (H - hcard)/2
    pygame.draw.rect(surface, (10,10,20,220), (x,y,wcard,hcard), border_radius=12)
    title = BIG.render("2-Player Snake", True, (255,255,255))
    surface.blit(title, (x+30, y+20))
    for i, item in enumerate(menu_items):
        yy = y + 110 + i*56
        col = (240,240,240) if i==sel else (180,180,190)
        brect = pygame.Rect(x+30, yy-8, wcard-60, 44)
        if i==sel:
            pygame.draw.rect(surface, (40,120,200), brect, border_radius=10)
        surface.blit(text(item, FONT, col), (x+50, yy))

def render_gameover(surface, txt):
    # Game over overlay
    overlay = pygame.Surface((W,H), pygame.SRCALPHA)
    overlay.fill((0,0,0,160))
    surface.blit(overlay, (0,0))
    g = BIG.render(txt, True, (255,200,200))
    instr = FONT.render("Press R to restart or Esc for menu", True, (220,220,220))
    surface.blit(instr, (W//2 - instr.get_width()//2, H//2 + 10))
    surface.blit(g, (W//2 - g.get_width()//2, H//2 - 50))

# Main loop
last_t = time.time()
acc = 0.0
while True:
    t = time.time()
    dt = t - last_t
    last_t = t

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type == pygame.KEYDOWN:
            if STATE == "menu":
                if ev.key == pygame.K_UP:
                    menu_selected = (menu_selected - 1) % len(menu_items)
                if ev.key == pygame.K_DOWN:
                    menu_selected = (menu_selected + 1) % len(menu_items)
                if ev.key == pygame.K_RETURN:
                    if menu_items[menu_selected] == "Play (1v1)":
                        snake1, colors1, dir1, snake2, colors2, dir2 = reset_game()
                        spawn_foods()
                        dash_energy1 = DASH_MAX
                        dash_energy2 = DASH_MAX
                        score1 = 0
                        score2 = 0
                        particles.clear()
                        STATE = "playing"
                    elif menu_items[menu_selected] == "Quit":
                        pygame.quit(); sys.exit()

            # General In-Game Controls (Playing or Game Over)
            elif ev.key == pygame.K_ESCAPE:
                STATE = "menu"

            if ev.key == pygame.K_r:
                # Reset game state and scores
                snake1, colors1, dir1, snake2, colors2, dir2 = reset_game()
                spawn_foods()
                dash_energy1 = DASH_MAX
                dash_energy2 = DASH_MAX
                score1 = 0
                score2 = 0
                particles.clear()
                STATE = "playing" # Set state back to playing

    keys = pygame.key.get_pressed()

    # Menu state handling (skip game logic)
    if STATE == "menu":
        SCREEN.blit(BACKGROUND, (0,0))
        render_menu(SCREEN, menu_selected)
        pygame.display.update()
        CLOCK.tick(60)
        continue

    # Game Logic Only Runs in "playing" State
    if STATE == "playing":
        # Controls: P1 WASD
        if keys[pygame.K_w] and dir1 != (0,1): dir1 = (0,-1)
        if keys[pygame.K_s] and dir1 != (0,-1): dir1 = (0,1)
        if keys[pygame.K_a] and dir1 != (1,0): dir1 = (-1,0)
        if keys[pygame.K_d] and dir1 != (-1,0): dir1 = (1,0)

        # Controls: P2 arrows
        if keys[pygame.K_UP] and dir2 != (0,1): dir2 = (0,-1)
        if keys[pygame.K_DOWN] and dir2 != (0,-1): dir2 = (0,1)
        if keys[pygame.K_LEFT] and dir2 != (1,0): dir2 = (-1,0)
        if keys[pygame.K_RIGHT] and dir2 != (-1,0): dir2 = (1,0)

        # Dash handling for P1 (Space)
        dashing1 = keys[pygame.K_SPACE] and dash_energy1 > 0
        dash_energy1 += ((-DRAIN_PER_SEC) if dashing1 else RECOVER_PER_SEC) * dt
        dash_energy1 = max(0, min(DASH_MAX, dash_energy1))
        speed1 = DASH_SPEED if dashing1 else NORMAL_SPEED

        # Dash handling for P2 (Right Shift)
        dashing2 = keys[pygame.K_RSHIFT] and dash_energy2 > 0
        dash_energy2 += ((-DRAIN_PER_SEC) if dashing2 else RECOVER_PER_SEC) * dt
        dash_energy2 = max(0, min(DASH_MAX, dash_energy2))
        speed2 = DASH_SPEED if dashing2 else NORMAL_SPEED

        # Step timing synchronized by the fastest player
        speed = max(speed1, speed2)
        step_time = 1.0 / speed

        acc += dt
        loser = None

        while acc >= step_time:
            acc -= step_time

            # compute next heads
            h1 = snake1[0]
            h2 = snake2[0]
            nx1, ny1 = h1[0] + dir1[0], h1[1] + dir1[1]
            nx2, ny2 = h2[0] + dir2[0], h2[1] + dir2[1]

            # check wall collisions
            hit1_wall = (nx1 < 0 or nx1 >= GRID_W or ny1 < 0 or ny1 >= GRID_H)
            hit2_wall = (nx2 < 0 or nx2 >= GRID_W or ny2 < 0 or ny2 >= GRID_H)

            new1 = (nx1, ny1)
            new2 = (nx2, ny2)

            # Check fatal collisions
            p1_dead = hit1_wall
            p2_dead = hit2_wall

            # Head-on collision or Head-Swap
            if new1 == new2 or (new1 == h2 and new2 == h1):
                p1_dead = p2_dead = True

            # Body collisions (P1 vs P1/P2)
            if not p1_dead:
                # Check collision with own body (excluding current head cell)
                if new1 in snake1[1:] or new1 in snake2:
                    p1_dead = True

            # Body collisions (P2 vs P2/P1)
            if not p2_dead:
                # Check collision with own body (excluding current head cell)
                if new2 in snake2[1:] or new2 in snake1:
                    p2_dead = True

            # Determine loser
            if p1_dead and p2_dead:
                loser = "tie"
                break
            elif p1_dead:
                loser = "P1"
                break
            elif p2_dead:
                loser = "P2"
                break

            # If no death, commit movement
            snake1.insert(0, new1)
            snake2.insert(0, new2)

            colors1[new1] = (255,255,255) # P1 Head color
            colors2[new2] = (240,240,50)  # P2 Head color

            # Check if any food was eaten
            ate1 = False
            ate2 = False
            eaten_foods = []

            for food in foods:
                if new1 == food:
                    ate1 = True
                    eaten_foods.append(food)
                    score1 += 1
                elif new2 == food:
                    ate2 = True
                    eaten_foods.append(food)
                    score2 += 1

            # Remove eaten foods and create particles
            for food in eaten_foods:
                foods.remove(food)
                px = (food[0] + 0.5) * CELL
                py = (food[1] + 0.5) * CELL
                for _ in range(18):
                    particles.append(Particle((px,py), rand_color()))

            # Spawn new foods if we're below minimum
            if len(foods) < 3:
                spawn_foods()

            # Set the segment behind the head to a random color (new body segment)
            if ate1: colors1[new1] = rand_color()
            if ate2: colors2[new2] = rand_color()

            # If not eating, remove tail segments
            if not ate1:
                tail1 = snake1.pop()
                colors1.pop(tail1, None)
            if not ate2:
                tail2 = snake2.pop()
                colors2.pop(tail2, None)


        # If loop set a loser
        if loser is not None:
            if loser == "tie":
                winner_text = "Tie!"
            elif loser == "P1":
                winner_text = "Player 2 Wins!"
            elif loser == "P2":
                winner_text = "Player 1 Wins!"
            if loser != "tie": STATE = "gameover"

    # Update particles (run regardless of game state)
    for p in particles[:]:
        p.update(dt)
        if not p.alive(): particles.remove(p)

    # Drawing
    SCREEN.blit(BACKGROUND, (0,0))

    # Draw all apples
    for food in foods:
        ax, ay = food
        arect = pygame.Rect(ax*CELL + 6, ay*CELL + 6, CELL-12, CELL-12)
        pygame.draw.rect(SCREEN, (255,80,80), arect, border_radius=10)
        pygame.draw.rect(SCREEN, (255,160,160), arect.inflate(-8,-8), border_radius=8)
        stem = pygame.Rect(arect.centerx-3, arect.top-6, 6, 8)
        pygame.draw.rect(SCREEN, (40,140,40), stem, border_radius=3)

    # Draw particles behind snakes
    for p in particles:
        p.draw(SCREEN)

    # Draw snakes (body then head)
    # Snake1 (Player1: White Head)
    for i, (sx, sy) in enumerate(snake1):
        px = sx * CELL
        py = sy * CELL
        if i == 0:
            draw_head_triangle(SCREEN, (px + CELL/2, py + CELL/2), dir1, (255,255,255))
        else:
            col = colors1.get((sx,sy), rand_color())
            pygame.draw.rect(SCREEN, col, (px+3, py+3, CELL-6, CELL-6), border_radius=8)

    # Snake2 (Player2: Yellow/Gold Head)
    for i, (sx, sy) in enumerate(snake2):
        px = sx * CELL
        py = sy * CELL
        if i == 0:
            draw_head_triangle(SCREEN, (px + CELL/2, py + CELL/2), dir2, (240,240,50))
        else:
            col = colors2.get((sx,sy), rand_color())
            pygame.draw.rect(SCREEN, col, (px+3, py+3, CELL-6, CELL-6), border_radius=8)

    # UI: scores and dash
    draw_scoreboard(SCREEN)

    # Centered Dash Bars
    dash_bar_width = 180
    total_height = 60  # Space for both bars with gap
    start_y = H - total_height - 10  # Position from bottom

    # Player 1 Dash Bar (centered, top of the two)
    dash_x = W // 2 - dash_bar_width // 2
    dash_y1 = start_y
    draw_dash_bar(SCREEN, dash_x, dash_y1, w=dash_bar_width, val=(dash_energy1/DASH_MAX), name="P1 Dash (Space)", color=(20,180,240))

    # Player 2 Dash Bar (centered, below P1)
    dash_y2 = start_y + 30
    draw_dash_bar(SCREEN, dash_x, dash_y2, w=dash_bar_width, val=(dash_energy2/DASH_MAX), name="P2 Dash (RShift)", color=(40,200,80))

    # Gameover screen overlay
    if STATE == "gameover":
        render_gameover(SCREEN, winner_text)

    pygame.display.update()
    CLOCK.tick(60)
